# prompt-orchestrator — Technical Specification

## Goal

A domain-agnostic Python framework for orchestrating prompt-driven AI
agents. The same engine has been used to drive security assessments,
research workflows, smart-contract audits, and DevOps automation —
the engine itself has no opinions about the domain.

The orchestrator is **deliberately generic**. It does not know what
"assessment", "research", or "ops" means. It knows about **phases**,
**skills**, **tools**, **memory**, and **agents** — and lets the
domain-specific content live in markdown files.

## Core model

```
User request → Orchestrator agent → Phase tree → Skills → Tools → Memory
                                  ↘                ↗
                                   Parallelism, retries, state
```

### 1. Agents

An **agent** is a markdown file (`agents/*.md`) with YAML frontmatter:

```yaml
---
name: orchestrator
role: workflow coordinator
tools: [task, bash, glob, grep, read, write, edit]
model: any
---
You are the orchestrator. Your job is to break the user's request
into a phase tree, delegate each phase to a specialist agent, and
verify the output before moving on.
```

The agent file is the **only** place the system prompt lives. To
retune the agent, edit the markdown. No code changes.

### 2. Skills

A **skill** is a reusable markdown prompt template (`skills/*.md`)
that wraps either a tool invocation, a reasoning pattern, or both:

```yaml
---
name: scan
phase: 2
wraps: tools/scanner.py
inputs: [subject]
outputs: [raw_findings]
---
## Goal
Run a structured scan against the subject.

## Steps
1. Enumerate endpoints via the scanner tool.
2. Capture raw output to working memory.
3. Hand off findings to the analyzer skill.
```

Skills are loaded at startup and indexed by name. New skills can be
added by dropping a `.md` file in the directory.

### 3. Tools

A **tool** is a Python module that exposes a typed interface over an
external capability — a CLI binary, a REST API, a database, anything.

The orchestrator treats all tools uniformly:

```python
class Tool(Protocol):
    name: str
    description: str
    parameters: dict
    def run(self, **kwargs) -> Result: ...
```

The `tools/` and `integration/` directories ship adapters for common
external systems (scanners, proxies, search engines, chat front-ends).
Adding a new tool = write a Python module conforming to the protocol.

### 4. Memory (5 layers)

| Layer      | Backend           | Used for                                  |
|------------|-------------------|-------------------------------------------|
| working    | in-process dict   | current conversation / active workflow    |
| semantic   | Qdrant (vectors)  | similarity recall                         |
| episodic   | SQLite KV         | past actions + outcomes                   |
| knowledge  | markdown wiki     | compounding domain knowledge              |
| session    | SQLite FTS5       | full-text search across past sessions     |

The pattern follows Karpathy's LLM Wiki idea: the LLM rewrites raw
observations into structured wiki pages over time, so knowledge
**compounds** instead of being re-derived each session.

### 5. Workflows

A **workflow** is a sequence of phases. Each phase invokes one skill.
Phases can be sequential, parallel, or depend on other phases' outputs:

```python
workflow = Workflow(
    name="subject-assessment",
    phases=[
        Phase("discover", skill="discover", parallel=True),
        Phase("scan",     skill="scan",     depends_on=["discover"]),
        Phase("analyze",  skill="analyze",  depends_on=["scan"]),
        Phase("document", skill="document", depends_on=["analyze"]),
    ],
)
engine.run(workflow, subject="example.com")
```

The engine persists state between phases. A workflow killed mid-flight
can be resumed without loss.

## Execution model

The execution engine (`execution/engine.py`) is responsible for:

1. Loading agent + skill markdown at startup
2. Validating the workflow (dependency graph, missing skills)
3. Running phases in topological order with parallelism
4. Persisting state after each phase
5. Routing phase outputs to the next phase's input
6. Handling retries with backoff
7. Supporting manual intervention (pause / resume / stop)

## Integration surfaces

The engine exposes the same workflow capability through three front-ends:

- **CLI** — `python -m prompt_orchestrator run <workflow> --subject X`
- **REPL** — `python -m prompt_orchestrator --interactive`
- **Telegram bot** — `execution/telegram/bot.py`

All three call into the same engine. The front-end just shapes the
user input into a workflow invocation.

## Configuration

`config.yaml` controls runtime behaviour:

```yaml
paths:
  knowledge_db: ~/.prompt_orchestrator/knowledge.db
  workspace: ~/.prompt_orchestrator/workspace

agents:
  default: orchestrator
  planner: planner
  worker: worker

memory:
  working_ttl: 3600
  semantic_backend: qdrant
  episodic_backend: sqlite

execution:
  parallelism: 4
  retry_max: 3
  retry_backoff: exponential
```

## Extensibility points

1. **New agent** — drop `agents/<name>.md`
2. **New skill** — drop `skills/<name>.md`
3. **New tool** — write a module in `tools/` or `integration/`
4. **New workflow** — register in `execution/workflows.py`
5. **New memory layer** — implement the `MemoryLayer` protocol
6. **New front-end** — implement the `FrontEnd` protocol (CLI / REPL /
   Telegram are reference implementations)

## Design principles

1. **Markdown over code for prompts.** System prompts live in `.md`
   files. Retuning is a content edit.
2. **Uniform tool interface.** All external capabilities look the same
   to the agent loop.
3. **Composing memory.** Each layer solves one recall problem;
   combining them enables new recall patterns.
4. **Crash-safe workflows.** Phase state is persisted before yielding.
5. **Domain agnostic.** The engine has no opinions about the domain.
