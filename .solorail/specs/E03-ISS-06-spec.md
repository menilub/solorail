# Technical Spec: E03-ISS-06

- **Issue:** Refresh metrics on SessionStart and git-touching Bash commands
- **Epic:** E-03 (Day-2 Disruption Handling & Deterministic Status Sync)
- **Est:** 1.0h
- **Date:** 2026-11-25
- **Depends on:** E03-ISS-01 (idempotent, non-destructive sync), E03-ISS-02 (`resolve_active_sprint`), E03-ISS-03 (status derivation)

## Problem

`hooks/hooks.json` fires `sync_metrics.py` on `PostToolUse` for `Edit|Write` **only**. It does not fire on:

- **`SessionStart`** — a fresh session shows whatever the last `Edit`/`Write` left behind. `session_start.py` prints the banner from unsynced state.
- **any Bash command** — a `git merge`, `git pull`, PR merge, or branch checkout changes which issues exist and what is `DONE`, and nothing re-reads it.

This is exactly how this project's own status went stale: **PRs #2 and #3 merged outside this workspace** and no surface noticed. Status is only ever as fresh as the last file edit made through Claude's own Edit/Write tools.

`sync_metrics.py` is now safe to run often — `E03-ISS-01` made it idempotent and non-destructive, and `E03-ISS-03`'s closure rule is interlocked on a retro — so increasing its frequency is no longer risky.

## Design decision: why a wrapper script, not a matcher pattern

Claude Code hook matchers match the **tool name**, not the tool's arguments. There is no way to express "Bash, but only when the command touches git" in `hooks.json`. Running a full sync on *every* Bash call would mean a sync per `ls`, `grep`, and `python3` invocation.

So `PostToolUse` gains a `Bash` matcher pointing at a new `scripts/sync_on_git.py`, which reads the hook payload from stdin, inspects the command string, and delegates to `sync_metrics.sync()` only when the command plausibly changed git state.

## Allowlisted Files to Create/Modify

- `hooks/hooks.json` *(modify)* — add the `SessionStart` sync and the `Bash` `PostToolUse` matcher
- `scripts/sync_on_git.py` *(create)* — command-gated sync wrapper
- `scripts/test_sync_on_git.py` *(create)*

No other file may be touched.

## Interface / Schema Contract

```python
# scripts/sync_on_git.py

GIT_STATE_COMMANDS = {
    "merge", "pull", "checkout", "switch", "commit", "rebase",
    "cherry-pick", "reset", "revert", "am", "apply", "stash", "clone",
}

def touches_git_state(command: str) -> bool:
    """True when the command plausibly changed git working-tree or history
    state, so sprint boards may now be stale.

    Matches `git <subcommand>` for the set above, and `gh pr merge`/`gh pr
    checkout`. Deliberately ignores read-only git (`status`, `log`, `diff`,
    `show`, `branch` with no argument) so an ordinary inspection does not
    trigger a file-writing sync.
    """

def main(argv=None) -> int:
    """Read the PostToolUse payload from stdin, run sync() when the command
    touches git state, and always exit 0.

    A PostToolUse hook must never fail the tool call that triggered it: this
    is an opportunistic refresh, not a gate. Any exception is swallowed with a
    short stderr note.
    """
```

`hooks/hooks.json` after the change:

- `PreToolUse` / `Edit|Write` → `enforce_gate.py` *(unchanged)*
- `PostToolUse` / `Edit|Write` → `sync_metrics.py` *(unchanged)*
- `PostToolUse` / `Bash` → `sync_on_git.py` *(new)*
- `SessionStart` → `sync_metrics.py`, then `session_start.py` *(sync added, order matters — the banner must read synced state)*

## Test Cases

`scripts/test_sync_on_git.py`, stdlib-only:

1. **State-changing commands match.** `git merge main`, `git pull`, `git checkout -b x`, `git commit -m "y"`, `git rebase main`, `gh pr merge 4` → all `True`.
2. **Read-only git does not match.** `git status`, `git log --oneline`, `git diff`, `git show HEAD`, `git branch --show-current` → all `False`. *(A sync writes files; an inspection must not trigger one.)*
3. **Non-git commands do not match.** `ls`, `python3 scripts/x.py`, `grep -r foo .`, `echo git merge` → `False`. The last is the important one: the word appearing as an argument is not a git invocation.
4. **Compound commands match when any segment touches git.** `cd /x && git merge main`, `git status; git pull` → `True`.
5. **`main` exits 0 and runs sync for a git command**, verified against a temp fixture whose stale `## Metrics` block is corrected.
6. **`main` exits 0 and does NOT write for a non-git command** — fixture left byte-identical.
7. **`main` exits 0 on malformed stdin** (empty, non-JSON, missing keys) and on a sync that raises. A `PostToolUse` hook must never fail the tool call.
8. **`hooks.json` stays valid JSON** and declares all four hook entries, with `sync_metrics.py` ordered before `session_start.py` under `SessionStart`.

## No-Go Constraints

Must **not** be touched:

- `scripts/sync_metrics.py` — this issue changes *when* it runs, never what it does.
- `scripts/session_start.py`, `scripts/enforce_gate.py` — their logic is settled by `E03-ISS-02`.
- The `PreToolUse` gate entry in `hooks.json`, and the existing `Edit|Write` `PostToolUse` entry.
- `scripts/next_sprint.py` — `E03-ISS-04`; sprint generation is never automatic.

## Risk Notes

- **A `PostToolUse` hook that fails breaks the tool call that triggered it.** `main` must catch everything and exit 0 always. This is the single biggest risk in the issue.
- A sync writes files. Triggering it on read-only git inspection would mean `git status` mutates the working tree, which would be surprising and would dirty diffs mid-review. Hence the explicit read-only exclusion list, tested.
- `sync_on_git.py` runs on **every** Bash call, so `touches_git_state` must be cheap and must not import anything heavy before deciding. `sync_metrics` is imported lazily, only once the command matches.

## Definition of Done

- [ ] All 8 tests pass; full suite green via `python3 -m unittest discover -s scripts`.
- [ ] `hooks.json` parses as JSON and declares the `Bash` `PostToolUse` matcher plus `SessionStart` sync ordered before the banner.
- [ ] A git command through the wrapper corrects a stale fixture; a non-git command leaves it byte-identical.
- [ ] The wrapper exits 0 on malformed stdin and on a raising sync.
- [ ] `git status` does **not** trigger a write.
- [ ] Live repo: running the wrapper with a `git status` payload leaves `sprint-02.md` byte-identical.
