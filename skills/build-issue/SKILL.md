---
name: build-issue
description: Implement an Issue using strict RED-GREEN-REFACTOR TDD within allowlisted spec files.
argument-hint: "<ISSUE-ID, e.g. E01-ISS-01>"
---

# SoloRail Build Issue Skill (Stage 3)

**STEP 0: GATE CHECK**
Verify `.solorail/specs/<ISSUE-ID>-spec.md` exists and `<ISSUE-ID>` is `IN_PROGRESS` in `.solorail/sprints/sprint-*.md`. If not, ABORT and tell the user to run `/solorail:architect-issue <ISSUE-ID>` first.

1. **Branch Check:** Run `git branch --show-current`. Warn the user before editing if directly on `main` or `master`.
2. **TDD Execution Loop (RED → GREEN → REFACTOR):**
   - **RED:** Write failing automated tests matching `.solorail/specs/<ISSUE-ID>-spec.md` and run the test suite to verify failure.
   - **GREEN:** Write the simplest production code needed to pass the tests, obeying `.solorail/CONTEXT.md` conventions.
   - **REFACTOR:** Clean up duplication/naming while keeping tests green. Note: `enforce_gate.py` blocks edits to any file not listed in `<ISSUE-ID>-spec.md`.
3. **Checkpoint:** Summarize changed files and test results, and prompt the user to run `/solorail:verify-issue <ISSUE-ID>`.
