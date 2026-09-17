"""null_battery.py -- calibrated search for exploitable structure in the point
representation.  Three groups:

  A. LEAK tests.  Joint statistics of (k, x(kP)).  A generic-group algorithm sees
     nothing here by construction; any dependence would be non-generic structure.
     Null: exact independence.  We chi^2-test many (f(k), g(x)) pairs and check the
     p-value distribution against uniform, with a Bonferroni-corrected threshold.

  B. FACTOR-BASE tests.  Structure of X = {x in F_p : x^3+7 is a QR}, the set of
     x-coordinates.  If a structured set S met X more often than |S|/2, S would be
     a better-than-random factor base.  Null: hypergeometric.

  C. METRIC tests.  Translation distortion of the group law: does a coordinate
     distance d(P,Q) predict d(P+R, Q+R)?  If it did, locality-sensitive hashing
     could beat the birthday bound.  Null: independence.

Every group is run alongside a CONTROL built from a source known to satisfy the
null, so the reported thresholds are calibrated rather than assumed.
"""
from __future__ import annotations
import sys, os, math, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import toolkit as T

# ---------------------------------------------------------------- chi^2 helper
def chi2_indep(a, b, na, nb):
    """chi^2 test of independence for integer-coded samples a (0..na-1), b (0..nb-1).
    Returns (chi2, dof, p_value)."""
    from scipy_stub import chi2_sf
    O = np.zeros((na, nb), dtype=np.float64)
    np.add.at(O, (a, b), 1.0)
    N = O.sum()
    ra, cb = O.sum(1, keepdims=True), O.sum(0, keepdims=True)
    Eexp = ra * cb / N
    mask = Eexp > 0
    chi2 = float((((O - Eexp) ** 2)[mask] / Eexp[mask]).sum())
    dof = (np.count_nonzero(ra) - 1) * (np.count_nonzero(cb) - 1)
    return chi2, dof, chi2_sf(chi2, dof)


# -------------------------------------------------------------- feature makers
def k_features(ks, n):
    """integer-coded features of the (secret) scalar -- used ONLY to test for a
    leak; never fed to a solver."""
    ks = np.asarray(ks, dtype=object)
    F = {}
    for i in (0, 1, 2, 7, 15):
        F[f"k_bit{i}"] = (np.array([int(k) >> i & 1 for k in ks]), 2)
    for m in (3, 5, 7, 11, 16):
        F[f"k_mod{m}"] = (np.array([int(k) % m for k in ks]), m)
    nb = n.bit_length()
    F["k_top3"] = (np.array([(int(k) >> (nb - 3)) & 7 for k in ks]), 8)
    F["k_oct"] = (np.array([int(k) * 8 // n for k in ks]), 8)
    return F


def x_features(xs, p, cur=None):
    xs_np = np.asarray(xs, dtype=object)
    F = {}
    for i in (0, 1, 2, 7, 15):
        F[f"x_bit{i}"] = (np.array([int(x) >> i & 1 for x in xs_np]), 2)
    for m in (3, 5, 7, 11, 16):
        F[f"x_mod{m}"] = (np.array([int(x) % m for x in xs_np]), m)
    pb = p.bit_length()
    F["x_top3"] = (np.array([(int(x) >> (pb - 3)) & 7 for x in xs_np]), 8)
    F["x_oct"] = (np.array([int(x) * 8 // p for x in xs_np]), 8)
    F["x_legendre"] = (np.array([1 if pow(int(x), (p - 1) // 2, p) == 1 else 0 for x in xs_np]), 2)
    # cubic residue character (p = 1 mod 3): the j=0 structure's natural character
    F["x_cubic"] = (np.array([_cubic_class(int(x), p) for x in xs_np]), 3)
    F["x_popcount_par"] = (np.array([bin(int(x)).count("1") & 1 for x in xs_np]), 2)
    if cur is not None and hasattr(cur, "t"):
        F["x_digit0"] = (np.array([int(x) % cur.t % 8 for x in xs_np]), 8)
        F["x_digit7"] = (np.array([(int(x) // cur.t ** 7) % 8 for x in xs_np]), 8)
    return F


_CUBIC_CACHE = {}
def _cubic_class(x, p):
    e = (p - 1) // 3
    v = pow(x % p, e, p)
    c = _CUBIC_CACHE.setdefault(p, {})
    if v not in c:
        c[v] = len(c) % 3
    return c[v]


# ============================================================ GROUP A: leak test
def group_a(cur, nsample=60000, seed=1, control=False):
    rng = random.Random(seed)
    n, p = cur.n, cur.p
    ks, xs, ys = [], [], []
    G = cur.G()
    for _ in range(nsample):
        k = rng.randrange(1, n)
        Q = T.c_mul(cur, k, G)
        if Q.inf:
            continue
        ks.append(k); xs.append(Q.x); ys.append(Q.y)
    if control:
        # destroy the (k, x) link while keeping both marginals exactly
        perm = list(range(len(xs))); rng.shuffle(perm)
        xs = [xs[i] for i in perm]; ys = [ys[i] for i in perm]
    KF, XF = k_features(ks, n), x_features(xs, p, cur)
    rows = []
    for kn, (ka, kna) in KF.items():
        for xn, (xa, xnb) in XF.items():
            c2, dof, pv = chi2_indep(ka.astype(int), xa.astype(int), kna, xnb)
            rows.append(dict(kfeat=kn, xfeat=xn, chi2=c2, dof=dof, pvalue=pv))
    return rows


# ==================================================== GROUP B: factor-base sets
def group_b(cur, seed=2, nsample=200000):
    """Is a structured set S met by the curve's x-set X more often than |S|/2?"""
    p, n = cur.p, cur.n
    rng = random.Random(seed)
    out = []

    def is_x(x):
        return pow((x * x % p * x + 7) % p, (p - 1) // 2, p) in (0, 1)

    def test(label, sampler, size_hint):
        hit = tot = 0
        for _ in range(nsample):
            x = sampler()
            if x is None:
                continue
            tot += 1
            hit += 1 if is_x(x) else 0
        if tot == 0:
            return
        phat = hit / tot
        # null: each x is on the curve with prob ~1/2 (exactly (n-1)/2 of p values,
        # plus x with x^3+7=0); use the measured global rate as the reference
        se = math.sqrt(0.25 / tot)
        z = (phat - 0.5) / se
        out.append(dict(set=label, tested=tot, hit_rate=phat, z=z,
                        size_hint=size_hint))

    test("uniform_F_p", lambda: rng.randrange(0, p), p)
    test("interval_low", lambda: rng.randrange(0, max(2, p >> 8)), p >> 8)
    test("interval_high", lambda: p - 1 - rng.randrange(0, max(2, p >> 8)), p >> 8)
    for e in (3, 5, 7):
        if (p - 1) % e == 0:
            test(f"eth_powers_{e}", lambda e=e: pow(rng.randrange(1, p), e, p), (p - 1) // e)
    # multiplicative subgroup cosets
    for m in _small_divisors(p - 1, 3, 2000):
        g = pow(_prim_root(p), (p - 1) // m, p)
        test(f"mu_{m}", lambda g=g, m=m: pow(g, rng.randrange(0, m), p), m)
    if hasattr(cur, "t"):
        for D in (2, 4, 8):
            if D < cur.t:
                test(f"tadic_digits<{D}", lambda D=D: sum(rng.randrange(0, D) * cur.t ** i
                                                          for i in range(cur.d)) % p, D ** cur.d)
    return out


def _small_divisors(N, lo, hi):
    ds, i = [], 2
    M = N
    fac = {}
    while i * i <= M and i < 100000:
        while M % i == 0:
            fac[i] = fac.get(i, 0) + 1
            M //= i
        i += 1
    if M > 1:
        fac[M] = fac.get(M, 0) + 1
    divs = [1]
    for q, e in fac.items():
        divs = [d * q ** j for d in divs for j in range(e + 1) if d * q ** j <= hi * 100]
    return sorted({d for d in divs if lo <= d <= hi})[:6]


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
    for g in range(2, 200):
        if all(pow(g, (p - 1) // q, p) != 1 for q in fac):
            return g
    raise RuntimeError("no primitive root found")


# ================================================ GROUP C: translation distortion
def group_c(cur, nsample=40000, seed=3, control=False):
    """Does d(P,Q) predict d(P+R, Q+R)?  Tested for several coordinate metrics."""
    rng = random.Random(seed)
    E = T.EC(cur.p, 7, n=cur.n)
    G = cur.G()
    p = cur.p
    metrics = {
        "absdx": lambda A, B: min((A.x - B.x) % p, (B.x - A.x) % p),
        "hamming": lambda A, B: bin(A.x ^ B.x).count("1"),
        "hibits": lambda A, B: (A.x >> (p.bit_length() - 8)) ^ (B.x >> (p.bit_length() - 8)),
    }
    D0 = {kk: [] for kk in metrics}
    D1 = {kk: [] for kk in metrics}
    for _ in range(nsample):
        a, b, r = (rng.randrange(1, cur.n) for _ in range(3))
        P, Q = T.c_mul(cur, a, G), T.c_mul(cur, b, G)
        R = T.c_mul(cur, r, G)
        PR, QR = E.add(P, R), E.add(Q, R)
        if P.inf or Q.inf or PR.inf or QR.inf:
            continue
        for kk, f in metrics.items():
            D0[kk].append(f(P, Q)); D1[kk].append(f(PR, QR))
    rows = []
    for kk in metrics:
        a0 = np.array(D0[kk], dtype=float); a1 = np.array(D1[kk], dtype=float)
        if control:
            a1 = np.random.default_rng(seed).permutation(a1)
        qa = _bin_rank(a0, 8); qb = _bin_rank(a1, 8)
        c2, dof, pv = chi2_indep(qa, qb, 8, 8)
        rows.append(dict(metric=kk, n=len(a0), chi2=c2, dof=dof, pvalue=pv,
                         pearson=float(np.corrcoef(a0, a1)[0, 1]) if len(a0) > 2 else 0.0))
    return rows


def _bin_rank(a, nb):
    r = np.argsort(np.argsort(a))
    return (r * nb // max(1, len(a))).astype(int)


# ------------------------------------------------------------------------ main
if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    curves = [c for c in T.load_curves() if c.bits in (28, 36, 44)] + \
             [c for c in T.load_special() if c.bits in (32, 48)]
    res = {}
    for cur in curves:
        key = cur.name
        res[key] = {}
        if which in ("all", "a"):
            t0 = time.time()
            res[key]["A_real"] = group_a(cur, seed=100 + cur.bits)
            res[key]["A_control"] = group_a(cur, seed=100 + cur.bits, control=True)
            print(f"{key} group A done in {time.time()-t0:.0f}s", flush=True)
        if which in ("all", "b"):
            t0 = time.time()
            res[key]["B"] = group_b(cur, seed=200 + cur.bits, nsample=60000)
            print(f"{key} group B done in {time.time()-t0:.0f}s", flush=True)
        if which in ("all", "c"):
            t0 = time.time()
            res[key]["C_real"] = group_c(cur, seed=300 + cur.bits)
            res[key]["C_control"] = group_c(cur, seed=300 + cur.bits, control=True)
            print(f"{key} group C done in {time.time()-t0:.0f}s", flush=True)
    T.jdump(res, os.path.join(T.DATA, "null_battery.json"))
    print("saved", os.path.join(T.DATA, "null_battery.json"))
