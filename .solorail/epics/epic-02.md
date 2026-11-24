# Epic E-02: Gate-Enforced Feature Delivery

- **Status:** DONE
- **Goal:** Architect → Build → Verify stages run with a hard-blocking spec gate, deterministic worktree isolation, and reliable TDD enforcement so solo developers can't drift out of scope or skip tests.
- **Out of Scope:** Re-architecting the gate script itself, multi-worktree orchestration, non-Git VCS support.

## Acceptance Criteria
- [x] `architect-issue` never offers to create a nested Git worktree when the session is already running inside one.
- [x] Every issue is developed on its own feature branch — `build-issue`'s branch-check gate hard-blocks (not just warns) edits made directly on `main`/`master`.
- [x] `verify-issue` opens a pull request to close out an issue instead of only printing merge instructions.
- [x] `verify-issue` computes `Actual` hours itself from real elapsed time instead of asking the user to self-report.

## Issue Breakdown
- `E02-ISS-01`: `architect-issue` should check whether the session is already inside a Git worktree before offering/suggesting to create a new nested worktree (Est: 1.0h)
- `E02-ISS-02`: Require a feature branch per issue, hard-block edits on main/master in build-issue's gate, and have verify-issue open a PR to close the issue (Est: 1.5h)
- `E02-ISS-03`: `verify-issue` should compute `Actual` hours automatically (real elapsed wall-clock time between an Issue's `Started At` and verification, read from the system clock / file mtimes — not a self-reported guess) instead of asking the user to confirm hours (Est: 1.0h)

## Scope & Requirement Change Log
| Date | Change Description | Reason | Sprint Impact |
| :--- | :--- | :--- | :--- |
| 2026-11-24 | Pivot: added E02-ISS-01 — detect existing worktree before offering to create one | Discovered mid-sprint during E01-ISS-01 architect step; architect-issue suggested creating `../wt-E01-ISS-01` while already inside the Conductor worktree `zurich` | +1.0h to Sprint 01 (5.5h → 6.5h) |
| 2026-11-24 | Pivot: added E02-ISS-02 — feature branch + PR required per issue, main/master hard-blocked | User policy: never work directly on main; every issue must land via branch + PR | +1.5h to Sprint 01 (6.5h → 8.0h) |
| 2026-11-24 | Pivot: added E02-ISS-03 — verify-issue computes Actual hours itself instead of asking | User wants hours logged from measured elapsed time, not self-reported estimates, during E01-ISS-02 verification | +1.0h to Sprint 01 (8.0h → 9.0h) |
