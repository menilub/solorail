# Technical Spec: E03-ISS-05

- **Issue:** Record a PR per issue, open it via `gh pr create`, show live state in status
- **Epic:** E-03 (Day-2 Disruption Handling & Deterministic Status Sync)
- **Est:** 2.0h
- **Date:** 2026-11-25
- **Depends on:** E03-ISS-01 (non-destructive splice makes a section below the summary possible at all)

## Problem

Nothing in `.solorail/` records a pull request. The original review found "no PR exists" as a cause of stale status; `E02-ISS-02` has since added a `gh pr create` step to the `verify-issue` skill, so **PRs do get opened — they just are not stored anywhere.** No status surface can show what was never recorded, and a merged PR stays invisible.

Concretely, this session's own PR #4 carries ten commits closing six issues, and no sprint board, epic, or receipt references it.

## Design decision: a managed section, not a table column

The issue table is parsed **by column index** by five consumers (`status` at index 4, `Started At` at index 7, and `Est`/`Actual` at 5/6). Appending a `PR` column would shift nothing today but makes the row format wider and more fragile for every future parser, and `sync_metrics.split_row` discards empty cells, so a blank PR cell changes the index of everything after it.

Instead, PRs live in a **managed `## Pull Requests` section** below the velocity summary, keyed by issue ID. This is only possible because `E03-ISS-01` stopped the splice truncating to EOF — before that, any such section was deleted on the next sync.

```markdown
<!-- solorail:pull-requests:start -->
## Pull Requests
| Issue | PR | State |
| :--- | :--- | :--- |
| E03-ISS-01 | #4 | OPEN |
<!-- solorail:pull-requests:end -->
```

`State` is a cached value refreshed on demand, never trusted as live truth — see below.

## Design decision: `gh` is optional and never blocks

`gh` may be absent, unauthenticated, or offline, and the repository may have no remote. Every `gh` call therefore:

- has a hard timeout (5s),
- returns `None` rather than raising on any failure,
- leaves the recorded `State` untouched when it cannot be refreshed.

A missing `gh` must degrade to "PR recorded, state unknown", never to a failed verify or a wrong state.

## Allowlisted Files to Create/Modify

- `scripts/pr_state.py` *(create)* — record, read, and refresh PR rows
- `scripts/test_pr_state.py` *(create)*
- `.solorail/sprints/_TEMPLATE.md` *(modify)* — ship the empty Pull Requests block
- `skills/verify-issue/SKILL.md` *(modify)* — record the PR it already opens
- `skills/status/SKILL.md` *(modify)* — display PR state

No other file may be touched.

## Interface / Schema Contract

```python
# scripts/pr_state.py

BLOCK_NAME = "pull-requests"

def parse_pr_rows(lines: list[str]) -> dict[str, dict]:
    """Recorded PRs as {issue_id: {"pr": "#4", "state": "OPEN"}}."""

def render_pr_table(rows: dict[str, dict]) -> list[str]:
    """The '## Pull Requests' block body, issue IDs sorted for stable diffs."""

def record_pr(sprint_path: str, issue_id: str, pr_ref: str,
              state: str = "UNKNOWN") -> None:
    """Insert or update one issue's PR row, writing through replace_block so
    the rest of the board is untouched. Idempotent."""

def normalize_pr_ref(raw: str) -> str:
    """'#4', '4', or a full GitHub PR URL -> '#4'. Returns '' when unparseable,
    so a malformed ref is never recorded as if valid."""

def query_pr_state(pr_ref: str, timeout: float = 5.0) -> str | None:
    """Live state via `gh pr view <n> --json state`: 'OPEN' | 'MERGED' |
    'CLOSED', or None when gh is missing, unauthenticated, offline, times out,
    or returns anything unexpected."""

def refresh_pr_states(sprint_path: str, timeout: float = 5.0) -> dict[str, str]:
    """Re-query every recorded PR and write back the states that resolved.
    Rows whose query returns None keep their previous value."""
```

CLI: `python3 scripts/pr_state.py record <ISSUE-ID> <PR>` and `python3 scripts/pr_state.py refresh`.

## Test Cases

`scripts/test_pr_state.py`, stdlib-only, `gh` always mocked:

1. **`normalize_pr_ref`** maps `#4`, `4`, `https://github.com/o/r/pull/4` → `#4`; returns `''` for `abc`, `''`, `#`, `#-1`.
2. **`record_pr` inserts** a row into a board that has no Pull Requests block, and the board's other content survives.
3. **`record_pr` is idempotent** — recording the same issue twice yields one row; recording a new PR for the same issue replaces it.
4. **Recording does not disturb the metric blocks** — a following `sync()` still updates them, and the PR section survives that sync. *(The interaction `E03-ISS-01` unblocked.)*
5. **`query_pr_state` returns None** when `gh` is missing (`FileNotFoundError`), exits non-zero, times out, or emits unparseable JSON.
6. **`query_pr_state` parses** `{"state":"MERGED"}` → `'MERGED'`.
7. **`refresh_pr_states` preserves** a prior state when the query returns None, and updates it when it resolves.
8. **Two issues, one PR** is representable — several issues may share a PR, as they do on this branch.
9. **A CLOSED sprint is not written** — recording against a frozen board is refused, consistent with `E03-ISS-01`.

## No-Go Constraints

Must **not** be touched:

- `scripts/sync_metrics.py` — it must remain unaware of the PR block; the block survives because the splice is bounded, not because sync manages it.
- `scripts/enforce_gate.py`, `scripts/spec_allowlist.py`, `scripts/solorail_state.py`, `scripts/next_sprint.py`, `scripts/sync_on_git.py`.
- `hooks/hooks.json` — PR refresh is on-demand, never a hook. A hook that shells out to `gh` on every edit would add network latency to the edit path.
- The issue table's column layout.
- Existing sprint boards' recorded content.

## Risk Notes

- **Shelling out to `gh` is the main hazard**: latency, auth prompts, and network failure. Hence the 5s timeout, the `None`-on-any-failure contract, refresh being explicitly on demand, and `gh` being mocked in every test.
- `record_pr` writes to a tracked sprint board. It goes through `replace_block`, which `E03-ISS-01` made non-destructive and idempotent, and refuses CLOSED boards.
- Recorded `State` is a cache. The status skill must label it as last-known rather than present it as live, or a stale `OPEN` on a merged PR is worse than showing nothing.

## Definition of Done

- [ ] All 9 tests pass; full suite green via `python3 -m unittest discover -s scripts`.
- [ ] `record_pr` then `sync_metrics.sync()` leaves both the PR section and the metric blocks correct.
- [ ] Every `gh` failure mode yields `None` and preserves the recorded state.
- [ ] Recording against a `CLOSED` board is refused.
- [ ] Live repo: this session's PR #4 is recorded for the issues it closes, and `refresh` reports its real state.
- [ ] `skills/verify-issue/SKILL.md` records the PR it opens; `skills/status/SKILL.md` shows state as last-known.
- [ ] A PR block whose start sentinel was stripped by the stale plugin cache still parses, and recording into it preserves existing rows.
