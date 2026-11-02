# Persistent Nonhuman Cohabitation — v1.1.0

A **hypothetical** model-comparison research package, not evidence of nonhuman presence.

## Contents

- `Cohabitation_Adversarial_Detection_v1.1.0.md`: consolidated research note, including new v1.1 sections.
- `CHANGELOG_v1.1.0.md`: new derivations, model assumptions, and results.
- `verify_models.py`: unchanged v1.0 deterministic reproduction.
- `verify_models_v1_1.py`: v1.1 closed forms, cost sensitivity, and toy Stackelberg game.
- `results.json`, `adversarial_results.csv`: unchanged baseline outputs.
- `results_v1_1.json`, `cost_sensitivity.csv`, `stackelberg_results.csv`: v1.1 outputs.
- `requirements.txt`: NumPy and SciPy dependencies.

## Reproduction

```bash
python -m pip install -r requirements.txt
python verify_models.py --output-dir .
python verify_models_v1_1.py --output-dir .
```

All assumptions and observations are illustrative, not empirical observations of extraterrestrial residents. The reference selection is assumed private from the adversary until its action is committed, and the adversary can fully contaminate only one of the two controls.
