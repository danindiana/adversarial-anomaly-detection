#!/usr/bin/env bash
# Adversarial Anomaly Detection: one-shot setup and verification.
#
#   curl -fsSL https://raw.githubusercontent.com/danindiana/adversarial-anomaly-detection/main/setup.sh | bash
#
# Target: Ubuntu 24.04 LTS (works on any Linux with git and Python >= 3.11).
# Steps: check prerequisites -> clone or update the repo -> create .venv ->
# install pinned-minimum dependencies -> rerun the verifiers -> compare every
# regenerated table with the committed one, byte for byte.
#
# Environment options:
#   AAD_DIR=/path        where to clone (default: ~/adversarial-anomaly-detection)
#   AAD_PYTHON=python3.12  interpreter to build the venv with (default: python3)
#   AAD_FULL=1           also rerun the v1.3.3 Monte Carlo game (~1 min)
#   AAD_SKIP_APT=1       never call apt-get; just report what is missing
#   AAD_SKIP_VERIFY=1    install only, skip the verifiers
#
# Example: curl -fsSL .../setup.sh | AAD_FULL=1 bash

set -euo pipefail

REPO_URL="https://github.com/danindiana/adversarial-anomaly-detection"
PY="${AAD_PYTHON:-python3}"

if [ -t 1 ]; then B=$'\e[1m'; G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; N=$'\e[0m'; else B=""; G=""; Y=""; R=""; N=""; fi
say()  { printf '%s==>%s %s\n' "$B" "$N" "$*"; }
ok()   { printf '  %s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '  %s!%s %s\n' "$Y" "$N" "$*"; }
die()  { printf '  %s✗%s %s\n' "$R" "$N" "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
say "Checking the system"
if [ -r /etc/os-release ]; then
  . /etc/os-release
  if [ "${ID:-}" = "ubuntu" ] && [[ "${VERSION_ID:-}" == 24.04* ]]; then
    ok "Ubuntu ${VERSION_ID}"
  else
    warn "${PRETTY_NAME:-unknown OS}: tested on Ubuntu 24.04 LTS, continuing anyway"
  fi
fi

need_pkgs=()
command -v git >/dev/null 2>&1 || need_pkgs+=(git)
command -v "$PY" >/dev/null 2>&1 || need_pkgs+=(python3)
if command -v "$PY" >/dev/null 2>&1 && ! "$PY" -c 'import ensurepip, venv' >/dev/null 2>&1; then
  need_pkgs+=(python3-venv)
fi

if [ ${#need_pkgs[@]} -gt 0 ]; then
  if [ "${AAD_SKIP_APT:-0}" != "1" ] && command -v apt-get >/dev/null 2>&1; then
    warn "Installing missing packages with apt-get: ${need_pkgs[*]}"
    SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq "${need_pkgs[@]}"
  else
    die "Missing: ${need_pkgs[*]}. Install them (sudo apt install ${need_pkgs[*]}) and rerun."
  fi
fi
ok "git $(git --version | awk '{print $3}')"

"$PY" - <<'EOF' || die "Python >= 3.11 required (set AAD_PYTHON to another interpreter)"
import sys
sys.exit(0 if sys.version_info >= (3, 11) else 1)
EOF
ok "$("$PY" --version)"

# ---------------------------------------------------------------------------
say "Getting the repository"
SELF_DIR=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
if [ -n "$SELF_DIR" ] && [ -d "$SELF_DIR/framework" ] && [ -d "$SELF_DIR/covariance" ]; then
  DIR="$SELF_DIR"
  ok "Using this checkout: $DIR"
else
  DIR="${AAD_DIR:-$HOME/adversarial-anomaly-detection}"
  if [ -d "$DIR/.git" ]; then
    git -C "$DIR" pull --ff-only --quiet && ok "Updated $DIR"
  elif [ -e "$DIR" ]; then
    die "$DIR exists and is not a git checkout; set AAD_DIR to another path"
  else
    git clone --quiet "$REPO_URL" "$DIR" && ok "Cloned into $DIR"
  fi
fi
cd "$DIR"

# ---------------------------------------------------------------------------
say "Building the Python environment (.venv)"
[ -d .venv ] || "$PY" -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r framework/requirements.txt -r covariance/requirements.txt
ok "$(python -c 'import numpy, scipy, pandas; print(f"numpy {numpy.__version__}, scipy {scipy.__version__}, pandas {pandas.__version__}")')"

if [ "${AAD_SKIP_VERIFY:-0}" = "1" ]; then
  say "Done (verification skipped)."
  echo "  cd $DIR && source .venv/bin/activate"
  exit 0
fi

# ---------------------------------------------------------------------------
fails=0
compare() {  # compare <dir>: every regenerated out/*.csv against the committed copy
  local d="$1" f b
  for f in "$d"/out/*.csv; do
    b="$(basename "$f")"
    [ -f "$d/$b" ] || continue
    if cmp -s "$f" "$d/$b"; then ok "$d/$b"; else warn "$d/$b differs"; fails=$((fails+1)); fi
  done
}

say "Verifying the protected-covariance benchmark (v1.4.2)"
( cd covariance && rm -rf out && python verify_protected_v1_4_2.py \
    --archive-frontier mixed_policy_frontier_v1_3_5.csv \
    --archive-cells joint_strategy_results_v1_3_3.csv \
    --output-dir out >/dev/null )
compare covariance

say "Verifying the core framework (v1.3.4 reporting, v1.3.5 mixed frontier)"
( cd framework && rm -rf out
  if [ "${AAD_FULL:-0}" = "1" ]; then
    echo "  running the v1.3.3 Monte Carlo game (about a minute)..."
    python verify_models_v1_3_3.py --output-dir out >/dev/null
  fi
  python verify_reporting_v1_3_4.py --input joint_strategy_results_v1_3_3.csv --output-dir out >/dev/null
  python verify_models_v1_3_5.py --input joint_strategy_results_v1_3_3.csv --output-dir out >/dev/null )
compare framework

say "Verifying the advertising case study (adfraud)"
( cd adfraud && rm -rf out && python adfraud_case_study.py --output-dir out --no-figures >/dev/null )
compare adfraud

echo
if [ "$fails" -eq 0 ]; then
  say "${G}All regenerated tables match the committed ones byte for byte.${N}"
else
  say "${Y}${fails} table(s) differ.${N} Library versions can shift low-order digits; see the README."
fi
cat <<EOF

  Next:
    cd $DIR
    source .venv/bin/activate
    less README.md

EOF
