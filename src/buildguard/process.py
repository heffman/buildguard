from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Sequence

from buildguard.models import CommandResult


def _normalize_output(maybe_bytes: object) -> str:
    if maybe_bytes is None:
        return ''
    if isinstance(maybe_bytes, bytes):
        return maybe_bytes.decode(errors='replace')
    if isinstance(maybe_bytes, str):
        return maybe_bytes
    return str(maybe_bytes)


def run_command(
    args: Sequence[str],
    timeout_seconds: Optional[int] = None,
    cwd: Optional[Path] = None,
) -> CommandResult:
    try:
        completed_process = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            errors='replace',
            timeout=timeout_seconds,
            cwd=str(cwd) if cwd is not None else None,
            check=False,
        )
        return CommandResult(
            args=tuple(str(argument) for argument in args),
            return_code=completed_process.returncode,
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as timeout_error:
        return CommandResult(
            args=tuple(str(argument) for argument in args),
            return_code=-1,
            stdout=_normalize_output(timeout_error.stdout),
            stderr=_normalize_output(timeout_error.stderr),
            timed_out=True,
        )
