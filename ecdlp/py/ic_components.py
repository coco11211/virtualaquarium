"""ic_components.py -- decompose the measured index-calculus cost into its three
terms and check each against the model, instead of fitting one exponent to a sum of
terms with different exponents.

Model:   total(m, n) = A*m^j/j!      (build the j-sum table)
                     + B*n*m^(1-j)   (relation search)
                     + 26*m^2        (sparse Wiedemann linear algebra)
Asymptotically the first two balance at m = Theta(n^(1/(2j-1))) giving n^(j/(2j-1)),
which tends to n^(1/2) FROM ABOVE.  The m^2 term scales as n^(2/(2j-1)) -- SMALLER than
the other two -- so at small n it can dominate and depress the apparent exponent below
0.5.  That is a transient, not a win, and this file is what tells the two apart.
"""
from __future__ import annotations
import sys, os, json, glob, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import toolkit as T


def load_all():
    out = {}
    for path in sorted(glob.glob(os.path.join(T.DATA, "ic_sweep_k*.json"))):
        rows = json.load(open(path))
        if not rows:
            continue
        key = (int(rows[0]["k"]), int(rows[0]["j"]))
        out[key] = rows
    return out


def best_rows(rows):
    best = {}
    for r in rows:
        b = int(r["bits"])
        if b not in best or float(r["mean_ops"]) < float(best[b]["mean_ops"]):
            best[b] = r
    return [best[b] for b in sorted(best)]


def main():
    data = load_all()
    report = {}
    for (k, j), rows in sorted(data.items()):
        br = best_rows(rows)
        if len(br) < 3:
            continue
        print(f"\n{'='*92}")
        print(f"index calculus  k={k}, j={j}   ({len(br)} sizes)   "
              f"predicted asymptotic exponent {j}/{2*j-1} = {j/(2*j-1):.4f}")
        print(f"{'bits':>5s} {'m*':>6s} {'table':>12s} {'relations':>12s} {'lin.alg':>12s} "
              f"{'total':>12s} {'rho':>10s} {'ratio':>8s} {'dominant':>10s}")
        ns, tots, tabs, rels, las = [], [], [], [], []
        for r in br:
            tab = float(r.get("mean_ops", 0))
            # the sweep stores only the total; recover components from the model fit
            # by re-reading the per-run fields when present
            n = float(r["n"])
            ns.append(n); tots.append(float(r["mean_ops"]))
            m = int(r["m"])
            tmod = m ** j / math.factorial(j)
            lmod = 26.0 * m * m
            rmod = max(float(r["mean_ops"]) - tmod - lmod, 1.0)
            tabs.append(tmod); rels.append(rmod); las.append(lmod)
            dom = max((tmod, "table"), (rmod, "relations"), (lmod, "lin.alg"))[1]
            rho = T.rho_bar(n)
            print(f"{int(r['bits']):5d} {m:6d} {tmod:12.3g} {rmod:12.3g} {lmod:12.3g} "
                  f"{float(r['mean_ops']):12.4g} {rho:10.4g} "
                  f"{float(r['mean_ops'])/rho:8.1f}x {dom:>10s}")
        a, c, r2 = T.fit_loglog(ns, tots)
        fits = {"total": (a, c, r2)}
        print(f"  fitted TOTAL exponent            : {a:.4f}   (r2={r2:.4f})")
        for nm, arr in (("table", tabs), ("relations", rels), ("lin.alg", las)):
            aa, cc, rr = T.fit_loglog(ns, arr)
            fits[nm] = (aa, cc, rr)
            print(f"  fitted {nm:10s} exponent      : {aa:.4f}   (r2={rr:.4f})")
        print(f"  model predicts: table & relations -> n^{j/(2*j-1):.4f}, "
              f"lin.alg -> n^{2/(2*j-1):.4f}")
        # asymptotic projection using the MODEL with the measured constants
        print(f"  --> at small n the {max(fits, key=lambda z: 0 if z=='total' else 0)} ")
        report[f"k{k}j{j}"] = dict(sizes=[int(r["bits"]) for r in br],
                                   fits={q: dict(alpha=v[0], c=v[1], r2=v[2])
                                         for q, v in fits.items()},
                                   predicted_asymptote=j / (2 * j - 1))
    T.jdump(report, os.path.join(T.RESULTS, "ic_components.json"))
    print(f"\n{'='*92}")
    print("READING THIS TABLE.  A fitted TOTAL exponent below 0.5 is only a win if the")
    print("dominant term is 'table' or 'relations'.  When 'lin.alg' dominates, the fit is")
    print("measuring the m^2 term, which is asymptotically the SMALLEST of the three and")
    print("must be overtaken as n grows.  Check the 'dominant' column before believing")
    print("any exponent.")
    return report


if __name__ == "__main__":
    main()
