#!/usr/bin/env python3
"""Git worktree detection helper for SoloRail (E02-ISS-01).

Used by the `architect-issue` skill to decide whether to offer creating a new
isolated worktree. SoloRail must NOT offer to create a nested worktree when
the session is already running inside a *linked* worktree (e.g. a
Conductor-managed one, or one created by a prior `/solorail:architect-issue`
run). Running from the primary/main checkout is NOT considered "inside a
worktree" for this purpose -- that is the normal case where offering to
create one is still correct.

Detection relies on Git's own distinction: for a linked worktree,
`git rev-parse --git-dir` (e.g. `<common>/worktrees/<name>`) differs from
`git rev-parse --git-common-dir` (always the main repo's `.git`). In the
primary checkout, both resolve to the same directory.

Stdlib only (subprocess), no third-party dependencies.
"""

import os
import subprocess
import sys


def _git_dirs(cwd: str):
    """Return (git_dir, git_common_dir) as absolute paths for `cwd`, or
    (None, None) if `git` is unavailable, the command fails, or `cwd` is not
    inside a Git repository."""
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--git-dir", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None, None

    if result.returncode != 0 or not result.stdout:
        return None, None

    lines = result.stdout.splitlines()
    if len(lines) < 2:
        return None, None

    git_dir, git_common_dir = lines[0].strip(), lines[1].strip()
    if not git_dir or not git_common_dir:
        return None, None

    # `git rev-parse` may return a path relative to `cwd`; resolve it there.
    git_dir_abs = os.path.normpath(
        git_dir if os.path.isabs(git_dir) else os.path.join(cwd, git_dir)
    )
    git_common_dir_abs = os.path.normpath(
        git_common_dir
        if os.path.isabs(git_common_dir)
        else os.path.join(cwd, git_common_dir)
    )
    return git_dir_abs, git_common_dir_abs


def is_inside_worktree(cwd: str = None) -> bool:
    """Detect whether `cwd` (default: os.getcwd()) is inside a *linked* Git
    worktree, as opposed to the primary/main checkout.

    Returns False (never raises) if Git is unavailable, the command fails,
    `cwd` is not inside a Git repository, or `cwd` is the main checkout.
    """
    target = cwd if cwd is not None else os.getcwd()
    try:
        target_abs = os.path.abspath(target)
    except (TypeError, ValueError):
        return False

    git_dir, git_common_dir = _git_dirs(target_abs)
    if git_dir is None or git_common_dir is None:
        return False

    return git_dir != git_common_dir


def main() -> int:
    """CLI entry point: prints 'true' or 'false' and exits 0. Intended for
    use from the architect-issue skill via Bash, e.g.:
        python3 scripts/check_worktree.py
    """
    print("true" if is_inside_worktree() else "false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
