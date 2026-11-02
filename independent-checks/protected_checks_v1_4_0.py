import sys, math, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1]); import verify_protected_v1_4_0 as P
from scipy.stats import chi2, norm
mc=pd.read_csv(sys.argv[2])
# (A) Per-cell: analytic vs v1.3.3 Monte Carlo power, tau=3, level/none attacks, protected methods.
d=mc[(mc.tau==3.0)&mc.estimator.isin(['protected_scale','omnibus_protected','combined_protected'])
     &mc.attack_mode.isin(['none','level'])&(mc.signal_s>0)]
z=[]
for r in d.itertuples():
    pat=tuple(range(int(r.reach_r)))
    pa=P.average_power(10.,3.,0.,1,int(r.k),r.estimator,float(r.signal_s),int(r.reach_r),pat)
    se=math.sqrt(max(pa*(1-pa),1e-6)/10000); z.append((r.power-pa)/se)
z=np.array(z); print(f"(A) cells={len(z)} mean z={z.mean():+.3f} sd z={z.std():.3f} max|z|={abs(z).max():.2f} frac|z|>3={np.mean(abs(z)>3):.4f}")
# (B) Simulated size and power of whitened omnibus + combined under clustered Sigma, vs analytic.
rng=np.random.default_rng(5); n=200000
for rho,c in [(0.,4),(.5,4),(.9,2)]:
    S=P.sigma_full(10.,3.,rho,c); L=np.linalg.cholesky(S); k=8; Dm=P.contrast_matrix(k); O=Dm@S@Dm.T; Oi=np.linalg.inv(O)
    a=np.r_[1.,np.full(k,-1./k)]; sa=math.sqrt(a@S@a)
    for label,mu in [('null',np.zeros(9)),('aligned4',np.r_[10.,[10.]*4,[0.]*4]),('split2+2',np.r_[10.,10,10,0,0,10,10,0,0][:9])]:
        x=rng.standard_normal((n,9))@L.T+mu; dd=x@Dm.T; Q=np.einsum('ij,jk,ik->i',dd,Oi,dd); zz=x@a/sa
        om=np.mean(Q>chi2.isf(.01,k)); cb=np.mean((zz>norm.isf(.005))|(Q>chi2.isf(.005,k)))
        pa_om=P.exact_power(mu,S,'omnibus_protected')[0]; pa_cb=P.exact_power(mu,S,'combined_protected')[0]
        print(f"(B) rho={rho} c={c} {label:<9} omnibus sim={om:.4f} an={pa_om:.4f} | combined sim={cb:.4f} an={pa_cb:.4f}")
