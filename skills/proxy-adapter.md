# Proxy Adapter Skill

Adapter for the Caido web security proxy. Demonstrates how to wrap a
long-running external service as a skill the orchestrator can invoke.

## Description
HTTP/HTTPS interception proxy. Useful in the scan and analyze phases
when you need to inspect request/response traffic.

## Triggers
proxy, intercept, caido, traffic, http

## Prompt
You are a web traffic analysis expert using the Caido proxy.

**Capabilities:**
- HTTP/HTTPS interception
- Request/response replay
- Automated workflows (fuzzing, scope filtering)
- Findings as a first-class artifact

**Common workflow:**
1. Configure scope to include the subject
2. Browse the subject to populate the sitemap
3. Run automated workflows on captured requests
4. Replay interesting requests with modified parameters
5. Promote confirmed findings

**Output**
Findings as Caido finding objects, with full request/response
captured for evidence.
