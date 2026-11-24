---
name: pivot
description: Absorb mid-sprint scope, requirement, or feature changes safely across PRD.md, Epics, Sprints, and CONTEXT.md.
argument-hint: "<description of scope or requirement change>"
---

# SoloRail Pivot (Scope & Requirement Change) Skill

When the user invokes `/solorail:pivot`:

1. **Safety Check:** Run `git status --short`. If there are uncommitted code changes, advise the user to commit or stash them first so the pivot can be cleanly reverted if needed.
2. **Scoped Context Read:** Read `.solorail/PRD.md`, `.solorail/CONTEXT.md`, `.solorail/ROADMAP.md`, active `.solorail/epics/*.md`, and active `.solorail/sprints/sprint-XX.md`.
3. **Impact Analysis & Confirmation:** Present a clear summary of:
   - Updates needed in `.solorail/PRD.md` (MVP scope boundaries, user flows, or non-goals).
   - Existing `TODO` / `IN_PROGRESS` / `BLOCKED` Issues to mark `CUT` or modify.
   - New uniquely numbered Issues (`E01-ISS-XX`) to add with hour estimates.
   - Any superseded ADRs or glossary updates in `.solorail/CONTEXT.md`.
   Stop and ask the user to confirm before modifying files.
4. **Atomic State Update:**
   - Update `.solorail/PRD.md` (`Last Updated` + affected sections) if product scope changed.
   - In `.solorail/sprints/sprint-XX.md`: Never delete dropped rows—mark obsolete Issues `CUT` with `Notes: Cut via Pivot (<reason>)`, update modified Issues, and append new Issues as `TODO`.
   - In `.solorail/epics/epic-XX-*.md`: Update Acceptance Criteria and append a dated row to **Scope & Requirement Change Log**.
   - Warn if `Total Estimated (Active)` exceeds sprint `Capacity`.
