# Buildguard

**Stop broken Python dependencies from wasting your CI runs.**

Your CI passes.  
You merge.  
Next build fails — or worse, production breaks.

Same `requirements.txt`. Different result.

Buildguard detects when your dependency install will fail **before CI burns time on it**.

---

## What it catches

Buildguard runs a clean install of your pinned dependencies and surfaces real failure modes:

- Missing distributions (package/version no longer available)
- Python version incompatibilities
- Broken or inconsistent upstream releases
- Yanked or partially published packages

---

## Example

```bash
$ buildguard check requirements.txt

❌ INSTALL FAILURE DETECTED

Package: uvloop==0.17.0  
Error: No matching distribution found

This will fail your CI build.

Suggested fix:
- Check available versions
- Update or remove the pinned version
```

## Why this matters

Dependency failures are non-obvious and expensive:
- CI fails after minutes of runtime
- Failures appear “random” across environments
- Issues originate upstream — not in your code

Buildguard turns this into a fast preflight check.

## Install
```bash
pip install buildguard
```

## Usage
```bash
buildguard check requirements.txt
```

Optional flags:
```bash
--json                    # machine-readable output
--show-available-versions # show valid versions if install fails
--python-version 3.11     # simulate a specific Python version
```

## Use in CI (recommended)

Run Buildguard before your main install step:

```bash
buildguard check requirements.txt
```

Fail fast. Save time.

## GitHub Actions example (PyPI install)
```YAML
name: Buildguard Check

on:
  pull_request:
  push:

jobs:
  buildguard:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Buildguard
        run: python -m pip install --upgrade pip buildguard

      - name: Run Buildguard
        run: buildguard check requirements.txt
```

## JSON output (for automation)
```bash
buildguard check requirements.txt --json
```

Example:
```JSON
{
  "status": "fail",
  "failure_category": "missing_distribution",
  "failing_package_hint": "uvloop==0.17.0",
  "suggested_fixes": [
    "Check available versions",
    "Update pinned version"
  ]
}
```

## License

Free for personal use.

Commercial use requires a license:
👉 https://heffman.gumroad.com/l/buildguard


## Why Buildguard exists

This problem shows up everywhere:

> “CI worked yesterday. Today it fails. Nothing changed.”

It’s almost always dependency resolution or upstream state.

Buildguard isolates that failure before it costs you time.