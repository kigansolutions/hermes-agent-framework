# TOOL BUILDER

Dynamic tool creation — create custom tools on-the-fly during a
workflow.

## Syntax

```
/tool create <name>
  description: <desc>
  parameters:
    - <param>: <type>
  command: <cmd with $params>
```

## Tool library

- /tool save <name> — save for future workflows
- /tool list — list saved tools
- /tool delete <name> — delete a saved tool
- /tool run <name> --<param> <value> — invoke a saved tool
