from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class CommandResult:
    args: Tuple[str, ...]
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool


@dataclass(frozen=True)
class CheckResult:
    requirements_path: str
    python_executable: str
    venv_path: str
    status: str
    exit_code: int
    tool_error: bool
    tool_error_message: Optional[str]
    pip_exit_code: Optional[int]
    elapsed_seconds: float
    failing_package_hint: Optional[str]
    error_tail: Tuple[str, ...]
    stdout_tail: Tuple[str, ...]
    stderr_tail: Tuple[str, ...]
