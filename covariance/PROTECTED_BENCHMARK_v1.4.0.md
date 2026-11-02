# Protected covariance benchmark · v1.4.0

## Frozen information factors

Later v1.4 stages use one information factor per player rather than overlapping “regime” and “knowledge” factors:

- Observer information: true Sigma / clean estimate Sigma-hat_T / poisoned estimate.
- Hider information: true Sigma / its own estimate.

The present deliverable covers only `(observer=true Sigma, hider=true Sigma)`.

## Covariance family

For one ON channel in its own cluster and eight controls in clusters of size `c`:

`Sigma = v I + tau^2 [ rho 11^T + (1-rho) blockdiag(J_1, J_c, ... ) ]`.

Marginal variance is fixed at `v + tau^2`. Increasing `rho` transfers variance from cluster-specific modes into common mode. Common mode cancels in centered contrasts; cluster-aligned directions can nevertheless remain intrinsically noisy.

## Protected test

Let `D` map the observed channels to ON-minus-control contrasts and `Omega = D Sigma D^T`. The protected omnibus statistic is the Mahalanobis quadratic form. Under a mean shift with contrast vector `z`, its noncentrality is `lambda = z^T Omega^-1 z` and power is computed exactly from the noncentral chi-square distribution.

Known covariance therefore does **not** neutralize an aligned attack. It removes covariance uncertainty; it cannot erase genuine high-variance directions.

## Four invariants

1. `rho=0,c=1` reduces exactly to the independent scalar-heterogeneity model.
2. Adding pure common-mode covariance leaves contrast covariance unchanged.
3. The protected omnibus test has nominal null size for every positive-definite Sigma.
4. The analytic anchor agrees with the archived v1.3.5 Monte Carlo frontier within a declared regression tolerance. Exact byte equality is not meaningful because the predecessor is sampled.

## v1.4 target quantity

When estimated and attackable covariance stages are added, compare frontiers at fixed WTP cap and effort:

`Delta(w) = U_plain*(w; estimated/attackable) - U_plain*(w; protected)`.

The protected frontier is the analytic baseline. The later empirical question is the **excess** vulnerability caused by estimation error or calibration poisoning, beyond intrinsic Mahalanobis geometry.

Effort remains a vector `(E[k], T)`; protected covariance has no calibration-length cost, while estimated regimes will expose `T` explicitly.
