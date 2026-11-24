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
   - Run `python3 scripts/compute_actual_hours.py <ISSUE-ID>` and log that value directly as `Actual` — it computes real elapsed wall-clock time from `Started At` to now, rounded to the nearest 0.5h (0.5h floor). Do not ask the user to self-report or confirm it. If the script errors (e.g. `Started At` missing/unparseable), fall back to asking the user, since `Actual` must be `> 0.0h`.
   - Update `.solorail/sprints/sprint-XX.md`: set Status to `DONE` and record that `Actual` hours value.
   - Check off completed criteria in `.solorail/epics/epic-XX-*.md`. If all Epic issues are `DONE`, mark the Epic `DONE` in both the Epic file and `.solorail/ROADMAP.md`.
3. **Generate Verification Receipt:** Write `.solorail/specs/<ISSUE-ID>-verified.json` with timestamp, issue ID, and verified file list.
4. **Open Pull Request:** If currently on a `feat/<ISSUE-ID>` or `hotfix/<BUG-ID>` branch, push it (`git push -u origin <branch>`) and open a pull request against the repository's default branch (`gh pr create --base main --title "<ID>: <summary>" --body "..."`), referencing the Issue ID — instead of only printing merge instructions. Report the PR URL. If already on the default branch, or the branch/PR is externally managed (e.g. a Conductor workspace branch), state that plainly and skip opening a duplicate PR.
5. **Record the Pull Request:** Whether you opened it or it already existed, record it against the Issue so a status surface can show it: `python3 scripts/pr_state.py record <ISSUE-ID> <PR-NUMBER-OR-URL>`. This writes a row into the active sprint board's `## Pull Requests` section and caches the PR's current state. Several Issues may share one PR — record each one. If `gh` is unavailable the state is stored as `UNKNOWN`; that is expected, not an error, and the PR reference is still recorded.
