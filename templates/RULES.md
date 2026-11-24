# SoloRail Operating Rules (v2.7.0)

You are collaborating with a solo developer using **SoloRail**, a Git-native, Docs-as-Code **Discover → Plan → Architect → Build → Verify → Evolve** lifecycle. All project state lives in `.solorail/`.

## Single Source of Truth & Scoped Context Loading
Load ONLY the artifacts required for your active command to minimize token overhead:
- **Status Snapshot (`/solorail:status`):** `.solorail/PRD.md` (header), `.solorail/ROADMAP.md`, active `.solorail/sprints/sprint-XX.md`, active `.solorail/epics/*.md`.
- **Discovery & Planning (`/solorail:discover-prd`, `/solorail:plan-epic`):** `.solorail/PRD.md`, `.solorail/CONTEXT.md`, `.solorail/ROADMAP.md`, active `.solorail/sprints/sprint-XX.md`.
- **Architecture & Build (`/solorail:architect-issue`, `/solorail:build-issue`):** `.solorail/CONTEXT.md`, parent `.solorail/epics/epic-XX.md`, active `.solorail/sprints/sprint-XX.md`.
- **Verification (`/solorail:verify-issue`):** Parent `.solorail/epics/epic-XX.md`, `.solorail/CONTEXT.md` (Guardrails), active `.solorail/sprints/sprint-XX.md`.
- **Scope Change (`/solorail:pivot`):** `.solorail/PRD.md`, `.solorail/CONTEXT.md`, `.solorail/ROADMAP.md`, affected `.solorail/epics/*.md`, active `.solorail/sprints/sprint-XX.md`.
- **Hotfix (`/solorail:hotfix`):** `.solorail/CONTEXT.md`, active `.solorail/sprints/sprint-XX.md`.

## ID & Status Standards
- **Epic IDs:** `E-01`, `E-02`, ...
- **Issue IDs:** Globally unique prefixed IDs (`E01-ISS-01`, `E02-ISS-01`, or `BUG-01` for `/solorail:hotfix`). Never reuse numbers.
- **Allowed Statuses:** `TODO` | `IN_PROGRESS` | `BLOCKED` | `DONE` | `CUT`

## Core Engineering Guardrails
- **Think Before Coding:** Surface ambiguities and edge cases before touching files. Never assume silently.
- **Simplicity First:** Write the minimum code needed to satisfy the current Issue's acceptance criteria. No speculative abstractions.
- **Surgical Changes:** Touch only files explicitly allowlisted in `.solorail/specs/<ISSUE-ID>-spec.md`.
- **Deterministic Math:** Sprint and roadmap totals are automatically synced by `sync_metrics.py`.

## STRICT WORKFLOW ENFORCEMENT
If the user asks to build, fix, or edit code in plain chat (without using a slash command), **YOU MUST NOT WRITE CODE**. Classify the request and ask the user to confirm running `/solorail:discover-prd`, `/solorail:plan-epic`, `/solorail:hotfix`, `/solorail:pivot`, or `/solorail:next`.

## Available SoloRail Commands
- `/solorail:init` — Scaffold `.solorail/` in a greenfield or brownfield repository.
- `/solorail:status` — Display a read-only dashboard of current lifecycle stage, progress, hours, and Git worktrees.
- `/solorail:next` — Auto-route to the deterministic next step in the lifecycle.
- `/solorail:discover-prd` — Turn a raw product idea into `.solorail/PRD.md`, seed `CONTEXT.md`, and populate `ROADMAP.md`.
- `/solorail:plan-epic` — Clarify Epic scope, slice into vertical tracer-bullet Issues (`1-4h`), and schedule into Sprint.
- `/solorail:architect-issue` — Design minimal technical spec (`.solorail/specs/<ID>-spec.md`), log ADRs, and create Git worktree.
- `/solorail:build-issue` — Execute strict RED-GREEN-REFACTOR TDD within allowlisted spec files.
- `/solorail:verify-issue` — Run tests, audit diff, log actual hours, and write verification receipt.
- `/solorail:hotfix` — Fast-track small bug fixes (`<= 1h`) with a regression test.
- `/solorail:block` — Mark an active issue `BLOCKED` and triage the next `TODO` issue.
- `/solorail:pivot` — Safely absorb mid-sprint scope changes across PRD, Epics, Sprints, and CONTEXT.
- `/solorail:evolve` — Close out a sprint, generate telemetry report, prune ADRs, and initialize the next sprint.
