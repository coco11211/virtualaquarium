import json, random, math
from fractions import Fraction

def gauss_reduce(u,v):
    def dot(a,b): return a[0]*b[0]+a[1]*b[1]
    while True:
        if dot(v,v) < dot(u,u): u,v = v,u
        mu = Fraction(dot(u,v), dot(u,u))
        m = int(mu + Fraction(1,2)) if mu>=0 else -int(-mu + Fraction(1,2))
        vn = (v[0]-m*u[0], v[1]-m*u[1])
        if dot(vn,vn) >= dot(v,v): return u,v
        v = vn

def cvp_enum(u,v,target,R2):
    """enumerate lattice points w (integer combos of u,v) with |w-target|^2<=R2 (2D, brute-ish)"""
    def dot(a,b): return a[0]*b[0]+a[1]*b[1]
    # solve target = x*u + y*v over rationals
    det = u[0]*v[1]-u[1]*v[0]
    x = Fraction(target[0]*v[1]-target[1]*v[0], det)
    y = Fraction(u[0]*target[1]-u[1]*target[0], det)
    out=[]
    lu = math.isqrt(dot(u,u)); lv = math.isqrt(dot(v,v))
    ru = int(math.sqrt(R2)/max(lu,1))+2; rv = int(math.sqrt(R2)/max(lv,1))+2
    x0 = round(x); y0 = round(y)
    for i in range(x0-ru, x0+ru+1):
        for j in range(y0-rv, y0+rv+1):
            w=(i*u[0]+j*v[0], i*u[1]+j*v[1])
            d=(w[0]-target[0], w[1]-target[1])
            if dot(d,d)<=R2: out.append((-d[0],-d[1]))
    return out

# curve arithmetic
def add(P,Q,p,a=0):
    if P is None: return Q
    if Q is None: return P
    x1,y1=P; x2,y2=Q
    if x1==x2 and (y1+y2)%p==0: return None
    if P==Q: lam=(3*x1*x1)*pow(2*y1,p-2,p)%p
    else: lam=(y2-y1)*pow(x2-x1,p-2,p)%p
    x3=(lam*lam-x1-x2)%p; y3=(lam*(x1-x3)-y1)%p
    return (x3,y3)
def mul(k,P,p):
    if k==0 or P is None: return None
    if k<0: k=-k; P=(P[0],(-P[1])%p)
    R=None; Q=P
    while k:
        if k&1: R=add(R,Q,p)
        Q=add(Q,Q,p); k>>=1
    return R

curves=[]
for line in open('/home/user/virtualaquarium/ecdlp/data/curves_special.json'):
    line=line.strip()
    if not line.startswith('{'): continue
    d=json.loads(line)
    if 'p' in d: curves.append(d)

random.seed(12345)
for d in curves:
    p,n,lam,beta=d['p'],d['n'],d['lambda'],d['beta']
    G=(d['gx'],d['gy'])
    assert mul(lam,G,p)==(beta*G[0]%p, G[1]), "lambda/beta mismatch"
    L=gauss_reduce((n,0),(-lam,1))
    M=gauss_reduce((p,0),(-beta,1))
    bound2 = int(1.5*n)          # |(a,b)|^2 <= 1.5 n  search radius
    stats=[]; ok=0; trials=40
    for _ in range(trials):
        k=random.randrange(1,n)
        Q=mul(k,G,p)
        # GLV short rep of k
        cand=cvp_enum(L[0],L[1],(k,0),int(4*n))
        cand=[w for w in cand if (w[0]+w[1]*lam-k)%n==0]
        a,b=min(cand,key=lambda w:w[0]**2+w[1]**2)
        assert (a+b*lam-k)%n==0
        c=(a+b*beta)%p
        # recover from c alone
        sols=cvp_enum(M[0],M[1],(c,0),bound2)
        sols=[w for w in sols if (w[0]+w[1]*beta-c)%p==0]
        hit=False; ntest=0
        for (a2,b2) in sols:
            ntest+=1
            k2=(a2+b2*lam)%n
            if mul(k2,G,p)==Q: hit=True
        stats.append(len(sols)); ok+=hit
    print(f"bits={d['bits']:3d} p={p}  trials={trials} recovered={ok}  avg#candidates={sum(stats)/len(stats):.2f} max={max(stats)}  |glv|/sqrt(n)~{math.sqrt(a*a+b*b)/math.sqrt(n):.3f}")
