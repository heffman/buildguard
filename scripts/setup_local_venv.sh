#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${1:-python3}"
VENV_DIR="${2:-.venv}"

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel
"${VENV_DIR}/bin/python" -m pip install -e . --no-build-isolation

cat <<MSG
Local virtual environment is ready.

Activate the environment first:
  source ${VENV_DIR}/bin/activate

Then run commands with:
  buildguard check examples/requirements-good.txt
  buildguard check examples/requirements-bad.txt
  buildguard check examples/requirements-good.txt --json
  python scripts/smoke_test_check_success.py
  python scripts/smoke_test_check_failure.py
  python scripts/smoke_test_missing_distribution.py
MSG
