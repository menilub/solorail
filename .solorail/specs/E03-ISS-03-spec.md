# Technical Spec: E03-ISS-03

- **Issue:** Derive and write the sprint `Status:` transition automatically
- **Epic:** E-03 (Day-2 Disruption Handling & Deterministic Status Sync)
- **Est:** 1.5h
- **Date:** 2026-11-24
- **Depends on:** E03-ISS-02 (`resolve_active_sprint`), E03-ISS-01 (`replace_block`, frozen CLOSED sprints)

## Problem

The sprint header's `Status:` field has **no writer**. `sync_metrics.py` computes `done_count`/`active_count` but never acts on them, and the evolve skill's prose does not mention the transition. During Sprint 01's evolve the `ACTIVE` → `CLOSED` edit was made **by hand**; had it been skipped, sprint-01 and sprint-02 would both have read `ACTIVE` and `resolve_active_sprint` would now be warning about an ambiguous state on every hook invocation.

## Design decision: what closes a sprint

A sprint closes when **both** hold:

1. Every issue row is `DONE` or `CUT` (no `TODO`, `IN_PROGRESS`, or `BLOCKED`), **and**
2. a retro file exists at `.solorail/retros/sprint-NN-retro.md`.

The retro requirement is the safety interlock. Without it, a sprint would flip to `CLOSED` the instant the last issue was marked `DONE` — mid-session, as a side effect of an unrelated edit, before the developer had run `/solorail:evolve`. Requiring the retro means closure follows the lifecycle rather than racing it: `/solorail:evolve` writes the retro, and the next sync observes the sprint is closeable.

A sprint with **zero** issue rows never auto-closes; an empty board is a sprint not yet planned, not a finished one.

## Design decision: interaction with the CLOSED freeze

`E03-ISS-01` made `sync_metrics.py` skip CLOSED sprints entirely, so status derivation must not fight it. The rule:

- Status is derived **only for sprints that are not already CLOSED**.
- The `ACTIVE` → `CLOSED` write therefore happens exactly once, and the board freezes immediately after.
- Reopening a closed sprint stays a **deliberate human act** — edit the header back to `ACTIVE` — after which sync resumes managing it. Nothing automatic un-freezes history.

The reverse transition (`CLOSED` → `ACTIVE` because someone added a `TODO` row) is deliberately **not** automated: it would let an unrelated edit silently resurrect a closed sprint.

## Allowlisted Files to Create/Modify

- `scripts/solorail_state.py` *(modify)* — add the derivation and the header writer
- `scripts/test_solorail_state.py` *(modify)* — tests
- `scripts/sync_metrics.py` *(modify)* — apply the derived status before the freeze check

No other file may be touched.

## Interface / Schema Contract

```python
# scripts/solorail_state.py

def issue_statuses(lines: list[str]) -> list[str]:
    """Upper-cased Status cell of every issue row on the board, in order.
    Empty when the board has no issue rows."""

def retro_path_for(sprint_path: str) -> str:
    """The expected retro path for a sprint board:
    .solorail/sprints/sprint-07.md -> .solorail/retros/sprint-07-retro.md"""

def derive_sprint_status(lines: list[str], retro_exists: bool) -> str | None:
    """The status the board should declare, or None to leave it unchanged.

    Returns 'CLOSED' when every issue row is DONE/CUT, there is at least one
    row, and retro_exists. Returns None otherwise -- never 'ACTIVE', because
    automatically reopening a closed sprint would let an unrelated edit
    resurrect frozen history.
    """

def write_sprint_status(lines: list[str], status: str) -> list[str]:
    """Replace the header's Status value, preserving the line's existing
    markdown shape (e.g. '- **Status:** ACTIVE'). Returns the lines unchanged
    when no header Status line exists -- this function never invents one."""
```

`sync()` gains, per sprint, **before** the existing `is_closed_sprint` freeze check:

```python
derived = derive_sprint_status(lines, os.path.exists(retro_path_for(sp_path)))
if derived and read_sprint_status(lines) != derived:
    lines = write_sprint_status(lines, derived)
    print(f"SoloRail closed {basename}: all issues DONE/CUT and retro present")
```

The freeze check then sees `CLOSED` and skips the metric blocks, so a closing sprint's final sync writes the status and leaves the numbers as the last ACTIVE sync computed them.

## Test Cases

Added to `scripts/test_solorail_state.py`:

1. **Closes when all rows DONE/CUT and retro exists.** → `'CLOSED'`.
2. **Does not close while a `TODO` row remains**, even with a retro. → `None`.
3. **Does not close while an `IN_PROGRESS` or `BLOCKED` row remains.** → `None`.
4. **Does not close without a retro**, even with every row DONE. → `None`. *(The interlock.)*
5. **Empty board never closes.** → `None`.
6. **Never returns `'ACTIVE'`** — a CLOSED board with a fresh `TODO` row still yields `None`.
7. **`write_sprint_status` preserves the line shape** — `- **Status:** ACTIVE` becomes `- **Status:** CLOSED`, bold markers intact.
8. **`write_sprint_status` is a no-op with no header Status line.**
9. **`retro_path_for` maps sprints to retros** including a zero-padded number.
10. **End-to-end:** a fixture board with all rows DONE plus a retro file transitions to `CLOSED` after one `sync()`, and the metric blocks are left frozen on the following sync.

## No-Go Constraints

Must **not** be touched:

- `sprints/_TEMPLATE.md` and next-sprint generation — `E03-ISS-04`.
- `hooks/hooks.json` — `E03-ISS-06`.
- The `## Time & Velocity Summary` output format (byte-identical, per `E03-ISS-01`).
- `resolve_active_sprint`'s resolution order from `E03-ISS-02`.
- `enforce_gate.py`'s allowlist model and the `main`/`master` block (ADR-002).
- The evolve skill's prose — it may keep describing the transition; this issue makes the code authoritative, and rewriting plugin skill text is out of scope here.

## Risk Notes

- This writes to sprint files from a `PostToolUse` hook, so a wrong derivation mutates tracked state during an unrelated edit. The interlock (retro must exist) and the one-directional rule (never auto-`ACTIVE`) exist to bound that.
- Closing a sprint changes which board `resolve_active_sprint` returns, which changes what the gate enforces. A premature close would leave the gate pointing at a different sprint — hence no close while any row is still open.

## Definition of Done

- [ ] All new tests pass; full suite green via `python3 -m unittest discover -s scripts`.
- [ ] A fixture sprint with all rows DONE/CUT **and** a retro transitions to `CLOSED` on one sync.
- [ ] The same fixture **without** a retro stays `ACTIVE`.
- [ ] A fixture with one `TODO` row and a retro stays `ACTIVE`.
- [ ] Live repo: sprint-02 stays `ACTIVE` (6 open issues) and sprint-01 stays `CLOSED` and byte-identical.
- [ ] No automatic `CLOSED` → `ACTIVE` transition exists anywhere in the code.
