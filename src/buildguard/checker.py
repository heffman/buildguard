from __future__ import annotations

import logging
import shutil
import tempfile
import time
from pathlib import Path

from buildguard.models import CheckResult
from buildguard.parsing import extract_error_tail, extract_failing_package_hint, extract_stream_tail
from buildguard.process import run_command
from buildguard.venvtools import create_virtual_environment, get_venv_executables

logger = logging.getLogger(__name__)


def run_check(
    requirements_path: str,
    python_executable: str,
    timeout_seconds: int,
    keep_venv: bool,
    upgrade_tools: bool,
) -> CheckResult:
    start_time = time.monotonic()
    requirements_file_path = Path(requirements_path)

    if not requirements_file_path.is_file():
        elapsed_seconds = round(time.monotonic() - start_time, 3)
        return CheckResult(
            requirements_path=str(requirements_file_path),
            python_executable=python_executable,
            venv_path='',
            status='fail',
            exit_code=2,
            tool_error=True,
            tool_error_message=f'ERROR: requirements file not found: {requirements_file_path}',
            pip_exit_code=None,
            elapsed_seconds=elapsed_seconds,
            failing_package_hint=None,
            error_tail=tuple(),
            stdout_tail=tuple(),
            stderr_tail=tuple(),
        )

    temp_directory = tempfile.mkdtemp(prefix='buildguard-')
    venv_path = Path(temp_directory)

    try:
        logger.info('creating virtual environment at %s', venv_path)
        create_virtual_environment(venv_path=venv_path, python_executable=python_executable)
        _, pip_executable = get_venv_executables(venv_path)

        if upgrade_tools:
            logger.info('upgrading pip, setuptools, and wheel')
            upgrade_result = run_command([
                str(pip_executable),
                'install',
                '--upgrade',
                'pip',
                'setuptools',
                'wheel',
            ])
            if upgrade_result.return_code != 0:
                elapsed_seconds = round(time.monotonic() - start_time, 3)
                tool_error_message = upgrade_result.stderr.strip() or upgrade_result.stdout.strip() or 'unknown error'
                return CheckResult(
                    requirements_path=str(requirements_file_path),
                    python_executable=python_executable,
                    venv_path=str(venv_path),
                    status='fail',
                    exit_code=2,
                    tool_error=True,
                    tool_error_message=f'failed to upgrade tools: {tool_error_message}',
                    pip_exit_code=None,
                    elapsed_seconds=elapsed_seconds,
                    failing_package_hint=None,
                    error_tail=tuple(),
                    stdout_tail=extract_stream_tail(upgrade_result.stdout),
                    stderr_tail=extract_stream_tail(upgrade_result.stderr),
                )

        logger.info('running pip install -r %s', requirements_file_path)
        pip_install_result = run_command(
            [str(pip_executable), 'install', '-r', str(requirements_file_path)],
            timeout_seconds=timeout_seconds,
        )

        elapsed_seconds = round(time.monotonic() - start_time, 3)
        if pip_install_result.timed_out:
            return CheckResult(
                requirements_path=str(requirements_file_path),
                python_executable=python_executable,
                venv_path=str(venv_path),
                status='fail',
                exit_code=2,
                tool_error=True,
                tool_error_message='pip install timed out',
                pip_exit_code=None,
                elapsed_seconds=elapsed_seconds,
                failing_package_hint=None,
                error_tail=extract_error_tail(pip_install_result.stdout, pip_install_result.stderr),
                stdout_tail=extract_stream_tail(pip_install_result.stdout),
                stderr_tail=extract_stream_tail(pip_install_result.stderr),
            )

        status = 'pass' if pip_install_result.return_code == 0 else 'fail'
        exit_code = 0 if status == 'pass' else 1

        combined_output_text = pip_install_result.stdout + '\n' + pip_install_result.stderr
        failing_package_hint = extract_failing_package_hint(combined_output_text)
        error_tail = extract_error_tail(pip_install_result.stdout, pip_install_result.stderr)

        return CheckResult(
            requirements_path=str(requirements_file_path),
            python_executable=python_executable,
            venv_path=str(venv_path),
            status=status,
            exit_code=exit_code,
            tool_error=False,
            tool_error_message=None,
            pip_exit_code=0 if status == 'pass' else pip_install_result.return_code,
            elapsed_seconds=elapsed_seconds,
            failing_package_hint=failing_package_hint,
            error_tail=error_tail,
            stdout_tail=extract_stream_tail(pip_install_result.stdout),
            stderr_tail=extract_stream_tail(pip_install_result.stderr),
        )

    except Exception as unexpected_error:
        elapsed_seconds = round(time.monotonic() - start_time, 3)
        return CheckResult(
            requirements_path=str(requirements_file_path),
            python_executable=python_executable,
            venv_path=str(venv_path),
            status='fail',
            exit_code=2,
            tool_error=True,
            tool_error_message=str(unexpected_error),
            pip_exit_code=None,
            elapsed_seconds=elapsed_seconds,
            failing_package_hint=None,
            error_tail=tuple(),
            stdout_tail=tuple(),
            stderr_tail=tuple(),
        )
    finally:
        if not keep_venv and venv_path.exists():
            shutil.rmtree(venv_path, ignore_errors=True)
