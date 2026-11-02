import numpy as np
from scipy import stats, integrate, special
Y=1020
# Exp1 row1
print("row1", np.exp(stats.poisson.logpmf(Y,1020)-stats.poisson.logpmf(Y,1000)))
# Gamma B mean 1000 sd 100 -> shape 100, scale 10
a,sc=100,10
def marg(s):
    f=lambda B: stats.poisson.pmf(Y,B+s)*stats.gamma.pdf(B,a,scale=sc)
    return integrate.quad(f,500,1600,limit=200)[0]
m0=marg(0)
print("row2", marg(20)/m0)
nds=[n*d for n in (100,1000,10000) for d in (0.001,0.01)]
print("nds",nds)
print("row3", np.mean([marg(s) for s in nds])/m0)
print("per-Nd BF",[round(marg(s)/m0,3) for s in nds])
# high-spec
print("hs fixed", stats.poisson.pmf(2,2.05)/stats.poisson.pmf(2,0.05))
f1=lambda B: stats.poisson.pmf(2,B+2)*stats.expon.pdf(B,scale=0.05)
f0=lambda B: stats.poisson.pmf(2,B)*stats.expon.pdf(B,scale=0.05)
print("hs gamma", integrate.quad(f1,0,5)[0]/integrate.quad(f0,0,5)[0])
# Exp2
print("haz", 1e-3*integrate.quad(lambda t:(100+9*t)*(0.01+0.0009*t),0,100)[0])
H=3.7e3
lu=integrate.quad(lambda x: np.exp(-H*10**x),-5,-2)[0]/3
print("logunif",lu)
# Exp4
def q(rH,r=0.5,k=20): return 1/(1+np.exp(-k*(r-rH)))
for nm,(a_,b_) in {"W":(8,2),"C":(3,5)}.items():
    print(nm, integrate.quad(lambda x:q(x)*stats.beta.pdf(x,a_,b_),0,1)[0])
