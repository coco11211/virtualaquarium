/* Generate toy curves y^2 = x^3 + 7 over F_p, p = 1 mod 3, with PRIME group order.
   Deterministic: for each bit size we start at a fixed seed value and scan upward.
   Output: one JSON-ish line per curve.  */

findcurve(bits, seedoff) = {
  my(p, E, n, lo, cnt);
  lo = 2^(bits-1) + seedoff;
  if(lo % 2 == 0, lo = lo + 1);
  p = lo;
  cnt = 0;
  while(1,
    p = nextprime(p+1);
    cnt = cnt + 1;
    if(p >= 2^bits, error("overflow at bits=", bits));
    if(p % 3 != 1, next);
    if(p < 5, next);
    E = ellinit([0,7], p);
    if(type(E) != "t_VEC", next);
    n = ellcard(E);
    if(!isprime(n), next);
    if(n % 3 != 1, next);
    return([p, n, cnt]);
  );
};

/* a generator: any point of the prime-order curve that is not O */
findgen(p, n) = {
  my(E, x, y, P);
  E = ellinit([0,7], p);
  x = 1;
  while(1,
    if(issquare(Mod(x^3+7, p), &y),
      P = [lift(x) % p, lift(y) % p];
      if(ellisoncurve(E, P) && ellmul(E, P, n) == [0],
        /* make y canonical: smaller of y, p-y */
        if(P[2] > p - P[2], P = [P[1], p - P[2]]);
        return(P);
      );
    );
    x = x + 1;
  );
};

/* beta = primitive cube root of unity mod p ; lambda = root of X^2+X+1 mod n
   chosen so that (beta*x, y) = lambda * (x,y) */
findbeta(p) = {
  my(r);
  r = polrootsmod(x^2+x+1, p);
  return([lift(r[1]), lift(r[2])]);
};

findlambda(n) = {
  my(r);
  r = polrootsmod(x^2+x+1, n);
  return([lift(r[1]), lift(r[2])]);
};

{
  my(sizes, out, res, p, n, G, bs, ls, E, beta, lam, ok, i, j, tries);
  sizes = [20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62];
  print("[");
  for(i = 1, #sizes,
    bs = sizes[i];
    /* several curves per size, different seed offsets, for multi-target testing */
    for(j = 0, 2,
      res = findcurve(bs, j*7919 + 1);
      p = res[1]; n = res[2];
      G = findgen(p, n);
      beta = findbeta(p);
      lam  = findlambda(n);
      E = ellinit([0,7], p);
      /* pair up beta and lambda: test which lambda matches which beta */
      ok = 0;
      for(a = 1, 2,
        for(b = 1, 2,
          if(ellmul(E, G, lam[b]) == [lift(Mod(beta[a]*G[1], p)), G[2]],
            print("{\"bits\":", bs, ",\"idx\":", j, ",\"p\":", p, ",\"n\":", n,
                  ",\"gx\":", G[1], ",\"gy\":", G[2],
                  ",\"beta\":", beta[a], ",\"lambda\":", lam[b],
                  ",\"scan\":", res[3], "},");
            ok = 1;
          );
        );
      );
      if(ok == 0, print("{\"bits\":", bs, ",\"idx\":", j, ",\"ERROR\":\"no beta/lambda pairing\"},"));
    );
  );
  print("{}]");
}
quit;
