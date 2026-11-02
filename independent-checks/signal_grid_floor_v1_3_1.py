# At v1.3.1's tau=0 defender commitment (k=4: 31.6% physics_only one-sided, 68.4% combined_physics),
# does a hider signal below the grid floor (s=5) earn more than s=5? r=0 (no contamination).
import numpy as np, math
from scipy.stats import norm, chi2
v=10.; k=4; a=.01; n=400000; rng=np.random.default_rng(3)
w_dir, w_comb = 0.315867, 0.684133
def benefit(s): return 0.6*math.log1p(s/5)/math.log1p(4)
on0=rng.normal(0,math.sqrt(v),n); off=rng.normal(0,math.sqrt(v),(n,k))
for s in (1,2,2.5,3,4,5,7.5,10):
    on=on0+s
    z=(on-off.mean(1))/math.sqrt(v*(1+1/k))
    x=np.column_stack([on,off]); q=((x-x.mean(1,keepdims=True))**2).sum(1)/v
    p_dir=(z>norm.isf(a)).mean(); p_comb=((z>norm.isf(a/2))|(q>chi2.isf(a/2,k))).mean()
    det=w_dir*p_dir+w_comb*p_comb
    print(f"s={s:>4}: benefit={benefit(s):.3f} detect={det:.3f} utility={benefit(s)-det:.3f}")
