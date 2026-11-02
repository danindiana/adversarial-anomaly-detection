# Changelog v1.3.4

Closing maintenance patch for the v1.3 series.

- No change to the underlying Monte Carlo game or verified v1.3.3 statistical outputs.
- Added a symmetric interpretation layer to `contamination_wtp`: `size_valid`, grid-ceiling flag, and interpretation text.
- Marked empirical-SD WTP values whose best contaminated strategy hits `s=30` as lower bounds.
- Marked positive-tau physics-only policies size-invalid and excluded them from design comparison.
- Added `robustness_efficiency_frontier_v1_3_4.csv`, the Pareto frontier between best uncontaminated hider utility and contamination WTP over size-valid pure observer policies.
- Updated the closing claim to state the efficiency–robustness tradeoff explicitly.
