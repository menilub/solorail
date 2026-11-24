---
name: evolve
description: Close out a sprint, generate telemetry metrics, distill guardrails, prune old ADRs, and initialize the next sprint.
argument-hint: "[optional sprint number]"
---

# SoloRail Evolve (Retrospective & System Improvement) Skill

**STEP 0: GATE CHECK**
Check `.solorail/sprints/sprint-XX.md`. If ANY issue is `IN_PROGRESS`, ABORT and tell the user to close (`/solorail:verify-issue`), pause (`/solorail:block`), or drop (`/solorail:pivot`) all active issues before evolving.

1. **Calculate Telemetry:**
   - Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_metrics.py`.
   - Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/eval_metrics.py` to generate `.solorail/retros/sprint-XX-telemetry.md`.
   - Read the telemetry report to inform the retrospective.
2. **Distill & Prune Guardrails:**
   - Add 1–3 concrete lessons to `## 5. Learned Guardrails` in `.solorail/CONTEXT.md`.
   - If `CONTEXT.md` has more than 15 guardrails or superseded ADRs, archive the oldest entries into `.solorail/archive/adr-history.md` to prevent context token bloat.
3. **Write Retro & Roll Over:**
   - Create `.solorail/retros/sprint-XX-retro.md` from `.solorail/retros/_TEMPLATE.md` incorporating the telemetry results.
   - Ask the user if they want to initialize `.solorail/sprints/sprint-(XX+1).md` carrying over unfinished `TODO` or `BLOCKED` issues.
