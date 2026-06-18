# SCAN

Surface-mapping phase — service detection, version identification,
operating-surface enumeration.

## Phase: 2

## Tools (examples)
- Port scanners
- Service-version detectors
- Tech fingerprinting
- TLS / certificate analyzers

## Workflow

### Surface enumeration
```
curl_get <url>
curl_get <url> --follow_redirects false
```

### Version detection
Identify versions of services, libraries, frameworks. Cross-reference
with public vulnerability databases for known issues.

### Tech fingerprinting
Headers, error pages, default routes, file extensions.

## Output
Handoff to Analyze:
- Service table with versions
- Known-version references
- Surface summary
- Technology stack
