#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a local Python venv and install dependencies.
# Usage:
#   scripts/bootstrap_venv.sh [dev|prod] [PYTHON_BIN]
# Examples:
#   scripts/bootstrap_venv.sh dev          # uses python3.12 if available, else python3
#   scripts/bootstrap_venv.sh prod python3 # explicit interpreter

MODE="${1:-dev}"
PY_BIN="${2:-}"

if [[ -z "${PY_BIN}" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    PY_BIN="python3.12"
  else
    PY_BIN="python3"
  fi
fi

echo "[bootstrap] Using Python: ${PY_BIN} ($(${PY_BIN} -V))"

VENV_DIR="venv"
if [[ -d "${VENV_DIR}" ]]; then
  echo "[bootstrap] Removing existing ${VENV_DIR}"
  rm -rf "${VENV_DIR}"
fi

${PY_BIN} -m venv "${VENV_DIR}"
# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

python -V
pip install -U pip

if [[ "${MODE}" == "dev" ]]; then
  echo "[bootstrap] Installing development dependencies"
  pip install -r requirements-dev.txt
else
  echo "[bootstrap] Installing production dependencies"
  pip install -r requirements.txt
fi

echo "[bootstrap] Writing lock files"
pip freeze > requirements.lock

if [[ "${MODE}" == "dev" ]]; then
  pip freeze > requirements-dev.lock
fi

echo "[bootstrap] Done. Activate with: source venv/bin/activate"

