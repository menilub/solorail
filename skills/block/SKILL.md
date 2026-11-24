---
name: block
description: Mark an active issue as BLOCKED, record the blocker reason, and triage the next actionable issue.
argument-hint: "<ISSUE-ID> <reason for blocking>"
---

# SoloRail Block Issue Skill

When the user invokes `/solorail:block <ISSUE-ID> <reason>`:

1. **Record the Blocker:**
   - Open the active `.solorail/sprints/sprint-XX.md`.
   - Locate `<ISSUE-ID>`, change Status to `BLOCKED`, and set `Notes / Scope Impact` to `[BLOCKED] <reason>`.
2. **Triage Next Work:**
   - Read the sprint board and recommend the top 1–2 remaining `TODO` issues to pick up next via `/solorail:architect-issue`.
