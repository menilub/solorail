# Sprint 03 Retrospective & Evolution

- **Date:** 2026-11-25
- **Planned vs. Actual Hours:** 4.0h estimated (active) / 1.0h actual
- **Completed Issues:** 4 | **Cut/Deferred:** 1

## What Worked
- **Pre-architecture scope checks caught two PRD conflicts before any code was written.** E04-ISS-02 ("source scripts from target repo") and the original E04-ISS-04 wording ("configure auto-publish") both silently contradicted explicit PRD non-goals (plugin-cache architecture; no CI/CD pipelines). Catching both during architecture, not after building, avoided two wasted build-and-revert cycles.
- **A real bug surfaced from doing the work, not from planning it.** BUG-01 (the markdown-table-parser separator bug) was found while syncing metrics after the E04-ISS-02 pivot — an unplanned defect, fixed same-session via `/solorail:hotfix` with 3 regression tests, 0.25h actual.
- **The evolve → next_sprint.py wiring (E04-ISS-01) now works end-to-end.** This sprint generated cleanly without hand-authoring, closing the loop E03-ISS-04 opened.

## Friction & Estimation Drift
- **Estimation Accuracy Ratio: 0.25** — all 4 issues ran ~75% under estimate. Root cause: 3 of 4 were rescoped from "build" to "verify/cut" during architecture, which is inherently faster than the original build estimate assumed.
- **One of Sprint 02's own guardrails turned out to be wrong** and had to be corrected this sprint (see Context Updates below) — a reminder that a retro's lessons are themselves provisional, not settled fact.
- **A stray markdown edit silently broke metric counting for an entire sprint** (BUG-01) before anyone noticed the numbers were off. The fix hardens the parser, but the deeper lesson is to spot-check Est/Done counts against manual arithmetic after any direct Edit to a sprint board's issue table, not just trust the printed sync line.

## Context & Skill Updates Applied
- Corrected 1 guardrail from Sprint 02 (plugin-cache sourcing) that would have violated PRD §4 if acted on literally.
- Added 2 new Learned Guardrails to `CONTEXT.md` Section 5:
  1. **Markdown table parsers must check row shape, not assume fixed position**, before treating a row as structural. (From BUG-01.)
  2. **Sprint 03 Accuracy Ratio: 0.25** — bias "verify/rescope" issues toward 0.25–0.5h estimates regardless of the epic's original guess. (From E04-ISS-01, ISS-03, ISS-04.)
- Epic E-03 and E-04 both marked `DONE` in `ROADMAP.md`; `v0.4.0-beta` tagged and pushed to `origin` (PR #5, merged to `main` at `6c21e00`).
