# Epic E-03: Day-2 Disruption Handling & Deterministic Status Sync

- **Status:** ACTIVE
- **Goal:** Sprint, roadmap, and PR state update themselves from the work actually done, so `/solorail:status` is never stale and no human ever hand-edits a number or a status field. Covers both the status/progress plumbing and the Day-2 disruption commands (`hotfix` / `pivot` → `evolve`) that depend on it.
- **Out of Scope:**
  - External issue tracker sync (Jira, Linear, GitHub Issues) — PRD non-goal.
  - Token/cost scraping or remote telemetry — PRD non-goal.
  - Multi-developer or team status surfaces — PRD non-goal.
  - Rewriting the gate's core allowlist model; only its record-keeping exemptions change.
  - CI/CD or auto-merge of the PRs this epic opens.

## Acceptance Criteria
- [x] No number in any `.solorail/sprints/sprint-*.md` is hand-authored; every metric block is script-written and the two blocks always agree. *(E03-ISS-01)*
- [x] `sync_metrics.py` never deletes content below the block it rewrites — verified at `##`, `###` and `#` levels, with indented and fenced marker mentions, and on CLOSED sprints. *(E03-ISS-01, after a reopen: this was prematurely checked off once and falsified by code review.)*
- [x] Every script resolves the sprint by `Status: ACTIVE`, not by filename order. *(E03-ISS-02 — 4 call sites unified behind `solorail_state.resolve_active_sprint`)*
- [x] A sprint's `Status:` transitions `ACTIVE` → `CLOSED` automatically, derived from its issue rows plus the retro's existence. *(E03-ISS-03 — one-directional: never auto-reopens)*
- [x] A template + generator produce the next sprint, carrying over `TODO`/`BLOCKED` rows. *(E03-ISS-04 — `scripts/next_sprint.py`; wiring it into `/solorail:evolve` is a skill-prose change still outstanding)*
- [ ] Each issue records its PR, `verify-issue`/`evolve` open it via `gh pr create`, and `/solorail:status` shows live open/merged state.
- [x] Metrics refresh on `SessionStart` and after git-touching Bash commands, so an externally merged PR is reflected without a manual re-sync. *(E03-ISS-06 — read-only git excluded)*
- [ ] Record-keeping writes (retros, reviews, `.context/`) are permitted between issues without an `IN_PROGRESS` issue.
- [ ] The `hotfix` → `pivot` → `evolve` path is verified end-to-end against the new status machinery.

## Issue Breakdown
- `E03-ISS-01`: Make `sync_metrics.py` write both metric blocks and splice non-destructively (Est: 1.5h)
- `E03-ISS-02`: Resolve the ACTIVE sprint by status, not `sprint_files[-1]`, across all scripts (Est: 1.5h)
- `E03-ISS-03`: Derive and write the sprint `Status:` transition automatically (Est: 1.5h)
- `E03-ISS-04`: Add `sprints/_TEMPLATE.md` and generate the next sprint with carryover (Est: 1.5h)
- `E03-ISS-05`: Record a PR per issue, open it via `gh pr create`, show live state in status (Est: 2.0h)
- `E03-ISS-06`: Refresh metrics on SessionStart and git-touching Bash commands (Est: 1.0h)
- `E03-ISS-07`: Allow record-keeping writes between issues in `enforce_gate.py` (Est: 1.0h)
- `E03-ISS-08`: Verify `hotfix` → `pivot` → `evolve` end-to-end against the new status machinery (Est: 2.0h)
- `E03-ISS-09`: Parse a real allowlist section instead of substring-matching the whole spec (Est: 1.5h)

**Total: 13.5h** (Sprint 02 capacity 20.0h)

### Sequencing notes
- `ISS-01` and `ISS-02` are foundational — both fix live data-loss/targeting bugs and everything below reads the state they repair. Build them first, in that order.
- `ISS-03` depends on `ISS-02` (it must know which sprint is active to transition it).
- `ISS-04` depends on `ISS-03` (closing a sprint is what permits generating the next).
- `ISS-05` depends on `ISS-01` (the PR section can only live below the summary once the splice stops truncating).
- `ISS-08` is last by construction — it exercises everything above.

## Known Defects Being Fixed
| Finding | Location | Issue |
| :--- | :--- | :--- |
| `## Metrics` table never synced; disagrees with the summary block | `sync_metrics.py` (no code path) | `E03-ISS-01` |
| Splice truncates file to EOF, silently deleting anything below the marker | `sync_metrics.py:128` | `E03-ISS-01` |
| Gate reads `sprint_files[-1]`, so it now targets sprint-02 and ignores an active sprint-01 | `enforce_gate.py:17-20` | `E03-ISS-02` |
| Session banner reads `sprint_files[-1]`, can report a CLOSED sprint | `session_start.py:12-14` | `E03-ISS-02` |
| Sprint `Status:` has no writer; was hand-edited during Sprint 01 evolve | evolve skill prose | `E03-ISS-03` |
| No `sprints/_TEMPLATE.md`; every sprint hand-authored, risking marker drift | `.solorail/sprints/` | `E03-ISS-04` |
| No PR is opened or recorded anywhere in the lifecycle | evolve + verify-issue skills | `E03-ISS-05` |
| Metrics fire only on `Edit|Write`; git merges are invisible | `hooks/hooks.json` | `E03-ISS-06` |
| Gate blocks all non-`.solorail/` writes between issues, including `.context/` notes | `enforce_gate.py:66-72` | `E03-ISS-07` |

## Scope & Requirement Change Log
| Date | Change Description | Reason | Sprint Impact |
| :--- | :--- | :--- | :--- |
| 2026-11-24 | Initial Epic created | Baseline scope per PRD Section 5 (`hotfix` / `pivot` → `evolve`) | Drafted, unscheduled |
| 2026-11-24 | Merged deterministic status/progress sync into E-03 scope | Post-Sprint-01 review found 7 causes of stale status; the Day-2 commands depend on correct status plumbing, so splitting them into a separate epic would have ordered the work wrongly. User chose "merge both into E-03". | +12.0h added to Sprint 02 |
| 2026-11-24 | Truncation and `sprint_files[-1]` defects planned as issues rather than hotfixes | User chose planned issues over `/solorail:hotfix`; they are architectural, not isolated regressions. | Folded into `ISS-01`/`ISS-02` |
| 2026-11-25 | Added `E03-ISS-09` after verifying `E03-ISS-07` exposed a gate bypass: the allowlist check substring-matches the whole spec file, so any filename mentioned in prose — including in a no-go list — becomes writable. | Defeats the gate enforcing every other issue. | +1.5h to Sprint 02 |
| 2026-11-24 | Both metric blocks retained and synced | User chose "keep both, synced" over deleting either — nothing is removed from existing sprint files. | Scope of `ISS-01` |
