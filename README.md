# Hiding in the Noise

**Reach-limited contamination in ON/OFF detection: a framework for catching a careful actor who tries to look like ordinary background noise.**

This began as a thought experiment about a hidden nonhuman population living among us ("cryptoterrestrials") and turned into a small, fully reproducible study in adversarial statistics. The work was done by relaying versioned research packages between two AI systems that built, re-ran and critiqued each other's work, with a human operator directing the project.

> **Status:** research prototype. **All data are synthetic.** Nothing here is evidence for or against the existence of any hidden population. The framework describes what evidence would have to look like for such a hypothesis to become distinguishable from ordinary processes.

## The thought experiment

Assume some mixture of these is true:

1. Intelligent nonhuman life has been present on Earth throughout human evolution.
2. It lives among us in stealth, practically indistinguishable from humans.
3. It follows something like a prime directive: no steering of human affairs.
4. It is indifferent to us except for planet-scale effects: climate, nuclear war, bioweapon release.

The question became: **what could observation ever reveal?** Within a few rounds the aliens dropped out of the mathematics, leaving a general problem that also covers fraud detection, tampered sensors and poisoned training data.

## Main results (all within the synthetic models)

| Finding | Result |
|---|---|
| Perfect mimicry is undetectable | If presence leaves the observed distribution unchanged, the Bayes factor is exactly 1 forever. |
| Hiders exploit uncalibrated noise | Under a log concealment cost, the optimal footprint is `s* = √(κV)` and the optimal divergence is `KL* = κ/2`, independent of `V`. Calibration shrinks the footprint; it does not make the hider easier to catch. |
| Single-channel ON/OFF is not identifiable | With only ON counts, unlimited replication estimates `B + s`, never the components. An independent OFF control is required. |
| Check that comparisons agree | Against a hider shifting 4 of 8 controls (`τ = 0`, `s = 10`, all 8 measured), a mean-only test detects ~20%; an omnibus test of equality across channels detects ~84%. Contamination is itself evidence. |
| Uncalibrated spread is attackable | Estimating heterogeneity from the controls lets a hider inject spread: two ±δ controls drop power from 0.99 to 0.55 (δ = 10) with 8 controls. |
| Randomize tests, not just controls | The exact mixed-policy frontier (LP) drives contamination willingness-to-pay to zero at plain-activity hider utility 0.146 vs 0.202 for the best single test (`τ = 0`). |
| Hiders mostly do less | Better cross-channel testing usually pushes the hider toward a smaller footprint; whether it still contaminates depends on contamination cost relative to its willingness to pay. |
| Known covariance exposes, but cannot erase, geometry | With clustered covariance known exactly, a cluster-aligned shift loses ~54% of its noncentrality while a misaligned one gains ~80% (`ρ = 0`, `c = 4`). |

The closing statement of the geometry: for a feasible footprint direction `u` (fixed physical normalization) and ordinary background covariance `Σ`,

```
C*(Σ, U) = max_{u ∈ U, ‖u‖ = 1}  1 / sqrt(uᵀ Σ⁻¹ u)
```

which equals `sqrt(λ_max(Σ))` when every direction is feasible. Concealment gets expensive when the hider's physical needs force its footprint away from the background's high-variance directions.

## Repository layout

```
framework/     The core series, v1.0.0 → v1.3.6 (each release replaced this folder; see git history)
covariance/    The covariance stage, v1.4.0 → v1.4.2 (protected / known-Σ analytic benchmark)
independent-checks/   Scripts used to independently re-run and probe each release
```

Each release is a commit with a matching tag (`v1.0.0` … `v1.4.2`), so `git diff v1.3.2 v1.3.3` shows exactly what a correction changed. Every package ships a `SHA256SUMS.txt` manifest.

The v1.2.0 package shipped compiled Python bytecode; it was left out here, so that release's manifest lists two `.pyc` files that are absent.

Note: `framework/README.md` was carried forward unchanged from v1.3.2; the current notes are `Reach_Limited_Contamination_ON_OFF_v1.3.5.md` and `README_v1.3.5.md`.

## Reproducing

Python 3.11+.

```bash
pip install -r framework/requirements.txt

# Core game (Monte Carlo) and the v1.3.4 / v1.3.5 reporting and mixed-frontier tables
cd framework
python verify_models_v1_3_3.py --output-dir out
python verify_reporting_v1_3_4.py --input joint_strategy_results_v1_3_3.csv --output-dir out
python verify_models_v1_3_5.py --input joint_strategy_results_v1_3_3.csv --output-dir out
cd ..

# Protected-covariance benchmark with its five invariants
cd covariance
python verify_protected_v1_4_2.py \
  --archive-frontier mixed_policy_frontier_v1_3_5.csv \
  --archive-cells joint_strategy_results_v1_3_3.csv \
  --output-dir out
```

Generated tables should match the packaged ones byte for byte. The v1.4.2 seeded simulation uses Cholesky factorization so results agree across numpy/LAPACK builds.

## Version history

| Tag | What changed |
|---|---|
| v1.0.0 | Model comparison framework: Poisson–Gamma detection, secrecy hazard, genomic sampling, warden vs cohabitant intervention, first adversarial hider. |
| v1.1.0 | Closed form `s* = √(κV)`, `KL* = κ/2`; ON-only non-identifiability; toy Stackelberg game with a randomized control. |
| v1.2.0 | Coverage game over many controls; between-channel heterogeneity `τ`; false alarms under misspecified `τ`. |
| v1.3.0 | Joint hider strategy (signal, reach, level/spread/mixed attacks); robust scale estimators; size-valid calibration filter. |
| v1.3.1 | Observer gains omnibus and combined (exchangeability) tests. |
| v1.3.2 | Fine signal grid and utility sweep; retitled as a methods study. |
| v1.3.3 | Symmetric attack grid; contamination-cost sweep and willingness-to-pay. Corrects "contamination is rarely chosen". |
| v1.3.4 | Reporting: size-validity flags, grid-ceiling lower bounds, pure-policy robustness–efficiency frontier. |
| v1.3.5 | Exact mixed-policy frontier by linear programming; reproducible post-processor for the v1.3.4 tables. |
| v1.3.6 | Dependency fix (`pandas`). |
| v1.4.0 | Protected-covariance analytic benchmark with clustered `Σ`; alignment made a hider choice. |
| v1.4.1 | Real end-to-end simulation invariants; cell-level regression against v1.3.3. |
| v1.4.2 | Cholesky sampling for cross-platform reproducibility; documented basis for the regression bound. |

## Corrections made along the way

Both AI systems had claims retracted. Some examples:

- **Secrecy.** An early argument that a hidden group "would have leaked by now" used an invented leak rate. With a published estimate of secrecy failure (Grimes, 2016), a group growing to ~1,000 over a century has ~80% odds of no exposure.
- **Calibration.** "Noisier backgrounds let a hider do 3× more" is true for footprint, but the closed form shows optimized detectability is identical; calibration suppresses rather than catches.
- **Square-root steganography law.** Applied too broadly; it is conditional on imperfect hiding.
- **"Contamination is rarely chosen."** An artifact of fixed contamination costs and a coarser contaminated-strategy grid; at zero cost it is chosen in 20–27 of 27 settings.
- **Pure vs mixed frontier.** The pure-policy frontier overstated the robustness–efficiency tradeoff by 17–28%.
- **Verifier hygiene.** A size invariant that could never fail, a regression tolerance chosen just above the observed error, and SVD-based sampling that was not reproducible across machines were all replaced.

## Ethics

The framework is meant for aggregate, infrastructure-level analysis. Applied to individuals it is both statistically hopeless and harmful: with 1,000 hypothetical residents among 8 billion people, a test with a 1-in-10,000 false-alarm rate flags ~800,000 ordinary people for every 1,000 true positives, and a strategic hider would sit among already-marginalized groups. Do not use it to score individuals.

## Provenance

- Research packages (models, code, notes): generated by ChatGPT (OpenAI).
- Independent re-runs, critiques and the scripts in `independent-checks/`: Claude (Anthropic).
- Direction, relay between the two systems and decisions about what held up: Benjamin W. Denio.

Presented at the AI InTheRock Local AI Showcase, North Little Rock, November 2026.

## References

- Cachin, C. (1998). An information-theoretic model for steganography. *Information Hiding*, LNCS 1525.
- Ćirković, M. M., Sandberg, A., & Bostrom, N. (2010). Anthropic shadow. *Risk Analysis* 30(10).
- Grimes, D. R. (2016). On the viability of conspiratorial beliefs. *PLOS ONE* 11(1), with correction.
- Ker, A. D., Pevný, T., Kodovský, J., & Fridrich, J. (2008). The square root law of steganographic capacity. *MM&Sec*.
- Li, T.-P., & Ma, Y.-Q. (1983). Analysis methods for results in gamma-ray astronomy. *ApJ* 272.
- Lomas, T., Case, B., & Masters, M. P. (2024). The cryptoterrestrial hypothesis. *Philosophy and Cosmology* 33.

## License

MIT. See [LICENSE](LICENSE).
