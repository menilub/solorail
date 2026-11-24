# Spec: E02-ISS-03 — verify-issue Computes Actual Hours Automatically

**Issue ID:** E02-ISS-03
**Epic:** E-02 (Gate-Enforced Feature Delivery)
**Status:** IN_PROGRESS
**Started At:** 2026-11-24 22:45

---

## 1. Problem Statement

`verify-issue` Step 2 currently asks the user to confirm Actual hours, only *suggesting* elapsed time as a hint. The user wants it computed deterministically from the system clock — real elapsed wall-clock time between the issue's `Started At` (recorded in the sprint board by `architect-issue`) and the moment of verification — with no self-reported guess.

## 2. Technical Design

### 2.1 `scripts/compute_actual_hours.py`

```python
def compute_actual_hours(issue_id: str, sprints_dir: str, now: datetime = None) -> float | None:
    """Look up `issue_id`'s 'Started At' in the latest sprint-*.md file,
    compute elapsed hours to `now` (default: datetime.now()), round to the
    nearest 0.5h, floor at a 0.5h minimum. Returns None if the issue or a
    parseable Started At isn't found."""
```

- Parses the same sprint table row format `enforce_gate.py`/`check_worktree.py`'s siblings already rely on (`| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |`).
- Accepts `Started At` as `YYYY-MM-DD HH:MM` or `YYYY-MM-DD` (midnight assumed).
- Rounding: `round(elapsed_hours * 2) / 2`, then `max(result, 0.5)` — matches the existing 0.5h-increment convention seen elsewhere in the sprint board.
- CLI entry point: `python3 scripts/compute_actual_hours.py <ISSUE-ID>` prints the computed value (e.g. `1.5`) to stdout, or `ERROR` to stderr + exit 1 if not computable.

### 2.2 `verify-issue/SKILL.md` Step 2

Replace "Ask the user to confirm actual hours spent (suggesting elapsed time from `Started At`)" with: run `python3 scripts/compute_actual_hours.py <ISSUE-ID>` and log that value directly as `Actual` — no self-reported confirmation prompt. If the script errors (e.g. `Started At` missing), fall back to asking the user, since `Actual` must be `> 0.0h`.

---

## 3. Allowlisted Files to Create/Modify

| File | Action |
|------|--------|
| `scripts/compute_actual_hours.py` | Create |
| `scripts/test_compute_actual_hours.py` | Create: unit tests (stdlib `unittest`) |
| `skills/verify-issue/SKILL.md` | Modify: Step 2 |
| `.solorail/specs/E02-ISS-03-spec.md` | Create: this spec |
| `.solorail/sprints/sprint-01.md` | Modify: status/hours tracking only |

**No-Go Constraints:**
- Do NOT modify `scripts/enforce_gate.py`, `scripts/check_worktree.py`, `skills/build-issue/SKILL.md`, or `skills/architect-issue/SKILL.md` (closed under earlier issues).
- Do NOT modify `.solorail/RULES.md`, `.solorail/PRD.md`, or `.solorail/ROADMAP.md`.
- Do NOT change `verify-issue`'s Step 1, 3, or 4 (Definition of Done audit, verification receipt, PR step) — only Step 2's hours logic.

---

## 4. Test Cases (`scripts/test_compute_actual_hours.py`, stdlib `unittest`)

1. Elapsed 1.2h since `Started At` → rounds down to `1.0`.
2. Elapsed 1.3h since `Started At` → rounds up to `1.5`.
3. Elapsed 10 minutes since `Started At` → floors to the `0.5` minimum.
4. `now` before `Started At` (clock skew / bad data) → floors to the `0.5` minimum, never negative.
5. Issue ID not present in the sprint file → returns `None`.
6. `Started At` is `"-"` (not yet started) or unparseable → returns `None`.

---

## 5. Acceptance Criteria Checklist

- [ ] `compute_actual_hours()` implemented, all 6 tests pass.
- [ ] CLI (`python3 scripts/compute_actual_hours.py <ID>`) prints a numeric value for a real sprint row with a parseable `Started At`.
- [ ] `verify-issue/SKILL.md` Step 2 computes hours automatically; no self-report prompt in the normal path.
- [ ] Existing `check_worktree` and `enforce_gate` test suites still pass (regression check).
