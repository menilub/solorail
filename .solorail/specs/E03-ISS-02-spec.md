# Technical Spec: E03-ISS-02

- **Issue:** Resolve the ACTIVE sprint by status, not `sprint_files[-1]`, across all scripts
- **Epic:** E-03 (Day-2 Disruption Handling & Deterministic Status Sync)
- **Est:** 1.5h
- **Date:** 2026-11-24

## Problem

Three scripts pick the sprint board by sorting the glob and taking the **last filename**:

| Site | Line | Consequence |
| :--- | :--- | :--- |
| `scripts/enforce_gate.py` | 44–47 | The gate looks for `IN_PROGRESS` in the newest file only. With sprint-02 present, an `IN_PROGRESS` issue in sprint-01 stops being enforced — the gate silently lets edits through. |
| `scripts/session_start.py` | 10–14 | The session banner can report against a `CLOSED` sprint. |
| `scripts/eval_metrics.py` | 67–72 | Telemetry can be generated for the wrong sprint. |

Filename order is not sprint state. `sprint-10.md` sorts before `sprint-9.md` under plain string sort, and a closed sprint sorts last whenever it is the highest-numbered file.

`sync_metrics.py` is a fourth consumer: it already reads `Status: CLOSED` via its own `is_closed_sprint`, so the status-reading logic exists but is duplicated rather than shared.

## Allowlisted Files to Create/Modify

- `scripts/solorail_state.py` *(create)* — shared sprint-resolution module
- `scripts/test_solorail_state.py` *(create)*
- `scripts/enforce_gate.py` *(modify)* — use the shared resolver
- `scripts/session_start.py` *(modify)* — use the shared resolver
- `scripts/eval_metrics.py` *(modify)* — use the shared resolver
- `scripts/sync_metrics.py` *(modify)* — delegate `is_closed_sprint` to the shared module, removing the duplicate
- `scripts/compute_actual_hours.py` *(modify)* — **added mid-build**, see amendment below

No other file may be touched.

### Allowlist amendment — 2026-11-24

`scripts/compute_actual_hours.py:40,44` carries the **same** `sprint_files[-1]` defect and was missed when this spec was written; the problem statement named only three sites. It was caught by the spec's own Definition of Done (`grep` clean across all scripts), not by inspection.

It is in scope because the DoD requires no last-filename selection to remain anywhere, and because the defect is identical: `compute_actual_hours.py` computes an issue's `Actual` hours from its `Started At` cell, so pointed at the wrong board it either finds no row and returns a default, or reads a stale one — silently corrupting the hours ADR-003 makes authoritative.

## Interface / Schema Contract

```python
# scripts/solorail_state.py

def sprint_number(path: str) -> int:
    """Numeric sprint index from a sprint-NN.md path; -1 when unparseable.
    Used for ordering, so sprint-10 sorts after sprint-9 (plain string sort
    gets this wrong)."""

def list_sprint_files(sprints_dir: str) -> list[str]:
    """All sprint-*.md paths, ordered by sprint_number, not by filename."""

def read_sprint_status(lines: list[str]) -> str | None:
    """The sprint's declared Status from its header block, upper-cased
    ('ACTIVE' | 'CLOSED' | ...), or None when absent. Only the header is
    consulted: scanning stops at the first table row or non-h1 heading, so an
    issue row mentioning the word cannot flip the board's status."""

def is_closed_sprint(lines: list[str]) -> bool:
    """True when read_sprint_status(lines) == 'CLOSED'."""

def resolve_active_sprint(sprints_dir: str) -> str | None:
    """The path of the sprint to act on, or None when there are no sprints."""
```

**`resolve_active_sprint` resolution order** — deterministic, and chosen to fail safe:

1. Exactly one sprint with `Status: ACTIVE` → that file.
2. More than one `ACTIVE` → the **lowest-numbered** one, with a warning on stderr. That is the oldest sprint still open, which is the one needing attention; picking the newest would hide a sprint someone forgot to close.
3. No `ACTIVE` sprint → the **highest-numbered** file, with a warning. Preserves today's behaviour as a fallback rather than returning None, so the gate does not start failing open the moment every sprint is closed.
4. No sprint files at all → `None`.

Callers keep their existing "no sprint" branches unchanged.

## Test Cases

`scripts/test_solorail_state.py`, stdlib-only, temp-dir fixtures:

1. **`sprint_number` orders numerically.** `list_sprint_files` returns `sprint-9.md` before `sprint-10.md`, which plain `sorted()` reverses.
2. **One ACTIVE sprint wins regardless of filename order.** sprint-01 `ACTIVE`, sprint-02 `CLOSED` → resolves sprint-01, *not* the last filename. This is the gate bug.
3. **No ACTIVE falls back to the highest-numbered file** and warns, rather than returning None.
4. **Multiple ACTIVE picks the lowest-numbered** and warns.
5. **`read_sprint_status` reads only the header.** A board whose issue row contains the text `CLOSED` in a Notes cell still reports its header status.
6. **`resolve_active_sprint` returns None** for an empty sprints directory.

Plus integration coverage that each caller now honours status:

7. **`enforce_gate.get_active_issue` finds an `IN_PROGRESS` issue in an ACTIVE sprint-01 while a CLOSED sprint-02 exists.** Fails against the current code.

## No-Go Constraints

Must **not** be touched:

- The sprint `Status:` **writer** — that is `E03-ISS-03`. This issue only *reads* status.
- `sprints/_TEMPLATE.md` / next-sprint generation — `E03-ISS-04`.
- `hooks/hooks.json` — `E03-ISS-06`.
- `enforce_gate.py`'s allowlist model, the `main`/`master` block (ADR-002), and its fail-open behaviour for a missing `.solorail/`. Only sprint selection changes.
- The `## Time & Velocity Summary` output format (byte-identical, per E03-ISS-01).

## Risk Notes

- **`enforce_gate.py` is the gate.** A bug here either blocks every edit or stops enforcing entirely. Keep every existing early-exit path intact and change only which file is read.
- `enforce_gate.py` and `session_start.py` run as hooks via `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py"`, so `sys.path[0]` is the scripts directory and a sibling-module import resolves. The new module must stay stdlib-only and import-safe with no side effects at import time.
- A stderr warning from a `SessionStart` or `PreToolUse` hook is surfaced to the user, so warnings must be short and only fire on genuinely ambiguous state.

## Definition of Done

- [ ] All tests pass via `python3 scripts/test_solorail_state.py`.
- [ ] Full suite green: `python3 -m unittest discover -s scripts`.
- [ ] No **caller** selects the sprint by last filename; all five go through `resolve_active_sprint`. The one remaining `sprint_files[-1]` is the resolver's own documented rule-3 fallback, on a numerically-ordered list.
- [ ] With sprint-01 `ACTIVE` and sprint-02 `CLOSED` in a fixture, the gate enforces sprint-01's `IN_PROGRESS` issue.
- [ ] `sync_metrics.py` has no duplicate `is_closed_sprint` implementation.
- [ ] The live repo still behaves: gate blocks a non-allowlisted path and permits an allowlisted one.
