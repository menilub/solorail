#!/usr/bin/env python3
"""Unit tests for the metric-block rendering and non-destructive splice helpers
in sync_metrics.py (SoloRail E03-ISS-01).

Stdlib-only (unittest). Run with:
    python3 scripts/test_sync_metrics.py

All filesystem assertions run against temp-directory fixtures, never against the
live .solorail/sprints/ files (sync_metrics.py runs as a PostToolUse hook, so
pointing these tests at real state would corrupt sprint history).
"""

import os
import tempfile
import unittest

from sync_metrics import (
    render_metrics_table,
    render_velocity_summary,
    replace_block,
    sync,
)

SUMMARY_MARKER = "## Time & Velocity Summary"
METRICS_MARKER = "## Metrics"


class ReplaceBlockTests(unittest.TestCase):
    def test_preserves_content_below_next_heading(self):
        """Test 1 (RED for the truncation bug): a section below the replaced
        block survives verbatim."""
        lines = [
            "# Sprint 02\n",
            "\n",
            "## Time & Velocity Summary\n",
            "- **Total Actual:** 0.0h\n",
            "\n",
            "## Pull Requests\n",
            "| Issue | PR |\n",
            "| E03-ISS-01 | #4 |\n",
        ]
        new_block = ["## Time & Velocity Summary\n", "- **Total Actual:** 1.5h\n", "\n"]

        result = replace_block(lines, SUMMARY_MARKER, new_block)

        self.assertIn("## Pull Requests\n", result)
        self.assertIn("| E03-ISS-01 | #4 |\n", result)
        self.assertIn("- **Total Actual:** 1.5h\n", result)
        self.assertNotIn("- **Total Actual:** 0.0h\n", result)

    def test_appends_when_marker_absent(self):
        """Test 2: with no such heading, the block is appended and existing
        content is untouched."""
        lines = ["# Sprint 02\n", "\n", "## Planned Issues\n", "| ID |\n"]
        new_block = ["## Metrics\n", "| Metric | Planned | Actual |\n", "\n"]

        result = replace_block(lines, METRICS_MARKER, new_block)

        self.assertIn("## Planned Issues\n", result)
        self.assertIn("| ID |\n", result)
        self.assertIn("## Metrics\n", result)
        self.assertGreater(result.index("## Metrics\n"), result.index("| ID |\n"))

    def test_handles_marker_as_final_section(self):
        """Test 3: nothing below the marker -> clean replace, no IndexError."""
        lines = ["# Sprint 02\n", "\n", "## Time & Velocity Summary\n", "- old\n"]
        new_block = ["## Time & Velocity Summary\n", "- new\n"]

        result = replace_block(lines, SUMMARY_MARKER, new_block)

        self.assertEqual(result[-1], "- new\n")
        self.assertNotIn("- old\n", result)
        self.assertIn("# Sprint 02\n", result)


class RenderMetricsTableTests(unittest.TestCase):
    def test_maps_columns_per_contract(self):
        """Test 4: Planned column = planned values, Actual column = measured."""
        block = render_metrics_table(
            total_est=12.0, total_actual=0.0, active_count=8, done_count=0, cut_count=0
        )
        text = "".join(block)

        self.assertIn("## Metrics\n", text)
        self.assertIn("| **Total Hours** | 12.0h | 0.0h |", text)
        self.assertIn("| **Issues Completed** | 8 | 0 |", text)
        self.assertIn("| **Issues Cut** | 0 | 0 |", text)

    def test_summary_format_is_unchanged(self):
        """Guard: the existing summary format must stay byte-identical so no
        downstream reader breaks."""
        block = render_velocity_summary(
            total_est=9.0,
            total_cut=0.0,
            total_actual=4.5,
            done_count=7,
            active_count=7,
            cut_count=0,
        )
        text = "".join(block)

        self.assertIn("- **Total Estimated (Active):** 9.0h\n", text)
        self.assertIn("- **Total Cut:** 0.0h\n", text)
        self.assertIn("- **Total Actual:** 4.5h\n", text)
        self.assertIn("- **Completed / Total Active Issues:** 7 / 7\n", text)
        self.assertIn("- **Scope Changes (Cut Issues):** 0\n", text)


class EndToEndSyncTests(unittest.TestCase):
    def test_both_blocks_agree_after_sync(self):
        """Test 5: a stale ## Metrics table is corrected and both blocks report
        the same totals."""
        stale_sprint = """# Sprint 99

- **Capacity:** 20.0h

## Planned Issues
| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E99-ISS-01 | E-99 | First issue | DONE | 2.0h | 1.5h | - | - |
| E99-ISS-02 | E-99 | Second issue | TODO | 3.0h | - | - | - |

## Metrics
| Metric | Planned | Actual |
| :--- | :--- | :--- |
| **Total Hours** | 999.0h | 999.0h |
| **Issues Completed** | 999 | 999 |
| **Issues Cut** | 999 | 999 |

## Time & Velocity Summary
- **Total Estimated (Active):** 0.0h
"""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = os.path.join(tmp, ".solorail", "sprints")
            os.makedirs(sprints_dir)
            sprint_path = os.path.join(sprints_dir, "sprint-99.md")
            with open(sprint_path, "w", encoding="utf-8") as f:
                f.write(stale_sprint)

            try:
                os.chdir(tmp)
                sync()
            finally:
                os.chdir(original_cwd)

            with open(sprint_path, "r", encoding="utf-8") as f:
                result = f.read()

        # Stale placeholders are gone.
        self.assertNotIn("999", result)
        # Both blocks report the same computed totals: 5.0h est, 1.5h actual, 1/2 done.
        self.assertIn("| **Total Hours** | 5.0h | 1.5h |", result)
        self.assertIn("| **Issues Completed** | 2 | 1 |", result)
        self.assertIn("- **Total Estimated (Active):** 5.0h\n", result)
        self.assertIn("- **Total Actual:** 1.5h\n", result)
        self.assertIn("- **Completed / Total Active Issues:** 1 / 2\n", result)

    def test_sync_preserves_section_below_summary(self):
        """Regression for the EOF truncation: a section below the summary must
        survive a real sync() call."""
        sprint_with_pr_section = """# Sprint 98

## Planned Issues
| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E98-ISS-01 | E-98 | Only issue | DONE | 1.0h | 1.0h | - | - |

## Time & Velocity Summary
- **Total Estimated (Active):** 0.0h

## Pull Requests
| Issue | PR |
| :--- | :--- |
| E98-ISS-01 | #42 |
"""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = os.path.join(tmp, ".solorail", "sprints")
            os.makedirs(sprints_dir)
            sprint_path = os.path.join(sprints_dir, "sprint-98.md")
            with open(sprint_path, "w", encoding="utf-8") as f:
                f.write(sprint_with_pr_section)

            try:
                os.chdir(tmp)
                sync()
            finally:
                os.chdir(original_cwd)

            with open(sprint_path, "r", encoding="utf-8") as f:
                result = f.read()

        self.assertIn("## Pull Requests", result)
        self.assertIn("| E98-ISS-01 | #42 |", result)
        self.assertIn("- **Total Actual:** 1.0h\n", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
