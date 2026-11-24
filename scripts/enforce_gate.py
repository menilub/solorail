#!/usr/bin/env python3
"""PreToolUse gatekeeper hook for SoloRail v2.7.3.

Physically blocks Claude Code from editing application code outside the active workflow:
1. Requires the current branch to not be 'main'/'master' (hard block, not a warning).
2. Requires an issue marked IN_PROGRESS in .solorail/sprints/sprint-*.md.
3. Requires a technical spec receipt (.solorail/specs/<ID>-spec.md) unless it is a BUG-XX hotfix.
4. Requires the target file to be explicitly listed in that spec receipt.
"""

import json
import os
import subprocess
import sys

from solorail_state import resolve_active_sprint
from spec_allowlist import is_allowlisted


def get_current_branch(cwd: str = None) -> str:
    """Return the current branch name via `git rev-parse --abbrev-ref HEAD`,
    or None if git is unavailable, the command fails, or cwd isn't a repo."""
    target = cwd if cwd is not None else os.getcwd()
    try:
        result = subprocess.run(
            ["git", "-C", target, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None

    if result.returncode != 0 or not result.stdout:
        return None

    return result.stdout.strip() or None


def is_protected_branch(branch: str) -> bool:
    """True iff branch is exactly 'main' or 'master'. None/anything else fails open."""
    return branch in ("main", "master")


def get_active_issue(sprints_dir: str):
    # Resolve by declared Status, not by filename order: selecting the last
    # filename meant the gate stopped enforcing an IN_PROGRESS issue as soon
    # as a newer sprint file existed (E03-ISS-02).
    sprint_path = resolve_active_sprint(sprints_dir)
    if not sprint_path:
        return None
    with open(sprint_path, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            # Table row: ['', ID, Epic, Issue, Status, Est, Actual, Started At, Notes, '']
            if len(parts) >= 5 and parts[4].upper() == "IN_PROGRESS":
                return parts[1]
    return None


RECORD_KEEPING_PREFIXES = (".solorail", ".claude", ".context")
RECORD_KEEPING_FILES = ("CLAUDE.md",)


def is_record_keeping_path(rel_path: str) -> bool:
    """True for paths that record work rather than perform it.

    These stay writable with no issue IN_PROGRESS and on a protected branch,
    because between sprints -- exactly when retro, review and planning work
    happens -- everything else is correctly read-only, which previously pushed
    record-keeping out of the repo entirely.

    Deliberately NOT a blanket '*.md' exemption: that would unlock README.md
    and every doc under a source tree, and documentation is often exactly what
    an issue is scoped to change. Prefixes are matched at directory
    boundaries, and anything escaping the repo root is refused.
    """
    if not rel_path:
        return False
    normalized = rel_path.replace("\\", "/")
    if normalized.startswith("../") or normalized == "..":
        return False
    if normalized in RECORD_KEEPING_FILES:
        return False if "/" in normalized else True
    first_segment = normalized.split("/", 1)[0]
    return first_segment in RECORD_KEEPING_PREFIXES


def read_target_path(argv: list[str] = None) -> str:
    """The hook's target path: argv[1] when given, else the JSON payload.

    argv is checked FIRST and stdin is not read at all when argv supplies a
    path. Reading stdin unconditionally made the gate hang forever when it was
    invoked with a path from a context whose stdin was an open pipe that never
    closed -- json.load simply waits.
    """
    args = sys.argv if argv is None else argv
    if len(args) > 1 and args[1]:
        return args[1]

    try:
        if sys.stdin.isatty():
            return ""
        raw = sys.stdin.read()
    except Exception:
        return ""

    if not raw or not raw.strip():
        return ""
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return ""
    if not isinstance(data, dict):
        return ""
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ""
    return tool_input.get("file_path") or tool_input.get("path") or ""


def normalize_rel_path(raw_path: str) -> str:
    if not raw_path:
        return ""
    cwd = os.getcwd()
    abs_target = raw_path if os.path.isabs(raw_path) else os.path.abspath(os.path.join(cwd, raw_path))
    try:
        rel = os.path.relpath(abs_target, cwd)
    except ValueError:
        return raw_path
    return rel.replace("\\", "/")


def block(reason: str):
    print(reason, file=sys.stderr)
    sys.exit(2)


def main():
    target_path = read_target_path()

    rel_path = normalize_rel_path(target_path)
    if not rel_path:
        sys.exit(0)

    # Record-keeping paths (SoloRail state, Claude config, .context scratch)
    # stay writable with no issue IN_PROGRESS and on a protected branch:
    # ADR-002 protects application code, and a retro is not that.
    if is_record_keeping_path(rel_path):
        sys.exit(0)

    solorail_dir = os.path.join(os.getcwd(), ".solorail")
    if not os.path.exists(solorail_dir):
        sys.exit(0)

    current_branch = get_current_branch()
    if is_protected_branch(current_branch):
        block(
            f"BLOCKED [SoloRail]: Cannot edit application code directly on "
            f"'{current_branch}'. Create a feature branch first, e.g. "
            f"`git checkout -b feat/<ISSUE-ID>`."
        )

    active_issue = get_active_issue(os.path.join(solorail_dir, "sprints"))
    if not active_issue:
        block("BLOCKED [SoloRail]: No issue is IN_PROGRESS. Run `/solorail:architect-issue <ID>` (or `/solorail:hotfix`) first.")

    if active_issue.startswith("BUG-"):
        sys.exit(0)

    spec_path = os.path.join(solorail_dir, "specs", f"{active_issue}-spec.md")
    if not os.path.exists(spec_path):
        block(f"BLOCKED [SoloRail]: Stage 2 skipped. Run `/solorail:architect-issue {active_issue}` before writing code.")

    with open(spec_path, "r", encoding="utf-8") as f:
        spec_content = f.read()

    # Parse the spec's allowlist section rather than substring-matching the
    # whole file. The old check authorised any filename mentioned anywhere,
    # including in prose and in the no-go list -- naming a file as forbidden
    # granted write access to it (E03-ISS-09).
    allowed, reason = is_allowlisted(rel_path, spec_content)
    if not allowed:
        block(
            f"SCOPE VIOLATION [SoloRail]: '{rel_path}' is not allowlisted in "
            f".solorail/specs/{active_issue}-spec.md — {reason}"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
