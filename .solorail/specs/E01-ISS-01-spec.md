# Spec Receipt: E01-ISS-01

- **Title:** Add Mermaid lifecycle + command flowchart to README.md
- **Epic:** E-01
- **Status:** IN_PROGRESS

## Acceptance Criteria
- [ ] README.md contains a ```` ```mermaid ```` fenced code block using `flowchart` (or `graph`) syntax.
- [ ] Diagram shows all 6 lifecycle stages: Discover → Plan → Architect → Build → Verify → Evolve.
- [ ] Diagram shows all 12 `/solorail:*` commands, each attached to its stage.
- [ ] Diagram shows `hotfix`, `pivot`, and `block` as side branches off the main pipeline (not inline with the happy path).
- [ ] Diagram syntax is valid Mermaid (renders correctly on GitHub — verified by manual visual check, no renderer available locally).
- [ ] Placed in README.md between `## Features` and `## Installation` as a new `## Lifecycle` section.

## Allowlisted Files
- `README.md`

## No-Go Constraints
- Do not modify `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, or any skill/hook files.
- Do not alter existing README sections (Features, Installation, Quick Start, All Commands) beyond inserting the new section.
- Do not add any non-stdlib tooling or Mermaid-rendering dependency.

## Test Plan
Documentation-only change, no executable logic. Verification:
1. `grep -n '```mermaid' README.md` confirms the fenced block exists.
2. Manual read-through confirms all 6 stages and 12 commands appear as nodes.
3. Manual check confirms `hotfix`, `pivot`, `block` are drawn as branches off the main flow, not inline.
4. `markdownlint README.md` (if available) or manual inspection confirms no broken fencing/markdown around the new section.
5. Full README re-read confirms no existing section content was altered or removed.
