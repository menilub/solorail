#!/usr/bin/env python3
"""Shared SoloRail sprint-state resolution (E03-ISS-02).

Three scripts previously selected the sprint board with
`sorted(glob(...))[-1]` -- the last filename. Filename order is not sprint
state: a CLOSED sprint sorts last whenever it is the highest-numbered file, and
plain string sort puts `sprint-10.md` before `sprint-9.md`. The practical
consequence was that `enforce_gate.py` stopped enforcing an IN_PROGRESS issue
as soon as a newer sprint file existed.

Every consumer now resolves the sprint by its declared `Status:` through this
module. Stdlib-only and side-effect-free at import time, because
`enforce_gate.py` and `session_start.py` import it from inside Claude Code
hooks.
"""

import glob
import os
import re
import sys

SPRINT_NUMBER_RE = re.compile(r"sprint-(\d+)\.md$")
STATUS_RE = re.compile(r"status:\s*\**\s*([A-Za-z_]+)", re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6} ")


def sprint_number(path: str) -> int:
    """Numeric sprint index from a sprint-NN.md path, or -1 when unparseable.

    Ordering by this value rather than by filename keeps sprint-10 after
    sprint-9.
    """
    match = SPRINT_NUMBER_RE.search(os.path.basename(path))
    return int(match.group(1)) if match else -1


def list_sprint_files(sprints_dir: str) -> list[str]:
    """All sprint-*.md paths ordered by sprint number, lowest first."""
    if not os.path.isdir(sprints_dir):
        return []
    paths = glob.glob(os.path.join(sprints_dir, "sprint-*.md"))
    return sorted(paths, key=lambda p: (sprint_number(p), os.path.basename(p)))


def read_sprint_status(lines: list[str]) -> str | None:
    """The sprint's declared Status, upper-cased, or None when absent.

    Only the header block is consulted: the scan stops at the first table row
    or sub-heading, so an issue row whose Notes cell mentions a status word
    cannot flip the whole board.
    """
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("|"):
            break
        if HEADING_RE.match(line) and not line.startswith("# "):
            break
        match = STATUS_RE.search(line)
        if match:
            return match.group(1).upper()
    return None


def read_sprint_status_file(path: str) -> str | None:
    """read_sprint_status for a path, tolerating an unreadable file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return read_sprint_status(f.readlines())
    except OSError:
        return None


def is_closed_sprint(lines: list[str]) -> bool:
    """True when the sprint header declares Status: CLOSED."""
    return read_sprint_status(lines) == "CLOSED"


def resolve_active_sprint(sprints_dir: str) -> str | None:
    """Path of the sprint to act on, or None when there are no sprint files.

    Resolution order, chosen to stay deterministic and fail safe:
      1. exactly one ACTIVE sprint -> that one
      2. several ACTIVE -> the lowest-numbered, with a warning (the oldest
         still-open sprint is the one needing attention; picking the newest
         would hide a sprint someone forgot to close)
      3. none ACTIVE -> the highest-numbered, with a warning (preserves the
         previous behaviour rather than returning None, so the gate does not
         start failing open the moment every sprint is closed)
    """
    sprint_files = list_sprint_files(sprints_dir)
    if not sprint_files:
        return None

    active = [p for p in sprint_files if read_sprint_status_file(p) == "ACTIVE"]

    if len(active) == 1:
        return active[0]

    if len(active) > 1:
        names = ", ".join(os.path.basename(p) for p in active)
        print(
            f"WARNING [SoloRail]: more than one ACTIVE sprint ({names}); "
            f"using {os.path.basename(active[0])}.",
            file=sys.stderr,
        )
        return active[0]

    fallback = sprint_files[-1]
    print(
        f"WARNING [SoloRail]: no active sprint found; "
        f"falling back to {os.path.basename(fallback)}.",
        file=sys.stderr,
    )
    return fallback
