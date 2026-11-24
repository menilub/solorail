#!/usr/bin/env python3
"""Unit tests for the git-gated metrics refresh (SoloRail E03-ISS-06).

Stdlib-only (unittest). Run with:
    python3 scripts/test_sync_on_git.py
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from sync_on_git import main, touches_git_state

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS_JSON = os.path.join(REPO_ROOT, "hooks", "hooks.json")

STALE_SPRINT = """# Sprint 60

- **Status:** ACTIVE

## Planned Issues
| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E60-ISS-01 | E-60 | Work | DONE | 2.0h | 1.5h | - | - |

## Metrics
| Metric | Planned | Actual |
| :--- | :--- | :--- |
| **Total Hours** | 999.0h | 999.0h |

## Time & Velocity Summary
- **Total Actual:** 999.0h
"""


def run_main(payload, cwd: str):
    """Invoke main() with `payload` on stdin from inside `cwd`."""
    original = os.getcwd()
    text = payload if isinstance(payload, str) else json.dumps(payload)
    out, err = io.StringIO(), io.StringIO()
    try:
        os.chdir(cwd)
        with patch("sys.stdin", io.StringIO(text)):
            with redirect_stdout(out), redirect_stderr(err):
                code = main()
    finally:
        os.chdir(original)
    return code, out.getvalue() + err.getvalue()


def fixture(tmp: str) -> str:
    sprints_dir = os.path.join(tmp, ".solorail", "sprints")
    os.makedirs(sprints_dir)
    path = os.path.join(sprints_dir, "sprint-60.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(STALE_SPRINT)
    return path


class TouchesGitStateTests(unittest.TestCase):
    def test_state_changing_commands_match(self):
        """Test 1."""
        for cmd in [
            "git merge main",
            "git pull",
            "git pull --rebase origin main",
            "git checkout -b feature/x",
            "git switch main",
            'git commit -m "y"',
            "git rebase main",
            "git cherry-pick abc123",
            "git reset --hard origin/main",
            "git revert HEAD",
            "git stash push -u -m tag",
            "gh pr merge 4",
            "gh pr checkout 7",
        ]:
            with self.subTest(cmd=cmd):
                self.assertTrue(touches_git_state(cmd), cmd)

    def test_read_only_git_does_not_match(self):
        """Test 2: a sync writes files, so inspection must not trigger one."""
        for cmd in [
            "git status",
            "git status --short",
            "git log --oneline -5",
            "git diff origin/main",
            "git show HEAD",
            "git branch --show-current",
            "git rev-parse --abbrev-ref HEAD",
            "gh pr view --json state",
        ]:
            with self.subTest(cmd=cmd):
                self.assertFalse(touches_git_state(cmd), cmd)

    def test_non_git_commands_do_not_match(self):
        """Test 3: the word appearing as an argument is not an invocation."""
        for cmd in [
            "ls",
            "python3 scripts/x.py",
            "grep -r foo .",
            "echo git merge",
            'echo "git pull"',
            "cat gitmerge.txt",
            "mygit merge",
        ]:
            with self.subTest(cmd=cmd):
                self.assertFalse(touches_git_state(cmd), cmd)

    def test_compound_commands_match_any_segment(self):
        """Test 4."""
        for cmd in [
            "cd /x && git merge main",
            "git status; git pull",
            "git fetch && git rebase origin/main",
        ]:
            with self.subTest(cmd=cmd):
                self.assertTrue(touches_git_state(cmd), cmd)

    def test_empty_command_is_false(self):
        self.assertFalse(touches_git_state(""))
        self.assertFalse(touches_git_state(None))


class MainTests(unittest.TestCase):
    def test_git_command_runs_sync(self):
        """Test 5."""
        with tempfile.TemporaryDirectory() as tmp:
            path = fixture(tmp)
            code, _ = run_main(
                {"tool_input": {"command": "git merge main"}}, tmp
            )
            with open(path) as f:
                result = f.read()

        self.assertEqual(code, 0)
        self.assertNotIn("999.0h", result)
        self.assertIn("| **Total Hours** | 2.0h | 1.5h |", result)

    def test_non_git_command_does_not_write(self):
        """Test 6: fixture must be byte-identical."""
        with tempfile.TemporaryDirectory() as tmp:
            path = fixture(tmp)
            code, _ = run_main({"tool_input": {"command": "ls -la"}}, tmp)
            with open(path) as f:
                result = f.read()

        self.assertEqual(code, 0)
        self.assertEqual(result, STALE_SPRINT)

    def test_exits_zero_on_malformed_stdin(self):
        """Test 7a: a PostToolUse hook must never fail the tool call."""
        with tempfile.TemporaryDirectory() as tmp:
            fixture(tmp)
            for payload in ["", "not json", "{}", '{"tool_input": {}}', "null"]:
                with self.subTest(payload=payload):
                    code, _ = run_main(payload, tmp)
                    self.assertEqual(code, 0)

    def test_exits_zero_when_sync_raises(self):
        """Test 7b."""
        with tempfile.TemporaryDirectory() as tmp:
            fixture(tmp)
            with patch("sync_metrics.sync", side_effect=RuntimeError("boom")):
                code, output = run_main(
                    {"tool_input": {"command": "git merge main"}}, tmp
                )

        self.assertEqual(code, 0)
        self.assertIn("boom", output)


class HooksJsonTests(unittest.TestCase):
    def test_hooks_json_declares_all_entries(self):
        """Test 8."""
        with open(HOOKS_JSON) as f:
            config = json.load(f)

        hooks = config["hooks"]

        pre = [h for entry in hooks["PreToolUse"] for h in entry["hooks"]]
        self.assertTrue(any("enforce_gate.py" in h["command"] for h in pre))

        post_matchers = {entry.get("matcher"): entry for entry in hooks["PostToolUse"]}
        self.assertIn("Edit|Write", post_matchers)
        self.assertIn("Bash", post_matchers)
        self.assertTrue(any(
            "sync_on_git.py" in h["command"]
            for h in post_matchers["Bash"]["hooks"]
        ))

        session = [h["command"] for entry in hooks["SessionStart"] for h in entry["hooks"]]
        joined = " | ".join(session)
        self.assertIn("sync_metrics.py", joined)
        self.assertIn("session_start.py", joined)

        sync_at = next(i for i, c in enumerate(session) if "sync_metrics.py" in c)
        banner_at = next(i for i, c in enumerate(session) if "session_start.py" in c)
        self.assertLess(sync_at, banner_at, "banner must read synced state")


if __name__ == "__main__":
    unittest.main(verbosity=2)
