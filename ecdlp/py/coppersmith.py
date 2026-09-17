"""coppersmith.py -- the exponent gap for lattice attacks on Semaev decomposition.

THE BRANCH.  Take the factor base to be the points with x in a box [0, B], B = p^e --
the only kind of intermediate-size structured subset F_p really admits (intervals, GAPs,
digit boxes, Eisenstein balls are all of this type).  Decomposing a target then means
finding a SMALL ROOT of
        S_{k+1}(x_1, ..., x_k, x_R) = 0   (mod p),     |x_i| < p^e
which is exactly Coppersmith's setting.  Two conditions must hold at once:

  EXISTENCE.  The variety {S_{k+1}=0} is (k-1)-dimensional over F_p, so it has ~p^{k-1}
  points; intersected with a box of volume p^{ek} it has ~p^{ek-1}.  Relations exist iff
        e >= 1/k.
  SOLVABILITY.  A lattice method must actually recover the root.  For the standard
  triangular shift lattice with shifts 0..s in each of k variables and f of degree d in
  each variable, the box of monomials is {0..d+s}^k, so
        dim   = (d+s+1)^k,      shifts = (s+1)^k,
        det   = B^{k(d+s)(d+s+1)^k/2} * p^{(d+s+1)^k - (s+1)^k},
  and det < p^dim gives
        e  <  e*(k, d, s) = 2(s+1)^k / ( k (d+s) (d+s+1)^k ).
  Semaev's S_{k+1} has d = 2^{k-1}.

This file computes e*(k) = max_s e*(k,d,s) and MEASURES it with real LLL for k = 2.
"""
from __future__ import annotations
import sys, os, json, math, random, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolkit as T
import semaev


# ---------------------------------------------------------------- the two bounds
def e_star(k, d, smax=400):
    best, bs = 0.0, 0
    for s in range(0, smax + 1):
        v = 2.0 * (s + 1) ** k / (k * (d + s) * (d + s + 1) ** k)
        if v > best:
            best, bs = v, s
    return best, bs


def gap_table():
    print("EXPONENT GAP:  lattice-solvable e*  vs  relation-existence threshold 1/k")
    print(f"{'k':>3s} {'deg d = 2^(k-1)':>16s} {'best shift s':>13s} {'e* (solvable)':>14s} "
          f"{'1/k (needed)':>13s} {'shortfall':>10s}")
    rows = []
    for k in range(2, 9):
        d = 2 ** (k - 1)
        e, s = e_star(k, d)
        need = 1.0 / k
        rows.append(dict(k=k, d=d, best_s=s, e_star=e, needed=need, ratio=need / e))
        print(f"{k:3d} {d:16d} {s:13d} {e:14.5f} {need:13.5f} {need/e:9.1f}x")
    print("\nThe shortfall GROWS with k -- the opposite of what an attack needs, since a")
    print("win requires k >= 4.  Existence and solvability never overlap.")
    return rows


# ------------------------------------------------------------- the measurement
def lll_gp(rows, dim):
    """LLL-reduce an integer basis (rows) using PARI qflll; returns reduced rows."""
    mat = "[" + ";".join(",".join(str(v) for v in r) for r in rows) + "]"
    # gp's [a,b;c,d] is row-major, qflll treats COLUMNS as the basis, so transpose in
    # and transpose back out -- otherwise the "reduced vectors" are not lattice elements
    script = (f"M = {mat}~;\nT = qflll(M);\nR = (M*T)~;\n"
              "for(i=1,#R[,1], for(j=1,#R[1,],print1(R[i,j],\",\")); print(\"\"));\nquit;\n")
    with tempfile.NamedTemporaryFile("w", suffix=".gp", delete=False) as f:
        f.write(script); path = f.name
    try:
        out = subprocess.run(["gp", "-q", "--default", "parisize=2000000000", path],
                             capture_output=True, text=True, timeout=900)
        res = []
        for line in out.stdout.strip().splitlines():
            line = line.strip().rstrip(",")
            if not line:
                continue
            res.append([int(v) for v in line.split(",")])
        return res
    finally:
        os.unlink(path)


def build_lattice(fdict, p, X, Y, s, dx=2, dy=2):
    """Triangular Coppersmith lattice: shifts u^i v^j f for 0<=i,j<=s, and p*u^a v^b for
    the rest of the monomial box {0..dx+s} x {0..dy+s}.  Column (a,b) scaled by X^a Y^b."""
    A, Bd = dx + s + 1, dy + s + 1
    mons = [(a, b) for a in range(A) for b in range(Bd)]
    idx = {m: i for i, m in enumerate(mons)}
    lead = {(i + dx, j + dy) for i in range(s + 1) for j in range(s + 1)}
    rows = []
    for i in range(s + 1):
        for j in range(s + 1):
            v = [0] * len(mons)
            for (ea, eb), c in fdict.items():
                a, b = ea + i, eb + j
                v[idx[(a, b)]] += int(c) % p
            rows.append([v[t] * X ** mons[t][0] * Y ** mons[t][1] for t in range(len(mons))])
    for m in mons:
        if m in lead:
            continue
        v = [0] * len(mons)
        v[idx[m]] = p
        rows.append([v[t] * X ** mons[t][0] * Y ** mons[t][1] for t in range(len(mons))])
    return rows, mons


def poly_from_vec(vec, mons, X, Y):
    out = {}
    for c, (a, b) in zip(vec, mons):
        if c == 0:
            continue
        q, r = divmod(c, X ** a * Y ** b)
        if r != 0:
            return None                      # not a lattice vector: reject
        out[(a, b)] = q
    return out


def ev(poly, u, v, mod=None):
    t = 0
    for (a, b), c in poly.items():
        t += c * u ** a * v ** b
    return t % mod if mod else t


def measure(curve, e, s, ntrial=12, seed=1):
    """Plant a genuine 2-term decomposition with both x's in [0,B] and see whether the
    lattice recovers it.  B = round(p^e)."""
    p, n = curve.p, curve.n
    S3 = semaev.get(3, 0, 7).as_dict()
    E = T.EC(p, 7, n=n)
    rng = random.Random(seed)
    B = max(2, int(round(p ** e)))
    ok = 0; tried = 0
    for _ in range(ntrial):
        # find two points with x in [0,B)
        pts = []
        for _ in range(4000):
            x = rng.randrange(0, B)
            P = E.lift_x(x)
            if P is not None and not P.inf:
                pts.append(P)
            if len(pts) == 2:
                break
        if len(pts) < 2:
            continue
        P1, P2 = pts
        R = E.add(P1, P2)
        if R.inf:
            continue
        xr = R.x
        # f(u,v) = S_3(u, v, xr) mod p ; the planted root is (P1.x, P2.x)
        f = {}
        for (e1, e2, e3), c in S3.items():
            key = (e1, e2)
            f[key] = (f.get(key, 0) + int(c) * pow(xr, e3, p)) % p
        f = {kk: vv % p for kk, vv in f.items() if vv % p}
        assert ev(f, P1.x, P2.x, p) == 0, "planting is wrong: f does not vanish"
        tried += 1
        rows, mons = build_lattice(f, p, B, B, s)
        red = lll_gp(rows, len(mons))
        # the two shortest reduced vectors should be polynomials vanishing at the root
        # over Z (not just mod p)
        red.sort(key=lambda v: sum(x * x for x in v))
        # STRONGER CRITERION.  Two short vectors vanishing at the root over Z is not
        # enough -- Coppersmith only works if they are algebraically independent, so that
        # eliminating v leaves a nonzero univariate polynomial with x1 as a root.  That
        # elimination is the step an attacker would actually perform, so it is the step
        # we score.
        cands = []
        for v in red[:4]:
            h = poly_from_vec(v, mons, B, B)
            if h and ev(h, P1.x, P2.x) == 0:
                cands.append(h)
        good = False
        if len(cands) >= 2:
            import sympy as sp
            U, V = sp.symbols("U V")
            def to_expr(h):
                return sum(int(c) * U ** a * V ** b for (a, b), c in h.items())
            for i in range(len(cands)):
                for jj in range(i + 1, len(cands)):
                    try:
                        r = sp.resultant(sp.Poly(to_expr(cands[i]), V),
                                         sp.Poly(to_expr(cands[jj]), V))
                    except Exception:
                        continue
                    rp = sp.Poly(sp.expand(r), U)
                    if rp.is_zero or rp.total_degree() == 0:
                        continue
                    if rp.eval(int(P1.x)) == 0:
                        good = True; break
                if good:
                    break
        if good:
            ok += 1
    return dict(bits=curve.bits, e=e, s=s, B=B, trials=tried, recovered=ok,
                rate=(ok / tried if tried else 0.0))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "table"
    if mode in ("table", "all"):
        rows = gap_table()
        T.jdump(rows, os.path.join(T.DATA, "coppersmith_gap.json"))
    if mode in ("measure", "all"):
        print("\nMEASURED e* for k = 2 (S_3), real LLL on planted decompositions")
        pred = {s: 2.0 * (s + 1) ** 2 / (2 * (2 + s) * (3 + s) ** 2) for s in (1, 2, 3)}
        print(f"  predicted e*(s):  " + "  ".join(f"s={s}: {v:.4f}" for s, v in pred.items()))
        out = []
        for cur in [c for c in T.load_curves() if c.bits in (32, 40)]:
            if cur.idx:
                continue
            for s in (1, 2):
                for e in (0.04, 0.06, 0.08, 0.10, 0.12, 0.16, 0.22, 0.30, 0.40, 0.50):
                    r = measure(cur, e, s, ntrial=6, seed=100 + int(e * 1000))
                    out.append(r)
                    print(f"  {cur.name} s={s} e={e:.2f} B=2^{math.log2(max(r['B'],2)):5.1f}"
                          f"  recovered {r['recovered']}/{r['trials']}", flush=True)
        T.jdump(out, os.path.join(T.DATA, "coppersmith_measure.json"))
