"""eliminant.py -- the last open door in prime-field index calculus.

K1 killed the COMBINATORIAL (birthday / k-tree) decomposition oracle.  The other
family is ALGEBRAIC: given x_R, solve
        S_{k+1}(x_1,...,x_k, x_R) = 0     with all x_i in a structured set S
by elimination.  Over F_{q^n} Weil descent makes this cheap; over F_p there is no
descent, so the question is whether some algebraic S makes the ELIMINANT small.

For k = 2 the eliminant is  E(x_1) = prod_{s in S} S_3(x_1, s, x_R),  of degree 2|S|,
computable by a product tree in Otilde(|S|) -- for ANY S, structured or not.  That
already ties brute force (scan S, solve a quadratic), so k = 2 settles nothing and
in any case k = 2 index calculus is Theta(n).

For k = 3 the eliminant is  E(x_1,x_2) = prod_{s in S} S_4(x_1, x_2, s, x_R),  of
bidegree (4|S|, 4|S|).  Its DENSE size is ~16|S|^2, which is already brute force.
The only way an algebraic oracle can win is if E is SPARSE for some structured S --
i.e. if the structure makes almost all coefficients vanish.

So this file measures exactly one number: the density of the eliminant, for
S = mu_m (the canonical intermediate-size algebraic subset of F_p, which is also the
one with the richest structure) against a random control set of the same size.

The counting target from ATTACK_LOG: the decomposition oracle needs exponent
theta <= k-3 in |S|, while brute force is theta = k-1.  At k = 3 that means the
eliminant would have to be built in time |S|^0, i.e. essentially free.
"""
from __future__ import annotations
import sys, os, json, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import toolkit as T
import semaev


def polmul2(A, B, p):
    """bivariate polynomial multiplication mod p (numpy 2-D coefficient arrays)"""
    n1, m1 = A.shape; n2, m2 = B.shape
    C = np.zeros((n1 + n2 - 1, m1 + m2 - 1), dtype=np.int64)
    for i in range(n1):
        Ai = A[i]
        nz = np.nonzero(Ai)[0]
        if nz.size == 0:
            continue
        for j in nz:
            a = int(Ai[j])
            C[i:i + n2, j:j + m2] = (C[i:i + n2, j:j + m2] + a * B) % p
    return C % p


def s4_slice(S4dict, p, zeta, xr):
    """S_4(x1, x2, zeta, xr) as a bivariate coefficient array over F_p"""
    d = np.zeros((5, 5), dtype=np.int64)
    for mono, coef in S4dict.items():
        e1, e2, e3, e4 = mono
        v = int(coef) % p
        if v == 0:
            continue
        v = v * pow(int(zeta), int(e3), p) % p
        v = v * pow(int(xr), int(e4), p) % p
        d[e1, e2] = (d[e1, e2] + v) % p
    return d


def eliminant(S, S4dict, p, xr):
    """product tree of S_4(x1,x2,s,xr) over s in S"""
    polys = [s4_slice(S4dict, p, s, xr) for s in S]
    while len(polys) > 1:
        nxt = []
        for i in range(0, len(polys) - 1, 2):
            nxt.append(polmul2(polys[i], polys[i + 1], p))
        if len(polys) % 2:
            nxt.append(polys[-1])
        polys = nxt
    return polys[0]


def divisors(N, lo, hi):
    out, i = set(), 1
    while i * i <= N:
        if N % i == 0:
            out.add(i); out.add(N // i)
        i += 1
    return sorted(d for d in out if lo <= d <= hi)


def prim_root(p):
    fac, M, i = [], p - 1, 2
    while i * i <= M:
        if M % i == 0:
            fac.append(i)
            while M % i == 0:
                M //= i
        i += 1
    if M > 1:
        fac.append(M)
    for g in range(2, 5000):
        if all(pow(g, (p - 1) // q, p) != 1 for q in fac):
            return g
    raise RuntimeError


if __name__ == "__main__":
    S4 = semaev.get(4, 0, 7)
    S4dict = S4.as_dict()
    rows = []
    import random
    curves = [c for c in T.load_curves(os.path.join(T.DATA, "curves_small.json"))
              if 11 <= c.bits <= 15] + [c for c in T.load_curves() if c.bits == 20][:1]
    for cur in curves:
        p = cur.p
        g = prim_root(p)
        rng = random.Random(9 + cur.bits)
        xr = T.c_mul(cur, rng.randrange(1, cur.n), cur.G()).x
        for m in divisors(p - 1, 4, 40):
            gg = pow(g, (p - 1) // m, p)
            mu = []
            v = 1
            for _ in range(m):
                mu.append(v); v = v * gg % p
            t0 = time.time()
            Emu = eliminant(mu, S4dict, p, xr)
            tmu = time.time() - t0
            rnd = [rng.randrange(1, p) for _ in range(m)]
            t0 = time.time()
            Ern = eliminant(rnd, S4dict, p, xr)
            trn = time.time() - t0
            dens_mu = int(np.count_nonzero(Emu)); dens_rn = int(np.count_nonzero(Ern))
            dense = Emu.size
            r = dict(curve=cur.name, p=p, m=m, shape=list(Emu.shape),
                     dense_size=dense, nnz_mu=dens_mu, nnz_rand=dens_rn,
                     density_mu=dens_mu / dense, density_rand=dens_rn / dense,
                     sec_mu=tmu, sec_rand=trn)
            rows.append(r)
            print(f"  {cur.name:6s} p=2^{p.bit_length():2d} m={m:3d} eliminant {Emu.shape}"
                  f"  nnz(mu_m)={dens_mu:6d}/{dense:6d} ({r['density_mu']:.3f})"
                  f"   nnz(random)={dens_rn:6d} ({r['density_rand']:.3f})", flush=True)
    T.jdump(rows, os.path.join(T.DATA, "eliminant.json"))
    if rows:
        ms = [r["m"] for r in rows]; nz = [r["nnz_mu"] for r in rows]
        a, c, r2 = T.fit_loglog(ms, nz)
        a2, c2, r22 = T.fit_loglog(ms, [r["nnz_rand"] for r in rows])
        print(f"\n  nonzero coefficients of the eliminant:")
        print(f"    S = mu_m  : nnz ~ m^{a:.3f}   (r2={r2:.4f})")
        print(f"    S = random: nnz ~ m^{a2:.3f}   (r2={r22:.4f})")
        print(f"  dense would be m^2.  theta <= k-3 = 0 is what an algebraic win needs.")
