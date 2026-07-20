# hermes-agent-framework

> A modular Python framework for orchestrating prompt-driven AI agents
> with persistent multi-layer memory, a markdown-defined skill registry,
> and a pluggable tool layer. Designed to wrap any CLI/REST tool as a
> typed operation the agent can invoke.

Built around five primitives: **agents** (role + prompt), **skills**
(markdown prompt templates), **tools** (CLI/REST wrappers), **memory**
(5-layer persistence), and **workflows** (composable phases). Same
architecture underpins the Hermes agent platform I run day to day —
this is a generic, redacted reference implementation of that
architecture, open for inspection.

---

## What it does

`prompt-orchestrator` lets you build agents that:

1. **Load role + prompt from markdown** — agents are `.md` files with
   frontmatter, no code changes needed to retune the system prompt.
2. **Compose workflows from skills** — each skill is a reusable prompt
   template that wraps a tool or a reasoning pattern.
3. **Wrap arbitrary tools behind a uniform interface** — `nmap`,
   `sqlmap`, `curl`, REST APIs, custom Python — same adapter shape.
4. **Remember across sessions** — 5-layer memory: working, semantic
   (vector), episodic (key-value), knowledge (wiki), session (FTS).
5. **Run workflows in parallel with state save/resume** — the
   execution engine handles parallelism, retries, and crash recovery.
6. **Expose via CLI, REPL, or Telegram bot** — same engine, multiple
   surfaces.

The orchestrator is **domain-agnostic**. The same engine has been used
to drive security assessments, research workflows, smart-contract
audits, and DevOps automation. Skill sets differ; the engine stays the
same.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ENTRY POINTS                              │
│         CLI  ·  Interactive REPL  ·  Telegram bot               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EXECUTION ENGINE                             │
│   workflow runner  ·  parallel scheduler  ·  state save/resume   │
└───────┬─────────────────┬───────────────────┬───────────────────┘
        │                 │                   │
        ▼                 ▼                   ▼
┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐
│   AGENTS     │  │    SKILLS      │  │       TOOLS          │
│              │  │                │  │                      │
│ planner.md   │  │ discover.md    │  │ tools/scanner.py     │
│ orchestrator │  │ scan.md        │  │ tools/executor.py    │
│ .md          │  │ analyze.md     │  │ integration/         │
│ worker.md    │  │ build.md       │  │   · caido.py         │
│              │  │ document.md    │  │   · browser.py       │
│              │  │ scheduler.md   │  │   · web_search.py    │
│              │  │ ...            │  │   · telegram/        │
└──────┬───────┘  └────────┬───────┘  └──────────┬───────────┘
       │                   │                    │
       └───────────────────┼────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                          MEMORY (5 layers)                       │
│                                                                  │
│  working     —  in-flight conversation state                     │
│  semantic    —  vector store for similarity recall (Qdrant)       │
│  episodic    —  key-value store of past actions + outcomes        │
│  knowledge   —  structured wiki that compounds over time          │
│  session     —  full-text search across past sessions (FTS5)      │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                          KNOWLEDGE BASE                          │
│  domain reference modules  ·  checklists  ·  payload libraries   │
└─────────────────────────────────────────────────────────────────┘
```

---

## The 5 primitives

### 1. Agents (`agents/*.md`)

Each agent is a markdown file with YAML frontmatter that defines its
role, system prompt, and tool access. Adding a new agent = drop a
`.md` file. No code change.

```markdown
---
name: orchestrator
role: workflow coordinator
tools: [task, bash, glob, grep]
---
You are the orchestrator. Your job is to break the user's request
into phases, delegate each phase to a specialist agent, and verify
the output before moving on.
```

Three reference agents ship with the repo:

- `planner.md` — decomposes requests into phase trees
- `orchestrator.md` — coordinates phase execution
- `worker.md` — single-phase specialist

### 2. Skills (`skills/*.md`)

Skills are reusable prompt templates. They can wrap a tool (e.g. a
CLI invocation recipe), encode a reasoning pattern (e.g. structured
analysis), or both. The skill registry reads them at startup.

```markdown
---
name: scan
phase: 2
wraps: tools/scanner.py
---
Run a structured scan against the subject:
1. Enumerate endpoints via the scan tool
2. Capture raw output to working memory
3. Hand off findings to the analyzer skill
```

### 3. Tools (`tools/`, `integration/`)

Tools are Python modules that wrap an external capability behind a
typed interface. The orchestrator treats them uniformly — `bash`,
`curl`, `nmap`, `sqlmap`, custom REST APIs, etc. all look the same
to the agent loop.

Built-in adapters include:

- `tools/scanner.py` — generic CLI tool wrapper
- `tools/executor.py` — async subprocess manager
- `integration/caido.py` — Caido proxy SDK
- `integration/browser.py` — Chrome DevTools Protocol via CDP
- `integration/web_search.py` — DuckDuckGo / SearXNG
- `integration/telegram/` — Telegram bot front-end

### 4. Memory (`memory/`)

Five layers, each addressing a different recall problem:

| Layer      | Store             | Used for                                  |
|------------|-------------------|-------------------------------------------|
| working    | in-process dict   | current conversation / active workflow    |
| semantic   | Qdrant (vectors)  | "find similar to this" recall             |
| episodic   | SQLite KV         | "what happened last time we did X"        |
| knowledge  | markdown wiki     | compounding domain knowledge (LLM Wiki)   |
| session    | SQLite FTS5       | full-text search across past sessions     |

The pattern comes from Andrej Karpathy's "LLM Wiki" idea — knowledge
**compounds** because the LLM rewrites raw observations into
structured wiki pages over time, instead of re-deriving them each
session.

### 5. Workflows (`execution/engine.py`)

Workflows are sequences of phases (each phase = one skill). The
execution engine runs them with parallelism, retries, and crash
recovery. State is persisted between phases so a crashed workflow can
resume mid-flight.

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

---

## Quick start

```bash
git clone https://github.com/kigansolutions/hermes-agent-framework
cd hermes-agent-framework
pip install -r requirements.txt

# Run an interactive REPL with the default orchestrator agent
python -m prompt_orchestrator --interactive

# Run a workflow by name
python -m prompt_orchestrator run security-scan --subject example.com

# Run a single skill against a subject
python -m prompt_orchestrator skill scan --subject example.com
```

---

## Reference example: domain modules

The repo ships with reference content for **security assessment** as a
working example. The domain isn't load-bearing — it's there to show
how a domain module plugs in. Other domains (research workflows,
ops automation, content pipelines) follow the same pattern.

```
knowledge/
├── owasp-top-10.md          — domain reference module (security domain)
├── owasp-api.md             — domain reference (security domain)
├── owasp-smart-contract.md  — domain reference (security domain)
├── owasp-llm.md             — domain reference (security domain)
├── owasp-web.md             — domain reference (security domain)
├── payloads/
│   ├── xss.txt
│   ├── sqli.txt
│   ├── lfi.txt
│   └── ssrf.txt
├── checklists/
│   ├── web-testing.md
│   └── api-testing.md
└── techniques/
    └── lateral-movement.md
```

---

## Design principles

1. **Markdown over code for prompts.** Every system prompt lives in a
   `.md` file with frontmatter. Retuning the agent is a content edit,
   not a code change.
2. **Uniform tool interface.** A scanner for security is structurally
   identical to a scanner for compliance checks. The orchestrator
   doesn't know or care what domain the tool belongs to.
3. **Composing memory.** Each memory layer solves one recall problem.
   Combining them lets the agent answer questions it couldn't answer
   from any single layer.
4. **Crash-safe workflows.** Every phase writes state before yielding.
   A workflow can be killed mid-flight and resumed without loss.
5. **Domain agnostic.** The engine has no opinions about the domain.
   Security, research, ops, content — same engine, different skill
   sets.

---

## License

MIT. See [LICENSE](LICENSE).

## About

Built by [Cameron Weyers](https://github.com/kigansolutions), Kigan Agentic AI Solutions.
