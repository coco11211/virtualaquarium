"""project.py -- honest 256-bit projection of the measured index-calculus cost.

Fitting ONE exponent to a sum of terms with DIFFERENT exponents is wrong, and at toy
sizes it can read below 0.5 purely because the smallest-exponent term (the m^2 linear
algebra) still dominates.  Instead we fit the three-term model

    total(m, n) = A*m^j  +  B*n*m^(1-j)  +  C*m^2

to all measured (m, n, ops) points by least squares on log-residuals, check the fit,
then MINIMISE the fitted model over m at each n -- including n = 2^256 -- which is what
the attacker would actually do.
"""
from __future__ import annotations
import sys, os, json, glob, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import toolkit as T


def fit_model(rows, j):
    """Fit A, B, C with relative-error weighted linear least squares (stable, closed
    form).  When the sweep recorded the three cost components separately, each constant
    is fitted to ITS OWN measurements, which is far better conditioned than fitting a
    sum of three nearly collinear basis functions."""
    m = np.array([float(r["m"]) for r in rows])
    n = np.array([float(r["n"]) for r in rows])
    y = np.array([float(r["mean_ops"]) for r in rows])
    have_comp = all("mean_tab" in r for r in rows)
    if have_comp:
        tab = np.array([float(r["mean_tab"]) + float(r.get("mean_fb", 0)) for r in rows])
        rel = np.array([float(r["mean_rel"]) for r in rows])
        la = np.array([float(r["mean_la"]) for r in rows])
        A = float(np.median(tab / m ** j))
        B = float(np.median(rel / (n * m ** (1 - j))))
        C = float(np.median(la / m ** 2))
        p = np.array([A, B, C])
        pred = A * m ** j + B * n * m ** (1 - j) + C * m ** 2
        r = np.abs(pred - y) / y
        return p, float(r.max()), float(r.mean()), "per-component"
    basis = np.vstack([m ** j, n * m ** (1 - j), m ** 2]).T
    W = 1.0 / y
    Aw = basis * W[:, None]
    bw = y * W
    p, *_ = np.linalg.lstsq(Aw, bw, rcond=None)
    if np.any(p < 0):
        # drop negative components and refit on the rest
        keep = p > 0
        if keep.sum() == 0:
            keep = np.array([False, True, False])
        p2, *_ = np.linalg.lstsq(Aw[:, keep], bw, rcond=None)
        p = np.zeros(3); p[keep] = np.maximum(p2, 0)
    pred = basis @ p
    r = np.abs(pred - y) / np.maximum(y, 1)
    return p, float(r.max()), float(r.mean()), "weighted-total"


def optimise(p, j, n, mmax=None):
    A, B, C = p
    best, bm = None, None
    lo, hi = 1.0, (mmax or n ** 0.5)
    m = lo
    while m < hi:
        v = A * m ** j + B * n * m ** (1 - j) + C * m * m
        if best is None or v < best:
            best, bm = v, m
        m *= 1.05
    return bm, best


def main():
    print("=" * 96)
    print("THREE-TERM MODEL FIT AND 256-BIT PROJECTION")
    print("  total(m,n) = A*m^j + B*n*m^(1-j) + C*m^2     (table + relations + linear algebra)")
    print("=" * 96)
    out = {}
    paths = {}
    for path in sorted(glob.glob(os.path.join(T.DATA, "ic_sweep_k*.json"))):
        paths[os.path.basename(path).replace("ic_sweep_", "")] = path
    # a component re-run at the optimal m is better conditioned; prefer it
    for path in sorted(glob.glob(os.path.join(T.DATA, "ic_comp_k*.json"))):
        paths[os.path.basename(path).replace("ic_comp_", "")] = path
    for key in sorted(paths):
        path = paths[key]
        rows = json.load(open(path))
        if len(rows) < 6:
            continue
        k, j = int(rows[0]["k"]), int(rows[0]["j"])
        p, relmax, relmean, how = fit_model(rows, j)
        A, B, C = p
        sizes = sorted({int(r["bits"]) for r in rows})
        print(f"\nk={k}, j={j}   {len(rows)} measurements over sizes {sizes}")
        print(f"  fitted  A={A:.4g}  B={B:.4g}  C={C:.4g}   [{how}]   "
              f"(max rel. error {relmax*100:.1f}%, mean {relmean*100:.1f}%)")
        print(f"  theory says A ~ 1/j! = {1/math.factorial(j):.4g}; "
              f"C ~ 26 (the measured Wiedemann constant)")
        print(f"  {'bits':>5s} {'m_opt':>10s} {'table':>11s} {'relations':>11s} {'lin.alg':>11s} "
              f"{'total':>11s} {'rho':>11s} {'ratio':>10s}")
        proj = {}
        for b in [20, 28, 36, 48, 64, 96, 128, 192, 256]:
            n = float(2 ** b)
            bm, v = optimise(p, j, n)
            t1 = A * bm ** j; t2 = B * n * bm ** (1 - j); t3 = C * bm * bm
            rho = math.sqrt(math.pi / 12) * math.sqrt(n)
            print(f"  {b:5d} {bm:10.4g} {t1:11.4g} {t2:11.4g} {t3:11.4g} {v:11.4g} "
                  f"{rho:11.4g} {v/rho:10.4g}x")
            proj[b] = dict(m=bm, total=v, rho=rho, ratio=v / rho,
                           log2_total=math.log2(max(v, 1)), log2_rho=math.log2(rho))
        a_eff = (math.log2(proj[256]["total"]) - math.log2(proj[128]["total"])) / 128
        print(f"  effective exponent between 2^128 and 2^256: {a_eff:.4f} "
              f"(asymptote {j}/{2*j-1} = {j/(2*j-1):.4f})")
        print(f"  ==> at 256 bits: index calculus 2^{proj[256]['log2_total']:.1f} "
              f"vs rho 2^{proj[256]['log2_rho']:.1f}  "
              f"= 2^{proj[256]['log2_total']-proj[256]['log2_rho']:.1f} times WORSE")
        out[f"k{k}j{j}"] = dict(A=A, B=B, C=C, fit_method=how, rel_err_max=relmax, sizes=sizes,
                                projection=proj, effective_exponent_128_256=a_eff,
                                asymptote=j / (2 * j - 1))
    T.jdump(out, os.path.join(T.RESULTS, "ic_projection.json"))
    print("\nWhy the toy-size exponent can read below 0.5: the m^2 linear-algebra term has")
    print("exponent 2/(2j-1) < j/(2j-1), so it is the SMALLEST term asymptotically but can")
    print("dominate at small n.  Fitting one exponent to the sum then measures the wrong term.")
    return out


if __name__ == "__main__":
    main()
