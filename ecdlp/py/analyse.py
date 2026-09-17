"""analyse.py -- fit every measured attack's cost scaling and plot it against the
Pollard rho bar, then project each fit to 256 bits."""
from __future__ import annotations
import sys, os, json, math, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import toolkit as T

OUT = T.RESULTS
os.makedirs(OUT, exist_ok=True)


def load(path):
    with open(path) as f:
        return json.load(f)


def fnum(v):
    return float(v)


def rho_series():
    rows = []
    for tag in ("small", "mid", "big", "huge"):
        p = os.path.join(T.DATA, f"rho_bench_{tag}.json")
        if os.path.exists(p):
            rows += load(p)
    out = {}
    for r in rows:
        mode = r["mode"]
        out.setdefault(mode, []).append((fnum(r["n"]), fnum(r["mean_ops"])))
    return out


def ic_series():
    out = {}
    for p in sorted(glob.glob(os.path.join(T.DATA, "ic_sweep_k*.json"))):
        rows = load(p)
        if not rows:
            continue
        key = f"k={rows[0]['k']}, j={rows[0]['j']}"
        best = {}
        for r in rows:
            n = fnum(r["n"]); o = fnum(r["mean_ops"])
            if n not in best or o < best[n]:
                best[n] = o
        out[key] = sorted(best.items())
    return out


def fit(pts):
    xs = [a for a, _ in pts]; ys = [b for _, b in pts]
    if len(xs) < 3:
        return None
    a, c, r2 = T.fit_loglog(xs, ys)
    return dict(alpha=a, c=c, r2=r2, npts=len(xs),
                proj256=a * 256 + c)


def main():
    rho = rho_series()
    ic = ic_series()
    report = {"rho": {}, "index_calculus": {}}

    print("=" * 78)
    print("MEASURED COST SCALING   ops = 2^c * n^alpha     (fit over the toy-curve data)")
    print("=" * 78)
    print(f"{'algorithm':34s} {'pts':>4s} {'alpha':>8s} {'r2':>7s} {'log2 ops @ n=2^256':>19s}")
    print("-" * 78)
    for mode in ("plain", "neg", "endo"):
        if mode not in rho:
            continue
        f = fit(rho[mode])
        if not f:
            continue
        report["rho"][mode] = f
        print(f"{'Pollard rho (' + mode + ')':34s} {f['npts']:4d} {f['alpha']:8.4f} "
              f"{f['r2']:7.4f} {f['proj256']:19.1f}")
    for key, pts in sorted(ic.items()):
        f = fit(pts)
        if not f:
            print(f"{'index calculus ' + key:34s} {len(pts):4d}  (too few sizes to fit)")
            continue
        report["index_calculus"][key] = f
        print(f"{'index calculus ' + key:34s} {f['npts']:4d} {f['alpha']:8.4f} "
              f"{f['r2']:7.4f} {f['proj256']:19.1f}")
    print("-" * 78)
    print("The bar: rho with negation + endomorphism, sqrt(pi n/12) ~ 2^127.8 at 256 bits.")
    print("A win needs alpha < 0.5 AND a 256-bit projection below 2^100.")

    # ---------------------------------------------------------------- figure
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.2))
    ax = axes[0]
    colors = {"plain": "#666666", "neg": "#999999", "endo": "#111111"}
    for mode in ("plain", "neg", "endo"):
        if mode not in rho:
            continue
        pts = sorted(rho[mode])
        x = np.log2([a for a, _ in pts]); y = np.log2([b for _, b in pts])
        ax.plot(x, y, "o", ms=3.5, color=colors[mode], alpha=.75,
                label=f"Pollard rho ({mode})")
    ic_colors = ["#D1495B", "#EDAE49", "#00798C", "#7B2CBF"]
    for i, (key, pts) in enumerate(sorted(ic.items())):
        x = np.log2([a for a, _ in pts]); y = np.log2([b for _, b in pts])
        ax.plot(x, y, "s--", ms=5, color=ic_colors[i % 4], label=f"index calculus {key}")
    xs = np.linspace(18, 64, 50)
    ax.plot(xs, 0.5 * xs + math.log2(math.sqrt(math.pi / 12)), "-", lw=1.2,
            color="#111111", alpha=.6)
    ax.set_xlabel("log2 n  (group order)")
    ax.set_ylabel("log2 (total operations)")
    ax.set_title("Measured cost on toy curves  y² = x³ + 7,  prime order, j = 0")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=.25)

    ax = axes[1]
    lbls, alphas, cols = [], [], []
    for mode in ("plain", "neg", "endo"):
        if mode in report["rho"]:
            lbls.append(f"rho ({mode})"); alphas.append(report["rho"][mode]["alpha"])
            cols.append(colors[mode])
    for i, (key, f) in enumerate(sorted(report["index_calculus"].items())):
        lbls.append(f"IC {key}"); alphas.append(f["alpha"]); cols.append(ic_colors[i % 4])
    yy = np.arange(len(lbls))
    ax.barh(yy, alphas, color=cols, alpha=.85)
    ax.axvline(0.5, color="#111111", ls="--", lw=1.5)
    ax.text(0.505, len(lbls) - 0.6, "rho / generic bound  α = 0.5", fontsize=9, rotation=90,
            va="top")
    for i, a in enumerate(alphas):
        ax.text(a + 0.012, i, f"{a:.3f}", va="center", fontsize=9)
    ax.set_yticks(yy); ax.set_yticklabels(lbls, fontsize=9)
    ax.set_xlabel("fitted exponent α in  ops = 2^c · n^α")
    ax.set_xlim(0, max(alphas) * 1.22)
    ax.set_title("Nothing measured falls left of the dashed line")
    ax.grid(axis="x", alpha=.25)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "scaling.png"), dpi=155)
    print("\nfigure ->", os.path.join(OUT, "scaling.png"))
    T.jdump(report, os.path.join(OUT, "scaling_fits.json"))
    return report


if __name__ == "__main__":
    main()
