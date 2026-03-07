from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    existing_python_path = environment.get('PYTHONPATH', '')
    src_path = str(repo_root / 'src')
    if existing_python_path:
        environment['PYTHONPATH'] = src_path + os.pathsep + existing_python_path
    else:
        environment['PYTHONPATH'] = src_path

    command = [
        sys.executable,
        '-m',
        'buildguard',
        'check',
        str(repo_root / 'examples' / 'requirements-good.txt'),
        '--no-upgrade-tools',
    ]
    completed_process = subprocess.run(command, capture_output=True, text=True, env=environment, check=False)

    assert completed_process.returncode == 0, (
        f'expected return code 0, got {completed_process.returncode}\n'
        f'stdout:\n{completed_process.stdout}\n'
        f'stderr:\n{completed_process.stderr}'
    )
    assert 'PASS' in completed_process.stdout
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
