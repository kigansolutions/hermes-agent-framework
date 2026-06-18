# prompt-orchestrator Skills

Skills are reusable markdown prompt templates. Each skill wraps either
a tool invocation, a reasoning pattern, or both. The orchestrator
loads them at startup and indexes by name.

## Phases

The default workflow is six phases, plus three meta-phases. Phases
can run in parallel where dependencies allow.

| Phase  | Skill                 | Wraps                      |
|--------|-----------------------|----------------------------|
| 1      | `discover.md`         | passive + active discovery |
| 2      | `scan.md`             | surface mapping            |
| 3      | `analyze.md`          | reasoning about findings   |
| 4      | `build.md`            | produce artifacts / actions|
| 5      | `integrate.md`        | push to downstream systems |
| 6      | `document.md`         | final report               |

## Meta-phases

| Skill                       | Purpose                         |
|-----------------------------|---------------------------------|
| `orchestrator.md`           | run a named workflow end-to-end |
| `orchestrate-phases.md`     | combine phases into workflows   |
| `scheduler.md`              | recurring runs + drift detection|
| `tool-builder.md`           | dynamic tool creation           |
| `align-controls.md`         | map findings to controls        |

## Domain adapters (reference)

These are real skills targeting specific domains. They are
domain-specific on purpose — the orchestrator demonstrates the same
shape works for any domain.

| Skill                     | Domain                          |
|---------------------------|---------------------------------|
| `port-scan.md`            | network scanning (nmap, masscan)|
| `injection-probe.md`      | injection probing (sqlmap, etc.)|
| `proxy-adapter.md`        | web proxy (Caido)               |
| `browser.md`              | browser automation (CDP)        |
| `llm-eval.md`             | LLM-as-subject evaluation       |
| `contract-audit.md`       | smart-contract audit (EVM)      |

## Adding a new skill

1. Create `skills/<name>.md` with frontmatter and prompt template.
2. Add it to this README in the right category.
3. Reference it from a workflow in `execution/workflows.py` if you
   want it auto-loaded by a phase tree.

## Usage

```
/run subject-assessment --subject example.com
/skill discover --subject example.com
/skill scan --subject example.com
```

## Skill priority (default workflow)

1. `orchestrator` — entry point
2. `discover` → `scan` → `analyze` → `build` → `integrate` — main chain
3. `document` — final phase
4. `orchestrate-phases` — workflow composition
5. `scheduler` — recurring runs
6. `align-controls` — post-document mapping
7. `tool-builder` — dynamic capability
