"""ktree.py -- the k-tree / filtration test.

WHY THIS IS THE RIGHT QUESTION.

Index calculus on E(F_p) with a factor base F of size m and k-term decompositions
costs  m*T + m^2  where T is the cost of decomposing one point.  Guess-and-check
gives m*T = n always, so a win needs a smarter decomposition oracle.  The only
known family of smart oracles for k-sums is Wagner's k-tree algorithm, which on
2^l lists reaches time ~ n^{1/(l+1)} and would give a total of n^{2/(l+1)} --
BELOW rho's n^{1/2} as soon as l >= 4 (k = 16 lists, n^{2/5}).

Wagner's algorithm needs a FILTRATION: a chain of efficiently testable predicates
pi_0 > pi_1 > ... on group elements with
        pi_j(P) and pi_j(Q)  =>  pi_{j-1}(P+Q)                        (*)
In Z/2^b the predicates are "low j*b/(l+1) bits are zero" -- subgroups.  In Z_m
(Minder-Sinclair) they are short intervals, which satisfy (*) up to a factor 2
because the integer value of an element is visible and addition is almost
order-preserving.  E(F_p) has PRIME order, so it has no subgroups at all, and the
discrete log -- the only quantity that behaves like an integer value -- is exactly
what we cannot see.

So the question that decides this whole route is:

    Is there ANY efficiently computable predicate on the REPRESENTATION of a point
    (its coordinates) that behaves even approximately like (*) ?

That is non-generic by construction: it reads coordinates, which a generic-group
algorithm cannot.  This file measures it two ways.

  TEST 1 (direct):  rho = Pr[ pi(P+Q) | pi(P), pi(Q) ] / Pr[ pi(R) ].
                    Null rho = 1.  Z_m with an interval predicate gives rho = 2^(d-1).
                    A POSITIVE CONTROL in Z_n is run alongside so we can see the
                    instrument fire when a filtration really exists.

  TEST 2 (general):  even if no predicate we guessed works, maybe SOME function of
                    the representation is compatible.  So: is the distribution of
                    P+Q, for P,Q drawn from a structured set A, distinguishable
                    from uniform on the curve AT ALL?  If the sumset of a
                    structured set is statistically indistinguishable from random,
                    no predicate whatsoever can satisfy (*), and the route is dead
                    for every choice of predicate, not just the ones we tried.
"""
from __future__ import annotations
import sys, os, math, json, time, random, ctypes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import toolkit as T
from scipy_stub import chi2_sf

# ------------------------------------------------------------------ C bindings
_L = None
def L():
    global _L
    if _L is None:
        _L = T.lib()
        _L.ec_add_batch.argtypes = [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int] + \
            [ctypes.POINTER(ctypes.c_uint64)] * 6 + [ctypes.POINTER(ctypes.c_int)]
        _L.ec_lift_batch.argtypes = [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_int)]
        _L.ec_mul_batch.argtypes = [ctypes.c_uint64] * 4 + [ctypes.c_int] + \
            [ctypes.POINTER(ctypes.c_uint64)] * 3 + [ctypes.POINTER(ctypes.c_int)]
    return _L


def add_batch(cur, ax, ay, bx, by):
    N = len(ax)
    A = (ctypes.c_uint64 * N)(*ax); B = (ctypes.c_uint64 * N)(*ay)
    C = (ctypes.c_uint64 * N)(*bx); D = (ctypes.c_uint64 * N)(*by)
    rx = (ctypes.c_uint64 * N)(); ry = (ctypes.c_uint64 * N)(); ri = (ctypes.c_int * N)()
    L().ec_add_batch(cur.p, 7, N, A, B, C, D, rx, ry, ri)
    return np.frombuffer(rx, dtype=np.uint64).copy(), np.frombuffer(ry, dtype=np.uint64).copy(), \
           np.frombuffer(ri, dtype=np.int32).copy()


def lift_batch(cur, xs):
    N = len(xs)
    X = (ctypes.c_uint64 * N)(*[int(v) for v in xs])
    ry = (ctypes.c_uint64 * N)(); ok = (ctypes.c_int * N)()
    L().ec_lift_batch(cur.p, 7, N, X, ry, ok)
    return np.frombuffer(ry, dtype=np.uint64).copy(), np.frombuffer(ok, dtype=np.int32).copy()


def mul_batch(cur, ks, P=None):
    P = P or cur.G()
    N = len(ks)
    K = (ctypes.c_uint64 * N)(*[int(k) % cur.n for k in ks])
    rx = (ctypes.c_uint64 * N)(); ry = (ctypes.c_uint64 * N)(); ri = (ctypes.c_int * N)()
    L().ec_mul_batch(cur.p, 7, P.x, P.y, N, K, rx, ry, ri)
    return np.frombuffer(rx, dtype=np.uint64).copy(), np.frombuffer(ry, dtype=np.uint64).copy(), \
           np.frombuffer(ri, dtype=np.int32).copy()


def random_points(cur, N, rng):
    """uniform random points on the curve, via random scalars"""
    ks = [rng.randrange(1, cur.n) for _ in range(N)]
    x, y, inf = mul_batch(cur, ks)
    keep = inf == 0
    return x[keep], y[keep]


# ------------------------------------------------------------------ predicates
def make_predicates(cur):
    """Each entry: name -> (support_sampler(N, rng) -> xs, test(x, y) -> bool array).
    support_sampler draws x-coordinates from the predicate's support set."""
    p = cur.p
    pb = p.bit_length()
    P = {}

    def add_xlow(d):
        B = max(2, p >> d)
        P[f"x < p/2^{d}"] = (
            lambda N, rng, B=B: np.array([rng.randrange(0, B) for _ in range(N)], dtype=object),
            lambda x, y, B=B: x < B)
    for d in (4, 8, 12):
        add_xlow(d)

    # j=0 specific: the automorphism-orbit minimum.  Invariant under the order-6
    # automorphism group, so it is a predicate on the QUOTIENT E/Aut -- exactly the
    # space rho already works in.
    b1 = cur.beta % p
    b2 = b1 * b1 % p
    def orbmin(x):
        return min(int(x), int(x) * b1 % p, int(x) * b2 % p)
    for d in (4, 8):
        B = max(2, p >> d)
        P[f"orbmin(x) < p/2^{d}"] = (
            lambda N, rng, B=B, b1=b1, b2=b2: np.array(
                [rng.choice([1, b1, b2]) * rng.randrange(0, B) % p for _ in range(N)], dtype=object),
            lambda x, y, B=B: np.array([orbmin(v) < B for v in x]))

    # Hamming weight of the integer representative
    for w in (pb // 2 - 6, pb // 2 - 3):
        P[f"popcount(x) <= {w}"] = (
            lambda N, rng, w=w, pb=pb: np.array(
                [_rand_low_weight(pb, w, rng, p) for _ in range(N)], dtype=object),
            lambda x, y, w=w: np.array([bin(int(v)).count("1") <= w for v in x]))

    # power residues: multiplicative structure
    for r in (3, 5):
        if (p - 1) % r == 0:
            P[f"x is a {r}th power"] = (
                lambda N, rng, r=r: np.array([pow(rng.randrange(1, p), r, p) for _ in range(N)], dtype=object),
                lambda x, y, r=r: np.array([pow(int(v), (p - 1) // r, p) == 1 for v in x]))

    # integer smoothness of x -- an honest "smooth point" notion
    for Bs in (1 << 8,):
        P[f"x is {Bs}-smooth"] = (
            lambda N, rng, Bs=Bs: np.array([_rand_smooth(p, Bs, rng) for _ in range(N)], dtype=object),
            lambda x, y, Bs=Bs: np.array([_is_smooth(int(v), Bs) for v in x]))

    # t-adic small digits (special-shape primes only)
    if hasattr(cur, "t"):
        for D in (cur.t >> 2, cur.t >> 1):
            if D >= 2:
                P[f"t-adic digits < t/{cur.t//D}"] = (
                    lambda N, rng, D=D: np.array(
                        [sum(rng.randrange(0, D) * cur.t ** i for i in range(cur.d)) % p
                         for _ in range(N)], dtype=object),
                    lambda x, y, D=D: np.array(
                        [all(dg < D for dg in cur.tadic(int(v))) for v in x]))
    return P


def _rand_low_weight(pb, w, rng, p):
    for _ in range(100):
        bits = rng.sample(range(pb - 1), min(w, pb - 1))
        v = sum(1 << b for b in bits)
        if 0 < v < p:
            return v
    return rng.randrange(0, p)


_SMALL_PRIMES = None
def _primes_upto(N):
    sieve = bytearray([1]) * (N + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(N ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
    return [i for i in range(2, N + 1) if sieve[i]]


def _is_smooth(v, B):
    if v <= 1:
        return True
    global _SMALL_PRIMES
    if _SMALL_PRIMES is None or _SMALL_PRIMES[-1] < B:
        _SMALL_PRIMES = _primes_upto(max(B, 1 << 12))
    for q in _SMALL_PRIMES:
        if q > B:
            break
        while v % q == 0:
            v //= q
        if v == 1:
            return True
    return v == 1


def _rand_smooth(p, B, rng):
    global _SMALL_PRIMES
    if _SMALL_PRIMES is None or _SMALL_PRIMES[-1] < B:
        _SMALL_PRIMES = _primes_upto(max(B, 1 << 12))
    ps = [q for q in _SMALL_PRIMES if q <= B]
    v = 1
    while v < p // B:
        v *= rng.choice(ps)
    return v % p if v < p else v % p


# =============================================== TEST 1: predicate compatibility
def _budget(name, npair):
    """expensive predicates get a smaller but still adequately powered sample"""
    if "smooth" in name:   return max(5000, npair // 20)
    if "popcount" in name: return max(10000, npair // 8)
    return npair


def test1(cur, npair=200000, seed=7):
    rng = random.Random(seed)
    p = cur.p
    out = []
    preds = make_predicates(cur)
    for name, (sampler, test) in preds.items():
        npair_i = _budget(name, npair)
        ux, uy = random_points(cur, _budget(name, 60000), random.Random(seed + 1))
        base_mask = np.asarray(test(ux, uy), dtype=bool)
        delta = float(base_mask.mean())
        if delta <= 0 or delta >= 0.9:
            out.append(dict(pred=name, status="skipped", base_rate=delta))
            continue
        # draw P, Q from the predicate support (rejection onto the curve)
        need = npair_i
        AX, AY = [], []
        tries = 0
        while len(AX) < 2 * need and tries < 6:
            tries += 1
            xs = sampler(2 * need, rng)
            ys, ok = lift_batch(cur, xs)
            m = np.asarray(test(xs, ys), dtype=bool) & (ok == 1)
            AX.extend(list(np.asarray(xs)[m])); AY.extend(list(ys[m]))
        if len(AX) < 2000:
            out.append(dict(pred=name, status="too_few_support_points", have=len(AX), base_rate=delta))
            continue
        N = min(need, len(AX) // 2)
        ax = [int(v) for v in AX[:N]]; ay = [int(v) for v in AY[:N]]
        bx = [int(v) for v in AX[N:2 * N]]; by = [int(v) for v in AY[N:2 * N]]
        rx, ry, ri = add_batch(cur, ax, ay, bx, by)
        keep = ri == 0
        rxk = np.asarray(rx[keep], dtype=object); ryk = np.asarray(ry[keep], dtype=object)
        hit = int(np.asarray(test(rxk, ryk), dtype=bool).sum())
        Nk = int(keep.sum())
        exp = Nk * delta
        se = math.sqrt(max(Nk * delta * (1 - delta), 1e-12))
        out.append(dict(pred=name, status="ok", base_rate=delta, pairs=Nk,
                        hits=hit, expected=exp, rho=(hit / Nk) / delta if delta else 0.0,
                        z=(hit - exp) / se))
    return out


def test1_control_Zn(cur, npair=200000, seed=7):
    """POSITIVE CONTROL: the identical measurement in Z_n with interval predicates,
    where a filtration provably exists.  The instrument must fire here."""
    rng = random.Random(seed)
    n = cur.n
    out = []
    for d in (4, 8, 12):
        B = max(2, n >> d)
        delta = B / n
        a = np.array([rng.randrange(0, B) for _ in range(npair)], dtype=object)
        b = np.array([rng.randrange(0, B) for _ in range(npair)], dtype=object)
        s = np.array([(int(u) + int(v)) % n for u, v in zip(a, b)], dtype=object)
        hit = int(sum(1 for v in s if int(v) < B))
        exp = npair * delta
        se = math.sqrt(max(npair * delta * (1 - delta), 1e-12))
        out.append(dict(pred=f"[Z_n CONTROL] a < n/2^{d}", status="ok", base_rate=delta,
                        pairs=npair, hits=hit, expected=exp,
                        rho=(hit / npair) / delta, z=(hit - exp) / se))
    return out


# ================================================ TEST 2: sumset distinguishability
FEATS = None
def features(cur, x, y):
    """A rich integer feature vector of a point, for goodness-of-fit testing."""
    p = cur.p
    pb = p.bit_length()
    F = {}
    F["top6"] = np.array([(int(v) >> (pb - 6)) & 63 for v in x]), 64
    F["low6"] = np.array([int(v) & 63 for v in x]), 64
    F["mid6"] = np.array([(int(v) >> (pb // 2)) & 63 for v in x]), 64
    F["oct"] = np.array([min(63, int(v) * 64 // p) for v in x]), 64
    F["mod_p1"] = np.array([int(v) % 29 for v in x]), 29
    F["popcnt"] = np.array([min(63, bin(int(v)).count("1")) for v in x]), 64
    F["y_top6"] = np.array([(int(v) >> (pb - 6)) & 63 for v in y]), 64
    F["legendre"] = np.array([1 if pow(int(v), (p - 1) // 2, p) == 1 else 0 for v in x]), 2
    if hasattr(cur, "t"):
        F["digit_max"] = np.array([min(63, max(cur.tadic(int(v))) * 64 // cur.t) for v in x]), 64
    return F


def test2(cur, npair=150000, seed=11, dlist=(4, 8)):
    """Is the sumset of a structured set distinguishable from uniform?"""
    rng = random.Random(seed)
    p = cur.p
    rows = []
    # uniform reference sample and an independent uniform CONTROL sample
    ux, uy = random_points(cur, npair, random.Random(seed + 2))
    cx, cy = random_points(cur, npair, random.Random(seed + 3))
    ref = features(cur, ux, uy)

    def gof(name, sx, sy):
        cur_f = features(cur, sx, sy)
        for fname, (arr, nb) in cur_f.items():
            rarr = ref[fname][0]
            O = np.bincount(arr, minlength=nb).astype(float)
            Rc = np.bincount(rarr, minlength=nb).astype(float)
            # two-sample chi^2
            n1, n2 = O.sum(), Rc.sum()
            tot = O + Rc
            mask = tot > 0
            E1 = tot * n1 / (n1 + n2); E2 = tot * n2 / (n1 + n2)
            chi2 = float((((O - E1) ** 2 / np.maximum(E1, 1e-9))[mask]).sum() +
                         (((Rc - E2) ** 2 / np.maximum(E2, 1e-9))[mask]).sum())
            dof = int(mask.sum()) - 1
            rows.append(dict(sample=name, feature=fname, chi2=chi2, dof=dof,
                             pvalue=chi2_sf(chi2, dof), n=int(n1)))

    gof("CONTROL_uniform_sums", *_sums_of(cur, cx, cy, npair, rng))
    for d in dlist:
        B = max(2, p >> d)
        xs = np.array([rng.randrange(0, B) for _ in range(4 * npair)], dtype=object)
        ys, ok = lift_batch(cur, xs)
        m = ok == 1
        sx0 = np.asarray(xs)[m]; sy0 = ys[m]
        if len(sx0) < 2000:
            continue
        gof(f"A = points with x < p/2^{d}", *_sums_of(cur, sx0, sy0, npair, rng))
    return rows


def _sums_of(cur, sx, sy, npair, rng):
    N = min(npair, len(sx) // 2 * 2)
    idx1 = [rng.randrange(0, len(sx)) for _ in range(N)]
    idx2 = [rng.randrange(0, len(sx)) for _ in range(N)]
    ax = [int(sx[i]) for i in idx1]; ay = [int(sy[i]) for i in idx1]
    bx = [int(sx[i]) for i in idx2]; by = [int(sy[i]) for i in idx2]
    rx, ry, ri = add_batch(cur, ax, ay, bx, by)
    keep = ri == 0
    return rx[keep], ry[keep]


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    curves = [c for c in T.load_curves() if c.bits in (32, 40, 48)] + \
             [c for c in T.load_special() if c.bits in (40, 48)]
    res = {}
    for cur in curves:
        res[cur.name] = {}
        if mode in ("all", "1"):
            t0 = time.time()
            res[cur.name]["T1"] = test1(cur, npair=80000, seed=70 + cur.bits)
            res[cur.name]["T1_control"] = test1_control_Zn(cur, npair=80000, seed=70 + cur.bits)
            print(f"{cur.name} test1 {time.time()-t0:.0f}s", flush=True)
        if mode in ("all", "2"):
            t0 = time.time()
            res[cur.name]["T2"] = test2(cur, npair=80000, seed=110 + cur.bits)
            print(f"{cur.name} test2 {time.time()-t0:.0f}s", flush=True)
    T.jdump(res, os.path.join(T.DATA, "ktree.json"))
    print("saved")
