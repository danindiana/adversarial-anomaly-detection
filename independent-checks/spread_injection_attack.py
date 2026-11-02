# Variance-injection attack: observer estimates tau from control spread (prediction-interval t test);
# hider adds +delta/-delta to two reachable controls (mean unchanged, spread inflated).
import numpy as np
from scipy.stats import t as tdist
rng=np.random.default_rng(1); v0=10.0; s=20.0; n=200000
for k in (4,8):
    crit=tdist.isf(0.01,k-1)
    for delta in (0,10,20,40):
        on=s+rng.normal(0,np.sqrt(v0),n)
        c=rng.normal(0,np.sqrt(v0),(n,k)); c[:,0]+=delta; c[:,1]-=delta
        z=(on-c.mean(1))/(c.std(1,ddof=1)*np.sqrt(1+1/k))
        print(f"k={k} delta={delta:>2}  power={np.mean(z>crit):.3f}")
