# Technical Spec: E03-ISS-01

- **Issue:** Make `sync_metrics.py` write both metric blocks and splice non-destructively
- **Epic:** E-03 (Day-2 Disruption Handling & Deterministic Status Sync)
- **Est:** 1.5h
- **Date:** 2026-11-24

## Problem

`sync_metrics.py` has two defects that together make sprint status unreliable:

1. **The `## Metrics` table is never written.** The script only locates the marker `## Time & Velocity Summary` (line 111) and rewrites that block. The `## Metrics` table above it is hand-authored and drifts immediately. Sprint-01 read `6.5h / 0.0h / 0 completed` while the summary below correctly read `9.0h / 4.5h / 7-of-7`. Sprint-02 currently reads `0.0h / 0 / 0` against a correct `12.0h, 0/8`.
2. **The splice truncates to EOF.** Line 128 is `lines = lines[:sum_idx] + new_summary`, which deletes every line from the marker to end of file. Nothing can ever be added below the summary — including the PR section `E03-ISS-05` needs.

## Allowlisted Files to Create/Modify

- `scripts/sync_metrics.py` *(modify)*
- `scripts/test_sync_metrics.py` *(create)*

No other file may be touched by this issue.

## Interface / Schema Contract

Extract three pure, independently testable helpers, following the `enforce_gate.py` precedent from E02-ISS-02 (pure helpers + thin `main`):

```python
def replace_block(lines: list[str], marker: str, new_block: list[str]) -> list[str]:
    """Replace the section starting at `marker` up to (not including) the next
    top-level '## ' heading, preserving everything below. Appends `new_block`
    at EOF when `marker` is absent. Never truncates."""

def render_metrics_table(total_est: float, total_actual: float,
                         active_count: int, done_count: int,
                         cut_count: int) -> list[str]:
    """Render the '## Metrics' block. Planned column = planned values,
    Actual column = measured values."""

def render_velocity_summary(total_est: float, total_cut: float,
                            total_actual: float, done_count: int,
                            active_count: int, cut_count: int) -> list[str]:
    """Render the '## Time & Velocity Summary' block (existing format, unchanged)."""
```

`sync()` then calls `replace_block` twice — once per marker — so both blocks are written from the same computed totals and cannot disagree.

**Rendered `## Metrics` contract** (resolves the current ambiguity in the Planned/Actual columns):

| Row | Planned column | Actual column |
| :--- | :--- | :--- |
| `**Total Hours**` | `total_est_active` | `total_actual` |
| `**Issues Completed**` | `active_count` | `done_count` |
| `**Issues Cut**` | `0` | `cut_count` |

Block order within the file stays as-is (`## Metrics` above `## Time & Velocity Summary`). Both blocks must end with a trailing blank line so a following `## ` heading is never glued to the table.

## Test Cases

`scripts/test_sync_metrics.py`, stdlib-only (`unittest`), run as `python3 scripts/test_sync_metrics.py`:

1. **`replace_block` preserves content below the next heading.** Input with `## Time & Velocity Summary` followed by `## Pull Requests` and rows → the PR section survives verbatim. *(This is the RED test for the truncation bug.)*
2. **`replace_block` appends when the marker is absent.** No `## Metrics` heading present → block is appended at EOF, existing content untouched.
3. **`replace_block` handles the marker as the final section.** Nothing below the marker → behaves like the old path, no trailing garbage, no IndexError.
4. **`render_metrics_table` maps columns per the contract.** `(total_est=12.0, total_actual=0.0, active=8, done=0, cut=0)` → `| **Total Hours** | 12.0h | 0.0h |` and `| **Issues Completed** | 8 | 0 |`.
5. **End-to-end agreement on a fixture sprint file.** Write a temp sprint file with a stale `## Metrics` table, run `sync()` against it, assert both blocks report the same totals and that the stale numbers are gone.

## No-Go Constraints

Must **not** be touched by this issue:

- `scripts/enforce_gate.py`, `scripts/session_start.py`, `scripts/eval_metrics.py` — all three contain the `sprint_files[-1]` defect, which is **`E03-ISS-02`'s** scope. (Confirmed sites: `enforce_gate.py:47`, `session_start.py:14`, `eval_metrics.py:72`.)
- `hooks/hooks.json` — matcher changes belong to `E03-ISS-06`.
- Sprint `Status:` field writing — `E03-ISS-03`.
- Any `.solorail/` state file as a *deliverable*. The hook will rewrite sprint files as a side effect of running; that is expected, not an edit.
- The existing `## Time & Velocity Summary` output format — keep byte-identical so no downstream reader breaks.

## Risk Notes

- `sync_metrics.py` runs as a `PostToolUse` hook on every `Edit`/`Write`. A bug introduced here corrupts sprint files repo-wide and silently. Develop the helpers test-first and keep `sync()`'s file-writing path unchanged until tests pass.
- Because the hook fires on the very edits used to build this issue, verify against **temp-directory fixtures**, never against the live `.solorail/sprints/` files.

## Definition of Done

- [ ] All 5 tests pass via `python3 scripts/test_sync_metrics.py`.
- [ ] Existing suites still pass: `test_enforce_gate.py`, `test_check_worktree.py`, `test_compute_actual_hours.py`.
- [ ] Running `sync_metrics.py` on the live repo makes sprint-02's `## Metrics` table read `12.0h / 0.0h`, `8 / 0`, `0 / 0`.
- [ ] A manually added section below `## Time & Velocity Summary` survives a sync.
