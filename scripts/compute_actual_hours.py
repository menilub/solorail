#!/usr/bin/env python3
"""Automatic Actual-hours computation for SoloRail's verify-issue (E02-ISS-03).

Computes real elapsed wall-clock time between an Issue's `Started At`
(recorded in the sprint board by architect-issue) and verification, read
from the system clock -- not a self-reported guess. Confirmed (2026-11-24)
over a file-mtime-delta alternative: this intentionally counts idle time
between conversation turns, per ADR-003 in .solorail/CONTEXT.md.

Stdlib only (glob, datetime), no third-party dependencies.
"""

import os
import sys
from datetime import datetime

from solorail_state import list_sprint_files, resolve_active_sprint

MIN_HOURS = 0.5
_DATE_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d")


def _parse_started_at(raw: str):
    """Parse a 'Started At' cell. Returns a datetime, or None if it's the
    placeholder '-' or otherwise unparseable."""
    value = (raw or "").strip()
    if not value or value == "-":
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _find_started_at(issue_id: str, sprints_dir: str):
    """Find `issue_id`'s Started At cell across the sprint boards.

    Searches the ACTIVE sprint first, then every other board. Previously this
    read only the last filename, so an issue on any other board was invisible
    and the caller fell back to a default -- silently corrupting the hours
    ADR-003 makes authoritative. An issue ID is globally unique, so searching
    every board is safe and finds a carried-over issue too (E03-ISS-02).
    """
    search_order = _sprint_search_order(sprints_dir)
    if not search_order:
        return None

    for sprint_path in search_order:
        found = _scan_sprint_for_issue(sprint_path, issue_id)
        if found is not None:
            return found
    return None


def _sprint_search_order(sprints_dir: str) -> list[str]:
    """Sprint board paths with the ACTIVE one first."""
    all_sprints = list_sprint_files(sprints_dir)
    if not all_sprints:
        return []
    active = resolve_active_sprint(sprints_dir)
    if active and active in all_sprints:
        return [active] + [p for p in all_sprints if p != active]
    return all_sprints


def _scan_sprint_for_issue(sprint_path: str, issue_id: str):
    """The Started At cell for `issue_id` on one board, or None."""
    with open(sprint_path, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            # Table row: ['', ID, Epic, Issue, Status, Est, Actual, Started At, Notes, '']
            if len(parts) >= 8 and parts[1] == issue_id:
                return parts[7]
    return None


def compute_actual_hours(issue_id: str, sprints_dir: str, now: datetime = None):
    """Compute Actual hours for `issue_id` from real elapsed wall-clock time
    between its 'Started At' (in the latest sprint-*.md under `sprints_dir`)
    and `now` (default: datetime.now()).

    Rounds to the nearest 0.5h, floored at a 0.5h minimum (never negative).
    Returns None if the issue, the sprints directory, or a parseable
    Started At isn't found.
    """
    raw_started_at = _find_started_at(issue_id, sprints_dir)
    if raw_started_at is None:
        return None

    started_at = _parse_started_at(raw_started_at)
    if started_at is None:
        return None

    moment = now if now is not None else datetime.now()
    elapsed_hours = (moment - started_at).total_seconds() / 3600.0

    rounded = round(elapsed_hours * 2) / 2
    return max(rounded, MIN_HOURS)


def main() -> int:
    """CLI entry point: `python3 scripts/compute_actual_hours.py <ISSUE-ID>`.
    Prints the computed hours (e.g. "1.5") to stdout and exits 0, or prints
    ERROR to stderr and exits 1 if not computable.
    """
    if len(sys.argv) < 2:
        print("ERROR: usage: compute_actual_hours.py <ISSUE-ID>", file=sys.stderr)
        return 1

    issue_id = sys.argv[1]
    sprints_dir = os.path.join(os.getcwd(), ".solorail", "sprints")
    hours = compute_actual_hours(issue_id, sprints_dir)
    if hours is None:
        print(
            f"ERROR: could not compute Actual hours for '{issue_id}' "
            f"(issue not found or Started At unparseable).",
            file=sys.stderr,
        )
        return 1

    print(hours)
    return 0


if __name__ == "__main__":
    sys.exit(main())
