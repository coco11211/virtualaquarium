"""hom_search.py -- is there any efficiently computable map out of E(F_p) that
respects the group law even approximately?

MOTIVATION.  A homomorphism  f : E(F_p) -> H  with easy DLP in H breaks ECDLP.
The classical instance is MOV/Frey-Ruck into F_{p^k}^*, dead for secp256k1 because
the embedding degree is astronomically large.  But the x-coordinate already LIVES in
F_p^*, where the discrete log is subexponential -- and for secp256k1 the prime is a
degree-8 polynomial in 2^32, so SNFS makes it cheaper still.  So the natural question
is whether

        L(P) := log_g x(P)   in  Z/(p-1)

carries anything.  Three tests, all on toy curves small enough to tabulate the whole
F_p^* discrete log:

  T1 DIRECT TRANSFER: is L(kG) dependent on k?   (if yes, ECDLP reduces to DLP in F_p^*)
  T2 QUASI-HOMOMORPHISM: is  D = L(P+Q) - L(P) - L(Q)  mod (p-1)  non-uniform?
     A homomorphism would make D identically 0; anything short of uniform is a bias
     that could be amplified.
  T3 MACHINE SEARCH over a parameterised family of maps f(P) = x + c, x*y, y/x, ...
     looking for the member that minimises the conditional entropy H(f(P+Q) | f(P), f(Q)).
     A genuine homomorphism would give H = 0; the null is H = log2(bins).

Non-generic structure: the x-coordinate as an element of the multiplicative group of
the field, which a generic-group algorithm cannot see.
"""
from __future__ import annotations
import sys, os, math, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import toolkit as T
import ktree as K
from scipy_stub import chi2_sf


def log_table(p):
    """full discrete-log table for F_p^*: tab[v] = log_g(v)"""
    g = _prim_root(p)
    tab = np.zeros(p, dtype=np.int64) - 1
    v = 1
    for i in range(p - 1):
        tab[v] = i
        v = v * g % p
    return g, tab


def _prim_root(p):
    fac, M, i = [], p - 1, 2
    while i * i <= M:
        if M % i == 0:
            fac.append(i)
            while M % i == 0:
                M //= i
        i += 1
    if M > 1:
        fac.append(M)
    for g in range(2, 1000):
        if all(pow(g, (p - 1) // q, p) != 1 for q in fac):
            return g
    raise RuntimeError


def chi2_uniform(counts):
    counts = np.asarray(counts, dtype=float)
    N = counts.sum(); k = len(counts)
    if N == 0 or k < 2:
        return 0.0, 0, 1.0
    E = N / k
    chi2 = float(((counts - E) ** 2 / E).sum())
    return chi2, k - 1, chi2_sf(chi2, k - 1)


def chi2_indep(a, b, na, nb):
    O = np.zeros((na, nb))
    np.add.at(O, (a, b), 1.0)
    N = O.sum()
    ra, cb = O.sum(1, keepdims=True), O.sum(0, keepdims=True)
    E = ra * cb / N
    mask = E > 0
    chi2 = float((((O - E) ** 2)[mask] / E[mask]).sum())
    dof = (np.count_nonzero(ra) - 1) * (np.count_nonzero(cb) - 1)
    return chi2, dof, chi2_sf(chi2, dof)


def run_curve(cur, nsample=120000, nbin=32, seed=5):
    p, n = cur.p, cur.n
    rng = random.Random(seed)
    g, tab = log_table(p)
    out = {"curve": cur.name, "bits": cur.bits, "p": p, "n": n, "g": g}

    # ---- T1: does L(kG) depend on k ?
    ks = [rng.randrange(1, n) for _ in range(nsample)]
    x, y, inf = K.mul_batch(cur, ks)
    keep = (inf == 0) & (x != 0)
    ksa = np.array([ks[i] for i in np.nonzero(keep)[0]], dtype=object)
    L = tab[x[keep].astype(np.int64)]
    kb = np.array([int(v) * nbin // n for v in ksa], dtype=int)
    Lb = (L * nbin // (p - 1)).astype(int)
    c2, dof, pv = chi2_indep(kb, Lb, nbin, nbin)
    out["T1"] = dict(test="L(kG) vs k", chi2=c2, dof=dof, pvalue=pv, n=int(keep.sum()))
    # MANDATORY CONTROL.  Sampling any DETERMINISTIC table with replacement inflates
    # chi^2 by about N*dof/n, whatever the table is; without this control the 20-bit
    # data reads as p = 1.6e-7.  Replacing the real discrete-log table by a random
    # bijection must reproduce the effect -- and it does.
    rperm = np.random.default_rng(1).permutation(p - 1)
    tab2 = np.zeros(p, dtype=np.int64) - 1
    tab2[1:] = rperm[:p - 1]
    L2 = tab2[x[keep].astype(np.int64)]
    c2c, dofc, pvc = chi2_indep(kb, (L2 * nbin // (p - 1)).astype(int), nbin, nbin)
    out["T1_random_table_control"] = dict(chi2=c2c, dof=dofc, pvalue=pvc,
                                          predicted_excess=float(int(keep.sum()) * dof / n))
    # also low bits
    c2b, dofb, pvb = chi2_indep(np.array([int(v) & 15 for v in ksa]),
                                (L & 15).astype(int), 16, 16)
    out["T1_lowbits"] = dict(test="L low 4 bits vs k low 4 bits", chi2=c2b, dof=dofb, pvalue=pvb)

    # ---- T2: quasi-homomorphism defect
    ax, ay = K.random_points(cur, nsample, random.Random(seed + 1))
    bx, by = K.random_points(cur, nsample, random.Random(seed + 2))
    m = min(len(ax), len(bx))
    rx, ry, ri = K.add_batch(cur, [int(v) for v in ax[:m]], [int(v) for v in ay[:m]],
                             [int(v) for v in bx[:m]], [int(v) for v in by[:m]])
    ok = (ri == 0) & (rx != 0) & (ax[:m] != 0) & (bx[:m] != 0)
    LA = tab[ax[:m][ok].astype(np.int64)]
    LB = tab[bx[:m][ok].astype(np.int64)]
    LR = tab[rx[ok].astype(np.int64)]
    D = (LR - LA - LB) % (p - 1)
    cnt = np.bincount((D * nbin // (p - 1)).astype(int), minlength=nbin)
    c2, dof, pv = chi2_uniform(cnt)
    out["T2"] = dict(test="L(P+Q)-L(P)-L(Q) uniform?", chi2=c2, dof=dof, pvalue=pv,
                     n=int(ok.sum()), max_bin_excess=float(cnt.max() / cnt.mean() - 1))
    # CONTROL: the same statistic with the pairing destroyed
    perm = np.random.default_rng(seed).permutation(len(LR))
    Dc = (LR[perm] - LA - LB) % (p - 1)
    cc = np.bincount((Dc * nbin // (p - 1)).astype(int), minlength=nbin)
    c2c, dofc, pvc = chi2_uniform(cc)
    out["T2_control"] = dict(chi2=c2c, dof=dofc, pvalue=pvc)

    # ---- T3: machine search over candidate maps for low conditional entropy
    cands = {
        "x": lambda X, Y: X,
        "y": lambda X, Y: Y,
        "x*y": lambda X, Y: X * Y % p,
        "x+y": lambda X, Y: (X + Y) % p,
        "x^2": lambda X, Y: X * X % p,
        "x^3": lambda X, Y: X * X % p * X % p,
        "y/x": lambda X, Y: Y * pow(int(X), p - 2, p) % p if np.isscalar(X) else None,
        "logx": lambda X, Y: tab[X],
        "logy": lambda X, Y: tab[Y] if Y else 0,
        "log(x*y)": lambda X, Y: (tab[X] + tab[Y]) % (p - 1),
        "x mod small": lambda X, Y: X % 1009,
        "legendre(x)": lambda X, Y: 1 if pow(int(X), (p - 1) // 2, p) == 1 else 0,
    }
    AXo = ax[:m][ok]; AYo = ay[:m][ok]; BXo = bx[:m][ok]; BYo = by[:m][ok]
    RXo = rx[ok]; RYo = ry[ok]
    t3 = []
    NB = 16
    for name, f in cands.items():
        try:
            if name in ("y/x",):
                fa = np.array([f(int(a), int(b)) for a, b in zip(AXo, AYo)])
                fb = np.array([f(int(a), int(b)) for a, b in zip(BXo, BYo)])
                fr = np.array([f(int(a), int(b)) for a, b in zip(RXo, RYo)])
            elif name == "legendre(x)":
                fa = np.array([f(int(a), 0) for a in AXo]); fb = np.array([f(int(a), 0) for a in BXo])
                fr = np.array([f(int(a), 0) for a in RXo])
            elif name in ("logx",):
                fa = tab[AXo.astype(np.int64)]; fb = tab[BXo.astype(np.int64)]; fr = tab[RXo.astype(np.int64)]
            elif name in ("logy",):
                fa = tab[np.maximum(AYo, 1).astype(np.int64)]
                fb = tab[np.maximum(BYo, 1).astype(np.int64)]
                fr = tab[np.maximum(RYo, 1).astype(np.int64)]
            elif name == "log(x*y)":
                fa = (tab[AXo.astype(np.int64)] + tab[np.maximum(AYo,1).astype(np.int64)]) % (p - 1)
                fb = (tab[BXo.astype(np.int64)] + tab[np.maximum(BYo,1).astype(np.int64)]) % (p - 1)
                fr = (tab[RXo.astype(np.int64)] + tab[np.maximum(RYo,1).astype(np.int64)]) % (p - 1)
            else:
                fa = np.array([int(f(int(a), int(b))) for a, b in zip(AXo, AYo)])
                fb = np.array([int(f(int(a), int(b))) for a, b in zip(BXo, BYo)])
                fr = np.array([int(f(int(a), int(b))) for a, b in zip(RXo, RYo)])
        except Exception as ex:
            continue
        mx = max(int(fa.max()), int(fb.max()), int(fr.max()), 1) + 1
        A = (fa.astype(np.int64) * NB // mx); Bv = (fb.astype(np.int64) * NB // mx)
        R = (fr.astype(np.int64) * NB // mx)
        joint = A * NB + Bv
        H = _cond_entropy(R, joint, NB, NB * NB)
        H0 = _cond_entropy(R, np.zeros_like(R), NB, 1)      # unconditional entropy
        t3.append(dict(map=name, cond_entropy_bits=H, uncond_entropy_bits=H0,
                       info_bits=H0 - H))
    out["T3"] = sorted(t3, key=lambda d: -d["info_bits"])
    return out


def _cond_entropy(r, j, nr, nj):
    """H(R | J) in bits, plug-in estimator"""
    O = np.zeros((nj, nr))
    np.add.at(O, (j, r), 1.0)
    N = O.sum()
    pj = O.sum(1)
    H = 0.0
    for a in range(nj):
        if pj[a] == 0:
            continue
        pr = O[a] / pj[a]
        nz = pr > 0
        H += (pj[a] / N) * float(-(pr[nz] * np.log2(pr[nz])).sum())
    return H


if __name__ == "__main__":
    res = []
    for cur in [c for c in T.load_curves() if c.bits in (20, 22, 24)]:
        t0 = time.time()
        r = run_curve(cur)
        res.append(r)
        print(f"{cur.name}: T1 p={r['T1']['pvalue']:.4g}  T1_lowbits p={r['T1_lowbits']['pvalue']:.4g}  "
              f"T2 p={r['T2']['pvalue']:.4g} (control {r['T2_control']['pvalue']:.4g})  "
              f"T1ctl p={r['T1_random_table_control']['pvalue']:.4g}  "
              f"best map: {r['T3'][0]['map']} leaks {r['T3'][0]['info_bits']:+.5f} of "
              f"{r['T3'][0]['uncond_entropy_bits']:.3f} bits   [{time.time()-t0:.0f}s]", flush=True)
    T.jdump(res, os.path.join(T.DATA, "hom_search.json"))
