# Technical Spec: E03-ISS-04

- **Issue:** Add `sprints/_TEMPLATE.md` and generate the next sprint with carryover
- **Epic:** E-03 (Day-2 Disruption Handling & Deterministic Status Sync)
- **Est:** 1.5h
- **Date:** 2026-11-25
- **Depends on:** E03-ISS-03 (closing a sprint is what permits generating the next), E03-ISS-02 (`list_sprint_files`, `resolve_active_sprint`), E03-ISS-01 (`replace_block` sentinels)

## Problem

`.solorail/retros/_TEMPLATE.md` and `.solorail/epics/_TEMPLATE.md` exist. **`.solorail/sprints/_TEMPLATE.md` does not.** Sprint-02 was hand-authored during this project's own evolve by copying sprint-01's shape by eye.

That matters more than it looks, because every consumer parses sprint boards by **exact marker match**:

| Consumer | Marker it requires |
| :--- | :--- |
| `sync_metrics.py` | `\| ID \|` table header, `## Metrics`, `## Time & Velocity Summary` |
| `enforce_gate.py` | `\| ID \|` rows, column 4 = Status |
| `solorail_state.py` | `Status:` in the header block |
| `eval_metrics.py` | `\| ID \|` rows |
| `compute_actual_hours.py` | column 7 = Started At |

A hand-authored board that drifts — a renamed heading, a reordered column, a missing `Status:` line — is **silently un-synced**. No error, just stale numbers, which is the whole class of bug Epic E-03 exists to kill. A template plus a generator removes the hand-authoring step entirely.

Separately, the evolve skill currently asks the user whether to initialize the next sprint and leaves an agent to write the file. Carryover of unfinished `TODO`/`BLOCKED` rows is prose instruction, not code, so it depends on an agent remembering to do it.

## Allowlisted Files to Create/Modify

- `.solorail/sprints/_TEMPLATE.md` *(create)* — the canonical board shape
- `scripts/next_sprint.py` *(create)* — generator CLI
- `scripts/test_next_sprint.py` *(create)*
- `scripts/solorail_state.py` *(modify)* — add carryover row extraction
- `scripts/sync_metrics.py` *(modify)* — **added mid-build**, see amendment below

No other file may be touched.

### Allowlist amendment — 2026-11-25: epic totals double-count carried rows

The original spec put `sync_metrics.py` out of scope. That was wrong: **the generator is what creates the duplicate-ID condition**, so shipping it without the aggregation fix would ship a corruption path.

A carried-over issue exists on two boards — as `TODO` on the sprint it came from, and as a carried `TODO` on its successor. `sync_metrics.py` aggregates `epic_est`/`epic_act` across **every** sprint file (by design, so closed sprints still feed ROADMAP), so it counts that issue twice.

Measured on a fixture: a single 10.0h unfinished issue carried once produced **`E-01 | 20.0h`** in `ROADMAP.md`. It also emitted a `Duplicate Issue ID` warning per carried row, which is a false positive — a carried issue is the same issue continuing, not a reused number, and noisy false warnings train people to ignore real ones.

**Fix:** epic aggregation dedupes by issue ID, with the **ACTIVE** sprint's row winning. Per-sprint totals are unaffected and still count every row on their own board, because a carried row genuinely is part of the new sprint's planned work. The duplicate warning now fires only for a true duplicate — the same ID twice on one board, or across boards without a carryover marker.

Added: `solorail_state.is_carryover_row`.

## Template contract

`.solorail/sprints/_TEMPLATE.md` carries placeholder tokens the generator substitutes:

```markdown
# Sprint {{NUMBER}}

- **Start Date:** {{START_DATE}}
- **End Date:** {{END_DATE}}
- **Capacity:** {{CAPACITY}}
- **Status:** ACTIVE

## Planned Issues
| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{{CARRYOVER_ROWS}}
<!-- solorail:metrics:start -->
## Metrics
| Metric | Planned | Actual |
| :--- | :--- | :--- |
| **Total Hours** | 0.0h | 0.0h |
| **Cut Hours** | 0.0h | 0.0h |
| **Issues Completed** | 0 | 0 |
| **Issues Cut** | — | 0 |
<!-- solorail:metrics:end -->

<!-- solorail:velocity-summary:start -->
## Time & Velocity Summary
- **Total Estimated (Active):** 0.0h
- **Total Cut:** 0.0h
- **Total Actual:** 0.0h
- **Completed / Total Active Issues:** 0 / 0
- **Scope Changes (Cut Issues):** 0
<!-- solorail:velocity-summary:end -->
```

The template ships **with sentinels already in place**, so a generated board is managed by `sync_metrics.py` from its first sync and never needs the heading-fallback migration path.

Placeholder tokens: `{{NUMBER}}`, `{{START_DATE}}`, `{{END_DATE}}`, `{{CAPACITY}}`, `{{CARRYOVER_ROWS}}`. Any unsubstituted `{{...}}` token in generated output is a bug (asserted by a test).

## Interface / Schema Contract

```python
# scripts/solorail_state.py  (additions)

def carryover_rows(lines: list[str]) -> list[str]:
    """Issue rows whose Status is TODO or BLOCKED, verbatim, in board order.
    These are the rows an unfinished sprint hands to its successor. DONE and
    CUT rows stay behind as that sprint's history."""

def reset_row_for_carryover(row: str) -> str:
    """A carried row with its Actual and Started At cells cleared and a note
    recording which sprint it came from. Est and Status are preserved: a
    BLOCKED issue stays blocked across the boundary."""
```

```python
# scripts/next_sprint.py

def next_sprint_number(sprints_dir: str) -> int:
    """Highest existing sprint number + 1; 1 when none exist."""

def render_template(template: str, number: int, start_date: str,
                    end_date: str, capacity: str,
                    carryover: list[str]) -> str:
    """Substitute every placeholder. Raises ValueError if any {{TOKEN}}
    remains, so a template/generator mismatch fails loudly instead of
    writing a half-filled board."""

def generate_next_sprint(solorail_dir: str, capacity: str = "20.0h",
                         weeks: int = 2, today: date = None,
                         force: bool = False) -> str:
    """Write the next sprint board and return its path.

    Refuses (RuntimeError) when a sprint is still ACTIVE unless force=True:
    two ACTIVE boards is the ambiguous state E03-ISS-02 has to warn about.
    Refuses to overwrite an existing file.
    """
```

CLI: `python3 scripts/next_sprint.py [--capacity 20.0h] [--weeks 2] [--force]`, printing the created path.

## Test Cases

`scripts/test_next_sprint.py`, stdlib-only, temp-dir fixtures:

1. **`next_sprint_number`** returns 1 on an empty dir, and `11` when `sprint-09.md` and `sprint-10.md` exist (numeric, not lexical — the ordering bug from ISS-02).
2. **Generated board parses cleanly.** After generating, `read_sprint_status` reads `ACTIVE`, and `sync_metrics.sync()` runs against it and updates both metric blocks — proving the template matches every marker the consumers require. *(This is the test that would have caught the drift risk.)*
3. **Carryover moves only `TODO` and `BLOCKED` rows.** A closed sprint with `DONE`, `CUT`, `TODO`, `BLOCKED` rows yields exactly the `TODO` and `BLOCKED` ones.
4. **Carried rows are reset.** `Actual` and `Started At` are cleared; `Est` and `Status` are preserved so a `BLOCKED` issue stays blocked; the note records the origin sprint.
5. **Refuses while a sprint is ACTIVE**, and succeeds with `force=True`.
6. **Refuses to overwrite** an existing sprint file.
7. **No unsubstituted token** appears in generated output; `render_template` raises on a leftover `{{TOKEN}}`.
8. **Dates are derived** — end date is `weeks * 7 - 1` days after start, matching the existing 2-week / 20.0h cadence in `CONTEXT.md`.

## No-Go Constraints

Must **not** be touched:

- `sync_metrics.py` — this issue only *produces* boards it can read; the metric-writing path is settled by `E03-ISS-01`.
- `hooks/hooks.json` — `E03-ISS-06`.
- `enforce_gate.py` allowlist model and the `main`/`master` block (ADR-002).
- Existing sprint-01 / sprint-02 files. The generator creates `sprint-03.md` only when asked; it is not run as part of this issue's verification against the live repo.
- The evolve skill's prose. Wiring the generator into `/solorail:evolve` is a plugin-skill change, deliberately left out of this issue's allowlist; the CLI is the deliverable.

## Risk Notes

- A generator that writes a subtly wrong board is worse than hand-authoring, because it scales the mistake. Test 2 guards this by running the real `sync()` against generated output rather than asserting on strings.
- `generate_next_sprint` must never clobber a board. Both the ACTIVE-sprint refusal and the overwrite refusal are hard failures, not warnings.

## Definition of Done

- [ ] All 8 tests pass; full suite green via `python3 -m unittest discover -s scripts`.
- [ ] A generated board survives a real `sync_metrics.sync()` with both metric blocks updated.
- [ ] `TODO`/`BLOCKED` rows carry over with `Actual`/`Started At` cleared; `DONE`/`CUT` stay behind.
- [ ] Generation refuses while a sprint is `ACTIVE` and refuses to overwrite.
- [ ] No `{{TOKEN}}` survives in generated output.
- [ ] Live repo untouched: `sprint-01.md` and `sprint-02.md` byte-identical, no `sprint-03.md` created.
