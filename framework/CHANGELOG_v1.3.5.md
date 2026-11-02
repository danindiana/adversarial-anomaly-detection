# Changelog — v1.3.5

- Added `verify_reporting_v1_3_4.py`, closing the reproducibility gap in v1.3.4.
- Canonicalized the packaged v1.3.4 reporting CSVs to the deterministic postprocessor output.
- Added `verify_models_v1_3_5.py` and `mixed_policy_frontier_v1_3_5.csv`.
- Replaced interpretation of the pure-policy frontier with an exact mixed-commitment LP frontier.
- Added explicit expected-control budgets K = 4, 6, 8 and reported expected measurement effort.
- Confirmed the zero-WTP mixed commitments improve the pure omnibus endpoint for tau = 0, 3, 10.
- No Monte Carlo model changes relative to v1.3.3; v1.3.5 operates on the already verified payoff table.
