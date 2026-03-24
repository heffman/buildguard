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
    lines = []

    if result.status == 'pass':
        lines.extend([
            '✅ INSTALL OK',
            '',
            f'Requirements: {result.requirements_path}',
            f'Python: {result.python_executable}',
            '',
            'Pinned requirements installed successfully in a clean environment.',
            '',
            f'Elapsed: {_format_elapsed_seconds(result.elapsed_seconds)}s',
            f'pip exit code: {result.pip_exit_code}',
        ])
        _append_license_notice(lines)
        return '\n'.join(lines)

    if result.tool_error:
        lines.extend([
            '❌ BUILDGUARD ERROR',
            '',
            f'Requirements: {result.requirements_path}',
            f'Python: {result.python_executable}',
            '',
            result.tool_error_message or 'Buildguard encountered a fatal tool/runtime error.',
        ])

        if include_verbose_errors:
            if result.stderr_tail:
                lines.extend([
                    '',
                    'Verbose pip stderr tail:',
                    *[f'  {line}' for line in result.stderr_tail],
                ])
            if result.stdout_tail:
                lines.extend([
                    '',
                    'Verbose pip stdout tail:',
                    *[f'  {line}' for line in result.stdout_tail],
                ])

        lines.extend([
            '',
            f'Elapsed: {_format_elapsed_seconds(result.elapsed_seconds)}s',
        ])
        _append_license_notice(lines)
        return '\n'.join(lines)

    lines.extend([
        '❌ INSTALL FAILURE DETECTED',
        '',
        f'Requirements: {result.requirements_path}',
        f'Python: {result.python_executable}',
    ])

    if result.failing_package_hint:
        lines.extend([
            '',
            f'Package: {result.failing_package_hint}',
        ])

    error_line = None
    if result.error_tail:
        error_line = result.error_tail[0].strip()
    elif result.failure_detail:
        error_line = result.failure_detail.strip()

    if error_line:
        lines.extend([
            f'Error: {error_line}',
        ])

    lines.extend([
        '',
        'This will fail your CI build.',
    ])

    if result.suggested_fixes:
        lines.extend([
            '',
            'Suggested fix:',
        ])
        for fix in result.suggested_fixes[:3]:
            lines.append(f'- {fix}')

    if result.available_versions:
        versions_line = ', '.join(result.available_versions)
        if result.available_versions_more_count > 0:
            versions_line = f'{versions_line}, ... (+{result.available_versions_more_count} more)'
        lines.extend([
            '',
            'Available versions:',
            versions_line,
        ])
    elif result.available_versions_query_error:
        lines.extend([
            '',
            f'Available versions: unavailable ({result.available_versions_query_error})',
        ])

    if include_verbose_errors:
        if result.stderr_tail:
            lines.extend([
                '',
                'Verbose pip stderr tail:',
                *[f'  {line}' for line in result.stderr_tail],
            ])
        if result.stdout_tail:
            lines.extend([
                '',
                'Verbose pip stdout tail:',
                *[f'  {line}' for line in result.stdout_tail],
            ])

    lines.extend([
        '',
        f'Elapsed: {_format_elapsed_seconds(result.elapsed_seconds)}s',
        f'pip exit code: {result.pip_exit_code}',
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