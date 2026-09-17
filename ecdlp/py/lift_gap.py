"""lift_gap.py -- quantify the asymmetry that makes index calculus work for F_p*
and not for E(F_p), and run the xedni-calculus independence test.

PART 1 -- FACTOR BASE SIZE.
  F_p*  : the factor base is {primes <= B}, of size ~ B/log B, and a representative
          is decomposed by FACTORING THE INTEGER -- subexponential, because Z has
          unique factorisation and the integer representative literally carries the
          multiplicative structure of the group.
  E(F_p): the analogue of a prime is a Mordell-Weil generator.  E(Q) is finitely
          generated of small rank r, so the number of rational points of naive height
          <= H grows like (log H)^{r/2}, not like H/log H.  And decomposing a point
          into r generators with bounded coefficients is itself an r-dimensional
          discrete log -- circular.
  We measure both counts.

PART 2 -- XEDNI INDEPENDENCE (Silverman 1998; analysed by Jacobson, Koblitz,
  Menezes, Stein and Teske around 1999-2000).  Xedni lifts r points of E(F_p) to Q
  and fits a cubic through them, hoping the lifted points satisfy a relation.  The
  published objection is that they are independent with probability ~ 1.  We measure
  that probability directly, via the rank of the canonical-height pairing matrix, and
  we do it on CM curves (j = 0) to test whether secp256k1's CM structure helps.
"""
import sys, os, json, subprocess, tempfile, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toolkit as T


def gp(script, parisize="1000000000"):
    with tempfile.NamedTemporaryFile("w", suffix=".gp", delete=False) as f:
        f.write(script + "\nquit;\n")
        path = f.name
    try:
        out = subprocess.run(["gp", "-q", "--default", f"parisize={parisize}", path],
                             capture_output=True, text=True, timeout=1800)
        return out.stdout, out.stderr
    finally:
        os.unlink(path)


def part1():
    """count rational points of bounded height on y^2 = x^3 + b, vs primes"""
    script = r"""
countpts(b, H) = {
  my(cnt = 0, E, y);
  E = ellinit([0, b]);
  for(c = 1, floor(sqrt(H)),
    for(a = -H, H,
      if(gcd(a, c) != 1 && c > 1, next);
      my(num = a^3 + b*c^6);
      if(issquare(num, &y),
        cnt = cnt + if(y == 0, 1, 2);
      );
    );
  );
  return(cnt);
};
{
  my(bs, Hs);
  bs = [7, 1, 2, 3, 17];
  Hs = [100, 1000, 10000, 100000];
  for(i = 1, #bs,
    my(b = bs[i], E = ellinit([0,b]), r);
    r = ellrank(E);
    print("RANK b=", b, " rank_bounds=", r[1], "..", r[2], " known_pts=", #r[4]);
    for(j = 1, #Hs,
      print("PTS b=", b, " H=", Hs[j], " count=", countpts(b, Hs[j]),
            " primes_below_H=", primepi(Hs[j]));
    );
  );
}
"""
    out, err = gp(script)
    print(out)
    if err.strip():
        print("stderr:", err[:500])
    return out


def part2(ntrial=40, rvals=(2, 3, 4, 5), seed=1):
    """xedni independence: lift r points of E(F_p) to Q on a fitted cubic and
    measure how often they are dependent."""
    curves = [c for c in T.load_curves() if c.bits in (20, 24, 28)]
    lines = []
    for cur in curves:
        for r in rvals:
            lines.append(f"runtest({cur.p}, {cur.n}, {cur.gx}, {cur.gy}, {r}, {ntrial}, {seed});")
    script = r"""
/* Fit y^2 + a1 x y + a3 y = x^3 + a2 x^2 + a4 x + a6 through r lifted points.
   Five free coefficients, so up to 5 points determine a curve; we lift r <= 5
   points of E(F_p) to integer coordinates, solve the linear system for
   (a1,a2,a3,a4,a6) over Q, and test independence via the height pairing. */
runtest(p, n, gx, gy, r, ntrial, seed) = {
  my(E, G, dep = 0, ok = 0, sing = 0, badfit = 0, P, xs, ys, M, v, sol, EQ, pts, H, d, ht);
  setrand(seed);
  E = ellinit([0,7], p);
  G = [gx, gy];
  for(t = 1, ntrial,
    xs = vector(r); ys = vector(r);
    for(i = 1, r,
      P = ellmul(E, G, 1 + random(n-1));
      if(P == [0], next(2));
      /* lift: take the integer representatives in [0,p) and add a random multiple
         of p to x and y, keeping the numbers modest (the xedni recipe) */
      xs[i] = lift(P[1]) - if(random(2), p, 0);
      ys[i] = lift(P[2]) - if(random(2), p, 0);
    );
    /* linear system in (a1,a2,a3,a4,a6):
       y^2 - x^3 = a1 x y + a2 x^2 + a3 y + a4 x + a6                       */
    M = matrix(r, 5, i, j,
          if(j==1, xs[i]*ys[i], if(j==2, xs[i]^2, if(j==3, ys[i], if(j==4, xs[i], 1)))));
    v = vectorv(r, i, ys[i]^2 - xs[i]^3);
    sol = matinverseimage(M, v);
    if(type(sol) != "t_COL", badfit = badfit + 1; next);
    /* the fit solves  a1 xy + a2 x^2 + a3 y + a4 x + a6 = y^2 - x^3, whereas the
       Weierstrass form is  y^2 + A1 xy + A3 y = x^3 + A2 x^2 + A4 x + A6,
       so A1 = -a1 and A3 = -a3. */
    EQ = ellinit([-sol[1], sol[2], -sol[3], sol[4], sol[5]]);
    if(type(EQ) != "t_VEC", sing = sing + 1; next);
    pts = vector(r, i, [xs[i], ys[i]]);
    for(i = 1, r, if(!ellisoncurve(EQ, pts[i]), badfit = badfit + 1; next(2)));
    /* height pairing matrix; singular <=> the points are dependent */
    H = matrix(r, r, i, j, ellbil(EQ, pts[i], pts[j]));
    d = matdet(H);
    ht = prod(i = 1, r, abs(H[i,i])) + 1e-300;
    ok = ok + 1;
    /* dependent <=> the regulator vanishes; compare against the product of the
       diagonal (Hadamard scale) so the test is relative, not absolute */
    if(abs(d)/ht < 1e-9, dep = dep + 1);
  );
  print("XEDNI p=", p, " r=", r, " trials=", ntrial, " fitted=", ok,
        " dependent=", dep, " singular=", sing, " badfit=", badfit);
};
"""
    out, err = gp(script + "\n" + "\n".join(lines))
    print(out)
    if err.strip():
        print("stderr:", err[:2000])
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "1"
    res = {}
    if which in ("1", "all"):
        print("=== PART 1: factor-base size asymmetry ===")
        res["part1"] = part1()
    if which in ("2", "all"):
        print("\n=== PART 2: xedni independence ===")
        res["part2"] = part2()
    T.jdump(res, os.path.join(T.DATA, f"lift_gap_{which}.json"))
