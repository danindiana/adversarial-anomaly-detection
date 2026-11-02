#!/usr/bin/env python3
"""Reproducible *synthetic* model calculations, v1.0.0.

No empirical evidence about extraterrestrial residence is used or inferred.
Requires numpy, scipy. Run: python verify_models.py
Optional: python verify_models.py --output-dir .
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from scipy.special import expit
from scipy.stats import nbinom, poisson, beta

BG_MEAN = 1000.0
BG_SD = 100.0
BG_K = (BG_MEAN / BG_SD) ** 2
BG_THETA = BG_SD ** 2 / BG_MEAN
BG_P = 1 / (1 + BG_THETA)
OBS = 1020


def pmf_gamma_poisson_at_y(y: int, s: float, k: float = BG_K, p: float = BG_P) -> float:
    """Pr(Y=y | background ~ Gamma(k, theta), extra Pois(s)).

    Gamma-poisson mixture gives NB for background; extra signal is independent
    Poisson. Stable finite convolution with only the required outcome.
    """
    j = np.arange(y + 1)
    return float(np.dot(nbinom.pmf(y - j, k, p), poisson.pmf(j, s)))


def bf_known_background(y: int, bg: float, signal: float) -> float:
    return float(np.exp(-signal) * (1 + signal / bg) ** y)


def bf_uncertain_background(y: int, signal: float, k: float = BG_K, p: float = BG_P) -> float:
    return pmf_gamma_poisson_at_y(y, signal, k, p) / nbinom.pmf(y, k, p)


def loguniform_average(func, low: float, high: float) -> float:
    """Average over log-uniform signal prior, integrate in log signal."""
    val, _ = quad(lambda u: func(np.exp(u)), np.log(low), np.log(high),
                  epsabs=1e-10, epsrel=1e-10, limit=150)
    return float(val / np.log(high / low))


def secrecy_values():
    # N(t)=100+9t; v(t)=0.01+0.0009t; 0 <= t <= 100 years.
    integrated_nv = 3700.0
    integrated_n = 55000.0
    naive_rate = 1e-3
    grimes = 4.09e-6
    return dict(
        integrated_agents_times_verification=integrated_nv,
        person_years=integrated_n,
        uncalibrated_example_no_detect=np.exp(-naive_rate * integrated_nv),
        naive_transfer_with_second_verification=np.exp(-grimes * integrated_nv),
        **{"direct_transfer_grimes_fatal_exposure": np.exp(-grimes * integrated_n)},
        loguniform_unknown_rate=np.real(loguniform_average(
            lambda rate: np.exp(-rate * integrated_nv), 1e-5, 1e-2)),
    )


def genomic_values():
    return {
        "example1_expected": 1000 * 0.5 * 0.2 * 0.9,
        "example1_zero_exact": (1 - 0.5 * 0.2 * 0.9) ** 1000,
        "example1_zero_poisson_approx": np.exp(-1000 * 0.5 * 0.2 * 0.9),
        "example2_expected": 1000 * 0.01 * 0.2 * 0.01,
        "example2_zero_exact": (1 - 0.01 * 0.2 * 0.01) ** 1000,
    }


def intervention_probability(a: float, b: float, r: float = 0.5, k: float = 20.0) -> float:
    return float(quad(lambda threshold: expit(k * (r - threshold)) * beta.pdf(threshold, a, b),
                      0, 1, epsabs=1e-11, epsrel=1e-11)[0])


def kl_signal_vs_null(s: float, uncertain_bg: bool = True, xmax: int = 2300) -> float:
    """KL(P(Y|signal=s) || P(Y|null)); all are prior predictive.

    Under uncertain B: background NB + independent Poisson(s).
    pmfs truncated at Y=xmax; tail probability is negligible at s<=100.
    """
    y = np.arange(xmax + 1)
    if uncertain_bg:
        base = nbinom.pmf(y, BG_K, BG_P)
        max_extra = min(xmax, max(80, int(np.ceil(s + 12 * np.sqrt(max(s, 1)) + 20))))
        addition = poisson.pmf(np.arange(max_extra + 1), s)
        alt = np.convolve(base, addition, mode="full")[:xmax + 1]
    else:
        base = poisson.pmf(y, BG_MEAN)
        alt = poisson.pmf(y, BG_MEAN + s)
    # avoid numerical underflow where both probabilities are negligible
    valid = (alt > 0) & (base > 0)
    return float(np.sum(alt[valid] * np.log(alt[valid] / base[valid])))


def optimize_hider(kappa: float, uncertain_bg=True, N=1000,
                   d0=.1, d_min=.001):
    """Hider minimizes predictive KL + kappa*log(d0/d).

    d chosen BEFORE Y. This is an illustrative best-response optimization,
    not a calibrated economic or ecological cost model and not a full game.
    """
    def objective(d):
        return kl_signal_vs_null(N*d, uncertain_bg) + kappa*np.log(d0/d)
    sol = minimize_scalar(objective, bounds=(d_min, d0), method="bounded",
                          options={"xatol": 1e-9})
    candidates = [(d_min, objective(d_min)), (d0, objective(d0)), (float(sol.x), float(sol.fun))]
    dstar, value = min(candidates, key=lambda pair: pair[1])
    kldiv = kl_signal_vs_null(N*dstar, uncertain_bg)
    return {
        "kappa": kappa, "dstar": dstar, "signal": N*dstar,
        "KL_nats": kldiv,
        "cost": kappa*np.log(d0/dstar), "objective": value,
        "pinsker_TV_upper_bound": min(1.0, np.sqrt(kldiv/2)),
        "BF_for_Y1020": bf_uncertain_background(OBS, N*dstar)
                         if uncertain_bg else bf_known_background(OBS, BG_MEAN, N*dstar),
    }


def main(output_dir=None):
    signals = [0.1, 1, 1, 10, 10, 100]
    branches = [bf_uncertain_background(OBS, s) for s in signals]
    exp1 = {
        "BF_fixed_B_signal20": bf_known_background(OBS, 1000, 20),
        "BF_gammaB_signal20": bf_uncertain_background(OBS, 20),
        "signals_six_branches": signals,
        "BF_six_branches": branches,
        "BF_six_branch_mean": float(np.mean(branches)),
    }
    high = {
        "BF_fixed_B_signal2_Y2": bf_known_background(2, .05, 2),
        "BF_gammaB_signal2_Y2": bf_uncertain_background(2, 2, k=1, p=1/1.05),
        "BF_fixed_B_signal_loguniform_0p01_100": loguniform_average(
            lambda s: bf_known_background(2, .05, s), .01, 100),
        "BF_gammaB_signal_loguniform_0p01_100": loguniform_average(
            lambda s: bf_uncertain_background(2, s, k=1, p=1/1.05), .01, 100),
    }
    secrecy = secrecy_values()
    genomic = genomic_values()
    pw = intervention_probability(8, 2)
    pc = intervention_probability(3, 5)
    intervention = {"P_W": pw, "P_C": pc, "BF_C_over_W_event": pc/pw,
                    "BF_W_over_C_no_event": (1-pw)/(1-pc)}
    game = {
        "model": "min_d KL(P1_d||P0)+kappa log(d0/d)",
        "uncertain_background": [optimize_hider(c) for c in (0.02, 0.1, 0.5)],
        "known_background": [optimize_hider(c, uncertain_bg=False) for c in (0.02, 0.1, 0.5)],
        "unhardened_d0": {"d": 0.1, "signal": 100,
                          "KL_nats": kl_signal_vs_null(100),
                          "BF_for_Y1020": bf_uncertain_background(OBS, 100)},
        "maximum_hardening_dmin": {"d": 0.001, "signal": 1,
                                    "KL_nats": kl_signal_vs_null(1),
                                    "BF_for_Y1020": bf_uncertain_background(OBS, 1)},
    }
    results = {"version": "1.0.0", "synthetic": True, "experiment_1": exp1,
               "high_specificity": high, "secrecy": secrecy,
               "genomics": genomic, "interventions": intervention,
               "adversarial_experiment_5": game}

    # Assert key previously discussed numbers and consistency conditions.
    assert abs(exp1["BF_fixed_B_signal20"]-1.220) < .005
    assert abs(exp1["BF_gammaB_signal20"]-1.037) < .005
    assert abs(exp1["BF_six_branch_mean"]-0.979) < .005
    assert abs(secrecy["uncalibrated_example_no_detect"]-0.0247) < .0001
    assert abs(secrecy["loguniform_unknown_rate"]-0.399) < .003
    assert abs(intervention["P_W"]-.035) < .003
    assert abs(intervention["P_C"]-.750) < .003
    for background_name, uncertain in (("uncertain_background", True),
                                      ("known_background", False)):
        for z in game[background_name]:
            assert 0.001 <= z["dstar"] <= 0.1
            assert z["KL_nats"] >= -1e-10
            assert z["objective"] <= kl_signal_vs_null(1000*0.001, uncertain) + z["kappa"]*np.log(100) + 1e-7
            assert z["objective"] <= kl_signal_vs_null(1000*0.1, uncertain) + 1e-7
            assert abs(z["objective"] - z["KL_nats"] - z["cost"]) < 1e-8

    if output_dir is not None:
        path = Path(output_dir)
        path.mkdir(exist_ok=True, parents=True)
        (path / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        rows = ["kappa,background,d_star,expected_signal,KL_nats,cost,objective,BF_y1020"]
        for bg in ("uncertain_background", "known_background"):
            for z in game[bg]:
                rows.append(f'{z["kappa"]},{bg},{z["dstar"]:.9f},{z["signal"]:.6f},{z["KL_nats"]:.9f},{z["cost"]:.9f},{z["objective"]:.9f},{z["BF_for_Y1020"]:.9f}')
        (path / 'adversarial_results.csv').write_text('\n'.join(rows) + '\n')
    print('Experiment 1 Bayes factors:', round(exp1["BF_fixed_B_signal20"],3),
          round(exp1["BF_gammaB_signal20"],3), round(exp1["BF_six_branch_mean"],3))
    print('High-specificity sharp and log-uniform BFs:',
          {key: round(val,3) for key, val in high.items()})
    print('Secrecy, example / Grimes transfer:',
          secrecy["uncalibrated_example_no_detect"],
          secrecy["direct_transfer_grimes_fatal_exposure"])
    print('Genomics, exact and Poisson-approx P0:', genomic["example1_zero_exact"], genomic["example1_zero_poisson_approx"])
    print('Intervention P(warden/cohabitant):', pw, pc)
    print('Adversarial best response with uncertain background:')
    for z in game["uncertain_background"]:
        print('  kappa={:.2f}  d*={:.5f}  expected signal={:.2f}  KL={:.5f} nats  cost={:.5f}  BF(Y=1020)={:.5f}'.format(
            z["kappa"], z["dstar"], z["signal"], z["KL_nats"], z["cost"], z["BF_for_Y1020"]))
    print('Adversarial best response with known background:')
    for z in game["known_background"]:
        print('  kappa={:.2f}  d*={:.5f}  expected signal={:.2f}  KL={:.5f} nats'.format(
            z["kappa"], z["dstar"], z["signal"], z["KL_nats"]))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=str, default=None)
    args = parser.parse_args()
    main(args.output_dir)
