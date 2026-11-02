# v1.3.5 reproducibility

Run from this directory:

```bash
python verify_reporting_v1_3_4.py --input joint_strategy_results_v1_3_3.csv --output-dir .
python verify_models_v1_3_5.py --input joint_strategy_results_v1_3_3.csv --output-dir .
sha256sum -c SHA256SUMS.txt
```

The first command regenerates the v1.3.4 reporting tables. The second generates the exact mixed-policy frontier for v1.3.5. No Monte Carlo simulation is required for either command.

Primary v1.3.5 files:

- `Reach_Limited_Contamination_ON_OFF_v1.3.5.md`
- `verify_reporting_v1_3_4.py`
- `verify_models_v1_3_5.py`
- `mixed_policy_frontier_v1_3_5.csv`
- `CHANGELOG_v1.3.5.md`
