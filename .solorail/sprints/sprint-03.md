# Sprint 3

- **Start Date:** 2026-11-25
- **End Date:** 2026-12-08
- **Capacity:** 20.0h
- **Status:** ACTIVE

## Planned Issues
| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E04-ISS-01 | E-04 | Wire `next_sprint.py` into `/solorail:evolve` skill | DONE | 0.5h | 0.25h | 2026-11-25 02:30 | One-line edit to evolve skill + test; all tests pass |
| E04-ISS-02 | E-04 | Update skill instructions to source scripts from `.solorail/scripts/` | CUT | 1.0h | - | - | Cut via Pivot (contradicted PRD §4: "plugin logic stays in Claude Code's plugin cache, not the target repo"; this repo's self-hosting dev friction is a one-time `/plugin update solorail`, not a sprint issue) |
| E04-ISS-03 | E-04 | Bump version to 0.4.0 and test marketplace install | TODO | 1.0h | - | - | Update plugin.json, marketplace.json, README |
| E04-ISS-04 | E-04 | Write marketplace listing and configure auto-publish | TODO | 1.5h | - | - | MVP polish complete; ready for beta |
| BUG-01 | HOTFIX | `parse_markdown_table` silently drops the first data row when a sprint board's separator row is missing/misplaced | DONE | 1.0h | 0.25h | 2026-11-25 03:00 | Checks row shape before skipping as separator; 3 regression tests added, 22/22 pass |

<!-- solorail:metrics:start -->
## Metrics
| Metric | Planned | Actual |
| :--- | :--- | :--- |
| **Total Hours** | 4.0h | 0.5h |
| **Cut Hours** | 1.0h | 0.0h |
| **Issues Completed** | 4 | 2 |
| **Issues Cut** | — | 1 |
<!-- solorail:metrics:end -->

<!-- solorail:velocity-summary:start -->
## Time & Velocity Summary
- **Total Estimated (Active):** 4.0h
- **Total Cut:** 1.0h
- **Total Actual:** 0.5h
- **Completed / Total Active Issues:** 2 / 4
- **Scope Changes (Cut Issues):** 1
<!-- solorail:velocity-summary:end -->

