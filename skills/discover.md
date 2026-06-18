# DISCOVER

Discovery phase — passive and active enumeration of the subject. Maps
what exists before deeper phases touch it.

## Phase: 1

## Tools (examples — domain-specific tools slot in here)

- DNS / WHOIS lookups
- Subdomain / asset enumeration
- HTTP probing / fingerprinting
- OSINT aggregators
- Public-source scrapers

## Workflow

### Passive discovery (priority — no direct contact)
```
whois <subject>
dig <subject> ANY
curl_head <url>
```

### Active discovery
```
curl_get <url>
check_http_methods <url>
```

### Output
Handoff to Scan:
- Subject list (endpoints, identifiers, assets)
- Metadata (versions, headers, fingerprints)
- Key findings
- Recommended next steps

## Key findings to document
- Subject metadata
- Operating surface
- Identifiers (IDs, emails, accounts)
- Dependencies (services, libraries)
- Public footprint
