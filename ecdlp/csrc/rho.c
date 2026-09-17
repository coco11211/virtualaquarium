/* rho.c -- Pollard rho baseline for ECDLP on y^2 = x^3 + b over F_p, p < 2^63.
 *
 * van Oorschot-Wiener parallel collision search with distinguished points and
 * batched (Montgomery-trick) inversions.  Three modes:
 *   MODE_PLAIN  0 : no equivalence reduction        expected ~ sqrt(pi*n/2)
 *   MODE_NEG    1 : negation map, group size n/2    expected ~ sqrt(pi*n/4)
 *   MODE_ENDO   2 : negation + lambda endomorphism, group size n/6
 *                                                   expected ~ sqrt(pi*n/12)
 *
 * The solver receives ONLY public data (p, n, b, G, Q).  There is no argument
 * through which the secret scalar could reach it.
 *
 * Fruitless cycles (an artifact of the equivalence-class reduction) are handled
 * by 2-cycle detection with a deterministic escape (double the smaller of the
 * two cycle points) plus a per-walk stall bailout.  Both escapes are functions
 * of the point alone, so the iteration map stays deterministic and collisions
 * stay meaningful.
 */
#include "fp.h"
#include <stdio.h>
#include <inttypes.h>

#define MODE_PLAIN 0
#define MODE_NEG   1
#define MODE_ENDO  2

typedef struct {
    uint64_t n;          /* group order (prime), < 2^63          */
    uint64_t lambda;     /* lambda mod n, standard (non-Mont) rep */
    uint64_t beta;       /* beta mod p, Montgomery form           */
} grp_ctx;

static inline uint64_t nadd(uint64_t n, uint64_t a, uint64_t b) { uint64_t r=a+b; return r>=n?r-n:r; }
static inline uint64_t nsub(uint64_t n, uint64_t a, uint64_t b) { return a>=b?a-b:a+n-b; }
static inline uint64_t nmul(uint64_t n, uint64_t a, uint64_t b) { return (uint64_t)(((u128)a*b)%n); }
static uint64_t npow(uint64_t n, uint64_t a, uint64_t e){ uint64_t r=1; a%=n; while(e){ if(e&1) r=nmul(n,r,a); a=nmul(n,a,a); e>>=1;} return r; }
static uint64_t ninv(uint64_t n, uint64_t a){ return npow(n,a,n-2); }   /* n prime */

/* splitmix64 -- deterministic PRNG for reproducible runs */
static inline uint64_t sm64(uint64_t *s){
    uint64_t z = (*s += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

/* ---- canonical representative of the equivalence class of P ----
   MODE_NEG : class {P, -P}            -> pick y <= p-y
   MODE_ENDO: class {+-b^i P, i=0,1,2} -> pick the smallest x among
              {x, beta*x, beta^2*x} (compared in STANDARD, not Montgomery,
              representation so the ordering is well-defined and shared by all
              walks) then the smaller y.
   Returns via *ktw: the automorphism applied, encoded so the caller can update
   the scalar coefficients: e = i + 3*s where the point was mapped by
   (-1)^s * lambda^i, i.e. new = (-1)^s lambda^i * old. */
static inline void canon(const fp_ctx *c, const grp_ctx *g, int mode, ecpt *P, int *ktw)
{
    *ktw = 0;
    if (P->inf) return;
    if (mode == MODE_PLAIN) return;

    int besti = 0;
    if (mode == MODE_ENDO) {
        uint64_t x0 = from_mont(c, P->x);
        uint64_t x1m = mont_mul(c, P->x, g->beta);
        uint64_t x1 = from_mont(c, x1m);
        uint64_t x2m = mont_mul(c, x1m, g->beta);
        uint64_t x2 = from_mont(c, x2m);
        uint64_t bx = x0; uint64_t bxm = P->x;
        if (x1 < bx) { bx = x1; bxm = x1m; besti = 1; }
        if (x2 < bx) { bx = x2; bxm = x2m; besti = 2; }
        P->x = bxm;
    }
    int s = 0;
    uint64_t ys = from_mont(c, P->y);
    if (ys > c->p - ys) { P->y = mont_neg(c, P->y); s = 1; }
    *ktw = besti + 3*s;
}

/* apply the same automorphism to the coefficient pair (a,b) of P = aG + bQ */
static inline void canon_coeff(const grp_ctx *g, int ktw, uint64_t *a, uint64_t *b)
{
    if (!ktw) return;
    int i = ktw % 3, s = ktw / 3;
    if (i) {
        uint64_t l = (i == 1) ? g->lambda : nmul(g->n, g->lambda, g->lambda);
        *a = nmul(g->n, *a, l);
        *b = nmul(g->n, *b, l);
    }
    if (s) { *a = nsub(g->n, 0, *a); *b = nsub(g->n, 0, *b); }
}

/* ------------------------- distinguished point table ------------------------- */
typedef struct { uint64_t x, y, a, b; int used; } dpent;

typedef struct {
    dpent *t; uint64_t mask; uint64_t cnt;
} dptab;

static void dptab_init(dptab *T, int logsz){
    uint64_t sz = 1ULL << logsz;
    T->t = (dpent*)calloc(sz, sizeof(dpent));
    T->mask = sz - 1; T->cnt = 0;
}
static void dptab_free(dptab *T){ free(T->t); }

/* returns 1 and fills (oa,ob) if a *different* representation of the same point
   was already stored */
static int dptab_insert(dptab *T, uint64_t x, uint64_t y, uint64_t a, uint64_t b,
                        uint64_t *oa, uint64_t *ob)
{
    uint64_t h = x * 0x9E3779B97F4A7C15ULL; h ^= h >> 29; h *= 0xBF58476D1CE4E5B9ULL; h ^= h >> 32;
    uint64_t i = h & T->mask;
    for (;;) {
        dpent *e = &T->t[i];
        if (!e->used) { e->used = 1; e->x = x; e->y = y; e->a = a; e->b = b; T->cnt++; return 0; }
        if (e->x == x && e->y == y) {
            if (e->a == a && e->b == b) return 0;      /* identical, no info */
            *oa = e->a; *ob = e->b; return 1;
        }
        i = (i + 1) & T->mask;
    }
}

/* ------------------------------- the solver ------------------------------- */
typedef struct {
    uint64_t k;             /* recovered scalar, or 0 on failure */
    uint64_t steps;         /* total walk steps == point additions            */
    uint64_t extra_ops;     /* extra point ops: escapes (doublings) + restarts */
    uint64_t dps;           /* distinguished points found                     */
    uint64_t cycles;        /* fruitless cycles escaped                       */
    uint64_t restarts;      /* stalled walks restarted                        */
    int      ok;
} rho_res;

#define NWALK_MAX 4096

int rho_solve(uint64_t p, uint64_t nn, uint64_t b_std,
              uint64_t Gx, uint64_t Gy, uint64_t Qx, uint64_t Qy,
              uint64_t beta_std, uint64_t lambda_std,
              int mode, int dbits, int nwalk, int rparts,
              uint64_t seed, uint64_t maxsteps, int logtab,
              rho_res *out)
{
    fp_ctx c; fp_init(&c, p, b_std);
    grp_ctx g; g.n = nn; g.lambda = lambda_std % nn; g.beta = to_mont(&c, beta_std);

    memset(out, 0, sizeof(*out));

    ecpt G = { to_mont(&c, Gx), to_mont(&c, Gy), 0 };
    ecpt Q = { to_mont(&c, Qx), to_mont(&c, Qy), 0 };
    if (!ec_on_curve(&c, &G) || !ec_on_curve(&c, &Q)) return -1;

    if (nwalk > NWALK_MAX) nwalk = NWALK_MAX;
    if (rparts > 4096) rparts = 4096;

    /* ---- precompute the r step points M_j = c_j G + d_j Q ---- */
    ecpt  *M  = malloc(sizeof(ecpt) * rparts);
    uint64_t *Ma = malloc(sizeof(uint64_t) * rparts);
    uint64_t *Mb = malloc(sizeof(uint64_t) * rparts);
    uint64_t s = seed ? seed : 0x1234567890ABCDEFULL;
    for (int j = 0; j < rparts; j++) {
        uint64_t cj = sm64(&s) % nn, dj = sm64(&s) % nn;
        if (cj == 0) cj = 1;
        ecpt A, B, R;
        ec_mul(&c, &G, cj, &A);
        ec_mul(&c, &Q, dj, &B);
        ec_add(&c, &A, &B, &R);
        if (R.inf) { j--; continue; }
        M[j] = R; Ma[j] = cj; Mb[j] = dj;
    }

    /* ---- walk state ---- */
    ecpt     *P  = malloc(sizeof(ecpt) * nwalk);
    uint64_t *wa = malloc(sizeof(uint64_t) * nwalk);
    uint64_t *wb = malloc(sizeof(uint64_t) * nwalk);
    ecpt     *Pp = malloc(sizeof(ecpt) * nwalk);       /* previous point, for 2-cycle detect */
    uint64_t *stall = malloc(sizeof(uint64_t) * nwalk);
    uint64_t *den = malloc(sizeof(uint64_t) * nwalk);
    uint64_t *acc = malloc(sizeof(uint64_t) * (nwalk + 1));
    int      *jj  = malloc(sizeof(int) * nwalk);

    for (int w = 0; w < nwalk; w++) {
        uint64_t a0 = sm64(&s) % nn, b0 = sm64(&s) % nn;
        ecpt A, B, R;
        ec_mul(&c, &G, a0, &A); ec_mul(&c, &Q, b0, &B); ec_add(&c, &A, &B, &R);
        if (R.inf) { w--; continue; }
        int kt; canon(&c, &g, mode, &R, &kt); canon_coeff(&g, kt, &a0, &b0);
        P[w] = R; wa[w] = a0; wb[w] = b0; Pp[w].inf = 1; Pp[w].x = Pp[w].y = 0; stall[w] = 0;
    }

    dptab T; dptab_init(&T, logtab);

    uint64_t dmask = (dbits >= 64) ? ~0ULL : ((1ULL << dbits) - 1);
    uint64_t stall_limit = ((uint64_t)1 << dbits) * 40ULL;
    uint64_t steps = 0;
    int found = 0;
    uint64_t ka = 0, kb = 0, oa = 0, ob = 0;

    while (!found && steps < maxsteps) {
        /* 1. choose step indices and denominators */
        for (int w = 0; w < nwalk; w++) {
            uint64_t xs = from_mont(&c, P[w].x);
            uint64_t h = xs * 0x2545F4914F6CDD1DULL; h ^= h >> 33;
            int j = (int)(h % (uint64_t)rparts);
            /* deterministic fix-ups for the degenerate x-collisions */
            if (P[w].x == M[j].x) {
                if (P[w].y == M[j].y) { /* doubling: use 2y as denominator */ }
                else { j = (j + 1) % rparts; }     /* P = -M_j : shift index */
            }
            jj[w] = j;
            den[w] = (P[w].x == M[j].x && P[w].y == M[j].y)
                     ? mont_add(&c, P[w].y, P[w].y)
                     : mont_sub(&c, M[j].x, P[w].x);
            if (den[w] == 0) den[w] = c.r1;        /* y = 0 impossible on prime-order j=0 curve */
        }
        /* 2. batch inversion (Montgomery's trick) */
        acc[0] = c.r1;
        for (int w = 0; w < nwalk; w++) acc[w+1] = mont_mul(&c, acc[w], den[w]);
        uint64_t iv = mont_inv(&c, acc[nwalk]);
        for (int w = nwalk - 1; w >= 0; w--) {
            uint64_t d = mont_mul(&c, iv, acc[w]);   /* = 1/den[w] */
            iv = mont_mul(&c, iv, den[w]);
            den[w] = d;
        }
        /* 3. complete the additions */
        for (int w = 0; w < nwalk; w++) {
            int j = jj[w];
            uint64_t lam, num;
            if (P[w].x == M[j].x && P[w].y == M[j].y) {
                uint64_t x2 = mont_mul(&c, P[w].x, P[w].x);
                num = mont_add(&c, mont_add(&c, x2, x2), x2);
            } else {
                num = mont_sub(&c, M[j].y, P[w].y);
            }
            lam = mont_mul(&c, num, den[w]);
            uint64_t xr = mont_sub(&c, mont_sub(&c, mont_mul(&c, lam, lam), P[w].x), M[j].x);
            uint64_t yr = mont_sub(&c, mont_mul(&c, lam, mont_sub(&c, P[w].x, xr)), P[w].y);
            ecpt prev = P[w];
            ecpt nx = { xr, yr, 0 };
            uint64_t na = nadd(nn, wa[w], Ma[j]), nb = nadd(nn, wb[w], Mb[j]);
            int kt; canon(&c, &g, mode, &nx, &kt); canon_coeff(&g, kt, &na, &nb);

            /* --- fruitless 2-cycle: new point equals the point before prev --- */
            if (mode != MODE_PLAIN && !Pp[w].inf && nx.x == Pp[w].x && nx.y == Pp[w].y) {
                out->cycles++;
                /* escape deterministically: double the smaller of {prev, nx} */
                ecpt *mn; uint64_t *ma_, *mb_;
                uint64_t px = from_mont(&c, prev.x), nxs = from_mont(&c, nx.x);
                if (px < nxs) { mn = &prev; ma_ = &wa[w]; mb_ = &wb[w]; }
                else          { mn = &nx;   ma_ = &na;    mb_ = &nb;    }
                ecpt D; ec_add(&c, mn, mn, &D);
                uint64_t da = nadd(nn, *ma_, *ma_), db = nadd(nn, *mb_, *mb_);
                int kt2; canon(&c, &g, mode, &D, &kt2); canon_coeff(&g, kt2, &da, &db);
                nx = D; na = da; nb = db;
                out->extra_ops++;
            }
            Pp[w] = prev; P[w] = nx; wa[w] = na; wb[w] = nb;
            steps++;
            stall[w]++;

            /* 4. distinguished point? */
            if (!nx.inf && (from_mont(&c, nx.x) & dmask) == 0) {
                out->dps++;
                stall[w] = 0;
                uint64_t xs = from_mont(&c, nx.x), ys = from_mont(&c, nx.y);
                if (dptab_insert(&T, xs, ys, na, nb, &oa, &ob)) {
                    if (nb != ob) { ka = na; kb = nb; found = 1; break; }
                }
            } else if (stall[w] > stall_limit) {
                /* long cycle we did not detect: restart this walk */
                out->restarts++;
                uint64_t a0 = sm64(&s) % nn, b0 = sm64(&s) % nn;
                ecpt A, B, R;
                ec_mul(&c, &G, a0, &A); ec_mul(&c, &Q, b0, &B); ec_add(&c, &A, &B, &R);
                if (!R.inf) {
                    int kt3; canon(&c, &g, mode, &R, &kt3); canon_coeff(&g, kt3, &a0, &b0);
                    P[w] = R; wa[w] = a0; wb[w] = b0; Pp[w].inf = 1; stall[w] = 0;
                    out->extra_ops += 64;
                }
            }
        }
    }

    out->steps = steps;
    if (found) {
        /* ka*G + kb*Q = oa*G + ob*Q  =>  (kb-ob) Q = (oa-ka) G  =>  k = (oa-ka)/(kb-ob) */
        uint64_t num = nsub(nn, oa, ka), den2 = nsub(nn, kb, ob);
        uint64_t k = nmul(nn, num, ninv(nn, den2));
        out->k = k; out->ok = 1;
    }
    dptab_free(&T);
    free(M); free(Ma); free(Mb); free(P); free(wa); free(wb); free(Pp);
    free(stall); free(den); free(acc); free(jj);
    return out->ok ? 0 : 1;
}

/* small helper exposed for the harness: compute k*G on the curve */
void ec_scalar_mul(uint64_t p, uint64_t b_std, uint64_t Gx, uint64_t Gy,
                   uint64_t k, uint64_t *rx, uint64_t *ry, int *inf)
{
    fp_ctx c; fp_init(&c, p, b_std);
    ecpt G = { to_mont(&c, Gx), to_mont(&c, Gy), 0 }, R;
    ec_mul(&c, &G, k, &R);
    *inf = R.inf; *rx = R.inf ? 0 : from_mont(&c, R.x); *ry = R.inf ? 0 : from_mont(&c, R.y);
}

/* ---------------- batch helpers for the experiment harness ---------------- */

/* Batch affine point addition with one shared inversion (Montgomery's trick).
   Inputs/outputs in STANDARD representation.  inf[] flags: bit0 of code.
   Returns 0.  Degenerate cases (equal x) are handled per-point. */
int ec_add_batch(uint64_t p, uint64_t b_std, int cnt,
                 const uint64_t *ax, const uint64_t *ay,
                 const uint64_t *bx, const uint64_t *by,
                 uint64_t *rx, uint64_t *ry, int *rinf)
{
    fp_ctx c; fp_init(&c, p, b_std);
    uint64_t *den = malloc(sizeof(uint64_t) * cnt);
    uint64_t *acc = malloc(sizeof(uint64_t) * (cnt + 1));
    uint64_t *AX = malloc(sizeof(uint64_t) * cnt), *AY = malloc(sizeof(uint64_t) * cnt);
    uint64_t *BX = malloc(sizeof(uint64_t) * cnt), *BY = malloc(sizeof(uint64_t) * cnt);
    int *deg = malloc(sizeof(int) * cnt);
    for (int i = 0; i < cnt; i++) {
        AX[i] = to_mont(&c, ax[i]); AY[i] = to_mont(&c, ay[i]);
        BX[i] = to_mont(&c, bx[i]); BY[i] = to_mont(&c, by[i]);
        if (AX[i] == BX[i]) {
            if (AY[i] == BY[i] && AY[i] != 0) { deg[i] = 1; den[i] = mont_add(&c, AY[i], AY[i]); }
            else { deg[i] = 2; den[i] = c.r1; }         /* P = -Q -> infinity */
        } else { deg[i] = 0; den[i] = mont_sub(&c, BX[i], AX[i]); }
    }
    acc[0] = c.r1;
    for (int i = 0; i < cnt; i++) acc[i+1] = mont_mul(&c, acc[i], den[i]);
    uint64_t iv = mont_inv(&c, acc[cnt]);
    for (int i = cnt - 1; i >= 0; i--) {
        uint64_t d = mont_mul(&c, iv, acc[i]);
        iv = mont_mul(&c, iv, den[i]);
        den[i] = d;
    }
    for (int i = 0; i < cnt; i++) {
        if (deg[i] == 2) { rinf[i] = 1; rx[i] = ry[i] = 0; continue; }
        uint64_t num;
        if (deg[i] == 1) { uint64_t x2 = mont_mul(&c, AX[i], AX[i]);
                           num = mont_add(&c, mont_add(&c, x2, x2), x2); }
        else             { num = mont_sub(&c, BY[i], AY[i]); }
        uint64_t lam = mont_mul(&c, num, den[i]);
        uint64_t xr = mont_sub(&c, mont_sub(&c, mont_mul(&c, lam, lam), AX[i]), BX[i]);
        uint64_t yr = mont_sub(&c, mont_mul(&c, lam, mont_sub(&c, AX[i], xr)), AY[i]);
        rx[i] = from_mont(&c, xr); ry[i] = from_mont(&c, yr); rinf[i] = 0;
    }
    free(den); free(acc); free(AX); free(AY); free(BX); free(BY); free(deg);
    return 0;
}

/* For each x in xs[], if x^3+b is a QR return the point (x, min(y,p-y)) and set
   ok=1, else ok=0.  Standard representation. */
int ec_lift_batch(uint64_t p, uint64_t b_std, int cnt, const uint64_t *xsv,
                  uint64_t *ry, int *ok)
{
    fp_ctx c; fp_init(&c, p, b_std);
    if (p % 4 != 3) {
        /* Tonelli-Shanks setup */
        uint64_t q = p - 1; int s = 0;
        while (!(q & 1)) { q >>= 1; s++; }
        uint64_t zz = 2;
        while (mont_pow(&c, to_mont(&c, zz), (p-1)/2) != c.p - c.r1 + (c.r1 ? 0 : 0)) {
            /* find a non-residue: compare against -1 in Montgomery form */
            uint64_t v = mont_pow(&c, to_mont(&c, zz), (p-1)/2);
            if (v == mont_neg(&c, c.r1)) break;
            zz++;
            if (zz > 1000) break;
        }
        uint64_t cc = mont_pow(&c, to_mont(&c, zz), q);
        for (int i = 0; i < cnt; i++) {
            uint64_t a = to_mont(&c, xsv[i]);
            uint64_t rhs = mont_add(&c, mont_mul(&c, mont_mul(&c, a, a), a), c.b);
            if (rhs == 0) { ry[i] = 0; ok[i] = 1; continue; }
            if (mont_pow(&c, rhs, (p-1)/2) != c.r1) { ok[i] = 0; ry[i] = 0; continue; }
            int m = s; uint64_t C = cc;
            uint64_t t = mont_pow(&c, rhs, q);
            uint64_t r = mont_pow(&c, rhs, (q+1)/2);
            while (t != c.r1) {
                int i2 = 0; uint64_t t2 = t;
                while (t2 != c.r1) { t2 = mont_mul(&c, t2, t2); i2++; }
                uint64_t bb = C;
                for (int j = 0; j < m - i2 - 1; j++) bb = mont_mul(&c, bb, bb);
                m = i2; C = mont_mul(&c, bb, bb);
                t = mont_mul(&c, t, C);
                r = mont_mul(&c, r, bb);
            }
            uint64_t y = from_mont(&c, r);
            ry[i] = y < p - y ? y : p - y; ok[i] = 1;
        }
        return 0;
    }
    for (int i = 0; i < cnt; i++) {
        uint64_t a = to_mont(&c, xsv[i]);
        uint64_t rhs = mont_add(&c, mont_mul(&c, mont_mul(&c, a, a), a), c.b);
        if (rhs == 0) { ry[i] = 0; ok[i] = 1; continue; }
        uint64_t y = mont_pow(&c, rhs, (p + 1) / 4);
        if (mont_mul(&c, y, y) != rhs) { ok[i] = 0; ry[i] = 0; continue; }
        uint64_t ys = from_mont(&c, y);
        ry[i] = ys < p - ys ? ys : p - ys; ok[i] = 1;
    }
    return 0;
}

/* batch scalar multiples k_i * P  (standard representation) */
int ec_mul_batch(uint64_t p, uint64_t b_std, uint64_t Gx, uint64_t Gy, int cnt,
                 const uint64_t *ks, uint64_t *rx, uint64_t *ry, int *rinf)
{
    fp_ctx c; fp_init(&c, p, b_std);
    ecpt G = { to_mont(&c, Gx), to_mont(&c, Gy), 0 };
    for (int i = 0; i < cnt; i++) {
        ecpt R; ec_mul(&c, &G, ks[i], &R);
        rinf[i] = R.inf;
        rx[i] = R.inf ? 0 : from_mont(&c, R.x);
        ry[i] = R.inf ? 0 : from_mont(&c, R.y);
    }
    return 0;
}
