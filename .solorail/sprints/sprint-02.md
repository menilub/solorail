# Sprint 02

- **Start Date:** 2026-11-25
- **End Date:** 2026-12-08
- **Capacity:** 20.0h
- **Status:** ACTIVE

## Planned Issues
| ID | Epic | Issue | Status | Est | Actual | Started At | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E03-ISS-01 | E-03 | Make `sync_metrics.py` write both metric blocks and splice non-destructively | TODO | 1.5h | - | - | Fixes EOF truncation (line 128) + unsynced `## Metrics` table |
| E03-ISS-02 | E-03 | Resolve the ACTIVE sprint by status, not `sprint_files[-1]`, across all scripts | TODO | 1.5h | - | - | Affects enforce_gate.py, session_start.py, sync_metrics.py |
| E03-ISS-03 | E-03 | Derive and write the sprint `Status:` transition automatically | TODO | 1.5h | - | - | Depends on ISS-02 |
| E03-ISS-04 | E-03 | Add `sprints/_TEMPLATE.md` and generate the next sprint with carryover | TODO | 1.5h | - | - | Depends on ISS-03 |
| E03-ISS-05 | E-03 | Record a PR per issue, open it via `gh pr create`, show live state in status | TODO | 2.0h | - | - | Depends on ISS-01 |
| E03-ISS-06 | E-03 | Refresh metrics on SessionStart and git-touching Bash commands | TODO | 1.0h | - | - | hooks.json matcher change |
| E03-ISS-07 | E-03 | Allow record-keeping writes between issues in `enforce_gate.py` | TODO | 1.0h | - | - | Keeps main/master block (ADR-002) intact |
| E03-ISS-08 | E-03 | Verify `hotfix` → `pivot` → `evolve` end-to-end against new status machinery | TODO | 2.0h | - | - | Original PRD E-03 scope; build last |

## Metrics
| Metric | Planned | Actual |
| :--- | :--- | :--- |
| **Total Hours** | 0.0h | 0.0h |
| **Issues Completed** | 0 | 0 |
| **Issues Cut** | 0 | 0 |

## Time & Velocity Summary
- **Total Estimated (Active):** 12.0h
- **Total Cut:** 0.0h
- **Total Actual:** 0.0h
- **Completed / Total Active Issues:** 0 / 8
- **Scope Changes (Cut Issues):** 0
