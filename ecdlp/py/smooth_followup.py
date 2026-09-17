"""High-power follow-up on the one borderline signal from the k-tree test:
does  x(P) and x(Q) both B-smooth  raise the chance that x(P+Q) is B-smooth?

A real effect would be a new 'smooth point' notion compatible with the group law,
which is exactly what index calculus over E(F_p) lacks.  The original test saw
mean rho = 1.14 with one curve at rho = 4.0 (|z| = 3.0, Bonferroni threshold 3.49)
on only 5000 pairs.  Here we sieve random windows of [0,p) for B-smooth
x-coordinates, which gives two orders of magnitude more support points, and run a
matched control on uniform points.
"""
import sys, os, math, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, toolkit as T, ktree as K


def primes_upto(N):
    s = bytearray([1]) * (N + 1); s[0:2] = b"\x00\x00"
    for i in range(2, int(N ** .5) + 1):
        if s[i]: s[i * i::i] = bytearray(len(s[i * i::i]))
    return [i for i in range(2, N + 1) if s[i]]


def smooth_in_window(W, L, PS):
    """indices in [W, W+L) whose value is PS-smooth, by sieving"""
    rem = np.arange(W, W + L, dtype=np.int64)
    for q in PS:
        start = int((-W) % q)
        idx = np.arange(start, L, q, dtype=np.int64)
        while idx.size:
            rem[idx] //= q
            idx = idx[rem[idx] % q == 0]
    return (np.nonzero(rem == 1)[0] + W).astype(np.int64)


def is_smooth_arr(vals, PS):
    rem = np.asarray(vals, dtype=np.int64).copy()
    for q in PS:
        idx = np.nonzero(rem % q == 0)[0]
        while idx.size:
            rem[idx] //= q
            idx = idx[rem[idx] % q == 0]
    return rem == 1


def collect(cur, PS, want, rng, L=1 << 19):
    SX, SY = [], []
    guard = 0
    while len(SX) < want and guard < 4000:
        guard += 1
        W = rng.randrange(1, max(2, cur.p - L))
        xs = smooth_in_window(W, L, PS)
        if xs.size == 0:
            continue
        ys, ok = K.lift_batch(cur, [int(v) for v in xs])
        keep = ok == 1
        SX.extend([int(v) for v in xs[keep]]); SY.extend([int(v) for v in ys[keep]])
    return SX[:want], SY[:want]


if __name__ == "__main__":
    B = 1 << 8
    PS = primes_upto(B)
    rows = []
    for cur in [c for c in T.load_curves() if c.bits in (32, 40, 48)] + \
               [c for c in T.load_special() if c.bits in (40, 48)]:
        rng = random.Random(4242 + cur.bits * 7 + cur.idx)
        ux, uy = K.random_points(cur, 400000, random.Random(99 + cur.bits))
        delta = float(is_smooth_arr([int(v) for v in ux], PS).mean())
        if delta <= 0:
            rows.append(dict(curve=cur.name, status="base_rate_zero")); continue
        SX, SY = collect(cur, PS, 2 * 60000, rng)
        N = len(SX) // 2
        if N < 5000:
            rows.append(dict(curve=cur.name, status="underpowered", have=len(SX))); continue
        rx, ry, ri = K.add_batch(cur, SX[:N], SY[:N], SX[N:2 * N], SY[N:2 * N])
        k2 = ri == 0
        hits = int(is_smooth_arr([int(v) for v in rx[k2]], PS).sum())
        Nk = int(k2.sum()); exp = Nk * delta; se = math.sqrt(max(Nk * delta * (1 - delta), 1e-12))
        cx, cy = K.random_points(cur, 2 * Nk, random.Random(7 + cur.bits))
        h = len(cx) // 2
        crx, cry, cri = K.add_batch(cur, [int(v) for v in cx[:h]], [int(v) for v in cy[:h]],
                                    [int(v) for v in cx[h:2 * h]], [int(v) for v in cy[h:2 * h]])
        ck = cri == 0
        chits = int(is_smooth_arr([int(v) for v in crx[ck]], PS).sum()); cN = int(ck.sum())
        r = dict(curve=cur.name, bits=cur.bits, status="ok", base_rate=delta, pairs=Nk,
                 hits=hits, expected=exp, rho=(hits / Nk) / delta, z=(hits - exp) / se,
                 ctrl_pairs=cN, ctrl_hits=chits,
                 ctrl_rho=(chits / cN) / delta if cN else 0.0,
                 ctrl_z=(chits - cN * delta) / math.sqrt(max(cN * delta * (1 - delta), 1e-12)))
        rows.append(r)
        print(f"  {cur.name:7s} base={delta:.5f} pairs={Nk:6d} hits={hits:6d} exp={exp:8.1f} "
              f"rho={r['rho']:.3f} z={r['z']:+.2f}  ||  control rho={r['ctrl_rho']:.3f} "
              f"z={r['ctrl_z']:+.2f}", flush=True)
    T.jdump(rows, os.path.join(T.DATA, "smooth_followup.json"))
    ok = [r for r in rows if r.get("status") == "ok"]
    if ok:
        z = np.array([r["z"] for r in ok]); cz = np.array([r["ctrl_z"] for r in ok])
        rh = np.array([r["rho"] for r in ok])
        print(f"\n  {len(ok)} curves, {sum(r['pairs'] for r in ok)} pairs total")
        print(f"  REAL   : mean rho={rh.mean():.4f}  mean z={z.mean():+.3f}  max|z|={abs(z).max():.2f}")
        print(f"  CONTROL: mean z={cz.mean():+.3f}  max|z|={abs(cz).max():.2f}")
