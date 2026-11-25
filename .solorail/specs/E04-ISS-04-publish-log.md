# E04-ISS-04 Publish Log

**Date:** 2026-11-25
**Result:** ✅ PASS (5/5 checks)

## Actions Taken
1. Added a "License" section to `README.md` — links `LICENSE` (MIT) and the GitHub repo URL.
2. Confirmed `marketplace.json`'s plugin entry already has `name`, `description`, `version`, `author`, `license` — no changes needed.
3. Opened PR #5 (`menilub/solorail-status-v4` → `main`), squash-merged at `6c21e00fb855c5452456da4984b5959742e10da3`.
4. Tagged `v0.4.0-beta` at that commit and pushed to `origin`.

## Verification
| Check | Result |
| :--- | :--- |
| README has License section | ✅ `## License` heading present |
| README has repo link | ✅ `github.com/menilub/solorail` present |
| marketplace.json valid JSON, all fields present | ✅ name/description/version/author/license all set |
| Tag `v0.4.0-beta` exists, points at merge commit | ✅ `3c8288a` → `6c21e00` |
| Tag pushed to origin | ✅ confirmed via `git ls-remote --tags origin` |

## Publish Mechanism
Manual, one-time: `git tag -a v0.4.0-beta <sha> -m "..."` + `git push origin v0.4.0-beta`. No GitHub Action, webhook, or scheduled job — consistent with PRD §3's non-goal of automated release/deployment pipelines.

## Conclusion
SoloRail v0.4.0-beta is now tagged on `main` at the GitHub-hosted repo `menilub/solorail`, installable via the existing marketplace entry (`source: "./"` resolves against the default branch, which now includes this release).
