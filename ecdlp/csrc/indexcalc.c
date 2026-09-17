/* indexcalc.c -- index calculus / generalised-birthday attack on the ECDLP over
 * a PRIME field, built so its cost can be measured rather than argued about.
 *
 * Factor base  F = the m points of smallest x-coordinate (a public, canonical set).
 * Relations are  a_i G + b_i Q = sum_j e_ij P_j  with e_ij in {0,+-1} and exactly
 * k nonzero entries.  Decomposition uses a precomputed table of all j-fold sums of
 * factor-base elements, then enumerates (k-j)-fold signed sums per target:
 *
 *      build table            m^j
 *      per-target work        (2m)^(k-j)
 *      targets needed         ~ m * n / (2m)^k
 *      relation cost          ~ m * n / (2m)^j
 *      linear algebra         m^2 (sparse) / m^3 (the dense solve used here)
 *
 * Working in E/{+-1}: the table is keyed on the x-coordinate, so it covers a sum
 * and its negative at once; the outer sign is resolved from y.
 *
 * The solver is handed only (p, n, b, G, Q).  There is no argument through which
 * the secret scalar could reach it.
 */
#include "fp.h"
#include <time.h>

/* provided by wiedemann.c, linked into the same shared object */
int sparse_left_kernel(uint64_t n, int R, int C, const int *off, const int *col,
                       const uint64_t *val, uint64_t seed, uint64_t *out,
                       uint64_t *ops, int max_try);
#include <stdio.h>
#include <string.h>

typedef struct {
    uint64_t fb_ops;       /* point ops building the factor base   */
    uint64_t tab_ops;      /* point ops building the sum table     */
    uint64_t rel_ops;      /* point ops + lookups finding relations*/
    uint64_t la_ops;       /* field ops in the linear algebra      */
    uint64_t targets;      /* random R's tried                     */
    uint64_t relations;    /* relations collected                  */
    uint64_t table_size;
    double   sec_fb, sec_tab, sec_rel, sec_la;
    int      ok;
} ic_stats;

/* ---------------------------------------------------------------- hash table */
typedef struct { uint64_t *key; uint64_t *val; uint64_t mask; uint64_t cnt; } htab;

static void ht_init(htab *H, uint64_t want) {
    uint64_t sz = 16;
    while (sz < want * 2) sz <<= 1;
    H->key = malloc(sz * sizeof(uint64_t));
    H->val = malloc(sz * sizeof(uint64_t));
    memset(H->key, 0xFF, sz * sizeof(uint64_t));    /* ~0 = empty */
    H->mask = sz - 1; H->cnt = 0;
}
static void ht_free(htab *H) { free(H->key); free(H->val); }
static inline uint64_t ht_h(uint64_t x) {
    x *= 0x9E3779B97F4A7C15ULL; x ^= x >> 31; x *= 0xBF58476D1CE4E5B9ULL; x ^= x >> 29;
    return x;
}
static void ht_put(htab *H, uint64_t k, uint64_t v) {
    uint64_t i = ht_h(k) & H->mask;
    while (H->key[i] != ~0ULL) { if (H->key[i] == k) return; i = (i + 1) & H->mask; }
    H->key[i] = k; H->val[i] = v; H->cnt++;
}
static int ht_get(const htab *H, uint64_t k, uint64_t *v) {
    uint64_t i = ht_h(k) & H->mask;
    while (H->key[i] != ~0ULL) {
        if (H->key[i] == k) { *v = H->val[i]; return 1; }
        i = (i + 1) & H->mask;
    }
    return 0;
}

/* ------------------------------------------------------- mod-n helpers */
static inline uint64_t Nadd(uint64_t n, uint64_t a, uint64_t b){uint64_t r=a+b;return r>=n?r-n:r;}
static inline uint64_t Nsub(uint64_t n, uint64_t a, uint64_t b){return a>=b?a-b:a+n-b;}
static inline uint64_t Nmul(uint64_t n, uint64_t a, uint64_t b){return (uint64_t)(((u128)a*b)%n);}
static uint64_t Npow(uint64_t n,uint64_t a,uint64_t e){uint64_t r=1;a%=n;while(e){if(e&1)r=Nmul(n,r,a);a=Nmul(n,a,a);e>>=1;}return r;}
static uint64_t Ninv(uint64_t n,uint64_t a){return Npow(n,a,n-2);}
static inline uint64_t sm64b(uint64_t *s){uint64_t z=(*s+=0x9E3779B97F4A7C15ULL);
    z=(z^(z>>30))*0xBF58476D1CE4E5B9ULL;z=(z^(z>>27))*0x94D049BB133111EBULL;return z^(z>>31);}

/* -------------------------------------- dense left-kernel over F_n (Gaussian) */
/* M is rows x cols, row-major, entries in [0,n).  Finds a nonzero v with v^T M = 0.
   Returns 1 on success, writing v into out[rows]. */
static int left_kernel(uint64_t n, int rows, int cols, uint64_t *M, uint64_t *out,
                       uint64_t *ops)
{
    /* augment with the identity: work on [M | I] and look for a row whose M-part
       vanishes; its I-part is then a left-kernel vector. */
    int W = cols + rows;
    uint64_t *A = calloc((size_t)rows * W, sizeof(uint64_t));
    for (int i = 0; i < rows; i++) {
        memcpy(A + (size_t)i * W, M + (size_t)i * cols, cols * sizeof(uint64_t));
        A[(size_t)i * W + cols + i] = 1;
    }
    int r = 0;
    for (int c = 0; c < cols && r < rows; c++) {
        int piv = -1;
        for (int i = r; i < rows; i++) if (A[(size_t)i * W + c]) { piv = i; break; }
        if (piv < 0) continue;
        if (piv != r) for (int j = c; j < W; j++) {
            uint64_t t = A[(size_t)r*W+j]; A[(size_t)r*W+j] = A[(size_t)piv*W+j]; A[(size_t)piv*W+j] = t;
        }
        uint64_t iv = Ninv(n, A[(size_t)r*W+c]);
        for (int j = c; j < W; j++) A[(size_t)r*W+j] = Nmul(n, A[(size_t)r*W+j], iv);
        for (int i = 0; i < rows; i++) {
            if (i == r) continue;
            uint64_t f = A[(size_t)i*W+c];
            if (!f) continue;
            for (int j = c; j < W; j++)
                A[(size_t)i*W+j] = Nsub(n, A[(size_t)i*W+j], Nmul(n, f, A[(size_t)r*W+j]));
            *ops += (uint64_t)(W - c);
        }
        r++;
    }
    int found = 0;
    for (int i = 0; i < rows && !found; i++) {
        int zero = 1;
        for (int j = 0; j < cols; j++) if (A[(size_t)i*W+j]) { zero = 0; break; }
        if (!zero) continue;
        int nz = 0;
        for (int j = 0; j < rows; j++) if (A[(size_t)i*W+cols+j]) { nz = 1; break; }
        if (!nz) continue;
        for (int j = 0; j < rows; j++) out[j] = A[(size_t)i*W+cols+j];
        found = 1;
    }
    free(A);
    return found;
}

/* ------------------------------------------------------------------- the attack */
int index_calculus(uint64_t p, uint64_t nn, uint64_t b_std,
                   uint64_t Gx, uint64_t Gy, uint64_t Qx, uint64_t Qy,
                   int m, int k, int j, uint64_t seed, uint64_t max_targets,
                   uint64_t *k_out, ic_stats *st)
{
    fp_ctx c; fp_init(&c, p, b_std);
    memset(st, 0, sizeof(*st));
    ecpt G = { to_mont(&c, Gx), to_mont(&c, Gy), 0 };
    ecpt Q = { to_mont(&c, Qx), to_mont(&c, Qy), 0 };
    if (!ec_on_curve(&c, &G) || !ec_on_curve(&c, &Q)) return -1;
    if (j < 1 || j >= k) return -2;

    clock_t t0 = clock();
    /* ---- 1. factor base: the m points with smallest x ---- */
    ecpt *F = malloc(sizeof(ecpt) * m);
    int got = 0;
    for (uint64_t x = 0; got < m && x < p; x++) {
        uint64_t xm = to_mont(&c, x);
        uint64_t rhs = mont_add(&c, mont_mul(&c, mont_mul(&c, xm, xm), xm), c.b);
        st->fb_ops++;
        if (rhs == 0) { F[got].x = xm; F[got].y = 0; F[got].inf = 0; got++; continue; }
        if (mont_pow(&c, rhs, (p - 1) / 2) != c.r1) continue;
        uint64_t y;
        if (p % 4 == 3) y = mont_pow(&c, rhs, (p + 1) / 4);
        else {                                        /* Tonelli-Shanks */
            uint64_t q = p - 1; int s = 0;
            while (!(q & 1)) { q >>= 1; s++; }
            uint64_t z = 2;
            while (mont_pow(&c, to_mont(&c, z), (p-1)/2) != mont_neg(&c, c.r1)) z++;
            uint64_t C = mont_pow(&c, to_mont(&c, z), q);
            uint64_t t = mont_pow(&c, rhs, q);
            y = mont_pow(&c, rhs, (q + 1) / 2);
            int mm = s;
            while (t != c.r1) {
                int i2 = 0; uint64_t t2 = t;
                while (t2 != c.r1) { t2 = mont_mul(&c, t2, t2); i2++; }
                uint64_t bb = C;
                for (int q2 = 0; q2 < mm - i2 - 1; q2++) bb = mont_mul(&c, bb, bb);
                mm = i2; C = mont_mul(&c, bb, bb);
                t = mont_mul(&c, t, C); y = mont_mul(&c, y, bb);
            }
        }
        if (mont_mul(&c, y, y) != rhs) continue;
        uint64_t ys = from_mont(&c, y);
        F[got].x = xm; F[got].y = to_mont(&c, ys < p - ys ? ys : p - ys); F[got].inf = 0;
        got++;
    }
    if (got < m) { free(F); return -3; }
    st->sec_fb = (double)(clock() - t0) / CLOCKS_PER_SEC;

    /* ---- 2. table of all j-fold sums P_{i1} + ... + P_{ij}, i1 <= ... <= ij ---- */
    t0 = clock();
    uint64_t want = 1;
    { double w = 1; for (int q = 0; q < j; q++) w = w * (m + q) / (q + 1); want = (uint64_t)w + 16; }
    htab H; ht_init(&H, want);
    {
        int idx[8]; for (int q = 0; q < j; q++) idx[q] = 0;
        ecpt part[9];
        part[0].inf = 1; part[0].x = part[0].y = 0;
        /* iterative odometer over non-decreasing index tuples */
        int depth = 0;
        while (1) {
            if (depth == j) {
                if (!part[j].inf) {
                    uint64_t key = from_mont(&c, part[j].x);
                    uint64_t v = 0;
                    for (int q = 0; q < j; q++) v = v * (uint64_t)m + (uint64_t)idx[q];
                    ht_put(&H, key, v);
                    st->tab_ops++;
                }
                depth--;
                while (depth >= 0) {
                    idx[depth]++;
                    if (idx[depth] < m) break;
                    depth--;
                }
                if (depth < 0) break;
                ec_add(&c, &part[depth], &F[idx[depth]], &part[depth + 1]);
                st->tab_ops++;
                for (int q = depth + 1; q < j; q++) idx[q] = idx[depth];
                depth++;
                while (depth < j) {
                    ec_add(&c, &part[depth], &F[idx[depth]], &part[depth + 1]);
                    st->tab_ops++; depth++;
                }
            } else {
                ec_add(&c, &part[depth], &F[idx[depth]], &part[depth + 1]);
                st->tab_ops++; depth++;
            }
        }
    }
    st->table_size = H.cnt;
    st->sec_tab = (double)(clock() - t0) / CLOCKS_PER_SEC;

    /* ---- 3. relations ---- */
    t0 = clock();
    int need = m + 24;
    int kmax = k + 2;
    int      *roff = malloc(sizeof(int) * (size_t)(need + 1));
    int      *rcol = malloc(sizeof(int) * (size_t)need * kmax);
    uint64_t *rval = malloc(sizeof(uint64_t) * (size_t)need * kmax);
    int      *tidx = malloc(sizeof(int) * (size_t)kmax);
    int64_t  *tcof = malloc(sizeof(int64_t) * (size_t)kmax);
    roff[0] = 0;
    uint64_t *RA = malloc(sizeof(uint64_t) * need), *RB = malloc(sizeof(uint64_t) * need);
    int nrel = 0;
    uint64_t s = seed ? seed : 0xC0FFEE123456789ULL;
    int e = k - j;                                  /* elements enumerated per target */
    int eidx[8]; int esgn[8];

    while (nrel < need && st->targets < max_targets) {
        uint64_t a = sm64b(&s) % nn, bb = sm64b(&s) % nn;
        ecpt A, B, R;
        ec_mul(&c, &G, a, &A); ec_mul(&c, &Q, bb, &B); ec_add(&c, &A, &B, &R);
        st->targets++;
        if (R.inf) continue;
        /* enumerate signed e-tuples i1 <= ... <= ie with signs */
        int done = 0;
        for (int q = 0; q < e; q++) { eidx[q] = 0; esgn[q] = 0; }
        while (!done) {
            ecpt S = R;                              /* S = R - sum eps_q P_{i_q} */
            for (int q = 0; q < e; q++) {
                ecpt Pq = F[eidx[q]];
                if (esgn[q]) Pq.y = mont_neg(&c, Pq.y);
                ecpt nn2; ec_neg(&c, &Pq, &nn2);
                ecpt tmp; ec_add(&c, &S, &nn2, &tmp); S = tmp;
                st->rel_ops++;
            }
            uint64_t v;
            if (!S.inf && ht_get(&H, from_mont(&c, S.x), &v)) {
                /* S = +-(P_{t1} + ... + P_{tj}); resolve the outer sign */
                int tid[8];
                uint64_t vv = v;
                for (int q = j - 1; q >= 0; q--) { tid[q] = (int)(vv % (uint64_t)m); vv /= (uint64_t)m; }
                ecpt T2; T2.inf = 1; T2.x = T2.y = 0;
                for (int q = 0; q < j; q++) { ecpt t3; ec_add(&c, &T2, &F[tid[q]], &t3); T2 = t3; }
                int outer = (T2.y == S.y) ? +1 : -1;
                /* R = sum_q eps_q P_{i_q} + outer * sum_q P_{t_q}; accumulate the
                   (index, coefficient) pairs, merging repeats and dropping zeros */
                int nt = 0;
                for (int q = 0; q < e + j; q++) {
                    int idxq  = (q < e) ? eidx[q] : tid[q - e];
                    int64_t d = (q < e) ? (esgn[q] ? -1 : 1) : (outer > 0 ? 1 : -1);
                    int f2 = -1;
                    for (int r2 = 0; r2 < nt; r2++) if (tidx[r2] == idxq) { f2 = r2; break; }
                    if (f2 >= 0) tcof[f2] += d;
                    else { tidx[nt] = idxq; tcof[nt] = d; nt++; }
                }
                { int w2 = 0;
                  for (int q = 0; q < nt; q++) if (tcof[q]) { tidx[w2] = tidx[q]; tcof[w2] = tcof[q]; w2++; }
                  nt = w2; }
                if (nt == 0) break;                    /* trivial relation, no information */
                /* verify the relation exactly against a_i G + b_i Q */
                ecpt chk; chk.inf = 1; chk.x = chk.y = 0;
                for (int q = 0; q < nt; q++) {
                    int64_t cq = tcof[q]; int neg = cq < 0; if (neg) cq = -cq;
                    for (int64_t r2 = 0; r2 < cq; r2++) {
                        ecpt use = F[tidx[q]]; if (neg) use.y = mont_neg(&c, use.y);
                        ecpt t4; ec_add(&c, &chk, &use, &t4); chk = t4;
                    }
                }
                ecpt lhs; { ecpt A2, B2; ec_mul(&c, &G, a, &A2); ec_mul(&c, &Q, bb, &B2);
                            ec_add(&c, &A2, &B2, &lhs); }
                if (chk.inf == lhs.inf && (chk.inf || (chk.x == lhs.x && chk.y == lhs.y))) {
                    int base = roff[nrel];
                    for (int q = 0; q < nt; q++) {
                        rcol[base + q] = tidx[q];
                        rval[base + q] = (tcof[q] >= 0) ? (uint64_t)tcof[q]
                                                        : nn - (uint64_t)(-tcof[q]);
                    }
                    roff[nrel + 1] = base + nt;
                    RA[nrel] = a; RB[nrel] = bb; nrel++;
                    st->relations++;
                }
                break;                                 /* one relation per target */
            }
            /* odometer over (eidx, esgn) */
            int q = e - 1;
            while (q >= 0) {
                if (!esgn[q]) { esgn[q] = 1; break; }
                esgn[q] = 0; eidx[q]++;
                if (eidx[q] < m) break;
                q--;
            }
            if (q < 0) done = 1;
            else for (int q2 = q + 1; q2 < e; q2++) { eidx[q2] = eidx[q]; esgn[q2] = 0; }
        }
    }
    st->sec_rel = (double)(clock() - t0) / CLOCKS_PER_SEC;
    if (nrel < m + 1) {
        free(F); free(roff); free(rcol); free(rval); free(tidx); free(tcof);
        free(RA); free(RB); ht_free(&H);
        return -4;
    }

    /* ---- 4. linear algebra: v^T M = 0  =>  (sum v_i a_i) G + (sum v_i b_i) Q = O ---- */
    t0 = clock();
    uint64_t *v = calloc(nrel, sizeof(uint64_t));
    uint64_t la = 0;
    int ok = sparse_left_kernel(nn, nrel, m, roff, rcol, rval, seed ^ 0x5DEECE66DULL,
                                v, &la, 8);
    st->la_ops = la;
    st->sec_la = (double)(clock() - t0) / CLOCKS_PER_SEC;
    int rc = 1;
    if (ok) {
        uint64_t sa = 0, sb = 0;
        for (int i = 0; i < nrel; i++) {
            if (!v[i]) continue;
            sa = Nadd(nn, sa, Nmul(nn, v[i], RA[i]));
            sb = Nadd(nn, sb, Nmul(nn, v[i], RB[i]));
        }
        if (sb != 0) {
            *k_out = Nmul(nn, Nsub(nn, 0, sa), Ninv(nn, sb));
            st->ok = 1; rc = 0;
        }
    }
    free(v); free(F); free(roff); free(rcol); free(rval); free(tidx); free(tcof);
    free(RA); free(RB); ht_free(&H);
    return rc;
}
