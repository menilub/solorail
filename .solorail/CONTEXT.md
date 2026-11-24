# Project Context (Single Source of Truth)

## 1. Product & Domain Overview
- **Goal:** A lightweight, Git-native, Docs-as-Code SDLC plugin for Claude Code that structures solo-developer delivery into a gated Discover → Plan → Architect → Build → Verify → Evolve pipeline, anchoring all state in version-controlled Markdown/JSON inside `.solorail/`.
- **Current Stage:** MVP

## 2. Tech Stack & Conventions
- **Backend:** [e.g., Python 3.12 / FastAPI / PostgreSQL]
- **Frontend:** [e.g., React / TypeScript / Tailwind]
- **Testing:** [e.g., pytest, Playwright]
- **Repo Conventions:** [e.g., REST naming, package structure, error handling rules]

## 3. Domain Glossary (Ubiquitous Language)
- **Epic:** A large unit of user value (`E-01`, `E-02`, ...) tracked in `.solorail/ROADMAP.md` and detailed in `.solorail/epics/epic-XX.md`.
- **Issue:** A vertical tracer-bullet slice of an Epic, sized 1.0–4.0h, with a globally unique ID (`E01-ISS-01`) and status `TODO | IN_PROGRESS | BLOCKED | DONE | CUT`.
- **Spec Receipt:** `.solorail/specs/<ISSUE-ID>-spec.md`, the allowlisted file list + test plan an Issue must have before any code edit is permitted.
- **Gate:** The `PreToolUse` hook (`enforce_gate.py`) that blocks (exit code 2) any edit outside the active Issue's spec receipt allowlist.
- **Tracer-bullet:** A thin, end-to-end vertical slice of functionality sized small enough to implement and verify within one Issue.
- **Hotfix:** An urgent, ≤1.0h bug fix handled via `/solorail:hotfix` in an isolated worktree with a regression test, rolled into `ROADMAP.md` under `HOTFIX`.
- **Pivot:** A mid-sprint scope or requirement change absorbed via `/solorail:pivot`, marking dropped items `CUT` while preserving audit history.
- **Learned Guardrail:** A rule distilled from a sprint retrospective into `CONTEXT.md` Section 5 via `/solorail:evolve`, capped at 15 rules.
- **ADR (Architecture Decision Record):** A lightweight 4-line log entry in `CONTEXT.md` Section 4 for each irreversible technical choice.

## 4. Architecture Decision Records (ADRs)
> Append lightweight 4-line ADRs here whenever an irreversible technical choice is made.

- **ADR-001 (2026-11-24):** Restart plugin versioning at `0.4.0-beta` instead of continuing from `2.7.3` — *Context:* No installs or public releases exist yet; `2.7.3` overstated maturity for a pre-release beta. — *Consequence:* `plugin.json`, `marketplace.json`, and README references must be kept in sync going forward; prior git commit messages mentioning `v2.7.x` remain as historical artifacts, not live version claims.

## 5. Learned Guardrails (Updated via /solorail:evolve)
- [Rule added from past bugs or retro insights]
