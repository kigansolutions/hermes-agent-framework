# prompt-orchestrator — Quick Reference

When the user asks to run a workflow against a subject, follow this
generic pattern. Domain-specific commands slot into the same shape.

## Quick scan
```bash
# Surface enumeration
curl_head <url>
whois <domain>
check_http_methods <url>
```

## Surface mapping
```bash
# Build a fuller picture of the subject
curl_get <url>
curl_get <url> --follow_redirects false
```

## Domain-specific tooling
The orchestrator ships with generic tools active. Domain-specific
tools (port scanners, finding templates, etc.) live in
`tools/registry.py` as commented-out reference implementations.
Uncomment the registration block and the corresponding schema to
activate them.

## Examples

- "run a workflow against example.com" → orchestrator runs the
  default phase tree (discover → scan → analyze → build →
  integrate → document)
- "scan example.com" → invoke the scan skill directly with
  `subject=example.com`
- "what's running on example.com?" → invoke the discover skill

## Rules

1. Run real tools via the registry. Don't fabricate output.
2. Report findings clearly with evidence.
3. Don't ask permission for generic scans (curl, whois).
4. Verify scope if the request is unclear.
5. Document everything you find.
