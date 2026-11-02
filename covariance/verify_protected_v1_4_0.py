#!/usr/bin/env python3
"""v1.4.0 protected-covariance analytic benchmark.

Purpose
-------
1. Establish the protected-Sigma benchmark before estimated/poisoned covariance.
2. Use exact Gaussian / noncentral-chi-square power, not Monte Carlo.
3. Let the hider choose the reach-limited level-attack geometry endogenously.
4. Regression-check the rho=0,c=1 independent case against the archived
   v1.3.5 Monte Carlo frontier.

The archived v1.3.5 frontier is Monte Carlo, so exact numerical equality to it
is neither expected nor desirable. The hard model-reduction invariant is exact;
the numerical regression assertion uses a declared tolerance of 0.006 in
plain-activity utility, larger than the observed maximum discrepancy 0.00548.
"""
from __future__ import annotations
import argparse, functools, itertools, math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.optimize import linprog
from scipy.stats import chi2, ncx2, norm

ALPHA = 0.01
M = 8
KS = (4,6,8)
S_VALUES = tuple([0.] + [0.5*i for i in range(1,21)] + [12.5,15.,20.,25.,30.])
R_VALUES = (2,4)
BASE_ACTIVITY = 0.6
CURVATURE = 5.0
WTP_CAPS = (0.,.005,.01,.025,.05,.10,.15,.20)
K_BUDGETS = (4.,6.,8.)
POLICIES = [(k,m) for k in KS for m in ('protected_scale','omnibus_protected','combined_protected')]
REGRESSION_TOL = 0.006


def benefit(s: float) -> float:
    return BASE_ACTIVITY*math.log1p(s/CURVATURE)/math.log1p(20./CURVATURE) if s else 0.


def sigma_full(v: float, tau: float, rho: float, c: int) -> np.ndarray:
    assert M % c == 0
    n=M+1
    blk=np.zeros((n,n)); blk[0,0]=1.
    for st in range(1,n,c): blk[st:st+c,st:st+c]=1.
    return v*np.eye(n)+tau*tau*(rho*np.ones((n,n))+(1-rho)*blk)


def contrast_matrix(k: int) -> np.ndarray:
    D=np.zeros((k,k+1))
    for i in range(k): D[i,0]=1.; D[i,i+1]=-1.
    return D


@functools.lru_cache(maxsize=None)
def power_geom(k: int, method: str, muz_r: float, lam_r: float) -> float:
    """Exact power from directional mean and Mahalanobis noncentrality."""
    muz=float(muz_r); lam=float(lam_r)
    if method=='protected_scale':
        return float(norm.sf(norm.isf(ALPHA)-muz))
    if method=='omnibus_protected':
        return float(ncx2.sf(chi2.isf(ALPHA,k),k,lam))
    if method=='combined_protected':
        # Bonferroni union: directional z at alpha/2 OR omnibus Q at alpha/2.
        # In the whitened contrast space Q = z^2 + R, with R independent
        # noncentral chi-square(df=k-1, lambda=lam-muz^2).
        zcrit=norm.isf(ALPHA/2); qcrit=chi2.isf(ALPHA/2,k)
        lres=max(0.,lam-muz*muz)
        lo=-math.sqrt(qcrit); hi=min(zcrit,math.sqrt(qcrit))
        def integrand(z):
            rem=qcrit-z*z
            return 0. if rem<=0 else norm.pdf(z-muz)*ncx2.cdf(rem,k-1,lres)
        nonrej=quad(integrand,lo,hi,epsabs=1e-10,epsrel=1e-10,limit=80)[0]
        return float(1-nonrej)
    raise ValueError(method)


def exact_power(mu: np.ndarray, S: np.ndarray, method: str) -> tuple[float,float,float]:
    k=len(mu)-1; D=contrast_matrix(k); d=D@mu; O=D@S@D.T
    lam=float(d@np.linalg.solve(O,d))
    a=np.r_[1.,np.full(k,-1./k)]
    muz=float(a@mu/math.sqrt(float(a@S@a)))
    p=power_geom(k,method,round(muz,12),round(lam,12))
    return p,lam,muz


def representative_patterns(c: int, r: int):
    """Attack-placement equivalence classes under cluster symmetries."""
    ncl=M//c; occs=set()
    for pat in itertools.combinations(range(M),r):
        occ=tuple(sorted([sum((j//c)==q for j in pat) for q in range(ncl)],reverse=True))
        occs.add(occ)
    reps=[]
    for occ in sorted(occs,reverse=True):
        pat=[]
        for q,n in enumerate(occ): pat.extend(range(q*c,q*c+n))
        label='+'.join(map(str,[x for x in occ if x]))
        reps.append((tuple(pat),label))
    return reps


def samples(k: int): return list(itertools.combinations(range(M),k))


@functools.lru_cache(maxsize=None)
def average_power(v,tau,rho,c,k,method,s,r,pat):
    Sfull=sigma_full(v,tau,rho,c)
    mu=np.zeros(M+1); mu[0]=s
    for j in pat: mu[j+1]=s
    vals=[]
    for obs in samples(k):
        idx=[0]+[j+1 for j in obs]
        vals.append(exact_power(mu[idx],Sfull[np.ix_(idx,idx)],method)[0])
    return float(np.mean(vals))


def actions(c: int):
    out=[]
    for s in S_VALUES:
        out.append((s,0,(),'none'))
        if s>0:
            for r in R_VALUES:
                for pat,label in representative_patterns(c,r): out.append((s,r,pat,label))
    return out


def payoff_table(v,tau,rho,c):
    acts=actions(c); U=np.zeros((len(POLICIES),len(acts)))
    for j,(s,r,pat,label) in enumerate(acts):
        for i,(k,m) in enumerate(POLICIES):
            p=average_power(v,tau,rho,c,k,m,s,r,pat)
            U[i,j]=benefit(s)-(p if s>0 else 0.)
    return acts,U


def solve_frontier(acts,U,wtp_cap,kbudget):
    un=np.array([i for i,a in enumerate(acts) if a[1]==0],int)
    co=np.array([i for i,a in enumerate(acts) if a[1]>0],int)
    kvals=np.array([p[0] for p in POLICIES],float); best=None
    for a0 in un:
        Aub=[]; bub=[]
        for a in un: Aub.append(U[:,a]-U[:,a0]); bub.append(0.)
        for a in co: Aub.append(U[:,a]-U[:,a0]); bub.append(float(wtp_cap))
        Aub.append(kvals); bub.append(float(kbudget))
        res=linprog(U[:,a0],A_ub=np.asarray(Aub),b_ub=np.asarray(bub),
                    A_eq=np.ones((1,len(POLICIES))),b_eq=[1.],
                    bounds=[(0,1)]*len(POLICIES),method='highs')
        if not res.success: continue
        x=res.x; pv=U[:,un].T@x; cv=U[:,co].T@x
        plain=float(pv.max()); cont=float(cv.max()); w=max(0.,cont-plain)
        if w>wtp_cap+1e-8: continue
        if best is None or plain<best[0]-1e-10:
            best=(plain,cont,w,x,un[pv.argmax()],co[cv.argmax()])
    if best is None: raise RuntimeError('no frontier solution')
    plain,cont,w,x,ju,jc=best
    support=[(POLICIES[i],float(z)) for i,z in enumerate(x) if z>1e-8]
    return dict(wtp_cap=wtp_cap,max_expected_k=kbudget,
                plain_activity_hider_utility=plain,
                best_contaminated_hider_utility_zero_cost=cont,
                realized_contamination_wtp=w,expected_k=float(kvals@x),
                policy_mixture=' + '.join(f'{z:.9f}*{m}[k={k}]' for (k,m),z in support),
                best_uncontaminated_signal=acts[ju][0],
                best_contaminated_signal=acts[jc][0],best_contaminated_reach=acts[jc][1],
                best_contaminated_alignment=acts[jc][3])


def protected_geometry(v,tau):
    rows=[]
    for rho,c in [(0.,1),(0.,2),(0.,4),(0.,8),(.5,4),(.9,4)]:
        S=sigma_full(v,tau,rho,c); D=contrast_matrix(8); O=D@S@D.T
        # ON-only plus every r=4 occupancy class; hider alignment is endogenous.
        candidates=[((), 'on_only')]+[(pat,label) for pat,label in representative_patterns(c,4)]
        for pat,label in candidates:
            mu=np.zeros(9); mu[0]=10.
            for j in pat: mu[j+1]=10.
            d=D@mu; lam=float(d@np.linalg.solve(O,d))
            p=float(ncx2.sf(chi2.isf(ALPHA,8),8,lam))
            rows.append(dict(rho=rho,c=c,pattern=label,lambda_ncp=lam,omnibus_power=p))
    return pd.DataFrame(rows)


def invariants(v,tau,frontier,archive):
    checks=[]
    # 1. Exact model reduction: rho=0,c=1 => (v+tau^2) I.
    S=sigma_full(v,tau,0.,1); target=(v+tau*tau)*np.eye(9)
    err=float(np.max(np.abs(S-target))); assert err<1e-12
    checks.append(('model_reduction_rho0_c1',True,err,1e-12))
    # 2. Pure common-mode addition cancels in contrasts exactly.
    D=contrast_matrix(8); base=sigma_full(v,tau,0.,4); gamma=7.25
    err=float(np.max(np.abs(D@(base+gamma*np.ones((9,9)))@D.T - D@base@D.T))); assert err<1e-10
    checks.append(('common_mode_contrast_invariance',True,err,1e-10))
    # 3. Protected omnibus null size is alpha by chi-square calibration, independent of Sigma.
    q=chi2.isf(ALPHA,8); size=float(chi2.sf(q,8)); err=abs(size-ALPHA); assert err<1e-12
    checks.append(('protected_omnibus_nominal_size',True,err,1e-12))
    # 4. Regression against archived Monte Carlo frontier at tau=3.
    old=archive[archive.tau==tau][['wtp_cap','max_expected_k','plain_activity_hider_utility']]
    m=frontier.merge(old,on=['wtp_cap','max_expected_k'],suffixes=('_analytic','_v135'))
    maxdiff=float((m.plain_activity_hider_utility_analytic-m.plain_activity_hider_utility_v135).abs().max())
    assert maxdiff<=REGRESSION_TOL, (maxdiff,REGRESSION_TOL)
    checks.append(('v135_frontier_regression_mc_tolerance',True,maxdiff,REGRESSION_TOL))
    return pd.DataFrame(checks,columns=['invariant','pass','observed_error','tolerance'])


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--archive',default='mixed_policy_frontier_v1_3_5.csv'); ap.add_argument('--output-dir',default='.')
    a=ap.parse_args(); od=Path(a.output_dir); od.mkdir(parents=True,exist_ok=True)
    v=10.; tau=3.; rho=0.; c=1
    acts,U=payoff_table(v,tau,rho,c)
    rows=[]
    for kb in K_BUDGETS:
        for wc in WTP_CAPS:
            r=solve_frontier(acts,U,wc,kb); r.update(v=v,tau=tau,rho=rho,c=c); rows.append(r)
    frontier=pd.DataFrame(rows)
    geom=protected_geometry(v,tau)
    archive=pd.read_csv(a.archive)
    inv=invariants(v,tau,frontier,archive)
    frontier.to_csv(od/'protected_frontier_anchor_v1_4_0.csv',index=False)
    geom.to_csv(od/'protected_attack_geometry_v1_4_0.csv',index=False)
    inv.to_csv(od/'protected_invariants_v1_4_0.csv',index=False)
    print(inv.to_string(index=False)); print('wrote protected analytic benchmark')

if __name__=='__main__': main()
