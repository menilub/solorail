---
name: verify-issue
description: Verify implementation against spec and Definition of Done, log actual hours, sync metrics, and write verification receipt.
argument-hint: "<ISSUE-ID, e.g. E01-ISS-01>"
---

# SoloRail Verify Issue Skill (Stage 4)

**STEP 0: GATE CHECK**
Run the full test suite and linter. If any check fails, ABORT and fix failures before closing. Inspect `git status --short` to ensure no stray debug files or unapproved edits exist.

1. **Definition of Done Audit:** Verify every acceptance criterion in `.solorail/specs/<ISSUE-ID>-spec.md` and parent `.solorail/epics/epic-XX-*.md` is met. Update `.solorail/CONTEXT.md` Domain Glossary if new domain terms were introduced.
2. **Log Hours & Close Issue:**
   - Ask the user to confirm actual hours spent (suggesting elapsed time from `Started At`).
   - Update `.solorail/sprints/sprint-XX.md`: set Status to `DONE` and record `Actual` hours (must be `> 0.0h`).
   - Check off completed criteria in `.solorail/epics/epic-XX-*.md`. If all Epic issues are `DONE`, mark the Epic `DONE` in both the Epic file and `.solorail/ROADMAP.md`.
3. **Generate Verification Receipt:** Write `.solorail/specs/<ISSUE-ID>-verified.json` with timestamp, issue ID, and verified file list.
4. **Worktree Cleanup:** Output exact Git merge and worktree removal commands if on a `feat/<ISSUE-ID>` branch.
