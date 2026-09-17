"""indexcalc.py -- driver and cost measurement for the prime-field index-calculus
attack.  The parameter (k, j) means: decompose into k factor-base points using a
precomputed table of j-fold sums and enumerating the remaining k-j with signs.

Predicted optimum (see ATTACK_LOG):  with a j-sum table and k = 2j,
    total = m^j + n/m^{j-1} + m^2   minimised at m = n^{1/(2j-1)},  total = n^{j/(2j-1)}
so the exponent is 1 (j=1), 2/3 (j=2), 3/5 (j=3), ... -> 1/2 from ABOVE.
Rho is n^{1/2} with negligible memory, so the prediction is that index calculus
never wins.  This file measures it instead of asserting it.
"""
from __future__ import annotations
import sys, os, ctypes, math, json, time, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolkit as T


class ICStats(ctypes.Structure):
    _fields_ = [("fb_ops", ctypes.c_uint64), ("tab_ops", ctypes.c_uint64),
                ("rel_ops", ctypes.c_uint64), ("la_ops", ctypes.c_uint64),
                ("targets", ctypes.c_uint64), ("relations", ctypes.c_uint64),
                ("table_size", ctypes.c_uint64),
                ("sec_fb", ctypes.c_double), ("sec_tab", ctypes.c_double),
                ("sec_rel", ctypes.c_double), ("sec_la", ctypes.c_double),
                ("ok", ctypes.c_int)]


_ic = None
def ic():
    global _ic
    if _ic is None:
        _ic = ctypes.CDLL(os.path.join(T.ROOT, "lib", "libic.so"))
        _ic.index_calculus.restype = ctypes.c_int
        _ic.index_calculus.argtypes = [ctypes.c_uint64] * 7 + [ctypes.c_int] * 3 + \
            [ctypes.c_uint64, ctypes.c_uint64,
             ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ICStats)]
    return _ic


def solve(cur, Q, m, k, j, seed=1, max_targets=1 << 40):
    kout = ctypes.c_uint64()
    st = ICStats()
    t0 = time.perf_counter()
    rc = ic().index_calculus(cur.p, cur.n, cur.b, cur.gx, cur.gy, Q.x, Q.y,
                             m, k, j, seed, max_targets, ctypes.byref(kout),
                             ctypes.byref(st))
    dt = time.perf_counter() - t0
    total = st.fb_ops + st.tab_ops + st.rel_ops + st.la_ops
    return dict(rc=rc, k=kout.value if st.ok else None, ok=bool(st.ok),
                m=m, kk=k, j=j, seconds=dt,
                fb_ops=st.fb_ops, tab_ops=st.tab_ops, rel_ops=st.rel_ops,
                la_ops=st.la_ops, targets=st.targets, relations=st.relations,
                table_size=st.table_size, total_ops=total,
                sec_fb=st.sec_fb, sec_tab=st.sec_tab, sec_rel=st.sec_rel, sec_la=st.sec_la)


def best_m(n, j, mmin=16, mmax=None, memcap=3 * 10 ** 7):
    """Minimise the modelled cost
         table        ~ m^j / j!
         relations    ~ n * m^{1-j}   (targets x per-target enumeration)
         linear alg.  ~ 26 m^2        (Wiedemann, constant measured in lib/libwied.so)
    subject to the j-sum table fitting in memory."""
    import math as _m
    best, bm = None, mmin
    mmax = mmax or int(memcap ** (1.0 / j)) + 1
    m = mmin
    while m <= mmax:
        tab = m ** j / _m.factorial(j)
        if m ** j > memcap:
            break
        cost = tab + n * m ** (1 - j) + 26.0 * m * m
        if best is None or cost < best:
            best, bm = cost, m
        m = int(m * 1.15) + 1
    return bm, best


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    if mode == "test":
        # correctness first: does it actually solve instances?
        bad = 0
        for cur in [c for c in T.load_curves() if c.bits in (20, 22, 24)]:
            for (k, j) in ((2, 1), (3, 2), (4, 2)):
                m, _ = best_m(cur.n, j, mmin=24, memcap=2 * 10 ** 6)
                m = max(24, min(m, 400))
                for t in T.make_targets(cur, 2, seed=5):
                    r = solve(cur, t.Q, m, k, j, seed=17)
                    good = r["ok"] and t.verify(r["k"])
                    if not good:
                        bad += 1
                        print(f"  FAIL {cur.name} k={k} j={j} m={m} rc={r['rc']} "
                              f"rel={r['relations']} targets={r['targets']}")
                    else:
                        print(f"  ok   {cur.name} k={k} j={j} m={m:4d} "
                              f"targets={r['targets']:8d} rel={r['relations']:4d} "
                              f"tab={r['table_size']:8d} total_ops={r['total_ops']:12d} "
                              f"{r['seconds']:.2f}s", flush=True)
        print("INDEX CALCULUS CORRECTNESS:", "OK" if bad == 0 else f"{bad} FAILURES")
