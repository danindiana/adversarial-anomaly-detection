# Reach-Limited Contamination in ON/OFF Detection — v1.4.0 protected benchmark

This is the first v1.4 deliverable. It contains only the **protected covariance** regime: the observer knows the true covariance matrix `Sigma`.

The omnibus statistic is the Mahalanobis quadratic form in ON-minus-control contrasts. Its alternative distribution is noncentral chi-square with `lambda = z^T Omega^-1 z`. Directional power is Gaussian. The Bonferroni combined test is evaluated deterministically by decomposing the whitened contrast into the directional coordinate and an independent residual quadratic component.

The hider chooses level-attack placement endogenously. Cluster-symmetric placements are represented by occupancy classes rather than redundant labeled subsets.

Run:

```bash
python verify_protected_v1_4_0.py --archive mixed_policy_frontier_v1_3_5.csv --output-dir out
```

Outputs:
- `protected_frontier_anchor_v1_4_0.csv`
- `protected_attack_geometry_v1_4_0.csv`
- `protected_invariants_v1_4_0.csv`

Important regression note: v1.3.5 is Monte Carlo. The exact analytic v1.4 benchmark therefore cannot reproduce its sampled frontier byte-for-byte. The exact invariant is the model reduction `rho=0,c=1 => Sigma=(v+tau^2)I`; the archived frontier is checked with a declared numerical tolerance of 0.006 in plain-activity utility. The observed maximum difference is about 0.00548.
