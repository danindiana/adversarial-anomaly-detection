#!/usr/bin/env python3
"""End-to-end test of the Criteo pipeline on synthetic data with a known answer.

Generates a file with the Criteo v2.1 schema in which exposure raises conversion by
exactly 3 percentage points, runs analyze_criteo_attribution.py on it, and checks that
the pipeline recovers that effect within its own 95% bootstrap interval. Takes about
25 seconds. It tests the code, not any claim about real advertising.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "smoke_out"
TRUE_LATE = 0.03


def main() -> int:
    OUT.mkdir(exist_ok=True)
    data = OUT / "synthetic.csv.gz"
    subprocess.run([sys.executable, str(HERE / "make_synthetic_criteo.py"), str(data), "600000"], check=True)
    subprocess.run([sys.executable, str(HERE / "analyze_criteo_attribution.py"), str(data),
                    "--outdir", str(OUT / "figures"), "--results", str(OUT / "results.csv"),
                    "--summary", str(OUT / "summary.json"), "--bins", "10", "--model-sample", "200000",
                    "--bootstrap", "40", "--no-figures"], check=True, stdout=subprocess.DEVNULL)
    s = json.loads((OUT / "summary.json").read_text())
    late, se = s["global"]["conv_late_wald"], s["global_se"]["conv_late_wald"]
    print(f"recovered LATE {late:.4f} ± {1.96 * se:.4f} (truth {TRUE_LATE})")
    assert abs(late - TRUE_LATE) <= 1.96 * se, "pipeline failed to recover the known effect"
    assert s["strong_bins"] >= 5, "too few bins passed the first-stage threshold"
    print("Criteo pipeline smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
