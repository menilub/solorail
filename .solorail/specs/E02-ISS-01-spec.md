# Spec: E02-ISS-01 — Detect Existing Worktree Before Offering Creation

**Issue ID:** E02-ISS-01  
**Epic:** E-02 (Gate-Enforced Feature Delivery)  
**Status:** IN_PROGRESS  
**Started At:** 2026-11-24 15:30  

---

## 1. Problem Statement

When running `/solorail:architect-issue` inside a Conductor worktree (e.g., `vientiane` or `zurich`), the skill currently offers to create a new nested worktree (e.g., `../wt-E02-ISS-01`), which violates Git worktree isolation rules and confuses directory navigation. The skill should **detect** that it is already inside an active worktree and **skip** the worktree creation offer entirely.

---

## 2. Technical Design

### 2.1 Worktree Detection Logic

**Input:** Current working directory (or any directory within it).

**Output:** Boolean: `True` if inside an active Git worktree, `False` otherwise.

**Method:**
1. Run `git worktree list --porcelain` and parse the output.
2. For each worktree line, extract the worktree path (first column).
3. Check if the current working directory is a descendant of any active worktree path (use `os.path.commonpath` or string prefix matching).
4. Return `True` if a match is found; `False` otherwise.

**Example Output (git worktree list --porcelain):**
```
/Users/menilub/IdeaProjects/solorail-v1 (main)
/Users/menilub/conductor/workspaces/solorail-v1/vientiane (menilub/solorail-status-v2)
/Users/menilub/conductor/workspaces/solorail-v1/zurich (menilub/feature-X)
```

If `cwd` is `/Users/menilub/conductor/workspaces/solorail-v1/vientiane/src`, it matches the second worktree.

### 2.2 Allowlisted Files to Create/Modify

| File | Purpose | Action |
|------|---------|--------|
| `scripts/check_worktree.py` | Stdlib helper: detects if cwd is inside an active Git worktree | Create |
| `scripts/test_check_worktree.py` | Unit tests (stdlib `unittest`) for `check_worktree.py` | Create |
| `skills/architect-issue/SKILL.md` | Skill instructions | Modify: Step 4 checks worktree status via `check_worktree.py` before offering creation |
| `.solorail/specs/E02-ISS-01-spec.md` | This spec receipt | Create |
| `.solorail/sprints/sprint-01.md` | Sprint board | Modify: status/hours updates only |

**No-Go Constraints:**
- Do NOT modify `.solorail/RULES.md`, `.solorail/PRD.md`, or `.solorail/ROADMAP.md`.
- Do NOT modify `scripts/enforce_gate.py`, `scripts/sync_metrics.py`, `scripts/eval_metrics.py`, or `scripts/session_start.py`.
- Do NOT modify other issue specs, epics, or other skills' `SKILL.md` files.

---

## 3. Interface / Schema Contract

### 3.1 Function Signature (Python)

```python
def is_inside_worktree(cwd: str = None) -> bool:
    """
    Detect if the current working directory is inside an active Git worktree.
    
    Args:
        cwd (str, optional): Working directory to check. Defaults to os.getcwd().
    
    Returns:
        bool: True if inside a worktree, False otherwise (or if Git fails).
    """
    pass
```

### 3.2 Usage in `architect-issue` Skill

**Current (buggy):**
```
If not already in a worktree, offer: "Create isolated worktree? (y/n)"
```

**After fix:**
```
already_in_worktree = is_inside_worktree()
if already_in_worktree:
    print("ℹ️ Already inside Git worktree. Skipping worktree creation.")
else:
    print("Create isolated worktree? (y/n)")
```

---

## 4. Test Cases

### Test 1: Inside Conductor Worktree
- **Setup:** Call `is_inside_worktree()` from within `/Users/menilub/conductor/workspaces/solorail-v1/vientiane/`.
- **Expected:** `True`
- **Rationale:** Conductor worktree is active; should detect it.

### Test 2: Inside Nested Directory of Conductor Worktree
- **Setup:** Call `is_inside_worktree()` from `/Users/menilub/conductor/workspaces/solorail-v1/vientiane/.solorail/specs/`.
- **Expected:** `True`
- **Rationale:** Subdirectory should still match parent worktree.

### Test 3: In Main Repo (Not in Worktree)
- **Setup:** Call `is_inside_worktree()` from `/Users/menilub/IdeaProjects/solorail-v1/` (main checkout).
- **Expected:** `False`
- **Rationale:** Main repo is not a worktree; should not detect one.

### Test 4: Nonexistent Directory
- **Setup:** Call `is_inside_worktree("/nonexistent/path")`.
- **Expected:** `False`
- **Rationale:** Graceful fallback; should not crash.

### Test 5: Git Command Fails (No .git)
- **Setup:** Call `is_inside_worktree()` from a directory outside any Git repo.
- **Expected:** `False` (exception caught and logged)
- **Rationale:** Graceful error handling; skill continues without worktree creation.

---

## 5. Acceptance Criteria Checklist

- [ ] Worktree detection function is implemented and passes all 5 test cases.
- [ ] `architect-issue` skill checks for existing worktree before offering creation.
- [ ] Running `/solorail:architect-issue` inside `vientiane` does NOT offer worktree creation.
- [ ] Running `/solorail:architect-issue` in a fresh main repo DOES offer worktree creation.
- [ ] All existing tests (if any) still pass.
- [ ] Skill output clearly indicates whether worktree creation is skipped.

---

## 6. No-Go Constraints

- **Do NOT** refactor or rewrite the entire `architect-issue` skill.
- **Do NOT** modify Git worktree creation logic itself; only add a check before the offer.
- **Do NOT** add external dependencies (must use stdlib only).
- **Do NOT** change the user-facing CLI interface or command syntax.

---

## 7. Notes & Decisions

- The detection uses `git worktree list --porcelain` for reliable, scriptable output parsing.
- Path matching is case-sensitive on Linux/macOS and case-insensitive on Windows (use `pathlib.Path` for portability).
- Errors (e.g., Git not found, `.git/` missing) are caught and logged; the skill continues with `is_inside_worktree() → False` as the safe default.
