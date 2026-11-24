---
name: discover-prd
description: Turn a raw product idea into a structured .solorail/PRD.md, seed CONTEXT.md, and populate initial Epics in ROADMAP.md.
argument-hint: "[product idea or --quick]"
---

# SoloRail Discover PRD Skill (Stage 0)

When the user invokes `/solorail:discover-prd`:

1. **Scoped Context Read:** Read `.solorail/PRD.md`, `.solorail/CONTEXT.md`, and `.solorail/ROADMAP.md`.
2. **Product Discovery Interview (Skip if `--quick` is passed):**
   - Ask **4 to 6 high-leverage product questions** covering:
     1. Core user pain and primary user persona.
     2. The 2–3 critical end-to-end user flows required for MVP.
     3. Explicit **Non-Goals** (what we intentionally cut from v1).
     4. Hard technical, budget, or timeline constraints.
   - Stop and wait for the user's answers before writing files.
3. **Generate `.solorail/PRD.md`:** Synthesize answers into `.solorail/PRD.md` (Problem, User Flows, MVP Scope Boundaries, Constraints, and High-Level Epic Map). Set Status to `APPROVED` (or `DRAFT` if `--quick`).
4. **Seed Single Source of Truth:**
   - Populate Section 1 (`Product & Domain Overview`) and Section 3 (`Domain Glossary`) in `.solorail/CONTEXT.md`.
   - Populate `.solorail/ROADMAP.md` with initial Epics (`E-01`, `E-02`, ...) in `DRAFT` status.
5. **Handoff:** Summarize the PRD and Epic Map, and prompt the user to run `/solorail:plan-epic E-01`.
