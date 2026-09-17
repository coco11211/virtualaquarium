"""sat_scaling.py -- measure the real scaling exponent of SAT/SMT on the ECDLP.

Non-generic structure used: the bit-level circuit representation of F_p arithmetic.
A generic-group algorithm cannot see it; a solver can, in principle, propagate
through it.

Encoding (Z3, bitvectors, width 2*bits+8 so products never overflow):
  scalar k as a bitvector; a double-and-add chain of `bits` steps in AFFINE
  coordinates with division replaced by a multiplication constraint
        lam * (x2 - x1) == (y2 - y1)   (mod p)
  which avoids encoding modular inversion.  Degenerate steps (x1 == x2) are
  excluded by asserting x1 != x2 and handled by the chain structure: we use the
  fixed-window form  Q = sum_i b_i * (2^i G)  with all multiples of G PRECOMPUTED
  as constants, so every addition is a generic addition of a variable point and a
  constant point.  Only the b_i are unknown.

That is the friendliest honest encoding: the solver is handed the whole algebraic
structure and only has to find `bits` boolean unknowns.

Baselines to beat: brute force is alpha = 1.0 in  log2(time) = alpha * bits + c;
rho is alpha = 0.5.  Kill criterion: fitted alpha >= 0.5 with no improvement from
the special prime shape or the endomorphism.
"""
from __future__ import annotations
import sys, os, time, json, math, signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolkit as T
import z3


def encode(cur, Q, timeout_s=600, use_endo=False):
    p, n = cur.p, cur.n
    W = 2 * p.bit_length() + 8
    B = n.bit_length()
    E = T.EC(p, 7, n=n)
    G = cur.G()

    def C(v):
        return z3.BitVecVal(v % p, W)

    P = z3.BitVecVal(p, W)
    s = z3.Solver()
    s.set("timeout", int(timeout_s * 1000))

    bits = [z3.Bool(f"b{i}") for i in range(B)]
    # precomputed constants 2^i * G
    mults = []
    acc = G
    for i in range(B):
        mults.append(acc)
        acc = E.add(acc, acc)

    def mod(e):
        return z3.URem(e, P)

    # running sum, with a "is infinity" flag
    curx = z3.BitVec("x0", W); cury = z3.BitVec("y0", W); curinf = z3.Bool("inf0")
    s.add(curx == 0, cury == 0, curinf == True)
    for i in range(B):
        Mi = mults[i]
        nx = z3.BitVec(f"x{i+1}", W); ny = z3.BitVec(f"y{i+1}", W)
        ninf = z3.Bool(f"inf{i+1}")
        lam = z3.BitVec(f"l{i}", W)
        s.add(z3.ULT(nx, P), z3.ULT(ny, P), z3.ULT(lam, P))
        # case bit = 0 : carry the accumulator unchanged
        keep = z3.And(nx == curx, ny == cury, ninf == curinf)
        # case bit = 1 and accumulator = O : the result is the constant
        setc = z3.And(nx == C(Mi.x), ny == C(Mi.y), ninf == False)
        # case bit = 1 and accumulator != O : a generic addition
        #   lam*(Mx - x) = (My - y),  nx = lam^2 - x - Mx,  ny = lam*(x - nx) - y
        dx = mod(C(Mi.x) + P - curx)
        dy = mod(C(Mi.y) + P - cury)
        gen = z3.And(mod(lam * dx) == dy,
                     nx == mod(mod(lam * lam) + 2 * P - curx - C(Mi.x)),
                     ny == mod(mod(lam * mod(curx + P - nx)) + P - cury),
                     ninf == False,
                     curx != C(Mi.x))
        s.add(z3.If(z3.Not(bits[i]), keep,
                    z3.If(curinf, setc, gen)))
        curx, cury, curinf = nx, ny, ninf
    s.add(curinf == False, curx == C(Q.x), cury == C(Q.y))
    return s, bits, B


def run(bits_list=(8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22), ntarget=3, timeout_s=900):
    rows = []
    allc = T.load_curves(os.path.join(T.DATA, 'curves_small.json')) + T.load_curves()
    for b in bits_list:
        cands = [c for c in allc if c.bits == b]
        if not cands:
            # generate an ad-hoc small curve with PARI if the size is not in the set
            continue
        cur = cands[0]
        for ti, t in enumerate(T.make_targets(cur, ntarget, seed=4000 + b)):
            s, bitvars, B = encode(cur, t.Q, timeout_s=timeout_s)
            t0 = time.perf_counter()
            res = s.check()
            dt = time.perf_counter() - t0
            solved = (res == z3.sat)
            kk = None
            if solved:
                mdl = s.model()
                kk = sum((1 << i) for i in range(B)
                         if z3.is_true(mdl.eval(bitvars[i], model_completion=True)))
            ok = solved and t.verify(kk)
            rows.append(dict(bits=b, curve=cur.name, target=ti, seconds=dt,
                             status=str(res), solved=bool(solved), correct=bool(ok),
                             n=cur.n))
            print(f"  bits={b:3d} target{ti} {str(res):8s} {dt:9.2f}s  correct={ok}",
                  flush=True)
            if dt > timeout_s * 0.95:
                break
        T.jdump(rows, os.path.join(T.DATA, "sat_scaling.json"))
        med = sorted(r["seconds"] for r in rows if r["bits"] == b)
        if med and med[len(med)//2] > timeout_s * 0.9:
            print(f"  -> hit the {timeout_s}s wall at {b} bits; stopping", flush=True)
            break
    return rows


if __name__ == "__main__":
    tl = int(sys.argv[1]) if len(sys.argv) > 1 else 900
    rows = run(timeout_s=tl)
    import numpy as np
    okrows = [r for r in rows if r["correct"]]
    if len(okrows) >= 6:
        byb = {}
        for r in okrows:
            byb.setdefault(r["bits"], []).append(r["seconds"])
        xs = sorted(byb)
        ys = [float(np.median(byb[b])) for b in xs]
        A = np.vstack([np.array(xs, float), np.ones(len(xs))]).T
        (al, c), *_ = np.linalg.lstsq(A, np.log2(ys), rcond=None)
        print(f"\nfit: log2(seconds) = {al:.4f} * bits + {c:.3f}")
        print(f"  brute force would be 1.0 (per bit of n), rho 0.5")
        print(f"  projection to 256 bits: 2^{al*256+c:.1f} seconds")
