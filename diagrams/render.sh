#!/usr/bin/env bash
# Re-render every diagram in this folder to PNG (160 dpi) and SVG.
# Needs Graphviz: sudo apt install -y graphviz
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
fail=0
for f in *.dot; do
  b="${f%.dot}"
  if dot -Tpng -Gdpi=160 "$f" -o "$b.png" && dot -Tsvg "$f" -o "$b.svg"; then
    echo "rendered $b"
  else
    echo "FAILED  $f" >&2; fail=1
  fi
done
exit "$fail"
