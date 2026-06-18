# BUILD

Build phase — produce artifacts, scripts, or actions from analysis
output. The phase where analysis becomes concrete output.

## Phase: 4

## Tools (examples)
- Code generation
- Script runners
- Payload assemblers
- Custom action builders

## Workflow

1. Verify the analysis finding is actionable
2. Produce the artifact / run the action
3. Test on the subject if safe
4. Document evidence

## Artifact template

```
### Artifact Name
**Inputs**: <input list>
**Outputs**: <output list>
**Evidence**: <command or code>
```

## Output
Handoff to Integrate:
- Artifacts produced
- Actions taken
- Evidence captured
