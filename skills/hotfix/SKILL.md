---
name: hotfix
description: Fast-track a small bug fix or regression (<= 1h) with a regression test, surgical fix, and sprint time logging.
argument-hint: "<bug description>"
---

# SoloRail Hotfix Skill (Fast-Track Bug Workflow)

When the user invokes `/solorail:hotfix <bug description>`:

1. **Branch Isolation Check:**
   - Run `git branch --show-current`. If currently on a `feat/*` branch with uncommitted changes, offer to stash and create an isolated worktree (`git worktree add ../wt-hotfix -b hotfix/BUG-XX`) so bug fixes never contaminate feature branches.
2. **Scoped Context Read:** Read `.solorail/CONTEXT.md` and the active `.solorail/sprints/sprint-XX.md`.
3. **Register Bug Issue:**
   - Determine the next sequential `BUG-XX` ID from `sprint-XX.md`.
   - Append a new row to `.solorail/sprints/sprint-XX.md` with Epic `HOTFIX`, Status `IN_PROGRESS`, Est `1.0h`, and `Started At` (`YYYY-MM-DD HH:MM`).
4. **Reproduce & Fix (TDD):**
   - Write a minimal failing regression test reproducing the bug.
   - Apply the smallest surgical fix to make the test pass and verify the full suite stays green.
5. **Close & Clean Up:**
   - Ask the user to confirm actual time spent, mark `BUG-XX` as `DONE` in `sprint-XX.md`, and output merge/worktree cleanup commands.
