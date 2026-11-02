# Reach-Limited Contamination in ON/OFF Detection — v1.3.3

## Status

This patch closes the v1.3.x sensitivity work before covariance structure is introduced in v1.4. The extraterrestrial scenario that motivated the project is retained only as a motivating example; all numerical results below concern a synthetic reach-limited adversarial ON/OFF detection game.

## What changed from v1.3.2

1. **Symmetric signal grid.** Contaminated and uncontaminated strategies now use the same signal grid: 0.5 increments through 10, then 12.5, 15, 20, 25, and 30. This removes the prior coarse-grid bias against contamination.
2. **Contamination-cost sensitivity.** At the default activity utility, the reach cost is swept over 0, 0.005, 0.01, and 0.02 per reached control, with spread cost fixed at twice the reach cost.
3. **Cost-free willingness to pay (WTP).** For every pure observer policy and heterogeneity level, WTP is defined as the hider's best zero-contamination-cost utility with contamination available minus its best utility without contamination. Negative values mean contamination is inferior even when free; economically, positive WTP is max(0, raw difference).
4. **Equal treatment of attack classes.** The signal grid no longer differs between control-contamination and uncontaminated strategies.
5. The verified v1.3.2 utility sweep is retained as historical context rather than recomputed in a full cross-product with contamination costs. This patch targets the two diagnostics needed to resolve the critique directly.

## Default-utility equilibria on the symmetric grid

| tau | signal s* | reach r* | mode | detection |
|---:|---:|---:|---|---:|
| 0 | 3.5 | 0 | none | 0.083 |
| 3 | 5 | 0 | none | 0.087 |
| 10 | 15 | 0 | none | 0.094 |

At the default contamination costs (0.02 per reached control; spread cost 0.04), the hider again avoids control contamination. The refined grid gives s*=3.5, 5, and 15 for tau=0, 3, and 10 respectively. These are Monte Carlo equilibria under the specified utility function, not general theorems.

## Default-utility contamination-cost sweep

| tau | cost/control | best regime | s | r | mode | detection |
|---:|---:|---|---:|---:|---|---:|
| 0 | 0 | contaminate | 4 | 4 | level | 0.063 |
| 0 | 0.005 | suppress | 4 | 0 | none | 0.074 |
| 0 | 0.01 | suppress | 3.5 | 0 | none | 0.071 |
| 0 | 0.02 | suppress | 3.5 | 0 | none | 0.083 |
| 3 | 0 | contaminate | 6 | 4 | level | 0.069 |
| 3 | 0.005 | suppress | 6 | 0 | none | 0.083 |
| 3 | 0.01 | suppress | 5.5 | 0 | none | 0.075 |
| 3 | 0.02 | suppress | 5 | 0 | none | 0.087 |
| 10 | 0 | contaminate | 15 | 4 | level | 0.073 |
| 10 | 0.005 | operate_uncontaminated | 15 | 0 | none | 0.091 |
| 10 | 0.01 | operate_uncontaminated | 15 | 0 | none | 0.103 |
| 10 | 0.02 | operate_uncontaminated | 15 | 0 | none | 0.094 |

At the default utility parameters, **free contamination is selected at every heterogeneity level**, normally as a four-control level shift. Raising the reach cost to only 0.005 per control is sufficient to switch the best response away from contamination in all three cases. This shows why the earlier “contamination is rarely selected” count was not a stable result: the fixed cost constant was doing substantial work.

## Willingness to pay for contamination

For a fixed observer policy d, define

```text
WTP(d,tau) = max_a in contaminated U_h(a|d,tau,c=0)
             - max_a in uncontaminated U_h(a|d,tau).
```

This is a cost-free measure of how much strategic value contamination adds before an operating price is imposed. It is not itself an equilibrium quantity because the observer policy is held fixed. A positive value is the maximum total contamination cost the hider would rationally pay under that policy and the default activity/detection utilities. A negative value means the contamination capability has no positive willingness-to-pay.

The full table is in `contamination_wtp_v1_3_3.csv`. A few qualitative patterns are robust in this synthetic model:

- Mean-only empirical-scale tests can give contamination substantial value, especially when control heterogeneity is larger.
- Protected-scale omnibus tests often make contamination inferior even when it is free; this is the direct value of testing cross-channel disagreement.
- Combined protected tests leave a smaller but usually positive contamination value in many settings because the hider can trade off directional and equality violations.
- Physics-only tests are invalid when natural heterogeneity tau>0 unless the physical model actually accounts for that heterogeneity; negative WTP there should not be interpreted as superior real-world performance.

## Interpretation

The stable statement is therefore weaker and cleaner than the v1.3.2 regime-count claim:

> **Cross-channel testing sharply reduces the value of control contamination when between-channel heterogeneity is small or externally calibrated, so modest contamination costs can then deter it. As uncalibrated heterogeneity grows, contamination can regain value. Whether the adaptive response is abstention, footprint suppression, contamination, or continued operation depends on the actor's utility function, contamination costs, and the observer's background model.**

The cost-free WTP statistic is preferable to raw regime counts when comparing test architectures because it separates the *strategic value* of contamination from an arbitrary assumed contamination price.

## Statistical qualification

The omnibus statistic used here tests equality of Gaussian channel means under a common known variance. Equality of means is **one consequence of exchangeability**, not exchangeability itself. Unmodeled heterogeneity or covariance can violate that consequence without any adversary. Conversely, an adversary that can induce correlated structure may hide inside an incorrectly specified covariance model.

That makes covariance the natural v1.4 object: replace scalar heterogeneity tau^2 with a covariance matrix Sigma, distinguish known/protected/estimated Sigma, and track contamination WTP as the primary response variable.

## Reproducibility

`verify_models_v1_3_3.py` uses a fixed seed and 10,000 Monte Carlo draws per policy/attack cell. v1.3.3 deliberately reduces this from 20,000 to keep the symmetric attack grid tractable; all reported v1.3.3 files are generated by the packaged script. Historical v1.3.2 outputs remain in the package for comparison. No Python bytecode is shipped.
