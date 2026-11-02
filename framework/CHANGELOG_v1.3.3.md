# Changelog v1.3.3

- Unified signal grids across contaminated and uncontaminated attacks.
- Added default-utility contamination-cost sweep at reach costs 0, 0.005, 0.01, 0.02 per control; spread cost remains 2x reach cost.
- Added cost-free contamination willingness-to-pay by observer policy.
- Replaced the v1.3.2 “rare contamination” headline with a cost-sensitive interpretation.
- Retained the equal-means / exchangeability qualification explicitly.
- Reduced v1.3.3 Monte Carlo cells to 10,000 draws to accommodate the expanded symmetric attack grid.
- No .pyc or __pycache__ artifacts are packaged.
