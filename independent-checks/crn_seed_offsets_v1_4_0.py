import sys, math, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1]); import verify_protected_v1_4_0 as P
for f in sys.argv[2:]:
    mc=pd.read_csv(f)
    d=mc[(mc.tau==3.0)&mc.estimator.isin(['protected_scale','omnibus_protected','combined_protected'])&mc.attack_mode.isin(['none','level'])&(mc.signal_s>0)]
    z=np.array([(r.power-P.average_power(10.,3.,0.,1,int(r.k),r.estimator,float(r.signal_s),int(r.reach_r),tuple(range(int(r.reach_r)))))
                /math.sqrt(max(P.average_power(10.,3.,0.,1,int(r.k),r.estimator,float(r.signal_s),int(r.reach_r),tuple(range(int(r.reach_r))))*(1-P.average_power(10.,3.,0.,1,int(r.k),r.estimator,float(r.signal_s),int(r.reach_r),tuple(range(int(r.reach_r))))),1e-6)/10000) for r in d.itertuples()])
    print(f.split('/')[-2], f"mean z={z.mean():+.3f} sd={z.std():.3f}")
