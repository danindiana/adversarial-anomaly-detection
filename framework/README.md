# Adversarial Detection Research — v1.3.1

Synthetic mathematical and statistical methods motivated by a philosophical hypothetical. **Not evidence for extraterrestrial activity or any concealed population.**

## Current files
- `Cohabitation_Adversarial_Detection_v1.3.1.md`: consolidated note, model definitions, implications and limitations
- `verify_models_v1_3_1.py`: v1.3.1 synthetic experiments and Stackelberg equilibrium calculations
- `joint_strategy_results_v1_3_1.csv`: 24 observer policies x 45 attack actions per tau
- `stackelberg_joint_equilibria_v1_3_1.csv`: three re-solved equilibrium rows
- `spread_benchmark_v1_3_1.csv`: balanced spread attack comparison
- `results_v1_3_1.json`: parameters and summary
- `legacy/`: archived earlier notes, scripts and outputs, without compiled bytecode
- `SHA256SUMS.txt`: manifest of archive files except itself

## Run

```bash
python -m pip install -r requirements.txt
python -B verify_models_v1_3_1.py --output-dir .
sha256sum -c SHA256SUMS.txt
```

The check of SHA256SUMS requires the original outputs to remain byte-identical. Versions of NumPy/SciPy may affect final digits. A no-bytecode run is recommended.

The game has finite attack/defense strategy grids, synthetic utilities, independent Gaussian channels, and oracle-like protected scale calibration. It does not establish actual populations or motive.
