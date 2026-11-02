#!/usr/bin/env python3
"""Ad-fraud case study: the adversarial-detection framework applied to ad measurement.

Four results, each written to adfraud/figures/ (light and dark PNG) and to
results.json / results.csv:

  1. Noise floor     How many users an experiment needs before an ad effect is
                     distinguishable from zero (analytic; calibrated to and
                     checked against Lewis & Rao 2015).
  2. Attribution gap Platform-attributed conversions vs holdout-measured
                     incremental conversions for three illustrative campaigns
                     (simulated; H0 worthless, H1 effective, H2 attribution theft).
  3. Theft detection How large a share of organic conversions one of six ad
                     vendors can claim before a cross-vendor consistency test
                     catches it (analytic omnibus test, Monte Carlo checked).
  4. Holdout control How much fake lift a vendor manufactures when it chooses
                     its own holdout group, vs an advertiser-randomized holdout
                     (simulated).

All data are synthetic. The parameters are illustrative and stated in the code;
only result 1 is calibrated to a published study. Nothing here measures any real
vendor, platform or campaign.

Run:  python adfraud_case_study.py [--output-dir DIR] [--no-figures]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import chi2, ncx2, norm

SEED = 20261102
ALPHA = 0.01

# Shared illustrative setting
P0 = 0.02            # organic (no-ad) conversion probability in the attribution window
M_VENDORS = 6        # ad vendors / networks, each with its own randomized holdout

# --------------------------------------------------------------------------- #
# 1. Noise floor (Lewis & Rao 2015)
# --------------------------------------------------------------------------- #
LR_EFFECT_SD_RATIO = 0.0047   # $0.35 per-person lift over a $75 per-person SD (their example)
LR_T_2M_PAPER = 3.30          # expected t at 2 million users, as reported
LR_T_200K_PAPER = 1.04        # expected t at 200,000 users, as reported
T_TARGET = 3.0                # Lewis & Rao's power benchmark: expected t-statistic of 3


def expected_t(d: float, n_total: float) -> float:
    """Expected t for a two-arm experiment split evenly: d * sqrt(N) / 2."""
    return d * math.sqrt(n_total) / 2


def users_needed(d: np.ndarray | float, t: float = T_TARGET):
    """Total users (both arms) for an expected t-statistic of t."""
    return (2 * t / np.asarray(d)) ** 2


def noise_floor() -> dict:
    t2m = expected_t(LR_EFFECT_SD_RATIO, 2_000_000)
    t200k = expected_t(LR_EFFECT_SD_RATIO, 200_000)
    assert abs(t2m - LR_T_2M_PAPER) < 0.03, t2m
    assert abs(t200k - LR_T_200K_PAPER) < 0.03, t200k
    d = np.logspace(-3, -1, 200)
    return {
        "d": d, "n": users_needed(d),
        "lr_d": LR_EFFECT_SD_RATIO,
        "lr_users_for_t3": float(users_needed(LR_EFFECT_SD_RATIO)),
        "lr_expected_t_2M": t2m, "lr_expected_t_200k": t200k,
        "lr_power_200k_one_sided_5pct": float(norm.sf(norm.isf(0.025) - t200k)),
    }


# --------------------------------------------------------------------------- #
# 2. Attribution vs incrementality
# --------------------------------------------------------------------------- #
N_ARM_ATTR = 1_000_000
SELECTION_CLAIM = 0.002   # organic conversions last-touch credits to the ad via targeting
CAMPAIGNS = [
    # label, true incremental rate, injected (stolen) attribution rate
    ("Worthless (H0)", 0.0, 0.0),
    ("Effective (H1)", 0.001, 0.0),
    ("Attribution theft (H2)", 0.001, 0.006),
]


def attribution_gap(rng: np.random.Generator) -> list[dict]:
    rows = []
    for label, delta, injected in CAMPAIGNS:
        conv_t = rng.binomial(N_ARM_ATTR, P0 + delta)
        conv_c = rng.binomial(N_ARM_ATTR, P0)
        # Attributed = caused + organic credited by targeting + injected clicks.
        attr_rate = delta + SELECTION_CLAIM + injected
        attributed = rng.binomial(N_ARM_ATTR, attr_rate)
        inc = (conv_t - conv_c) / N_ARM_ATTR
        se = math.sqrt((conv_t / N_ARM_ATTR) * (1 - conv_t / N_ARM_ATTR) / N_ARM_ATTR
                       + (conv_c / N_ARM_ATTR) * (1 - conv_c / N_ARM_ATTR) / N_ARM_ATTR)
        rows.append({
            "campaign": label, "true_incremental_per_1000": 1000 * delta,
            "attributed_per_1000": 1000 * attributed / N_ARM_ATTR,
            "measured_incremental_per_1000": 1000 * inc,
            "incremental_ci95_per_1000": 1000 * 1.96 * se,
            "attributed_over_incremental": (attributed / N_ARM_ATTR) / inc if inc > 0 else float("inf"),
        })
    return rows


# --------------------------------------------------------------------------- #
# 3. Theft detection across vendors (omnibus consistency test)
# --------------------------------------------------------------------------- #
HOLDOUT_SIZES = (50_000, 200_000, 1_000_000)   # users per arm, per vendor
TAU_VALUES = (0.0, 0.0005, 0.001)               # honest between-vendor SD of excess attribution (rate)
STEAL_GRID = np.linspace(0, 0.30, 301)          # share of organic conversions the thief claims


def excess_variance(n_arm: int, tau: float = 0.0) -> float:
    """Variance of one vendor's excess-attribution rate (attributed minus incremental).

    E_v = attributed/n - (conv_T - conv_C)/n; its sampling noise is dominated by the
    two binomial conversion counts, about 2 p0 (1 - p0) / n, plus honest
    between-vendor heterogeneity tau^2 in how much organic credit targeting claims.
    """
    return 2 * P0 * (1 - P0) / n_arm + tau ** 2


def omnibus_power(steal_share: np.ndarray, n_arm: int, tau: float = 0.0,
                  m: int = M_VENDORS, alpha: float = ALPHA) -> np.ndarray:
    """Power of the chi-square test of equal excess attribution across m vendors,
    one of which inflates its excess by steal_share * p0 (variance known)."""
    s = np.asarray(steal_share) * P0
    lam = s ** 2 * (m - 1) / m / excess_variance(n_arm, tau)
    return ncx2.sf(chi2.isf(alpha, m - 1), m - 1, lam)


def share_at_power(target: float, n_arm: int, tau: float = 0.0) -> float:
    lo, hi = 0.0, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if omnibus_power(mid, n_arm, tau) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def false_alarm_if_tau_ignored(n_arm: int, tau_true: float, m: int = M_VENDORS) -> float:
    """Actual size of the nominal-1% test when honest heterogeneity is assumed to be zero."""
    v_assumed = excess_variance(n_arm, 0.0)
    v_true = excess_variance(n_arm, tau_true)
    return float(chi2.sf(chi2.isf(ALPHA, m - 1) * v_assumed / v_true, m - 1))


def monte_carlo_power(steal_share: float, n_arm: int, rng: np.random.Generator,
                      reps: int = 40_000) -> float:
    """Direct binomial simulation of the six-vendor experiment (tau = 0)."""
    m = M_VENDORS
    conv_c = rng.binomial(n_arm, P0, size=(reps, m))
    conv_t = rng.binomial(n_arm, P0, size=(reps, m))          # worthless campaign: no lift
    claim = np.full(m, SELECTION_CLAIM)
    claim[0] += steal_share * P0                              # vendor 0 steals
    # Attributed conversions are a subset of treatment conversions.
    attributed = rng.binomial(conv_t, np.clip(claim / P0, 0, 1))
    excess = (attributed - (conv_t - conv_c)) / n_arm
    v = excess_variance(n_arm)
    q = ((excess - excess.mean(axis=1, keepdims=True)) ** 2).sum(axis=1) / v
    return float(np.mean(q > chi2.isf(ALPHA, m - 1)))


def theft_detection(rng: np.random.Generator) -> dict:
    curves = {n: omnibus_power(STEAL_GRID, n) for n in HOLDOUT_SIZES}
    s50 = {n: share_at_power(0.5, n) for n in HOLDOUT_SIZES}
    s50_tau = {tau: share_at_power(0.5, 200_000, tau) for tau in TAU_VALUES}
    fa = {tau: false_alarm_if_tau_ignored(200_000, tau) for tau in TAU_VALUES}
    # Check the analytic power against a direct simulation at one point.
    check_share = s50[200_000]
    mc = monte_carlo_power(check_share, 200_000, rng)
    assert abs(mc - 0.5) < 0.03, mc
    null_mc = monte_carlo_power(0.0, 200_000, rng)
    assert abs(null_mc - ALPHA) < 0.004, null_mc
    return {"curves": curves, "share_at_50pct_power": s50,
            "share_at_50pct_power_by_tau_200k": s50_tau,
            "false_alarm_if_tau_ignored_200k": fa,
            "monte_carlo_check": {"steal_share": check_share, "analytic_power": 0.5,
                                  "simulated_power": mc, "simulated_null_size": null_mc}}


# --------------------------------------------------------------------------- #
# 4. Who controls the holdout
# --------------------------------------------------------------------------- #
N_POP = 2_000_000
PROPENSITY_SHAPE = 0.5      # gamma shape: heavy heterogeneity in purchase propensity
PREDICTION_CORR = 0.5       # how well the vendor's model ranks users (on log propensity)
Q_GRID = np.linspace(0, 0.5, 26)
N_ARM_HOLDOUT = 200_000


def holdout_control(rng: np.random.Generator) -> dict:
    p = np.minimum(rng.gamma(PROPENSITY_SHAPE, P0 / PROPENSITY_SHAPE, N_POP), 1.0)
    logp = np.log(p)
    z = (logp - logp.mean()) / logp.std()
    score = PREDICTION_CORR * z + math.sqrt(1 - PREDICTION_CORR ** 2) * rng.standard_normal(N_POP)
    low = score < np.median(score)
    p_mean, p_low = p.mean(), p[low].mean()
    # The vendor fills a share q of holdout slots with users it predicts are unlikely
    # to buy; the rest of the holdout, and the whole treatment group, are random.
    holdout_mean = (1 - Q_GRID) * p_mean + Q_GRID * p_low
    fake_lift = p_mean - holdout_mean                    # true lift is zero
    se = math.sqrt(2 * p_mean * (1 - p_mean) / N_ARM_HOLDOUT)
    return {"q": Q_GRID, "fake_lift_rate": fake_lift, "fake_lift_relative": fake_lift / p_mean,
            "advertiser_ci95_rate": 1.96 * se, "p_mean": p_mean, "p_low_half": p_low}


# --------------------------------------------------------------------------- #
# 6. Selection bias: observational vs randomized lift (design: ChatGPT)
# --------------------------------------------------------------------------- #
N_SEL = 400_000
SEL_BASE_LOGIT = math.log(0.08 / 0.92)   # 8% purchase probability at average intent
SEL_INTENT_EFFECT = 1.0                  # how strongly latent intent drives purchase
TRUE_LIFT_PP = 0.01                      # true causal lift: +1 percentage point
GAMMA_GRID = np.linspace(0, 2.5, 11)     # how strongly intent drives exposure (targeting)


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def selection_bias(rng: np.random.Generator) -> dict:
    intent = rng.standard_normal(N_SEL)
    p_base = _sigmoid(SEL_BASE_LOGIT + SEL_INTENT_EFFECT * intent)
    u_buy = rng.random(N_SEL)
    obs, rct = [], []
    for g in GAMMA_GRID:
        exposed = rng.random(N_SEL) < _sigmoid(g * intent)            # targeted exposure
        y = u_buy < np.where(exposed, p_base + TRUE_LIFT_PP, p_base)
        obs.append(y[exposed].mean() - y[~exposed].mean())
        assigned = rng.random(N_SEL) < 0.5                             # randomized holdout
        y_r = u_buy < np.where(assigned, p_base + TRUE_LIFT_PP, p_base)
        rct.append(y_r[assigned].mean() - y_r[~assigned].mean())
    obs, rct = np.array(obs), np.array(rct)
    assert abs(obs[0] - TRUE_LIFT_PP) < 0.004 and np.all(np.abs(rct - TRUE_LIFT_PP) < 0.004), (obs[0], rct)
    se = math.sqrt(2 * 0.1 * 0.9 / (N_SEL / 2))
    return {"gamma": GAMMA_GRID, "observational": obs, "randomized": rct, "rct_ci95": 1.96 * se}


# --------------------------------------------------------------------------- #
# 7. Covariance geometry of equal-size footprints (design: ChatGPT)
# --------------------------------------------------------------------------- #
CHANNELS = ["spend", "impressions", "clicks", "attributed", "visits", "revenue", "margin"]
CHANNEL_SD = np.array([1.0, 3.0, 3.0, 2.5, 2.0, 1.0, 0.8])
# Illustrative correlations: engagement metrics move together strongly; revenue and
# margin move together; the two blocks are only loosely linked through visits.
_R = np.eye(7)
for (i, j), r in {
    (0, 1): 0.6, (0, 2): 0.5, (0, 3): 0.4, (0, 4): 0.4, (0, 5): 0.2, (0, 6): 0.1,
    (1, 2): 0.9, (1, 3): 0.7, (1, 4): 0.8, (1, 5): 0.3, (1, 6): 0.2,
    (2, 3): 0.75, (2, 4): 0.85, (2, 5): 0.3, (2, 6): 0.2,
    (3, 4): 0.7, (3, 5): 0.35, (3, 6): 0.25,
    (4, 5): 0.5, (4, 6): 0.35,
    (5, 6): 0.9,
}.items():
    _R[i, j] = _R[j, i] = r
SIGMA_ADS = _R * np.outer(CHANNEL_SD, CHANNEL_SD)
FOOTPRINTS = {
    # label: raw footprint before normalizing to unit length
    "Attribution-heavy": {"clicks": 1, "attributed": 1},
    "Traffic-heavy": {"impressions": 1, "clicks": 1, "visits": 1},
    "Bot traffic:\nclicks, no visits": {"impressions": 1, "clicks": 1, "visits": -0.6},
    "Revenue-heavy": {"visits": 1, "revenue": 1},
    "Margin-heavy": {"revenue": 1, "margin": 1},
}


def covariance_geometry() -> list[dict]:
    assert np.all(np.linalg.eigvalsh(SIGMA_ADS) > 0), "Sigma must be positive definite"
    inv = np.linalg.inv(SIGMA_ADS)
    rows = []
    for label, spec in FOOTPRINTS.items():
        u = np.zeros(len(CHANNELS))
        for ch, w in spec.items():
            u[CHANNELS.index(ch)] = w
        u /= np.linalg.norm(u)
        joint = 1 / math.sqrt(float(u @ inv @ u))
        per_metric = 1 / math.sqrt(float(np.sum((u / CHANNEL_SD) ** 2)))   # ignores correlation
        rows.append({"footprint": label, "per_metric_capacity": per_metric, "joint_capacity": joint})
    return rows


# --------------------------------------------------------------------------- #
# 5. Published comparison (not simulated)
# --------------------------------------------------------------------------- #
# Gordon, Moakler & Zettelmeyer (2023), "Close Enough?", Marketing Science 42(4):
# 663 Facebook experiments. Median RCT lift and the median absolute percentage-point
# difference between non-experimental estimates and the RCT, by funnel level.
GORDON_2023 = [("Upper funnel", 28, 115), ("Mid funnel", 19, 107), ("Lower funnel", 6, 62)]


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #
THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", grid="#e4e3df",
                  blue="#2a78d6", orange="#eb6834", aqua="#1baf7a",
                  seq=("#86b6ef", "#2a78d6", "#104281"), band="#2a78d6"),
    "dark": dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", grid="#33332f",
                 blue="#3987e5", orange="#d95926", aqua="#199e70",
                 seq=("#184f95", "#3987e5", "#9ec5f4"), band="#3987e5"),
}


def _setup(plt, theme: dict, title: str, subtitle: str):
    fig, ax = plt.subplots(figsize=(9.6, 5.4), dpi=170)
    fig.patch.set_facecolor(theme["surface"])
    ax.set_facecolor(theme["surface"])
    fig.subplots_adjust(left=0.1, right=0.83, top=0.8, bottom=0.17)
    fig.text(0.1, 0.93, title, fontsize=15, fontweight="bold", color=theme["ink"], ha="left")
    fig.text(0.1, 0.875, subtitle, fontsize=10.5, color=theme["ink2"], ha="left")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(theme["grid"])
    ax.tick_params(colors=theme["ink2"], labelsize=9.5, length=0)
    ax.grid(True, color=theme["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def _note(fig, theme, text):
    fig.text(0.1, 0.035, text, fontsize=8.5, color=theme["ink2"], ha="left")


def make_figures(out: Path, nf: dict, gap: list[dict], theft: dict, hold: dict,
                 sel: dict, geo: list[dict]) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, PercentFormatter

    plt.rcParams["font.family"] = ["Inter", "DejaVu Sans", "sans-serif"]
    plt.rcParams["svg.hashsalt"] = "aad"
    out.mkdir(parents=True, exist_ok=True)
    written = []

    def users_fmt(x, _):
        if x >= 1e9:
            return f"{x/1e9:g}B"
        if x >= 1e6:
            return f"{x/1e6:g}M"
        if x >= 1e3:
            return f"{x/1e3:g}k"
        return f"{x:g}"

    for mode, th in THEMES.items():
        # 1. Noise floor --------------------------------------------------- #
        fig, ax = _setup(plt, th, "Ad effects hide in the noise",
                         "Users needed for an expected t-statistic of 3, by effect size (lift ÷ SD of per-user sales)")
        ax.loglog(nf["d"], nf["n"], color=th["blue"], linewidth=2.2)
        ax.axhline(500_000, color=th["ink2"], linewidth=1, linestyle=(0, (4, 3)))
        ax.text(1.02e-3, 560_000, "Smallest Lewis & Rao trial: 500k users", color=th["ink2"], fontsize=9)
        x, y = nf["lr_d"], nf["lr_users_for_t3"]
        ax.plot([x], [y], "o", markersize=9, color=th["orange"],
                markeredgecolor=th["surface"], markeredgewidth=2)
        ax.annotate(f"Lewis & Rao example\n\\$0.35 lift on a \\$75 SD ({x:.4f})\n→ {y/1e6:.1f}M users",
                    xy=(x, y), xytext=(x * 2.3, y * 6), color=th["ink"], fontsize=9.5,
                    arrowprops=dict(arrowstyle="-", color=th["ink2"], linewidth=1))
        ax.set_xlabel("Effect size: per-user sales lift ÷ per-user sales SD", color=th["ink2"], fontsize=10)
        ax.set_ylabel("Total users needed", color=th["ink2"], fontsize=10)
        ax.yaxis.set_major_formatter(FuncFormatter(users_fmt))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        _note(fig, th, "Analytic: N = (2t/d)². Reproduces Lewis & Rao (2015): expected t = 3.30 at 2M users and 1.04 at 200k.")
        fig.savefig(out / f"noise_floor-{mode}.png", facecolor=th["surface"])
        plt.close(fig)
        written.append(f"noise_floor-{mode}.png")

        # 2. Attribution vs incrementality --------------------------------- #
        fig, ax = _setup(plt, th, "What the platform reports vs what the ads caused",
                         "Conversions per 1,000 exposed users: last-touch attributed vs measured against a randomized holdout")
        labels = [r["campaign"] for r in gap]
        xs = np.arange(len(labels))
        w = 0.34
        att = [r["attributed_per_1000"] for r in gap]
        inc = [r["measured_incremental_per_1000"] for r in gap]
        ci = [r["incremental_ci95_per_1000"] for r in gap]
        b1 = ax.bar(xs - w / 2 - 0.01, att, w, color=th["blue"], label="Attributed by platform")
        b2 = ax.bar(xs + w / 2 + 0.01, inc, w, color=th["orange"], label="Incremental (holdout)")
        ax.errorbar(xs + w / 2 + 0.01, inc, yerr=ci, fmt="none", ecolor=th["ink"], elinewidth=1.4, capsize=5)
        for bar, v in zip(b1, att):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.18, f"{v:.1f}", ha="center", color=th["ink"], fontsize=10)
        for bar, v, e in zip(b2, inc, ci):
            ax.text(bar.get_x() + bar.get_width() / 2, max(v, 0) + e + 0.18, f"{v:.1f}",
                    ha="center", color=th["ink"], fontsize=10)
        ax.set_xticks(xs, labels, color=th["ink"], fontsize=10.5)
        ax.set_ylabel("Conversions per 1,000 users", color=th["ink2"], fontsize=10)
        ax.axhline(0, color=th["ink2"], linewidth=1)
        ax.set_ylim(min(0, min(inc) - 0.6), max(att) * 1.18)
        ax.grid(False, axis="x")
        leg = ax.legend(loc="upper left", frameon=False, fontsize=10, labelcolor=th["ink"])
        _note(fig, th, "Simulated: 1M users per arm, 2% organic conversion. Error bars: 95% CI of the holdout estimate. Illustrative parameters.")
        fig.savefig(out / f"attribution_gap-{mode}.png", facecolor=th["surface"])
        plt.close(fig)
        written.append(f"attribution_gap-{mode}.png")

        # 3. Theft detection ------------------------------------------------- #
        fig, ax = _setup(plt, th, "How much a vendor can steal before it shows",
                         "Chance a 1% cross-vendor test flags one of six vendors that claims a share of organic conversions")
        for color, n in zip(th["seq"], HOLDOUT_SIZES):
            y = theft["curves"][n]
            ax.plot(STEAL_GRID, y, color=color, linewidth=2.2)
            s50 = theft["share_at_50pct_power"][n]
            ax.plot([s50], [0.5], "o", markersize=8, color=color,
                    markeredgecolor=th["surface"], markeredgewidth=2)
            ax.text(s50 + 0.006, 0.47, f"{users_fmt(n, None)} per arm\n{s50:.0%} at 50%",
                    color=th["ink"], fontsize=9.5, va="top", ha="left")
        ax.axhline(0.5, color=th["ink2"], linewidth=1, linestyle=(0, (4, 3)))
        ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        ax.set_xlim(0, STEAL_GRID[-1])
        ax.set_ylim(0, 1.02)
        ax.set_xlabel("Share of organic conversions the vendor claims as its own", color=th["ink2"], fontsize=10)
        ax.set_ylabel("Detection probability", color=th["ink2"], fontsize=10)
        _note(fig, th, "Analytic omnibus χ² test, 6 vendors, 2% organic conversion, no honest heterogeneity; checked by binomial simulation. Dots: 50% detection.")
        fig.savefig(out / f"theft_detection-{mode}.png", facecolor=th["surface"])
        plt.close(fig)
        written.append(f"theft_detection-{mode}.png")

        # 4. Holdout control -------------------------------------------------- #
        fig, ax = _setup(plt, th, "A vendor that picks its own control group can manufacture lift",
                         "Measured lift for a campaign whose true effect is zero, by share of holdout slots the vendor fills selectively")
        q = hold["q"]
        rel_ci = hold["advertiser_ci95_rate"] / hold["p_mean"]
        ax.fill_between(q, -rel_ci, rel_ci, color=th["band"], alpha=0.14, linewidth=0)
        ax.plot(q, np.zeros_like(q), color=th["blue"], linewidth=2.2)
        ax.plot(q, hold["fake_lift_relative"], color=th["orange"], linewidth=2.2)
        ax.text(q[-1] + 0.006, hold["fake_lift_relative"][-1], "Vendor-chosen\nholdout", color=th["ink"], fontsize=9.5, va="center")
        ax.text(q[-1] + 0.006, 0, "Advertiser-\nrandomized\nholdout", color=th["ink"], fontsize=9.5, va="center")
        ax.text(0.49, -rel_ci + 0.006, "95% noise band, 200k users per arm", color=th["ink2"], fontsize=9, ha="right")
        ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        ax.set_xlim(0, q[-1])
        ax.set_xlabel("Share of holdout slots filled with users the vendor predicts won't buy", color=th["ink2"], fontsize=10)
        ax.set_ylabel("Measured lift (relative to organic)", color=th["ink2"], fontsize=10)
        _note(fig, th, "Simulated: 2M users, gamma-distributed purchase propensity (mean 2%), vendor ranking correlation 0.5. True lift is zero.")
        fig.savefig(out / f"holdout_control-{mode}.png", facecolor=th["surface"])
        plt.close(fig)
        written.append(f"holdout_control-{mode}.png")

        # 5. Published: observational error vs RCT lift ----------------------- #
        fig, ax = _setup(plt, th, "Observational estimates miss by more than the effect itself",
                         "663 Facebook experiments: median RCT lift vs median absolute error of non-experimental estimates")
        levels = [g[0] for g in GORDON_2023]
        rct = [g[1] for g in GORDON_2023]
        err = [g[2] for g in GORDON_2023]
        xs = np.arange(len(levels))
        w = 0.34
        b1 = ax.bar(xs - w / 2 - 0.01, rct, w, color=th["blue"], label="Median RCT lift")
        b2 = ax.bar(xs + w / 2 + 0.01, err, w, color=th["orange"], label="Median absolute error, non-experimental")
        for bars, vals, suffix in ((b1, rct, "%"), (b2, err, " pts")):
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, v + 2, f"{v}{suffix}", ha="center",
                        color=th["ink"], fontsize=10)
        ax.set_xticks(xs, levels, color=th["ink"], fontsize=10.5)
        ax.set_ylabel("Percent / percentage points", color=th["ink2"], fontsize=10)
        ax.set_ylim(0, max(err) * 1.2)
        ax.grid(False, axis="x")
        ax.legend(loc="upper right", frameon=False, fontsize=10, labelcolor=th["ink"])
        _note(fig, th, "Published values: Gordon, Moakler & Zettelmeyer (2023), Marketing Science 42(4). Not simulated.")
        fig.savefig(out / f"gordon2023_observational_error-{mode}.png", facecolor=th["surface"])
        plt.close(fig)
        written.append(f"gordon2023_observational_error-{mode}.png")

        # 6. Selection bias ------------------------------------------------- #
        fig, ax = _setup(plt, th, "Targeting alone can make a small effect look huge",
                         "Estimated purchase lift as targeting leans harder on purchase intent; true lift is fixed at 1 point")
        g = sel["gamma"]
        ax.axhline(100 * TRUE_LIFT_PP, color=th["ink2"], linewidth=1, linestyle=(0, (4, 3)))
        ax.fill_between(g, 100 * (sel["randomized"] - sel["rct_ci95"]), 100 * (sel["randomized"] + sel["rct_ci95"]),
                        color=th["band"], alpha=0.14, linewidth=0)
        ax.plot(g, 100 * sel["observational"], color=th["orange"], linewidth=2.2, marker="o", markersize=7,
                markeredgecolor=th["surface"], markeredgewidth=1.5)
        ax.plot(g, 100 * sel["randomized"], color=th["blue"], linewidth=2.2, marker="o", markersize=7,
                markeredgecolor=th["surface"], markeredgewidth=1.5)
        ax.text(g[-1] + 0.05, 100 * sel["observational"][-1], f"Exposed vs\nunexposed\n{100 * sel['observational'][-1]:.1f} pts",
                color=th["ink"], fontsize=9.5, va="center")
        ax.text(g[-1] + 0.05, 100 * sel["randomized"][-1] + 0.6, f"Randomized\nholdout\n{100 * sel['randomized'][-1]:.1f} pts",
                color=th["ink"], fontsize=9.5, va="bottom")
        ax.text(0.05, 100 * TRUE_LIFT_PP - 0.9, "True lift: 1 point", color=th["ink2"], fontsize=9)
        ax.set_xlim(0, g[-1])
        ax.set_xlabel("How strongly targeting follows latent purchase intent (logit coefficient)", color=th["ink2"], fontsize=10)
        ax.set_ylabel("Estimated lift (percentage points)", color=th["ink2"], fontsize=10)
        _note(fig, th, "Simulated: 400k users, 8% purchase rate at average intent. Band: 95% noise of the randomized estimate. Design after ChatGPT.")
        fig.savefig(out / f"selection_bias-{mode}.png", facecolor=th["surface"])
        plt.close(fig)
        written.append(f"selection_bias-{mode}.png")

        # 7. Covariance geometry --------------------------------------------- #
        fig, ax = _setup(plt, th, "Equal-size footprints are not equally easy to hide",
                         "Concealment capacity 1/√(uᵀΣ⁻¹u) of five unit-size footprints across seven ad metrics")
        labels = [r["footprint"] for r in geo]
        pm = [r["per_metric_capacity"] for r in geo]
        jt = [r["joint_capacity"] for r in geo]
        xs = np.arange(len(labels))
        w = 0.36
        b1 = ax.bar(xs - w / 2 - 0.01, pm, w, color=th["blue"], label="Per-metric view (ignores correlation)")
        b2 = ax.bar(xs + w / 2 + 0.01, jt, w, color=th["orange"], label="Joint view (full covariance)")
        for bars, vals in ((b1, pm), (b2, jt)):
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, v + 0.04, f"{v:.2f}", ha="center", color=th["ink"], fontsize=9.5)
        ax.set_xticks(xs, labels, color=th["ink"], fontsize=9.5)
        ax.set_ylabel("Concealment capacity (higher = easier to hide)", color=th["ink2"], fontsize=10)
        ax.set_ylim(0, max(pm + jt) * 1.25)
        ax.grid(False, axis="x")
        ax.legend(loc="upper right", frameon=False, fontsize=9.5, labelcolor=th["ink"])
        _note(fig, th, "Synthetic covariance: engagement metrics highly correlated, revenue and margin correlated, blocks loosely linked. Design after ChatGPT.")
        fig.savefig(out / f"covariance_geometry-{mode}.png", facecolor=th["surface"])
        plt.close(fig)
        written.append(f"covariance_geometry-{mode}.png")
    return written


# --------------------------------------------------------------------------- #
def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args()
    out = a.output_dir
    out.mkdir(parents=True, exist_ok=True)

    nf = noise_floor()
    gap = attribution_gap(np.random.default_rng(SEED))
    theft = theft_detection(np.random.default_rng(SEED + 1))
    hold = holdout_control(np.random.default_rng(SEED + 2))
    sel = selection_bias(np.random.default_rng(SEED + 3))
    geo = covariance_geometry()

    i10 = int(np.argmin(np.abs(hold["q"] - 0.10)))
    i25 = int(np.argmin(np.abs(hold["q"] - 0.25)))
    summary = {
        "synthetic": True,
        "settings": {"organic_conversion": P0, "vendors": M_VENDORS, "alpha": ALPHA, "seed": SEED},
        "noise_floor": {k: v for k, v in nf.items() if k not in ("d", "n")},
        "attribution_gap": gap,
        "theft_detection": {
            "share_at_50pct_power_by_holdout_per_arm": {str(k): v for k, v in theft["share_at_50pct_power"].items()},
            "share_at_50pct_power_by_tau_200k": {str(k): v for k, v in theft["share_at_50pct_power_by_tau_200k"].items()},
            "false_alarm_if_tau_ignored_200k": {str(k): v for k, v in theft["false_alarm_if_tau_ignored_200k"].items()},
            "monte_carlo_check": theft["monte_carlo_check"],
        },
        "holdout_control": {
            "fake_relative_lift_at_q10": float(hold["fake_lift_relative"][i10]),
            "fake_relative_lift_at_q25": float(hold["fake_lift_relative"][i25]),
            "fake_relative_lift_at_q50": float(hold["fake_lift_relative"][-1]),
            "advertiser_relative_ci95": float(hold["advertiser_ci95_rate"] / hold["p_mean"]),
            "mean_propensity": float(hold["p_mean"]),
            "mean_propensity_vendor_low_half": float(hold["p_low_half"]),
        },
        "selection_bias": {
            "gamma": [float(x) for x in sel["gamma"]],
            "observational_lift": [float(x) for x in sel["observational"]],
            "randomized_lift": [float(x) for x in sel["randomized"]],
        },
        "covariance_geometry": geo,
    }
    (out / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (out / "results.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["result", "metric", "value"])
        w.writerow(["noise_floor", "users_for_expected_t3_at_LR_example", round(nf["lr_users_for_t3"])])
        w.writerow(["noise_floor", "power_at_200k_users_two_sided_5pct", round(summary["noise_floor"]["lr_power_200k_one_sided_5pct"], 4)])
        for r in gap:
            w.writerow(["attribution_gap", f"{r['campaign']} attributed_per_1000", round(r["attributed_per_1000"], 3)])
            w.writerow(["attribution_gap", f"{r['campaign']} incremental_per_1000", round(r["measured_incremental_per_1000"], 3)])
        for n, s in theft["share_at_50pct_power"].items():
            w.writerow(["theft_detection", f"share_at_50pct_power_{n}_per_arm", round(s, 4)])
        for tau, s in theft["share_at_50pct_power_by_tau_200k"].items():
            w.writerow(["theft_detection", f"share_at_50pct_power_200k_tau_{tau}", round(s, 4)])
        for tau, fa in theft["false_alarm_if_tau_ignored_200k"].items():
            w.writerow(["theft_detection", f"false_alarm_if_tau_ignored_200k_tau_{tau}", round(fa, 4)])
        for k in ("fake_relative_lift_at_q10", "fake_relative_lift_at_q25", "fake_relative_lift_at_q50", "advertiser_relative_ci95"):
            w.writerow(["holdout_control", k, round(summary["holdout_control"][k], 4)])
        for gmm, o, r in zip(sel["gamma"], sel["observational"], sel["randomized"]):
            w.writerow(["selection_bias", f"gamma_{gmm:.2f} observational_pp", round(100 * o, 3)])
            w.writerow(["selection_bias", f"gamma_{gmm:.2f} randomized_pp", round(100 * r, 3)])
        for r in geo:
            name = r["footprint"].replace("\n", " ")
            w.writerow(["covariance_geometry", f"{name} per_metric", round(r["per_metric_capacity"], 4)])
            w.writerow(["covariance_geometry", f"{name} joint", round(r["joint_capacity"], 4)])

    if not a.no_figures:
        files = make_figures(out / "figures", nf, gap, theft, hold, sel, geo)
        print(f"wrote {len(files)} figures to {out / 'figures'}")
    print(json.dumps({"noise_floor_users_t3": round(nf["lr_users_for_t3"]),
                      "steal_share_50pct": {k: round(v, 3) for k, v in theft["share_at_50pct_power"].items()},
                      "fake_lift_q25": round(summary["holdout_control"]["fake_relative_lift_at_q25"], 3)}))
    print("All ad-fraud case-study checks passed.")
    return summary


if __name__ == "__main__":
    main()
