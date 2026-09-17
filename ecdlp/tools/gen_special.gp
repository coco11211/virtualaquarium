/* Toy curves over primes with secp256k1's SHAPE:  p = t^d - t - c,  t = 2^s.
   secp256k1 has d=8, s=32, c=977.  We keep d=8 and vary s, so F_p carries the
   same rank-8 t-adic Z-module structure.  Require p prime, p = 1 mod 3,
   #E(y^2=x^3+7) prime and = 1 mod 3.  */
findgen(p, n) = {
  my(E, x, y, P);
  E = ellinit([0,7], p); x = 1;
  while(1,
    if(issquare(Mod(x^3+7, p), &y),
      P = [lift(x) % p, lift(y) % p];
      if(ellisoncurve(E,P) && ellmul(E,P,n)==[0],
        if(P[2] > p-P[2], P=[P[1],p-P[2]]); return(P)));
    x = x+1);
};
{
  my(d, s, t, c, p, E, n, G, beta, lam, found, cmax);
  d = 8; cmax = 200000;
  for(si = 3, 8,
    s = si;                      /* p ~ 2^(8s) : 24,32,40,48,56,64 bits */
    t = 2^s;
    found = 0;
    for(c = 1, cmax,
      if(found, break);
      p = t^d - t - c;
      if(p < 100, next);
      if(p >= 2^63, next);
      if(!isprime(p), next);
      if(p % 3 != 1, next);
      E = ellinit([0,7], p);
      if(type(E) != "t_VEC", next);
      n = ellcard(E);
      if(!isprime(n) || n % 3 != 1, next);
      G = findgen(p, n);
      beta = lift(polrootsmod(x^2+x+1, p)[1]);
      lam  = lift(polrootsmod(x^2+x+1, n)[1]);
      if(ellmul(E,G,lam) != [lift(Mod(beta*G[1],p)), G[2]],
         lam = lift(polrootsmod(x^2+x+1, n)[2]));
      if(ellmul(E,G,lam) != [lift(Mod(beta*G[1],p)), G[2]],
         beta = lift(polrootsmod(x^2+x+1, p)[2]);
         lam  = lift(polrootsmod(x^2+x+1, n)[1]);
         if(ellmul(E,G,lam) != [lift(Mod(beta*G[1],p)), G[2]],
            lam = lift(polrootsmod(x^2+x+1, n)[2])));
      print("{\"shape\":\"t^8-t-c\",\"s\":", s, ",\"t\":", t, ",\"c\":", c,
            ",\"bits\":", #binary(p), ",\"p\":", p, ",\"n\":", n,
            ",\"gx\":", G[1], ",\"gy\":", G[2], ",\"beta\":", beta,
            ",\"lambda\":", lam, "}");
      found = 1;
    );
    if(!found, print("{\"s\":", s, ",\"NONE\":1}"));
  );
}
quit;
