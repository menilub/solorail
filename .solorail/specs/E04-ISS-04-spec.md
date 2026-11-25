# E04-ISS-04 Spec: Marketplace listing + one-time manual publish

**Decision (2026-11-25):** "Auto-publish" means a one-time manual publish step (push a git tag, confirm the marketplace listing is complete), not a CI/CD pipeline — PRD §3 excludes automated release/deployment pipelines.

## Allowlisted Files
- `README.md` (add a License + repo link section, if missing)
- `.claude-plugin/marketplace.json` (add explicit repo URL field, if the schema supports one)
- `.solorail/specs/E04-ISS-04-publish-log.md` (new — publish record)

## Interface / Schema Contract
No code interface. Deliverables:
1. `README.md` gets a short "License" section: link to `LICENSE` (MIT), author attribution, and the GitHub repo URL (`https://github.com/menilub/solorail`).
2. `marketplace.json`'s plugin entry already has `description`, `author`, `license` — confirm these are present (they are) and leave as-is unless the schema has a dedicated `homepage`/`repository` field worth adding.
3. Publish step: tag the current commit `v0.4.0-beta` and push the tag to `origin` — the mechanism by which `menilub/solorail`'s marketplace entry becomes installable at this version for any user. No GitHub Action, no webhook, no scheduled job.
4. Record the publish action (tag name, commit SHA, push confirmation) in `.solorail/specs/E04-ISS-04-publish-log.md`.

## Test Cases
1. **README has license section:** grep for "License" heading and a `LICENSE`/MIT reference.
2. **README has repo link:** grep for `github.com/menilub/solorail`.
3. **marketplace.json valid JSON:** parses without error after any edit.
4. **Tag exists and matches HEAD:** `git tag` lists `v0.4.0-beta` pointing at the issue's closing commit.
5. **Tag pushed to origin:** `git ls-remote --tags origin` includes `v0.4.0-beta`.

## No-Go Constraints
- Do NOT add a GitHub Actions workflow, webhook, or any scheduled/triggered automation (PRD §3 non-goal: no CI/CD pipelines).
- Do NOT touch `scripts/*.py` or `hooks/hooks.json`.
- Do NOT modify `LICENSE` (already correct).

## Definition of Done
- [ ] README has a License section with repo link and MIT attribution.
- [ ] `marketplace.json` confirmed complete (description, author, license present).
- [ ] `v0.4.0-beta` git tag created and pushed to `origin`.
- [ ] Publish log recorded in `.solorail/specs/E04-ISS-04-publish-log.md`.
