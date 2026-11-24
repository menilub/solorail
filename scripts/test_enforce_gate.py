#!/usr/bin/env python3
"""Unit tests for the main/master hard-block helpers in enforce_gate.py
(SoloRail E02-ISS-02).

Stdlib-only (unittest + unittest.mock). Run with:
    python3 scripts/test_enforce_gate.py
"""

import unittest
from unittest.mock import patch

from enforce_gate import get_current_branch, is_protected_branch


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


if __name__ == "__main__":
    unittest.main()
