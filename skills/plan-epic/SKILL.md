---
name: plan-epic
description: Plan an Epic, clarify requirements via targeted questions, slice into vertical tracer-bullet Issues, and check sprint capacity.
argument-hint: "[Epic ID or feature description, e.g. E-01]"
---

# SoloRail Plan Epic Skill (Stage 1)

**STEP 0: GATE CHECK**
Check `.solorail/PRD.md`. If it still has `[Name]` placeholders or `Status: DRAFT` (unless `--quick` was explicitly requested), ABORT and prompt the user to complete `/solorail:discover-prd` first.

1. **Scoped Context Read:** Read `.solorail/PRD.md`, `.solorail/CONTEXT.md`, `.solorail/ROADMAP.md`, and the active sprint file in `.solorail/sprints/`.
2. **Clarify Before Designing (Skip if `--quick` is passed):**
   - Ask 3 to 5 sharp, high-leverage questions to resolve edge cases, data models, and explicit "Out of Scope" boundaries. Stop and wait for answers.
3. **Slice Into Vertical Tracer Bullets:**
   - Create `.solorail/epics/epic-XX-<slug>.md` from `.solorail/epics/_TEMPLATE.md`.
   - Break the Epic into vertical end-to-end Issues (`E01-ISS-01`, `E01-ISS-02`, ...), each sized between `1.0h` and `4.0h`.
4. **Capacity Check & Sprint Update:**
   - Update `.solorail/ROADMAP.md` (`Status: ACTIVE`).
   - Append Issues to the active `.solorail/sprints/sprint-XX.md` with status `TODO`.
   - Compare `Total Estimated (Active)` against the sprint's `Capacity` field. If it exceeds Capacity, STOP and ask the user which issues to defer to the next sprint.
5. **Output:** Present the Epic and Issue table, and prompt the user to run `/solorail:architect-issue E01-ISS-01`.
