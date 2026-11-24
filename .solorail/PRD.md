# Product Requirements Document (PRD)

- **Product Name:** SoloRail
- **Status:** APPROVED
- **Last Updated:** 2026-11-24

## 1. Problem & Target User
- **Problem Statement:** Solo developers using Claude Code lose project context between sessions, let AI agents over-engineer or edit unrelated files, skip tests under time pressure, lose track of real velocity from manual Markdown math, and have no way to safely absorb mid-sprint bugs or scope changes without a team. If unsolved, solo builders accumulate technical debt, untracked scope creep, and unreliable AI-driven delivery.
- **Primary User Persona:** Independent developers, founders, and maintainers using Claude Code to build new greenfield apps or extend existing brownfield repos without team ceremony.
- **Success Metrics (MVP):**
  1. A user can go from raw idea → scoped, capacity-checked sprint backlog using only `/solorail:*` commands.
  2. `enforce_gate.py` reliably blocks any edit to a file not allowlisted in an `IN_PROGRESS` issue's spec receipt.
  3. Sprint/roadmap hour totals and telemetry are always deterministically correct (no manual math, no drift).

## 2. Core User Flows (Happy Paths)
1. **Repository Onboarding & Capacity-Checked Planning:** `/solorail:init` detects greenfield/brownfield and scaffolds `.solorail/` → `/solorail:discover-prd` turns an idea into `PRD.md` + seeded `CONTEXT.md` + draft Epics in `ROADMAP.md` → `/solorail:plan-epic` slices an Epic into 1–4h tracer-bullet issues, halting if sprint capacity (20h/2 weeks) is exceeded.
2. **Gate-Enforced Feature Delivery:** `/solorail:architect-issue` writes an allowlisted spec receipt + ADRs + Git worktree → `/solorail:build-issue` enforces RED-GREEN-REFACTOR TDD, with `enforce_gate.py` blocking any out-of-allowlist file edit → `/solorail:verify-issue` blocks closure unless tests/linters pass, then `sync_metrics.py` recalculates sprint/roadmap hours → `/solorail:next` auto-routes to the next deterministic stage.
3. **Day-2 Disruption Handling & Sprint Evolution:** `/solorail:hotfix` isolates ≤1h bug fixes with a regression test in a separate worktree, rolling hours into `ROADMAP.md` under `HOTFIX` → `/solorail:pivot` absorbs scope changes, marking dropped items `CUT` with preserved audit trail → `/solorail:evolve` closes the sprint (blocking if any issue is still `IN_PROGRESS`), generates telemetry, distills `Learned Guardrails` (capped at 15), and rolls unfinished issues into the next sprint.

## 3. MVP Scope Boundaries
- **Must-Have (In Scope):**
  - 12 `/solorail:*` slash commands covering the full Discover → Plan → Architect → Build → Verify → Evolve lifecycle.
  - `PreToolUse` gate (`enforce_gate.py`) blocking unallowlisted file edits with exit code 2.
  - `PostToolUse` deterministic metric sync (`sync_metrics.py`, `eval_metrics.py`).
  - `SessionStart` hook surfacing active `IN_PROGRESS` work automatically.
  - Git worktree isolation for features and hotfixes.
  - Greenfield + brownfield auto-detection on `/solorail:init`.
- **Explicit Non-Goals (Out of Scope for v1):**
  - Multi-developer/team collaboration features.
  - External issue tracker integrations (Jira, Linear, GitHub Issues).
  - Hosted web UI, external database, or background daemon.
  - Multi-editor/cross-agent adapters (Cursor, Windsurf, Codex CLI).
  - Automated token/API cost scraping.
  - Automated release/deployment (CI/CD) pipelines.
  - Remote telemetry or backend services.

## 4. Technical & Business Constraints
- **Stack:** Claude Code plugin architecture (`.claude-plugin/`, `SKILL.md`, hooks); automation scripts are Python 3 stdlib only, zero pip dependencies; requires Git CLI + `git worktree`.
- **State:** All project state as Markdown/JSON inside `.solorail/`; single `@.solorail/RULES.md` import in `CLAUDE.md`; plugin logic stays in Claude Code's plugin cache, not the target repo.
- **Budget/Infra:** $0 hosting, zero external infrastructure, distributed via self-hosted GitHub plugin marketplace.
- **Token efficiency:** Each command loads only the `.solorail/` files required for its stage; `Learned Guardrails` capped at 15 rules.
- **Cadence:** 2-week sprints, 20.0h default capacity; issues sized 1.0–4.0h; hotfixes capped at ≤1.0h.
- **Security/Privacy:** No outbound network calls, no remote telemetry; all state stays local; MIT licensed.

## 5. Epic Map (Feeds ROADMAP.md)
- **E-01:** Repository Onboarding & Capacity-Checked Planning (init → discover-prd → plan-epic)
- **E-02:** Gate-Enforced Feature Delivery (architect-issue → build-issue → verify-issue → next)
- **E-03:** Day-2 Disruption Handling & Sprint Evolution (hotfix / pivot → evolve)
