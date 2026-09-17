"""mu6_graded.py -- does the j=0 automorphism group lower the ALGEBRAIC complexity of
Semaev decomposition, or only the constants?

The order-3 automorphism is (x,y) -> (beta x, y) = lambda*(x,y), so if P_1+...+P_k = O
then lambda P_1 + ... + lambda P_k = O too.  The solution set of S_k is therefore stable
under the DIAGONAL action x_i -> beta x_i, and S_k must be homogeneous for a mu_3 grading.
The claim to test is that re-grading by this action lowers the solving complexity.

Three measurements:
  G1  Confirm the grading and find the weight: S_k(beta x_1,...,beta x_k) = beta^w S_k.
      Equivalently, every monomial of S_k has total degree = w (mod 3).
  G2  Graded density of the ELIMINANT.  IC2 found the eliminant
      E(x1,x2) = prod_{s in S} S_4(x1,x2,s,x_R) is 100% dense.  If S is mu_3-stable, does
      E concentrate on one residue class of (e1+e2) mod 3?  That would be a genuine (but
      constant-factor) sparsity of 1/3.
  G3  Orbit reduction.  Working in E/<lambda> shrinks the factor base by 3 and the
      k-tuple space by 3^k.  Measure the exact factor -- it is a constant, and constants
      do not move exponents, but the size of the constant is worth knowing.
"""
from __future__ import annotations
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import toolkit as T
import semaev, eliminant as EL


def g1_grading():
    print("G1  grading of the summation polynomials under x_i -> beta x_i")
    out = []
    for k in (3, 4):
        P = semaev.get(k, 0, 7)
        degs = {}
        for mono, coef in P.as_dict().items():
            if int(coef) == 0:
                continue
            degs.setdefault(sum(mono) % 3, 0)
            degs[sum(mono) % 3] += 1
        graded = len(degs) == 1
        w = list(degs)[0] if graded else None
        print(f"  S_{k}: monomials by (total degree mod 3): {dict(sorted(degs.items()))}"
              f"   -> {'GRADED, weight ' + str(w) if graded else 'NOT graded'}")
        out.append(dict(k=k, classes=degs, graded=graded, weight=w))
    print("  consequence: the solution set is a union of mu_3-orbits, so an orbit-reduced")
    print("  factor base covers the same relations with m/3 elements.  That is a CONSTANT.")
    return out


def g2_graded_density():
    print("\nG2  graded density of the eliminant  E(x1,x2) = prod_{s in S} S_4(x1,x2,s,x_R)")
    S4 = semaev.get(4, 0, 7).as_dict()
    rows = []
    curves = [c for c in T.load_curves(os.path.join(T.DATA, "curves_small.json"))
              if 11 <= c.bits <= 15] + [c for c in T.load_curves() if c.bits == 20][:1]
    for cur in curves:
        p = cur.p
        g = EL.prim_root(p)
        rng = random.Random(17 + cur.bits)
        xr = T.c_mul(cur, rng.randrange(1, cur.n), cur.G()).x
        for m in EL.divisors(p - 1, 6, 40):
            if m % 3:
                continue                      # need mu_3 <= mu_m for the set to be stable
            gg = pow(g, (p - 1) // m, p)
            mu, v = [], 1
            for _ in range(m):
                mu.append(v); v = v * gg % p
            E = EL.eliminant(mu, S4, p, xr)
            nz = np.nonzero(E)
            cls = np.zeros(3, dtype=int)
            for a, b in zip(*nz):
                cls[(a + b) % 3] += 1
            tot = int(cls.sum())
            # control: a random set of the same size (not mu_3-stable)
            rnd = [rng.randrange(1, p) for _ in range(m)]
            Er = EL.eliminant(rnd, S4, p, xr)
            nzr = np.nonzero(Er)
            clsr = np.zeros(3, dtype=int)
            for a, b in zip(*nzr):
                clsr[(a + b) % 3] += 1
            r = dict(curve=cur.name, m=m, shape=list(E.shape), total_nnz=tot,
                     classes=[int(z) for z in cls], max_class_share=float(cls.max() / max(tot, 1)),
                     rand_total=int(clsr.sum()),
                     rand_max_share=float(clsr.max() / max(clsr.sum(), 1)),
                     dense=int(E.size), density=tot / E.size)
            rows.append(r)
            print(f"  {cur.name:6s} m={m:3d}  nnz={tot:6d}/{E.size:6d} (density {r['density']:.3f})"
                  f"  by (e1+e2) mod 3: {list(cls)}  max share {r['max_class_share']:.3f}"
                  f"   || random S max share {r['rand_max_share']:.3f}", flush=True)
    print("  a mu_3-induced sparsity would show max share ~ 1.000 with the other two classes")
    print("  empty (density 1/3).  Equal thirds means no graded sparsity.")
    return rows


def g3_orbit_reduction():
    print("\nG3  orbit reduction: how much does working in E/<lambda,-1> actually save?")
    rows = []
    for cur in [c for c in T.load_curves() if c.bits in (24, 28, 32)]:
        p, b1 = cur.p, cur.beta % cur.p
        b2 = b1 * b1 % p
        rng = random.Random(5 + cur.bits)
        xs = set()
        N = 40000
        for _ in range(N):
            k = rng.randrange(1, cur.n)
            Q = T.c_mul(cur, k, cur.G())
            if Q.inf:
                continue
            xs.add(min(Q.x, Q.x * b1 % p, Q.x * b2 % p))
        # how many distinct orbit representatives did N samples produce?
        reps = len(xs)
        # the classes have size 3 (generic), so the reduced space is (n-1)/6
        exp_space = (cur.n - 1) / 6
        coll = N - reps
        rows.append(dict(curve=cur.name, samples=N, distinct_reps=reps,
                         reduced_space=exp_space, collisions=coll))
        print(f"  {cur.name:7s} {N} samples -> {reps} distinct orbit representatives;"
              f"  reduced space (n-1)/6 = {exp_space:.3g}")
    print("  factor-base saving is exactly 6 (3 from lambda, 2 from negation): a CONSTANT.")
    print("  Cost scales as m^j and n*m^(1-j); replacing m by m/6 rescales by 6^j and 6^(j-1),")
    print("  i.e. a constant factor.  The exponent j/(2j-1) is unchanged.")
    return rows


if __name__ == "__main__":
    res = dict(G1=g1_grading(), G2=g2_graded_density(), G3=g3_orbit_reduction())
    T.jdump(res, os.path.join(T.DATA, "mu6_graded.json"))
    print("\nsaved")
