#!/usr/bin/env python3
"""v1.4.2 protected-covariance analytic benchmark.

Purpose
-------
1. Establish the protected-Sigma benchmark before estimated/poisoned covariance.
2. Use exact Gaussian / noncentral-chi-square power, not Monte Carlo.
3. Let the hider choose the reach-limited level-attack geometry endogenously.
4. Validate analytic null size and power by seeded direct simulation.
5. Regression-check the rho=0,c=1 model reduction against the archived
   v1.3.3 Monte Carlo powers at the cell level using standardized residuals.

The archived v1.3.3 powers use common random numbers, so residuals across cells
are correlated. The regression diagnostic therefore checks that their spread is
consistent with binomial Monte Carlo noise and that the common mean shift is not
large; it does not require a downstream frontier to match sampled noise exactly.
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
MC_INVARIANT_REPS = 200000
MC_INVARIANT_SEED = 20261102
ARCHIVE_MC_REPS = 10000


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


def simulate_protected_case(v: float, tau: float, rho: float, c: int, pattern: tuple[int,...],
                            s: float=10., reps: int=MC_INVARIANT_REPS, seed: int=MC_INVARIANT_SEED):
    """Directly simulate k=8 protected tests from N(mu, Sigma)."""
    S=sigma_full(v,tau,rho,c)
    mu=np.zeros(9); mu[0]=s
    for j in pattern: mu[j+1]=s
    rng=np.random.default_rng(seed)
    x=rng.multivariate_normal(mu,S,size=reps,check_valid='raise',method='cholesky')
    D=contrast_matrix(8); O=D@S@D.T
    zc=x@D.T
    # Mahalanobis Q for centered contrasts.
    q=np.einsum('bi,ij,bj->b',zc,np.linalg.inv(O),zc)
    a=np.r_[1.,np.full(8,-1/8.)]
    z=(x@a)/math.sqrt(float(a@S@a))
    om=float(np.mean(q>chi2.isf(ALPHA,8)))
    comb=float(np.mean((z>norm.isf(ALPHA/2)) | (q>chi2.isf(ALPHA/2,8))))
    pa=exact_power(mu,S,'omnibus_protected')[0]
    pc=exact_power(mu,S,'combined_protected')[0]
    return om,pa,comb,pc


def simulation_invariants(v: float, tau: float) -> pd.DataFrame:
    """Exercise Sigma, whitening, null size, and noncentral-power code end to end."""
    cases=[
        ('null_rho0_c4',0.,4,(),0.),
        ('aligned_rho0_c4',0.,4,(0,1,2,3),10.),
        ('misaligned_rho0_c4',0.,4,(0,1,4,5),10.),
        ('aligned_rho05_c4',.5,4,(0,1,2,3),10.),
        ('aligned_rho09_c2',.9,2,(0,1,2,3),10.),
    ]
    rows=[]
    for i,(name,rho,c,pat,sig) in enumerate(cases):
        om,oa,cm,ca=simulate_protected_case(v,tau,rho,c,pat,s=sig,seed=MC_INVARIANT_SEED+i)
        for method,sim,ana in [('omnibus',om,oa),('combined',cm,ca)]:
            se=math.sqrt(max(ana*(1-ana),1e-12)/MC_INVARIANT_REPS)
            zerr=(sim-ana)/se
            # Four-sigma MC envelope plus a tiny numerical allowance.
            passed=abs(sim-ana) <= 4*se+2e-4
            assert passed,(name,method,sim,ana,se,zerr)
            rows.append(dict(case=name,rho=rho,c=c,pattern='+'.join(map(str,pat)) if pat else 'none',
                             signal_s=sig,method=method,simulated_power=sim,analytic_power=ana,
                             mc_se=se,standardized_error=zerr,passed=passed))
    return pd.DataFrame(rows)


def archive_cell_regression(v: float, tau: float, archive_cells: pd.DataFrame) -> tuple[pd.DataFrame,dict]:
    """Compare 675 non-null v1.3.3 protected cells with exact independent-model powers."""
    amap={'protected_scale':'protected_scale','omnibus_protected':'omnibus_protected',
          'combined_protected':'combined_protected'}
    f=archive_cells[(archive_cells.tau==tau) & archive_cells.estimator.isin(amap) &
                    archive_cells.attack_mode.isin(['none','level']) & (archive_cells.signal_s>0)].copy()
    assert len(f)==675,len(f)
    exact=[]
    for row in f.itertuples(index=False):
        k=int(row.k); s0=float(row.signal_s); r=int(row.reach_r); method=amap[row.estimator]
        if r==0:
            pat=()
        else:
            pat=tuple(range(r))
        p=average_power(v,tau,0.,1,k,method,s0,r,pat)
        exact.append(p)
    f['analytic_power']=exact
    se=np.sqrt(np.maximum(f.analytic_power*(1-f.analytic_power),1e-12)/ARCHIVE_MC_REPS)
    f['mc_se']=se
    f['standardized_residual']=(f.power-f.analytic_power)/se
    mean=float(f.standardized_residual.mean())
    sd=float(f.standardized_residual.std(ddof=1))
    # These are diagnostics for correlated CRN residuals, not iid-normal tests.
    # A spread near one is the key Monte Carlo-noise check; the mean may shift
    # because every attack reused the same random draws in v1.3.3. The |mean|
    # bound of 1.5 was frozen from four independent v1.3.3 seed checks whose
    # observed means were +0.79, +0.02, +0.49, and +0.05; 1.5 is roughly twice
    # the largest observed common shift and is not tuned to the archived seed.
    passed=(0.65 <= sd <= 1.35) and (abs(mean) <= 1.5)
    assert passed,(mean,sd)
    summary=dict(n_cells=len(f),mean_standardized_residual=mean,sd_standardized_residual=sd,
                 sd_lower=0.65,sd_upper=1.35,abs_mean_upper=1.5,passed=passed)
    cols=['tau','k','estimator','signal_s','reach_r','attack_mode','power','analytic_power','mc_se','standardized_residual']
    return f[cols],summary


def invariants(v,tau,cell_summary,simdf):
    checks=[]
    # 1. Exact model reduction: rho=0,c=1 => (v+tau^2) I.
    S=sigma_full(v,tau,0.,1); target=(v+tau*tau)*np.eye(9)
    err=float(np.max(np.abs(S-target))); assert err<1e-12
    checks.append(('model_reduction_rho0_c1',True,err,1e-12,'exact matrix identity'))
    # 2. Pure common-mode addition cancels in contrasts exactly.
    D=contrast_matrix(8); base=sigma_full(v,tau,0.,4); gamma=7.25
    err=float(np.max(np.abs(D@(base+gamma*np.ones((9,9)))@D.T - D@base@D.T))); assert err<1e-10
    checks.append(('common_mode_contrast_invariance',True,err,1e-10,'exact contrast identity'))
    # 3. Seeded direct simulation exercises protected null size.
    null=simdf[(simdf.case=='null_rho0_c4') & (simdf.method=='omnibus')].iloc[0]
    err=abs(float(null.simulated_power)-ALPHA)
    tol=4*float(null.mc_se)+2e-4
    checks.append(('protected_omnibus_null_size_simulated',bool(null.passed),err,tol,'seeded direct N(mu,Sigma) simulation'))
    # 4. Seeded direct simulation matches analytic noncentral power across clustered cases.
    nonnull=simdf[simdf.signal_s>0]
    maxz=float(nonnull.standardized_error.abs().max()); passed=bool(nonnull.passed.all()); assert passed
    checks.append(('protected_power_matches_noncentral_prediction',True,maxz,4.0,'max |MC-analytic| in MC standard errors'))
    # 5. Regression reason: v1.3.3 per-cell residual spread matches MC noise; CRN mean shift bounded.
    checks.append(('v133_cellwise_mc_regression',bool(cell_summary['passed']),
                   float(cell_summary['sd_standardized_residual']),1.35,
                   f"sd in [0.65,1.35], |mean| <= 1.5; bound based on four seed means [+0.79,+0.02,+0.49,+0.05]; mean={cell_summary['mean_standardized_residual']:.6f}"))
    return pd.DataFrame(checks,columns=['invariant','pass','observed','tolerance_or_bound','basis'])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--archive-frontier',default='mixed_policy_frontier_v1_3_5.csv')
    ap.add_argument('--archive-cells',default='joint_strategy_results_v1_3_3.csv')
    ap.add_argument('--output-dir',default='.')
    a=ap.parse_args(); od=Path(a.output_dir); od.mkdir(parents=True,exist_ok=True)
    v=10.; tau=3.; rho=0.; c=1
    acts,U=payoff_table(v,tau,rho,c)
    rows=[]
    for kb in K_BUDGETS:
        for wc in WTP_CAPS:
            r=solve_frontier(acts,U,wc,kb); r.update(v=v,tau=tau,rho=rho,c=c); rows.append(r)
    frontier=pd.DataFrame(rows)
    geom=protected_geometry(v,tau)
    simdf=simulation_invariants(v,tau)
    archived_cells=pd.read_csv(a.archive_cells)
    residuals,cell_summary=archive_cell_regression(v,tau,archived_cells)
    inv=invariants(v,tau,cell_summary,simdf)
    frontier.to_csv(od/'protected_frontier_anchor_v1_4_2.csv',index=False)
    geom.to_csv(od/'protected_attack_geometry_v1_4_2.csv',index=False)
    simdf.to_csv(od/'protected_simulation_checks_v1_4_2.csv',index=False)
    residuals.to_csv(od/'protected_v133_cell_residuals_v1_4_2.csv',index=False)
    inv.to_csv(od/'protected_invariants_v1_4_2.csv',index=False)
    print(inv.to_string(index=False))
    print('cell residual summary:',cell_summary)
    print('wrote protected analytic benchmark v1.4.2')

if __name__=='__main__': main()
