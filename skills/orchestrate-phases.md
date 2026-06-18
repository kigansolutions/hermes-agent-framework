# ORCHESTRATE PHASES

Phase orchestration — combine multiple phases into multi-stage
workflows.

## Phase: meta (used by the planner agent)

## Concept

Workflows combine phases:

```
discover -> scan -> analyze -> build -> integrate -> document
```

## Workflow

1. Map dependency graph between phases
2. Execute phases in topological order
3. Document outputs at each step

## Patterns

| Pattern   | Path              | Use case              |
|-----------|-------------------|-----------------------|
| Linear    | A → B → C         | Simple pipelines      |
| Diamond   | A → [B,C] → D     | Independent phases    |
| Branching | A → B OR C        | Conditional flows     |
| Loop      | A → B → A         | Iterative refinement  |

## Output
- Workflow executed
- Phase results
- Combined impact assessment
