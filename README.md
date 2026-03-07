# buildguard

Catch upstream Python dependency breakage before it surprises your CI build.

`buildguard` is a deterministic CLI that creates a clean virtual environment, attempts to install your pinned dependency set, and fails early when upstream package ecosystem drift breaks installation.

It is intended as a preflight install check for CI.

Common upstream drift this catches includes:

- versions disappearing
- wheels removed from package indexes
- build backend behavior changes
- dependency resolution breakage
- incompatible metadata changes
- missing distributions for a Python version or platform

`buildguard` is not:

- a vulnerability scanner
- a dependency resolver
- a lockfile manager
- a license scanner

## Quick Start

```bash
buildguard check requirements.txt
buildguard check requirements.txt --json
buildguard check requirements.txt --timeout 300
```

## What It Checks

`buildguard check` verifies that dependencies from a requirements file still install in a clean environment, even when your repository code has not changed.

## Example Output

Success:

```text
buildguard check: requirements.txt
python: python3.11
venv: /tmp/buildguard-abc123

PASS

requirements installed successfully in a clean environment

summary:
elapsed_seconds=18.4
pip_exit_code=0
```

Failure:

```text
buildguard check: requirements.txt
python: python3.11
venv: /tmp/buildguard-abc123

FAIL

pip install -r requirements.txt exited with code 1

likely failing dependency:
uvloop==0.17.0

pip error summary:
Failed building wheel for uvloop
error: subprocess-exited-with-error

summary:
elapsed_seconds=22.7
pip_exit_code=1
```

## Exit Codes

- `0`: success
- `1`: install failure
- `2`: fatal tool/runtime/config error

## Why This Exists

Upstream dependency ecosystem changes can break installs unexpectedly and waste CI time. `buildguard` makes dependency installation a deliberate, fail-fast preflight step.

## Support Scope

`buildguard` v1 is intentionally small and practical. It focuses on deterministic preflight install checks for one requirements file.
