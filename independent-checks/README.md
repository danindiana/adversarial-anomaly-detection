# Independent checks

Short scripts Claude used to re-run and probe each release independently of the packaged verifiers. They are reviewer probes, not part of the packaged pipelines; each one produced a specific correction or confirmation recorded in the main README and git history.

| Script | Checks | Run from the repo root |
|---|---|---|
| `recheck_v1_0.py` | Recomputes every v1.0 Bayes factor, secrecy probability and intervention probability from scratch. | `python independent-checks/recheck_v1_0.py` |
| `spread_injection_attack.py` | Shows that estimating heterogeneity from the controls lets a hider erase detection by injecting ±δ spread. | `python independent-checks/spread_injection_attack.py` |
| `omnibus_vs_directional_v1_3.py` | Re-simulates the v1.3.0 equilibrium attacks against an omnibus equality test; motivated v1.3.1. | `python independent-checks/omnibus_vs_directional_v1_3.py` |
| `signal_grid_floor_v1_3_1.py` | Shows the v1.3.1 equilibrium signal sat on the grid floor; motivated the v1.3.2 fine grid. | `python independent-checks/signal_grid_floor_v1_3_1.py` |
| `mixed_frontier_probe_v1_3_4.py` | Two-policy mixtures beat the pure-policy frontier; motivated the v1.3.5 LP. | `python independent-checks/mixed_frontier_probe_v1_3_4.py framework/joint_strategy_results_v1_3_3.csv` |
| `clustered_noncentrality.py` | Known-Σ omnibus noncentrality for aligned vs misaligned attacks under clustered covariance. | `python independent-checks/clustered_noncentrality.py` |
| `protected_checks_v1_4_0.py` | Cell-level regression of the analytic benchmark against v1.3.3 Monte Carlo, plus simulated size and power under clustered Σ. | `python independent-checks/protected_checks_v1_4_0.py covariance framework/joint_strategy_results_v1_3_3.csv` |
| `crn_seed_offsets_v1_4_0.py` | Shows the v1.3.3 regression offset is a common-random-numbers seed effect. Needs v1.3.3 outputs regenerated under other seeds (change `SEED` in `framework/verify_models_v1_3_3.py`). | `python independent-checks/crn_seed_offsets_v1_4_0.py covariance <csv> [<csv> ...]` |

The two `v1_4_0` scripts import `verify_protected_v1_4_0.py`, which ships in `covariance/` at tags v1.4.0–v1.4.2 (`git checkout v1.4.0 -- covariance` if it is missing).
