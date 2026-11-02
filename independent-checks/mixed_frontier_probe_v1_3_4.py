import csv, math, sys, itertools
import numpy as np
rows=list(csv.DictReader(open(sys.argv[1])))
def ben(s): return 0.6*math.log1p(s/5)/math.log1p(4) if s else 0.
for tau in ('0.0','3.0','10.0'):
    R=[r for r in rows if r['tau']==tau]
    pols=sorted({(int(r['k']),r['estimator']) for r in R})
    atts=sorted({(float(r['signal_s']),int(r['reach_r']),r['attack_mode'],float(r['spread_delta'])) for r in R})
    ai={a:i for i,a in enumerate(atts)}; pi={p:i for i,p in enumerate(pols)}
    U=np.zeros((len(pols),len(atts)))
    for r in R:
        a=(float(r['signal_s']),int(r['reach_r']),r['attack_mode'],float(r['spread_delta']))
        U[pi[(int(r['k']),r['estimator'])],ai[a]]=ben(a[0])-(float(r['power']) if a[0]>0 else 0.)
    clean=np.array([a[1]==0 for a in atts])
    def point(p):
        u=p@U; return u[clean].max(), max(0.,u[~clean].max()-u[clean].max())
    valid=[p for p in pols if p[1] in ('omnibus_protected','combined_protected','protected_scale')]
    pure={p:point(np.eye(len(pols))[pi[p]]) for p in valid}
    # check reproduction of a pure point
    print(f"tau={tau} pure omnibus k4 {pure[(4,'omnibus_protected')][0]:.3f},{pure[(4,'omnibus_protected')][1]:.3f}; combined k8 {pure[(8,'combined_protected')][0]:.3f},{pure[(8,'combined_protected')][1]:.3f}; directional k4 {pure[(4,'protected_scale')][0]:.3f},{pure[(4,'protected_scale')][1]:.3f}")
    # two-policy mixtures over all valid pairs, weights 0..1
    best=[]
    for a,b in itertools.combinations(valid,2):
        for w in np.linspace(0,1,101):
            p=np.zeros(len(pols)); p[pi[a]]=w; p[pi[b]]=1-w
            Uc,W=point(p); best.append((Uc,W,a,b,w))
    # for WTP budgets, min hider clean utility: pure vs mixed
    for cap in (0.0,0.01,0.025,0.05):
        bp=min((v[0],k) for k,v in pure.items() if v[1]<=cap+1e-12)
        bm=min((x for x in best if x[1]<=cap+1e-12), key=lambda x:x[0])
        print(f"   WTP<={cap:<5}: best pure U={bp[0]:.3f} {bp[1]} | best 2-mix U={bm[0]:.3f} WTP={bm[1]:.3f} {bm[2]}x{bm[4]:.2f}+{bm[3]}")
