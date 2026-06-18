# Tools Reference

Reference skill listing the available tools in `tools/registry.py`.
Loaded when the user asks "what tools do I have?".

## Generic tools (always active)

| Tool                | Purpose                              |
|---------------------|--------------------------------------|
| `curl_head`         | HEAD request, returns headers        |
| `curl_get`          | GET request, returns body            |
| `whois`             | Domain registration lookup           |
| `check_http_methods`| OPTIONS request, lists HTTP methods  |

## Domain-specific tools (commented out by default)

These are shipped as commented-out reference implementations in
`tools/registry.py`. Uncomment the registration block and the schema
to activate them.

| Tool           | Domain                |
|----------------|-----------------------|
| `run_nmap`     | Network scanning      |
| `run_nuclei`   | Template-based finding|
| `run_subfinder`| Passive enumeration   |
| `run_gobuster` | Wordlist enumeration  |
| `run_nikto`    | Web server scanning   |

## Adding a new tool

1. Write the wrapper method in `tools/registry.py`.
2. Register it in the `tools` dict at `__init__`.
3. Add a matching `*_SCHEMA` dict to `TOOL_SCHEMAS` so the LLM knows
   the tool's parameter shape.

The pattern is identical regardless of what the tool does — CLI,
REST, library, internal service. The orchestrator doesn't care.
