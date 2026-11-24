#!/usr/bin/env python3
"""Generate the next SoloRail sprint board from a template (E03-ISS-04).

Sprint boards were hand-authored. Every consumer parses them by exact marker
match -- `| ID |`, `## Metrics`, `## Time & Velocity Summary`, the header
`Status:` line, and fixed column positions -- so a board that drifts is
*silently* un-synced: no error, just stale numbers. Generating from
`.solorail/sprints/_TEMPLATE.md` removes the hand-authoring step, and carrying
unfinished rows forward in code removes the other thing an agent had to
remember.

Usage:
    python3 scripts/next_sprint.py [--capacity 20.0h] [--weeks 2] [--force]
"""

import argparse
import os
import re
import sys
from datetime import date, timedelta

from solorail_state import (
    carryover_rows,
    list_sprint_files,
    read_sprint_status_file,
    reset_row_for_carryover,
    sprint_number,
)

TOKEN_RE = re.compile(r"\{\{[A-Z_]+\}\}")
TEMPLATE_NAME = "_TEMPLATE.md"


def next_sprint_number(sprints_dir: str) -> int:
    """Highest existing sprint number + 1; 1 when no sprints exist.

    Uses the numeric index, so sprint-09 plus sprint-10 yields 11 rather than
    the 10 a lexical sort would give.
    """
    existing = list_sprint_files(sprints_dir)
    if not existing:
        return 1
    return max(sprint_number(p) for p in existing) + 1


def render_template(template: str, number: int, start_date: str,
                    end_date: str, capacity: str,
                    carryover: list[str]) -> str:
    """Substitute every placeholder in the template.

    Raises ValueError if any {{TOKEN}} remains, so a template/generator
    mismatch fails loudly instead of writing a half-filled board that would
    then parse as valid-but-wrong.
    """
    rows = "".join(carryover)
    out = (
        template
        .replace("{{NUMBER}}", str(number))
        .replace("{{START_DATE}}", start_date)
        .replace("{{END_DATE}}", end_date)
        .replace("{{CAPACITY}}", capacity)
        .replace("{{CARRYOVER_ROWS}}", rows)
    )

    leftover = TOKEN_RE.findall(out)
    if leftover:
        raise ValueError(
            f"unsubstituted template tokens: {sorted(set(leftover))}"
        )
    return out


def collect_carryover(sprints_dir: str) -> list[str]:
    """Unfinished rows from every existing board, reset for the new sprint."""
    carried = []
    for sprint_path in list_sprint_files(sprints_dir):
        with open(sprint_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        origin = os.path.basename(sprint_path).removesuffix(".md")
        for row in carryover_rows(lines):
            carried.append(reset_row_for_carryover(row, origin=origin))
    return carried


def generate_next_sprint(solorail_dir: str, capacity: str = "20.0h",
                         weeks: int = 2, today: date = None,
                         force: bool = False) -> str:
    """Write the next sprint board and return its path.

    Refuses when a sprint is still ACTIVE unless force=True: two ACTIVE boards
    is exactly the ambiguous state resolve_active_sprint has to warn about.
    Refuses to overwrite an existing board -- both are hard failures, because a
    clobbered sprint board is unrecoverable tracked state.
    """
    sprints_dir = os.path.join(solorail_dir, "sprints")
    template_path = os.path.join(sprints_dir, TEMPLATE_NAME)
    if not os.path.exists(template_path):
        raise RuntimeError(f"missing sprint template: {template_path}")

    still_active = [
        p for p in list_sprint_files(sprints_dir)
        if read_sprint_status_file(p) == "ACTIVE"
    ]
    if still_active and not force:
        names = ", ".join(os.path.basename(p) for p in still_active)
        raise RuntimeError(
            f"{names} is still ACTIVE. Close it first (all issues DONE/CUT plus "
            f"a retro), or pass --force to create a parallel sprint."
        )

    number = next_sprint_number(sprints_dir)
    target = os.path.join(sprints_dir, f"sprint-{number:02d}.md")
    if os.path.exists(target):
        raise RuntimeError(f"refusing to overwrite existing board: {target}")

    start = today or date.today()
    end = start + timedelta(days=weeks * 7 - 1)

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    content = render_template(
        template,
        number=number,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        capacity=capacity,
        carryover=collect_carryover(sprints_dir),
    )

    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate the next SoloRail sprint board.")
    parser.add_argument("--capacity", default="20.0h", help="sprint capacity (default: 20.0h)")
    parser.add_argument("--weeks", type=int, default=2, help="sprint length in weeks (default: 2)")
    parser.add_argument("--force", action="store_true",
                        help="create even while another sprint is ACTIVE")
    args = parser.parse_args(argv)

    solorail_dir = os.path.join(os.getcwd(), ".solorail")
    if not os.path.isdir(solorail_dir):
        print("No .solorail/ directory found.", file=sys.stderr)
        return 1

    try:
        path = generate_next_sprint(
            solorail_dir, capacity=args.capacity, weeks=args.weeks, force=args.force
        )
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR [SoloRail]: {exc}", file=sys.stderr)
        return 2

    print(f"Created {os.path.relpath(path, os.getcwd())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
