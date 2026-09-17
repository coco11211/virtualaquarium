"""null_battery2.py -- corrected Groups B and C.

v1 had two statistics bugs, both of which manufactured enormous fake signals:
  B: structured sets were SAMPLED WITH REPLACEMENT 60000 times even when the set
     had 3 elements, so the binomial variance was wrong by sqrt(60000/|S|).
  C: the 'hamming' metric is a small integer with heavy ties, so rank-binning was
     degenerate and the chi^2 invalid (the control showed the identical p-value).
Both are fixed here: B enumerates the set exactly and uses the exact global rate
as the null; C uses a permutation null for the statistic actually computed.
"""
from __future__ import annotations
import sys, os, math, json, random, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import toolkit as T


def curve_x_rate(cur):
    """Exact fraction of F_p that is an x-coordinate of an affine point.
    #E = p + 1 + sum_x chi(x^3+b)  =>  sum chi = n - p - 1.
    #\{x: chi=+1\} = (p - z + S)/2 with z = #\{x : x^3+b = 0\}, S = sum chi.
    An x is an x-coordinate iff chi(x^3+b) >= 0, i.e. chi=+1 or x^3+b=0."""
    p, n = cur.p, cur.n
    S = n - p - 1
    # z = number of cube roots of -b
    z = 3 if pow((-7) % p, (p - 1) // 3, p) == 1 else 0
    npos = (p - z + S) // 2
    return (npos + z) / p, npos, z


def enumerate_or_sample(gen, size, cap=400000, rng=None):
    """Return a list of DISTINCT elements: exhaustive if size<=cap else a
    without-replacement sample of cap elements."""
    if size <= cap:
        return list(dict.fromkeys(gen()))
    seen, out = set(), []
    while len(out) < cap:
        v = next(gen())
        if v not in seen:
            seen.add(v); out.append(v)
    return out


def group_b(cur, seed=2, cap=200000):
    p, n = cur.p, cur.n
    rho, npos, z = curve_x_rate(cur)
    rng = random.Random(seed)

    def is_x(x):
        v = (x * x % p * x + 7) % p
        return v == 0 or pow(v, (p - 1) // 2, p) == 1

    out = []

    def test(label, elems, true_size, exhaustive):
        m = len(elems)
        if m == 0:
            return
        h = sum(1 for x in elems if is_x(x))
        exp = m * rho
        se = math.sqrt(m * rho * (1 - rho))
        # exhaustive test of a subset of F_p: hypergeometric is the right null,
        # finite-population correction (p - m)/(p - 1) ~ 1 since m << p
        zsc = (h - exp) / se if se > 0 else 0.0
        out.append(dict(set=label, enumerated=m, true_size=true_size,
                        exhaustive=exhaustive, hits=h, rate=h / m,
                        null_rate=rho, z=zsc))

    g = _prim_root(p)
    # multiplicative subgroups, enumerated EXACTLY
    for mdiv in _divisors_upto(p - 1, cap):
        gg = pow(g, (p - 1) // mdiv, p)
        elems = []
        v = 1
        for _ in range(mdiv):
            elems.append(v); v = v * gg % p
        test(f"mu_{mdiv}", elems, mdiv, True)
    # intervals, enumerated exactly
    for e in (6, 8, 10):
        B = max(4, p >> e)
        L = min(B, cap)
        test(f"interval_low_p/2^{e}", list(range(L)), B, L == B)
    # cubes / higher power residues: image of x -> x^e
    for e in (3, 5, 7):
        if (p - 1) % e == 0:
            sz = (p - 1) // e
            if sz <= cap:
                gg = pow(g, e, p)
                elems, v = [], 1
                for _ in range(sz):
                    elems.append(v); v = v * gg % p
                test(f"{e}th_powers", elems, sz, True)
    # t-adic small-digit sets on special-shape primes
    if hasattr(cur, "t"):
        for D in (2, 3, 4):
            sz = D ** cur.d
            if sz <= cap:
                elems = [sum(dg[i] * cur.t ** i for i in range(cur.d)) % p
                         for dg in itertools.product(range(D), repeat=cur.d)]
                test(f"tadic_digits<{D}", elems, sz, True)
    # CONTROL: random subsets of matching sizes
    for sz in (256, 4096, 65536):
        if sz <= cap:
            test(f"CONTROL_random_{sz}", [rng.randrange(0, p) for _ in range(sz)], sz, True)
    return out


def _divisors_upto(N, cap):
    fac, M, i = {}, N, 2
    while i * i <= M and i < 200000:
        while M % i == 0:
            fac[i] = fac.get(i, 0) + 1; M //= i
        i += 1
    if M > 1:
        fac[M] = fac.get(M, 0) + 1
    divs = [1]
    for q, e in fac.items():
        nd = []
        for d in divs:
            v = d
            for _ in range(e + 1):
                if v <= cap:
                    nd.append(v)
                v *= q
        divs = nd
    return sorted({d for d in divs if 3 <= d <= cap})[-12:]


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
    for g in range(2, 500):
        if all(pow(g, (p - 1) // q, p) != 1 for q in fac):
            return g
    raise RuntimeError


# --------------------------------------------------------------------- group C
def group_c(cur, nsample=60000, seed=3, nperm=300):
    """Permutation-null test of translation distortion.

    Statistic: adjusted mutual information between a coarse code of d(P,Q) and the
    same code of d(P+R,Q+R), plus Spearman rho.  Null obtained by permuting the
    second sequence -- exact, and immune to tie/binning artifacts.
    """
    rng = random.Random(seed)
    nprng = np.random.default_rng(seed)
    E = T.EC(cur.p, 7, n=cur.n)
    G = cur.G()
    p = cur.p
    pb = p.bit_length()
    metrics = {
        "absdx":    lambda A, B: min((A.x - B.x) % p, (B.x - A.x) % p),
        "hamming":  lambda A, B: bin(A.x ^ B.x).count("1"),
        "top8_eq":  lambda A, B: int((A.x >> (pb - 8)) == (B.x >> (pb - 8))),
        "xor_top8": lambda A, B: (A.x >> (pb - 8)) ^ (B.x >> (pb - 8)),
    }
    D0 = {k: [] for k in metrics}; D1 = {k: [] for k in metrics}
    for _ in range(nsample):
        a, b, r = (rng.randrange(1, cur.n) for _ in range(3))
        P, Q, R = T.c_mul(cur, a, G), T.c_mul(cur, b, G), T.c_mul(cur, r, G)
        PR, QR = E.add(P, R), E.add(Q, R)
        if P.inf or Q.inf or PR.inf or QR.inf or P == Q:
            continue
        for k, f in metrics.items():
            D0[k].append(f(P, Q)); D1[k].append(f(PR, QR))
    rows = []
    for k in metrics:
        a0 = np.asarray(D0[k], dtype=np.float64); a1 = np.asarray(D1[k], dtype=np.float64)
        obs_mi = _mi(a0, a1)
        obs_sp = _spearman(a0, a1)
        perm_mi = np.empty(nperm); perm_sp = np.empty(nperm)
        for i in range(nperm):
            q = nprng.permutation(a1)
            perm_mi[i] = _mi(a0, q); perm_sp[i] = _spearman(a0, q)
        rows.append(dict(
            metric=k, n=len(a0),
            mi=obs_mi, mi_null_mean=float(perm_mi.mean()), mi_null_sd=float(perm_mi.std()),
            mi_z=float((obs_mi - perm_mi.mean()) / max(perm_mi.std(), 1e-12)),
            mi_pval=float((np.sum(perm_mi >= obs_mi) + 1) / (nperm + 1)),
            spearman=obs_sp, sp_null_sd=float(perm_sp.std()),
            sp_z=float((obs_sp - perm_sp.mean()) / max(perm_sp.std(), 1e-12)),
            sp_pval=float((np.sum(np.abs(perm_sp) >= abs(obs_sp)) + 1) / (nperm + 1))))
    return rows


def _code(a, nb=16):
    u = np.unique(a)
    if len(u) <= nb:
        return np.searchsorted(u, a), len(u)
    q = np.quantile(a, np.linspace(0, 1, nb + 1)[1:-1])
    return np.searchsorted(q, a), nb


def _mi(a, b, nb=16):
    ca, na = _code(a, nb); cb, nbb = _code(b, nb)
    O = np.zeros((na, nbb))
    np.add.at(O, (ca, cb), 1.0)
    N = O.sum(); P = O / N
    pa = P.sum(1, keepdims=True); pbv = P.sum(0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        term = P * np.log2(P / (pa * pbv))
    return float(np.nansum(term))


def _spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


if __name__ == "__main__":
    curves = [c for c in T.load_curves() if c.bits in (28, 36, 44)] + \
             [c for c in T.load_special() if c.bits in (32, 48)]
    res = {}
    for cur in curves:
        res[cur.name] = {}
        t0 = time.time(); res[cur.name]["B"] = group_b(cur, seed=200 + cur.bits)
        print(f"{cur.name} B ({time.time()-t0:.0f}s)", flush=True)
        t0 = time.time(); res[cur.name]["C"] = group_c(cur, seed=300 + cur.bits)
        print(f"{cur.name} C ({time.time()-t0:.0f}s)", flush=True)
    T.jdump(res, os.path.join(T.DATA, "null_battery2.json"))
    print("saved")
