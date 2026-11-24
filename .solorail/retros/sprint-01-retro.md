# Sprint 01 Retrospective & Evolution

- **Date:** 2026-11-24
- **Planned vs. Actual Hours:** 9.0h estimated / 4.5h actual
- **Completed Issues:** 7 | **Cut/Deferred:** 0

## What Worked
- 100% sprint throughput (7/7 issues DONE), 0% unplanned maintenance drag.
- The hard-gate pipeline (`enforce_gate.py` + spec allowlists) held across all 7 issues — no out-of-scope edits slipped through, even while modifying the gate itself in E02-ISS-02.
- Three mid-sprint pivots (E02-ISS-01/02/03) were absorbed cleanly with full audit trails in `epic-02.md`'s Scope & Requirement Change Log, without destabilizing the original E-01 plan.
- Epic E-02 closed with all 4 of its acceptance criteria met and verified live (not just unit-tested) before each issue's closure.

## Friction & Estimation Drift
- **Estimation Accuracy Ratio: 0.50** — every E-02 issue landed at roughly half its estimate (1.0h→0.5h, 1.5h→1.0h, 1.0h→0.5h). These were small, surgical fixes (one helper script + tests + a short `SKILL.md` prose edit); estimates didn't account for how thin that slice actually was.
- **A real correctness bug was caught mid-build, not at verification:** E02-ISS-01's first implementation of "is this a worktree?" used `git worktree list`, which also lists the main checkout — so it would have disabled the worktree-creation offer everywhere, not just in linked worktrees. Caught by the session's own next-work check before it shipped; fixed by switching to a `git rev-parse --git-dir` vs. `--git-common-dir` comparison.
- **E02-ISS-03's issue text was ambiguous** ("system clock / file mtimes") and conflicted with an existing in-repo precedent (E01-ISS-02/03's file-mtime-delta convention). Surfaced to the user before building rather than guessed; user confirmed raw wall-clock.
- `E01-ISS-04` has no spec/verified receipt on file (pre-dates this session's strict spec-first habit) — the telemetry's "6/7 architected issues passed verified diff receipts" reflects that gap, not a new issue.

## Context & Skill Updates Applied
- `.solorail/CONTEXT.md`: added ADR-002 (code-level main/master block) and ADR-003 (raw wall-clock hours, confirmed over mtime-delta); added a "Linked Worktree" glossary term; added 3 Learned Guardrails (worktree-detection test coverage, surface spec ambiguity before building, estimation bias for small surgical fixes).
- `scripts/enforce_gate.py`: hard-blocks app-code edits on `main`/`master` (exit 2).
- `scripts/check_worktree.py`, `scripts/compute_actual_hours.py`: new stdlib helpers, each with a dedicated `unittest` suite (22 tests total across the sprint's new scripts, all passing).
- `skills/architect-issue/SKILL.md`, `skills/build-issue/SKILL.md`, `skills/verify-issue/SKILL.md`: updated prose to match the new code-level behavior (worktree check, hard branch stop, PR-on-close, automatic hours).
