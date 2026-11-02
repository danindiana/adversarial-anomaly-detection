# v1.4.1

- Replaced the tautological chi-square size check with seeded direct simulation through Σ, contrasts, whitening, and the actual omnibus statistic.
- Added the previously agreed protected-power invariant: simulated omnibus and combined power must match analytic noncentral predictions across clustered/aligned cases.
- Replaced the post-hoc 0.006 frontier regression tolerance with a 675-cell standardized-residual regression against archived v1.3.3 protected-policy Monte Carlo powers.
- Added `joint_strategy_results_v1_3_3.csv` to make that regression self-contained.
- Documented that v1.4 protected attacks are level-only by design; spread/mixed attacks return when Σ is estimated or attackable.
- No substantive protected-frontier or attack-geometry model change from v1.4.0.
