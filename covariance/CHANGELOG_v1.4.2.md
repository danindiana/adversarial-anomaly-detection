# Changelog — v1.4.2 protected benchmark

Maintenance-only portability and documentation patch.

- Seeded multivariate-normal verifier now uses `method='cholesky'` rather than NumPy's default SVD factorization. The clustered covariance matrices contain repeated eigenvalues; SVD bases can differ across LAPACK builds, making identical seeds produce different sample paths. The positive-definite Cholesky factor is unique up to floating-point rounding and gives a stable seeded construction across builds.
- The cell-regression `|mean standardized residual| <= 1.5` bound now states its empirical basis explicitly: four independently checked v1.3.3 seeds produced mean residuals +0.79, +0.02, +0.49, and +0.05. The bound was frozen at roughly twice the largest observed common shift.
- No model, covariance family, test, strategy set, utility, or analytic frontier definition changed.
- Clean-estimate stage specification frozen: estimated covariance tests must use finite-sample calibration (Hotelling/scaled-F where applicable), covariance estimator is an observer action, and calibration-data visibility is an explicit information factor.
