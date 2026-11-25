# E04-ISS-03 Spec: Confirm version alignment and test marketplace install

**Decision (2026-11-25):** Version stays `0.4.0-beta` — matches current manifests and the epic's "public beta" goal. No version bump needed; this issue verifies alignment and tests the install path end-to-end.

## Allowlisted Files
- `.solorail/specs/E04-ISS-03-install-check.md` (new — install verification log)
- `README.md` (only if a version-string mismatch is found)
- `.claude-plugin/plugin.json` (only if a version-string mismatch is found)
- `.claude-plugin/marketplace.json` (only if a version-string mismatch is found)

## Interface / Schema Contract
No code interface. This issue is a verification pass:
1. Diff `plugin.json`, `marketplace.json`, and all `README.md` version references for `0.4.0-beta` consistency.
2. Confirm `installed_plugins.json`'s cached `gitCommitSha` for solorail is not required to match HEAD for this check (that's the separately-cut E04-ISS-02 concern) — only the *manifest version string* must match.
3. Run `/plugin update solorail` (or equivalent) once, then exercise the full lifecycle on a scratch greenfield repo: `/solorail:init` → `/solorail:discover-prd` → `/solorail:plan-epic` → `/solorail:architect-issue` → `/solorail:build-issue` → `/solorail:verify-issue` → `/solorail:hotfix` → `/solorail:pivot` → `/solorail:evolve`.
4. Record the install-check result in `.solorail/specs/E04-ISS-03-install-check.md`.

## Test Cases
1. **Manifest match:** `plugin.json.version == marketplace.json.plugins[0].version == "0.4.0-beta"`.
2. **README consistency:** every version string in README.md (if any beyond the existing path reference) says `0.4.0-beta`, not a stale `2.7.3` or bare `0.4.0`.
3. **Gate enforcement works on a fresh install:** `enforce_gate.py` blocks an edit outside an IN_PROGRESS issue's allowlist.
4. **Metrics sync works on a fresh install:** `sync_metrics.py` runs without error as a PostToolUse hook.
5. **Day-2 commands load:** `/solorail:hotfix`, `/solorail:pivot`, `/solorail:evolve` are all present and invocable from the installed plugin cache.

## No-Go Constraints
- Do NOT touch `scripts/*.py` (no code behavior changes in this issue — verification only).
- Do NOT touch `.claude/hooks/hooks.json`.
- Do NOT create a real external test repo; use a local scratch directory under `/tmp` or similar, never a tracked path in this repo.

## Definition of Done
- [ ] Manifest versions confirmed to match (`0.4.0-beta` everywhere).
- [ ] Full lifecycle smoke-tested on a scratch greenfield repo via the installed plugin cache.
- [ ] Install-check results recorded in `.solorail/specs/E04-ISS-03-install-check.md`.
