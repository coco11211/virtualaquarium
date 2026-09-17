"""High-power follow-up on the single borderline signal from the k-tree test:
   does  x(P) and x(Q) both B-smooth  raise the chance that x(P+Q) is B-smooth?
A real effect here would be a genuinely new 'smooth point' notion compatible with
the group law.  Run at 40x the original sample size, with a matched control."""
import sys, os, math, random, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, toolkit as T, ktree as K

def primes_upto(N):
    s = bytearray([1])*(N+1); s[0:2]=b"\x00\x00"
    for i in range(2,int(N**.5)+1):
        if s[i]: s[i*i::i]=bytearray(len(s[i*i::i]))
    return [i for i in range(2,N+1) if s[i]]

def smooth_mask(vals, B, PS):
    out = np.zeros(len(vals), dtype=bool)
    for i, v in enumerate(vals):
        v = int(v)
        if v <= 1: out[i] = True; continue
        for q in PS:
            if q > B: break
            while v % q == 0: v //= q
            if v == 1: break
        out[i] = (v == 1)
    return out

if __name__ == "__main__":
    B = 1 << 8
    PS = primes_upto(B)
    rows = []
    for cur in [c for c in T.load_curves() if c.bits in (32, 40, 48)] + \
               [c for c in T.load_special() if c.bits in (40, 48)]:
        p = cur.p
        rng = random.Random(4242 + cur.bits)
        # base rate of B-smooth x over uniform curve points
        ux, uy = K.random_points(cur, 200000, random.Random(99 + cur.bits))
        bm = smooth_mask(ux, B, PS)
        delta = float(bm.mean())
        # collect points whose x is B-smooth, by sieving random x's
        SX, SY = [], []
        while len(SX) < 60000:
            xs = np.array([rng.randrange(1, p) for _ in range(200000)], dtype=object)
            sm = smooth_mask(xs, B, PS)
            xs2 = xs[sm]
            ys, ok = K.lift_batch(cur, xs2)
            keep = ok == 1
            SX.extend(list(xs2[keep])); SY.extend(list(ys[keep]))
            if len(xs2) == 0: break
        N = min(60000, len(SX)//2)
        if N < 5000 or delta <= 0:
            rows.append(dict(curve=cur.name, status="underpowered", have=len(SX), base=delta)); continue
        ax=[int(v) for v in SX[:N]]; ay=[int(v) for v in SY[:N]]
        bx=[int(v) for v in SX[N:2*N]]; by=[int(v) for v in SY[N:2*N]]
        rx, ry, ri = K.add_batch(cur, ax, ay, bx, by)
        k2 = ri == 0
        hits = int(smooth_mask(rx[k2], B, PS).sum())
        Nk = int(k2.sum()); exp = Nk*delta; se = math.sqrt(Nk*delta*(1-delta))
        # matched CONTROL: sums of uniform points, same count
        cx, cy = K.random_points(cur, 2*Nk, random.Random(7 + cur.bits))
        h = len(cx)//2
        crx, cry, cri = K.add_batch(cur, [int(v) for v in cx[:h]], [int(v) for v in cy[:h]],
                                          [int(v) for v in cx[h:2*h]], [int(v) for v in cy[h:2*h]])
        ck = cri == 0
        chits = int(smooth_mask(crx[ck], B, PS).sum()); cN = int(ck.sum())
        rows.append(dict(curve=cur.name, bits=cur.bits, status="ok", base_rate=delta,
                         pairs=Nk, hits=hits, expected=exp, rho=(hits/Nk)/delta, z=(hits-exp)/se,
                         ctrl_pairs=cN, ctrl_hits=chits,
                         ctrl_rho=(chits/cN)/delta if cN else 0,
                         ctrl_z=(chits-cN*delta)/math.sqrt(max(cN*delta*(1-delta),1e-9))))
        r = rows[-1]
        print(f"  {cur.name:7s} base={delta:.5f} pairs={Nk:6d} hits={hits:6d} exp={exp:8.1f} "
              f"rho={r['rho']:.3f} z={r['z']:+.2f}  ||  control rho={r['ctrl_rho']:.3f} z={r['ctrl_z']:+.2f}",
              flush=True)
    T.jdump(rows, os.path.join(T.DATA, "smooth_followup.json"))
    ok = [r for r in rows if r.get("status")=="ok"]
    if ok:
        z = np.array([r["z"] for r in ok]); cz = np.array([r["ctrl_z"] for r in ok])
        print(f"\n  {len(ok)} curves: mean z={z.mean():+.3f} max|z|={abs(z).max():.2f}"
              f"   control mean z={cz.mean():+.3f} max|z|={abs(cz).max():.2f}")
        print(f"  Bonferroni |z| threshold for {len(ok)} tests ~ {abs(np.percentile(np.random.default_rng(0).normal(size=400000),100*(1-0.025/len(ok)))):.2f}")
