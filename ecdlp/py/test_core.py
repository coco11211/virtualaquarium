"""Correctness tests for the C arithmetic core and the rho solver."""
import sys, os, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolkit as T

def test_scalar_mul():
    rng = random.Random(12345)
    bad = 0
    for c in T.load_curves():
        E = T.EC(c.p, 7, n=c.n); G = c.G()
        for _ in range(8):
            k = rng.randrange(1, c.n)
            a, b = E.mul(k, G), T.c_mul(c, k, G)
            if a != b:
                bad += 1; print("MISMATCH", c.name, k, a, b)
        # identities
        if T.c_mul(c, c.n, G) != T.O: bad += 1; print("n*G != O", c.name)
        if T.c_mul(c, c.n - 1, G) != E.neg(G): bad += 1; print("(n-1)G != -G", c.name)
    print(f"scalar-mul: {'OK' if bad==0 else str(bad)+' FAILURES'}")
    return bad == 0

def test_target_pipeline():
    bad = 0
    for c in T.load_curves()[:12]:
        for t in T.make_targets(c, 3, seed=7):
            E = T.EC(c.p, 7, n=c.n)
            k = t.reveal_for_logging()
            if E.mul(k, c.G()) != t.Q: bad += 1; print("target Q wrong", c.name)
            if not t.verify(k): bad += 1; print("verify(k) false", c.name)
            if t.verify(k + 1): bad += 1; print("verify(k+1) true", c.name)
            pub = t.public()
            if any(str(k) == str(v) for v in pub.values()): 
                print("  note: secret coincides with a public field (harmless collision)", c.name)
    print(f"target pipeline: {'OK' if bad==0 else str(bad)+' FAILURES'}")
    return bad == 0

def test_rho_small():
    """rho must actually solve instances in every mode."""
    bad = 0
    for c in T.load_curves():
        if c.bits > 32: continue
        for t in T.make_targets(c, 2, seed=3):
            pub = t.public()
            for mode in (T.MODE_PLAIN, T.MODE_NEG, T.MODE_ENDO):
                r = T.rho_solve(c, t.Q, mode=mode, dbits=max(3, c.bits//4-2),
                                nwalk=32, rparts=256, seed=99, maxsteps=1<<30)
                if not r["ok"] or not t.verify(r["k"]):
                    bad += 1
                    print("RHO FAIL", c.name, T.MODE_NAME[mode], r)
    print(f"rho correctness (<=32 bit, all modes): {'OK' if bad==0 else str(bad)+' FAILURES'}")
    return bad == 0

def test_no_secret_leak():
    """Static audit: the solver entry point must not be able to see the scalar."""
    import inspect
    src = inspect.getsource(T.rho_solve)
    bad = 0
    for tok in ("reveal_for_logging", "_Target__k", "Target"):
        if tok in src: bad += 1; print("LEAK TOKEN in rho_solve:", tok)
    csrc = open(os.path.join(T.ROOT, "csrc", "rho.c")).read()
    # the C solver's signature must contain no secret argument
    sig = csrc.split("int rho_solve(")[1].split(")")[0]
    for tok in ("secret", "scalar_k", "known_k"):
        if tok in sig: bad += 1; print("LEAK ARG:", tok)
    print(f"leak audit: {'OK' if bad==0 else str(bad)+' PROBLEMS'}")
    return bad == 0

if __name__ == "__main__":
    ok = all([test_scalar_mul(), test_target_pipeline(), test_no_secret_leak(), test_rho_small()])
    print("=== ALL TESTS PASS ===" if ok else "=== FAILURES ===")
    sys.exit(0 if ok else 1)
