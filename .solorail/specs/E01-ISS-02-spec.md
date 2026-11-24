# Spec Receipt: E01-ISS-02

- **Title:** Create `.solorail/GUIDE.md` with command-by-command walkthrough + embedded diagram
- **Epic:** E-01
- **Status:** IN_PROGRESS

## Acceptance Criteria
- [ ] `.solorail/GUIDE.md` exists.
- [ ] Contains the same Mermaid lifecycle flowchart as `README.md` (copied verbatim, kept in sync).
- [ ] Contains one subsection per `/solorail:*` command (all 12), each stating: what it **reads**, what it **writes**, and what it **hands off to** (the next command / stage).
- [ ] Commands are grouped under their stage headings (Discover, Plan, Architect, Build, Verify, Evolve) plus a "Meta & Day-2" group for `init`, `status`, `next`, `hotfix`, `block`, `pivot`.
- [ ] Does not touch `CLAUDE.md` or `skills/init/SKILL.md` (that's `E01-ISS-03`'s job).

## Allowlisted Files
- `.solorail/GUIDE.md`

## No-Go Constraints
- Do not modify `CLAUDE.md`, `README.md`, or any file under `skills/`.
- Do not re-architect or change behavior of any existing skill — this issue is documentation-only.
- Do not add non-stdlib tooling or a Mermaid-rendering dependency.

## Test Plan
Documentation-only change, no executable logic. Verification:
1. `test -f .solorail/GUIDE.md` confirms the file exists.
2. `grep -c '```mermaid' .solorail/GUIDE.md` returns 1 (exactly one diagram block).
3. `grep -oE '/solorail:[a-z-]+' .solorail/GUIDE.md | sort -u | wc -l` returns 12 (all commands covered).
4. Manual read-through confirms each command's subsection states reads/writes/hands-off-to.
5. `git status --short` shows only `.solorail/GUIDE.md` as new/changed from this issue's work.
