# v1.3.0 — changes relative to v1.2.0

- Removed all compiled Python files (`*.pyc` and `__pycache__`) from the package and regenerated SHA-256 manifest.
- Restored hider choice of signal magnitude `s`, including ceasing activity, instead of fixing it to 20.
- Added control-mean shifts, balanced spread injection, and mixed shift-and-spread attacks under a hard control-reach budget.
- Added honest simultaneous-control observation policies using empirical standard deviation, empirically calibrated MAD, protected externally specified scale, and physics-only counting variance.
- Excluded policies failing a predeclared null false-alarm tolerance from equilibrium optimization; retains them in sensitivity output for diagnostics.
- Switched to synthetic follower/leader utilities that distinguish hider benefit, detection risk, attack cost, missed active-signal harm, false alarms, and measurement cost.
- Reproduced the two-control balanced-spread prediction-interval attack independently under its own fixed-observation sampling frame.
- Added a restricted identifiability proposition and corrected the overstatement that no pre-contact baseline implies only physics-calculated calibration can identify a signal.
- Kept v1.0/v1.1/v1.2 source and notes as historical artifacts, without stale bytecode.

**Caution:** Synthetic equilibria are illustrative; no observations of nonhuman beings or their technologies are used.
