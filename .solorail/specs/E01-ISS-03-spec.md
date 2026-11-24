# Spec Receipt: E01-ISS-03

- **Title:** Link GUIDE.md from CLAUDE.md and init completion output
- **Epic:** E-01
- **Status:** IN_PROGRESS

## Acceptance Criteria
- [ ] `CLAUDE.md`'s "Quick Start" section links to `.solorail/GUIDE.md`.
- [ ] `skills/init/SKILL.md` step 6 ("Finish") mentions `.solorail/GUIDE.md` in its completion summary for both Greenfield and Brownfield paths.
- [ ] No behavior change to init's detection logic, scaffolding, or any other skill.

## Allowlisted Files
- `CLAUDE.md`
- `skills/init/SKILL.md`

## No-Go Constraints
- Do not modify `README.md`, `.solorail/GUIDE.md`, or any other skill file.
- Do not change init's greenfield/brownfield detection or scaffolding steps (1–5) — only step 6's completion message.
- Do not add non-stdlib tooling.

## Test Plan
Documentation-only change, no executable logic. Verification:
1. `grep -n 'GUIDE.md' CLAUDE.md` confirms a link exists.
2. `grep -n 'GUIDE.md' skills/init/SKILL.md` confirms step 6 references it.
3. Manual diff review confirms only step 6 text changed in `skills/init/SKILL.md` — steps 1–5 untouched.
4. `git status --short` shows only `CLAUDE.md` and `skills/init/SKILL.md` changed from this issue's work.
