from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

_MEANINGFUL_LINE_LIMIT = 10
_NOISE_PREFIXES = (
    'WARNING: Retrying',
    'Looking in indexes:',
    '[notice] ',
)


def _meaningful_lines(lines: Iterable[str]) -> List[str]:
    return [line.strip() for line in lines if line and line.strip()]


def _normalize_name(package_name: str) -> str:
    return re.sub(r'[-_.]+', '-', package_name.strip().lower())


def _extract_collecting_package(line: str) -> Optional[str]:
    collecting_match = re.search(r'^Collecting\s+(.+)$', line)
    if collecting_match is None:
        return None
    return collecting_match.group(1).strip()


def _extract_package_name_from_spec(package_spec: str) -> str:
    stripped_spec = package_spec.strip()
    for separator in ['==', '>=', '<=', '!=', '~=', '>', '<']:
        if separator in stripped_spec:
            return stripped_spec.split(separator, 1)[0].strip()
    return stripped_spec.split('[', 1)[0].strip()


def extract_failing_package_hint(output_text: str) -> Optional[str]:
    lines = _meaningful_lines(output_text.splitlines())
    latest_collecting_by_name: Dict[str, str] = {}

    for line in lines:
        collecting_spec = _extract_collecting_package(line)
        if collecting_spec is not None:
            collecting_name = _extract_package_name_from_spec(collecting_spec)
            latest_collecting_by_name[_normalize_name(collecting_name)] = collecting_spec
            continue

        no_version_match = re.search(
            r'Could not find a version that satisfies the requirement\s+([^\s]+)',
            line,
        )
        if no_version_match is not None:
            return no_version_match.group(1).strip()

        no_distribution_match = re.search(
            r'No matching distribution found for\s+([^\s]+)',
            line,
        )
        if no_distribution_match is not None:
            return no_distribution_match.group(1).strip()

        failed_wheel_match = re.search(r'Failed building wheel for\s+([^\s]+)$', line)
        if failed_wheel_match is not None:
            package_name = failed_wheel_match.group(1).strip()
            normalized_name = _normalize_name(package_name)
            if normalized_name in latest_collecting_by_name:
                return latest_collecting_by_name[normalized_name]
            return package_name

        building_wheel_match = re.search(r'Building wheel for\s+([^\s]+)', line)
        if building_wheel_match is not None:
            package_name = building_wheel_match.group(1).strip()
            normalized_name = _normalize_name(package_name)
            if normalized_name in latest_collecting_by_name:
                latest_collecting_by_name[normalized_name] = latest_collecting_by_name[normalized_name]
            else:
                latest_collecting_by_name[normalized_name] = package_name

    return None


def extract_error_tail(stdout_text: str, stderr_text: str) -> Tuple[str, ...]:
    combined_lines = _meaningful_lines((stdout_text + '\n' + stderr_text).splitlines())
    filtered_lines = [line for line in combined_lines if not line.startswith(_NOISE_PREFIXES)]
    if filtered_lines:
        return tuple(filtered_lines[-_MEANINGFUL_LINE_LIMIT:])
    return tuple(combined_lines[-_MEANINGFUL_LINE_LIMIT:])


def extract_stream_tail(stream_text: str, limit: int = _MEANINGFUL_LINE_LIMIT) -> Tuple[str, ...]:
    meaningful = _meaningful_lines(stream_text.splitlines())
    return tuple(meaningful[-limit:])
