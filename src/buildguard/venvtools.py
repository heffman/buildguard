from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

from buildguard.process import run_command


def create_virtual_environment(venv_path: Path, python_executable: str) -> None:
    command_result = run_command([python_executable, '-m', 'venv', str(venv_path)])
    if command_result.return_code != 0:
        message = command_result.stderr.strip() or command_result.stdout.strip() or 'unknown error'
        raise RuntimeError(f'failed to create virtual environment: {message}')


def get_venv_executables(venv_path: Path) -> Tuple[Path, Path]:
    if os.name == 'nt':
        scripts_directory = venv_path / 'Scripts'
        python_path = scripts_directory / 'python.exe'
        pip_path = scripts_directory / 'pip.exe'
    else:
        bin_directory = venv_path / 'bin'
        python_path = bin_directory / 'python'
        pip_path = bin_directory / 'pip'
    return python_path, pip_path
