#!/usr/bin/env python3
"""Version 1.1.0: deterministic synthetic extensions of verify_models.py.

No empirical data about nonhuman residence is used. All results are conditional
on a deliberately simplified model, *not* measurements of the physical world.
Run: python verify_models_v1_1.py --output-dir .
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import math
import numpy as np
from verify_models import main as baseline_main, optimize_hider

S_MIN, S_MAX = 1.0, 100.0
VARIANCES = {"known_background": 1000.0,
             "uncertain_background": 11000.0}
KAPPAS = (0.02, 0.10, 0.50)


def quadratic_kl(signal: float, variance: float) -> float:
    """Local Gaussian small-signal approximation, not exact count KL."""
    return signal * signal / (2 * variance)


def log_cost_optimum(kappa: float, variance: float,
                     s_min: float = S_MIN, s_max: float = S_MAX) -> dict:
    """Closed-form minimizer of s²/(2V)+kappa*log(s_max/s)."""
    unconstrained = math.sqrt(kappa * variance)
    signal = min(s_max, max(s_min, unconstrained))
    divergence = quadratic_kl(signal, variance)
    cost = kappa * math.log(s_max / signal)
    return {"kappa": kappa, "variance": variance,
            "unconstrained_signal": unconstrained, "signal_opt": signal,
            "at_boundary": signal != unconstrained,
            "KL_opt_quadratic": divergence, "cost": cost,
            "total_objective": divergence + cost}


def power_cost_optimum(alpha: float, c: float, variance: float,
                       s_min: float = S_MIN, s_max: float = S_MAX) -> dict:
    """Closed-form minimizer of s²/(2V)+c*s^(-alpha)."""
    assert alpha > 0 and c > 0 and variance > 0
    unconstrained = (alpha*c*variance)**(1/(alpha+2))
    signal = min(s_max, max(s_min, unconstrained))
    kl = quadratic_kl(signal, variance)
    cost = c*signal**(-alpha)
    return {"alpha": alpha, "coefficient_c": c,
            "variance": variance, "unconstrained_signal": unconstrained,
            "signal_opt": signal, "at_boundary": signal != unconstrained,
            "KL_opt_quadratic": kl, "cost": cost,
            "total_objective": kl+cost}


def profiled_on_off_poisson_kl(background: float, signal: float,
                              control_contamination: float = 0,
                              blocks: int = 100) -> float:
    """Infimum KL to null with common unknown ON/OFF Poisson mean.

    This KL I-projection is not a Bayes factor and does not incorporate a
    prior on background B. Each block has equal exposures and shared B.
    """
    mu_on = background + signal
    mu_off = background + control_contamination
    assert min(mu_on, mu_off) > 0
    mu_null = 0.5*(mu_on+mu_off)
    return blocks*(mu_on*math.log(mu_on/mu_null)
                   + mu_off*math.log(mu_off/mu_null))


def attacker_best_response(prob_A: float, clean_information: float,
                           attack_cost: float) -> dict:
    """Follower minimizes expected KL + fixed cost, pessimistic tie break.

    Assumes attack is permanent, cannot adapt to realized randomized control
    assignment, and can fully contaminate at most one candidate control.
    """
    actions = [
        {"action":"none", "expected_information":clean_information, "cost":0.0},
        {"action":"attack_A", "expected_information":(1-prob_A)*clean_information,
         "cost":attack_cost},
        {"action":"attack_B", "expected_information":prob_A*clean_information,
         "cost":attack_cost},
    ]
    for a in actions:
        a["hider_loss"] = a["expected_information"]+a["cost"]
    # Smaller info breaks a near-equal hider-loss tie against the defender.
    return min(actions, key=lambda a: (round(a["hider_loss"], 10),
                                       a["expected_information"], a["action"]))


def stackelberg_game(background=1000., signal=20., blocks=100,
                     attack_cost_fraction=0., grid_count=1001):
    """Leader commits to Pr(A); follower chooses which control to spoof."""
    clean_info = profiled_on_off_poisson_kl(background, signal, 0., blocks)
    contam_info = profiled_on_off_poisson_kl(background, signal, signal, blocks)
    assert abs(contam_info) < 1e-9
    attack_cost = attack_cost_fraction*clean_info
    grid = []
    for prob_A in np.linspace(0, 1, grid_count):
        follower = attacker_best_response(float(prob_A), clean_info, attack_cost)
        grid.append({"prob_A":float(prob_A), **follower})
    # Leader maximizes information; ties prefer p nearest one half.
    leader = max(grid, key=lambda row:(round(row["expected_information"],10),
                                       -abs(row["prob_A"]-.5)))
    return {
        "background_per_channel":background, "signal_per_block":signal,
        "blocks":blocks, "clean_information_nats":clean_info,
        "contaminated_information_nats":contam_info,
        "attack_cost_fraction":attack_cost_fraction,
        "attack_cost_nats_equivalent":attack_cost,
        "leader_prob_A":leader["prob_A"],
        "follower_action":leader["action"],
        "leader_expected_profile_KL_nats":leader["expected_information"],
        "follower_loss":leader["hider_loss"],
        "grid":grid,
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open('w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def run(output_dir: Path | None) -> dict:
    baseline = baseline_main(str(output_dir) if output_dir else None)
    rows = []
    for label, variance in VARIANCES.items():
        for kappa in KAPPAS:
            opt = log_cost_optimum(kappa, variance)
            # Independent comparison with the exact v1.0 predictive-KL optimization.
            exact = optimize_hider(kappa, uncertain_bg=(label=='uncertain_background'))
            rows.append({"cost_model":"log", "background":label,
                         "parameter":kappa, "signal_opt":opt["signal_opt"],
                         "KL_opt_quadratic":opt["KL_opt_quadratic"],
                         "exact_poisson_signal":exact["signal"],
                         "exact_poisson_KL":exact["KL_nats"]})
        for alpha,c in [(1.,1.), (2., 100.)]:
            opt = power_cost_optimum(alpha,c,variance)
            rows.append({"cost_model":f"power_alpha_{alpha:g}",
                         "background":label,"parameter":c,
                         "signal_opt":opt["signal_opt"],
                         "KL_opt_quadratic":opt["KL_opt_quadratic"],
                         "exact_poisson_signal":"", "exact_poisson_KL":""})

    cases = [("zero_cost",0.),("quarter_information",.25),
             ("three_quarter_information",.75)]
    games = {label:stackelberg_game(attack_cost_fraction=frac)
             for label, frac in cases}

    # Numerical tests for exact closed form and the qualitative conclusion.
    for kappa in KAPPAS:
        known = log_cost_optimum(kappa, VARIANCES['known_background'])
        uncertain = log_cost_optimum(kappa, VARIANCES['uncertain_background'])
        assert not known['at_boundary'] and not uncertain['at_boundary']
        assert math.isclose(known['signal_opt']**2, kappa*1000, rel_tol=1e-12)
        assert math.isclose(uncertain['signal_opt']/known['signal_opt'],
                            math.sqrt(11), rel_tol=1e-12)
        assert math.isclose(known['KL_opt_quadratic'],kappa/2, rel_tol=1e-12)
        assert math.isclose(uncertain['KL_opt_quadratic'],kappa/2, rel_tol=1e-12)
    p_known = power_cost_optimum(1,1,1000)
    p_uncertain = power_cost_optimum(1,1,11000)
    assert math.isclose(p_known['signal_opt'],10.,rel_tol=1e-12)
    assert math.isclose(p_known['KL_opt_quadratic'],.05,rel_tol=1e-12)
    assert math.isclose(p_known['KL_opt_quadratic']/p_uncertain['KL_opt_quadratic'],
                        11**(1/3),rel_tol=1e-12)
    for label, game in games.items():
        assert game['leader_prob_A']==.5
        assert game['clean_information_nats']>0
        assert abs(game['contaminated_information_nats'])<1e-9
        if label in ("zero_cost","quarter_information"):
            assert math.isclose(game['leader_expected_profile_KL_nats'],
                                game['clean_information_nats']/2,rel_tol=1e-10)
            assert game['follower_action']!='none'
        else:
            assert math.isclose(game['leader_expected_profile_KL_nats'],
                                game['clean_information_nats'],rel_tol=1e-10)
            assert game['follower_action']=='none'
    zero = games['zero_cost']
    d0 = zero['clean_information_nats']
    assert math.isclose(profiled_on_off_poisson_kl(1000,20,0,100),d0)
    assert attacker_best_response(1.,d0,0.)['expected_information']==0
    assert attacker_best_response(0.,d0,0.)['expected_information']==0

    summary_games=[]
    grid_rows=[]
    for label, game in games.items():
        summary_games.append({"case":label, **{k:v for k,v in game.items() if k!='grid'}})
        for r in game['grid']:
            grid_rows.append({"case":label,**r})
    out={"version":"1.1.0", "synthetic":True,
         "v1_0_previous_verified": baseline['version'],
         "quadratic_KL_log_cost": [log_cost_optimum(k,v)
                                   for v in VARIANCES.values() for k in KAPPAS],
         "quadratic_KL_power_cost": [power_cost_optimum(a,c,v)
                                     for v in VARIANCES.values()
                                     for a,c in [(1.,1.),(2.,100.)]],
         "cost_form_sensitivity":rows,
         "on_off_identifiability":{
             "on_only_parameter": "B+s; B and s not separately identifiable",
             "on_off_null_constraint": "mu_on=mu_off with equal exposures",
             "clean_profiled_KL_nats":d0,
             "perfectly_contaminated_profiled_KL_nats":0.,
         },
         "toy_stackelberg":summary_games}
    if output_dir:
        output_dir.mkdir(exist_ok=True, parents=True)
        (output_dir/'results_v1_1.json').write_text(json.dumps(out,indent=2)+'\n')
        write_csv(output_dir/'cost_sensitivity.csv',rows,
                  ['cost_model','background','parameter','signal_opt',
                   'KL_opt_quadratic','exact_poisson_signal','exact_poisson_KL'])
        write_csv(output_dir/'stackelberg_results.csv',summary_games,
                  ['case','attack_cost_fraction','attack_cost_nats_equivalent',
                   'leader_prob_A','follower_action',
                   'clean_information_nats','leader_expected_profile_KL_nats',
                   'follower_loss'])
        write_csv(output_dir/'stackelberg_strategy_grid.csv',grid_rows,
                  ['case','prob_A','action','expected_information',
                   'cost','hider_loss'])
    print('\nVersion 1.1.0 | closed form & Stackelberg toy:')
    print('  Footprint ratio from uncertain/known V: {:.6f}'.format(math.sqrt(11)))
    print('  Log-cost interior KL*=kappa/2 for all three illustrative kappa values.')
    print('  Power alpha=1, c=1: KL known={:.6f}, KL uncertain={:.6f}'.format(
        p_known['KL_opt_quadratic'],p_uncertain['KL_opt_quadratic']))
    for label, game in games.items():
        print('  {:>28}: p*= {:.3f}, response= {:>8}, clean KL={:.6f}, expected KL={:.6f}'.format(
            label,game['leader_prob_A'],game['follower_action'],
            game['clean_information_nats'],game['leader_expected_profile_KL_nats']))
    print('  All v1.1.0 assertions passed.')
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=None)
    args=parser.parse_args()
    run(args.output_dir)
