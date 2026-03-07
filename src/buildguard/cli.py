from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Optional, Sequence

from buildguard import __version__
from buildguard.checker import run_check
from buildguard.report import format_json_report, format_text_report

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='buildguard',
        description='Catch upstream Python dependency breakage before it surprises your CI build.',
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    subparsers = parser.add_subparsers(dest='command', required=True)
    check_parser = subparsers.add_parser(
        'check',
        help='check for upstream dependency drift by installing requirements in a clean virtual environment',
    )
    check_parser.add_argument('requirements_path', help='path to requirements.txt file')
    check_parser.add_argument('--json', action='store_true', dest='emit_json', help='emit JSON output')
    check_parser.add_argument('--timeout', type=int, default=300, help='timeout in seconds for pip install')
    check_parser.add_argument('--python', default=sys.executable, dest='python_executable', help='python executable used to create virtual environment')
    check_parser.add_argument('--keep-venv', action='store_true', help='do not delete temporary virtual environment')
    check_parser.add_argument('--no-upgrade-tools', action='store_true', help='skip upgrading pip, setuptools, and wheel')
    check_parser.description = (
        'Create a clean virtual environment and install a pinned dependency set to detect upstream '
        'ecosystem drift before your main CI build runs.'
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command != 'check':
        parser.error('unsupported command')

    if arguments.timeout <= 0:
        output = {
            'tool': 'buildguard',
            'version': __version__,
            'command': 'check',
            'requirements_path': arguments.requirements_path,
            'python_executable': arguments.python_executable,
            'status': 'fail',
            'exit_code': 2,
            'elapsed_seconds': 0.0,
            'venv_path': '',
            'pip_exit_code': None,
            'failing_package_hint': None,
            'error_tail': [],
            'stdout_tail': [],
            'stderr_tail': [],
            'tool_error': True,
            'tool_error_message': '--timeout must be greater than 0',
        }
        if arguments.emit_json:
            sys.stdout.write(json.dumps(output, indent=2) + '\n')
        else:
            sys.stdout.write('buildguard check: invalid arguments\n\nFAIL\n\n--timeout must be greater than 0\n')
        return 2

    try:
        result = run_check(
            requirements_path=arguments.requirements_path,
            python_executable=arguments.python_executable,
            timeout_seconds=arguments.timeout,
            keep_venv=arguments.keep_venv,
            upgrade_tools=not arguments.no_upgrade_tools,
        )
    except Exception as unexpected_error:
        logger.info('unexpected top-level error: %s', unexpected_error)
        if arguments.emit_json:
            sys.stdout.write(
                json.dumps(
                    {
                        'tool': 'buildguard',
                        'version': __version__,
                        'command': 'check',
                        'requirements_path': arguments.requirements_path,
                        'python_executable': arguments.python_executable,
                        'status': 'fail',
                        'exit_code': 2,
                        'elapsed_seconds': 0.0,
                        'venv_path': '',
                        'pip_exit_code': None,
                        'failing_package_hint': None,
                        'error_tail': [],
                        'stdout_tail': [],
                        'stderr_tail': [],
                        'tool_error': True,
                        'tool_error_message': str(unexpected_error),
                    },
                    indent=2,
                )
                + '\n'
            )
        else:
            sys.stdout.write('buildguard check: fatal error\n\nFAIL\n\n')
            sys.stdout.write(f'{unexpected_error}\n')
        return 2

    if arguments.emit_json:
        sys.stdout.write(format_json_report(result) + '\n')
    else:
        sys.stdout.write(format_text_report(result) + '\n')
    return result.exit_code


if __name__ == '__main__':
    raise SystemExit(main())
