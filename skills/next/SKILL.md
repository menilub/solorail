---
name: next
description: Auto-route to the deterministic next step in the SoloRail lifecycle without requiring the user to type issue IDs.
---

# SoloRail Next (Auto-Router) Skill

When the user runs `/solorail:next`:

1. **Inspect Workspace State:**
   - Read `.solorail/PRD.md`, `.solorail/ROADMAP.md`, the active `.solorail/sprints/sprint-*.md`, and `.solorail/specs/`.
2. **Determine Deterministic Transition:**
   - **If `.solorail/` does not exist:** Run `/solorail:init`.
   - **If `PRD.md` is `DRAFT` or contains `[Product Name]`:** Run `/solorail:discover-prd`.
   - **If active sprint has zero `TODO`/`IN_PROGRESS`/`BLOCKED` issues and `DRAFT` Epics exist:** Run `/solorail:plan-epic E-01`.
   - **If an Issue `<ID>` is `IN_PROGRESS`:**
     - If `.solorail/specs/<ID>-spec.md` does not exist: Run `/solorail:architect-issue <ID>`.
     - If `.solorail/specs/<ID>-spec.md` exists and source edits/tests exist: Run `/solorail:verify-issue <ID>` (if tests pass) or `/solorail:build-issue <ID>` (if not yet implemented).
   - **If no Issue is `IN_PROGRESS` and `TODO` issues exist:** Pick the top `TODO` issue `<ID>` and run `/solorail:architect-issue <ID>`.
   - **If all active sprint issues are `DONE` or `CUT`:** Run `/solorail:evolve`.
3. **Execute Immediately:** Invoke the determined SoloRail skill directly.
