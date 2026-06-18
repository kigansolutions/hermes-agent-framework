# prompt-orchestrator — Knowledge Base

Reference materials available to the agent during workflow execution.
Documents are loaded by `knowledge/base.py` and indexed by category.

## Directory Structure
```
knowledge/
├── owasp-top-10.md          # Generic OWASP Top 10 reference
├── owasp-web.md             # Web security reference
├── owasp-api.md             # API security reference
├── owasp-llm.md             # LLM security reference
└── owasp-smart-contract.md  # Smart contract reference
```

## Adding New References

Drop a markdown file into this directory. The knowledge base
indexer picks it up by filename; the file content is exposed via
the agent's `get_reference_doc()` lookup.