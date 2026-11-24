#!/usr/bin/env python3
"""Unit tests for enforce_gate.py helpers.

Covers the main/master hard block (E02-ISS-02) and the record-keeping
exemption plus argv-first target resolution (E03-ISS-07).

Stdlib-only (unittest + unittest.mock). Run with:
    python3 scripts/test_enforce_gate.py
"""

import json
import unittest
from unittest.mock import patch

from enforce_gate import (
    get_current_branch,
    is_protected_branch,
    is_record_keeping_path,
    read_target_path,
)


def _fake_run(returncode=0, stdout=""):
    class _Result:
        pass

    result = _Result()
    result.returncode = returncode
    result.stdout = stdout
    return result


class IsProtectedBranchTests(unittest.TestCase):
    def test_main_is_protected(self):
        """Test 1: 'main' is protected."""
        self.assertTrue(is_protected_branch("main"))

    def test_master_is_protected(self):
        """Test 2: 'master' is protected."""
        self.assertTrue(is_protected_branch("master"))

    def test_feature_branch_is_not_protected(self):
        """Test 3: a feature branch is not protected."""
        self.assertFalse(is_protected_branch("feat/E02-ISS-02"))

    def test_none_is_not_protected(self):
        """Edge case: unknown branch (None) fails open, not blocked."""
        self.assertFalse(is_protected_branch(None))


class GetCurrentBranchTests(unittest.TestCase):
    def test_success_returns_branch_name(self):
        """Test 4: git succeeds -> returns the trimmed branch name."""
        with patch("enforce_gate.subprocess.run", return_value=_fake_run(stdout="main\n")):
            self.assertEqual(get_current_branch(), "main")

    def test_git_failure_returns_none(self):
        """Test 5: git exits non-zero -> None, no crash."""
        with patch("enforce_gate.subprocess.run", return_value=_fake_run(returncode=128, stdout="")):
            self.assertIsNone(get_current_branch())

    def test_git_not_found_returns_none(self):
        """Test 6: git binary missing -> None, no crash."""
        with patch("enforce_gate.subprocess.run", side_effect=FileNotFoundError("git not found")):
            self.assertIsNone(get_current_branch())


class IsRecordKeepingPathTests(unittest.TestCase):
    """E03-ISS-07: paths that record work stay writable between issues."""

    def test_record_keeping_paths_are_exempt(self):
        """Test 1."""
        for path in [
            ".solorail/retros/sprint-01-retro.md",
            ".solorail/archive/adr-history.md",
            ".solorail/sprints/sprint-02.md",
            ".context/notes.md",
            ".context/nested/deep/file.json",
            ".claude/settings.json",
            "CLAUDE.md",
        ]:
            with self.subTest(path=path):
                self.assertTrue(is_record_keeping_path(path), path)

    def test_source_and_doc_paths_are_not_exempt(self):
        """Test 2: guards against a blanket *.md exemption. Documentation is
        often exactly what an issue is scoped to change."""
        for path in [
            "scripts/sync_metrics.py",
            "README.md",
            "hooks/hooks.json",
            "src/app.py",
            "docs/guide.md",
            "templates/thing.md",
            "LICENSE",
        ]:
            with self.subTest(path=path):
                self.assertFalse(is_record_keeping_path(path), path)

    def test_path_escaping_the_repo_is_not_exempt(self):
        """Test 3: an absolute path outside the repo normalizes to '../' and
        must never be silently exempt."""
        for path in ["../../tmp/x.md", "../outside.md", "../.context/x.md"]:
            with self.subTest(path=path):
                self.assertFalse(is_record_keeping_path(path), path)

    def test_prefix_is_matched_at_a_directory_boundary(self):
        """Test 4: '.contextual/' must not match the '.context' exemption."""
        self.assertFalse(is_record_keeping_path(".contextual/file.md"))
        self.assertFalse(is_record_keeping_path(".solorailway/file.md"))
        self.assertFalse(is_record_keeping_path("CLAUDE.md.bak"))

    def test_bare_directory_names_are_exempt(self):
        self.assertTrue(is_record_keeping_path(".solorail"))
        self.assertTrue(is_record_keeping_path(".context"))


class ReadTargetPathTests(unittest.TestCase):
    """E03-ISS-07: argv is read first so the hook never blocks on stdin."""

    def test_prefers_argv_without_reading_stdin(self):
        """Test 5: the hang regression. json.load on an open pipe that never
        closes blocks forever, so stdin must not be touched when argv has a
        path."""
        class ExplodingStdin:
            def isatty(self):
                return False

            def read(self, *a):
                raise AssertionError("stdin must not be read when argv has a path")

        with patch("enforce_gate.sys.stdin", ExplodingStdin()):
            self.assertEqual(read_target_path(["prog", "a/b.py"]), "a/b.py")

    def test_falls_back_to_stdin_payload(self):
        """Test 6."""
        import io

        payload = io.StringIO(json.dumps({"tool_input": {"file_path": "x/y.py"}}))
        payload.isatty = lambda: False
        with patch("enforce_gate.sys.stdin", payload):
            self.assertEqual(read_target_path(["prog"]), "x/y.py")

        payload2 = io.StringIO(json.dumps({"tool_input": {"path": "p/q.py"}}))
        payload2.isatty = lambda: False
        with patch("enforce_gate.sys.stdin", payload2):
            self.assertEqual(read_target_path(["prog"]), "p/q.py")

    def test_returns_empty_on_malformed_stdin(self):
        """Test 7."""
        import io

        for raw in ["", "not json", "null", "{}", '{"tool_input": {}}']:
            with self.subTest(raw=raw):
                payload = io.StringIO(raw)
                payload.isatty = lambda: False
                with patch("enforce_gate.sys.stdin", payload):
                    self.assertEqual(read_target_path(["prog"]), "")


class ProseMentionBypassTests(unittest.TestCase):
    """E03-ISS-09 regression: a filename mentioned only in spec prose must not
    be writable. The E03-ISS-07 spec's sentence 'would unlock `README.md`'
    previously authorised README.md."""

    SPEC = """# Spec

## Problem

A blanket exemption would unlock `README.md`, which we do not want.

## Allowlisted Files to Create/Modify

- `scripts/target.py` *(modify)*

## No-Go Constraints

- `scripts/forbidden.py`
"""

    def test_prose_mention_blocked_and_allowlist_permitted(self):
        from spec_allowlist import is_allowlisted as check

        allowed, reason = check("README.md", self.SPEC)
        self.assertFalse(allowed, f"prose mention must not authorise: {reason}")

        allowed, _ = check("scripts/forbidden.py", self.SPEC)
        self.assertFalse(allowed, "a no-go entry must not authorise")

        allowed, _ = check("scripts/target.py", self.SPEC)
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()
