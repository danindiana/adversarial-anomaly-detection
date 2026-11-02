# Version 1.1.0 — changes from 1.0.0

- Derived and verified `s*=clip(sqrt(kappa*V))` and interior `KL*=kappa/2` under a quadratic KL approximation and logarithmic operating cost.
- Reframed background calibration: it constrains the activity footprint but need not improve optimized distinguishability under that specific cost.
- Added a power-law concealment-cost family with a different optimized-KL dependence on background variance.
- Proved ON-only nonidentifiability for an unknown constant background and signal; added matched ON/OFF structure and contamination caveats.
- Implemented a two-reference-control Stackelberg toy game with a private randomized control selection and one-control attacker budget.
- Identified limits of that game: matched backgrounds, unavailable realized assignments, inability to spoof both controls, and binary attack choices.
- Preserved `verify_models.py` and its v1.0 outputs unchanged. New tests and CSVs are in `verify_models_v1_1.py`.
- All numerical inputs remain synthetic; there is no empirical validation of the four premises.
