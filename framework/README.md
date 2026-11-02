# Adversarial Detection Research — v1.3.0

An abstract mathematical and statistical model inspired by a hypothetical concealed presence. **Not evidence for a concealed population or extraterrestrial activity.**

## Contents
- `Cohabitation_Adversarial_Detection_v1.3.0.md`: consolidated note, equations, results, and limitations
- `verify_models_v1_3.py`: reproducible Gaussian simulation, 45-action follower, and 12-policy defender game
- `joint_strategy_results.csv`: full sensitivity matrix (scenario, measurement policy, attack)
- `stackelberg_joint_equilibria.csv`: one equilibrium per heterogeneity scenario
- `spread_benchmark.csv`: direct replication of spread-inflation t-test (200,000 draws)
- `results_v1_3.json`: synthetic numerical constants and output summary
- `legacy/`: previous scripts and notes for comparison, no bytecode
- `SHA256SUMS.txt`: SHA-256 manifest for the packaged files, excluding itself

## Run

```bash
python -m pip install -r requirements.txt
python -B verify_models_v1_3.py --output-dir .
sha256sum -c SHA256SUMS.txt
```

Use `python -B` to suppress `.pyc` generation. Numerical calculations should reproduce with the specified NumPy/SciPy versions; some last digits may vary under other environments.

Important: the benchmark fixes two *observed* controls as contaminated; the joint game randomizes selection of `k` from `m=8` controls after the hider acts. These represent different designs and must not be conflated.
