findgen(p, n) = { my(E,x,y,P); E=ellinit([0,7],p); x=1;
  while(1, if(issquare(Mod(x^3+7,p),&y), P=[lift(x)%p,lift(y)%p];
    if(ellisoncurve(E,P)&&ellmul(E,P,n)==[0], if(P[2]>p-P[2],P=[P[1],p-P[2]]); return(P))); x=x+1); };
{
  my(p,E,n,G,beta,lam,found);
  for(bits = 8, 19,
    found = 0; p = 2^(bits-1)+1;
    while(!found && p < 2^bits,
      p = nextprime(p+1);
      if(p >= 2^bits, break);
      if(p % 3 != 1 || p < 5, next);
      E = ellinit([0,7], p); if(type(E)!="t_VEC", next);
      n = ellcard(E);
      if(!isprime(n) || n % 3 != 1, next);
      G = findgen(p,n);
      beta = lift(polrootsmod(x^2+x+1,p)[1]);
      lam  = lift(polrootsmod(x^2+x+1,n)[1]);
      if(ellmul(E,G,lam)!=[lift(Mod(beta*G[1],p)),G[2]], lam=lift(polrootsmod(x^2+x+1,n)[2]));
      if(ellmul(E,G,lam)!=[lift(Mod(beta*G[1],p)),G[2]],
         beta=lift(polrootsmod(x^2+x+1,p)[2]); lam=lift(polrootsmod(x^2+x+1,n)[1]);
         if(ellmul(E,G,lam)!=[lift(Mod(beta*G[1],p)),G[2]], lam=lift(polrootsmod(x^2+x+1,n)[2])));
      print("{\"bits\":",bits,",\"idx\":0,\"p\":",p,",\"n\":",n,",\"gx\":",G[1],
            ",\"gy\":",G[2],",\"beta\":",beta,",\"lambda\":",lam,",\"scan\":0}");
      found = 1;
    );
  );
}
quit;
