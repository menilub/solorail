#!/usr/bin/env python3
"""Unit tests for PR recording and state refresh (SoloRail E03-ISS-05).

`gh` is mocked in every test: shelling out to it is the main hazard in this
issue, and a test suite that needs network or auth is not a test suite.

Stdlib-only (unittest). Run with:
    python3 scripts/test_pr_state.py
"""

import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from pr_state import (
    normalize_pr_ref,
    parse_pr_rows,
    query_pr_state,
    record_pr,
    refresh_pr_states,
    render_pr_table,
)

BOARD = """# Sprint 42

- **Status:** ACTIVE

## Planned Issues
| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E42-ISS-01 | E-42 | First | DONE | 2.0h | 1.5h | - | - |
| E42-ISS-02 | E-42 | Second | DONE | 1.0h | 1.0h | - | - |

<!-- solorail:metrics:start -->
## Metrics
| Metric | Planned | Actual |
| :--- | :--- | :--- |
| **Total Hours** | 0.0h | 0.0h |
<!-- solorail:metrics:end -->

<!-- solorail:velocity-summary:start -->
## Time & Velocity Summary
- **Total Actual:** 0.0h
<!-- solorail:velocity-summary:end -->
"""


def _result(returncode=0, stdout=""):
    class R:
        pass

    r = R()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = ""
    return r


def write_board(tmp: str, content: str = BOARD, status: str = None) -> str:
    sprints = os.path.join(tmp, ".solorail", "sprints")
    os.makedirs(sprints, exist_ok=True)
    if status:
        content = content.replace("- **Status:** ACTIVE", f"- **Status:** {status}")
    path = os.path.join(sprints, "sprint-42.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class NormalizePrRefTests(unittest.TestCase):
    def test_accepted_forms(self):
        """Test 1a."""
        for raw in ["#4", "4", "https://github.com/o/r/pull/4", "o/r#4"]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_pr_ref(raw), "#4")

    def test_rejected_forms(self):
        """Test 1b: a malformed ref must never be recorded as if valid."""
        for raw in ["abc", "", "#", "#-1", "-1", None, "pull/request"]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_pr_ref(raw), "")


class RecordPrTests(unittest.TestCase):
    def test_inserts_into_board_without_block(self):
        """Test 2: other content must survive."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_board(tmp)
            record_pr(path, "E42-ISS-01", "#4", state="OPEN")
            with open(path) as f:
                result = f.read()

        self.assertIn("## Pull Requests", result)
        self.assertIn("| E42-ISS-01 | #4 | OPEN |", result)
        self.assertIn("| E42-ISS-01 | E-42 | First | DONE", result)
        self.assertIn("## Metrics", result)
        self.assertIn("## Time & Velocity Summary", result)

    def test_is_idempotent_and_replaces(self):
        """Test 3."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_board(tmp)
            record_pr(path, "E42-ISS-01", "#4", state="OPEN")
            record_pr(path, "E42-ISS-01", "#4", state="OPEN")
            with open(path) as f:
                twice = f.read()
            self.assertEqual(twice.count("| E42-ISS-01 |"), 2,
                             "one issue row + one PR row")
            self.assertEqual(twice.count("<!-- solorail:pull-requests:start -->"), 1)

            record_pr(path, "E42-ISS-01", "#9", state="MERGED")
            with open(path) as f:
                replaced = f.read()

        self.assertIn("| E42-ISS-01 | #9 | MERGED |", replaced)
        self.assertNotIn("#4", replaced)

    def test_two_issues_can_share_one_pr(self):
        """Test 8: several issues may land in one PR, as on this branch."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_board(tmp)
            record_pr(path, "E42-ISS-01", "#4", state="OPEN")
            record_pr(path, "E42-ISS-02", "#4", state="OPEN")
            with open(path) as f:
                lines = f.readlines()

        rows = parse_pr_rows(lines)
        self.assertEqual(rows["E42-ISS-01"]["pr"], "#4")
        self.assertEqual(rows["E42-ISS-02"]["pr"], "#4")

    def test_survives_a_real_sync(self):
        """Test 4: the interaction E03-ISS-01 unblocked. Before that fix any
        section below the summary was deleted on the next sync."""
        from sync_metrics import sync

        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            path = write_board(tmp)
            record_pr(path, "E42-ISS-01", "#4", state="OPEN")
            try:
                os.chdir(tmp)
                sync()
            finally:
                os.chdir(cwd)
            with open(path) as f:
                result = f.read()

        self.assertIn("| E42-ISS-01 | #4 | OPEN |", result)
        self.assertIn("| **Total Hours** | 3.0h | 2.5h |", result)
        self.assertIn("- **Total Actual:** 2.5h", result)

    def test_refuses_closed_board(self):
        """Test 9: consistent with E03-ISS-01's frozen-history rule."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_board(tmp, status="CLOSED")
            with open(path) as f:
                before = f.read()

            with self.assertRaises(RuntimeError):
                record_pr(path, "E42-ISS-01", "#4", state="OPEN")

            with open(path) as f:
                self.assertEqual(f.read(), before)

    def test_malformed_ref_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_board(tmp)
            with self.assertRaises(ValueError):
                record_pr(path, "E42-ISS-01", "not-a-pr")


class RenderAndParseTests(unittest.TestCase):
    def test_rows_are_sorted_for_stable_diffs(self):
        block = "".join(render_pr_table({
            "E42-ISS-02": {"pr": "#5", "state": "OPEN"},
            "E42-ISS-01": {"pr": "#4", "state": "MERGED"},
        }))
        self.assertLess(block.index("E42-ISS-01"), block.index("E42-ISS-02"))

    def test_parse_empty_board_is_empty_dict(self):
        self.assertEqual(parse_pr_rows(BOARD.splitlines(keepends=True)), {})

    def test_parses_block_missing_its_start_sentinel(self):
        """Regression: a block damaged by an older truncating sync kept its
        heading and end sentinel but lost the start one. Requiring the start
        sentinel silently dropped every recorded row on the next write."""
        damaged = BOARD + (
            "\n## Pull Requests\n"
            "| Issue | PR | State |\n"
            "| :--- | :--- | :--- |\n"
            "| E42-ISS-01 | #4 | OPEN |\n"
            "| E42-ISS-02 | #7 | MERGED |\n"
            "<!-- solorail:pull-requests:end -->\n"
        )
        rows = parse_pr_rows(damaged.splitlines(keepends=True))

        self.assertEqual(rows["E42-ISS-01"], {"pr": "#4", "state": "OPEN"})
        self.assertEqual(rows["E42-ISS-02"], {"pr": "#7", "state": "MERGED"})

    def test_recording_into_a_damaged_block_preserves_existing_rows(self):
        damaged = BOARD + (
            "\n## Pull Requests\n"
            "| Issue | PR | State |\n"
            "| :--- | :--- | :--- |\n"
            "| E42-ISS-01 | #4 | OPEN |\n"
            "<!-- solorail:pull-requests:end -->\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = write_board(tmp, damaged)
            record_pr(path, "E42-ISS-02", "#4", state="OPEN")
            with open(path) as f:
                rows = parse_pr_rows(f.readlines())

        self.assertIn("E42-ISS-01", rows, "existing row must survive")
        self.assertIn("E42-ISS-02", rows)

    def test_does_not_read_past_the_next_section(self):
        trailing = BOARD + (
            "\n## Pull Requests\n"
            "| Issue | PR | State |\n"
            "| :--- | :--- | :--- |\n"
            "| E42-ISS-01 | #4 | OPEN |\n"
            "\n## Notes\n"
            "| E42-ISS-99 | #99 | OPEN |\n"
        )
        rows = parse_pr_rows(trailing.splitlines(keepends=True))
        self.assertIn("E42-ISS-01", rows)
        self.assertNotIn("E42-ISS-99", rows)


class QueryPrStateTests(unittest.TestCase):
    def test_parses_state(self):
        """Test 6."""
        with patch("pr_state.subprocess.run", return_value=_result(stdout='{"state":"MERGED"}')):
            self.assertEqual(query_pr_state("#4"), "MERGED")

    def test_returns_none_on_every_failure_mode(self):
        """Test 5: gh may be missing, unauthenticated, offline, or slow. None
        in every case -- never an exception, never a wrong state."""
        failures = [
            ("gh missing", {"side_effect": FileNotFoundError("gh")}),
            ("non-zero exit", {"return_value": _result(returncode=1, stdout="")}),
            ("timeout", {"side_effect": subprocess.TimeoutExpired("gh", 5)}),
            ("unparseable json", {"return_value": _result(stdout="not json")}),
            ("empty output", {"return_value": _result(stdout="")}),
            ("unexpected state", {"return_value": _result(stdout='{"state":"WEIRD"}')}),
            ("missing key", {"return_value": _result(stdout='{"other":1}')}),
            ("os error", {"side_effect": OSError("boom")}),
        ]
        for label, kwargs in failures:
            with self.subTest(label=label):
                with patch("pr_state.subprocess.run", **kwargs):
                    self.assertIsNone(query_pr_state("#4"), label)

    def test_rejects_malformed_ref_without_calling_gh(self):
        with patch("pr_state.subprocess.run", side_effect=AssertionError("must not call gh")):
            self.assertIsNone(query_pr_state("nonsense"))


class RefreshPrStatesTests(unittest.TestCase):
    def test_preserves_state_when_query_fails(self):
        """Test 7a."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_board(tmp)
            record_pr(path, "E42-ISS-01", "#4", state="OPEN")

            with patch("pr_state.query_pr_state", return_value=None):
                refresh_pr_states(path)

            with open(path) as f:
                rows = parse_pr_rows(f.readlines())

        self.assertEqual(rows["E42-ISS-01"]["state"], "OPEN")

    def test_updates_state_when_query_resolves(self):
        """Test 7b."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_board(tmp)
            record_pr(path, "E42-ISS-01", "#4", state="OPEN")

            with patch("pr_state.query_pr_state", return_value="MERGED"):
                updated = refresh_pr_states(path)

            with open(path) as f:
                rows = parse_pr_rows(f.readlines())

        self.assertEqual(rows["E42-ISS-01"]["state"], "MERGED")
        self.assertEqual(updated, {"E42-ISS-01": "MERGED"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
