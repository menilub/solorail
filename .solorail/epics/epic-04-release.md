# Epic E-04: Polish & Release v0.4.0

- **Status:** DRAFT
- **Goal:** Complete MVP polish (wire `next_sprint.py` into the evolve skill), then publish SoloRail v0.4.0 to the Claude Code plugin marketplace for public beta.
- **Out of Scope:** Multi-developer collaboration, external issue tracker integrations, CI/CD pipelines, remote telemetry. Plugin-cache-vs-repo dev sync friction (resolved operationally via `/plugin update solorail`, not via product code — see Scope Change Log).

## Acceptance Criteria
- [x] `next_sprint.py` CLI is wired into `/solorail:evolve` skill prose (one-line edit to call the script). *(E04-ISS-01)*
- [x] `plugin.json`, `marketplace.json`, and README versions all agree on `0.4.0-beta` (confirmed via user decision 2026-11-25: stays beta, matches the epic's "public beta" goal). *(E04-ISS-03)*
- [x] A test user can install SoloRail from the marketplace, run the full `/solorail:*` lifecycle on a greenfield repo, and verify gate enforcement, metrics sync, and Day-2 disruption handling work end-to-end. *(E04-ISS-03 — verified against this repo's HEAD on a scratch scaffold; see `.solorail/specs/E04-ISS-03-install-check.md`)*
- [ ] Marketplace listing includes a one-line description, link to GitHub repo, and MIT license attribution.

## Issue Breakdown
- `E04-ISS-01`: Wire `next_sprint.py` into `/solorail:evolve` skill (Est: 0.5h) — DONE
- `E04-ISS-02`: ~~Update skill instructions to source scripts from `.solorail/scripts/`~~ (Est: 1.0h) — CUT via Pivot
- `E04-ISS-03`: Bump version to 0.4.0 across all manifests and test marketplace install (Est: 1.0h)
- `E04-ISS-04`: Write marketplace listing and configure auto-publish (Est: 1.5h)

**Total (active): 3.0h** (Sprint 03 capacity 20.0h)

## Scope & Requirement Change Log
| Date | Change Description | Reason | Sprint Impact |
| :--- | :--- | :--- | :--- |
| 2026-11-25 | Initial Epic created | MVP polish gate + first public release | Added to Sprint 03 |
| 2026-11-25 | `E04-ISS-02` cut via Pivot | Its plan (move scripts into target repo's `.solorail/`) contradicted PRD §4: "plugin logic stays in Claude Code's plugin cache, not the target repo." This repo's self-hosting dev friction (stale cache after each merge) is a one-time `/plugin update solorail`, not a sprint issue. | −1.0h from Sprint 03 |
