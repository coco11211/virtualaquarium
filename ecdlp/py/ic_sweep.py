"""ic_sweep.py -- measure the real cost scaling of prime-field index calculus.

For each (k, j) and each curve size we sweep the factor-base size m, measure the
TOTAL operation count (factor base + sum table + relation search + linear
algebra) on several hidden targets, take the empirical optimum over m, and fit
  log2(total_ops) = alpha * log2(n) + c.
alpha is then compared with rho's measured 0.503.
"""
from __future__ import annotations
import sys, os, math, json, time, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolkit as T
import indexcalc as IC

CONFIGS = [
    # (k, j, label, max curve bits, memory cap on the table, m grid cap)
    (2, 1, "k=2, j=1 (meet-in-the-middle)", 28, 10 ** 6, 4000),
    (3, 2, "k=3, j=2 (2-sum table)",        36, 2 * 10 ** 7, 5000),
    (4, 2, "k=4, j=2 (2-sum table)",        36, 2 * 10 ** 7, 5000),
    (6, 3, "k=6, j=3 (3-sum table)",        36, 4 * 10 ** 7, 400),
]


def mgrid(n, j, memcap, mcap):
    m0, _ = IC.best_m(n, j, mmin=16, memcap=memcap)
    g = sorted({max(16, min(mcap, int(m0 * f))) for f in (0.4, 0.6, 0.8, 1.0, 1.3, 1.8, 2.5)})
    return [m for m in g if m ** j <= memcap]


def run(k, j, label, maxbits, memcap, mcap, ntarget=3, tag=""):
    rows = []
    for cur in T.load_curves():
        if cur.bits > maxbits or cur.idx != 0:
            continue
        tgts = T.make_targets(cur, ntarget, seed=900 + cur.bits)
        best = None
        for m in mgrid(cur.n, j, memcap, mcap):
            ops, secs, okall = [], [], True
            comp = dict(fb=[], tab=[], rel=[], la=[], targets=[], relations=[], tabsz=[])
            for i, t in enumerate(tgts):
                r = IC.solve(cur, t.Q, m, k, j, seed=31 + 101 * i,
                             max_targets=1 << 40)
                if not (r["ok"] and t.verify(r["k"])):
                    okall = False
                    break
                ops.append(r["total_ops"]); secs.append(r["seconds"])
                comp["fb"].append(r["fb_ops"]); comp["tab"].append(r["tab_ops"])
                comp["rel"].append(r["rel_ops"]); comp["la"].append(r["la_ops"])
                comp["targets"].append(r["targets"]); comp["relations"].append(r["relations"])
                comp["tabsz"].append(r["table_size"])
            if not okall:
                continue
            rec = dict(curve=cur.name, bits=cur.bits, n=cur.n, k=k, j=j, m=m,
                       mean_ops=statistics.mean(ops), mean_sec=statistics.mean(secs),
                       ntarget=len(ops),
                       **{f"mean_{q}": statistics.mean(v) for q, v in comp.items()})
            rows.append(rec)
            if best is None or rec["mean_ops"] < best["mean_ops"]:
                best = rec
            print(f"  {cur.name:7s} k={k} j={j} m={m:5d}  ops={rec['mean_ops']:14.0f}"
                  f"  {rec['mean_sec']:7.2f}s", flush=True)
        T.jdump(rows, os.path.join(T.DATA, f"ic_sweep_k{k}j{j}{tag}.json"))
        if best:
            print(f"  -> {cur.name} BEST m={best['m']} ops={best['mean_ops']:.4g}"
                  f"   rho_endo={T.rho_bar(cur.n):.4g}", flush=True)
    T.jdump(rows, os.path.join(T.DATA, f"ic_sweep_k{k}j{j}{tag}.json"))
    return rows


if __name__ == "__main__":
    sel = sys.argv[1] if len(sys.argv) > 1 else "all"
    for (k, j, label, mb, mc, mcap) in CONFIGS:
        if sel != "all" and sel != f"{k}{j}":
            continue
        print(f"\n=== {label} ===", flush=True)
        run(k, j, label, mb, mc, mcap)
