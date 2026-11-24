---
name: architect-issue
description: Design the minimal technical implementation for an Issue, record ADRs, write the spec receipt, and prepare a Git worktree.
argument-hint: "<ISSUE-ID, e.g. E01-ISS-01>"
allowed-tools: [Read, Glob, Grep, Bash, Write, Edit]
---

# SoloRail Architect Issue Skill (Stage 2)

*Constraint: You may NOT modify application source code during architecture.*

**STEP 0: GATE CHECK**
Check `.solorail/sprints/sprint-*.md`. If another issue is already `IN_PROGRESS`, ABORT and tell the user to run `/solorail:verify-issue` or `/solorail:block` on that issue first.

1. **Scoped Context Read:** Read `.solorail/CONTEXT.md`, parent `.solorail/epics/epic-XX-*.md`, and the active `.solorail/sprints/sprint-XX.md`.
2. **Minimal Technical Spec:** Define:
   - **Allowlisted Files to Create/Modify:** Exact relative paths (used by `enforce_gate.py`).
   - **Interface / Schema Contract:** Signatures, payloads, or DB migrations.
   - **Test Cases:** 3–5 concrete happy-path and edge-case tests.
   - **No-Go Constraints:** Files/modules that must NOT be touched.
3. **Generate State Receipt:** Write the spec to `.solorail/specs/<ISSUE-ID>-spec.md`. This file MUST exist for SoloRail's gatekeeper to permit code edits in Stage 3.
4. **Log Decisions & Prepare Workspace:**
   - Append a 4-line ADR to `.solorail/CONTEXT.md` if an irreversible technical decision was made.
   - Offer to create an isolated Git worktree (`git worktree add ../wt-<ISSUE-ID> -b feat/<ISSUE-ID>`).
   - Update `.solorail/sprints/sprint-XX.md`: set Status to `IN_PROGRESS` and record `Started At` (`YYYY-MM-DD HH:MM`).
