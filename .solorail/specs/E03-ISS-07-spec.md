# Technical Spec: E03-ISS-07

- **Issue:** Allow record-keeping writes between issues in `enforce_gate.py`
- **Epic:** E-03 (Day-2 Disruption Handling & Deterministic Status Sync)
- **Est:** 1.0h
- **Date:** 2026-11-25

## Problem

`enforce_gate.py:97-103` exempts only `.solorail/`, `.claude/`, and `CLAUDE.md`. Every other path is blocked whenever no issue is `IN_PROGRESS`:

```
BLOCKED [SoloRail]: No issue is IN_PROGRESS.
Run `/solorail:architect-issue <ID>` (or `/solorail:hotfix`) first.
```

Observed directly in this project: writing the post-sprint status review to `.context/` was blocked, and so was a fallback to `/tmp` (an absolute path outside the repo normalizes to `../../..`, which matches no exemption). Between sprints — exactly when retro, review and planning work happens — everything outside `.solorail/` is read-only. That pushes the record-keeping SoloRail exists to encourage out of the repo entirely.

### Second defect, same function (previously logged as a loose end)

`main()` reads stdin whenever it is not a tty:

```python
if not sys.stdin.isatty():
    data = json.load(sys.stdin)
```

Invoked with a path as `argv[1]` from a non-interactive context whose stdin is an open pipe, `json.load` blocks forever. This happened in practice during this epic: a verification command hung for 120s and had to be killed. `argv` is already supported as a fallback, so the fix is to prefer it and never block waiting for input that is not coming.

## Design decision: what counts as record-keeping

Exempt paths that **record** work rather than perform it:

| Path | Why |
| :--- | :--- |
| `.solorail/**` | Already exempt — lifecycle state |
| `.claude/**`, `CLAUDE.md` | Already exempt — agent configuration |
| `.context/**` | Workspace scratch and agent collaboration; gitignored |
| `.solorail/retros/**`, `.solorail/archive/**` | Covered by `.solorail/**`; named here for clarity |

**Explicitly rejected:** a blanket `*.md` exemption. It reads as harmless but would unlock `README.md`, every doc under a source tree, and any `.md` an issue's spec deliberately left off its allowlist — turning a scope gate into a suggestion. Documentation is often exactly what an issue is scoped to change, so it must stay inside the allowlist.

Record-keeping paths bypass the `main`/`master` block as well, matching how `.solorail/` already behaves. ADR-002 protects *application code* on protected branches; a retro or a scratch note is not that, and blocking it would make `/solorail:evolve` unusable on `main`.

## Allowlisted Files to Create/Modify

- `scripts/enforce_gate.py` *(modify)* — record-keeping exemption + stdin fix
- `scripts/test_enforce_gate.py` *(modify)* — tests

No other file may be touched.

## Interface / Schema Contract

```python
# scripts/enforce_gate.py

RECORD_KEEPING_PREFIXES = (".solorail/", ".claude/", ".context/")
RECORD_KEEPING_FILES = ("CLAUDE.md",)

def is_record_keeping_path(rel_path: str) -> bool:
    """True for paths that record work rather than perform it, which stay
    writable with no issue IN_PROGRESS and on a protected branch.

    Returns False for a path that escapes the repository root ('../'), so an
    absolute path outside the repo is never silently exempt.
    """

def read_target_path(argv: list[str] | None = None) -> str:
    """The hook's target path: argv[1] when present, otherwise the
    PostToolUse/PreToolUse JSON payload on stdin.

    argv is checked FIRST and stdin is not read at all when argv supplies a
    path, because json.load on an open pipe that never closes blocks forever.
    """
```

## Test Cases

Added to `scripts/test_enforce_gate.py`:

1. **Record-keeping paths are exempt.** `.solorail/retros/x.md`, `.solorail/archive/adr-history.md`, `.context/notes.md`, `.claude/settings.json`, `CLAUDE.md` → `True`.
2. **Source and docs paths are not exempt.** `scripts/sync_metrics.py`, `README.md`, `hooks/hooks.json`, `src/app.py`, `docs/guide.md` → `False`. *(Guards against the rejected blanket `*.md`.)*
3. **A path escaping the repo is not exempt.** `../../tmp/x.md`, `../outside.md` → `False`.
4. **`.context` prefix is matched as a directory**, not a string prefix: `.contextual/file.md` → `False`.
5. **`read_target_path` prefers argv and does not touch stdin.** With `argv=['prog','a/b.py']` and a stdin that would block if read, returns `a/b.py`. *(The hang regression.)*
6. **`read_target_path` falls back to the stdin payload** when argv has no path, reading `tool_input.file_path` and `tool_input.path`.
7. **`read_target_path` returns `''` on malformed stdin** rather than raising.

## No-Go Constraints

Must **not** be touched:

- The allowlist-matching logic itself (`rel_path in spec_content`) — out of scope, and its known looseness (basename matching) is a separate concern.
- `is_protected_branch` / `get_current_branch` and the ADR-002 block for non-record paths.
- `get_active_issue` and `resolve_active_sprint` — settled by `E03-ISS-02`.
- `hooks/hooks.json` — `E03-ISS-06`.
- `scripts/sync_metrics.py`, `scripts/solorail_state.py`.

## Risk Notes

- **This widens the gate.** Every added exemption is a path an agent may write with no spec receipt. The exemption list is therefore explicit, prefix-anchored to directory boundaries, and refuses anything containing `../`. Test 2 exists to catch a future broadening.
- `enforce_gate.py` is the gate: a bug either blocks every edit or stops enforcing. All existing early-exit paths and the fail-open behaviour for a missing `.solorail/` stay intact.

## Definition of Done

- [ ] All new tests pass; full suite green via `python3 -m unittest discover -s scripts`.
- [ ] With **no** issue `IN_PROGRESS`, a write to `.context/x.md` is permitted and a write to `README.md` is still blocked.
- [ ] `python3 scripts/enforce_gate.py <path>` returns immediately and never hangs, with stdin an open pipe.
- [ ] A path outside the repository root is not exempt.
- [ ] `README.md` and `docs/*.md` remain gated.
