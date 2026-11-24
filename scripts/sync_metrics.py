#!/usr/bin/env python3
"""Deterministic metrics synchronizer for SoloRail v2.7.3.

Parses active sprint boards (.solorail/sprints/sprint-*.md) and updates:
1. Each sprint file's 'Time & Velocity Summary' block.
2. .solorail/ROADMAP.md 'Est. Hours' and 'Actual Hours' per Epic and HOTFIX.
"""

import glob
import os
import re

from solorail_state import (
    derive_sprint_status,
    is_carryover_row,
    is_closed_sprint,
    read_sprint_status,
    resolve_active_sprint,
    retro_path_for,
    write_sprint_status,
)


def parse_hours(val: str) -> float:
    cleaned = val.strip().lower().rstrip("h").strip()
    if not cleaned or cleaned == "-":
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def split_row(line: str) -> list[str]:
    parts = re.split(r'(?<!\\)\|', line)
    return [p.strip() for p in parts if p.strip()]


def parse_markdown_table(lines: list[str], header_marker: str):
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and header_marker in line:
            start_idx = i
            break
    if start_idx is None:
        return None, None, []

    rows = []
    end_idx = start_idx + 2
    for i in range(start_idx + 2, len(lines)):
        line = lines[i].strip()
        if not line.startswith("|"):
            break
        cells = split_row(line)
        rows.append((i, cells))
        end_idx = i + 1
    return start_idx, end_idx, rows


FENCE = "```"
HEADING_RE = re.compile(r"^#{1,6} ")


def sentinel_tags(block_name: str) -> tuple[str, str]:
    """Return the (start, end) sentinel comments delimiting a managed block.

    Sentinels replace the old '## '-prefix heuristic for locating a block.
    Heading-shape matching could not distinguish a real heading from an
    indented or fenced mention of one, and treated '### '/'# ' sections as
    non-boundaries -- so they were deleted along with the block.
    """
    return (
        f"<!-- solorail:{block_name}:start -->",
        f"<!-- solorail:{block_name}:end -->",
    )


def fenced_line_flags(lines: list[str]) -> list[bool]:
    """Mark each line that sits inside a ``` fenced code block.

    Markdown inside a fence is an example, not structure: a fenced '## Metrics'
    must never be mistaken for the real heading, in either direction.
    """
    flags = [False] * len(lines)
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith(FENCE):
            flags[i] = True
            in_fence = not in_fence
            continue
        flags[i] = in_fence
    return flags


def is_orphan_sentinel(line: str) -> bool:
    """True for any SoloRail sentinel comment line.

    Used to sweep up sentinels written under a previous block name during the
    heading-fallback path, so renames do not leave stray comments behind.
    """
    stripped = line.strip()
    return stripped.startswith("<!-- solorail:") and stripped.endswith("-->")


def find_block_bounds(lines: list[str], marker: str, block_name: str):
    """Locate the managed block as a half-open [start, end) line range.

    Prefers the sentinel pair. Falls back to the literal heading for files
    written before sentinels existed, bounded by the next heading of ANY level
    so sub-sections below the block are preserved. Returns None when absent.
    """
    start_tag, end_tag = sentinel_tags(block_name)

    start_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == start_tag:
            start_idx = i
        elif stripped == end_tag and start_idx is not None:
            # Absorb the blank separator that follows the block; wrap_block
            # re-adds exactly one, so repeated syncs stay idempotent instead
            # of accumulating a blank line per run.
            end = i + 1
            while end < len(lines) and not lines[end].strip():
                end += 1
            return start_idx, end

    fenced = fenced_line_flags(lines)

    # Migration path: exact heading match at column 0, outside any fence.
    for i, line in enumerate(lines):
        if fenced[i] or line.rstrip("\n").rstrip() != marker:
            continue

        # Absorb orphaned sentinels left by an earlier run under a different
        # block name, so a rename does not strand a stray comment above the
        # heading or below the block.
        start = i
        while start > 0 and is_orphan_sentinel(lines[start - 1]):
            start -= 1

        end = len(lines)
        for j in range(i + 1, len(lines)):
            if not fenced[j] and HEADING_RE.match(lines[j]):
                end = j
                break
        while end < len(lines) and is_orphan_sentinel(lines[end]):
            end += 1

        return start, end

    return None


def wrap_block(block_name: str, content: list[str]) -> list[str]:
    """Wrap rendered content in its sentinel pair, with a trailing blank line.

    The trailing blank keeps a following heading from being glued onto the last
    line of the block.
    """
    start_tag, end_tag = sentinel_tags(block_name)
    return [f"{start_tag}\n"] + content + [f"{end_tag}\n", "\n"]


def replace_block(lines: list[str], marker: str, new_block: list[str],
                  block_name: str | None = None) -> list[str]:
    """Replace the managed block identified by `marker` with `new_block`,
    preserving everything else in the file.

    Never truncates: content below the block -- headings of any level, prose,
    or further managed blocks -- is retained. When the block is absent it is
    inserted before the first heading that follows `marker`'s expected
    position, or appended at EOF.
    """
    name = block_name or marker.lstrip("#").strip().lower().replace(" ", "-")
    bounds = find_block_bounds(lines, marker, name)
    wrapped = wrap_block(name, new_block)

    if bounds is None:
        if lines and not lines[-1].endswith("\n"):
            lines = lines[:-1] + [lines[-1] + "\n"]
        return lines + ["\n"] + wrapped

    start_idx, end_idx = bounds
    return lines[:start_idx] + wrapped + lines[end_idx:]


def render_metrics_table(total_est: float, total_actual_active: float,
                         total_cut: float, total_actual_cut: float,
                         active_count: int, done_count: int,
                         cut_count: int) -> list[str]:
    """Render the '## Metrics' block.

    'Total Hours' compares active-only estimate against active-only actual, so
    both columns share one basis. Cut work is reported on its own row rather
    than folded into the Actual column, which previously let Actual exceed
    Planned after a /solorail:pivot with no visible explanation.

    Total Hours actual + Cut Hours actual reconciles exactly to the velocity
    summary's 'Total Actual'.
    """
    return [
        "## Metrics\n",
        "| Metric | Planned | Actual |\n",
        "| :--- | :--- | :--- |\n",
        f"| **Total Hours** | {total_est:.1f}h | {total_actual_active:.1f}h |\n",
        f"| **Cut Hours** | {total_cut:.1f}h | {total_actual_cut:.1f}h |\n",
        f"| **Issues Completed** | {active_count} | {done_count} |\n",
        f"| **Issues Cut** | — | {cut_count} |\n",
    ]


def render_velocity_summary(total_est: float, total_cut: float,
                            total_actual: float, done_count: int,
                            active_count: int, cut_count: int) -> list[str]:
    """Render the '## Time & Velocity Summary' block.

    Format is kept byte-identical to the pre-E03-ISS-01 output so downstream
    readers (eval_metrics.py, the status skill) keep parsing it.
    """
    return [
        "## Time & Velocity Summary\n",
        f"- **Total Estimated (Active):** {total_est:.1f}h\n",
        f"- **Total Cut:** {total_cut:.1f}h\n",
        f"- **Total Actual:** {total_actual:.1f}h\n",
        f"- **Completed / Total Active Issues:** {done_count} / {active_count}\n",
        f"- **Scope Changes (Cut Issues):** {cut_count}\n",
    ]


def sync():
    solorail_dir = os.path.join(os.getcwd(), ".solorail")
    if not os.path.exists(solorail_dir):
        return

    sprint_files = sorted(glob.glob(os.path.join(solorail_dir, "sprints", "sprint-*.md")))
    roadmap_path = os.path.join(solorail_dir, "ROADMAP.md")

    epic_est = {}
    epic_act = {}
    seen_issues = set()
    # One entry per issue ID, so an issue carried across sprints is counted
    # once in the ROADMAP epic totals.
    issue_epic_rows = {}
    valid_statuses = {"TODO", "IN_PROGRESS", "BLOCKED", "DONE", "CUT"}
    active_sprint_path = resolve_active_sprint(
        os.path.join(solorail_dir, "sprints")
    )

    for sp_path in sprint_files:
        with open(sp_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        is_active_sprint = sp_path == active_sprint_path

        _, _, rows = parse_markdown_table(lines, "| ID |")
        total_est_active = 0.0
        total_cut = 0.0
        total_actual = 0.0
        total_actual_active = 0.0
        total_actual_cut = 0.0
        done_count = 0
        active_count = 0
        cut_count = 0

        for row_idx, cells in rows:
            if len(cells) < 6:
                continue

            issue_id = cells[0].strip()
            epic_id = cells[1].strip()
            status = cells[3].strip().upper()
            est = parse_hours(cells[4])
            act = parse_hours(cells[5])

            if issue_id == "-" or not status:
                continue

            # A carried-over issue legitimately appears on two boards: as a
            # TODO/BLOCKED row on the sprint it came from, and as a carried row
            # on its successor. Warning about that is a false positive, and
            # noisy false warnings train people to ignore real ones.
            raw_row = lines[row_idx] if row_idx < len(lines) else ""
            carried = is_carryover_row(raw_row)
            if issue_id in seen_issues and not carried:
                print(f"WARNING [SoloRail]: Duplicate Issue ID '{issue_id}' found in {os.path.basename(sp_path)}")
            seen_issues.add(issue_id)

            if status not in valid_statuses:
                print(f"WARNING [SoloRail]: Invalid status '{status}' for {issue_id}")

            if status == "DONE" and act == 0.0:
                print(f"WARNING [SoloRail]: Issue {issue_id} is DONE but has 0.0h actual time logged.")

            if status == "CUT":
                total_cut += est
                total_actual_cut += act
                cut_count += 1
            else:
                total_est_active += est
                total_actual_active += act
                active_count += 1
                if status == "DONE":
                    done_count += 1

            total_actual += act

            # Per-sprint totals above count every row on this board -- a
            # carried row genuinely is part of this sprint's planned work.
            # Epic totals must NOT: an issue carried forward appears on two
            # boards, which measurably doubled a 10.0h issue to 20.0h in
            # ROADMAP.md. Keep one entry per issue ID, preferring the ACTIVE
            # sprint's row since that is the live one.
            existing = issue_epic_rows.get(issue_id)
            if existing is None or (is_active_sprint and not existing["from_active"]):
                issue_epic_rows[issue_id] = {
                    "epic_id": epic_id,
                    "status": status,
                    "est": est,
                    "act": act,
                    "from_active": is_active_sprint,
                }

        # Derive the sprint's own Status before the freeze check, so a sprint
        # that just became closeable gets its header written once and is frozen
        # from the next sync onward (E03-ISS-03). The field previously had no
        # writer at all and was edited by hand during Sprint 01's evolve.
        derived = derive_sprint_status(
            lines, os.path.exists(retro_path_for(sp_path))
        )
        if derived and read_sprint_status(lines) != derived:
            lines = write_sprint_status(lines, derived)
            with open(sp_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(
                f"SoloRail closed {os.path.basename(sp_path)}: "
                "all issues DONE/CUT and retro present"
            )

        # A CLOSED sprint is frozen history. Its rows still feed the ROADMAP
        # epic totals above, but the file itself is never rewritten -- this
        # hook fires on every Edit/Write, so silently editing closed sprint
        # boards would mutate committed history with no diff review.
        if is_closed_sprint(lines):
            print(f"SoloRail skipped {os.path.basename(sp_path)}: Status CLOSED (frozen)")
            continue

        # Both blocks are rendered from the same computed totals, so they can
        # never disagree (ADR-004).
        lines = replace_block(
            lines,
            "## Metrics",
            render_metrics_table(
                total_est=total_est_active,
                total_actual_active=total_actual_active,
                total_cut=total_cut,
                total_actual_cut=total_actual_cut,
                active_count=active_count,
                done_count=done_count,
                cut_count=cut_count,
            ),
            block_name="metrics",
        )
        lines = replace_block(
            lines,
            "## Time & Velocity Summary",
            render_velocity_summary(
                total_est=total_est_active,
                total_cut=total_cut,
                total_actual=total_actual,
                done_count=done_count,
                active_count=active_count,
                cut_count=cut_count,
            ),
            block_name="velocity-summary",
        )

        with open(sp_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"SoloRail synced {os.path.basename(sp_path)}: Est={total_est_active:.1f}h, Act={total_actual:.1f}h, Done={done_count}/{active_count}")

    # Aggregate epic totals from the deduped per-issue map, not inline during
    # the row scan, so each issue contributes exactly once no matter how many
    # boards carry it.
    for row in issue_epic_rows.values():
        epic_id = row["epic_id"]
        if row["status"] != "CUT":
            epic_est[epic_id] = epic_est.get(epic_id, 0.0) + row["est"]
        epic_act[epic_id] = epic_act.get(epic_id, 0.0) + row["act"]

    if os.path.exists(roadmap_path):
        with open(roadmap_path, "r", encoding="utf-8") as f:
            r_lines = f.readlines()

        _, _, r_rows = parse_markdown_table(r_lines, "| Epic ID |")
        for line_idx, cells in r_rows:
            if len(cells) < 6:
                continue
            eid = cells[0].strip()
            est_val = epic_est.get(eid, parse_hours(cells[3]))
            act_val = epic_act.get(eid, parse_hours(cells[4]))
            cells[3] = f"{est_val:.1f}h"
            cells[4] = f"{act_val:.1f}h"
            r_lines[line_idx] = "| " + " | ".join(cells) + " |\n"

        with open(roadmap_path, "w", encoding="utf-8") as f:
            f.writelines(r_lines)
        print("SoloRail synced ROADMAP.md")


if __name__ == "__main__":
    sync()
