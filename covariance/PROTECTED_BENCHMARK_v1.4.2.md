# Reach-Limited Contamination in ON/OFF Detection — v1.4.2 Protected-Covariance Benchmark

## Purpose

This maintenance release hardens the protected-covariance benchmark before the clean-estimate and attackable-covariance stages.

The protected regime assumes the observer knows the true covariance matrix Σ and uses it in the test. Its role is to separate **intrinsic attack geometry** from any later excess vulnerability caused by estimating or poisoning Σ.

## Covariance family

For nine channels (one ON channel and eight controls),

Σ = v I + τ² [ ρ 11ᵀ + (1−ρ) blockdiag(J_c) ].

At ρ = 0 and c = 1 this reduces exactly to (v+τ²)I, which is the independent scalar-heterogeneity model used by the protected-scale branch of v1.3.

For centered contrasts z = Cx, the contrast covariance is Ω = CΣCᵀ. The protected omnibus statistic is Mahalanobis:

Q = zᵀ Ω⁻¹ z.

Under a fixed mean shift its power is given by a noncentral χ² distribution with noncentrality λ = μ_zᵀ Ω⁻¹ μ_z.

## Verifier invariants

v1.4.2 retains the v1.4.1 substantive checks and makes the seeded simulation portable across linear-algebra builds.

1. **Exact model reduction.** ρ=0,c=1 gives (v+τ²)I to numerical precision.
2. **Common-mode contrast identity.** Adding γ11ᵀ leaves CΣCᵀ unchanged.
3. **Seeded null-size simulation.** Direct multivariate-normal simulation under clustered Σ exercises the actual whitening/statistic path and must reproduce the nominal 1% omnibus size within a four-Monte-Carlo-SE envelope.
4. **Seeded power simulation.** Direct simulation across several clustered/aligned/misaligned cases must match the analytic omnibus and combined powers within a four-Monte-Carlo-SE envelope.
5. **Cell-level v1.3.3 regression.** All 675 non-null protected-policy Monte Carlo cells at τ=3 are compared with their exact independent-model powers. Differences are divided by their binomial Monte Carlo standard errors. The residual SD must remain near one; a common mean offset is allowed because v1.3.3 deliberately reused the same random draws across attacks.

For the archived v1.3.3 seed, the standardized residual mean is +0.793234 and SD is 0.959403. Three additional checked seeds produced mean residuals +0.02, +0.49, and +0.05. The verifier therefore freezes |mean| <= 1.5 (roughly twice the largest observed common shift) together with residual SD in [0.65, 1.35]. This records the basis of the bound rather than tuning it to the archived seed.

The seeded multivariate-normal verifier uses Cholesky factorization explicitly. Clustered covariance matrices have repeated eigenvalues, so SVD-based seeded sampling is not portable across LAPACK implementations even when the distribution is identical.

## Protected attack geometry

Known covariance does not neutralize an aligned attack. Whitening correctly weights directions by their actual covariance; it cannot make a genuinely noisy eigen-direction as informative as a quiet one.

Thus the protected benchmark captures the intrinsic geometric component of contamination value. Later v1.4 stages should measure frontier degradation relative to this protected baseline rather than attributing all difficulty to covariance estimation.

## Scope of attack family

The protected benchmark intentionally includes **level shifts only**. Spread and mixed attacks from v1.3 are omitted here because with true Σ fixed and protected they do not attack the covariance estimator; they simply induce additional observable structure under the specified mean-shift testing problem.

They must return in the estimated-Σ and attackable-Σ stages, where spread injection can alter or poison Σ̂ and is therefore strategically distinct rather than redundant.

## Outputs

- `protected_frontier_anchor_v1_4_2.csv`
- `protected_attack_geometry_v1_4_2.csv`
- `protected_simulation_checks_v1_4_2.csv`
- `protected_v133_cell_residuals_v1_4_2.csv`
- `protected_invariants_v1_4_2.csv`

The archived `joint_strategy_results_v1_3_3.csv` is included so the cell-level regression can be regenerated from the package itself.

## Frozen clean-estimate design

Before the estimated-covariance stage, three choices are fixed. First, a statistic whitened by an estimated covariance must use its finite-sample reference distribution rather than chi-square critical values when that distribution is known; for the ordinary independent covariance estimate/new-observation setup this is the relevant Hotelling/scaled-F correction and requires adequate calibration degrees of freedom. Second, covariance estimation method is an observer action: both a full covariance estimate and lower-dimensional structured estimates belong in the policy set, with misspecification risk recorded explicitly. Third, calibration-data visibility is an information factor: the hider may know only the true covariance, or may additionally see the realized estimated covariance when calibration records are public. Private/randomized calibration membership is reserved for the attackable stage.
