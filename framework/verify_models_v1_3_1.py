#!/usr/bin/env python3
"""Version 1.3.1: add omnibus and combined exchangeability-contrast tests.

Only numpy/scipy (standard library for CSV/JSON). No factual inference about
nonhuman populations. Independent Gaussian channel averages approximate a
high-count Poisson ON/OFF experiment with persistent channel heterogeneity.

Run: python verify_models_v1_3_1.py --output-dir .
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from scipy.stats import chi2, norm, t

SEED = 20261101
M = 8
KS = (4, 6, 8)
TAUS = (0.0, 3.0, 10.0)
B = 1000.0
BLOCKS = 100
V_POISSON = B / BLOCKS
ALPHA = .01
S_VALUES = (0., 5., 10., 20., 30.)
DELTA_VALUES = (10., 20.)
N_REPS = 30000
CAL_REPS = 250000
BASE_ACTIVITY = .6
DETECTION_PENALTY = 1.
C_REACH = .02
C_SPREAD = .04
C_MEASURE = .01
C_METHOD = {'empirical_std': 0., 'empirical_mad': .02,
            'protected_scale': .06, 'physics_only': 0.,
            'omnibus_protected': .06, 'combined_protected': .06,
            'omnibus_physics': 0., 'combined_physics': 0.}
FALSE_ALARM_COST = .1

@dataclass(frozen=True)
class Attack:
    s: float
    r: int
    mode: str
    delta: float

    @property
    def name(self) -> str:
        return f's={self.s:g}|r={self.r}|{self.mode}|delta={self.delta:g}'


def attacks() -> list[Attack]:
    options = [Attack(0., 0, 'none', 0.)]
    for s in S_VALUES[1:]:
        options.append(Attack(s, 0, 'none', 0.))
        for r in (2, 4):
            options.append(Attack(s, r, 'level', 0.))
            for delta in DELTA_VALUES:
                options.append(Attack(s, r, 'spread', delta))
                options.append(Attack(s, r, 'mixed', delta))
    return options


def contamination_vector(a: Attack) -> np.ndarray:
    """Hider fixes identities before privately randomized observer sample.

    Level attacks add s to the first r controls. Spread attacks add balanced
    +/-delta offsets to r controls; mixed attacks add s plus those offsets.
    """
    out = np.zeros(M)
    if a.r == 0:
        return out
    if a.mode in ('level', 'mixed'):
        out[:a.r] += a.s
    if a.mode in ('spread', 'mixed'):
        out[:a.r:2] += a.delta
        out[1:a.r:2] -= a.delta
    return out


def hider_benefit(a: Attack) -> float:
    """Activity earns benefit; detection and spoofing have explicit costs."""
    benefit = BASE_ACTIVITY * math.log1p(a.s/5.) / math.log1p(20./5.) if a.s else 0.
    operational_cost = C_REACH*a.r + C_SPREAD*a.r*(a.delta/20.)**2
    return benefit - operational_cost


def mad_scale(x: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    med = np.median(x, axis=1)
    scale = 1.4826 * np.median(np.abs(x - med[:, None]), axis=1)
    return med, np.maximum(scale, 1.e-10)


def statistic(on: np.ndarray, off: np.ndarray, method: str, tau: float) -> np.ndarray:
    k = off.shape[1]
    if method == 'empirical_std':
        center = off.mean(axis=1)
        sd = off.std(axis=1, ddof=1)
        return (on-center)/(np.maximum(sd,1.e-10)*np.sqrt(1+1/k))
    if method == 'empirical_mad':
        center, sd = mad_scale(off)
        return (on-center)/(sd*np.sqrt(1+1/k))
    center = off.mean(axis=1)
    assumed_var = V_POISSON + (tau**2 if method == 'protected_scale' else 0.)
    return (on-center)/np.sqrt(assumed_var*(1+1/k))



def omnibus_statistic(on: np.ndarray, off: np.ndarray, assumed_var: float) -> np.ndarray:
    """Known-scale equal-means chi-square statistic, df = number of controls.

    Shared unknown background cancels. The chi-square calibration assumes
    independent channel Gaussian errors with a common known variance.
    """
    samples = np.concatenate((on[:, None], off), axis=1)
    return np.sum((samples - samples.mean(axis=1,keepdims=True))**2,axis=1)/assumed_var


def rejection(on: np.ndarray, off: np.ndarray, method: str, tau: float, crit: dict) -> np.ndarray:
    k = off.shape[1]
    if method in ('omnibus_protected','combined_protected','omnibus_physics','combined_physics'):
        known = method.endswith('protected')
        v = V_POISSON + (tau*tau if known else 0.)
        q=omnibus_statistic(on,off,v)
        if method.startswith('omnibus'):
            return q > chi2.isf(ALPHA,k)
        # Bonferroni family-wise size <= alpha: directional + omnibus.
        z=(on-off.mean(axis=1))/math.sqrt(v*(1+1/k))
        return (z > norm.isf(ALPHA/2)) | (q > chi2.isf(ALPHA/2,k))
    return statistic(on,off,method,tau)>crit[f'{k}:{method}']

def null_cutoffs(rng: np.random.Generator, reps: int=CAL_REPS) -> dict:
    """Null calibration for MAD at each k, with independent fixed RNG.

    The other null tests have analytic critical values under the stated
    independent-Gaussian assumptions.
    """
    crit = {}
    for k in KS:
        x = rng.standard_normal((reps,k+1))
        z = statistic(x[:,0],x[:,1:],'empirical_mad',tau=0.)
        crit[f'{k}:empirical_mad'] = float(np.quantile(z,1-ALPHA))
        crit[f'{k}:empirical_std'] = float(t.isf(ALPHA,k-1))
        crit[f'{k}:protected_scale'] = float(norm.isf(ALPHA))
        crit[f'{k}:physics_only'] = float(norm.isf(ALPHA))
    return crit


def simulate_payoff(tau: float, reps: int, crit: dict, seed: int) -> tuple[list[dict], np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    v = V_POISSON+tau*tau
    # Channel-specific persistent offsets + block-count noise; N(v) total.
    on0 = rng.normal(0, np.sqrt(v), size=reps)
    controls0 = rng.normal(0,np.sqrt(v),size=(reps,M))
    perms = np.argsort(rng.random((reps,M)),axis=1)
    candidate_attacks = attacks()
    policies = [(k,method) for k in KS for method in C_METHOD]
    powers = np.zeros((len(policies),len(candidate_attacks)))
    for j,a in enumerate(candidate_attacks):
        on = on0+a.s
        offset=contamination_vector(a)
        for d,(k,method) in enumerate(policies):
            sel=perms[:,:k]
            off=controls0[np.arange(reps)[:,None],sel] + offset[sel]
            powers[d,j]=float(np.mean(rejection(on,off,method,tau,crit)))

    # The null row's rejection frequency is the Monte Carlo false-alarm rate.
    assert candidate_attacks[0].s == 0
    false_alarm=powers[:,0]
    risk_penalty = np.asarray([DETECTION_PENALTY * (powers[:,j] if a.s>0 else np.zeros(len(policies)))
                               for j,a in enumerate(candidate_attacks)]).T
    attack_benefit=np.array([hider_benefit(a) for a in candidate_attacks])[None,:]
    hider_utility=attack_benefit-risk_penalty
    defender_loss=np.empty_like(powers)
    for d,(k,method) in enumerate(policies):
        base_cost = C_MEASURE*k + C_METHOD[method] + FALSE_ALARM_COST*false_alarm[d]
        for j,a in enumerate(candidate_attacks):
            defender_loss[d,j]=base_cost + (a.s/20.)*(1-powers[d,j])
    rows=[]
    for d,(k,method) in enumerate(policies):
        for j,a in enumerate(candidate_attacks):
            rows.append({'tau':tau,'k':k,'estimator':method,'signal_s':a.s,'reach_r':a.r,
                         'attack_mode':a.mode,'spread_delta':a.delta,
                         'power':powers[d,j],'miss':1-powers[d,j],
                         'false_alarm_size':false_alarm[d],
                         'hider_utility':hider_utility[d,j],
                         'defender_loss':defender_loss[d,j]})
    return rows, hider_utility, defender_loss, powers


def leader_solution(hu: np.ndarray, dl: np.ndarray, allowed: np.ndarray, strict_margin: float=0.) -> dict:
    """Enumerate follower best-response regions and solve each leader LP.

    Strong Stackelberg ties favor defender; conditional worst-case ties are
    also evaluated at the selected policy. Numerical tolerances explicit.
    """
    n_def, n_attack=hu.shape
    assert allowed.shape == (n_def,) and np.any(allowed)
    best=None
    for j in range(n_attack):
        # Sum_i p_i [u_i,a - u_i,j] <= -margin for all a != j.
        rivals=np.arange(n_attack)!=j
        A=(hu[:,rivals]-hu[:,[j]]).T
        b=np.full(A.shape[0],-strict_margin)
        res=linprog(dl[:,j],A_ub=A,b_ub=b,A_eq=np.ones((1,n_def)),b_eq=[1.],
                    bounds=[(0.,1.) if ok else (0.,0.) for ok in allowed], method='highs')
        if not res.success:
            continue
        p=np.clip(res.x,0.,1.);p/=p.sum()
        u=p@hu
        ties=np.flatnonzero(u>=u.max()-1e-7)
        # Strong tie break chooses lowest observer loss among best replies.
        response=min(ties, key=lambda a:float(p@dl[:,a]))
        loss=float(p@dl[:,response])
        obj=(loss, p, int(response), float(u[response]))
        if best is None or obj[0]<best[0]:
            best=obj
    if best is None:
        raise RuntimeError('No feasible Stackelberg response region')
    loss,p,response,utility=best
    return {'leader_probs':p,'attack_index':response,
            'leader_loss':loss,'attacker_utility':utility,
            'follower_exploitability':max(0.,float(np.max(p@hu)-utility))}


def benchmark_t_test(n: int=200000) -> list[dict]:
    """Directly reproduce the reader's spread-inflation experiment.

    Here the hider reaches exactly two of the k measured controls; it does
    not face unobserved controls. The baseline variance of each channel mean
    is 10. This benchmark has its own distinct experimental sampling frame.
    """
    rng=np.random.default_rng(SEED+1)
    rows=[]
    for k in (4,8):
        base=rng.normal(0,np.sqrt(V_POISSON),size=(n,k+1))
        for delta in (0.,10.,20.):
            x=base.copy()
            x[:,0]+=20.
            x[:,1]+=delta
            x[:,2]-=delta
            z=statistic(x[:,0],x[:,1:],'empirical_std',tau=0.)
            rows.append({'k':k,'delta':delta,'power':float(np.mean(z>t.isf(ALPHA,k-1))),
                         'mc_n':n})
    return rows


def write_csv(path:Path, rows:list[dict]) -> None:
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        writer.writeheader();writer.writerows(rows)


def main(out:Path, reps:int=N_REPS)->dict:
    out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(SEED)
    crit=null_cutoffs(rng)
    bench=benchmark_t_test()
    bench_lookup={(x['k'],x['delta']):x['power'] for x in bench}
    # Comparisons are statistical, not equality tests: independent Monte Carlo.
    for key, expected in { (4,0.):.774,(4,10.):.007,(4,20.):0.,
                           (8,0.):.991,(8,10.):.549,(8,20.):.001 }.items():
        assert abs(bench_lookup[key]-expected)<.013,(key,bench_lookup[key],expected)
    allrows=[]; equilibria=[]
    for tau in TAUS:
        rows,hu,dl,powers=simulate_payoff(tau,reps,crit,SEED+int(tau)*100+2)
        allrows.extend(rows)
        # A size-invalid calibration is displayed in sensitivity outputs,
        # but excluded from the valid design game. Otherwise an oracle could
        # intentionally purchase cheap false positives for a lower price.
        policies=[(k,m) for k in KS for m in C_METHOD]
        allowed=np.asarray([abs(float(powers[i,0])-ALPHA)<.007
                            for i in range(len(policies))])
        eq=leader_solution(hu,dl,allowed)
        attack=attacks()[eq['attack_index']]
        probs=eq['leader_probs']
        row={'tau':tau,'best_response':attack.name,'signal_s':attack.s,
             'reach_r':attack.r,'attack_mode':attack.mode,'spread_delta':attack.delta,
             'expected_detection_power':float(probs@powers[:,eq['attack_index']]),
             'size_valid_policies':';'.join(f'{k}:{m}' for valid,(k,m) in zip(allowed,policies) if valid),
             'expected_false_alarm':float(probs@powers[:,0]),
             'expected_k':float(sum(p*k for p,(k,m) in zip(probs,policies))),
             'defender_loss':eq['leader_loss'],
             'hider_utility':eq['attacker_utility'],
             'follower_exploitability':eq['follower_exploitability'],
             'policy':';'.join(f'{k}:{m}={p:.6f}' for p,(k,m) in zip(probs,policies) if p>1.e-5)}
        equilibria.append(row)
        assert eq['follower_exploitability']<1.e-6
        # External calibration maintains size under heterogeneous Gaussian null.
        for d,(k,method) in enumerate(policies):
            if method in ('empirical_std','empirical_mad','protected_scale',
                          'omnibus_protected','combined_protected'):
                assert abs(powers[d,0]-ALPHA)<.007,(tau,k,method,powers[d,0])
    # Clean pure measurement identifies positive signal in no-spoof case.
    write_csv(out/'joint_strategy_results_v1_3_1.csv',allrows)
    write_csv(out/'stackelberg_joint_equilibria_v1_3_1.csv',equilibria)
    write_csv(out/'spread_benchmark_v1_3_1.csv',bench)
    summary={'model':'v1.3.1 synthetic Gaussian ON/OFF; attacker chooses s, r, mode and delta; defender has directional/omnibus/combined policies',
             'seed':SEED,'n_reps_per_policy':reps,'null_calibration_reps':CAL_REPS,
             'critical_values':crit,'cost_parameters':{'activity_benefit':BASE_ACTIVITY,
              'detection_penalty':DETECTION_PENALTY,'c_reach':C_REACH,'c_spread':C_SPREAD,
              'c_measure':C_MEASURE,'method_costs':C_METHOD,'false_alarm_cost':FALSE_ALARM_COST},
             'benchmark':bench,'equilibria':equilibria,
             'limitations':['private control selection; fixed attacked identities before sampling',
             'independent Gaussian channel offsets; no correlated heterogeneity',
             'protected scale is an oracle available only when clean calibration is physically secured',
             'physics-only ignores tau and can have incorrect false-alarm size',
             'finite discrete strategy sets; follower sees leader commitment, not realization',
             'omnibus tests assume independent exchangeable Gaussian channels with known scale',
             'one-sided and omnibus tests address distinct alternatives; Bonferroni combination controls family-wise size',
             'Monte Carlo best replies and equilibrium depend on seed and costs',
             'no data about actual concealed populations']}
    (out/'results_v1_3_1.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--output-dir',type=Path,default=Path('.'))
    ap.add_argument('--reps',type=int,default=N_REPS)
    args=ap.parse_args()
    summary=main(args.output_dir,args.reps)
    for e in summary['equilibria']:
        print(f"tau={e['tau']:g}, policy={e['policy']}, hider={e['best_response']}, "
              f"power={e['expected_detection_power']:.4f}, "+
              f"size={e['expected_false_alarm']:.4f}, loss={e['defender_loss']:.4f}")
    print('All v1.3.1 checks pass.')
