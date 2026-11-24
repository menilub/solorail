# Spec: E02-ISS-02 — Feature Branch Required; Hard-Block main/master; verify-issue Opens a PR

**Issue ID:** E02-ISS-02
**Epic:** E-02 (Gate-Enforced Feature Delivery)
**Status:** IN_PROGRESS
**Started At:** 2026-11-24 22:00

---

## 1. Problem Statement

Two gaps in the delivery lifecycle:
1. `build-issue`'s branch check only **warns** when the agent is on `main`/`master`; a model can ignore the warning and edit application code anyway. There is no code-level (unbypassable) enforcement.
2. `verify-issue` only **prints** Git merge instructions at the end — it never actually opens a pull request, so closing an issue still requires a manual step outside SoloRail.

## 2. Technical Design

### 2.1 Hard Block on `main`/`master` (`scripts/enforce_gate.py`)

Add two small, mockable helpers (mirrors the style of `scripts/check_worktree.py`):

```python
def get_current_branch(cwd: str = None) -> str | None:
    """Return the current branch name via `git rev-parse --abbrev-ref HEAD`,
    or None if git is unavailable, the command fails, or cwd isn't a repo."""

def is_protected_branch(branch: str | None) -> bool:
    """True iff branch is exactly 'main' or 'master' (case-sensitive)."""
```

Wire into `main()`: immediately after the existing `.solorail/`/`.claude/`/`CLAUDE.md` exemption and the "no `.solorail/` dir" early-exit — i.e. only for application-code edits, before the active-issue/spec-allowlist checks — call:

```python
if is_protected_branch(get_current_branch()):
    block(
        f"BLOCKED [SoloRail]: Cannot edit application code directly on "
        f"'{branch}'. Create a feature branch first, e.g. "
        f"`git checkout -b feat/<ISSUE-ID>`."
    )
```

This exits 2 (hard block), not a warning — SoloRail state files remain editable on `main` (needed for `architect-issue` to write specs/update the sprint board before a branch exists).

### 2.2 `verify-issue` Opens a PR Instead of Printing Instructions

Replace Step 4 ("Worktree Cleanup: print merge/removal commands") with: if on a `feat/<ISSUE-ID>` or `hotfix/<BUG-ID>` branch, push it and run `gh pr create --base main --title "<ID>: <summary>" --body "..."`, report the PR URL. If already on the default branch, or the branch/PR is externally managed (e.g. a Conductor workspace branch), state that plainly and skip — no duplicate PR.

### 2.3 `build-issue` Step 1 Reflects the Hard Block

Reword Step 1 from "warn" to: STOP on `main`/`master`, tell the user a feature branch is required, and note that `enforce_gate.py` enforces this regardless (exit code 2) — the agent must not attempt to bypass it.

---

## 3. Allowlisted Files to Create/Modify

| File | Action |
|------|--------|
| `scripts/enforce_gate.py` | Modify: add `get_current_branch()`, `is_protected_branch()`, wire into `main()` |
| `scripts/test_enforce_gate.py` | Create: unit tests for the two new helpers |
| `skills/build-issue/SKILL.md` | Modify: Step 1 — hard stop, not a warning |
| `skills/verify-issue/SKILL.md` | Modify: Step 4 — open a PR via `gh`, not print instructions |
| `.solorail/specs/E02-ISS-02-spec.md` | Create: this spec |
| `.solorail/sprints/sprint-01.md` | Modify: status/hours tracking only |

**No-Go Constraints:**
- Do NOT modify `scripts/check_worktree.py`, `scripts/test_check_worktree.py`, or `skills/architect-issue/SKILL.md` (closed under E02-ISS-01).
- Do NOT modify `.solorail/RULES.md`, `.solorail/PRD.md`, or `.solorail/ROADMAP.md`.
- Do NOT touch `verify-issue`'s hours logic (Step 2) — that is E02-ISS-03's scope.
- Do NOT modify `scripts/sync_metrics.py`, `scripts/eval_metrics.py`, `scripts/session_start.py`, or any other skill's `SKILL.md`.

---

## 4. Test Cases (`scripts/test_enforce_gate.py`, stdlib `unittest`)

1. `is_protected_branch("main")` → `True`
2. `is_protected_branch("master")` → `True`
3. `is_protected_branch("feat/E02-ISS-02")` → `False`
4. `get_current_branch()` with mocked `subprocess.run` returning `"main\n"`, exit 0 → `"main"`
5. `get_current_branch()` with mocked `subprocess.run` returning non-zero exit → `None`
6. `get_current_branch()` with mocked `subprocess.run` raising `FileNotFoundError` → `None`

---

## 5. Acceptance Criteria Checklist

- [ ] `get_current_branch()` / `is_protected_branch()` implemented, all 6 tests pass.
- [ ] `enforce_gate.py` hard-blocks (exit 2) an app-code edit while on `main`/`master`; still allows `.solorail/` edits there.
- [ ] `build-issue/SKILL.md` Step 1 describes a hard stop, not a warning.
- [ ] `verify-issue/SKILL.md` Step 4 opens a PR via `gh pr create`, not just prints instructions.
- [ ] Existing `check_worktree` test suite still passes (regression check).
