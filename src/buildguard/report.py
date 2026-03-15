from __future__ import annotations

import json
from typing import Any, Dict

from buildguard import __version__
from buildguard.licensing import LICENSE_NOTICE, should_show_license_notice
from buildguard.models import CheckResult


def _format_elapsed_seconds(elapsed_seconds: float) -> str:
    return f'{elapsed_seconds:.1f}'


def _append_license_notice(lines: list[str]) -> None:
    if not should_show_license_notice():
        return
    lines.extend([
        '',
        LICENSE_NOTICE,
    ])


def format_text_report(
    result: CheckResult,
    include_verbose_errors: bool = False,
) -> str:
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
        _append_license_notice(lines)
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
            if result.failing_package_hint_is_best_effort:
                lines.append('likely failing dependency (best effort):')
            else:
                lines.append('likely failing dependency:')
            lines.append(result.failing_package_hint)
            lines.append('')
        if result.error_tail:
            lines.append('pip error summary:')
            for line in result.error_tail:
                lines.append(line)
            lines.append('')
        if result.failure_detail:
            lines.append('diagnosis:')
            lines.append(result.failure_detail)
            lines.append('')
        if result.suggested_fixes:
            lines.append('what to try:')
            for fix in result.suggested_fixes:
                lines.append(f'- {fix}')
            lines.append('')
        if result.available_versions:
            versions_line = ', '.join(result.available_versions)
            if result.available_versions_more_count > 0:
                versions_line = f'{versions_line}, ... (+{result.available_versions_more_count} more)'
            lines.append('available versions (latest first):')
            lines.append(versions_line)
            lines.append('')
        if result.available_versions_query_error:
            lines.append('available versions:')
            lines.append(f'unavailable ({result.available_versions_query_error})')
            lines.append('')
        if include_verbose_errors:
            if result.stderr_tail:
                lines.append('verbose pip stderr tail:')
                for line in result.stderr_tail:
                    lines.append(f'  {line}')
                lines.append('')
            if result.stdout_tail:
                lines.append('verbose pip stdout tail:')
                for line in result.stdout_tail:
                    lines.append(f'  {line}')
                lines.append('')

    lines.extend([
        'summary:',
        f'elapsed_seconds={_format_elapsed_seconds(result.elapsed_seconds)}',
        f'pip_exit_code={result.pip_exit_code}',
    ])
    _append_license_notice(lines)
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
        'failing_package_hint_is_best_effort': result.failing_package_hint_is_best_effort,
        'failure_category': result.failure_category,
        'failure_detail': result.failure_detail,
        'suggested_fixes': list(result.suggested_fixes),
        'available_versions': list(result.available_versions),
        'available_versions_more_count': result.available_versions_more_count,
        'available_versions_query_error': result.available_versions_query_error,
        'error_tail': list(result.error_tail),
        'stdout_tail': list(result.stdout_tail),
        'stderr_tail': list(result.stderr_tail),
        'tool_error': result.tool_error,
    }
    if result.tool_error and result.tool_error_message:
        payload['tool_error_message'] = result.tool_error_message
    return json.dumps(payload, indent=2)
