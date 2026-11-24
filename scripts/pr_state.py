#!/usr/bin/env python3
"""Record and refresh the pull request behind each SoloRail issue (E03-ISS-05).

Nothing in .solorail/ recorded a PR. verify-issue has opened one since
E02-ISS-02, so PRs existed -- they were just never stored, and no status
surface can show what was never recorded.

PRs live in a managed '## Pull Requests' section below the velocity summary,
NOT as a table column: the issue table is parsed by column index by five
consumers, and sync_metrics.split_row discards empty cells, so a blank PR cell
would shift every index after it. The section is only viable because
E03-ISS-01 stopped the metric splice truncating to EOF.

Recorded State is a CACHE, refreshed on demand. `gh` may be missing,
unauthenticated, offline or slow, so every call to it has a timeout and
returns None on any failure, leaving the previous value in place. A missing
`gh` degrades to "PR recorded, state unknown" -- never to a wrong state.

Usage:
    python3 scripts/pr_state.py record <ISSUE-ID> <PR>
    python3 scripts/pr_state.py refresh
"""

import json
import os
import re
import subprocess
import sys

from solorail_state import is_closed_sprint, resolve_active_sprint
from sync_metrics import replace_block

BLOCK_NAME = "pull-requests"
BLOCK_MARKER = "## Pull Requests"
VALID_STATES = {"OPEN", "MERGED", "CLOSED", "DRAFT", "UNKNOWN"}
PR_NUMBER_RE = re.compile(r"(?:^|/pull/|#)(\d+)$")
GH_TIMEOUT = 5.0


def normalize_pr_ref(raw) -> str:
    """'#4', '4', 'o/r#4' or a GitHub PR URL -> '#4'; '' when unparseable.

    Returning '' rather than guessing keeps a malformed ref from being
    recorded as if it were valid.
    """
    if not raw or not isinstance(raw, str):
        return ""
    match = PR_NUMBER_RE.search(raw.strip())
    if not match:
        return ""
    number = int(match.group(1))
    return f"#{number}" if number > 0 else ""


def parse_pr_rows(lines: list[str]) -> dict[str, dict]:
    """Recorded PRs as {issue_id: {"pr": "#4", "state": "OPEN"}}.

    Entered by the start sentinel, or by the '## Pull Requests' heading when
    that sentinel is missing. The fallback matters: requiring the sentinel
    meant a block damaged by an older truncating sync lost every recorded row
    on the next write, silently. Mirrors replace_block's own migration path.
    """
    rows = {}
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped == f"<!-- solorail:{BLOCK_NAME}:start -->":
            inside = True
            continue
        if not inside and stripped == BLOCK_MARKER:
            inside = True
            continue
        if stripped == f"<!-- solorail:{BLOCK_NAME}:end -->":
            break
        if inside and stripped.startswith("## ") and stripped != BLOCK_MARKER:
            break
        if not inside or "|" not in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 5:
            continue
        issue_id, pr_ref, state = cells[1], cells[2], cells[3]
        if issue_id in ("Issue", "") or set(issue_id) <= set(":- "):
            continue
        rows[issue_id] = {"pr": pr_ref, "state": state or "UNKNOWN"}
    return rows


def render_pr_table(rows: dict[str, dict]) -> list[str]:
    """The '## Pull Requests' block body. Issue IDs are sorted so repeated
    writes produce stable diffs."""
    out = [
        f"{BLOCK_MARKER}\n",
        "| Issue | PR | State |\n",
        "| :--- | :--- | :--- |\n",
    ]
    for issue_id in sorted(rows):
        row = rows[issue_id]
        out.append(f"| {issue_id} | {row['pr']} | {row.get('state') or 'UNKNOWN'} |\n")
    return out


def _read(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def record_pr(sprint_path: str, issue_id: str, pr_ref: str,
              state: str = "UNKNOWN") -> None:
    """Insert or update one issue's PR row. Idempotent.

    Refuses a CLOSED board, matching E03-ISS-01's rule that closed sprints are
    frozen history.
    """
    normalized = normalize_pr_ref(pr_ref)
    if not normalized:
        raise ValueError(f"unparseable PR reference: {pr_ref!r}")

    lines = _read(sprint_path)
    if is_closed_sprint(lines):
        raise RuntimeError(
            f"{os.path.basename(sprint_path)} is CLOSED; its board is frozen."
        )

    rows = parse_pr_rows(lines)
    rows[issue_id] = {
        "pr": normalized,
        "state": state if state in VALID_STATES else "UNKNOWN",
    }

    updated = replace_block(
        lines, BLOCK_MARKER, render_pr_table(rows), block_name=BLOCK_NAME
    )
    with open(sprint_path, "w", encoding="utf-8") as f:
        f.writelines(updated)


def query_pr_state(pr_ref: str, timeout: float = GH_TIMEOUT):
    """Live PR state via gh, or None on any failure.

    None covers: gh absent, unauthenticated, offline, timed out, non-zero
    exit, unparseable output, or a state we do not recognise. Callers keep
    their cached value in that case.
    """
    normalized = normalize_pr_ref(pr_ref)
    if not normalized:
        return None

    try:
        result = subprocess.run(
            ["gh", "pr", "view", normalized.lstrip("#"), "--json", "state"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0 or not (result.stdout or "").strip():
        return None

    try:
        payload = json.loads(result.stdout)
    except (ValueError, TypeError):
        return None

    if not isinstance(payload, dict):
        return None

    state = str(payload.get("state") or "").upper()
    return state if state in VALID_STATES - {"UNKNOWN"} else None


def refresh_pr_states(sprint_path: str, timeout: float = GH_TIMEOUT) -> dict[str, str]:
    """Re-query every recorded PR; write back only the states that resolved."""
    lines = _read(sprint_path)
    rows = parse_pr_rows(lines)
    if not rows:
        return {}

    resolved = {}
    for issue_id, row in rows.items():
        state = query_pr_state(row["pr"], timeout=timeout)
        if state:
            rows[issue_id]["state"] = state
            resolved[issue_id] = state

    if resolved and not is_closed_sprint(lines):
        updated = replace_block(
            lines, BLOCK_MARKER, render_pr_table(rows), block_name=BLOCK_NAME
        )
        with open(sprint_path, "w", encoding="utf-8") as f:
            f.writelines(updated)

    return resolved


def main(argv=None) -> int:
    args = (argv if argv is not None else sys.argv)[1:]
    sprints_dir = os.path.join(os.getcwd(), ".solorail", "sprints")
    sprint_path = resolve_active_sprint(sprints_dir)
    if not sprint_path:
        print("No active sprint board found.", file=sys.stderr)
        return 1

    if len(args) >= 3 and args[0] == "record":
        try:
            state = query_pr_state(args[2]) or "UNKNOWN"
            record_pr(sprint_path, args[1], args[2], state=state)
        except (ValueError, RuntimeError) as exc:
            print(f"ERROR [SoloRail]: {exc}", file=sys.stderr)
            return 2
        print(f"Recorded {args[1]} -> {normalize_pr_ref(args[2])} ({state})")
        return 0

    if args and args[0] == "refresh":
        resolved = refresh_pr_states(sprint_path)
        if not resolved:
            print("No PR states could be refreshed (gh unavailable or none recorded).")
        for issue_id, state in sorted(resolved.items()):
            print(f"{issue_id}: {state}")
        return 0

    print(__doc__.strip().splitlines()[-3].strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
