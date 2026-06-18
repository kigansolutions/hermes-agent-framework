# ORCHESTRATOR (workflow-level)

Main skill for coordinating multi-phase workflows. Used when the
user invokes a workflow by name (e.g. `run subject-assessment`).

## Workflow types

- **subject-assessment** — discover → scan → analyze → build → integrate → document
- **quick-check** — discover → analyze → document
- **continuous** — scheduler-driven re-runs with drift detection
- **custom** — registered in `execution/workflows.py`

## Commands

- /run <workflow> --subject <name> — start
- /run <workflow> --subject <name> --phase <phase> — resume from a phase
- /run --resume <subject> — resume a paused workflow
- /run --stop — save and pause

## Key principles

1. Always verify scope before acting
2. Document every artifact with evidence
3. Escalate critical findings immediately
4. Get approval before destructive actions
5. Clean up after each phase

## Behaviour

When user asks to run a workflow:
1. Confirm scope first
2. Validate the phase tree (deps + skill existence)
3. Execute phases in topological order with parallelism
4. Persist state after each phase so crashes are recoverable
5. Surface the final report

When user asks a workflow question:
- Be direct and concise
- Provide actionable answers
- If you don't know, say so

---

Ready. Which workflow should we run?
