# Reach-Limited Contamination in ON/OFF Detection, v1.3.2

**Status:** Synthetic adversarial-statistics methods note. The original extraterrestrial scenario is retained only as motivation; no empirical claim about a concealed population is made.  
**Version:** 1.3.2  
**Date:** 2026-11-01  
**Reproducibility:** `python -B verify_models_v1_3_2.py --output-dir .`

## Abstract

This note studies an ON/OFF detection problem in which an adaptive source can reduce its signal and can contaminate a reach-limited subset of control channels. The observer may use directional ON-minus-OFF tests, equal-means omnibus tests, or a Bonferroni combination, with empirical, protected, or physics-only scale calibration. Version 1.3.2 addresses a weakness in v1.3.1: the equilibrium signal sat on the lower edge of a coarse grid, and the activity/detection utilities had not been stress-tested.

The signal grid is refined to 0.5-unit spacing below 10, and the game is re-solved under 27 combinations of activity-benefit scale, detection penalty, and benefit curvature for each heterogeneity level. The main result is narrower than the earlier claim: footprint suppression is common at low and moderate heterogeneity, but it is not universal. At high heterogeneity, most tested utility settings support continued uncontaminated activity. Control contamination is rarely optimal once the observer can exploit cross-channel disagreement.

## 1. Motivating scenario and scope

The project began from four speculative premises about a persistent concealed nonhuman population. Those premises no longer enter the mathematics. They motivate only the adversarial structure: a source may prefer low detectability, may have long access to the observation environment, and may strategically alter its footprint.

The actual model is therefore best read as a small study of **reach-limited contamination in ON/OFF detection**. Its conclusions apply only to the stated Gaussian toy model and utility functions.

## 2. Structural conclusions retained from earlier versions

1. **Restricted non-identifiability.** If an adversary can make the full observed joint distribution identical to an allowed null distribution, passive observations cannot distinguish the two.
2. **Conditional identifiability.** If reach, timing, physics, or distributional structure prevents full matching, informative contrasts can remain.
3. **Equal-means structure is not full exchangeability.** The omnibus test used here asks whether Gaussian channels share a mean under a common known variance. That is one testable consequence of exchangeability, not a test of exchangeability itself. Ordinary heterogeneity can violate it without an adversary.
4. **Coverage matters only when the statistic uses cross-channel structure.** Measuring more controls does little for a pure ON-minus-average statistic against some level attacks, but it can strongly increase power for an omnibus disagreement test.

## 3. v1.3.2 changes

The uncontaminated signal grid is

`0, 0.5, 1.0, ..., 10.0, 12.5, 15, 20, 25, 30`.

Control-contamination attacks use a smaller strategic grid `2, 4, 5, 7.5, 10, 20, 30` for tractability. The observer action set is unchanged from v1.3.1.

The hider's activity benefit is generalized to

\[
U_{\rm benefit}(s)=A\,\frac{\log(1+s/c)}{\log(1+20/c)},
\]

where `A` is the activity-benefit scale and `c` controls curvature. Detection carries penalty `D`. The sensitivity sweep uses

- `A in {0.3, 0.6, 0.9}`;
- `D in {0.5, 1.0, 2.0}`;
- `c in {2.5, 5.0, 10.0}`.

This gives 27 utility settings per heterogeneity level. Statistical power is simulated once per attack and reused across utility settings; only the game utilities and equilibria are recomputed.

## 4. Default-utility equilibrium after refining the signal grid

With the original default utility parameters (`A=0.6`, `D=1`, `c=5`):

| tau | v1.3.1 signal | v1.3.2 signal | reach | contamination | detection |
|---:|---:|---:|---:|---|---:|
| 0 | 5 | **3.5** | 0 | none | 0.0848 |
| 3 | 5 | **5.0** | 0 | none | 0.0940 |
| 10 | 20 | **15.0** | 0 | none | 0.0985 |

The v1.3.1 grid-floor concern was real at `tau=0`: the finer game moves the best response below 5. The high-heterogeneity equilibrium also shifts from 20 to 15. In all three default cases the hider avoids control contamination.

These detection probabilities are equilibrium outputs under invented utilities. They should not be interpreted as empirical detection rates.

## 5. Utility sensitivity: where the qualitative regime changes

For reporting, hider responses are classified as:

- **abstain:** `s=0`;
- **suppress:** positive `s<10`, no control contamination;
- **operate_uncontaminated:** `s>=10`, no control contamination;
- **contaminate:** positive signal with control contamination.

Across the 27 settings at each tau:

| tau | Abstain | Suppress | Operate uncontaminated | Contaminate |
|---:|---:|---:|---:|---:|
| 0 | 2 | **18** | 6 | 1 |
| 3 | 2 | **19** | 5 | 1 |
| 10 | 0 | 4 | **23** | 0 |

Thus footprint suppression is a broad regime at low and moderate heterogeneity in this sweep, but not at high heterogeneity. The earlier conclusion that a capable observer generally forces the hider to “do less” was too broad.

Only two of 81 utility/tau combinations select contamination. Both use high activity benefit (`A=0.9`), unit detection penalty, high curvature (`c=10`), signal `s=30`, reach `r=2`, and a level attack. This suggests that the observer's enlarged cross-channel test set usually makes contamination less attractive than changing activity level, **within the tested utility region**.

Abstention appears only at `tau=0` or `tau=3`, under low activity benefit (`A=0.3`) and high detection penalty (`D=2`). No high-heterogeneity setting in this sweep produces abstention.

## 6. What the sensitivity sweep establishes—and what it does not

The sweep changes the status of the footprint-suppression claim.

It is **not a theorem** and not a property of the statistical tests alone. It is a game-theoretic outcome jointly determined by:

- statistical power;
- signal benefit;
- detection penalty;
- control-contamination costs;
- measurement costs; and
- the allowed strategy grids.

Within the tested region, suppression is common for `tau=0` and `tau=3`, while continued uncontaminated operation dominates at `tau=10`. The correct conclusion is therefore:

> Better cross-channel testing often changes the hider's preferred response from control contamination to adjustment of the activity level, but whether that adjustment means abstention, strong suppression, or continued operation depends materially on the utility model and background heterogeneity.

That is an illustration of a robust *mechanism*—substitution away from contamination—not a universal equilibrium law.

## 7. Why covariance belongs in v1.4, not v1.3.2

The present model assumes independent Gaussian channel errors after accounting for scalar heterogeneity `tau`. An unknown covariance matrix `Sigma` creates the matrix analogue of the earlier scale problem:

- innocent correlation can mimic or mask cross-channel disagreement;
- empirical covariance estimation can itself be contaminated;
- a strategic source may inject correlated structure rather than only mean or scale shifts.

Version 1.4 should therefore replace scalar `tau` with structured covariance families and distinguish protected, empirical-robust, and physics-constrained covariance calibration. That extension is meaningful only after the utility sensitivity in v1.3.2, because otherwise changes in equilibrium could be incorrectly attributed to covariance when they are actually caused by arbitrary preference choices.

## 8. Stable closing claims

The project now supports three carefully qualified claims:

1. **Non-identifiability under unrestricted distribution matching.** If the alternative can reproduce every observable distribution allowed by the null, passive data cannot distinguish labels on that same distribution.
2. **Conditional identifiability through protected structure.** If the adversary cannot preserve a valid structural relation—here, an equal-means relation across independently calibrated Gaussian channels—an observer can recover information without knowing an absolute historical baseline.
3. **Strategic substitution, not guaranteed suppression.** When contamination becomes detectable, an adaptive source may substitute toward lower activity. The amount of suppression is utility-sensitive, and at high heterogeneity the tested game usually favors continued uncontaminated activity instead.

These are results about the synthetic adversarial-detection model. They neither establish nor refute the motivating extraterrestrial premises.

## 9. Reproducibility

Run:

`python -B verify_models_v1_3_2.py --output-dir .`

Primary outputs:

- `joint_strategy_results_v1_3_2.csv`
- `stackelberg_joint_equilibria_v1_3_2.csv`
- `utility_sensitivity_v1_3_2.csv`
- `utility_regime_summary_v1_3_2.csv`
- `spread_benchmark_v1_3_2.csv`
- `results_v1_3_2.json`

Historical versions are retained for comparison. The archive intentionally excludes `__pycache__` and `*.pyc` files.
