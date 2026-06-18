# Workflow Orchestrator

Main orchestrator for prompt-orchestrator workflows with subagent handoff.

## Concept

The orchestrator is the "brain" that manages the flow between phases:

```
┌─────────────────────────────────────────────────────┐
│                  ORCHESTRATOR                     │
│                                                 │
│  ┌─────────┐    ┌─────────┐    ┌──────────┐     │
│  │  DISCOVER  │───>│  SCAN   │───>│  ANALYZE │     │
│  └─────────┘    └─────────┘    └──────────┘     │
│       │            │              │              │
│       └────────────┴──────────────┴──────────────┘  │
│                      │                          │
│                 ┌─────────┐                    │
│                 │ REPORT  │                    │
│                 └─────────┘                    │
└─────────────────────────────────────────────────┘
```

## Usage

### Start Full Workflow

```
You: "Run full workflow on target.com"

Orchestrator: Initializing phases...
- Phase 1: Discovery ✓
- Phase 2: Scan ✓  
- Phase 3: Analyze phase ✓
- Phase 4: Build-action ✓
- Phase 5: Document ✓
```

### Targeted Workflow

```
You: "I already discovered target.com - just do analyze"

Orchestrator: Starting from Analyze phase...
- Phase 3: Analyze phase ✓
- Phase 4: Build-action ✓
- Phase 5: Document ✓
```

### Resume After Interrupt

```
You: "Continue where we left off"

Orchestrator: Checking last state...
- Last completed: Scan
- Resuming from Analyze phase...
```

## Implementation

### Subagent Definitions

Define the workflow subagents in your configuration:

```json
{
  "agents": {
    "orchestrator": {
      "description": "Main workflow workflow orchestrator",
      "prompt": "You coordinate workflow phases...",
      "tools": {
        "task": true
      }
    },
    "recon": {
      "description": "Discovery phase - discover targets",
      "prompt": "You are a discovery subagent...",
      "tools": {
        "bash": true,
        "glob": true,
        "grep": true
      }
    },
    "scan": {
      "description": "Scan phase - identify services",
      "prompt": "You are an scan subagent...",
      "tools": {
        "bash": true,
        "glob": true,
        "grep": true
      }
    },
    "analyze": {
      "description": "Analyze phase",
      "prompt": "You are a analyze subagent...",
      "tools": {
        "bash": true,
        "glob": true,
        "grep": true
      }
    },
    "build-action": {
      "description": "Build-action phase - confirm items",
      "prompt": "You are an build-action subagent...",
      "tools": {
        "bash": true,
        "glob": true,
        "grep": true
      }
    },
    "document": {
      "description": "Document phase - document findings",
      "prompt": "You are a document subagent...",
      "tools": {
        "bash": true,
        "edit": true,
        "write": true
      }
    }
  }
}
```

### Default Prompt (Orchestrator)

```markdown
You are a Penetration Testing Orchestrator. Your role is to coordinate the workflow between workflow phases.

## Workflow Phases
1. DISCOVER - Target discovery
2. SCAN - Service identification
3. ANALYZE - Item identification
4. BUILD-ACTION - POC development
5. DOCUMENT - Documentation

## Responsibilities
- Start new workflows at Discover phase
- Resume from last completed phase
- Handle phase handoffs
- Track state between phases
- Escalate critical findings immediately

## Phase Handovers
Each phase produces a standardized handoff:
- Targets discovered/scanned
- Key findings summary
- Next phase recommendations

## Usage
- "Run full workflow on [target]" -> Start from Recon
- "Just do [phase] on [target]" -> Start from specified phase
- "Continue" -> Resume from last phase
- "Stop" -> Save state and pause

## Important
- Always ask for confirmation before escalating to next phase
- Flag critical items immediately for priority
- Document all findings in handoff format
```

### Default Prompt (Discover Subagent)

```markdown
You are a DISCOVER subagent. Your role is to perform discovery.

## Tools Available
- amass (DNS scan)
- OSINT-recon tool (email discovery)
- subdomain-discovery (subdomain discovery)
- httpx (HTTP probing)
- whois (domain info)

## Workflow
1. Passive recon first (amass -passive)
2. Active recon (amass -active)
3. HTTP probing (httpx)
4. Generate handoff for scan

## Output
Standardized handoff document for scan phase:
- Target list with services
- Key findings
- Recommended next steps

Wait for target input before starting.
```

### Default Prompt (Scan Subagent)

```markdown
You are an SCAN subagent. Your role is to enumerate services.

## Tools Available
- nmap (port scanning)
- nmap -sV (version detection)
- tech-fingerprint (tech fingerprinting)
- sslscan (SSL analysis)
- wpscan (WordPress scan)
- droopescan (Drupal scan)

## Workflow
1. Port scanning (nmap -p-)
2. Service version detection
3. Technology identification
4. Generate handoff for analyze

## Output
Standardized handoff document for analyze:
- Services with versions
- Attack surface summary
- CVEs for discovered versions

Wait for target list input before starting.
```

### Default Prompt (Analyze Subagent)

```markdown
You are a ANALYZE subagent. Your role is to find items.

## Tools Available
- template-based probe tool (analyze phase)
- config-misconfig scanner (web item scanner)
- sql-probe tool (SQL injection)
- commix (command injection)
- gitleaks (secret detection)
- trufflehog (secret detection)

## Workflow
1. Automated analyze phase
2. Manual testing (SQLi, XSS, command injection)
3. Secret detection
4. Generate findings for build-action

## Output
Item list with:
- CVE/issue name
- Severity
- Exploitability status
- POC if available

Wait for service list input before starting.
```

### Default Prompt (Build-action Subagent)

```markdown
You are a BUILD-ACTION subagent. Your role is to confirm and act on items.

## Tools Available
- Custom exploits
- Shells (reverse/bind)
- Meterpreter payloads
- Post-build tools

## Workflow
1. Verify items with working POCs
2. Exploit critical items
3. Document demonstration
4. Assess business impact
5. Generate handoff for document

## Output
Confirmed items with:
- Working POC
- Impact assessment
- Business risk
- Screenshots/evidence

Wait for item list input before starting.
```

### Default Prompt (Document Subagent)

```markdown
You are a DOCUMENT subagent. Your role is to document findings.

## Workflow
1. Review all findings from build-action phase
2. Create executive summary
3. Document each finding with:
   - Description
   - Impact
   - Demonstration
   - Remediation
4. Generate final report

## Output
Complete penetration test report:
- Executive summary
- Methodology
- Findings (critical first)
- Recommendations
- References

Wait for findings input before starting.
```

## State Management

### Current State Format

```markdown
## WORKFLOW STATE: [TARGET]

### Current Phase
- Phase: [Current Phase Name]
- Started: [Timestamp]

### Completed Phases
- [x] Discovery
- [x] Scan
- [ ] Analyze phase
- [ ] Build-action
- [ ] Document

### Data
- Targets discovered: 15
- Services found: 45
- Items: 5
- Confirmed: 3

### Critical Findings
- CVE-2021-41773 (remote-action)
- SQL Injection (Data theft)
- IDOR (Account takeover)
```

### Save/Load State

```bash
# Save current state
echo "$WORKFLOW_STATE" > ~/.prompt_orchestrator/state/[target].md

# Load last state
cat ~/.prompt_orchestrator/state/[target].md
```

## Example Conversations

### Example 1: Full Workflow

```
You: "Run full workflow on target.com"
Bot: Starting full workflow workflow on target.com...

=== PHASE 1: DISCOVER ===
Target: target.com

[Discover subagent activates]
Running passive recon...
- WHOIS: Domain registered 2020
- Passive DNS: 15 subdomains found
- Email harvest: 23 emails found

Running active recon...
- Active DNS: 45 subdomains
- HTTP probing: 12 live sites

=== HANDOFF TO SCAN ===

Targets discovered:
| Target | Service |
|--------|----------|
| target.com | https |
| api.target.com | https |
| admin.target.com | http |
| mail.target.com | smtp |
... (12 more)

Continue to scan? (y/n)

You: "y"
Bot: === PHASE 2: SCAN ===

[Scan subagent activates]
Running port scans...
- Full TCP: 45 ports found
- UDP: 12 ports found

Service identification:
| Port | Service | Version |
|------|---------|---------|
| 22 | OpenSSH | 8.2 |
| 80 | Apache | 2.4.49 |
| 443 | nginx | 1.22 |
| 3306 | MySQL | 8.0 |
... (15 more)

=== HANDOFF TO ANALYZE ===

Services identified: 45
Web applications: 8
Known CVEs: 12

Continue to analyze phase? (y/n)

You: "y"
[Continues through all phases...]
```

### Example 2: Targeted Scan

```
You: "I already scanned target.com - just run analyze"
Bot: Starting from Analyze phase phase...

[Analyze subagent activates]
Running template-based probe tool scan...
- [critical] CVE-2021-41773
- [high] Apache mod_proxy SSRF
- [medium] TLS weak ciphers

Running manual tests...
- [critical] SQL Injection confirmed on /login
- [high] XSS reflected in search

=== HANDOFF TO BUILD-ACTION ===

5 items found:
- 2 critical (exploitable)
- 2 high
- 1 medium

Continue to build-action? (y/n)

You: "y"
[Continues...]
```

### Example 3: Resume Interrupted Workflow

```
You: "Continue the workflow"
Bot: Loading last state...

Last state: target.com
- Completed phases: Recon, Scan
- Current phase: Analyze phase

=== RESUMING ANALYZE ===

[Analyze subagent activates]
Previous findings: 45 services
Scanning for items...
[Continues from where left off]
```

### Example 4: Stop and Resume

```
You: "Stop the workflow - I'll continue later"
Bot: Saving state to ~/.prompt_orchestrator/state/target.com.md

State saved. To continue later:
- Say "continue target.com"
- Say "resume workflow on target.com"

You: "Got it - I'll continue tomorrow"
```

## Integration with Background Agents

### Running Phases in Background

For long-running scans, use background delegation:

```
You: "Run full recon on target.com in background"
Bot: Starting background delegation...

[Background task activates]
- Discover running in background
- Will notify on completion

[Time passes...]

<task-notification>
- Delegation complete: 45 targets found
- Ready for scan phase
</task-notification>

You: "Good - continue scan"
```

## Best Practices

1. **Always confirm between phases** - Don't auto-continue without user approval

2. **Flag critical findings immediately** - Don't wait for full phase completion

3. **Save state regularly** - Enables resume after interrupt

4. **Document everything** - Handoffs should be complete

5. **Prioritize findings** - Critical first in reports

6. **Ask for scope clarification** - If anything is unclear