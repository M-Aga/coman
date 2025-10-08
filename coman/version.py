"""Semantic version metadata for the Coman platform."""

from __future__ import annotations

from datetime import date

COMAN_VERSION = "1.0.0"
"""Umbrella version of the Coman platform following SemVer."""

API_MAJOR_VERSION = 1
"""Current public API major version exposed via HTTP routes."""

LEGACY_ROUTE_REMOVAL_DATE = date(2025, 9, 30)
"""Planned sunset date for unversioned legacy HTTP routes."""

# Per-module semantic versions. Modules inherit the umbrella version unless
# explicitly overridden in this mapping.
MODULE_VERSIONS: dict[str, str] = {}


def get_module_version(module_name: str) -> str:
    """Return the semantic version string for a module."""

    return MODULE_VERSIONS.get(module_name, COMAN_VERSION)
