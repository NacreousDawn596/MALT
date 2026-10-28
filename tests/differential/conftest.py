"""Collection-time check: CI must not silently skip the differential suite.

When ``MALT_REQUIRE_OCTAVE=1`` is set, a missing ``octave-cli`` is a hard
failure (not a skip), so the Octave differential tests cannot be silently
dropped from a CI run.
"""

from __future__ import annotations

import os

import pytest

from . import octave_available


def pytest_configure(config):  # noqa: ARG001
    if os.environ.get("MALT_REQUIRE_OCTAVE") == "1" and not octave_available():
        raise pytest.UsageError(
            "MALT_REQUIRE_OCTAVE=1 is set but 'octave-cli' is not on PATH; "
            "the differential suite must not be silently skipped in CI"
        )
