# Spec Receipt: E01-ISS-04

- **Title:** Rebase plugin version to 0.4.0-beta
- **Epic:** E-01
- **Status:** IN_PROGRESS

## Acceptance Criteria
- [ ] `.claude-plugin/plugin.json` `version` field reads `0.4.0-beta`.
- [ ] `.claude-plugin/marketplace.json` `plugins[0].version` field reads `0.4.0-beta`.
- [ ] `README.md` local test-install reference reflects the new version string.

## Allowlisted Files
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `README.md`

## Test Plan
Metadata-only change, no executable logic. Verification is manual inspection: `grep -r "0.4.0-beta" .claude-plugin/ README.md` confirms all three files updated and no stray `2.7.3` references remain in those files.
