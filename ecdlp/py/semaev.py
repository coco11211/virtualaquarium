"""semaev.py -- Semaev summation polynomials for y^2 = x^3 + a x + b.

S_m(X1,...,Xm) = 0  <=>  there exist y_i with sum_i (X_i, y_i) = O on E.

  S_2(X1,X2)    = X1 - X2
  S_3(X1,X2,X3) = (X1-X2)^2 X3^2
                  - 2((X1+X2)(X1X2+a) + 2b) X3
                  + ((X1X2 - a)^2 - 4b(X1+X2))
  S_m           = Res_X( S_{m-1}(X1..X_{m-2}, X), S_3(X_{m-1}, X_m, X) )   (m >= 4)

deg_{X_i} S_m = 2^{m-2}.
"""
from __future__ import annotations
import os, pickle, sympy as sp

CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "semaev")


def xs(m):
    return sp.symbols(f"x1:{m+1}")


def S3(X1, X2, X3, a, b):
    return sp.expand((X1 - X2) ** 2 * X3 ** 2
                     - 2 * ((X1 + X2) * (X1 * X2 + a) + 2 * b) * X3
                     + ((X1 * X2 - a) ** 2 - 4 * b * (X1 + X2)))


def build(m, a=0, b=7, verbose=False):
    """Return S_m as a sympy Poly in x1..xm."""
    V = xs(m)
    X = sp.Symbol("_X")
    if m == 2:
        return sp.Poly(V[0] - V[1], *V)
    if m == 3:
        return sp.Poly(S3(V[0], V[1], V[2], a, b), *V)
    prev = build(m - 1, a, b)                      # in x1..x_{m-1}
    Vp = xs(m - 1)
    f = prev.as_expr().subs(Vp[m - 2], X)           # replace its last var by X
    g = S3(V[m - 2], V[m - 1], X, a, b)
    r = sp.resultant(sp.Poly(sp.expand(f), X), sp.Poly(sp.expand(g), X))
    P = sp.Poly(sp.expand(r), *V)
    # the iterated resultant carries an extraneous square factor; remove repeated
    # factors so that S_m is the true summation polynomial
    P = sp.Poly(sp.prod([fac for fac, _ in sp.factor_list(P.as_expr())[1]]), *V) \
        if m >= 4 else P
    if verbose:
        print(f"S_{m}: {len(P.terms())} terms, degrees {[sp.degree(P, v) for v in V]}")
    return P


def get(m, a=0, b=7, rebuild=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"S{m}_a{a}_b{b}.pkl")
    if os.path.exists(path) and not rebuild:
        with open(path, "rb") as f:
            return pickle.load(f)
    P = build(m, a, b)
    with open(path, "wb") as f:
        pickle.dump(P, f)
    return P


# ---------------------------------------------------------------- verification
def verify(m, curve, ntrial=15, seed=11):
    """S_m must vanish exactly on x-coordinate tuples of points summing to O."""
    import random, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import toolkit as T
    rng = random.Random(seed)
    E = T.EC(curve.p, 7, n=curve.n)
    G = curve.G()
    P = get(m, 0, 7)
    V = xs(m)
    p = curve.p
    d = P.as_dict()
    def ev(Xv):
        acc = 0
        for mono, coef in d.items():
            t = int(coef) % p
            for e, xv in zip(mono, Xv):
                if e: t = t * pow(xv, e, p) % p
            acc = (acc + t) % p
        return acc
    ok_pos = ok_neg = skipped = 0
    for _ in range(ntrial):
        ks = [rng.randrange(1, curve.n) for _ in range(m - 1)]
        pts = [E.mul(k, G) for k in ks]
        last = E.neg(E.mul(sum(ks) % curve.n, G))
        if last.inf or any(q.inf for q in pts):
            skipped += 1
            continue
        Xv = [q.x for q in pts] + [last.x]
        if ev(Xv) != 0:
            print(f"  S_{m} FAILED to vanish on a genuine relation")
            return False
        ok_pos += 1
        Xv2 = list(Xv); Xv2[0] = (Xv2[0] + rng.randrange(1, p)) % p
        if ev(Xv2) != 0:
            ok_neg += 1
    print(f"  S_{m}: vanished on {ok_pos}/{ok_pos+skipped} true relations, "
          f"nonzero on {ok_neg}/{ok_pos} perturbed tuples")
    return ok_pos > 0 and ok_neg >= ok_pos - 1


if __name__ == "__main__":
    import sys, time
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import toolkit as T
    mmax = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    cur = [c for c in T.load_curves() if c.bits == 20][0]
    for m in range(3, mmax + 1):
        t0 = time.time()
        P = get(m, 0, 7, rebuild=True)
        V = xs(m)
        print(f"S_{m}: built in {time.time()-t0:.1f}s, {len(P.terms())} terms, "
              f"deg/var {[sp.degree(P, v) for v in V]}, total deg {sp.total_degree(P.as_expr())}", flush=True)
        verify(m, cur, ntrial=12)
