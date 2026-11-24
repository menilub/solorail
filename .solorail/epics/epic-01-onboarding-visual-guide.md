# Epic E-01: Repository Onboarding & Capacity-Checked Planning — Visual Guide

- **Status:** ACTIVE
- **Goal:** A new or returning solo developer can see, in one glance, how the SoloRail lifecycle (Discover → Plan → Architect → Build → Verify → Evolve) and its 12 `/solorail:*` commands fit together — in both the public README (GitHub-rendered) and a deeper in-repo guide.
- **Out of Scope:** Interactive/HTML diagrams, video walkthroughs, re-architecting the existing init/discover-prd/plan-epic skills (already shipped in v2.7.3).

## Acceptance Criteria
- [ ] README.md contains a Mermaid flowchart showing all 6 lifecycle stages and all 12 `/solorail:*` commands, including hotfix/pivot/block side branches, and renders correctly on GitHub.
- [ ] `.solorail/GUIDE.md` exists with the same diagram plus a command-by-command walkthrough (what each command reads, writes, and hands off to).
- [ ] The guide is discoverable: linked from `CLAUDE.md` and referenced in `/solorail:init`'s completion message.

## Issue Breakdown
- `E01-ISS-01`: Add Mermaid lifecycle + command flowchart to README.md (Est: 1.5h)
- `E01-ISS-02`: Create `.solorail/GUIDE.md` with full command-by-command walkthrough + embedded diagram (Est: 2.5h)
- `E01-ISS-03`: Link GUIDE.md from CLAUDE.md and init completion output (Est: 1.0h)
- `E01-ISS-04`: Rebase plugin version to 0.4.0-beta across plugin.json, marketplace.json, README.md (Est: 0.5h)

## Scope & Requirement Change Log
| Date | Change Description | Reason | Sprint Impact |
| :--- | :--- | :--- | :--- |
| 2026-11-24 | Epic created: visual workflow guide (README + GUIDE.md) | init/discover-prd/plan-epic already shipped in v2.7.3; user wants onboarding clarity instead | Added to Sprint 01 |
| 2026-11-24 | Pivot: added E01-ISS-04 to restart versioning at 0.4.0-beta | No installs exist yet; 2.7.3 overstated maturity for a pre-release beta | +0.5h to Sprint 01 (5.0h → 5.5h) |
