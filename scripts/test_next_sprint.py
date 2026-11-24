#!/usr/bin/env python3
"""Unit tests for sprint generation and carryover (SoloRail E03-ISS-04).

Stdlib-only (unittest). Run with:
    python3 scripts/test_next_sprint.py
"""

import os
import re
import shutil
import tempfile
import unittest
from datetime import date

from next_sprint import (
    generate_next_sprint,
    next_sprint_number,
    render_template,
)
from solorail_state import carryover_rows, read_sprint_status, reset_row_for_carryover

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE_TEMPLATE = os.path.join(REPO_ROOT, ".solorail", "sprints", "_TEMPLATE.md")

ROW_HEADER = (
    "| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |\n"
    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
)


def make_solorail(tmp: str, sprints: dict[int, tuple[str, str]]) -> str:
    """Build a .solorail tree. sprints maps number -> (status, rows)."""
    solorail = os.path.join(tmp, ".solorail")
    sprints_dir = os.path.join(solorail, "sprints")
    os.makedirs(sprints_dir)
    os.makedirs(os.path.join(solorail, "retros"))
    shutil.copy(LIVE_TEMPLATE, os.path.join(sprints_dir, "_TEMPLATE.md"))
    for number, (status, rows) in sprints.items():
        with open(os.path.join(sprints_dir, f"sprint-{number:02d}.md"), "w") as f:
            f.write(
                f"# Sprint {number}\n\n- **Status:** {status}\n\n"
                f"## Planned Issues\n{ROW_HEADER}{rows}"
            )
    return solorail


class NextSprintNumberTests(unittest.TestCase):
    def test_empty_directory_starts_at_one(self):
        """Test 1a."""
        with tempfile.TemporaryDirectory() as tmp:
            solorail = make_solorail(tmp, {})
            self.assertEqual(next_sprint_number(os.path.join(solorail, "sprints")), 1)

    def test_numeric_not_lexical_increment(self):
        """Test 1b: sprint-09 + sprint-10 -> 11, not 10. Plain string sort would
        pick sprint-09 as the highest."""
        with tempfile.TemporaryDirectory() as tmp:
            solorail = make_solorail(tmp, {9: ("CLOSED", ""), 10: ("CLOSED", "")})
            self.assertEqual(next_sprint_number(os.path.join(solorail, "sprints")), 11)


class RenderTemplateTests(unittest.TestCase):
    def test_no_token_survives(self):
        """Test 7a."""
        with open(LIVE_TEMPLATE) as f:
            template = f.read()

        out = render_template(
            template, number=3, start_date="2026-12-09", end_date="2026-12-22",
            capacity="20.0h", carryover=[],
        )

        leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
        self.assertEqual(leftover, [], f"unsubstituted tokens: {leftover}")
        self.assertIn("# Sprint 3", out)
        self.assertIn("2026-12-09", out)

    def test_raises_on_leftover_token(self):
        """Test 7b: a template/generator mismatch must fail loudly."""
        with self.assertRaises(ValueError):
            render_template(
                "# Sprint {{NUMBER}}\n{{SOMETHING_UNKNOWN}}\n",
                number=1, start_date="a", end_date="b", capacity="c", carryover=[],
            )


class CarryoverTests(unittest.TestCase):
    def _board(self):
        rows = (
            "| E01-ISS-01 | E-01 | Finished | DONE | 1.0h | 1.0h | 2026-11-20 09:00 | - |\n"
            "| E01-ISS-02 | E-01 | Dropped | CUT | 2.0h | 0.5h | - | descoped |\n"
            "| E01-ISS-03 | E-01 | Not started | TODO | 3.0h | - | - | - |\n"
            "| E01-ISS-04 | E-01 | Stuck | BLOCKED | 2.0h | 0.5h | 2026-11-21 10:00 | waiting on API |\n"
        )
        return (
            f"# Sprint 1\n\n- **Status:** CLOSED\n\n## Planned Issues\n{ROW_HEADER}{rows}"
        ).splitlines(keepends=True)

    def test_only_todo_and_blocked_carry(self):
        """Test 3: DONE and CUT stay behind as that sprint's history."""
        carried = carryover_rows(self._board())
        ids = [r.split("|")[1].strip() for r in carried]
        self.assertEqual(ids, ["E01-ISS-03", "E01-ISS-04"])

    def test_carried_row_is_reset(self):
        """Test 4: Actual and Started At cleared; Est and Status preserved."""
        blocked = [r for r in carryover_rows(self._board()) if "E01-ISS-04" in r][0]
        reset = reset_row_for_carryover(blocked, origin="sprint-01")
        cells = [c.strip() for c in reset.split("|")]

        self.assertEqual(cells[4], "BLOCKED", "a blocked issue stays blocked")
        self.assertEqual(cells[5], "2.0h", "estimate preserved")
        self.assertEqual(cells[6], "-", "actual cleared")
        self.assertEqual(cells[7], "-", "started at cleared")
        self.assertIn("sprint", cells[8].lower(), "note records the origin sprint")


class GenerateNextSprintTests(unittest.TestCase):
    def test_generated_board_survives_a_real_sync(self):
        """Test 2: the generated board must satisfy every marker the consumers
        parse. Asserted by running the real sync(), not by string matching --
        this is what would have caught hand-authored drift."""
        from sync_metrics import sync

        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            solorail = make_solorail(tmp, {1: ("CLOSED", "")})
            path = generate_next_sprint(solorail, today=date(2026, 12, 9))

            # Add a real issue row so sync has something to total.
            with open(path) as f:
                content = f.read()
            content = content.replace(
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
                "| E09-ISS-01 | E-09 | Real work | DONE | 2.0h | 1.5h | - | - |\n",
            )
            with open(path, "w") as f:
                f.write(content)

            try:
                os.chdir(tmp)
                sync()
            finally:
                os.chdir(cwd)

            with open(path) as f:
                synced = f.read()

        self.assertIn("| **Total Hours** | 2.0h | 1.5h |", synced)
        self.assertIn("- **Total Actual:** 1.5h", synced)
        self.assertIn("- **Completed / Total Active Issues:** 1 / 1", synced)

    def test_generated_board_is_active_and_numbered(self):
        with tempfile.TemporaryDirectory() as tmp:
            solorail = make_solorail(tmp, {1: ("CLOSED", "")})
            path = generate_next_sprint(solorail, today=date(2026, 12, 9))

            self.assertTrue(path.endswith("sprint-02.md"))
            with open(path) as f:
                lines = f.readlines()
            self.assertEqual(read_sprint_status(lines), "ACTIVE")

    def test_dates_derived_from_cadence(self):
        """Test 8: 2 weeks -> end is 13 days after start."""
        with tempfile.TemporaryDirectory() as tmp:
            solorail = make_solorail(tmp, {1: ("CLOSED", "")})
            path = generate_next_sprint(solorail, today=date(2026, 12, 9), weeks=2)
            with open(path) as f:
                content = f.read()

        self.assertIn("**Start Date:** 2026-12-09", content)
        self.assertIn("**End Date:** 2026-12-22", content)

    def test_carryover_lands_in_generated_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            solorail = make_solorail(tmp, {
                1: ("CLOSED",
                    "| E01-ISS-01 | E-01 | Done | DONE | 1.0h | 1.0h | - | - |\n"
                    "| E01-ISS-02 | E-01 | Open | TODO | 3.0h | - | - | - |\n"),
            })
            path = generate_next_sprint(solorail, today=date(2026, 12, 9))
            with open(path) as f:
                content = f.read()

        self.assertIn("E01-ISS-02", content)
        self.assertNotIn("E01-ISS-01", content, "DONE rows must not carry over")

    def test_refuses_while_a_sprint_is_active(self):
        """Test 5: two ACTIVE boards is the ambiguous state ISS-02 warns about."""
        with tempfile.TemporaryDirectory() as tmp:
            solorail = make_solorail(tmp, {1: ("ACTIVE", "")})
            with self.assertRaises(RuntimeError):
                generate_next_sprint(solorail, today=date(2026, 12, 9))

            path = generate_next_sprint(solorail, today=date(2026, 12, 9), force=True)
            self.assertTrue(os.path.exists(path))

    def test_refuses_to_overwrite(self):
        """Test 6: the overwrite guard.

        Normal numbering cannot collide -- the next number is derived from the
        existing files -- so the guard is defence in depth against a manual or
        concurrent state. Exercised by forcing the number to collide.
        """
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            solorail = make_solorail(tmp, {1: ("CLOSED", ""), 2: ("CLOSED", "")})

            with patch("next_sprint.next_sprint_number", return_value=2):
                with self.assertRaises(RuntimeError) as ctx:
                    generate_next_sprint(solorail, today=date(2026, 12, 9))

            self.assertIn("refusing to overwrite", str(ctx.exception))

            # And the existing board is untouched.
            with open(os.path.join(solorail, "sprints", "sprint-02.md")) as f:
                self.assertIn("# Sprint 2", f.read())


class CarryoverDoubleCountTests(unittest.TestCase):
    """A carried issue exists on two boards. Epic totals must count it once.

    Found mid-build: a single 10.0h unfinished issue carried once produced
    'E-01 | 20.0h' in ROADMAP.md.
    """

    def _setup(self, tmp: str) -> str:
        solorail = os.path.join(tmp, ".solorail")
        sprints_dir = os.path.join(solorail, "sprints")
        os.makedirs(sprints_dir)
        os.makedirs(os.path.join(solorail, "retros"))
        shutil.copy(LIVE_TEMPLATE, os.path.join(sprints_dir, "_TEMPLATE.md"))
        with open(os.path.join(solorail, "ROADMAP.md"), "w") as f:
            f.write(
                "# Product Roadmap\n\n"
                "| Epic ID | Title | Status | Est. Hours | Actual Hours | Spec File |\n"
                "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
                "| E-01 | Thing | ACTIVE | 0.0h | 0.0h | - |\n"
            )
        with open(os.path.join(sprints_dir, "sprint-01.md"), "w") as f:
            f.write(
                "# Sprint 01\n\n- **Status:** CLOSED\n\n## Planned Issues\n"
                + ROW_HEADER
                + "| E01-ISS-01 | E-01 | Unfinished | TODO | 10.0h | - | - | - |\n"
            )
        with open(os.path.join(solorail, "retros", "sprint-01-retro.md"), "w") as f:
            f.write("# retro\n")
        return solorail

    def test_epic_total_counts_carried_issue_once(self):
        from sync_metrics import sync

        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            solorail = self._setup(tmp)
            generate_next_sprint(solorail, today=date(2026, 12, 9))
            try:
                os.chdir(tmp)
                sync()
            finally:
                os.chdir(cwd)
            with open(os.path.join(solorail, "ROADMAP.md")) as f:
                roadmap = f.read()

        self.assertIn("| E-01 | Thing | ACTIVE | 10.0h |", roadmap)
        self.assertNotIn("20.0h", roadmap)

    def test_no_false_duplicate_warning_for_carryover(self):
        import io
        from contextlib import redirect_stdout

        from sync_metrics import sync

        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            solorail = self._setup(tmp)
            generate_next_sprint(solorail, today=date(2026, 12, 9))
            out = io.StringIO()
            try:
                os.chdir(tmp)
                with redirect_stdout(out):
                    sync()
            finally:
                os.chdir(cwd)

        self.assertNotIn("Duplicate Issue ID", out.getvalue())

    def test_real_duplicate_on_one_board_still_warns(self):
        """The warning must keep working for a genuine duplicate."""
        import io
        from contextlib import redirect_stdout

        from sync_metrics import sync

        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            solorail = os.path.join(tmp, ".solorail")
            sprints_dir = os.path.join(solorail, "sprints")
            os.makedirs(sprints_dir)
            with open(os.path.join(sprints_dir, "sprint-01.md"), "w") as f:
                f.write(
                    "# Sprint 01\n\n- **Status:** ACTIVE\n\n## Planned Issues\n"
                    + ROW_HEADER
                    + "| E01-ISS-01 | E-01 | One | TODO | 1.0h | - | - | - |\n"
                    + "| E01-ISS-01 | E-01 | Same ID again | TODO | 2.0h | - | - | - |\n"
                )
            out = io.StringIO()
            try:
                os.chdir(tmp)
                with redirect_stdout(out):
                    sync()
            finally:
                os.chdir(cwd)

        self.assertIn("Duplicate Issue ID 'E01-ISS-01'", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
