# Workflow Orchestrator

Main orchestrator for PromptOrchestrator pentesting workflows with subagent handoff.

## Concept

The orchestrator is the "brain" that manages the flow between phases:

```
┌─────────────────────────────────────────────────────┐
│                  ORCHESTRATOR                     │
│                                                 │
│  ┌─────────┐    ┌─────────┐    ┌──────────┐     │
│  │  RECON  │───>│  ENUM   │───>│  VULN    │     │
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

### Start Full Pentest

```
You: "Run full pentest on target.com"

Orchestrator: Initializing phases...
- Phase 1: Reconnaissance ✓
- Phase 2: Enumeration ✓  
- Phase 3: Vulnerability Analysis ✓
- Phase 4: Exploitation ✓
- Phase 5: Reporting ✓
```

### Targeted Workflow

```
You: "I already recon'd target.com - just do vuln analysis"

Orchestrator: Starting from Vuln Analysis phase...
- Phase 3: Vulnerability Analysis ✓
- Phase 4: Exploitation ✓
- Phase 5: Reporting ✓
```

### Resume After Interrupt

```
You: "Continue where we left off"

Orchestrator: Checking last state...
- Last completed: Enumeration
- Resuming from Vulnerability Analysis...
```

## Implementation

### Subagent Definitions

Define the workflow subagents in your configuration:

```json
{
  "agents": {
    "orchestrator": {
      "description": "Main pentest workflow orchestrator",
      "prompt": "You coordinate pentest phases...",
      "tools": {
        "task": true
      }
    },
    "recon": {
      "description": "Reconnaissance phase - discover targets",
      "prompt": "You are a reconnaissance subagent...",
      "tools": {
        "bash": true,
        "glob": true,
        "grep": true
      }
    },
    "enumeration": {
      "description": "Enumeration phase - identify services",
      "prompt": "You are an enumeration subagent...",
      "tools": {
        "bash": true,
        "glob": true,
        "grep": true
      }
    },
    "vuln_analysis": {
      "description": "Vulnerability analysis phase",
      "prompt": "You are a vuln analysis subagent...",
      "tools": {
        "bash": true,
        "glob": true,
        "grep": true
      }
    },
    "exploitation": {
      "description": "Exploitation phase - confirm vulnerabilities",
      "prompt": "You are an exploitation subagent...",
      "tools": {
        "bash": true,
        "glob": true,
        "grep": true
      }
    },
    "reporting": {
      "description": "Reporting phase - document findings",
      "prompt": "You are a reporting subagent...",
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
You are a Penetration Testing Orchestrator. Your role is to coordinate the workflow between pentest phases.

## Workflow Phases
1. RECON - Target discovery
2. ENUMERATION - Service identification
3. VULN_ANALYSIS - Vulnerability identification
4. EXPLOITATION - POC development
5. REPORTING - Documentation

## Responsibilities
- Start new pentests at Recon phase
- Resume from last completed phase
- Handle phase handoffs
- Track state between phases
- Escalate critical findings immediately

## Phase Handovers
Each phase produces a standardized handoff:
- Targets discovered/enumerated
- Key findings summary
- Next phase recommendations

## Usage
- "Run full pentest on [target]" -> Start from Recon
- "Just do [phase] on [target]" -> Start from specified phase
- "Continue" -> Resume from last phase
- "Stop" -> Save state and pause

## Important
- Always ask for confirmation before escalating to next phase
- Flag critical vulnerabilities immediately for priority
- Document all findings in handoff format
```

### Default Prompt (Recon Subagent)

```markdown
You are a RECON subagent. Your role is to perform reconnaissance.

## Tools Available
- amass (DNS enumeration)
- theHarvester (email discovery)
- subfinder (subdomain discovery)
- httpx (HTTP probing)
- whois (domain info)

## Workflow
1. Passive recon first (amass -passive)
2. Active recon (amass -active)
3. HTTP probing (httpx)
4. Generate handoff for enumeration

## Output
Standardized handoff document for enumeration phase:
- Target list with services
- Key findings
- Recommended next steps

Wait for target input before starting.
```

### Default Prompt (Enumeration Subagent)

```markdown
You are an ENUMERATION subagent. Your role is to enumerate services.

## Tools Available
- nmap (port scanning)
- nmap -sV (version detection)
- whatweb (tech fingerprinting)
- sslscan (SSL analysis)
- wpscan (WordPress scan)
- droopescan (Drupal scan)

## Workflow
1. Port scanning (nmap -p-)
2. Service version detection
3. Technology identification
4. Generate handoff for vuln analysis

## Output
Standardized handoff document for vuln analysis:
- Services with versions
- Attack surface summary
- CVEs for discovered versions

Wait for target list input before starting.
```

### Default Prompt (Vuln Analysis Subagent)

```markdown
You are a VULN_ANALYSIS subagent. Your role is to find vulnerabilities.

## Tools Available
- nuclei (vulnerability scanning)
- nikto (web vulnerability scanner)
- sqlmap (SQL injection)
- commix (command injection)
- gitleaks (secret detection)
- trufflehog (secret detection)

## Workflow
1. Automated vulnerability scanning
2. Manual testing (SQLi, XSS, command injection)
3. Secret detection
4. Generate findings for exploitation

## Output
Vulnerability list with:
- CVE/issue name
- Severity
- Exploitability status
- POC if available

Wait for service list input before starting.
```

### Default Prompt (Exploitation Subagent)

```markdown
You are an EXPLOITATION subagent. Your role is to confirm and exploit vulnerabilities.

## Tools Available
- Custom exploits
- Shells (reverse/bind)
- Meterpreter payloads
- Post-exploitation tools

## Workflow
1. Verify vulnerabilities with working POCs
2. Exploit critical vulnerabilities
3. Document proof of concept
4. Assess business impact
5. Generate handoff for reporting

## Output
Confirmed vulnerabilities with:
- Working POC
- Impact assessment
- Business risk
- Screenshots/evidence

Wait for vulnerability list input before starting.
```

### Default Prompt (Reporting Subagent)

```markdown
You are a REPORTING subagent. Your role is to document findings.

## Workflow
1. Review all findings from exploitation phase
2. Create executive summary
3. Document each finding with:
   - Description
   - Impact
   - Proof of Concept
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
## PENTEST STATE: [TARGET]

### Current Phase
- Phase: [Current Phase Name]
- Started: [Timestamp]

### Completed Phases
- [x] Reconnaissance
- [x] Enumeration
- [ ] Vulnerability Analysis
- [ ] Exploitation
- [ ] Reporting

### Data
- Targets discovered: 15
- Services found: 45
- Vulnerabilities: 5
- Confirmed: 3

### Critical Findings
- CVE-2021-41773 (RCE)
- SQL Injection (Data theft)
- IDOR (Account takeover)
```

### Save/Load State

```bash
# Save current state
echo "$PENTEST_STATE" > ~/.prompt_orchestrator/state/[target].md

# Load last state
cat ~/.prompt_orchestrator/state/[target].md
```

## Example Conversations

### Example 1: Full Pentest

```
You: "Run full pentest on target.com"
Bot: Starting full pentest workflow on target.com...

=== PHASE 1: RECON ===
Target: target.com

[Recon subagent activates]
Running passive recon...
- WHOIS: Domain registered 2020
- Passive DNS: 15 subdomains found
- Email harvest: 23 emails found

Running active recon...
- Active DNS: 45 subdomains
- HTTP probing: 12 live sites

=== HANDOFF TO ENUMERATION ===

Targets discovered:
| Target | Service |
|--------|----------|
| target.com | https |
| api.target.com | https |
| admin.target.com | http |
| mail.target.com | smtp |
... (12 more)

Continue to enumeration? (y/n)

You: "y"
Bot: === PHASE 2: ENUMERATION ===

[Enumeration subagent activates]
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

=== HANDOFF TO VULN ANALYSIS ===

Services identified: 45
Web applications: 8
Known CVEs: 12

Continue to vulnerability analysis? (y/n)

You: "y"
[Continues through all phases...]
```

### Example 2: Targeted Scan

```
You: "I already enumerated target.com - just run vuln analysis"
Bot: Starting from Vulnerability Analysis phase...

[Vuln Analysis subagent activates]
Running nuclei scan...
- [critical] CVE-2021-41773
- [high] Apache mod_proxy SSRF
- [medium] TLS weak ciphers

Running manual tests...
- [critical] SQL Injection confirmed on /login
- [high] XSS reflected in search

=== HANDOFF TO EXPLOITATION ===

5 vulnerabilities found:
- 2 critical (exploitable)
- 2 high
- 1 medium

Continue to exploitation? (y/n)

You: "y"
[Continues...]
```

### Example 3: Resume Interrupted Workflow

```
You: "Continue the pentest"
Bot: Loading last state...

Last state: target.com
- Completed phases: Recon, Enumeration
- Current phase: Vulnerability Analysis

=== RESUMING VULN ANALYSIS ===

[Vuln Analysis subagent activates]
Previous findings: 45 services
Scanning for vulnerabilities...
[Continues from where left off]
```

### Example 4: Stop and Resume

```
You: "Stop the pentest - I'll continue later"
Bot: Saving state to ~/.prompt_orchestrator/state/target.com.md

State saved. To continue later:
- Say "continue target.com"
- Say "resume pentest on target.com"

You: "Got it - I'll continue tomorrow"
```

## Integration with Background Agents

### Running Phases in Background

For long-running scans, use background delegation:

```
You: "Run full recon on target.com in background"
Bot: Starting background delegation...

[Background task activates]
- Recon running in background
- Will notify on completion

[Time passes...]

<task-notification>
- Delegation complete: 45 targets found
- Ready for enumeration phase
</task-notification>

You: "Good - continue enumeration"
```

## Best Practices

1. **Always confirm between phases** - Don't auto-continue without user approval

2. **Flag critical findings immediately** - Don't wait for full phase completion

3. **Save state regularly** - Enables resume after interrupt

4. **Document everything** - Handoffs should be complete

5. **Prioritize findings** - Critical first in reports

6. **Ask for scope clarification** - If anything is unclear