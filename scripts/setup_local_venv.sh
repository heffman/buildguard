#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${1:-python3}"
VENV_DIR="${2:-.venv}"

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel
"${VENV_DIR}/bin/python" -m pip install -e . --no-build-isolation

cat <<MSG
Local virtual environment is ready.

Run commands with:
  ${VENV_DIR}/bin/buildguard check examples/requirements-good.txt
  ${VENV_DIR}/bin/buildguard check examples/requirements-bad.txt
  ${VENV_DIR}/bin/python -m buildguard check examples/requirements-good.txt --json
  ${VENV_DIR}/bin/python scripts/smoke_test_check_success.py
  ${VENV_DIR}/bin/python scripts/smoke_test_check_failure.py
  ${VENV_DIR}/bin/python scripts/smoke_test_missing_distribution.py
MSG
