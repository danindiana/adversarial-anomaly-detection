#!/usr/bin/env python3
"""Synthetic stand-in with the Criteo Uplift v2.1 schema, for testing the pipeline only.

Known truth: exposure raises conversion by TRUE_LATE for every exposed user; exposure
happens only under treatment and is selected on features that also raise baseline
conversion, so the naive exposed-vs-unexposed contrast is biased upward.
"""
import sys
import numpy as np
import pandas as pd

TRUE_LATE = 0.03
n = int(sys.argv[2]) if len(sys.argv) > 2 else 600_000
rng = np.random.default_rng(7)
cont = rng.standard_normal((n, 4))
cat = rng.integers(0, [60, 552, 260, 132, 1645, 3743, 1594, 136], size=(n, 8)).astype(float)
X = np.empty((n, 12))
X[:, [0, 2, 7, 10]] = cont
X[:, [1, 3, 4, 5, 6, 8, 9, 11]] = cat
z = (rng.random(n) < 0.85).astype(int)
intent = 0.8 * cont[:, 0] + 0.5 * cont[:, 1] + 0.3 * rng.standard_normal(n)
p_expose = 1 / (1 + np.exp(-(-3.6 + 1.2 * intent)))
a = z * (rng.random(n) < p_expose)
p_base = 1 / (1 + np.exp(-(-6.4 + 0.9 * intent)))
y = (rng.random(n) < np.clip(p_base + TRUE_LATE * a, 0, 1)).astype(int)
v = (rng.random(n) < np.clip(10 * p_base + 0.2 * a, 0, 1)).astype(int)
df = pd.DataFrame(X, columns=[f"f{i}" for i in range(12)])
df["treatment"], df["conversion"], df["visit"], df["exposure"] = z, y, v, a
df.to_csv(sys.argv[1], index=False, compression="gzip")
print(f"rows={n} exposure|Z=1={a[z==1].mean():.4f} conv C={y[z==0].mean():.5f} T={y[z==1].mean():.5f}")
