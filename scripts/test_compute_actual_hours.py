#!/usr/bin/env python3
"""Unit tests for compute_actual_hours.py (SoloRail E02-ISS-03).

Stdlib-only (unittest + tempfile). Run with:
    python3 scripts/test_compute_actual_hours.py
"""

import os
import tempfile
import unittest
from datetime import datetime

from compute_actual_hours import compute_actual_hours

SPRINT_TEMPLATE = """# Sprint 01

## Planned Issues
| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E99-ISS-01 | E-99 | Example issue | IN_PROGRESS | 1.0h | 0.0h | {started_at} | - |
"""


def _write_sprint_file(tmpdir: str, started_at: str) -> str:
    sprints_dir = os.path.join(tmpdir, "sprints")
    os.makedirs(sprints_dir, exist_ok=True)
    path = os.path.join(sprints_dir, "sprint-01.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(SPRINT_TEMPLATE.format(started_at=started_at))
    return sprints_dir


class ComputeActualHoursTests(unittest.TestCase):
    def test_rounds_down_to_nearest_half_hour(self):
        """Test 1: 1.2h elapsed -> rounds down to 1.0."""
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = _write_sprint_file(tmp, "2026-11-24 10:00")
            now = datetime(2026, 11, 24, 11, 12)  # +1.2h
            self.assertEqual(
                compute_actual_hours("E99-ISS-01", sprints_dir, now=now), 1.0
            )

    def test_rounds_up_to_nearest_half_hour(self):
        """Test 2: 1.3h elapsed -> rounds up to 1.5."""
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = _write_sprint_file(tmp, "2026-11-24 10:00")
            now = datetime(2026, 11, 24, 11, 18)  # +1.3h
            self.assertEqual(
                compute_actual_hours("E99-ISS-01", sprints_dir, now=now), 1.5
            )

    def test_floors_at_half_hour_minimum(self):
        """Test 3: 10 minutes elapsed -> floors to 0.5h minimum."""
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = _write_sprint_file(tmp, "2026-11-24 10:00")
            now = datetime(2026, 11, 24, 10, 10)  # +10min
            self.assertEqual(
                compute_actual_hours("E99-ISS-01", sprints_dir, now=now), 0.5
            )

    def test_negative_elapsed_floors_at_half_hour_minimum(self):
        """Test 4: now before Started At (clock skew) -> floors to 0.5h, never negative."""
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = _write_sprint_file(tmp, "2026-11-24 10:00")
            now = datetime(2026, 11, 24, 9, 0)  # before Started At
            self.assertEqual(
                compute_actual_hours("E99-ISS-01", sprints_dir, now=now), 0.5
            )

    def test_issue_not_found_returns_none(self):
        """Test 5: issue ID not present in the sprint file -> None."""
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = _write_sprint_file(tmp, "2026-11-24 10:00")
            now = datetime(2026, 11, 24, 11, 0)
            self.assertIsNone(
                compute_actual_hours("E00-ISS-99", sprints_dir, now=now)
            )

    def test_started_at_placeholder_returns_none(self):
        """Test 6: Started At is '-' (not yet started) -> None."""
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = _write_sprint_file(tmp, "-")
            now = datetime(2026, 11, 24, 11, 0)
            self.assertIsNone(
                compute_actual_hours("E99-ISS-01", sprints_dir, now=now)
            )

    def test_date_only_started_at_assumes_midnight(self):
        """Started At with no time component (date only) is parseable."""
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = _write_sprint_file(tmp, "2026-11-24")
            now = datetime(2026, 11, 24, 1, 0)  # +1h from midnight
            self.assertEqual(
                compute_actual_hours("E99-ISS-01", sprints_dir, now=now), 1.0
            )

    def test_missing_sprints_dir_returns_none(self):
        """No sprints directory at all -> None, no crash."""
        with tempfile.TemporaryDirectory() as tmp:
            missing_dir = os.path.join(tmp, "nonexistent-sprints")
            now = datetime(2026, 11, 24, 11, 0)
            self.assertIsNone(
                compute_actual_hours("E99-ISS-01", missing_dir, now=now)
            )


if __name__ == "__main__":
    unittest.main()
