# v1.4.1 protected-covariance benchmark

Run:

```bash
python verify_protected_v1_4_1.py \
  --archive-cells joint_strategy_results_v1_3_3.csv \
  --archive-frontier mixed_policy_frontier_v1_3_5.csv \
  --output-dir .
```

The v1.3.5 frontier remains packaged as historical context. The v1.4.1 regression invariant operates at the 675 Monte Carlo power cells where v1.3 sampling noise entered, rather than imposing a post-hoc tolerance on the downstream frontier.

See `PROTECTED_BENCHMARK_v1.4.1.md` for scope, invariants, and the deliberate omission of spread/mixed attacks from the protected stage.
