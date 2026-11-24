# Epic E-04: Polish & Release v0.4.0

- **Status:** DRAFT
- **Goal:** Complete MVP polish (wire `next_sprint.py` into the evolve skill, fix plugin cache sourcing), then publish SoloRail v0.4.0 to the Claude Code plugin marketplace for public beta.
- **Out of Scope:** Multi-developer collaboration, external issue tracker integrations, CI/CD pipelines, remote telemetry.

## Acceptance Criteria
- [ ] `next_sprint.py` CLI is wired into `/solorail:evolve` skill prose (one-line edit to call the script).
- [ ] Skill instructions source scripts from `.solorail/scripts/` directory, not the plugin cache.
- [ ] `plugin.json`, `marketplace.json`, and README versions are all set to `0.4.0` and match.
- [ ] A test user can install SoloRail from the marketplace, run the full `/solorail:*` lifecycle on a greenfield repo, and verify gate enforcement, metrics sync, and Day-2 disruption handling work end-to-end.
- [ ] Marketplace listing includes a one-line description, link to GitHub repo, and MIT license attribution.

## Issue Breakdown
- `E04-ISS-01`: Wire `next_sprint.py` into `/solorail:evolve` skill (Est: 0.5h)
- `E04-ISS-02`: Update skill instructions to source scripts from `.solorail/scripts/` (Est: 1.0h)
- `E04-ISS-03`: Bump version to 0.4.0 across all manifests and test marketplace install (Est: 1.0h)
- `E04-ISS-04`: Write marketplace listing and configure auto-publish (Est: 1.5h)

**Total: 4.0h** (Sprint 03 capacity 20.0h)

## Scope & Requirement Change Log
| Date | Change Description | Reason | Sprint Impact |
| :--- | :--- | :--- | :--- |
| 2026-11-25 | Initial Epic created | MVP polish gate + first public release | Added to Sprint 03 |
