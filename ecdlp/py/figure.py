"""figure.py -- the master figure: everything measured, against the rho bar."""
from __future__ import annotations
import sys, os, json, glob, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import toolkit as T

C = {"rho_plain": "#9aa0a6", "rho_neg": "#5f6368", "rho_endo": "#111111",
     "k2": "#D1495B", "k3": "#EDAE49", "k6": "#00798C", "sat": "#7B2CBF"}


def rho_series():
    rows = []
    for tag in ("small", "mid", "big", "huge"):
        p = os.path.join(T.DATA, f"rho_bench_{tag}.json")
        if os.path.exists(p):
            rows += json.load(open(p))
    out = {}
    for r in rows:
        out.setdefault(r["mode"], []).append((float(r["n"]), float(r["mean_ops"])))
    return {k: sorted(v) for k, v in out.items()}


def ic_series():
    out = {}
    for path in sorted(glob.glob(os.path.join(T.DATA, "ic_comp_k*.json"))) or []:
        rows = json.load(open(path))
        out[(rows[0]["k"], rows[0]["j"])] = sorted(
            [(float(r["n"]), float(r["mean_ops"])) for r in rows])
    p2 = os.path.join(T.DATA, "ic_sweep_k2j1.json")
    if os.path.exists(p2):
        rows = json.load(open(p2))
        best = {}
        for r in rows:
            b = int(r["bits"])
            if b not in best or float(r["mean_ops"]) < best[b][1]:
                best[b] = (float(r["n"]), float(r["mean_ops"]))
        out[(2, 1)] = sorted(best.values())
    return out


def main():
    rho = rho_series(); ic = ic_series()
    proj = json.load(open(os.path.join(T.RESULTS, "ic_projection.json")))
    fig = plt.figure(figsize=(16.5, 9.4))
    gs = fig.add_gridspec(2, 3, hspace=.32, wspace=.42)

    # ---- (a) measured cost on toy curves
    ax = fig.add_subplot(gs[0, :2])
    for mode, col, lab in (("plain", C["rho_plain"], "Pollard rho (plain)"),
                           ("neg", C["rho_neg"], "rho + negation"),
                           ("endo", C["rho_endo"], "rho + negation + endomorphism  ← the bar")):
        if mode in rho:
            x = np.log2([a for a, _ in rho[mode]]); y = np.log2([b for _, b in rho[mode]])
            ax.plot(x, y, "o", ms=3.6, color=col, alpha=.8, label=lab)
    for (k, j), pts in sorted(ic.items()):
        col = C.get(f"k{k}", "#888")
        x = np.log2([a for a, _ in pts]); y = np.log2([b for _, b in pts])
        ax.plot(x, y, "s-", ms=5, lw=1.4, color=col,
                label=f"index calculus  k={k}, j={j}")
    xs = np.linspace(18, 64, 60)
    ax.plot(xs, 0.5 * xs + math.log2(math.sqrt(math.pi / 12)), "--", lw=1, color="#111", alpha=.5)
    ax.set_xlabel("log₂ n"); ax.set_ylabel("log₂ (total operations)")
    ax.set_title("(a)  Measured cost on toy curves  y² = x³ + 7,  prime order, j = 0", loc="left")
    ax.legend(fontsize=8.5, loc="upper left"); ax.grid(alpha=.22)

    # ---- (b) the transient: local slope rising toward the asymptote
    ax = fig.add_subplot(gs[0, 2])
    for path, lab, asym, col in (("ic_comp_k3j2.json", "k=3, j=2", 2 / 3, C["k3"]),
                                 ("ic_comp_k6j3.json", "k=6, j=3", 3 / 5, C["k6"])):
        p = os.path.join(T.DATA, path)
        if not os.path.exists(p):
            continue
        rows = sorted(json.load(open(p)), key=lambda r: r["bits"])
        mids, sl = [], []
        for a, b in zip(rows, rows[1:]):
            mids.append((a["bits"] + b["bits"]) / 2)
            sl.append((math.log2(b["mean_ops"]) - math.log2(a["mean_ops"])) /
                      (math.log2(b["n"]) - math.log2(a["n"])))
        ax.plot(mids, sl, "o-", ms=4, color=col, label=lab)
        ax.axhline(asym, ls=":", lw=1.1, color=col)
    ax.axhline(0.5, color="#111", ls="--", lw=1.6)
    ax.text(21, 0.508, "rho / generic bound", fontsize=8)
    ax.set_xlabel("bits (window midpoint)"); ax.set_ylabel("local exponent")
    ax.set_title("(b)  The sub-0.5 reading is a transient", loc="left")
    ax.legend(fontsize=8); ax.grid(alpha=.22); ax.set_ylim(0.28, 0.72)

    # ---- (c) cost-component shares
    ax = fig.add_subplot(gs[1, 0])
    p = os.path.join(T.DATA, "ic_comp_k6j3.json")
    if os.path.exists(p):
        rows = sorted(json.load(open(p)), key=lambda r: r["bits"])
        b = [r["bits"] for r in rows]
        tot = np.array([r["mean_ops"] for r in rows])
        for key, lab, col in (("mean_la", "linear algebra  (m², exponent 2/5)", "#00798C"),
                              ("mean_rel", "relation search  (exponent 3/5)", "#EDAE49"),
                              ("mean_tab", "3-sum table  (exponent 3/5)", "#D1495B")):
            ax.plot(b, np.array([r[key] for r in rows]) / tot * 100, "o-", ms=4,
                    color=col, label=lab)
    ax.set_xlabel("bits"); ax.set_ylabel("share of total cost (%)")
    ax.set_title("(c)  Why:  k=6, j=3 cost composition", loc="left")
    ax.legend(fontsize=7.4, loc="center right"); ax.grid(alpha=.22)

    # ---- (d) projection to 256 bits
    ax = fig.add_subplot(gs[1, 1])
    labs, vals, cols = [], [], []
    for key in ("k2j1", "k3j2", "k6j3"):
        if key in proj:
            labs.append(f"IC {key[0]}={key[1]}, {key[2]}={key[3]}")
            vals.append(proj[key]["projection"]["256"]["log2_total"])
            cols.append(C.get("k" + key[1], "#888"))
    labs.append("rho, measured fit"); vals.append(128.8); cols.append(C["rho_endo"])
    labs.append("rho, theory √(πn/12)"); vals.append(127.8); cols.append("#444")
    yy = np.arange(len(labs))
    ax.barh(yy, vals, color=cols, alpha=.87)
    ax.axvline(100, color="#c00", ls="--", lw=1.6)
    ax.text(104, len(labs) - 0.35, "win condition\n< 2¹⁰⁰", color="#c00", fontsize=8.5, va="top")
    for i, v in enumerate(vals):
        ax.text(v + 3, i, f"2^{v:.0f}", va="center", fontsize=8.5)
    ax.set_yticks(yy); ax.set_yticklabels(labs, fontsize=8.5)
    ax.set_xlabel("log₂ (operations) at n = 2²⁵⁶"); ax.set_xlim(0, max(vals) * 1.22)
    ax.set_title("(d)  Projection to secp256k1", loc="left"); ax.grid(axis="x", alpha=.22)

    # ---- (e) SAT/SMT
    ax = fig.add_subplot(gs[1, 2])
    p = os.path.join(T.DATA, "sat_scaling.json")
    if os.path.exists(p):
        rows = [r for r in json.load(open(p)) if r.get("correct")]
        byb = {}
        for r in rows:
            byb.setdefault(int(r["bits"]), []).append(float(r["seconds"]))
        xs = sorted(byb); ys = [float(np.median(byb[b])) for b in xs]
        ax.plot(xs, np.log2(ys), "o-", ms=5, color=C["sat"], label="Z3 (bitvector encoding)")
        if len(xs) >= 2:
            A = np.vstack([np.array(xs, float), np.ones(len(xs))]).T
            (al, c), *_ = np.linalg.lstsq(A, np.log2(ys), rcond=None)
            xe = np.linspace(min(xs), max(xs) + 4, 20)
            ax.plot(xe, al * xe + c, "--", lw=1, color=C["sat"],
                    label=f"fit: slope {al:.2f} bits⁻¹")
        ax.plot(xs, [0.5 * b - 16 for b in xs], ":", lw=1.4, color="#111",
                label="rho slope (0.5), arbitrary offset")
    ax.set_xlabel("curve size (bits)"); ax.set_ylabel("log₂ (seconds)")
    ax.set_title("(e)  SAT/SMT on the ECDLP", loc="left")
    ax.legend(fontsize=7.6); ax.grid(alpha=.22)

    fig.suptitle("secp256k1 ECDLP attack program — every measured attack, against the Pollard rho bar",
                 fontsize=13.5, y=.975)
    out = os.path.join(T.RESULTS, "scaling.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print("figure ->", out)


if __name__ == "__main__":
    main()
