# E04-ISS-01 Spec: Wire `next_sprint.py` into `/solorail:evolve` skill

**Issue:** The `next_sprint.py` CLI generator exists but is not called by the evolve skill. Evolve still asks an agent to hand-author the next sprint, leaving marker-drift risk in practice.

**Solution:** One-line edit to the evolve skill to invoke the generator instead of asking for hand-authoring.

## Allowlisted Files
- `./.claude/plugins/cache/solorail/solorail/0.4.0-beta/skills/evolve/SKILL.md` (modify step 3)
- `./scripts/test_evolve_wiring.py` (new test file)

## Changes
1. Locate section "3. **Write Retro & Roll Over:**" in evolve/SKILL.md
2. Replace the line "Ask the user if they want to initialize..." with a call to `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/next_sprint.py"`
3. Add error handling: if the script refuses (another sprint is active), skip this step with a note.

## Test Cases
1. **Happy path:** Sprint 02 → Sprint 03 transition works (already tested in E03-ISS-04).
2. **Guard:** If another sprint is ACTIVE, next_sprint.py exits non-zero; evolve skill does not break.
3. **Idempotence:** Running evolve twice on the same sprint still produces only one next-sprint file.

## No-Go Constraints
- Do NOT modify any `.solorail/scripts/*.py` files.
- Do NOT touch `.claude/hooks/` or any gate enforcement code.
- Do NOT change the return type or behavior of the skill (it must remain deterministic).

## Definition of Done
- [ ] Evolve skill step 3 calls next_sprint.py instead of asking for hand-authoring.
- [ ] Skill prose error handling is clear (skip if script refuses).
- [ ] A fresh evolve run on a closed sprint generates the next sprint without user intervention.
