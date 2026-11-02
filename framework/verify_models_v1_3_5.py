#!/usr/bin/env python3
"""v1.3.5 mixed-policy robustness-efficiency frontier.

Reads the verified v1.3.3 payoff table. The observer may commit to a mixture
of size-valid protected-scale policies. The hider chooses after seeing the
mixture but before the realized test. For each WTP cap and expected-control
budget, an exact finite-game LP minimizes the hider's best uncontaminated
utility subject to contamination WTP <= cap.
"""
from __future__ import annotations
import argparse, math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog

BASE_ACTIVITY=.6; DETECTION_PENALTY=1.; BENEFIT_CURVATURE=5.; C_MEASURE=.01
PROTECTED={'protected_scale','omnibus_protected','combined_protected'}
WTP_CAPS=(0.,.005,.01,.025,.05,.10,.15,.20)
K_BUDGETS=(4.,6.,8.)
ATTACK_COLS=['signal_s','reach_r','attack_mode','spread_delta']

def benefit(s): return BASE_ACTIVITY*math.log1p(s/BENEFIT_CURVATURE)/math.log1p(20./BENEFIT_CURVATURE) if s else 0.
def utility_zero_cost(r): return benefit(float(r.signal_s))-(float(r.power) if float(r.signal_s)>0 else 0.)

def solve_tau(df,tau,wtp_cap,k_budget):
 d=df[(df.tau==tau)&(df.estimator.isin(PROTECTED))].copy(); d['_u']=d.apply(utility_zero_cost,axis=1)
 policies=sorted([(int(k),e) for k,e in d[['k','estimator']].drop_duplicates().itertuples(index=False,name=None)])
 attacks=d[ATTACK_COLS].drop_duplicates().sort_values(ATTACK_COLS,kind='stable').reset_index(drop=True)
 pidx={p:i for i,p in enumerate(policies)}; aidx={tuple(r):i for i,r in enumerate(attacks.itertuples(index=False,name=None))}
 U=np.full((len(policies),len(attacks)),np.nan)
 for _,r in d.iterrows(): U[pidx[(int(r['k']),r['estimator'])],aidx[(r['signal_s'],r['reach_r'],r['attack_mode'],r['spread_delta'])]]=r['_u']
 if np.isnan(U).any(): raise RuntimeError('incomplete policy/attack payoff matrix')
 un=np.where(attacks.reach_r.to_numpy()==0)[0]; co=np.where(attacks.reach_r.to_numpy()>0)[0]
 kvals=np.array([p[0] for p in policies],float)
 best=None
 # Enumerate which uncontaminated attack attains the max. This makes the max-difference WTP constraint exact and linear.
 for a0 in un:
  c=U[:,a0].copy(); Aub=[]; bub=[]
  for a in un: Aub.append(U[:,a]-U[:,a0]); bub.append(0.)
  for a in co: Aub.append(U[:,a]-U[:,a0]); bub.append(float(wtp_cap))
  Aub.append(kvals); bub.append(float(k_budget))
  res=linprog(c,A_ub=np.asarray(Aub),b_ub=np.asarray(bub),A_eq=np.ones((1,len(policies))),b_eq=[1.],bounds=[(0.,1.)]*len(policies),method='highs')
  if not res.success: continue
  x=res.x; plain_vals=U[:,un].T@x; cont_vals=U[:,co].T@x
  plain=float(plain_vals.max()); cont=float(cont_vals.max()); wtp=max(0.,cont-plain)
  if wtp>wtp_cap+1e-8: continue
  if best is None or plain<best['plain']-1e-10:
   best={'plain':plain,'cont':cont,'wtp':wtp,'x':x,'policies':policies,'expected_k':float(kvals@x),
         'a0':int(un[np.argmax(plain_vals)]),'ac':int(co[np.argmax(cont_vals)]),'attacks':attacks}
 if best is None: return None
 support=[(p,float(w)) for p,w in zip(best['policies'],best['x']) if w>1e-8]
 a0=best['attacks'].iloc[best['a0']]; ac=best['attacks'].iloc[best['ac']]
 return {'tau':int(tau) if float(tau).is_integer() else tau,'wtp_cap':wtp_cap,'max_expected_k':k_budget,
  'plain_activity_hider_utility':best['plain'],'best_contaminated_hider_utility_zero_cost':best['cont'],'realized_contamination_wtp':best['wtp'],
  'expected_k':best['expected_k'],'expected_measurement_cost':C_MEASURE*best['expected_k'],'support_size':len(support),
  'policy_mixture':' + '.join(f'{w:.9f}*{e}[k={k}]' for (k,e),w in support),
  'best_uncontaminated_signal':float(a0.signal_s),'best_contaminated_signal':float(ac.signal_s),'best_contaminated_reach':int(ac.reach_r),
  'best_contaminated_mode':ac.attack_mode,'best_contaminated_delta':float(ac.spread_delta)}

def main():
 p=argparse.ArgumentParser(); p.add_argument('--input',default='joint_strategy_results_v1_3_3.csv'); p.add_argument('--output-dir',default='.')
 a=p.parse_args(); df=pd.read_csv(a.input); rows=[]
 for tau in sorted(df.tau.unique()):
  for kb in K_BUDGETS:
   for wc in WTP_CAPS:
    r=solve_tau(df,float(tau),float(wc),float(kb))
    if r: rows.append(r)
 out=pd.DataFrame(rows); od=Path(a.output_dir); od.mkdir(parents=True,exist_ok=True)
 out.to_csv(od/'mixed_policy_frontier_v1_3_5.csv',index=False)
 print('wrote',len(out),'mixed-frontier rows')
if __name__=='__main__': main()
