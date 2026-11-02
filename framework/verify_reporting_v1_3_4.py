#!/usr/bin/env python3
"""Regenerate the v1.3.4 reporting tables from v1.3.3 simulation output.

Inputs:
  joint_strategy_results_v1_3_3.csv
Outputs:
  contamination_wtp_v1_3_4.csv
  robustness_efficiency_frontier_v1_3_4.csv

This script performs no Monte Carlo simulation. It is a deterministic
post-processor for the reporting-only v1.3.4 patch.
"""
from __future__ import annotations
import argparse, math
from pathlib import Path
import pandas as pd

BASE_ACTIVITY=.6
DETECTION_PENALTY=1.0
BENEFIT_CURVATURE=5.0
ESTIMATOR_ORDER=['empirical_std','empirical_mad','protected_scale','physics_only',
                 'omnibus_protected','combined_protected','omnibus_physics','combined_physics']
PHYSICS_ONLY={'physics_only','omnibus_physics','combined_physics'}

def activity_benefit(s: float)->float:
    return BASE_ACTIVITY*math.log1p(s/BENEFIT_CURVATURE)/math.log1p(20.0/BENEFIT_CURVATURE) if s else 0.0

def zero_cost_utility(row)->float:
    return activity_benefit(float(row.signal_s)) - (DETECTION_PENALTY*float(row.power) if float(row.signal_s)>0 else 0.0)

def best_row(g: pd.DataFrame)->pd.Series:
    # Deterministic tie-breaking: utility, then lower reach, level before spread/mixed,
    # lower delta, lower signal. This reproduces the intended v1.3.4 reporting semantics.
    mode_rank={'none':0,'level':1,'spread':2,'mixed':3}
    z=g.copy()
    z['_mode_rank']=z.attack_mode.map(mode_rank).fillna(9)
    return z.sort_values(['_u0','reach_r','_mode_rank','spread_delta','signal_s'],
                         ascending=[False,True,True,True,True],kind='stable').iloc[0]

def build(inp: Path):
    df=pd.read_csv(inp)
    df['_u0']=df.apply(zero_cost_utility,axis=1)
    max_s=float(df.signal_s.max())
    rows=[]
    for tau in sorted(df.tau.unique()):
      for k in sorted(df.k.unique()):
       for est in ESTIMATOR_ORDER:
        g=df[(df.tau==tau)&(df.k==k)&(df.estimator==est)]
        if g.empty: continue
        u=best_row(g[g.reach_r==0])
        c=best_row(g[g.reach_r>0])
        wtp=float(c._u0-u._u0)
        valid=not (tau>0 and est in PHYSICS_ONLY)
        ceiling=bool(float(c.signal_s)>=max_s-1e-12)
        rows.append({
          'tau':int(tau) if float(tau).is_integer() else tau,'k':int(k),'estimator':est,
          'best_uncontaminated_signal':float(u.signal_s),'best_uncontaminated_utility':float(u._u0),
          'best_contaminated_signal':float(c.signal_s),'best_contaminated_reach':int(c.reach_r),
          'best_contaminated_mode':c.attack_mode,'best_contaminated_delta':int(c.spread_delta) if float(c.spread_delta).is_integer() else float(c.spread_delta),
          'best_contaminated_utility_zero_cost':float(c._u0),'willingness_to_pay_total':wtp,
          'willingness_to_pay_per_reached_control':wtp/float(c.reach_r),
          'willingness_to_pay_positive':max(0.0,wtp),'size_valid':bool(valid),
          'contaminated_signal_hits_grid_ceiling':ceiling,
          'wtp_interpretation':('size-invalid; exclude from design comparison' if not valid else ('lower bound: contaminated optimum hits signal-grid ceiling' if ceiling else 'interior/grid-not-binding at reported optimum'))})
    wtp=pd.DataFrame(rows)
    valid=wtp[wtp.size_valid].copy()
    # Pareto labels over pure policies: minimize both plain-activity utility and positive WTP.
    pareto=[]
    for _,r in valid.iterrows():
      same=valid[valid.tau==r.tau]
      dominated=((same.best_uncontaminated_utility<=r.best_uncontaminated_utility+1e-15)&
                 (same.willingness_to_pay_positive<=r.willingness_to_pay_positive+1e-15)&
                 ((same.best_uncontaminated_utility<r.best_uncontaminated_utility-1e-15)|
                  (same.willingness_to_pay_positive<r.willingness_to_pay_positive-1e-15))).any()
      pareto.append(not dominated)
    valid['pareto_nondominated']=pareto
    frontier=valid[['tau','k','estimator','best_uncontaminated_utility','willingness_to_pay_positive','pareto_nondominated','contaminated_signal_hits_grid_ceiling']].rename(columns={
      'best_uncontaminated_utility':'uncontaminated_hider_utility',
      'willingness_to_pay_positive':'contamination_wtp_positive'})
    frontier=frontier.sort_values(['tau','pareto_nondominated','contamination_wtp_positive','uncontaminated_hider_utility'],ascending=[True,False,True,True],kind='stable')
    return wtp,frontier

def main():
 p=argparse.ArgumentParser(); p.add_argument('--input',default='joint_strategy_results_v1_3_3.csv'); p.add_argument('--output-dir',default='.')
 a=p.parse_args(); od=Path(a.output_dir); od.mkdir(parents=True,exist_ok=True)
 w,f=build(Path(a.input)); w.to_csv(od/'contamination_wtp_v1_3_4.csv',index=False); f.to_csv(od/'robustness_efficiency_frontier_v1_3_4.csv',index=False)
 print('wrote',len(w),'WTP rows and',len(f),'pure-frontier rows')
if __name__=='__main__': main()
