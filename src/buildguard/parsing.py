from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

_MEANINGFUL_LINE_LIMIT = 10
_NOISE_PREFIXES = (
    'WARNING: Retrying',
    'Looking in indexes:',
    '[notice] ',
)
_SIGNAL_PATTERNS = (
    'Failed building wheel for',
    'error: subprocess-exited-with-error',
    'Could not find a version that satisfies the requirement',
    'No matching distribution found for',
    'Preparing metadata (pyproject.toml) ... error',
    'Getting requirements to build wheel ... error',
    'ResolutionImpossible',
    'metadata-generation-failed',
    'Failed to build',
    'ERROR:',
)
_MAX_SUMMARY_LINE_LENGTH = 220


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


def extract_package_name_from_requirement_spec(package_spec: str) -> str:
    return _extract_package_name_from_spec(package_spec)


def extract_failing_package_hint(output_text: str) -> Tuple[Optional[str], bool]:
    lines = _meaningful_lines(output_text.splitlines())
    latest_collecting_by_name: Dict[str, str] = {}
    most_recent_collecting_spec: Optional[str] = None

    for line in lines:
        collecting_spec = _extract_collecting_package(line)
        if collecting_spec is not None:
            collecting_name = _extract_package_name_from_spec(collecting_spec)
            latest_collecting_by_name[_normalize_name(collecting_name)] = collecting_spec
            most_recent_collecting_spec = collecting_spec
            continue

        no_version_match = re.search(
            r'Could not find a version that satisfies the requirement\s+([^\s]+)',
            line,
        )
        if no_version_match is not None:
            return no_version_match.group(1).strip(), False

        no_distribution_match = re.search(
            r'No matching distribution found for\s+([^\s]+)',
            line,
        )
        if no_distribution_match is not None:
            return no_distribution_match.group(1).strip(), False

        failed_wheel_match = re.search(r'Failed building wheel for\s+([^\s]+)$', line)
        if failed_wheel_match is not None:
            package_name = failed_wheel_match.group(1).strip()
            normalized_name = _normalize_name(package_name)
            if normalized_name in latest_collecting_by_name:
                return latest_collecting_by_name[normalized_name], False
            return package_name, False

        building_wheel_match = re.search(r'Building wheel for\s+([^\s]+)', line)
        if building_wheel_match is not None:
            package_name = building_wheel_match.group(1).strip()
            normalized_name = _normalize_name(package_name)
            if normalized_name in latest_collecting_by_name:
                latest_collecting_by_name[normalized_name] = latest_collecting_by_name[normalized_name]
            else:
                latest_collecting_by_name[normalized_name] = package_name
            most_recent_collecting_spec = latest_collecting_by_name[normalized_name]
            continue

        # Fallback: pip sometimes reports only generic errors. Use the most recently
        # collected requirement as a best-effort hint.
        if (
            'subprocess-exited-with-error' in line
            or 'metadata-generation-failed' in line
            or 'Preparing metadata (pyproject.toml) ... error' in line
            or 'Getting requirements to build wheel ... error' in line
        ):
            if most_recent_collecting_spec is not None:
                return most_recent_collecting_spec, True

    return None, False


def extract_error_tail(stdout_text: str, stderr_text: str) -> Tuple[str, ...]:
    combined_lines = _meaningful_lines((stdout_text + '\n' + stderr_text).splitlines())
    filtered_lines = [line for line in combined_lines if not line.startswith(_NOISE_PREFIXES)]
    source_lines = filtered_lines if filtered_lines else combined_lines

    summarized_lines = [_summarize_error_line(line) for line in source_lines]
    signal_lines = [line for line in summarized_lines if _is_signal_line(line)]
    selected_lines = signal_lines if signal_lines else summarized_lines
    return tuple(selected_lines[-_MEANINGFUL_LINE_LIMIT:])


def extract_stream_tail(stream_text: str, limit: int = _MEANINGFUL_LINE_LIMIT) -> Tuple[str, ...]:
    meaningful = _meaningful_lines(stream_text.splitlines())
    return tuple(meaningful[-limit:])


def infer_failure_diagnostics(
    output_text: str,
    failing_package_hint: Optional[str],
) -> Tuple[Optional[str], Optional[str], Tuple[str, ...]]:
    normalized_output = output_text.lower()

    if (
        'resolutionimpossible' in normalized_output
        or 'cannot install' in normalized_output and 'because these package versions have conflicting dependencies' in normalized_output
    ):
        return (
            'resolver_conflict',
            'Dependency resolution failed because pinned packages have incompatible constraints.',
            (
                'Review transitive constraints for conflicting pins and align incompatible versions.',
                'Temporarily loosen one or more strict pins to find a compatible set.',
            ),
        )

    if 'failed building wheel for' in normalized_output:
        package_text = f' for {failing_package_hint}' if failing_package_hint else ''
        return (
            'wheel_build_failure',
            f'pip could not build a wheel{package_text}.',
            (
                'Prefer a package version that ships prebuilt wheels for this Python version/platform.',
                'Install required native build tooling and headers, then retry.',
            ),
        )

    if (
        'metadata-generation-failed' in normalized_output
        or 'preparing metadata (pyproject.toml) ... error' in normalized_output
        or 'getting requirements to build wheel ... error' in normalized_output
    ):
        package_text = f' for {failing_package_hint}' if failing_package_hint else ''
        return (
            'metadata_generation_failure',
            f'Build metadata generation failed{package_text}.',
            (
                'This often indicates old package pins that are incompatible with modern build backends.',
                'Try a newer compatible version of the failing package or pin older build tooling in that package path.',
            ),
        )

    if (
        'no matching distribution found for' in normalized_output
        or 'could not find a version that satisfies the requirement' in normalized_output
    ):
        package_text = f' for {failing_package_hint}' if failing_package_hint else ''
        return (
            'missing_distribution',
            f'No installable distribution was found{package_text} on the current index/Python/platform.',
            (
                'Verify that the pinned version exists on your package index.',
                'Check Python-version/platform compatibility for that package version.',
            ),
        )

    if 'requires-python' in normalized_output or 'is not a supported wheel on this platform' in normalized_output:
        return (
            'python_platform_incompatibility',
            'At least one dependency is incompatible with the current Python version or platform.',
            (
                'Use a compatible Python interpreter version for this dependency set.',
                'Update pins to versions that support your runtime platform.',
            ),
        )

    return (
        None,
        None,
        tuple(),
    )


def parse_available_versions_from_pip_index_output(output_text: str) -> Tuple[str, ...]:
    for line in output_text.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith('Available versions:'):
            versions_text = stripped_line.split(':', 1)[1].strip()
            if not versions_text:
                return tuple()
            return tuple(version.strip() for version in versions_text.split(',') if version.strip())
    return tuple()


def _summarize_error_line(line: str) -> str:
    summarized_line = line
    if ' (from versions:' in summarized_line:
        summarized_line = summarized_line.split(' (from versions:', 1)[0]
    if len(summarized_line) > _MAX_SUMMARY_LINE_LENGTH:
        summarized_line = summarized_line[: _MAX_SUMMARY_LINE_LENGTH - 3] + '...'
    return summarized_line


def _is_signal_line(line: str) -> bool:
    for pattern in _SIGNAL_PATTERNS:
        if pattern in line:
            return True
    return False
