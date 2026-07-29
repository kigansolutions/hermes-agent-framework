# hermes-agent-framework

> A modular Python reference framework for orchestrating prompt-driven AI agents
> with persistent multi-layer memory, a markdown-defined skill registry,
> and a pluggable tool layer. Designed to show how CLI/REST tools can be
> wrapped as typed operations an agent can invoke under local operator control.

Built around five primitives: **agents** (role + prompt), **skills**
(markdown prompt templates), **tools** (CLI/REST wrappers), **memory**
(5-layer persistence), and **workflows** (composable phases). Same
architecture underpins the Hermes agent platform I run day to day —
this is a generic, redacted reference implementation of that
architecture, open for inspection.

This public repository is not a production-hardened autonomous assistant or a
live deployment surface. Treat it as an inspectable framework until CI,
packaging, command-safety, browser-safety, credential-memory, and runtime
validation gates are closed.

---

## What it does

`prompt-orchestrator` lets you build agents that:

1. **Load role + prompt from markdown** — agents are `.md` files with
   frontmatter, no code changes needed to retune the system prompt.
2. **Compose workflows from skills** — each skill is a reusable prompt
   template that wraps a tool or a reasoning pattern.
3. **Wrap tools behind a uniform interface** — `curl`, REST APIs, custom
   Python, and local CLI adapters can share the same adapter shape once they
   are explicitly allowed for a trusted local workflow.
4. **Remember across sessions** — 5-layer memory: working, semantic
   (vector), episodic (key-value), knowledge (wiki), session (FTS).
5. **Run workflows in parallel with state save/resume** — the
   execution engine handles parallelism, retries, and crash recovery.
6. **Expose via CLI, REPL, or Telegram bot** — same engine, multiple
   surfaces, but live surfaces require a separate safety review before use.

The orchestrator is **domain-agnostic**. The same engine pattern can support
security assessments, research workflows, smart-contract audits, and DevOps
automation. Skill sets differ; the engine stays the same.

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

Skills are reusable prompt templates. They can wrap a tool, encode a reasoning
pattern, or both. The skill registry reads them at startup.

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

Tools are Python modules that wrap an external capability behind a typed
interface. This repository includes reference adapters for local CLI execution,
Caido, browser automation, web search, and Telegram. Some adapters are sensitive
and are restricted by [the safety policy](docs/safety-policy.md).

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
**compounds** because the LLM rewrites raw observations into structured wiki
pages over time, instead of re-deriving them each session.

Credential-like memory is disabled by policy for public/client-safe use until a
separate data-handling decision covers consent, encryption, retention, purge,
and secret-scanning evidence.

### 5. Workflows (`execution/engine.py`)

Workflows are sequences of phases. The execution engine runs them with
parallelism, retries, and crash recovery. State is persisted between phases so a
crashed workflow can resume mid-flight.

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
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# Static smoke validation used by CI. This compiles representative modules
# without importing them or running live tools.
python scripts/smoke_validate.py

# Current CLI module path for the reference execution engine
python -m execution.engine workflow localhost
python -m execution.engine discover localhost

# Inspect local knowledge-store commands
python -m knowledge.knowledge target
```

Optional vector-memory and browser-automation dependencies live in
`requirements-optional.txt`. Install them only in a controlled local environment
after reviewing [the safety policy](docs/safety-policy.md).

---

## Safety boundaries

- Command execution is trusted-local-operator-only until allowlists, argument
  handling, scope confirmation, destructive-action gates, audit logging, and
  safe fixture tests are implemented.
- Browser stealth mode is restricted security-testing functionality, not a
  general assistant automation feature.
- Credential-like memory must not store real passwords, tokens, hashes, client
  data, payroll data, or private runtime memory until a separate handling
  decision is recorded.
- Telegram, Caido, browser automation, live accounts, and private Hermes runtime
  data are out of scope for this public repository unless Cameron explicitly
  approves a separate runtime-validation PR.

See [docs/safety-policy.md](docs/safety-policy.md) for the full policy.

---

## Reference example: domain modules

The repo ships with reference content for **security assessment** as a working
example. The domain is not load-bearing — it is there to show how a domain module
plugs in. Other domains such as research workflows, ops automation, and content
pipelines follow the same pattern.

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

1. **Markdown over code for prompts.** Every system prompt lives in a `.md` file
   with frontmatter. Retuning the agent is a content edit, not a code change.
2. **Uniform tool interface.** A scanner for security is structurally identical
   to a scanner for compliance checks. The orchestrator does not need domain
   knowledge to route tool results.
3. **Composing memory.** Each memory layer solves one recall problem. Combining
   them lets the agent answer questions it could not answer from any single
   layer.
4. **Crash-safe workflows.** Every phase writes state before yielding. A workflow
   can be killed mid-flight and resumed without loss.
5. **Domain agnostic.** The engine has no opinions about the domain. Security,
   research, ops, content — same engine, different skill sets.
6. **Safety before autonomy.** Public and live surfaces need explicit gates
   before shell execution, browser automation, credential handling, or external
   account actions are exposed.

---

## Validation

Pull requests and pushes to `main` run `.github/workflows/ci.yml`, which:

- installs base dependencies from `requirements.txt`;
- compiles representative Python modules;
- confirms the license, safety policy, optional dependency file, and corrected
  quick-start path are present.

The smoke check does not import Hermes modules, run shell commands, start a
browser, access Telegram/Caido, or touch live runtime data.

---

## License

MIT. See [LICENSE](LICENSE).

## About

Built by [Cameron Weyers](https://github.com/kigansolutions), Kigan Agentic AI Solutions.
