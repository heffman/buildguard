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
    failing_package_hint_is_best_effort: bool
    failure_category: Optional[str]
    failure_detail: Optional[str]
    suggested_fixes: Tuple[str, ...]
    available_versions: Tuple[str, ...]
    available_versions_more_count: int
    available_versions_query_error: Optional[str]
    error_tail: Tuple[str, ...]
    stdout_tail: Tuple[str, ...]
    stderr_tail: Tuple[str, ...]
