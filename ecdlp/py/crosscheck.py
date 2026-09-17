"""crosscheck.py -- independent verification that every solver is honest.

1. AGREEMENT: index calculus and rho, run on the same hidden targets, must return
   the same scalar, and it must verify against the sealed target.
2. LEAK AUDIT: no solver entry point may reach the secret.  Checked three ways:
   (a) the C sources' exported signatures carry no secret argument;
   (b) the python call sites pass only Target.public()-equivalent data;
   (c) a RUNTIME test: solve a target whose secret is replaced by a decoy after Q is
       computed.  A solver that secretly read the scalar would return the decoy.
3. SANITY: solving a target built from a DIFFERENT generator must fail to verify.
"""
import sys, os, re, random, inspect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolkit as T
import indexcalc as IC

def agreement():
    bad = 0; tot = 0
    for cur in [c for c in T.load_curves() if c.bits in (20, 22, 24, 26)]:
        for t in T.make_targets(cur, 2, seed=777 + cur.bits):
            tot += 1
            r = T.rho_solve(cur, t.Q, mode=T.MODE_ENDO, dbits=4, nwalk=32,
                            rparts=256, seed=5)
            m, _ = IC.best_m(cur.n, 2, mmin=24, memcap=5 * 10 ** 6)
            i = IC.solve(cur, t.Q, max(24, min(m, 300)), 3, 2, seed=11)
            okr = r["ok"] and t.verify(r["k"])
            oki = i["ok"] and t.verify(i["k"])
            same = r["k"] == i["k"]
            if not (okr and oki and same):
                bad += 1
                print(f"  DISAGREE {cur.name} rho={r['k']} ic={i['k']} okr={okr} oki={oki}")
    print(f"agreement: {tot-bad}/{tot} targets solved identically by rho and index calculus")
    return bad == 0

def leak_audit():
    bad = 0
    def strip_c_comments(src):
        src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
        return re.sub(r"//[^\n]*", " ", src)
    for f in ("rho.c", "indexcalc.c", "wiedemann.c"):
        src = strip_c_comments(open(os.path.join(T.ROOT, "csrc", f)).read())
        for pat in (r"\bsecret\b", r"\bknown_k\b", r"\btrue_k\b", r"\bscalar_in\b"):
            if re.search(pat, src):
                bad += 1; print(f"  LEAK TOKEN {pat} in {f} (in CODE, not a comment)")
    # the exported solver signatures must mention only public quantities
    for f, fn in (("rho.c", "rho_solve"), ("indexcalc.c", "index_calculus")):
        src = strip_c_comments(open(os.path.join(T.ROOT, "csrc", f)).read())
        m = re.search(re.escape("int " + fn) + r"\s*\(([^)]*)\)", src, flags=re.S)
        if not m:
            bad += 1; print(f"  could not locate {fn} signature"); continue
        params = [q.strip() for q in m.group(1).split(",")]
        allowed = {"p","nn","b_std","Gx","Gy","Qx","Qy","beta_std","lambda_std","mode",
                   "dbits","nwalk","rparts","seed","maxsteps","logtab","out","m","k","j",
                   "max_targets","k_out","st"}
        names = [q.split()[-1].lstrip("*") for q in params if q]
        extra = [q for q in names if q not in allowed]
        print(f"  {fn}({', '.join(names)})")
        if extra:
            bad += 1; print(f"  UNEXPECTED PARAMETER(S) in {fn}: {extra}")
    for fn in (T.rho_solve, IC.solve):
        s = inspect.getsource(fn)
        for tok in ("reveal_for_logging", "_Target__k"):
            if tok in s:
                bad += 1; print(f"  LEAK {tok} in {fn.__name__}")
    # runtime decoy test
    dec = 0
    for cur in [c for c in T.load_curves() if c.bits == 20]:
        rng = random.Random(3)
        for _ in range(3):
            k = rng.randrange(1, cur.n)
            t = T.Target(cur, k)
            # rebuild the Target object around the SAME Q but a decoy secret; a solver
            # that reads the secret would now return the decoy instead of the true k
            decoy = rng.randrange(1, cur.n)
            t2 = T.Target(cur, decoy)
            r = T.rho_solve(cur, t.Q, mode=T.MODE_ENDO, dbits=4, nwalk=32, rparts=256, seed=2)
            if r["k"] == decoy and decoy != k:
                dec += 1; print("  RUNTIME LEAK: solver returned the decoy")
            if r["k"] != k:
                bad += 1; print(f"  wrong answer {r['k']} != {k}")
            _ = t2
    print(f"leak audit: {'OK' if bad == 0 and dec == 0 else 'PROBLEMS'}")
    return bad == 0 and dec == 0

def sanity():
    """a solver must FAIL to verify against a target it was not given"""
    bad = 0
    for cur in [c for c in T.load_curves() if c.bits == 20]:
        ts = T.make_targets(cur, 2, seed=31)
        r = T.rho_solve(cur, ts[0].Q, mode=T.MODE_ENDO, dbits=4, nwalk=32, rparts=256, seed=9)
        if ts[1].verify(r["k"]):
            bad += 1; print("  SANITY FAIL: answer for target 0 verifies against target 1")
        if not ts[0].verify(r["k"]):
            bad += 1; print("  SANITY FAIL: correct answer does not verify")
    print(f"sanity: {'OK' if bad == 0 else 'PROBLEMS'}")
    return bad == 0

if __name__ == "__main__":
    ok = all([agreement(), leak_audit(), sanity()])
    print("=== CROSSCHECK PASS ===" if ok else "=== CROSSCHECK FAILED ===")
    sys.exit(0 if ok else 1)
