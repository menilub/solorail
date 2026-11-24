---
name: status
description: Show a read-only dashboard of the current SoloRail lifecycle stage, active Epic/Issue, blockers, hours, Git worktree state, and next command.
allowed-tools: [Read, Glob, Grep, Bash]
---

# SoloRail Status Dashboard Skill

1. **Read-Only Scoped Inspection (Do NOT modify files):**
   - Read `.solorail/PRD.md`, `.solorail/ROADMAP.md`, the latest `.solorail/sprints/sprint-*.md`, and active `.solorail/epics/epic-*.md` files.
   - Run `git branch --show-current`, `git status --short`, and `git worktree list`.

2. **Infer Current SoloRail Stage:**
   - **Stage 0 (Discover):** `PRD.md` is still placeholder/DRAFT with no concrete Epics.
   - **Stage 1 (Plan):** Epics are `DRAFT` or active sprint has no sliced issues yet.
   - **Stage 2 (Architect):** Issues are `TODO` and no `IN_PROGRESS` issue or spec exists yet.
   - **Stage 3 (Build):** An issue is `IN_PROGRESS` (or `BLOCKED`) with `.solorail/specs/<ID>-spec.md` present.
   - **Stage 4 (Verify):** An issue is `IN_PROGRESS` with implementation and tests ready for verification.
   - **Stage 5 (Evolve):** All active sprint issues are `DONE` or `CUT`.

3. **Render Dashboard:**
   Output a scannable Markdown dashboard showing:
   - **Project Status:** Product Name & Current Stage Name
   - **PRD Status, Git Branch, Working Tree State, and Worktree Count**
   - **Active Sprint Progress:** Visual bar (`[████░░░░░░] X%`), `Done / Active` issues, `Cut` count, `Actual` vs `Est` hours, and `Capacity`
   - **Active, Blocked & Up Next (`TODO`) Issues**
   - **Roadmap Epics Table**
   - **Recommended Next Action:** Exact `/solorail:<command>` to run next.
