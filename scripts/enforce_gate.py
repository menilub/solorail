#!/usr/bin/env python3
"""PreToolUse gatekeeper hook for SoloRail v2.7.0.

Physically blocks Claude Code from editing application code outside the active workflow:
1. Requires an issue marked IN_PROGRESS in .solorail/sprints/sprint-*.md.
2. Requires a technical spec receipt (.solorail/specs/<ID>-spec.md) unless it is a BUG-XX hotfix.
3. Requires the target file to be explicitly listed in that spec receipt.
"""

import glob
import json
import os
import sys


def get_active_issue(sprints_dir: str):
    sprint_files = sorted(glob.glob(os.path.join(sprints_dir, "sprint-*.md")))
    if not sprint_files:
        return None
    with open(sprint_files[-1], "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            # Table row: ['', ID, Epic, Issue, Status, Est, Actual, Started At, Notes, '']
            if len(parts) >= 5 and parts[4].upper() == "IN_PROGRESS":
                return parts[1]
    return None


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


def main():
    target_path = ""
    if not sys.stdin.isatty():
        try:
            data = json.load(sys.stdin)
            tool_input = data.get("tool_input", {}) or {}
            target_path = tool_input.get("file_path", "") or tool_input.get("path", "")
        except Exception:
            pass

    if not target_path and len(sys.argv) > 1:
        target_path = sys.argv[1]

    rel_path = normalize_rel_path(target_path)
    if not rel_path:
        sys.exit(0)

    # Allow SoloRail state files, Claude settings, and CLAUDE.md
    if (
        rel_path.startswith(".solorail/")
        or rel_path == ".solorail"
        or rel_path.startswith(".claude/")
        or rel_path == "CLAUDE.md"
    ):
        sys.exit(0)

    solorail_dir = os.path.join(os.getcwd(), ".solorail")
    if not os.path.exists(solorail_dir):
        sys.exit(0)

    active_issue = get_active_issue(os.path.join(solorail_dir, "sprints"))
    if not active_issue:
        print("BLOCKED [SoloRail]: No issue is IN_PROGRESS. Run `/solorail:architect-issue <ID>` (or `/solorail:hotfix`) first.")
        sys.exit(2)

    if active_issue.startswith("BUG-"):
        sys.exit(0)

    spec_path = os.path.join(solorail_dir, "specs", f"{active_issue}-spec.md")
    if not os.path.exists(spec_path):
        print(f"BLOCKED [SoloRail]: Stage 2 skipped. Run `/solorail:architect-issue {active_issue}` before writing code.")
        sys.exit(2)

    with open(spec_path, "r", encoding="utf-8") as f:
        spec_content = f.read()

    basename = os.path.basename(rel_path)
    if rel_path not in spec_content and basename not in spec_content:
        print(f"SCOPE VIOLATION [SoloRail]: '{rel_path}' is not allowlisted in .solorail/specs/{active_issue}-spec.md.")
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
