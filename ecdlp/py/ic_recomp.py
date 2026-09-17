"""ic_recomp.py -- re-run index calculus at the already-known optimal m for each size,
this time recording the three cost components separately (table / relations / linear
algebra).  Fitting the three-term model per component is far better conditioned than
fitting a sum of three nearly collinear basis functions to the total alone."""
import sys, os, json, glob, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolkit as T, indexcalc as IC

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "32"
    k, j = int(which[0]), int(which[1])
    path = os.path.join(T.DATA, f"ic_sweep_k{k}j{j}.json")
    rows = json.load(open(path))
    best = {}
    for r in rows:
        b = int(r["bits"])
        if b not in best or float(r["mean_ops"]) < float(best[b]["mean_ops"]):
            best[b] = r
    curves = {c.bits: c for c in T.load_curves() if c.idx == 0}
    out = []
    for b in sorted(best):
        m = int(best[b]["m"]); cur = curves[b]
        tg = T.make_targets(cur, 3, seed=900 + b)
        acc = {q: [] for q in ("fb", "tab", "rel", "la", "tot", "targets", "relations")}
        for i, t in enumerate(tg):
            r = IC.solve(cur, t.Q, m, k, j, seed=31 + 101 * i)
            assert r["ok"] and t.verify(r["k"]), (cur.name, m)
            acc["fb"].append(r["fb_ops"]); acc["tab"].append(r["tab_ops"])
            acc["rel"].append(r["rel_ops"]); acc["la"].append(r["la_ops"])
            acc["tot"].append(r["total_ops"]); acc["targets"].append(r["targets"])
            acc["relations"].append(r["relations"])
        rec = dict(curve=cur.name, bits=b, n=cur.n, k=k, j=j, m=m, ntarget=3,
                   mean_ops=statistics.mean(acc["tot"]),
                   **{f"mean_{q}": statistics.mean(v) for q, v in acc.items() if q != "tot"})
        out.append(rec)
        tot = rec["mean_ops"]
        print(f"  {cur.name:7s} m={m:5d}  table={rec['mean_tab']:12.4g} "
              f"({rec['mean_tab']/tot*100:4.1f}%)  relations={rec['mean_rel']:12.4g} "
              f"({rec['mean_rel']/tot*100:4.1f}%)  linalg={rec['mean_la']:12.4g} "
              f"({rec['mean_la']/tot*100:4.1f}%)  total={tot:12.4g}", flush=True)
    T.jdump(out, os.path.join(T.DATA, f"ic_comp_k{k}j{j}.json"))
    import math
    for q, lab in (("mean_tab", "table"), ("mean_rel", "relations"), ("mean_la", "lin.alg"),
                   ("mean_ops", "TOTAL")):
        xs = [r["n"] for r in out]; ys = [max(r[q], 1) for r in out]
        a, c, r2 = T.fit_loglog(xs, ys)
        print(f"  {lab:10s}: n^{a:.4f}  (r2={r2:.4f})   model: "
              f"{'n^%.4f' % (j/(2*j-1)) if lab in ('table','relations','TOTAL') else 'n^%.4f' % (2/(2*j-1))}")
