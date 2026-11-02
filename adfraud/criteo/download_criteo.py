#!/usr/bin/env python3
"""Download Criteo Uplift v2.1 without committing raw data.

Official publisher page:
  https://ailab.criteo.com/criteo-uplift-prediction-dataset/
Mirror used here:
  https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz
Expected SHA256 (Hugging Face file metadata):
  2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc

The dataset is CC BY-NC-SA 4.0. This script downloads it locally; the raw file is
not redistributed by this repository.
"""
from __future__ import annotations
import argparse, hashlib, sys, urllib.request
from pathlib import Path

URL = "https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz"
SHA256 = "2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/criteo-research-uplift-v2.1.csv.gz")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        got = sha256(out)
        if got == SHA256:
            print(f"OK: {out} already exists and SHA256 matches")
            return 0
        raise SystemExit(f"Existing file checksum mismatch: {got}")

    print(f"Downloading {URL}\n -> {out}")
    req = urllib.request.Request(URL, headers={"User-Agent": "adversarial-anomaly-detection/1.0"})
    with urllib.request.urlopen(req) as r, out.open("wb") as f:
        total = int(r.headers.get("Content-Length", "0") or 0)
        done = 0
        while True:
            chunk = r.read(8 << 20)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r{done/total:6.1%}", end="", flush=True)
    print()
    got = sha256(out)
    if got != SHA256:
        out.unlink(missing_ok=True)
        raise SystemExit(f"SHA256 mismatch: expected {SHA256}, got {got}")
    print(f"OK SHA256 {got}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
