# Nonhuman Cohabitation / Adversarial Detection Research — v1.2.0

This is an abstract, synthetic statistical-methods experiment motivated by a *hypothetical* population; it is **not** observational evidence of nonhuman residence.

## Run

```bash
python -m pip install -r requirements.txt
python verify_models_v1_2.py --output-dir .
```

The script writes four reproducible outputs and checks the analytical coverage identities, exact profile-Poisson KL comparisons, heterogeneity-calibration failure, and resource-game equilibrium constraints. The historical v1.0 and v1.1 scripts and notes remain in `legacy/` as frozen references, without the previous 250 KB strategy grid.

The main note is `Cohabitation_Adversarial_Detection_v1.2.0.md`. The game optimizes an **omnibus miss probability**, not expected KL; a separate contrast likelihood ratio illustrates how an incorrectly restricted alternative creates confident false reassurance.

The default leader/follower game assumes eight exchangeable controls, a hider with a hard reach budget of four, uniformly private selection of observed controls, persistent independent normal between-control offsets, and a cost of 0.002 in incentive units to enforce strict follower response. All numerical costs and population/attack variables are model inputs and must not be mistaken for real-world calibrations.
