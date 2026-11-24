#!/usr/bin/env python3
"""PostToolUse hook: refresh SoloRail metrics after a git-touching Bash command.

Metrics previously refreshed only on Edit/Write, so a `git merge`, a PR merge,
or a checkout left every status surface stale -- which is exactly how this
project's own status went stale when PRs merged outside the workspace.

Claude Code hook matchers match the tool NAME, not its arguments, so there is
no way to express "Bash, but only git" in hooks.json. This wrapper runs on
every Bash call, decides cheaply from the command string, and only then
imports and runs the sync.

A PostToolUse hook that fails breaks the tool call that triggered it. This is
an opportunistic refresh, not a gate, so main() always exits 0.
"""

import json
import re
import sys

# Subcommands that can change working-tree or history state. Read-only
# inspection (status, log, diff, show, branch, rev-parse) is deliberately
# absent: a sync writes files, and `git status` must not mutate the tree.
GIT_STATE_COMMANDS = {
    "merge", "pull", "checkout", "switch", "commit", "rebase",
    "cherry-pick", "reset", "revert", "am", "apply", "stash", "clone",
}

GH_STATE_COMMANDS = {"merge", "checkout"}

# Split on shell separators so a compound command is judged per segment.
SEGMENT_RE = re.compile(r"(?:&&|\|\||;|\n|\|)")


def _segment_tokens(segment: str) -> list[str]:
    return segment.strip().split()


def touches_git_state(command: str) -> bool:
    """True when the command plausibly changed git state.

    Judged per shell segment, so `cd /x && git merge main` matches while
    `echo git merge` does not -- the word must be the invoked program, not an
    argument.
    """
    if not command:
        return False

    for segment in SEGMENT_RE.split(command):
        tokens = _segment_tokens(segment)
        if not tokens:
            continue

        # Skip leading env assignments (FOO=bar git merge).
        index = 0
        while index < len(tokens) and "=" in tokens[index] and not tokens[index].startswith("-"):
            index += 1
        if index >= len(tokens):
            continue

        program = tokens[index].rsplit("/", 1)[-1]
        rest = [t for t in tokens[index + 1:] if not t.startswith("-")]

        if program == "git" and rest and rest[0] in GIT_STATE_COMMANDS:
            return True
        if program == "gh" and len(rest) >= 2 and rest[0] == "pr" and rest[1] in GH_STATE_COMMANDS:
            return True

    return False


def _read_command() -> str:
    """The Bash command from the PostToolUse payload, or '' when unavailable."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return ""
    if not raw.strip():
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
    return tool_input.get("command") or ""


def main(argv=None) -> int:
    """Run the sync when the command touched git state. Always exits 0."""
    try:
        command = _read_command()
        if not touches_git_state(command):
            return 0

        # Imported lazily: this hook runs on every Bash call, and most calls
        # do not need the sync machinery loaded at all.
        import sync_metrics

        sync_metrics.sync()
    except Exception as exc:  # never fail the tool call that triggered us
        print(f"NOTE [SoloRail]: metrics refresh skipped ({exc})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
