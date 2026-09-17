"""Benchmark the Pollard rho baseline: measure ops = C*sqrt(n) for each mode."""
import sys, os, math, json, time, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolkit as T

def params(c, nwalk=None):
    sq = math.sqrt(c.n)
    nwalk = nwalk or (16 if c.bits <= 28 else 64 if c.bits <= 40 else 256)
    d = max(1, int(math.log2(max(2.0, sq / (20.0 * nwalk)))))
    return nwalk, d

def run(sizes, ntarget, modes, tag, seed0=1000):
    curves = [c for c in T.load_curves() if c.bits in sizes]
    rows = []
    for c in curves:
        nwalk, d = params(c)
        tgts = T.make_targets(c, ntarget, seed=seed0 + c.bits * 13 + c.idx)
        for mode in modes:
            ops, secs, cyc, res = [], [], [], []
            for i, t in enumerate(tgts):
                r = T.rho_solve(c, t.Q, mode=mode, dbits=d, nwalk=nwalk,
                                rparts=1024, seed=seed0 + 7919 * i + c.idx,
                                maxsteps=1 << 42, logtab=22)
                assert r["ok"] and t.verify(r["k"]), (c.name, r)
                ops.append(r["total_ops"]); secs.append(r["seconds"])
                cyc.append(r["cycles"]); res.append(r["restarts"])
            mean = statistics.mean(ops)
            row = dict(curve=c.name, bits=c.bits, idx=c.idx, p=c.p, n=c.n,
                       mode=T.MODE_NAME[mode], ntarget=ntarget, nwalk=nwalk, dbits=d,
                       mean_ops=mean, median_ops=statistics.median(ops),
                       stdev_ops=(statistics.stdev(ops) if len(ops) > 1 else 0.0),
                       sem_ops=(statistics.stdev(ops)/math.sqrt(len(ops)) if len(ops) > 1 else 0.0),
                       sqrt_n=math.sqrt(c.n), C=mean/math.sqrt(c.n),
                       C_theory=T.MODE_CONST[mode],
                       mean_sec=statistics.mean(secs), total_sec=sum(secs),
                       ops_per_sec=(sum(ops)/sum(secs) if sum(secs) > 0 else 0),
                       mean_cycles=statistics.mean(cyc), mean_restarts=statistics.mean(res),
                       raw_ops=ops)
            rows.append(row)
            print(f"{c.name:9s} {T.MODE_NAME[mode]:6s} n=2^{math.log2(c.n):5.2f} "
                  f"mean_ops={mean:12.0f}  C={row['C']:.4f} (theory {row['C_theory']:.4f})  "
                  f"{row['ops_per_sec']/1e6:7.2f} Mops/s  cyc={row['mean_cycles']:.0f}", flush=True)
    T.jdump(rows, os.path.join(T.DATA, f"rho_bench_{tag}.json"))
    return rows

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "small"
    if which == "small":
        run(list(range(20, 41, 2)), 30, (T.MODE_PLAIN, T.MODE_NEG, T.MODE_ENDO), "small")
    elif which == "mid":
        run([42, 44, 46, 48], 12, (T.MODE_PLAIN, T.MODE_ENDO), "mid")
    elif which == "big":
        run([50, 52, 54, 56], 6, (T.MODE_ENDO,), "big")
    elif which == "huge":
        run([58, 60, 62], 3, (T.MODE_ENDO,), "huge")
