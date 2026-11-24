---
name: build-issue
description: Implement an Issue using strict RED-GREEN-REFACTOR TDD within allowlisted spec files.
argument-hint: "<ISSUE-ID, e.g. E01-ISS-01>"
---

# SoloRail Build Issue Skill (Stage 3)

**STEP 0: GATE CHECK**
Verify `.solorail/specs/<ISSUE-ID>-spec.md` exists and `<ISSUE-ID>` is `IN_PROGRESS` in `.solorail/sprints/sprint-*.md`. If not, ABORT and tell the user to run `/solorail:architect-issue <ISSUE-ID>` first.

1. **Branch Check (Hard-Blocked):** Run `git branch --show-current`. If it is `main` or `master`, STOP — do not edit any application code; tell the user a feature branch is required (e.g. `git checkout -b feat/<ISSUE-ID>`) and create one before proceeding. This is enforced regardless at the tool-call level: `scripts/enforce_gate.py` hard-blocks (exit code 2) any `Edit`/`Write` to application code on `main`/`master`, so do not attempt to work around it.
2. **TDD Execution Loop (RED → GREEN → REFACTOR):**
   - **RED:** Write failing automated tests matching `.solorail/specs/<ISSUE-ID>-spec.md` and run the test suite to verify failure.
   - **GREEN:** Write the simplest production code needed to pass the tests, obeying `.solorail/CONTEXT.md` conventions.
   - **REFACTOR:** Clean up duplication/naming while keeping tests green. Note: `enforce_gate.py` blocks edits to any file not listed in `<ISSUE-ID>-spec.md`.
3. **Checkpoint:** Summarize changed files and test results, and prompt the user to run `/solorail:verify-issue <ISSUE-ID>`.
