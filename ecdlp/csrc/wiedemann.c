/* wiedemann.c -- sparse left-kernel over F_n (n prime, n < 2^63).
 *
 * Index calculus needs one nonzero v with v^T M = 0, where M is R x C with only
 * a handful of nonzeros per row (R = C + slack).  Dense elimination is O(C^3),
 * which would dominate and destroy the very scaling we are trying to measure.
 * Wiedemann costs O(C) per matrix-vector product and O(C) products, i.e. O(C^2)
 * field operations -- the cost normally charged to index calculus.
 *
 * v^T M = 0  <=>  M^T v = 0.  We run Wiedemann on the square operator
 *      A = M D M^T          (R x R, symmetric, singular, rank <= C)
 * with D a random diagonal twist on F_n^C, which makes spurious isotropic kernel
 * vectors unlikely.  Every candidate is CHECKED against M^T v = 0 before being
 * returned, so a bad draw costs a retry and never a wrong answer.
 */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned __int128 u128_w;
static inline uint64_t Wadd(uint64_t n,uint64_t a,uint64_t b){uint64_t r=a+b;return r>=n?r-n:r;}
static inline uint64_t Wsub(uint64_t n,uint64_t a,uint64_t b){return a>=b?a-b:a+n-b;}
static inline uint64_t Wmul(uint64_t n,uint64_t a,uint64_t b){return (uint64_t)(((u128_w)a*b)%n);}
static uint64_t Wpow(uint64_t n,uint64_t a,uint64_t e){uint64_t r=1;a%=n;while(e){if(e&1)r=Wmul(n,r,a);a=Wmul(n,a,a);e>>=1;}return r;}
static uint64_t Winv(uint64_t n,uint64_t a){return Wpow(n,a,n-2);}
static inline uint64_t wsm(uint64_t *s){uint64_t z=(*s+=0x9E3779B97F4A7C15ULL);
    z=(z^(z>>30))*0xBF58476D1CE4E5B9ULL;z=(z^(z>>27))*0x94D049BB133111EBULL;return z^(z>>31);}

typedef struct { int R, C; const int *off, *col; const uint64_t *val; } spmat;

static void mTx(uint64_t n, const spmat *M, const uint64_t *x, uint64_t *y, uint64_t *ops) {
    memset(y, 0, sizeof(uint64_t) * M->C);
    for (int i = 0; i < M->R; i++) {
        uint64_t xi = x[i];
        if (!xi) continue;
        for (int t = M->off[i]; t < M->off[i+1]; t++)
            y[M->col[t]] = Wadd(n, y[M->col[t]], Wmul(n, xi, M->val[t]));
    }
    *ops += (uint64_t)M->off[M->R];
}
static void mZ(uint64_t n, const spmat *M, const uint64_t *z, uint64_t *y, uint64_t *ops) {
    for (int i = 0; i < M->R; i++) {
        uint64_t a = 0;
        for (int t = M->off[i]; t < M->off[i+1]; t++)
            a = Wadd(n, a, Wmul(n, M->val[t], z[M->col[t]]));
        y[i] = a;
    }
    *ops += (uint64_t)M->off[M->R];
}
static void applyA(uint64_t n, const spmat *M, const uint64_t *D,
                   const uint64_t *x, uint64_t *y, uint64_t *tmp, uint64_t *ops) {
    mTx(n, M, x, tmp, ops);
    for (int c = 0; c < M->C; c++) tmp[c] = Wmul(n, tmp[c], D[c]);
    mZ(n, M, tmp, y, ops);
}

/* Berlekamp-Massey over F_n.  c[0..deg], c[0] = 1.  Returns deg. */
static int bm(uint64_t n, const uint64_t *s, int L, uint64_t *c, uint64_t *ops) {
    uint64_t *b = calloc(L + 2, sizeof(uint64_t));
    uint64_t *t = calloc(L + 2, sizeof(uint64_t));
    memset(c, 0, sizeof(uint64_t) * (L + 2));
    c[0] = 1; b[0] = 1;
    int lc = 0, lb = 0, m = 1;
    uint64_t bb = 1;
    for (int i = 0; i < L; i++) {
        uint64_t d = s[i];
        for (int j = 1; j <= lc; j++) d = Wadd(n, d, Wmul(n, c[j], s[i - j]));
        *ops += (uint64_t)lc + 1;
        if (d == 0) { m++; continue; }
        memcpy(t, c, sizeof(uint64_t) * (L + 2));
        uint64_t co = Wmul(n, d, Winv(n, bb));
        for (int j = 0; j + m <= L; j++)
            c[j + m] = Wsub(n, c[j + m], Wmul(n, co, b[j]));
        *ops += (uint64_t)(L - m + 1);
        if (2 * lc <= i) {
            memcpy(b, t, sizeof(uint64_t) * (L + 2));
            lb = lc; lc = i + 1 - lc; bb = d; m = 1;
            (void)lb;
        } else m++;
    }
    int deg = 0;
    for (int j = 0; j <= L; j++) if (c[j]) deg = j;
    free(b); free(t);
    return deg;
}

int sparse_left_kernel(uint64_t n, int R, int C, const int *off, const int *col,
                       const uint64_t *val, uint64_t seed, uint64_t *out, uint64_t *ops,
                       int max_try)
{
    spmat M = { R, C, off, col, val };
    uint64_t s = seed ? seed : 0xABCDEF0123456789ULL;
    uint64_t *D = malloc(sizeof(uint64_t) * C);
    uint64_t *b = malloc(sizeof(uint64_t) * R);
    uint64_t *u = malloc(sizeof(uint64_t) * R);
    uint64_t *x = malloc(sizeof(uint64_t) * R);
    uint64_t *y = malloc(sizeof(uint64_t) * R);
    uint64_t *w = malloc(sizeof(uint64_t) * R);
    uint64_t *tmp = malloc(sizeof(uint64_t) * C);
    uint64_t *chk = malloc(sizeof(uint64_t) * C);
    int L = 2 * R + 2;
    uint64_t *seq = malloc(sizeof(uint64_t) * L);
    uint64_t *cf = calloc(L + 4, sizeof(uint64_t));
    int success = 0;

    for (int att = 0; att < max_try && !success; att++) {
        for (int c = 0; c < C; c++) D[c] = 1 + wsm(&s) % (n - 1);
        for (int i = 0; i < R; i++) { b[i] = wsm(&s) % n; u[i] = wsm(&s) % n; }
        memcpy(x, b, sizeof(uint64_t) * R);
        for (int i = 0; i < L; i++) {
            uint64_t a = 0;
            for (int q = 0; q < R; q++) a = Wadd(n, a, Wmul(n, u[q], x[q]));
            *ops += (uint64_t)R;
            seq[i] = a;
            applyA(n, &M, D, x, y, tmp, ops);
            memcpy(x, y, sizeof(uint64_t) * R);
        }
        int deg = bm(n, seq, L, cf, ops);
        if (deg <= 0) continue;
        /* Berlekamp-Massey returns RECURRENCE coefficients: s[i] = -sum_j cf[j] s[i-j],
           so the minimal polynomial is  f(x) = sum_{j=0}^{deg} cf[j] x^{deg-j},
           monic because cf[0] = 1.  A is singular, so x | f: writing hi for the
           largest index with cf[hi] != 0 gives f(x) = x^e g(x) with e = deg - hi and
           g(x) = sum_{i=0}^{hi} cf[hi-i] x^i,  g(0) = cf[hi] != 0.
           Then A^e (g(A) b) = f(A) b = 0, so g(A)b feeds a walk into ker A. */
        int hi = deg;
        while (hi >= 0 && cf[hi] == 0) hi--;
        if (hi < 0) continue;
        int e = deg - hi;
        /* Horner:  y = cf[0] b;  y <- A y + cf[j] b   for j = 1..hi */
        for (int q = 0; q < R; q++) y[q] = Wmul(n, cf[0], b[q]);
        for (int jj = 1; jj <= hi; jj++) {
            applyA(n, &M, D, y, w, tmp, ops);
            for (int q = 0; q < R; q++) y[q] = Wadd(n, w[q], Wmul(n, cf[jj], b[q]));
            *ops += (uint64_t)R;
        }
        /* walk down to the last nonzero vector before A sends it to 0 */
        for (int step = 0; step <= e + 2; step++) {
            int nz = 0;
            for (int q = 0; q < R; q++) if (y[q]) { nz = 1; break; }
            if (!nz) break;
            mTx(n, &M, y, chk, ops);
            int zero = 1;
            for (int c = 0; c < C; c++) if (chk[c]) { zero = 0; break; }
            if (zero) { memcpy(out, y, sizeof(uint64_t) * R); success = 1; break; }
            applyA(n, &M, D, y, w, tmp, ops);
            memcpy(y, w, sizeof(uint64_t) * R);
        }
    }
    free(D); free(b); free(u); free(x); free(y); free(w); free(tmp); free(chk); free(seq); free(cf);
    return success;
}
