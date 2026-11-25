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
    fenced_line_flags,
    find_block_bounds,
    is_closed_sprint,
    parse_markdown_table,
    render_metrics_table,
    render_velocity_summary,
    replace_block,
    sync,
)

SUMMARY_MARKER = "## Time & Velocity Summary"
METRICS_MARKER = "## Metrics"


class ParseMarkdownTableTests(unittest.TestCase):
    """BUG-01: a missing or misplaced separator row must not silently drop
    the first real data row. parse_markdown_table() used to always treat
    the line right after the header as the separator, regardless of
    whether it actually looked like one."""

    def test_missing_separator_still_reads_first_row(self):
        """RED for BUG-01: no '| :--- | ... |' row after the header at all
        -- every data row must still be read, none skipped."""
        lines = [
            "| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |\n",
            "| E04-ISS-01 | E-04 | Title one | DONE | 0.5h | 0.5h | - | n |\n",
            "| E04-ISS-02 | E-04 | Title two | TODO | 1.0h | - | - | n |\n",
            "\n",
        ]
        _, _, rows = parse_markdown_table(lines, "| ID |")
        ids = [cells[0].strip() for _, cells in rows]
        self.assertEqual(ids, ["E04-ISS-01", "E04-ISS-02"])

    def test_standard_separator_is_skipped_not_read_as_data(self):
        """A real '| :--- | ... |' separator row must still be excluded
        from the data rows (no regression on the normal case)."""
        lines = [
            "| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |\n",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n",
            "| E04-ISS-01 | E-04 | Title one | DONE | 0.5h | 0.5h | - | n |\n",
            "\n",
        ]
        _, _, rows = parse_markdown_table(lines, "| ID |")
        ids = [cells[0].strip() for _, cells in rows]
        self.assertEqual(ids, ["E04-ISS-01"])

    def test_separator_misplaced_after_data_is_not_read_as_data(self):
        """Regression for the exact failure mode: an Edit tool inserted new
        rows directly after the header, pushing the real separator below
        the data instead of removing it. The separator-shaped row must
        still be excluded wherever it lands; no real row may be dropped."""
        lines = [
            "| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |\n",
            "| E04-ISS-01 | E-04 | Title one | DONE | 0.5h | 0.5h | - | n |\n",
            "| E04-ISS-02 | E-04 | Title two | TODO | 1.0h | - | - | n |\n",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n",
            "\n",
        ]
        _, _, rows = parse_markdown_table(lines, "| ID |")
        ids = [cells[0].strip() for _, cells in rows]
        self.assertEqual(ids, ["E04-ISS-01", "E04-ISS-02"])


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
        """Test 3: nothing below the marker -> clean replace, no IndexError.

        The block now ends with its end sentinel plus a trailing blank line
        (finding 5), so '- new' is the last *content* line, not the last line.
        """
        lines = ["# Sprint 02\n", "\n", "## Time & Velocity Summary\n", "- old\n"]
        new_block = ["## Time & Velocity Summary\n", "- new\n"]

        result = replace_block(lines, SUMMARY_MARKER, new_block)

        self.assertIn("- new\n", result)
        self.assertNotIn("- old\n", result)
        self.assertIn("# Sprint 02\n", result)
        self.assertEqual(result[-1], "\n", "block must end with a blank separator")
        content = [ln for ln in result if ln.strip() and not ln.startswith("<!--")]
        self.assertEqual(content[-1], "- new\n")


class CodeReviewRegressionTests(unittest.TestCase):
    """Regressions for the five correctness findings that reopened E03-ISS-01.
    Each of these failed against the first implementation."""

    def test_subsection_below_block_survives(self):
        """Finding 1: a '### ' sub-section below the block must NOT be deleted.
        The old boundary check only matched column-0 '## '."""
        lines = [
            "## Time & Velocity Summary\n",
            "- old\n",
            "\n",
            "### Carryover Notes\n",
            "- carry E97-ISS-02 into sprint 98\n",
        ]
        result = replace_block(lines, "## Time & Velocity Summary", ["## Time & Velocity Summary\n", "- new\n"])
        joined = "".join(result)

        self.assertIn("### Carryover Notes", joined)
        self.assertIn("- carry E97-ISS-02 into sprint 98", joined)

    def test_h1_section_below_block_survives(self):
        """Finding 1 (second shape): a '# ' h1 below the block must survive."""
        lines = ["## Metrics\n", "| old |\n", "\n", "# Appendix\n", "- keep me\n"]
        result = replace_block(lines, "## Metrics", ["## Metrics\n", "| new |\n"])
        joined = "".join(result)

        self.assertIn("# Appendix", joined)
        self.assertIn("- keep me", joined)

    def test_indented_marker_mention_is_not_a_block_start(self):
        """Finding 2: an indented prose mention must not match as block start,
        which previously produced two disagreeing Metrics tables."""
        lines = [
            "# Sprint 02\n",
            "  ## Metrics  <- indented mention, not a heading\n",
            "\n",
            "## Metrics\n",
            "| **Total Hours** | 999.0h | 999.0h |\n",
        ]
        result = replace_block(lines, "## Metrics", ["## Metrics\n", "| **Total Hours** | 1.0h | 1.0h |\n"])
        joined = "".join(result)

        self.assertIn("  ## Metrics  <- indented mention, not a heading", joined)
        self.assertNotIn("999.0h", joined)
        self.assertEqual(joined.count("| **Total Hours** |"), 1)

    def test_fenced_marker_is_ignored(self):
        """Finding 3: a '## ' line inside a ``` fence is an example, not a
        boundary, and must not terminate the section or match as a start."""
        lines = [
            "## Time & Velocity Summary\n",
            "- old\n",
            "```\n",
            "## Metrics\n",
            "```\n",
            "## Pull Requests\n",
            "| E03-ISS-01 | #4 |\n",
        ]
        result = replace_block(lines, "## Time & Velocity Summary", ["## Time & Velocity Summary\n", "- new\n"])
        joined = "".join(result)

        self.assertIn("## Pull Requests", joined)
        self.assertIn("| E03-ISS-01 | #4 |", joined)
        self.assertEqual(joined.count("```"), 0, "fence should have been replaced with the block, not orphaned")

    def test_fenced_line_flags_marks_fence_interior(self):
        """Helper check for finding 3."""
        lines = ["a\n", "```\n", "## inside\n", "```\n", "b\n"]
        self.assertEqual(fenced_line_flags(lines), [False, True, True, True, False])

    def test_trailing_blank_separates_following_heading(self):
        """Finding 5: the block must end with a blank line so the next heading
        is never glued onto the last bullet."""
        lines = [
            "## Time & Velocity Summary\n",
            "- old\n",
            "\n",
            "## Pull Requests\n",
        ]
        result = replace_block(
            lines,
            "## Time & Velocity Summary",
            render_velocity_summary(total_est=1.0, total_cut=0.0, total_actual=1.0,
                                    done_count=1, active_count=1, cut_count=0),
        )
        pr_idx = result.index("## Pull Requests\n")
        self.assertEqual(result[pr_idx - 1], "\n", "no blank line before the following heading")

    def test_cut_hours_reported_on_own_row(self):
        """Finding 6: Planned and Actual must share one basis; cut work gets
        its own row instead of inflating Actual past Planned."""
        block = render_metrics_table(
            total_est=2.0, total_actual_active=1.0,
            total_cut=4.0, total_actual_cut=3.0,
            active_count=1, done_count=1, cut_count=1,
        )
        text = "".join(block)

        self.assertIn("| **Total Hours** | 2.0h | 1.0h |", text)
        self.assertIn("| **Cut Hours** | 4.0h | 3.0h |", text)
        self.assertIn("| **Issues Cut** | — | 1 |", text)
        self.assertNotIn("| **Issues Cut** | 0 |", text)

    def test_closed_sprint_is_detected(self):
        """Finding 4: a CLOSED sprint header is recognised as frozen."""
        closed = ["# Sprint 01\n", "- **Status:** CLOSED\n", "\n", "## Planned Issues\n"]
        active = ["# Sprint 02\n", "- **Status:** ACTIVE\n", "\n", "## Planned Issues\n"]
        self.assertTrue(is_closed_sprint(closed))
        self.assertFalse(is_closed_sprint(active))

    def test_closed_sprint_file_is_not_rewritten(self):
        """Finding 4: sync() must leave a CLOSED sprint board byte-identical."""
        closed_sprint = """# Sprint 97

- **Status:** CLOSED

## Planned Issues
| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E97-ISS-01 | E-97 | Done issue | DONE | 1.0h | 1.0h | - | - |

## Metrics
| Metric | Planned | Actual |
| :--- | :--- | :--- |
| **Total Hours** | 111.0h | 111.0h |

### Carryover Notes
- this must survive untouched
"""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            sprints_dir = os.path.join(tmp, ".solorail", "sprints")
            os.makedirs(sprints_dir)
            sprint_path = os.path.join(sprints_dir, "sprint-97.md")
            with open(sprint_path, "w", encoding="utf-8") as f:
                f.write(closed_sprint)
            try:
                os.chdir(tmp)
                sync()
            finally:
                os.chdir(original_cwd)
            with open(sprint_path, "r", encoding="utf-8") as f:
                result = f.read()

        self.assertEqual(result, closed_sprint, "CLOSED sprint board was modified")

    def test_sentinels_are_written_and_reused(self):
        """Sentinels replace the heading heuristic: after one sync the block is
        delimited by comments, and a second sync targets those, not the heading."""
        lines = ["## Metrics\n", "| old |\n"]
        once = replace_block(lines, "## Metrics", ["## Metrics\n", "| new |\n"])
        joined = "".join(once)

        self.assertIn("<!-- solorail:metrics:start -->", joined)
        self.assertIn("<!-- solorail:metrics:end -->", joined)

        bounds = find_block_bounds(once, "## Metrics", "metrics")
        self.assertIsNotNone(bounds)

        twice = replace_block(once, "## Metrics", ["## Metrics\n", "| newer |\n"])
        twice_joined = "".join(twice)
        self.assertEqual(twice_joined.count("<!-- solorail:metrics:start -->"), 1)
        self.assertIn("| newer |", twice_joined)
        self.assertNotIn("| new |", twice_joined)


class SentinelMigrationTests(unittest.TestCase):
    def test_orphaned_sentinel_from_rename_is_swept(self):
        """A sentinel written under a previous block name must not be stranded
        above the heading when the block name changes."""
        lines = [
            "<!-- solorail:time-&-velocity-summary:start -->\n",
            "## Time & Velocity Summary\n",
            "- old\n",
            "<!-- solorail:time-&-velocity-summary:end -->\n",
        ]
        result = replace_block(
            lines, "## Time & Velocity Summary",
            ["## Time & Velocity Summary\n", "- new\n"],
            block_name="velocity-summary",
        )
        joined = "".join(result)

        self.assertNotIn("time-&-velocity-summary", joined)
        self.assertEqual(joined.count("<!-- solorail:velocity-summary:start -->"), 1)
        self.assertEqual(joined.count("<!-- solorail:velocity-summary:end -->"), 1)

    def test_repeated_sync_is_idempotent(self):
        """Syncing twice must not duplicate sentinels or blocks."""
        lines = ["# Sprint 02\n", "\n", "## Metrics\n", "| old |\n"]
        once = replace_block(lines, "## Metrics", ["## Metrics\n", "| v |\n"], block_name="metrics")
        twice = replace_block(once, "## Metrics", ["## Metrics\n", "| v |\n"], block_name="metrics")

        self.assertEqual("".join(once), "".join(twice))


class RenderMetricsTableTests(unittest.TestCase):
    def test_maps_columns_per_contract(self):
        """Test 4: Planned column = planned values, Actual column = measured."""
        block = render_metrics_table(
            total_est=12.0, total_actual_active=0.0,
            total_cut=0.0, total_actual_cut=0.0,
            active_count=8, done_count=0, cut_count=0,
        )
        text = "".join(block)

        self.assertIn("## Metrics\n", text)
        self.assertIn("| **Total Hours** | 12.0h | 0.0h |", text)
        self.assertIn("| **Issues Completed** | 8 | 0 |", text)
        self.assertIn("| **Issues Cut** | — | 0 |", text)

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
