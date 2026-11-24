#!/usr/bin/env python3
"""Unit tests for shared sprint-state resolution (SoloRail E03-ISS-02).

Stdlib-only (unittest). Run with:
    python3 scripts/test_solorail_state.py
"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from solorail_state import (
    is_closed_sprint,
    list_sprint_files,
    read_sprint_status,
    resolve_active_sprint,
    sprint_number,
)

HEADER = "# Sprint {n}\n\n- **Status:** {status}\n\n## Planned Issues\n"
ROW_HEADER = (
    "| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |\n"
    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
)


def write_sprint(sprints_dir: str, number: int, status: str, rows: str = "") -> str:
    path = os.path.join(sprints_dir, f"sprint-{number:02d}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(HEADER.format(n=number, status=status) + ROW_HEADER + rows)
    return path


class SprintNumberTests(unittest.TestCase):
    def test_orders_numerically_not_lexically(self):
        """Test 1: sprint-9 must come before sprint-10; plain sorted() reverses
        this, which is part of why filename order is not sprint state."""
        with tempfile.TemporaryDirectory() as tmp:
            for n in (9, 10):
                path = os.path.join(tmp, f"sprint-{n}.md")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(HEADER.format(n=n, status="CLOSED"))

            ordered = [os.path.basename(p) for p in list_sprint_files(tmp)]

        self.assertEqual(ordered, ["sprint-9.md", "sprint-10.md"])
        self.assertEqual(sorted(ordered), ["sprint-10.md", "sprint-9.md"])

    def test_unparseable_name_is_minus_one(self):
        self.assertEqual(sprint_number("/x/sprint-draft.md"), -1)
        self.assertEqual(sprint_number("/x/sprint-07.md"), 7)


class ReadSprintStatusTests(unittest.TestCase):
    def test_reads_header_status(self):
        lines = HEADER.format(n=2, status="ACTIVE").splitlines(keepends=True)
        self.assertEqual(read_sprint_status(lines), "ACTIVE")
        self.assertFalse(is_closed_sprint(lines))

    def test_closed_header_detected(self):
        lines = HEADER.format(n=1, status="CLOSED").splitlines(keepends=True)
        self.assertEqual(read_sprint_status(lines), "CLOSED")
        self.assertTrue(is_closed_sprint(lines))

    def test_issue_row_mentioning_closed_does_not_flip_status(self):
        """Test 5: only the header block decides the board's status."""
        lines = (
            HEADER.format(n=2, status="ACTIVE")
            + ROW_HEADER
            + "| E03-ISS-01 | E-03 | Thing | DONE | 1.0h | 1.0h | - | sprint CLOSED early |\n"
        ).splitlines(keepends=True)

        self.assertEqual(read_sprint_status(lines), "ACTIVE")
        self.assertFalse(is_closed_sprint(lines))

    def test_missing_status_is_none(self):
        lines = ["# Sprint 03\n", "\n", "## Planned Issues\n"]
        self.assertIsNone(read_sprint_status(lines))


class ResolveActiveSprintTests(unittest.TestCase):
    def test_active_wins_over_last_filename(self):
        """Test 2 (the gate bug): an ACTIVE sprint-01 must be chosen even though
        a CLOSED sprint-02 sorts last."""
        with tempfile.TemporaryDirectory() as tmp:
            write_sprint(tmp, 1, "ACTIVE")
            write_sprint(tmp, 2, "CLOSED")

            resolved = resolve_active_sprint(tmp)

        self.assertEqual(os.path.basename(resolved), "sprint-01.md")

    def test_no_active_falls_back_to_highest_numbered_with_warning(self):
        """Test 3: never return None just because every sprint is closed."""
        with tempfile.TemporaryDirectory() as tmp:
            write_sprint(tmp, 1, "CLOSED")
            write_sprint(tmp, 2, "CLOSED")

            err = io.StringIO()
            with redirect_stderr(err):
                resolved = resolve_active_sprint(tmp)

        self.assertEqual(os.path.basename(resolved), "sprint-02.md")
        self.assertIn("no active sprint", err.getvalue().lower())

    def test_multiple_active_picks_lowest_numbered_with_warning(self):
        """Test 4: the oldest still-open sprint is the one needing attention."""
        with tempfile.TemporaryDirectory() as tmp:
            write_sprint(tmp, 1, "ACTIVE")
            write_sprint(tmp, 2, "ACTIVE")

            err = io.StringIO()
            with redirect_stderr(err):
                resolved = resolve_active_sprint(tmp)

        self.assertEqual(os.path.basename(resolved), "sprint-01.md")
        self.assertIn("more than one", err.getvalue().lower())

    def test_empty_directory_returns_none(self):
        """Test 6."""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(resolve_active_sprint(tmp))

    def test_missing_directory_returns_none(self):
        self.assertIsNone(resolve_active_sprint("/nonexistent/sprints"))


class GateIntegrationTests(unittest.TestCase):
    def test_gate_finds_in_progress_issue_in_active_older_sprint(self):
        """Test 7: the gate must enforce an IN_PROGRESS issue in an ACTIVE
        sprint-01 while a CLOSED sprint-02 exists. Fails before this issue."""
        from enforce_gate import get_active_issue

        with tempfile.TemporaryDirectory() as tmp:
            write_sprint(
                tmp, 1, "ACTIVE",
                "| E01-ISS-09 | E-01 | Live work | IN_PROGRESS | 1.0h | - | - | - |\n",
            )
            write_sprint(
                tmp, 2, "CLOSED",
                "| E03-ISS-01 | E-03 | Old work | DONE | 1.0h | 1.0h | - | - |\n",
            )

            active = get_active_issue(tmp)

        self.assertEqual(active, "E01-ISS-09")


class ComputeActualHoursIntegrationTests(unittest.TestCase):
    """The fourth defect site, found by this spec's own DoD grep rather than
    by inspection (compute_actual_hours.py:40,44)."""

    def test_finds_issue_on_active_sprint_not_last_filename(self):
        from compute_actual_hours import _find_started_at

        with tempfile.TemporaryDirectory() as tmp:
            write_sprint(
                tmp, 1, "ACTIVE",
                "| E01-ISS-09 | E-01 | Live work | IN_PROGRESS | 1.0h | - | 2026-11-24 09:00 | - |\n",
            )
            write_sprint(tmp, 2, "CLOSED", "")

            self.assertEqual(_find_started_at("E01-ISS-09", tmp), "2026-11-24 09:00")

    def test_finds_carried_over_issue_on_a_non_active_board(self):
        """An issue ID is globally unique, so a lookup must not fail just
        because the issue lives on another board."""
        from compute_actual_hours import _find_started_at

        with tempfile.TemporaryDirectory() as tmp:
            write_sprint(
                tmp, 1, "CLOSED",
                "| E01-ISS-03 | E-01 | Older work | DONE | 1.0h | 1.0h | 2026-11-20 14:00 | - |\n",
            )
            write_sprint(tmp, 2, "ACTIVE", "")

            self.assertEqual(_find_started_at("E01-ISS-03", tmp), "2026-11-20 14:00")

    def test_unknown_issue_returns_none(self):
        from compute_actual_hours import _find_started_at

        with tempfile.TemporaryDirectory() as tmp:
            write_sprint(tmp, 1, "ACTIVE", "")
            self.assertIsNone(_find_started_at("E99-ISS-99", tmp))


if __name__ == "__main__":
    unittest.main(verbosity=2)
