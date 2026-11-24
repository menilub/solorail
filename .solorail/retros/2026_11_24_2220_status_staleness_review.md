# SoloRail Status Staleness — Root Cause Review

- **Date:** 2026-11-24 22:20
- **Trigger:** `/solorail:status` did not reflect reality after Sprint 01 completion, retro, and PR merges.
- **Scope reviewed:** `scripts/sync_metrics.py`, `scripts/session_start.py`, `scripts/enforce_gate.py`, `hooks/hooks.json`, `skills/status/SKILL.md`, `skills/evolve/SKILL.md`, `.solorail/sprints/*`.
- **Outcome:** 8 causes found; all routed into Epic E-03 as `E03-ISS-01` … `E03-ISS-08` (12.0h, Sprint 02).

---

## Part 1 — Why the status was not updated

### Cause 1 — `sync_metrics.py` never writes the `## Metrics` table → `E03-ISS-01`

Every sprint file carries **two** numeric blocks:

| Block | Written by | Result |
| :--- | :--- | :--- |
| `## Metrics` (Total Hours / Issues Completed / Issues Cut) | **Nobody — hand-authored** | Goes stale immediately |
| `## Time & Velocity Summary` | `sync_metrics.py` | Always correct |

`sync_metrics.py` only searches for the marker `## Time & Velocity Summary` (line 111) and rewrites that block. The `## Metrics` table is never parsed or updated.

Observed in sprint-01 immediately before evolve:

```
## Metrics                          <- STALE (hand-written, never synced)
| Total Hours       | 6.5h | 0.0h |   wrong: 9.0h planned, 4.5h actual
| Issues Completed  | 0    | 0    |   wrong: 7 completed
| Issues Cut        | 0    | 0    |

## Time & Velocity Summary          <- CORRECT (script-written)
- Total Estimated (Active): 9.0h
- Total Actual: 4.5h
- Completed / Total Active Issues: 7 / 7
```

Two tables disagreeing inside one file. Anyone — human or agent — reading `## Metrics` first sees "0 issues done, 0 hours spent" on a fully completed sprint. This is the single biggest source of the "status isn't updating" symptom.

### Cause 2 — the sync is destructive, truncating to EOF → `E03-ISS-01`

`sync_metrics.py:128`:

```python
lines = lines[:sum_idx] + new_summary
```

Keeps everything **above** the marker and replaces everything from the marker **to end of file**.

- Any section below the summary is silently deleted on the next `Edit`/`Write` anywhere in the repo.
- The `## Metrics` table survives only because it happens to sit above the summary.
- No "PR link", "Retro link", or "Sprint Status" section can ever be added below — the hook eats it.

Fix: splice only the block's own range.

```python
end = next((j for j in range(sum_idx + 1, len(lines))
            if lines[j].startswith("## ")), len(lines))
lines = lines[:sum_idx] + new_summary + lines[end:]
```

### Cause 3 — scripts read `sprint_files[-1]`, not the ACTIVE sprint → `E03-ISS-02`

Both `enforce_gate.py:17-20` and `session_start.py:12-14` sort the sprint glob and take the **last filename**. Now that `sprint-02.md` exists, both ignore sprint-01 entirely. Had sprint-01 still held an `IN_PROGRESS` issue, the gate would have stopped enforcing it. The session banner can likewise report against a `CLOSED` sprint.

Fix: select the sprint whose header reads `Status: ACTIVE`; treat more than one ACTIVE sprint as an error.

### Cause 4 — sprint `Status:` (ACTIVE → CLOSED) has no writer → `E03-ISS-03`

Nothing in the framework transitions the header. `sync_metrics.py` computes `done_count`/`active_count` but never writes a status, and the evolve skill's prose doesn't mention it. During this session's evolve, `ACTIVE` → `CLOSED` was edited **by hand**. If skipped, sprint-01 and sprint-02 would both read `ACTIVE`.

Fix: derive it — all rows `DONE`/`CUT` **and** a retro file present → `CLOSED`; any row `IN_PROGRESS`/`TODO`/`BLOCKED` → `ACTIVE`. Exactly one sprint may be ACTIVE, and closing one is what permits creating the next.

### Cause 5 — no sprint template, so each sprint is hand-authored → `E03-ISS-04`

`.solorail/retros/_TEMPLATE.md` exists; `.solorail/sprints/_TEMPLATE.md` does not. Sprint-02 was written from scratch, copying sprint-01's shape by eye. Because `sync_metrics.py` parses by exact markers (`| ID |`, `## Time & Velocity Summary`), any header or column drift yields a **silently un-synced** sprint.

Fix: add the template; have evolve generate sprint-(XX+1) from it, carrying over `TODO`/`BLOCKED` rows.

### Cause 6 — nothing opens or tracks a PR → `E03-ISS-05`

This is why "including PR review" felt broken: **there was no PR.**

- `CLAUDE.md` mandates a feature branch + PR per story, and E02-ISS-02 added the `main`/`master` hard block in `enforce_gate.py`.
- But the evolve skill's instructions end at *"Ask the user if they want to initialize the next sprint."* No branch step, no PR step, no PR link recorded.
- The evolve commit therefore landed on whatever branch was checked out (`menilub/solorail-status-v3`), with no PR opened and no reference in any `.solorail/` file.
- No field anywhere stores a PR per issue or per sprint, so no status surface can ever show PR state.

Fix (user chose full automation): add a `PR` column to the sprint issue table; `verify-issue`/`evolve` create the branch, commit, run `gh pr create`, and write the URL back; `/solorail:status` calls `gh pr view --json state` to show open/merged live.

### Cause 7 — metrics refresh only on `Edit|Write`; git events are invisible → `E03-ISS-06`

`hooks.json` fires `sync_metrics.py` on `PostToolUse` for `Edit|Write` only. Not on `SessionStart`, and not on a `git merge` / PR merge / `git checkout` (Bash isn't matched). That is exactly this session's situation: PRs #2 and #3 merged **outside** this workspace and nothing re-read the state. Status is only ever as fresh as the last Edit/Write made through Claude's own tools.

Fix: add `sync_metrics.py` to `SessionStart`, and a `Bash` `PostToolUse` matcher gated on the command touching git (`git merge|checkout|pull|commit`) so it doesn't run on every shell call.

### Cause 8 — the gate has no exemption for record-keeping → `E03-ISS-07`

`enforce_gate.py:66-72` exempts only `.solorail/`, `.claude/`, and `CLAUDE.md`. Every other path is blocked whenever no issue is `IN_PROGRESS`:

```
BLOCKED [SoloRail]: No issue is IN_PROGRESS.
Run `/solorail:architect-issue <ID>` (or `/solorail:hotfix`) first.
```

Writing this very review to `.context/` was blocked, as was a fallback to `/tmp` (the relative path from cwd doesn't start with `.solorail/`). Between sprints — exactly when retro and planning work happens — everything outside `.solorail/` is read-only, pushing the record-keeping SoloRail wants to encourage out of the repo.

Fix: always permit `.context/**` and other non-source record paths, keeping the `main`/`master` block (ADR-002) and the source-file allowlist intact.

---

## Part 2 — Planning decisions taken

Recorded here because they shaped the issue slicing:

| Question | Decision | Consequence |
| :--- | :--- | :--- |
| Where do the plumbing fixes live? | **Merge into E-03** | E-03 widened to "Day-2 Disruption Handling & Deterministic Status Sync"; PRD Section 5 title now understates it. |
| Truncation + `sprint_files[-1]` defects: hotfix or planned? | **Planned issues** | Folded into `ISS-01`/`ISS-02` rather than `/solorail:hotfix`; they are architectural, not isolated regressions. |
| Which metrics block survives? | **Keep both, synced** | `sync_metrics.py` must write two blocks; nothing removed from existing sprint files. |
| How far does PR automation go? | **Run `gh pr create`** + live state | `ISS-05` grew to 2.0h and now owns the status-dashboard integration too. |

---

## Part 3 — Residual risk

- **`ISS-01` and `ISS-02` fix live defects.** Until `ISS-01` lands, any `Edit`/`Write` in this repo can still delete sprint-file content below the summary marker. Until `ISS-02` lands, the gate is pointed at sprint-02 only.
- **Estimates are upper bounds.** Sprint 01's Estimation Accuracy Ratio was 0.50 — surgical script fixes ran at roughly half their estimate. The existing `CONTEXT.md` guardrail says to bias this issue shape downward.
- **`ISS-08` is the only issue covering the original PRD E-03 scope** (`hotfix` → `pivot` → `evolve`). If that path needs more than verification, E-03 will need a second slice.
