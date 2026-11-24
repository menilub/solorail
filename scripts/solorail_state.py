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


OPEN_STATUSES = {"TODO", "IN_PROGRESS", "BLOCKED"}
CLOSEABLE_STATUSES = {"DONE", "CUT"}


def issue_statuses(lines: list[str]) -> list[str]:
    """Upper-cased Status cell of every issue row, in board order.

    Empty when the board carries no issue rows (header and separator only).
    """
    statuses = []
    for line in lines:
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        # Row shape: ['', ID, Epic, Issue, Status, Est, Actual, Started At, Notes, '']
        if len(cells) < 6:
            continue
        issue_id, status = cells[1], cells[4].upper()
        if issue_id in ("ID", "", "-") or set(issue_id) <= set(":- "):
            continue
        if status in OPEN_STATUSES or status in CLOSEABLE_STATUSES:
            statuses.append(status)
    return statuses


CARRYOVER_STATUSES = {"TODO", "BLOCKED"}


def is_issue_row(line: str) -> bool:
    """True for a real issue row, excluding the header and separator rows."""
    if "|" not in line:
        return False
    cells = [c.strip() for c in line.split("|")]
    if len(cells) < 6:
        return False
    issue_id = cells[1]
    if issue_id in ("ID", "", "-") or set(issue_id) <= set(":- "):
        return False
    return cells[4].upper() in (OPEN_STATUSES | CLOSEABLE_STATUSES)


def carryover_rows(lines: list[str]) -> list[str]:
    """Issue rows whose Status is TODO or BLOCKED, verbatim, in board order.

    These are the rows an unfinished sprint hands to its successor. DONE and
    CUT rows stay behind as that sprint's own history.
    """
    return [
        line for line in lines
        if is_issue_row(line) and line.split("|")[4].strip().upper() in CARRYOVER_STATUSES
    ]


def reset_row_for_carryover(row: str, origin: str = "") -> str:
    """A carried row with Actual and Started At cleared and a note recording
    where it came from.

    Est and Status are preserved deliberately: a BLOCKED issue is still
    blocked after the sprint boundary, and re-estimating is a planning
    decision, not a side effect of carryover.
    """
    cells = row.rstrip("\n").split("|")
    if len(cells) < 9:
        return row

    cells[6] = " - "   # Actual
    cells[7] = " - "   # Started At

    note = cells[8].strip()
    origin_note = f"carried over from {origin}" if origin else "carried over"
    if note and note != "-":
        cells[8] = f" {note}; {origin_note} "
    else:
        cells[8] = f" {origin_note} "

    return "|".join(cells) + "\n"


CARRYOVER_MARKER = "carried over"


def is_carryover_row(row: str) -> bool:
    """True when an issue row was carried forward from an earlier sprint.

    Lets epic aggregation tell a legitimate carryover (the same issue
    continuing on a new board) from a genuinely duplicated ID.
    """
    cells = row.split("|")
    if len(cells) < 9:
        return False
    return CARRYOVER_MARKER in cells[8].lower()


def retro_path_for(sprint_path: str) -> str:
    """The retro path matching a sprint board.

    .solorail/sprints/sprint-07.md -> .solorail/retros/sprint-07-retro.md
    """
    name = os.path.basename(sprint_path).removesuffix(".md")
    solorail_dir = os.path.dirname(os.path.dirname(sprint_path))
    return os.path.join(solorail_dir, "retros", f"{name}-retro.md")


def derive_sprint_status(lines: list[str], retro_exists: bool) -> str | None:
    """The status the board should declare, or None to leave it unchanged.

    'CLOSED' requires every issue row to be DONE/CUT, at least one row, and a
    retro on disk. The retro is the interlock: without it a sprint would flip
    to CLOSED the instant the last issue was marked DONE -- mid-session, as a
    side effect of an unrelated edit, before `/solorail:evolve` had run.

    Never returns 'ACTIVE'. Auto-reopening would let an unrelated edit
    resurrect frozen history, so reopening stays a deliberate human act.
    """
    if read_sprint_status(lines) == "CLOSED":
        return None

    statuses = issue_statuses(lines)
    if not statuses:
        # An unplanned board is not a finished one.
        return None
    if any(s in OPEN_STATUSES for s in statuses):
        return None
    if not retro_exists:
        return None
    return "CLOSED"


def write_sprint_status(lines: list[str], status: str) -> list[str]:
    """Replace the header's Status value, preserving the line's markdown shape.

    Returns the lines unchanged when the header has no Status line: this
    function never invents one.
    """
    updated = list(lines)
    for i, line in enumerate(updated):
        stripped = line.lstrip()
        if stripped.startswith("|"):
            break
        if HEADING_RE.match(line) and not line.startswith("# "):
            break
        match = STATUS_RE.search(line)
        if match:
            updated[i] = line[: match.start(1)] + status + line[match.end(1):]
            return updated
    return lines


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
