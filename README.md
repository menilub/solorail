# SoloRail

**One track from idea to shipped, tested code.**

**SoloRail** is a lightweight, Git-native **Discover → Plan → Architect → Build → Verify → Evolve** lifecycle plugin for Claude Code—built specifically for solo developers who want the speed of AI coding without context drift, over-engineering, or skipped tests.

## Features

- **Strict 6-Stage Pipeline:** `/solorail:discover-prd` → `/solorail:plan-epic` → `/solorail:architect-issue` → `/solorail:build-issue` → `/solorail:verify-issue` → `/solorail:evolve`.
- **Hard-Blocking TDD & Scope Gatekeeper:** A `PreToolUse` hook (`enforce_gate.py`) prevents code edits unless an issue is `IN_PROGRESS`, has a technical spec receipt in `.solorail/specs/`, and the target file is allowlisted.
- **Deterministic Velocity & Telemetry:** `PostToolUse` hooks automatically sync sprint and roadmap hours (`sync_metrics.py`) and generate sprint health scorecards (`eval_metrics.py`).
- **Zero Repo Plumbing:** Skills, hooks, and scripts live in Claude Code's plugin cache; target projects only track clean Markdown state in `.solorail/`.
- **Automatic Greenfield & Brownfield Onboarding:** `/solorail:init` detects existing codebases, seeds tech stack conventions in `.solorail/CONTEXT.md`, and injects `@.solorail/RULES.md` into `CLAUDE.md` idempotently.

## Installation

Add this repository as a Claude Code plugin marketplace and install **SoloRail**:

```bash
/plugin marketplace add <your-github-username>/solorail
/plugin install solorail@solorail
```

Or test locally before publishing:

```bash
claude --plugin-dir ./solorail-plugin-v0.4.0-beta
```

## Quick Start

Inside any greenfield or brownfield repository:

1. Run `/solorail:init` to scaffold `.solorail/` and link `@.solorail/RULES.md` in `CLAUDE.md`.
2. Run `/solorail:discover-prd` (greenfield) or `/solorail:status` (brownfield).
3. Drive the workflow step-by-step using `/solorail:next`.

## All Commands

| Command | Stage / Purpose |
| :--- | :--- |
| `/solorail:init` | Initialize `.solorail/` with greenfield/brownfield auto-detection |
| `/solorail:status` | Read-only dashboard of lifecycle stage, progress, hours, and Git worktrees |
| `/solorail:next` | Auto-route to the deterministic next lifecycle step |
| `/solorail:discover-prd` | Interview & generate `.solorail/PRD.md`, `CONTEXT.md`, and `ROADMAP.md` |
| `/solorail:plan-epic` | Slice an Epic into `1–4h` vertical tracer-bullet issues & check capacity |
| `/solorail:architect-issue` | Write `.solorail/specs/<ID>-spec.md`, log ADRs, and create Git worktree |
| `/solorail:build-issue` | Implement allowlisted files using strict RED-GREEN-REFACTOR TDD |
| `/solorail:verify-issue` | Run tests, audit diff, log actual hours, and write verification receipt |
| `/solorail:hotfix` | Fast-track `<= 1h` bug fixes in an isolated worktree |
| `/solorail:block` | Mark an active issue `BLOCKED` and triage the next `TODO` issue |
| `/solorail:pivot` | Safely absorb mid-sprint scope changes without losing audit history |
| `/solorail:evolve` | Generate telemetry report, prune ADRs, and roll over next sprint |
