# Technical Spec: E03-ISS-09

- **Issue:** Parse a real allowlist section instead of substring-matching the whole spec
- **Epic:** E-03 (Day-2 Disruption Handling & Deterministic Status Sync)
- **Est:** 1.5h
- **Date:** 2026-11-25
- **Origin:** Found while verifying `E03-ISS-07`

## Problem

`enforce_gate.py`'s scope check is a plain substring search over the entire spec file:

```python
if rel_path not in spec_content and basename not in spec_content:
    block(...)
```

So **any filename mentioned anywhere in a spec — including in prose — becomes writable.**

Found concretely: the `E03-ISS-07` spec argues *against* a blanket markdown exemption with the sentence "would unlock `README.md`". That sentence allowlisted `README.md`, and the end-to-end verification returned exit 0 where 2 was required.

Two things make this worse than a typical false positive:

1. **The no-go list inverts.** Every spec in this epic lists files that must *not* be touched. Naming a file as forbidden currently grants write access to it. `E03-ISS-09`'s own no-go list names `sync_metrics.py`, `solorail_state.py` and `next_sprint.py` — all of which the old matcher would therefore permit.
2. **Basename matching widens it further.** `basename in spec_content` means a spec mentioning `sync_metrics.py` authorises *any* path ending in that name, anywhere in the tree.

This defeats the gate that enforces every other issue in the epic, so it is worth interrupting the remaining backlog.

## Design: parse the allowlist section only

Extract paths from the spec's allowlist **section**, and from **bullet lines** within it — not from prose.

Existing specs use three heading shapes, all of which must keep working:

| Shape | Example |
| :--- | :--- |
| `## Allowlisted Files` | `E01-ISS-01` … `E01-ISS-04` |
| `## 3. Allowlisted Files to Create/Modify` | `E02-ISS-02`, `E02-ISS-03` |
| `### 2.2 Allowlisted Files to Create/Modify` | `E02-ISS-01` (level 3) |
| `## Allowlisted Files to Create/Modify` | all `E03-*` |

The section ends at the next heading of the **same or shallower** level, so a `### Allowlist amendment` subsection stays *inside* a `##` allowlist section. That matters: `E03-ISS-02` and `E03-ISS-04` both record mid-build allowlist amendments as `###` subsections, and their added files must stay authorised.

From each bullet (`-` or `*`), take the **first** backticked token and accept it when it looks like a path. Taking only the first excludes the descriptive backticks that follow — `- \`hooks/hooks.json\` *(modify)* — add the \`SessionStart\` sync` yields `hooks/hooks.json`, not `SessionStart`.

**Matching becomes exact on the normalized relative path.** Basename matching is dropped; it is half the hole.

### Fail-closed when no section exists

A spec with no recognisable allowlist section **blocks**, with a message naming the heading to add. Falling back to the old substring behaviour would preserve the hole, which is the whole point of the issue. This is safe because `.solorail/**` stays exempt via `E03-ISS-07`, so the author can always edit the spec to fix it.

## Allowlisted Files to Create/Modify

- `scripts/spec_allowlist.py` *(create)* — the parser
- `scripts/test_spec_allowlist.py` *(create)*
- `scripts/enforce_gate.py` *(modify)* — use the parser instead of substring matching
- `scripts/test_enforce_gate.py` *(modify)* — regression for the prose-mention bypass

No other file may be touched.

## Interface / Schema Contract

```python
# scripts/spec_allowlist.py

ALLOWLIST_HEADING_RE  # matches '## Allowlisted Files', '## 3. Allowlisted Files to
                      # Create/Modify', '### 2.2 Allowlisted Files ...'

def find_allowlist_section(lines: list[str]) -> list[str] | None:
    """Lines of the allowlist section, or None when the spec has none.

    The section ends at the next heading of the same or shallower level, so a
    '### Allowlist amendment' subsection inside a '##' section is retained.
    """

def parse_allowlist(spec_text: str) -> list[str] | None:
    """Allowlisted paths, or None when the spec declares no allowlist section.

    An empty list means 'section present but lists nothing' -- which blocks
    everything -- and is deliberately distinct from None.
    """

def is_allowlisted(rel_path: str, spec_text: str) -> tuple[bool, str]:
    """(allowed, reason). Exact match on the normalized relative path only;
    basename matching is deliberately not supported."""
```

`enforce_gate.main()` replaces its substring check with `is_allowlisted`, and blocks with the returned reason.

## Test Cases

`scripts/test_spec_allowlist.py`:

1. **The prose-mention bypass is closed.** A spec whose allowlist lists only `scripts/a.py` but whose prose says "would unlock `README.md`" → `README.md` rejected, `scripts/a.py` accepted. *(The exact `E03-ISS-07` failure.)*
2. **No-go list entries are rejected.** A spec listing `scripts/a.py` and naming `scripts/forbidden.py` in a `## No-Go Constraints` section → `scripts/forbidden.py` rejected.
3. **All four heading shapes parse**, including the level-3 `### 2.2 Allowlisted Files to Create/Modify`.
4. **A `###` amendment subsection stays inside a `##` section** — a file listed there is accepted. *(Guards `E03-ISS-02`/`E03-ISS-04`.)*
5. **The section ends at the next same-level heading** — a path bulleted under a later `## Interface` section is rejected.
6. **Only the first backticked token per bullet is taken** — `- \`a/b.py\` *(modify)* — uses \`c/d.py\`` accepts `a/b.py`, rejects `c/d.py`.
7. **Basename matching is gone** — a spec listing `scripts/sync_metrics.py` rejects `vendor/sync_metrics.py`.
8. **No allowlist section → `parse_allowlist` returns None** and `is_allowlisted` is False with an actionable reason.
9. **Every live spec in `.solorail/specs/` parses** to a non-None allowlist containing at least one path. *(Catches a heading shape this parser would silently reject.)*
10. **Each `E03-*` spec authorises its own declared files** — asserted against the real spec files.

Added to `scripts/test_enforce_gate.py`:

11. **End-to-end:** with a spec that mentions a filename only in prose, that path is blocked.

## No-Go Constraints

Must **not** be touched:

- `scripts/sync_metrics.py`, `scripts/solorail_state.py`, `scripts/next_sprint.py`, `scripts/sync_on_git.py`.
- `hooks/hooks.json`.
- `is_record_keeping_path` and `read_target_path` from `E03-ISS-07`, `is_protected_branch` (ADR-002), `get_active_issue` (`E03-ISS-02`).
- Any existing spec file. The parser adapts to the specs as written; rewriting history to suit the parser would be backwards.

*(Note: with this issue's own change in place, none of the files named above become writable merely by appearing here — which is the fix demonstrating itself.)*

## Risk Notes

- **This narrows the gate**, so the failure mode is blocking legitimate work rather than permitting illegitimate work. Test 9 runs the parser over every real spec to catch a shape it would reject; tests 4 and 10 protect the amendment subsections this epic relies on.
- Fail-closed on a missing section could strand an author mid-issue. Mitigated because `.solorail/**` is exempt, so the spec itself is always editable, and the block message names the exact heading to add.
- `enforce_gate.py` is the gate: all existing early-exit paths, the record-keeping exemption, and the ADR-002 branch block stay intact.

## Definition of Done

- [ ] All tests pass; full suite green via `python3 -m unittest discover -s scripts`.
- [ ] A path mentioned only in spec prose is **blocked** end-to-end (the `README.md` case).
- [ ] A path in the active spec's allowlist is still permitted.
- [ ] Every spec under `.solorail/specs/` parses to a non-empty allowlist.
- [ ] Basename-only matches are rejected.
- [ ] A spec with no allowlist section blocks with a message naming the heading to add.
