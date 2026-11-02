#!/usr/bin/env python3
"""v1.2: Synthetic adversarial ON/multiple-OFF coverage game.

No extraterrestrial or UAP observations. This is a Gaussian random-effects
approximation to Poisson counting, plus an exact profile-Poisson KL check.
Requirements: numpy, scipy. Run: python verify_models_v1_2.py --output-dir DIR
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from scipy.optimize import linprog
from scipy.stats import chi2, ncx2, norm
import numpy as np

BASE = 1000.0
SIGNAL = 20.0
BLOCKS = 100
ALPHA = 0.01
M = 8


def exact_profile_poisson_kl(controls: int, spoofed: int,
                             background: float=BASE, signal: float=SIGNAL,
                             blocks: int=BLOCKS) -> float:
    """Total exact I-projection KL against equal per-channel rates.

    Number of channels is controls+1, ON has +signal, and spoofed controls
    have +signal. The best-fit null has the pooled mean. Per-block rates.
    """
    assert 0 <= spoofed <= controls
    means = [background + signal] * (1 + spoofed) + [background] * (controls - spoofed)
    pool = sum(means) / len(means)
    return blocks * sum(x * math.log(x / pool) for x in means)


def coverage_pmf(m: int, k: int, r: int) -> dict[int, float]:
    """Hypergeometric number A of spoofed controls among k measured.

    All m controls exchangeable, k chosen uniformly after the adversary
    commits to r previously selected controls, assignment private.
    """
    assert 1 <= k <= m and 0 <= r <= m
    denom = math.comb(m, k)
    return {a: math.comb(r, a) * math.comb(m-r, k-a) / denom
            for a in range(max(0, k-(m-r)), min(k, r)+1)}


def contrast_metrics(k: int, a: int, tau: float,
                     background: float=BASE, signal: float=SIGNAL,
                     blocks: int=BLOCKS, alpha: float=ALPHA,
                     false_null_odds: float=10.0) -> dict:
    """Known-variance Gaussian contrast model, true ON+spoofed OFF shift.

    Samples are channel averages over `blocks` independent Poisson periods
    with persistent random channel offsets u_i~N(0,tau**2).
    After profiling a shared unknown background, contrast covariance is
    v*P, v=B/blocks+tau**2, P=I-11'/n.

    Omnibus Q=||P x||²/v: central Chi²_k under null, noncentral Chi²_k
    under attack with noncentrality 2*profile_KL. The separate clean-only
    likelihood ratio deliberately mis-specifies the possibility of spoofing.
    """
    assert 1 <= k and 0 <= a <= k and tau >= 0
    v = background/blocks + tau**2
    lam = signal**2/v * (1+a)*(k-a)/(k+1)
    kl = lam / 2
    cutoff = chi2.isf(alpha, k)
    power = ncx2.sf(cutoff, k, lam)
    # Misspecified clean-only direction: expected log BF(H1 clean/H0).
    clean_kl = signal**2 * k/(2*v*(k+1))
    logbf_mean = clean_kl * (1-2*a/k)
    logbf_sd = math.sqrt(2*clean_kl)
    false_null = norm.cdf((-math.log(false_null_odds)-logbf_mean)/logbf_sd)
    declared_present = norm.sf((math.log(false_null_odds)-logbf_mean)/logbf_sd)
    return {'k':k, 'a':a, 'tau':tau, 'variance_v':v,
            'profile_KL_gaussian':kl, 'noncentrality':lam,
            'omnibus_power':power, 'omnibus_miss':1-power,
            'clean_model_KL':clean_kl,
            'clean_only_mean_logBF':logbf_mean,
            'clean_only_false_null_probability':false_null,
            'clean_only_confident_presence_probability':declared_present}


def coverage_case(m: int, k: int, r: int, tau: float,
                  alpha: float=ALPHA) -> dict:
    pmf=coverage_pmf(m,k,r)
    metrics=[(a,p,contrast_metrics(k,a,tau,alpha=alpha)) for a,p in pmf.items()]
    return {'m':m,'k':k,'r':r,'tau':tau,'alpha':alpha,
            'p_all_controls_spoofed':pmf.get(k,0.0),
            'expected_spoofed_controls':sum(a*p for a,p in pmf.items()),
            'expected_KL_nats':sum(p*x['profile_KL_gaussian'] for a,p,x in metrics),
            'omnibus_power':sum(p*x['omnibus_power'] for a,p,x in metrics),
            'omnibus_miss':sum(p*x['omnibus_miss'] for a,p,x in metrics),
            'clean_only_false_null_probability':sum(p*x['clean_only_false_null_probability'] for a,p,x in metrics)}


def actual_false_alarm(k: int, tau_true: float, tau_assumed: float,
                       alpha: float=ALPHA) -> float:
    """If null variance is falsely treated as smaller, size inflates."""
    va=BASE/BLOCKS+tau_assumed**2
    vt=BASE/BLOCKS+tau_true**2
    return float(chi2.sf(chi2.isf(alpha,k)*va/vt,k))


def follower_response(p: np.ndarray, miss: np.ndarray, attacker_cost: float,
                      defender_cost: float=0.0, tolerance: float=1e-8) -> int:
    """Hider best-responds; Strong Stackelberg tie-breaking helps defender."""
    rset=np.arange(miss.shape[1])
    utilities=p@miss - attacker_cost*rset
    best=np.flatnonzero(utilities >= utilities.max()-tolerance)
    # Defender cost is identical across follower actions; minimize miss.
    return int(min(best, key=lambda r:(float(p@miss[:,r]),int(r))))


def stackelberg_coverage(m: int, tau: float, defender_cost: float,
                         attacker_cost: float, max_reach: int=4,
                         incentive_margin: float=0.002, alpha: float=ALPHA) -> dict:
    """Leader commits to distribution over k=1..m; follower chooses r=0..m.

    Enumerate follower best-response regions, solve one LP per r. Strong
    Stackelberg tie-breaking in defender's favor; report it explicitly.
    Utility for defender = -(omnibus miss probability + cD*k)
    Utility for hider = +(omnibus miss probability - cA*r).
    """
    assert 0 <= max_reach <= m and incentive_margin >= 0
    miss=np.asarray([[coverage_case(m,k,r,tau,alpha)['omnibus_miss']
                      for r in range(max_reach+1)] for k in range(1,m+1)])
    kvec=np.arange(1,m+1,dtype=float)
    sols=[]
    for r in range(max_reach+1):
        # p @ (M[:,r]-M[:,j]) >= costA*(r-j)
        # p @ (M[:,j]-M[:,r]) <= costA*(j-r)
        A=np.stack([miss[:,j]-miss[:,r] for j in range(max_reach+1) if j!=r])
        b=np.asarray([attacker_cost*(j-r)-incentive_margin
                      for j in range(max_reach+1) if j!=r])
        res=linprog(miss[:,r]+defender_cost*kvec, A_ub=A, b_ub=b,
                    A_eq=np.ones((1,m)), b_eq=np.asarray([1.]),
                    bounds=(0,None),method='highs')
        if not res.success: continue
        p=np.maximum(0.,res.x); p=p/p.sum()
        actual=follower_response(p,miss,attacker_cost,defender_cost)
        # If r is tied but follower would prefer another with *lower*
        # defender loss, this is consistent with strong Stackelberg.
        objective=float(p@miss[:,actual]+defender_cost*(p@kvec))
        sols.append((objective,p,actual,r))
    if not sols:
        raise RuntimeError('no feasible leader optimization region')
    objective,p,actual,rregion=min(sols,key=lambda item:item[0])
    miss_prob=float(p@miss[:,actual]); expected_k=float(p@kvec)
    p_full=float(sum(p[k-1]*coverage_pmf(m,k,actual).get(k,0.)
                     for k in range(1,m+1)))
    pure=[]
    for k in range(1,m+1):
        pk=np.eye(m)[k-1]
        rr=follower_response(pk,miss,attacker_cost)
        pure.append({'k':k, 'r':rr, 'observer_loss':float(miss[k-1,rr]+defender_cost*k),
                     'miss':float(miss[k-1,rr])})
    best_pure=min(pure,key=lambda x:x['observer_loss'])
    return {'m':m,'tau':tau,'alpha':alpha,'max_reach':max_reach,'defender_cost_per_control':defender_cost,
            'attacker_cost_per_reached_control':attacker_cost,
            'leader_distribution_over_k':[float(x) for x in p],
            'leader_expected_k':expected_k,
            'hider_best_response_r':int(actual),'incentive_margin':incentive_margin,
            'profiled_KL_not_used_as_payoff':True,
            'expected_omnibus_miss':miss_prob,
            'expected_prob_full_spoof':p_full,
            'leader_total_loss':objective,
            'best_pure':best_pure,
            'mixing_benefit_over_best_pure':float(best_pure['observer_loss']-objective),
            'attacker_utility':float(miss_prob-attacker_cost*actual),
            'follower_region_solved':int(rregion)}


def write_csv(path: Path,rows: list[dict], fields: list[str]) -> None:
    with path.open('w',newline='') as file:
        w=csv.DictWriter(file,fieldnames=fields,extrasaction='ignore')
        w.writeheader();w.writerows(rows)


def run(output_dir: Path|None=None)->dict:
    # Exact against profiled-Poisson original v1.1 results.
    exacts=[exact_profile_poisson_kl(2,a) for a in range(3)]
    assert abs(exacts[0]-13.22)<0.05,exacts
    assert abs(exacts[1]-13.19)<0.05,exacts
    assert abs(exacts[2])<1e-8,exacts
    assert abs(exact_profile_poisson_kl(1,0)-9.9009901308)<.02
    for m in (3,8):
        for k in range(1,m+1):
            for r in range(m+1):
                pmf=coverage_pmf(m,k,r)
                assert math.isclose(sum(pmf.values()),1,abs_tol=1e-12)
                assert math.isclose(pmf.get(k,0.),
                    math.comb(r,k)/math.comb(m,k) if r>=k else 0.,abs_tol=1e-12)
                assert math.isclose(sum(a*p for a,p in pmf.items()),k*r/m,abs_tol=1e-12)
    # Gaussian local approximation matches Poisson profile to first order.
    for a in (0,1,2):
        approx=contrast_metrics(2,a,0)['profile_KL_gaussian']
        assert abs(approx-exacts[a])<.16
    assert math.isclose(contrast_metrics(1,1,0)['omnibus_power'],ALPHA,rel_tol=1e-10)
    assert math.isclose(actual_false_alarm(2,0,0),ALPHA,rel_tol=1e-10)
    assert actual_false_alarm(2,10,0) >.6
    assert contrast_metrics(1,1,0)['clean_only_false_null_probability'] > .95
    # Attack one of the two controls: nearly preserved likelihood discrepancy.
    assert abs(exacts[0]-exacts[1]) <.05

    examples=[]
    for tau in (0.,3.,10.):
        for k,r in ((1,1),(2,0),(2,1),(2,2),(3,1),(4,2),(4,4),(6,2),(8,4),(8,8)):
            examples.append(coverage_case(M,k,r,tau))
    heterogeneity=[]
    for tau in (0.,3.,10.):
        for a in (0,1,2):
            met=contrast_metrics(2,a,tau)
            heterogeneity.append({**met,'exact_Poisson_KL_tau0':exacts[a] if tau==0 else ''})
    confusion=[]
    for k in (1,2,4,8):
        for a in (0,1,k):
            confusion.append(contrast_metrics(k,a,0.))
    game_cases=[]
    for tau in (0.,3.,10.):
        for cD,cA in ((0.01,.01),(.03,.02),(.06,.04)):
            game_cases.append(stackelberg_coverage(M,tau,cD,cA))
    for game in game_cases:
        p=np.asarray(game['leader_distribution_over_k']); assert abs(sum(p)-1)<1e-9
        assert game['mixing_benefit_over_best_pure']>=-1e-7
    result={'version':'1.2.0', 'purpose':'synthetic methodology, not evidence of nonhuman presence',
            'parameters':{'background':BASE,'signal':SIGNAL,'blocks':BLOCKS,
                          'alpha':ALPHA,'controls_m':M,
                          'iid_random_effects_tau':'between-channel SD in per-block rate',
                          'observation_variance':'B/blocks + tau^2'},
            'exact_profiled_poisson_k2':{'clean':exacts[0],
                                        'one_spoofed':exacts[1],
                                        'both_spoofed':exacts[2]},
            'heterogeneity':heterogeneity,
            'examples':examples,
            'clean_only_misspecification':confusion,
            'false_alarm_tau10_misread_tau0_k2':actual_false_alarm(2,10.,0.),
            'stackelberg_games':game_cases}
    if output_dir is not None:
        output_dir.mkdir(parents=True,exist_ok=True)
        (output_dir/'results_v1_2.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        write_csv(output_dir/'coverage_results.csv',examples,
                  ['m','k','r','tau','alpha','p_all_controls_spoofed',
                   'expected_spoofed_controls','expected_KL_nats',
                   'omnibus_power','omnibus_miss','clean_only_false_null_probability'])
        write_csv(output_dir/'heterogeneity_results.csv',heterogeneity,
                  ['k','a','tau','variance_v','profile_KL_gaussian',
                   'exact_Poisson_KL_tau0','omnibus_power','omnibus_miss',
                   'clean_only_false_null_probability'])
        savegames=[{**{k:v for k,v in d.items() if k not in ('leader_distribution_over_k','best_pure')},
                    'leader_distribution_over_k':json.dumps(d['leader_distribution_over_k']),
                    'best_pure_k':d['best_pure']['k'],'best_pure_r':d['best_pure']['r'],
                    'best_pure_loss':d['best_pure']['observer_loss']} for d in game_cases]
        write_csv(output_dir/'coverage_game_equilibria.csv',savegames,
                  ['m','tau','alpha','max_reach','incentive_margin','defender_cost_per_control','attacker_cost_per_reached_control',
                   'leader_distribution_over_k','leader_expected_k','hider_best_response_r',
                   'expected_omnibus_miss','expected_prob_full_spoof','leader_total_loss',
                   'best_pure_k','best_pure_r','best_pure_loss',
                   'mixing_benefit_over_best_pure','attacker_utility'])
    print('v1.2.0 verified: exact Poisson profile KL for k=2:',
          ', '.join(f'{x:.6f}' for x in exacts))
    print('false positive rate if true tau=10 but assumed tau=0, k=2:',
          f'{actual_false_alarm(2,10,0):.6f}')
    print('coverage P(all contaminated) for m=8, k=4, r=4:',
          f'{coverage_pmf(8,4,4).get(4,0):.6f}')
    for game in game_cases:
        weights=[f'k={k}:{p:.3f}' for k,p in enumerate(game['leader_distribution_over_k'],start=1) if p>1e-5]
        print('tau={} cD={} cA={} => {} r={} miss={:.4f} mix_gain={:.5f}'.format(
            game['tau'],game['defender_cost_per_control'],
            game['attacker_cost_per_reached_control'],
            ','.join(weights),game['hider_best_response_r'],
            game['expected_omnibus_miss'],game['mixing_benefit_over_best_pure']))
    print('All v1.2 assertions passed')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,default=Path('.'))
    args=parser.parse_args()
    run(args.output_dir)
