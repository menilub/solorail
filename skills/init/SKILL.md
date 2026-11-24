---
name: init
description: Scaffold SoloRail into the current repository with greenfield/brownfield auto-detection.
allowed-tools: [Read, Glob, Grep, Bash, Write, Edit]
---

# SoloRail Init Skill

1. **Auto-Detect Greenfield vs. Brownfield:**
   - Run `git rev-list --count HEAD 2>/dev/null || echo 0` and check for existing manifest files (`package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`).
   - If commits > 1 or manifests exist, classify as **Brownfield**. Otherwise, **Greenfield**.

2. **Scaffold `.solorail/` State Directories:**
   - Create `.solorail/archive`, `.solorail/epics`, `.solorail/retros`, `.solorail/specs`, `.solorail/sprints`.
   - Create `.solorail/archive/adr-history.md` and `.solorail/specs/README.md`.

3. **Copy Templates:**
   - Read `${CLAUDE_PLUGIN_ROOT}/templates/*` and write them into `.solorail/` (`RULES.md`, `CONTEXT.md`, `PRD.md`, `ROADMAP.md`, `epics/_TEMPLATE.md`, `retros/_TEMPLATE.md`).
   - Generate `.solorail/sprints/sprint-01.md` with today's start date and a 14-day end date (`Capacity: 20.0h`).

4. **Idempotent `CLAUDE.md` Setup:**
   - Check if `CLAUDE.md` exists in the repo root. If not, create it.
   - Read `CLAUDE.md`. If it does NOT contain `@.solorail/RULES.md`, prepend `@.solorail/RULES.md` as line 1.

5. **Brownfield Seeding (If detected):**
   - Read discovered manifests to identify language, framework, test runner, and linter.
   - Pre-fill `.solorail/CONTEXT.md` Section 2 (`Tech Stack & Conventions`) and set `Current Stage: Production` instead of generic placeholders.

6. **Finish:**
   - Summarize detected mode (`Greenfield` or `Brownfield`) and created files.
   - For Greenfield: Prompt user to run `/solorail:discover-prd`.
   - For Brownfield: Prompt user to run `/solorail:status` and complete `.solorail/CONTEXT.md` Section 3 (`Domain Glossary`).
