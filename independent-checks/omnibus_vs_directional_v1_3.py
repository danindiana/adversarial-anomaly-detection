# Does a heterogeneity-aware (omnibus) test defeat v1.3's equilibrium level attacks?
# Same frame as v1.3: m=8 controls, hider shifts r=4 fixed controls by s and ON by s;
# observer privately samples k controls; channel noise N(0, v), v = 10 + tau^2, known scale.
import numpy as np
from scipy.stats import chi2, norm
rng=np.random.default_rng(7); n=200000; m=8; a=0.01
cases=[(0,10),(3,10),(10,30)]  # (tau, s) from the v1.3 equilibria
print("tau  s  k | one-sided(v1.3) | omnibus | combined(Bonf.) | size_combined")
for tau,s in cases:
    v=10+tau**2
    for k in (4,8):
        perms=np.argsort(rng.random((n,m)),axis=1)[:,:k]
        shift=np.zeros(m); shift[:4]=s
        for label,on_s,sh in (("alt",s,shift),("null",0,np.zeros(m))):
            on=rng.normal(0,np.sqrt(v),n)+on_s
            off=rng.normal(0,np.sqrt(v),(n,k))+sh[perms]
            z=(on-off.mean(1))/np.sqrt(v*(1+1/k))
            x=np.column_stack([on,off]); q=((x-x.mean(1,keepdims=True))**2).sum(1)/v
            one=z>norm.isf(a); omni=q>chi2.isf(a,k)
            comb=(z>norm.isf(a/2))|(q>chi2.isf(a/2,k))
            if label=="alt": p=(one.mean(),omni.mean(),comb.mean())
            else: sz=comb.mean()
        print(f"{tau:>3} {s:>2} {k:>2} | {p[0]:.3f}           | {p[1]:.3f}   | {p[2]:.3f}           | {sz:.4f}")
