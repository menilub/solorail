#!/usr/bin/env python3
"""Unit tests for check_worktree.py (SoloRail E02-ISS-01).

Stdlib-only (unittest + unittest.mock). Run with:
    python3 scripts/test_check_worktree.py
"""

import unittest
from unittest.mock import patch

from check_worktree import is_inside_worktree

MAIN_CHECKOUT = "/Users/menilub/IdeaProjects/solorail-v1"
LINKED_WORKTREE = "/Users/menilub/conductor/workspaces/solorail-v1/vientiane"


def _fake_run(returncode=0, stdout=""):
    class _Result:
        pass

    result = _Result()
    result.returncode = returncode
    result.stdout = stdout
    return result


class IsInsideWorktreeTests(unittest.TestCase):
    def test_inside_linked_worktree_root(self):
        """Test 1: git-dir != git-common-dir -> True (e.g. a Conductor worktree)."""
        stdout = (
            f"{MAIN_CHECKOUT}/.git/worktrees/vientiane\n"
            f"{MAIN_CHECKOUT}/.git\n"
        )
        with patch("check_worktree.subprocess.run", return_value=_fake_run(stdout=stdout)):
            self.assertTrue(is_inside_worktree(LINKED_WORKTREE))

    def test_inside_nested_subdirectory_of_linked_worktree(self):
        """Test 2: git resolves the same git-dir/common-dir from a subdirectory -> True."""
        stdout = (
            f"{MAIN_CHECKOUT}/.git/worktrees/vientiane\n"
            f"{MAIN_CHECKOUT}/.git\n"
        )
        with patch("check_worktree.subprocess.run", return_value=_fake_run(stdout=stdout)):
            self.assertTrue(is_inside_worktree(f"{LINKED_WORKTREE}/.solorail/specs"))

    def test_main_checkout_returns_false(self):
        """Test 3: git-dir == git-common-dir in the primary checkout -> False,
        so a fresh main-repo session still gets the worktree-creation offer."""
        stdout = ".git\n.git\n"
        with patch("check_worktree.subprocess.run", return_value=_fake_run(stdout=stdout)):
            self.assertFalse(is_inside_worktree(MAIN_CHECKOUT))

    def test_directory_outside_any_git_repo_returns_false(self):
        """Test 4: not a Git repo (git exits non-zero) -> False."""
        with patch("check_worktree.subprocess.run", return_value=_fake_run(returncode=128, stdout="")):
            self.assertFalse(is_inside_worktree("/tmp/some/unrelated/dir"))

    def test_git_not_found_returns_false(self):
        """Test 5: git binary missing (FileNotFoundError) -> False, no crash."""
        with patch("check_worktree.subprocess.run", side_effect=FileNotFoundError("git not found")):
            self.assertFalse(is_inside_worktree("/Users/menilub/anywhere"))

    def test_malformed_output_returns_false(self):
        """Test 6: unexpected/empty output -> False, no crash."""
        with patch("check_worktree.subprocess.run", return_value=_fake_run(stdout="")):
            self.assertFalse(is_inside_worktree(MAIN_CHECKOUT))

    def test_defaults_to_real_cwd_when_no_argument_given(self):
        """is_inside_worktree() with no args should use os.getcwd()."""
        stdout = ".git\n.git\n"
        with patch("check_worktree.subprocess.run", return_value=_fake_run(stdout=stdout)):
            with patch("check_worktree.os.getcwd", return_value="/tmp/some/unrelated/dir"):
                self.assertFalse(is_inside_worktree())


if __name__ == "__main__":
    unittest.main()
