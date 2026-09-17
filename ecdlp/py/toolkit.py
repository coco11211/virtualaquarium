"""toolkit.py -- shared infrastructure for the secp256k1 ECDLP attack program.

Everything an experiment needs: toy-curve loading, pure-python reference
arithmetic, the C rho baseline, and a target generator whose secret scalars are
structurally unreachable from solver code.
"""
from __future__ import annotations
import ctypes, json, math, os, random, hashlib, time
from dataclasses import dataclass, asdict
from typing import Optional, Tuple, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RESULTS = os.path.join(ROOT, "results")
LIB = os.path.join(ROOT, "lib", "librho.so")

# --------------------------------------------------------------------------
# secp256k1 itself (reference constants, never attacked directly here)
# --------------------------------------------------------------------------
SECP_P = 2**256 - 2**32 - 977
SECP_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECP_B = 7
SECP_GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
SECP_GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
SECP_BETA = 0x7AE96A2B657C07106E64479EAC3434E99CF0497512F58995C1396C28719501EE
SECP_LAMBDA = 0x5363AD4CC05C30E0A5261C028812645A122E22EA20816678DF02967C1B23BD72

# --------------------------------------------------------------------------
# toy curves
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Curve:
    bits: int
    idx: int
    p: int
    n: int
    gx: int
    gy: int
    beta: int
    lam: int
    b: int = 7

    @property
    def name(self) -> str:
        return f"c{self.bits}_{self.idx}"

    def G(self) -> "Pt":
        return Pt(self.gx, self.gy)


def load_curves(path: Optional[str] = None) -> List[Curve]:
    path = path or os.path.join(DATA, "curves_raw.json")
    out, seen = [], set()
    with open(path) as f:
        for line in f:
            line = line.strip().rstrip("],").rstrip(",")
            if not line.startswith("{") or line == "{}":
                continue
            d = json.loads(line)
            if "ERROR" in d:
                raise RuntimeError(f"curve gen error: {d}")
            key = (d["bits"], d["idx"])
            if key in seen:            # gp prints both (beta,lambda) and (beta^2,lambda^2)
                continue
            seen.add(key)
            out.append(Curve(bits=d["bits"], idx=d["idx"], p=d["p"], n=d["n"],
                             gx=d["gx"], gy=d["gy"], beta=d["beta"], lam=d["lambda"]))
    out.sort(key=lambda c: (c.bits, c.idx))
    return out


# --------------------------------------------------------------------------
# reference (slow, obviously-correct) arithmetic in pure python
# --------------------------------------------------------------------------
class Pt:
    __slots__ = ("x", "y", "inf")

    def __init__(self, x=None, y=None, inf=False):
        self.x, self.y, self.inf = x, y, inf

    def __eq__(self, o):
        if not isinstance(o, Pt):
            return NotImplemented
        return (self.inf and o.inf) or (not self.inf and not o.inf and self.x == o.x and self.y == o.y)

    def __hash__(self):
        return hash(("inf",) if self.inf else (self.x, self.y))

    def __repr__(self):
        return "O" if self.inf else f"({self.x},{self.y})"


O = Pt(inf=True)


class EC:
    """y^2 = x^3 + a x + b over F_p, reference implementation."""

    def __init__(self, p: int, b: int = 7, a: int = 0, n: Optional[int] = None):
        self.p, self.a, self.b, self.n = p, a, b, n

    def on_curve(self, P: Pt) -> bool:
        if P.inf:
            return True
        return (P.y * P.y - P.x ** 3 - self.a * P.x - self.b) % self.p == 0

    def add(self, P: Pt, Q: Pt) -> Pt:
        p = self.p
        if P.inf:
            return Q
        if Q.inf:
            return P
        if P.x == Q.x:
            if (P.y + Q.y) % p == 0:
                return O
            lam = (3 * P.x * P.x + self.a) * pow(2 * P.y % p, p - 2, p) % p
        else:
            lam = (Q.y - P.y) * pow((Q.x - P.x) % p, p - 2, p) % p
        xr = (lam * lam - P.x - Q.x) % p
        return Pt(xr, (lam * (P.x - xr) - P.y) % p)

    def neg(self, P: Pt) -> Pt:
        return O if P.inf else Pt(P.x, (-P.y) % self.p)

    def sub(self, P: Pt, Q: Pt) -> Pt:
        return self.add(P, self.neg(Q))

    def mul(self, k: int, P: Pt) -> Pt:
        if self.n is not None:
            k %= self.n
        if k < 0:
            return self.mul(-k, self.neg(P))
        R, A = O, P
        while k:
            if k & 1:
                R = self.add(R, A)
            A = self.add(A, A)
            k >>= 1
        return R

    def lift_x(self, x: int) -> Optional[Pt]:
        """Return the point with this x and the smaller y, or None."""
        p = self.p
        rhs = (x * x % p * x + self.a * x + self.b) % p
        y = sqrt_mod(rhs, p)
        if y is None:
            return None
        return Pt(x % p, min(y, p - y))


def sqrt_mod(a: int, p: int) -> Optional[int]:
    a %= p
    if a == 0:
        return 0
    if pow(a, (p - 1) // 2, p) != 1:
        return None
    if p % 4 == 3:
        return pow(a, (p + 1) // 4, p)
    # Tonelli-Shanks
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p
            i += 1
        bb = pow(c, 1 << (m - i - 1), p)
        m, c = i, bb * bb % p
        t = t * c % p
        r = r * bb % p
    return r


# --------------------------------------------------------------------------
# the C rho baseline
# --------------------------------------------------------------------------
class RhoRes(ctypes.Structure):
    _fields_ = [("k", ctypes.c_uint64), ("steps", ctypes.c_uint64),
                ("extra_ops", ctypes.c_uint64), ("dps", ctypes.c_uint64),
                ("cycles", ctypes.c_uint64), ("restarts", ctypes.c_uint64),
                ("ok", ctypes.c_int)]


_lib = None


def lib():
    global _lib
    if _lib is None:
        _lib = ctypes.CDLL(LIB)
        _lib.rho_solve.restype = ctypes.c_int
        _lib.rho_solve.argtypes = [ctypes.c_uint64] * 9 + [ctypes.c_int] * 4 + \
                                  [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int,
                                   ctypes.POINTER(RhoRes)]
        _lib.ec_scalar_mul.restype = None
        _lib.ec_scalar_mul.argtypes = [ctypes.c_uint64] * 5 + \
            [ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
             ctypes.POINTER(ctypes.c_int)]
    return _lib


MODE_PLAIN, MODE_NEG, MODE_ENDO = 0, 1, 2
MODE_NAME = {0: "plain", 1: "neg", 2: "endo"}
# expected constant C in  E[ops] = C * sqrt(n)
MODE_CONST = {0: math.sqrt(math.pi / 2), 1: math.sqrt(math.pi / 4), 2: math.sqrt(math.pi / 12)}


def rho_solve(cur: Curve, Q: Pt, mode: int = MODE_ENDO, dbits: int = 10,
              nwalk: int = 256, rparts: int = 1024, seed: int = 1,
              maxsteps: int = 1 << 40, logtab: int = 22) -> dict:
    """Solve for k with Q = k*G.  Receives only public data."""
    res = RhoRes()
    t0 = time.perf_counter()
    rc = lib().rho_solve(cur.p, cur.n, cur.b, cur.gx, cur.gy, Q.x, Q.y,
                         cur.beta, cur.lam, mode, dbits, nwalk, rparts,
                         seed, maxsteps, logtab, ctypes.byref(res))
    dt = time.perf_counter() - t0
    return dict(rc=rc, k=res.k if res.ok else None, steps=res.steps,
                extra_ops=res.extra_ops, dps=res.dps, cycles=res.cycles,
                restarts=res.restarts, ok=bool(res.ok), seconds=dt,
                total_ops=res.steps + res.extra_ops, mode=MODE_NAME[mode])


def c_mul(cur: Curve, k: int, P: Pt) -> Pt:
    rx, ry, inf = ctypes.c_uint64(), ctypes.c_uint64(), ctypes.c_int()
    lib().ec_scalar_mul(cur.p, cur.b, P.x, P.y, k % cur.n,
                        ctypes.byref(rx), ctypes.byref(ry), ctypes.byref(inf))
    return O if inf.value else Pt(rx.value, ry.value)


# --------------------------------------------------------------------------
# targets:  the secret scalar is generated here and NEVER handed to a solver
# --------------------------------------------------------------------------
class Target:
    """A DLP instance.  `public()` is everything a solver may see.

    The secret is stored under a name-mangled attribute and is only reachable
    through `verify()`, which takes a candidate and returns a bool.  Solvers are
    handed `Target.public()`, never the object.
    """
    __slots__ = ("curve", "Q", "_Target__k", "label")

    def __init__(self, curve: Curve, k: int, label: str = ""):
        self.curve = curve
        self.__k = k % curve.n
        self.Q = c_mul(curve, self.__k, curve.G())
        self.label = label

    def public(self) -> dict:
        c = self.curve
        return dict(p=c.p, n=c.n, b=c.b, gx=c.gx, gy=c.gy,
                    qx=self.Q.x, qy=self.Q.y, beta=c.beta, lam=c.lam,
                    bits=c.bits, label=self.label)

    def verify(self, k: Optional[int]) -> bool:
        return k is not None and (k % self.curve.n) == self.__k

    def reveal_for_logging(self) -> int:
        """ONLY for post-hoc analysis and logs.  Never call from solver code."""
        return self.__k


def make_targets(cur: Curve, count: int, seed: int) -> List[Target]:
    rng = random.Random(hashlib.sha256(f"target|{cur.name}|{seed}".encode()).digest())
    return [Target(cur, rng.randrange(1, cur.n), f"{cur.name}#{i}") for i in range(count)]


# --------------------------------------------------------------------------
# misc
# --------------------------------------------------------------------------
def rho_bar(n: int, mode: int = MODE_ENDO) -> float:
    """The bar: expected group operations for rho in the given mode."""
    return MODE_CONST[mode] * math.sqrt(n)


def fit_loglog(xs: List[float], ys: List[float]) -> Tuple[float, float, float]:
    """Least-squares fit log2(y) = a*log2(x) + c.  Returns (a, c, r2)."""
    import numpy as np
    X = np.log2(np.asarray(xs, dtype=float))
    Y = np.log2(np.asarray(ys, dtype=float))
    A = np.vstack([X, np.ones_like(X)]).T
    (a, c), res, *_ = np.linalg.lstsq(A, Y, rcond=None)
    pred = a * X + c
    ss_res = float(((Y - pred) ** 2).sum())
    ss_tot = float(((Y - Y.mean()) ** 2).sum())
    return float(a), float(c), (1 - ss_res / ss_tot if ss_tot > 0 else 1.0)


def jdump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)
    return path


@dataclass(frozen=True)
class SpecialCurve(Curve):
    """Toy curve over a prime of secp256k1's shape p = t^d - t - c, t = 2^s."""
    s: int = 0
    t: int = 0
    c: int = 0
    d: int = 8

    @property
    def name(self) -> str:
        return f"sp{self.bits}"

    def tadic(self, x: int) -> List[int]:
        """base-t digits, least significant first, length d"""
        out = []
        for _ in range(self.d):
            out.append(x % self.t)
            x //= self.t
        return out


def load_special(path: Optional[str] = None) -> List["SpecialCurve"]:
    path = path or os.path.join(DATA, "curves_special.json")
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("{"):
                continue
            d = json.loads(line)
            if "NONE" in d:
                continue
            out.append(SpecialCurve(bits=d["bits"], idx=0, p=d["p"], n=d["n"],
                                    gx=d["gx"], gy=d["gy"], beta=d["beta"],
                                    lam=d["lambda"], s=d["s"], t=d["t"], c=d["c"], d=8))
    out.sort(key=lambda c: c.bits)
    return out
