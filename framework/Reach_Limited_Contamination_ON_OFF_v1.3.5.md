# Reach-Limited Contamination in ON/OFF Detection — v1.3.5

## Scope

This maintenance release closes the v1.3 series. The extraterrestrial scenario that originally motivated the work is retained only as motivation; the mathematical object is a finite adversarial ON/OFF detection game with reach-limited contamination.

v1.3.5 makes two corrections to v1.3.4:

1. **Reproducibility:** `verify_reporting_v1_3_4.py` deterministically regenerates the v1.3.4 WTP and pure-policy frontier tables from `joint_strategy_results_v1_3_3.csv`.
2. **Mixed commitments:** `verify_models_v1_3_5.py` computes an exact mixed-policy robustness–efficiency frontier using linear programming. The observer commits to a randomized protected-scale test before the hider chooses its action.

## Why the pure frontier was incomplete

The pure-policy frontier treated each observer test separately. But previous versions already allowed the observer to commit to randomized strategies. A hider that sees the distribution over tests but not the realized draw must choose one attack against the whole mixture.

For a mixture x over observer policies, define

- U0(x): the hider's maximum expected utility over uncontaminated actions;
- UC(x): the hider's maximum expected utility over zero-cost contaminated actions;
- WTP(x) = max(0, UC(x) - U0(x)).

For each WTP cap w and expected-control budget K, v1.3.5 solves

    minimize   U0(x)
    subject to WTP(x) <= w
               E_x[k] <= K
               sum_i x_i = 1,  x_i >= 0.

Because both U0 and UC are maxima over a finite action set, the script obtains the exact finite-game solution by enumerating the uncontaminated best-response face and solving a linear program on each face.

Only the size-valid protected-scale policy family is used in the mixed frontier:

- directional protected-scale;
- omnibus protected-scale;
- Bonferroni combined protected-scale;

for k in {4, 6, 8} controls.

## Main result: randomization moves the frontier inward

With no expected-k restriction beyond k <= 8, the zero-WTP optimum is:

| tau | Plain-activity hider utility | Optimal commitment |
| ---: | ---: | --- |
| 0 | 0.1464 | 69.0% combined + 31.0% omnibus, both k=8 |
| 3 | 0.2067 | 72.1% combined + 27.9% omnibus, both k=8 |
| 10 | 0.4224 | 74.4% combined + 25.6% omnibus, both k=8 |

These improve materially on the best pure zero-WTP policies. Randomization prevents the hider from tailoring a contamination strategy to a known test while retaining more power against uncontaminated ON activity than omnibus-only testing.

At tau=0, for example, the pure omnibus endpoint has plain-activity utility about 0.202 at WTP=0. The mixed commitment reduces that to about 0.146 while preserving zero contamination WTP.

## Measurement effort is a third axis

The frontier changes when expected control count is constrained. At WTP=0:

| tau | max E[k]=4 | max E[k]=6 | max E[k]=8 |
| ---: | ---: | ---: | ---: |
| 0 | 0.1737 | 0.1556 | 0.1464 |
| 3 | 0.2369 | 0.2167 | 0.2067 |
| 10 | 0.4695 | 0.4362 | 0.4224 |

Lower is better for the observer. Thus robustness, power against plain activity, and measurement effort form a three-way design problem. The CSV records both `expected_k` and an illustrative `expected_measurement_cost = 0.01 * expected_k`; the LP constrains expected k directly rather than burying measurement effort in the objective.

## Reproducibility repair for v1.3.4

`verify_reporting_v1_3_4.py` reads the verified v1.3.3 payoff table and writes:

- `contamination_wtp_v1_3_4.csv`
- `robustness_efficiency_frontier_v1_3_4.csv`

The size-validity rule is explicit: physics-only tests are diagnostic rather than design-valid when tau > 0. Grid-ceiling flags are also regenerated deterministically. The packaged v1.3.4 reporting CSVs are the outputs of this postprocessor.

## Final v1.3 conclusions

1. **Unrestricted distribution matching implies non-identifiability.** If an actor can make the complete observed joint distribution match an allowed null distribution, passive observations cannot distinguish the hypotheses.
2. **Reach limits can restore conditional identifiability.** Partial contamination can violate cross-channel equal-means structure when that structure is independently justified and its covariance/scale is adequately calibrated.
3. **Contamination value is test-dependent.** Directional tests can be efficient against plain activity yet exploitable by control contamination; omnibus tests can make partial contamination counterproductive but sacrifice directional power.
4. **Randomization improves the robustness–efficiency frontier.** A hider that cannot anticipate the realized test cannot tailor one contamination attack to each component of the observer's mixed commitment.
5. **Measurement effort matters separately.** The best mixed frontier improves as the observer can afford to measure more controls.
6. **Adaptive response is utility-dependent.** Abstention, footprint suppression, contamination, and continued operation are equilibrium outcomes only relative to specified benefits, detection penalties, contamination costs, and background structure.

A concise closing statement is therefore:

> A test that eliminates contamination WTP by sacrificing power against plain activity has moved the hider's gain along a robustness–efficiency frontier; randomizing over tests moves that frontier inward because a hider that cannot anticipate the realized test cannot tailor its contamination. The improvement is limited by measurement effort and by how well the observer knows the joint background structure.

## Next version

v1.4 should replace scalar heterogeneity with a covariance matrix Sigma and compute the mixed-commitment frontier from the outset as Sigma moves from known/protected to estimated to strategically attackable. Contamination WTP, plain-activity utility, and measurement effort should remain separate reported axes.
