from __future__ import annotations

import json
from typing import Any, Dict

from buildguard import __version__
from buildguard.models import CheckResult


def _format_elapsed_seconds(elapsed_seconds: float) -> str:
    return f'{elapsed_seconds:.1f}'


def format_text_report(result: CheckResult) -> str:
    lines = [
        f'buildguard check: {result.requirements_path}',
        f'python: {result.python_executable}',
        f'venv: {result.venv_path}',
        '',
    ]

    if result.status == 'pass':
        lines.extend([
            'PASS',
            '',
            'requirements installed successfully in a clean environment',
            '',
            'summary:',
            f'elapsed_seconds={_format_elapsed_seconds(result.elapsed_seconds)}',
            f'pip_exit_code={result.pip_exit_code}',
        ])
        return '\n'.join(lines)

    lines.extend(['FAIL', ''])

    if result.tool_error:
        lines.append('buildguard encountered a fatal tool/runtime error')
        lines.append('')
        if result.tool_error_message:
            lines.append(result.tool_error_message)
            lines.append('')
    else:
        pip_exit_code = result.pip_exit_code if result.pip_exit_code is not None else -1
        lines.append(f'pip install -r {result.requirements_path} exited with code {pip_exit_code}')
        lines.append('')
        if result.failing_package_hint:
            lines.append('likely failing dependency:')
            lines.append(result.failing_package_hint)
            lines.append('')
        if result.error_tail:
            lines.append('pip error summary:')
            for line in result.error_tail:
                lines.append(line)
            lines.append('')

    lines.extend([
        'summary:',
        f'elapsed_seconds={_format_elapsed_seconds(result.elapsed_seconds)}',
        f'pip_exit_code={result.pip_exit_code}',
    ])
    return '\n'.join(lines)


def format_json_report(result: CheckResult) -> str:
    payload: Dict[str, Any] = {
        'tool': 'buildguard',
        'version': __version__,
        'command': 'check',
        'requirements_path': result.requirements_path,
        'python_executable': result.python_executable,
        'status': result.status,
        'exit_code': result.exit_code,
        'elapsed_seconds': round(result.elapsed_seconds, 3),
        'venv_path': result.venv_path,
        'pip_exit_code': result.pip_exit_code,
        'failing_package_hint': result.failing_package_hint,
        'error_tail': list(result.error_tail),
        'stdout_tail': list(result.stdout_tail),
        'stderr_tail': list(result.stderr_tail),
        'tool_error': result.tool_error,
    }
    if result.tool_error and result.tool_error_message:
        payload['tool_error_message'] = result.tool_error_message
    return json.dumps(payload, indent=2)
