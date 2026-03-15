from __future__ import annotations

import os

LICENSE_NOTICE = (
    'Note: buildguard is free for evaluation/personal use. '
    'Commercial teams should purchase a license. '
    'Info: https://hefftools.dev/buildguard'
)

DEFAULT_SHOW_LICENSE_NOTICE = True
HIDE_LICENSE_NOTICE_ENV_VAR = 'BUILDGUARD_HIDE_LICENSE_NOTICE'


def should_show_license_notice() -> bool:
    override = os.environ.get(HIDE_LICENSE_NOTICE_ENV_VAR)
    if override is not None:
        return override.strip().lower() not in {'1', 'true', 'yes', 'on'}
    return DEFAULT_SHOW_LICENSE_NOTICE
