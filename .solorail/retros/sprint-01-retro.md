# Sprint 01 Retrospective & Evolution

- **Date:** 2026-11-24
- **Planned vs. Actual Hours:** 9.0h estimated / 4.5h actual
- **Completed Issues:** 7 | **Cut/Deferred:** 0

## What Worked
- **100% throughput:** All 7 issues completed on-time (7/7 DONE).
- **Surgical, focused scope:** E-01 (onboarding visual guide) and E-02 (gate enforcement + branch/PR rules) were small, well-defined tracer bullets.
- **Worktree detection fixed early:** E02-ISS-01 caught the main-checkout false-positive before any gate enforcement shipped, preventing silent regressions.
- **Fast verification loops:** Computed `Actual` hours automatically from wall-clock (ADR-003) eliminated manual time-reporting friction.

## Friction & Estimation Drift
- **Estimation ran 2x faster than planned (0.50 ratio):** Small surgical fixes (one helper script + tests + prose edits) completed in ~half their estimates.
  - E01 overhead (README + GUIDE.md + linking) bundled together more efficiently than estimated.
  - E02 enforcement was a single `enforce_gate.py` addition + `SKILL.md` update, not the more complex multi-stage rollout initially scoped.
- **Spec ambiguity caught mid-sprint:** E02-ISS-03 (computed vs. file-mtime Actual hours) had two valid implementations; user confirmed literal wall-clock spec before build, avoiding rework.
- **E01-ISS-04 has no spec or verified receipt on file.** It was added by pivot (version restart) without going through `/solorail:architect-issue`. This is why `sprint-01-telemetry.md` reports **6/7 architected issues passed verified diff receipts** — that figure reflects the missing receipt, not a failed verification. Pivot-added issues currently bypass the spec stage.
- **Worktree detection bug root cause (E02-ISS-01):** `git worktree list` reports the primary checkout alongside linked ones, so a naive membership test flagged the main checkout as "inside a worktree". The fix compares `git rev-parse --git-dir` against `--git-common-dir`, which differ only in a genuinely linked worktree.

## Context & Skill Updates Applied
- **Added 3 Learned Guardrails** to `CONTEXT.md` Section 5:
  1. Test worktree detection in both main and linked checkouts.
  2. Ask on spec ambiguity before building, not after.
  3. Bias downward future estimates for small surgical fixes; consider splitting "code enforcement" from "prose updates."
- **ADR updates:** ADR-001 (version restart), ADR-002 (gate code enforcement), ADR-003 (computed actual hours) logged.
- **No archival needed:** Guardrails at 3/15 capacity; ADRs at 3 entries; no token-bloat risk.

## Next Sprint (Sprint 02)
- **Roadmap:** E-03 is **ACTIVE**, planned on 2026-11-24 as "Day-2 Disruption Handling & Deterministic Status Sync" — widened from the PRD's original title to absorb the status-sync plumbing found in the post-sprint review. 8 issues, 12.0h.
- **Capacity:** 20.0h (default 2-week sprint).
- **Carryover:** No `TODO` or `BLOCKED` issues from sprint-01 (all DONE).

> This section was written while E-03 was still DRAFT and said it awaited `/solorail:plan-epic`. Corrected after planning so it no longer contradicts `ROADMAP.md`, which `/solorail:status` reads alongside it.
