# Background Agents for PromptOrchestrator

This guide covers adding background agents for parallel task execution.

## Option 1: OCX Installation (Recommended)

```bash
# Install OCX first
curl -fsSL https://ocx.sh | sh

# Add background agents plugin
ocx add kdco/background-agents --from https://registry.kdco.dev
```

## Option 2: Manual Installation

```bash
# Create plugin directory
mkdir -p ~/.opencode/plugin

# Copy the plugin file
# (from https://github.com/kdcokenny/opencode-background-agents)
```

## Usage in PromptOrchestrator

Once installed, you have these tools available:

### delegate(prompt, agent)
Launch a background task:
```
delegate("Run nuclei vulnerability scan on target.com", "general")
```

### delegation_read(id)
Retrieve results when ready:
```
delegation_read("abc-123")
```

### delegation_list()
List all delegations with summaries:
```
delegation_list()
```

## Example Workflow

```
You: "Run three things in background:
1. nmap -sV target.com
2. gobuster on http://target.com  
3. nuclei on target.com"

Bot: Starting 3 background tasks...

You: "While those run, tell me about OWASP API Security Top 10"

[Background tasks complete with notifications]

Bot: <task-notification>
- nmap: Found ports 22, 80, 443, 8080
- gobuster: Found /admin, /api, /login
- nuclei: 2 critical findings

You: "Give me details on the critical nuclei findings"
```

## ⚠️ Read-Only Limitation

The background-agents plugin has a **read-only** restriction by design:

- Background delegations run in **isolated sessions** outside OpenCode's session tree
- The **undo/branching system** cannot track changes made in background sessions
- This prevents **data loss** from unrevertable changes

### Why This Exists:
- Background tasks run in separate processes
- No access to main session's state
- Changes made could persist even if main session is reverted

## Workaround: Use Native `task` Tool

For **write-capable background tasks**, use OpenCode's native `task` tool instead:

```
task("Run full nmap scan and save results to /tmp/scan.txt", general)
```

The `task` tool:
- Supports write permissions
- Has full access to session
- **But**: Does NOT persist results if context compacts

## Recommendations

| Task Type | Use |
|-----------|-----|
| **Read-only scans** (nmap, nuclei, gobuster) | `delegate()` |
| **Scans that save results** | `task()` |
| **Long-running research** | `delegate()` |
| **File modifications** | Direct in main session |

## Benefits for PromptOrchestrator

1. **Parallel scanning** - Run multiple tools simultaneously
2. **Context efficient** - Heavy scanning doesn't fill context
3. **Persistence** - Results saved to disk, survive restarts
4. **Non-blocking** - Continue conversation while tools run