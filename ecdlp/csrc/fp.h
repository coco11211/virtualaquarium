/* fp.h -- Montgomery arithmetic mod an odd prime p < 2^63, and arithmetic on
   the toy curves y^2 = x^3 + b over F_p.  All values are stored in Montgomery
   form (a*R mod p, R = 2^64) except where explicitly noted.

   Constraint p < 2^63 keeps REDC free of 128-bit overflow:
     a*b <= (p-1)^2 < 2^126 and m*p < 2^64 * 2^63 = 2^127, sum < 2^128.  */
#ifndef FP_H
#define FP_H
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

typedef unsigned __int128 u128;

typedef struct {
    uint64_t p;     /* the prime, p < 2^63                       */
    uint64_t np;    /* -p^{-1} mod 2^64                          */
    uint64_t r1;    /* R   mod p  (= Montgomery form of 1)       */
    uint64_t r2;    /* R^2 mod p  (to enter Montgomery form)     */
    uint64_t b;     /* curve constant b, Montgomery form         */
} fp_ctx;

static inline uint64_t inv64(uint64_t a) {           /* a^{-1} mod 2^64, a odd */
    uint64_t x = a;                                  /* 3 bits correct */
    for (int i = 0; i < 5; i++) x *= 2 - a * x;      /* Newton: 3,6,12,24,48,96 */
    return x;
}

static inline uint64_t mont_mul(const fp_ctx *c, uint64_t a, uint64_t b) {
    u128 t = (u128)a * b;
    uint64_t m = (uint64_t)t * c->np;
    t += (u128)m * c->p;
    uint64_t r = (uint64_t)(t >> 64);
    return r >= c->p ? r - c->p : r;
}
static inline uint64_t mont_add(const fp_ctx *c, uint64_t a, uint64_t b) {
    uint64_t r = a + b;
    return r >= c->p ? r - c->p : r;
}
static inline uint64_t mont_sub(const fp_ctx *c, uint64_t a, uint64_t b) {
    return a >= b ? a - b : a + c->p - b;
}
static inline uint64_t mont_neg(const fp_ctx *c, uint64_t a) {
    return a ? c->p - a : 0;
}
static inline uint64_t to_mont(const fp_ctx *c, uint64_t a)   { return mont_mul(c, a % c->p, c->r2); }
static inline uint64_t from_mont(const fp_ctx *c, uint64_t a) { return mont_mul(c, a, 1); }

static inline uint64_t mont_pow(const fp_ctx *c, uint64_t a, uint64_t e) {
    uint64_t r = c->r1;
    while (e) { if (e & 1) r = mont_mul(c, r, a); a = mont_mul(c, a, a); e >>= 1; }
    return r;
}
/* p is prime so a^(p-2) = a^{-1}.  Returns 0 for a = 0. */
static inline uint64_t mont_inv(const fp_ctx *c, uint64_t a) {
    return a ? mont_pow(c, a, c->p - 2) : 0;
}

static inline void fp_init(fp_ctx *c, uint64_t p, uint64_t b_std) {
    c->p  = p;
    c->np = (uint64_t)(0 - inv64(p));                 /* -p^{-1} mod 2^64 */
    /* R mod p = 2^64 mod p */
    c->r1 = (uint64_t)(((u128)1 << 64) % p);
    /* R^2 mod p by repeated doubling of R */
    uint64_t t = c->r1;
    for (int i = 0; i < 64; i++) { t += t; if (t >= p) t -= p; }
    c->r2 = t;
    c->b  = to_mont(c, b_std);
}

/* ---------------- affine points on y^2 = x^3 + b ---------------- */
typedef struct { uint64_t x, y; int inf; } ecpt;          /* Montgomery coords */

static inline int ec_on_curve(const fp_ctx *c, const ecpt *P) {
    if (P->inf) return 1;
    uint64_t l = mont_mul(c, P->y, P->y);
    uint64_t r = mont_add(c, mont_mul(c, mont_mul(c, P->x, P->x), P->x), c->b);
    return l == r;
}
static inline void ec_neg(const fp_ctx *c, const ecpt *P, ecpt *R) {
    R->x = P->x; R->y = mont_neg(c, P->y); R->inf = P->inf;
}
/* full affine add with inversion (slow path / correctness reference) */
static void ec_add(const fp_ctx *c, const ecpt *P, const ecpt *Q, ecpt *R) {
    if (P->inf) { *R = *Q; return; }
    if (Q->inf) { *R = *P; return; }
    uint64_t lam;
    if (P->x == Q->x) {
        if (P->y != Q->y || P->y == 0) { R->inf = 1; R->x = R->y = 0; return; }
        uint64_t x2  = mont_mul(c, P->x, P->x);
        uint64_t num = mont_add(c, mont_add(c, x2, x2), x2);     /* 3x^2 (a = 0) */
        uint64_t den = mont_add(c, P->y, P->y);
        lam = mont_mul(c, num, mont_inv(c, den));
    } else {
        uint64_t num = mont_sub(c, Q->y, P->y);
        uint64_t den = mont_sub(c, Q->x, P->x);
        lam = mont_mul(c, num, mont_inv(c, den));
    }
    uint64_t xr = mont_sub(c, mont_sub(c, mont_mul(c, lam, lam), P->x), Q->x);
    uint64_t yr = mont_sub(c, mont_mul(c, lam, mont_sub(c, P->x, xr)), P->y);
    R->x = xr; R->y = yr; R->inf = 0;
}
static void ec_mul(const fp_ctx *c, const ecpt *P, uint64_t k, ecpt *R) {
    ecpt acc, base = *P;
    acc.inf = 1; acc.x = acc.y = 0;
    while (k) {
        if (k & 1) { ecpt t; ec_add(c, &acc, &base, &t); acc = t; }
        { ecpt t; ec_add(c, &base, &base, &t); base = t; }
        k >>= 1;
    }
    *R = acc;
}
#endif
