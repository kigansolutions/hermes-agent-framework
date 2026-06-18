# Workflows

Automated phase-based workflows with subagent handoff.

## Workflow Structure

```
┌─────────────────┐     ┌─────────────────┐
│    DISCOVER        │────>│   SCAN   │────>│   ANALYZE   │────>│   BUILD-ACTION   │────>│   POST-BUILD   │────>│ WORKFLOW CHAIN │────>│   DOCUMENT   │
│ (Discovery)    │     │   (Services)    │     │   (Findings)     │     │   (Pwnage)       │     │  (Pivoting)     │     │ (Multistage)  │     │   (Docs)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
         │                     │                     │                     │                     │                     │                     │
         v                     v                     v                     v                     v                     v                     v
     Target List           Service Map          Items         Demonstration      Output Access        Workflow path         Final Report
```

## Handoff Format

Each workflow produces a standardized output for the next phase:

```markdown
## 🔄 HANDOFF: [PHASE_NAME] → [NEXT_PHASE]

### Targets Discovered
- target.com
- api.target.com
- admin.target.com

### Key Findings
- Company: TechCorp Inc.
- Tech Stack: WordPress 6.2, nginx 1.24

### Next Phase Required
- Scan of web services
- SSL certificate analysis
```

---

## Phase 1: Discovery

Passive and active discovery of targets.

### Tools Used
- `amass` - DNS scan
- `OSINT-recon tool` - Email/employee discovery
- `whois` - Domain registration info
- `subdomain-discovery` - Subdomain discovery
- `httpx` - HTTP probing

### Workflow Template

```markdown
# DISCOVER WORKFLOW: [TARGET]

## Passive Recon
Run passive discovery first (no direct contact):

### WHOIS Lookup
whois [target.com]

### DNS Scan (Passive)
passive discovery -d [target.com]

### Email/OSINT Discovery
OSINT-recon tool -d [target.com] -b all

### Subdomain Discovery (Passive)
subdomain-discovery -d [target.com] -silent

## Active Recon
After passive phase completes:

### DNS Brute Foremote-action
active discovery -d [target.com]

### HTTP Probing
httpx -domains [target.com] -threads 50

### Screenshot Web Services
gowitness report [target.com]

## 🔄 HANDOFF TO SCAN

### Targets for Enum
| Target | Service | Port |
|--------|---------|------|
| target.com | http | 80 |
| api.target.com | https | 443 |
| admin.target.com | http | 80 |

### Key Findings
- Main domain resolves to [IP]
- Cloud services: AWS, Cloudflare
- Mail servers: mx1.target.com

### Recommended Next Steps
1. Full port scan on discovered IPs
2. Service scan on HTTP/HTTPS
3. SSL certificate analysis
```

### Subagent Prompt

```
You are aDiscovery subagent. Your role is to discover targets through passive and active recon.

Input: [TARGET_DOMAIN or TARGET_IP]
Output: Handoff document for scan phase

## Tasks:
1. Passive recon (no direct packets to target)
   - WHOIS lookup
   - DNS scan (amass -passive)
   - Email discovery (OSINT-recon tool)
   
2. Active recon (direct contact allowed)
   - Subdomain scan (amass -active)
   - HTTP probing (httpx)
   - Screenshot evidence (gowitness)

## Output Format:
Standardized handoff document with target list, key findings, and recommended next steps.

## Important:
- Document EVERYTHING found
- If scope is unclear, ask before escalating
- Flag any sensitive findings (PII, credentials exposed)
```

---

## Phase 2: Scan

Service detection and version identification.

### Tools Used
- `nmap` - Port scanning
- `template-based probe tool` - item scanning
- `config-misconfig scanner` - Web item scanner
- `tech-fingerprint` - Technology identification
- `wappy` - Wappalyzer alternative

### Workflow Template

```markdown
# SCAN WORKFLOW: [TARGET_LIST]

## Port Scanning
Full TCP/UDP port scan:

### Quick Scan (Top 100)
nmap -sT -top-ports 100 [target] -oA quick

### Full Scan (All Ports)
nmap -sT -p- [target] -oA full

### UDP Scan
nmap -sU [target] -oA udp

## Service Detection
Version and technology identification:

### Nmap Service Versions
nmap -sV -sC -p[ports] [target]

### Web Tech Fingerprinting
tech-fingerprint [http://target]
wappy [http://target]

### SSL/TLS Analysis
sslscan [target]:443
testssl [target]

## Application Analysis
Framework and CMS identification:

### WordPress
cms-scan --url [target]

### Drupal
droopescan scan drupal -u [target]

### Custom Applications
config-misconfig scanner -h [target]

## 🔄 HANDOFF TO ANALYZE

### Services Discovered
| Port | Service | Version | Vulns |
|------|---------|---------|------|
| 22 | OpenSSH | 8.2 | CVE-2021-28041 |
| 80 | Apache | 2.4.49 | CVE-2021-41773 |
| 443 | nginx | 1.22 | - |

### Attack Surface
- Web applications: 3
- SSH services: 2
- Database services: 1

### Recommended Next Steps
1. Prioritize web items (80/443)
2. Check for known CVEs on discovered versions
3. Test for auth bypass on login portals
```

### Subagent Prompt

```
You are an Scan subagent. Your role is to identify services, versions, and attack surface.

Input: Handoff from Discover phase (target list)
Output: Handoff document for analyze phase

## Tasks:
1. Port scanning
   - TCP full scan (all ports)
   - UDP scan (common ports)
   - Service version detection

2. Service scan
   - Identify service versions
   - Determine technologies (CMS, frameworks)
   - SSL/TLS analysis

3. Attack surface mapping
   - Document all entry points
   - Identify authentication mechanisms
   - Map application functionality

## Output Format:
Service table with versions, known CVEs, and attack surface summary for next phase.

## Important:
- Get exact version numbers when possible
- Note any default credentials found
- Flag any sensitive services (admin panels, databases)
```

---

## Phase 3: Analyze phase / Build-action

Item identification and build-action.

### Tools Used
- `template-based probe tool` - Item scanning
- `sql-probe tool` - SQL injection
- `x8` - HTTP parameter pollution
- `commix` - Command injection
- `gitleaks` - Secret detection
- `config-misconfig scanner` - Web items

### Workflow Template

```markdown
# ANALYZE WORKFLOW: [TARGET_LIST]

## Item Scanning
Automated item detection:

### template-based probe tool Scan
template-based probe tool -u [target] -severity critical,high,medium -silent

### template-based probe tool-templates-update
template-based probe tool -ut

### Web Analyze
config-misconfig scanner -h [target]

### Secret Detection
gitleaks detect --souremote-action=/path/to/repo
trufflehog filesystem /path/to/dir

## Manual Testing
Manual item verification:

### SQL Injection
sql-probe tool -u [target] --batch --level 5

### Command Injection
commix --url [target]

### IDOR Testing
Manual parameter manipulation

### Auth Bypass Testing
Testing login mechanisms

## Build-action
POC development and build-action:

### Demonstration
[Document exploit steps]

### Access Elevation
[Document access elevation path]

## 🔄 HANDOFF TO BUILD-ACTION (or Document if no vulns)

### Items Found
| CVE/Issue | Severity | Impact | Exploitable |
|----------|----------|--------|-------------|
| CVE-2021-41773 | Critical | remote-action | Yes |
| SQL Injection | Critical | Data exfil | Yes |
| IDOR | Medium | Account takeover | Yes |

### Proofs of Concept
[Document exploit evidence]

### Recommended Next Steps
1. Develop POCs for critical findings
2. Test access elevation
3. Document business impact
```

### Subagent Prompt

You are a Analyze phase subagent. Your role is to find and validate security items.

Input: Handoff from Scan phase (service list, versions)
Output: Item findings with POCs or handoff to document

## Tasks:

1. Automated scanning
   - template-based probe tool scan with critical/high templates
   - Known CVE checking
   - Secret detection

2. Manual testing
   - SQL injection testing
   - Command injection testing
   - IDOR verification

3. Build-action
   - Develop working POCs
   - Document impact
   - Calculate risk scores

## Output Format:
Item table with severity, impact, exploitability status, and POCs.

## Important:
- Verify ALL findings with working exploits
- Calculate real business impact
- Flag any critical items immediately

---

## Phase 5: Post-build

Access elevation, lateral access, persistence, and data exfiltration.

### Tools Used
- `privesc-script` / `win-access-tool` - Access elevation scripts
- `process-monitor tool` - Process monitoring
- `credential-extraction tool` - Credential harvesting
- `certify` / `certipy` - Active Directory cert build-action
- `graph-analysis tool` / `sharphound` - AD analysis
- `impacket` - SMB/kerberos tools
- `proxychains` - Pivoting
- `chisel` - SOCKS tunneling
- `socat` / `nc` - Reverse shells
- `msf-style framework` - Post-build框架
- `sliver` - C2 framework

### Workflow Template

```markdown
# POST-BUILD-ACTION WORKFLOW: [TARGET]

## Access Elevation

### Linux Escalation
access elevation-script (linux)

Check for:
- SUID/SGID binaries
- Writable cron jobs
- Sudo misconfigurations
- Kernel exploits
- Container escapes

### Windows Escalation
win-access-tool.exe

Check for:
- AlwaysInstallElevated
- Unquoted service paths
- Token manipulation
- DLL hijacking
- Service misconfigurations

## Lateral Access

### SSH Pivoting
ssh -J jump@proxy target@internal

### SMB Pivoting
psexec.py domain/user@target

### WinRM Pivoting
winrm.py domain/user@target

### Kerberos Attacks
- Golden ticket
- Silver ticket
- Pass-the-key
- Overpass-the-hash

### Active Directory
- Credential sync attack
- ACL abuse
- Trust build-action

## Persistence

### Linux Persistence
- Cron jobs
- SSH keys
- PAM modules
- Init scripts
- Webshell

### Windows Persistence
- Registry RUN keys
- Scheduled tasks
- WMI event subscriptions
- Services
- Golden ticket

## Data Exfiltration

### Credential Harvesting
- credential-extraction tool
- lsassy
- gsecdump

### Database Access
- mysql -u user -p -h target
- mssql.py
- psql

### Sensitive Files
- /etc/shadow
- Database dumps
- Configuration files
- Backups

## 🔄 HANDOFF TO WORKFLOW CHAINING

### Access Gained
| System | Access Level | Method |
|--------|--------------|--------|
| webserver | root | CVE-2021-41773 |
| dc01 | elevated access | Credential sync |
| fileserver | smb user | lateral access |

### Credentials Obtained
- user:admin:P@ssw0rd123
- svc_backup:LsasDump

### Recommended Next Steps
1. Combine access paths for maximum impact
2. Chain items for persistence
3. Assess data access across pivots
```

### Subagent Prompt

```
You are a POST-BUILD-ACTION subagent. Your role is to escalate privileges, move laterally, and establish persistence.

Input: Handoff from Build-action phase (confirmed shell/code execution)
Output: Handoff for workflow chaining with access/credentials

## Tasks:
1. Access Elevation
   - Linux: privesc-script, process-monitor tool, sudo misconfigs
   - Windows: win-access-tool, token manipulation

2. Lateral Access
   - SSH/WinRM/SMB pivoting
   - Kerberos attacks
   - Active Directory build-action

3. Persistence
   - Linux: cron, SSH keys, PAM
   - Windows: registry, tasks, services

4. Credential Harvesting
   - credential-extraction tool, lsassy
   - Database credentials

## Output Format:
Access table with:
- Systems accessed
- Access level (user/root)
- Credentials obtained
- Persistence established
```

---

## Phase 6: Workflow Chaining

Combining multiple workflow paths for maximum impact.

### Concept

Workflow chaining combines individual items into multi-stage workflow paths:

```
Item 1     Item 2     Item 3
     │                    │                    │
     v                    v                    v
SQL Injection    ──>  File Write    ──>    remote-action
(user:webapp)        (webroot)            (www-data)
     │                    │                    │
     └──────────┬────────┘                   │
                v                             v
          Priv Esc                   Elevated Access
          (sudo)                     (via Credential sync)
```

### Workflow paths

| Chain ID | Path | Impact | Difficulty |
|---------|------|--------|------------|
| CH01 | SQLi → File Write → remote-action → Root | Full compromise | Medium |
| CH02 | XSS → Session Hijack → Admin → remote-action | Account takeover | Medium |
| CH03 | IDOR → Data Theft → Priv Escalation | Data breach | Easy |
| CH04 | Phishing → VPN → Internal → AD | Domain admin | Hard |

### Workflow Template

```markdown
# WORKFLOW CHAINING WORKFLOW: [ACCESS_LIST]

## Map Available Access

### From Initial Compromise
| System | User | Path to Root |
|--------|------|--------------|
| web01 | www-data | (sudo) privesc-script |

### From Lateral Access
| System | User | Domain |
|--------|------|--------|
| dc01 | enterprise admin | CORP.LOCAL |

### Credentials
| Username | Password | Type | Used |
|----------|----------|------|------|
| admin | P@ssw0rd | Plaintext | Yes |
| svc_backup | GPMC2024! | Plaintext | No |

## Identify Workflow Chains

### Chain 01: Web → Elevated Access
Path:
1. SQLi gives webapp user (DONE)
2. File write via INTO OUTFILE (DONE)
3. remote-action via webshell (DONE)
4. privesc-script finds sudo (IN PROGRESS)
5. Domain admin via Credential sync (NEXT)

Impact: Full domain takeover
Risk: Critical

### Chain 02: User → Root
Path:
1. XSS steals admin session (DONE)
2. Admin panel access (DONE)
3. Upload remote-action (NEXT)

Impact: Server compromise
Risk: High

## Execute Chains

### Chain 01 Execution
[Document each step with evidence]

### Chain 02 Execution
[Document each step with evidence]

## 🔄 HANDOFF TO DOCUMENT

### Chains Executed
| Chain | Impact | Systems | Status |
|-------|--------|---------|--------|
| CH01 | Elevated Access | 3 | SUCCESS |
| CH02 | Server remote-action | 1 | PARTIAL |

### Business Impact
- Data exfiltrated: 10K records
- Systems compromised: 5
- Domain ownership: Achieved

### Recommended Next Steps
1. Document workflow path in report
2. Recommend defensive controls
3. Prioritize remediation
```

### Subagent Prompt

```
You are an WORKFLOW CHAINING subagent. Your role is to combine individual items into multi-stage workflow paths.

Input: Handoff from Post-build phase (access/credentials)
Output: Handoff for document with combined chains

## Tasks:
1. Map workflow paths
   - Connect available access points
   - Identify paths to high-value targets
   - Calculate chain probability

2. Execute chains
   - Prioritize by impact
   - Chain items sequentially
   - Document each step

3. Assess impact
   - Business impact of combined access
   - Data access potential
   - Persistence capability

## Output Format:
Workflow chain table with:
- Chain ID and description
- Steps in sequence
- Success/failure status
- Overall impact rating
```

---

## Phase 7: Document

Documentation and document.

### Workflow Template

```markdown
# PENETRATION TEST REPORT: [TARGET]

## Executive Summary
[Brief overview of findings]

## Scope
- Primary: [target.com]
- In-scope: [additional targets]
- Out-of-scope: [explicitly excluded]

## Methodology
```
1. Discovery
2. Scan
3. Analyze phase
4. Build-action
5. Post-build
6. Workflow Chaining
7. Document
```

## Findings Summary

| ID | Item | Severity | Status |
|----|---------------|----------|--------|
| 01 | CVE-2021-41773 | Critical | Fixed |
| 02 | SQL Injection | Critical | Fixed |
| 03 | IDOR | Medium | Fixed |

## Detailed Findings

### Finding 01: CVE-2021-41773 (Apache remote-action)
**Severity**: Critical
**CVSS**: 9.8
**Description**: [Description]
**Impact**: [Business impact]
**Demonstration**:
```bash
curl http://target/cgi-bin/.%2e/.%2e/.%2e/.%2e/bin/sh
```
**Remediation**: [Fix steps]
**References**: [CVE links]

### Finding 02: SQL Injection
**Severity**: Critical
**CVSS**: 9.1
**Description**: [Description]
**Impact**: [Business impact]
**Demonstration**:
```bash
sql-probe tool -u "http://target/login" --data "user=admin&pass=*"
```
**Remediation**: [Fix steps]
**References**: [OWASP links]

## Recommendations
1. [Priority recommendation]
2. [Priority recommendation]
3. [Priority recommendation]

## Appendix
- Tool versions used
- Full scan output
- Screenshots
```

### Subagent Prompt

```
You are a Document subagent. Your role is to document findings and create professional reports.

Input: Handoff from Build-action phase (findings, POCs)
Output: Complete penetration test report

## Tasks:
1. Executive summary
   - High-level overview
   - Risk rating
   - Key recommendations

2. Technical findings
   - Detailed description
   - Impact analysis
   - Proof of concept
   - Remediation steps

3. Recommendations
   - Prioritized fixes
   - Strategic improvements

## Output Format:
Markdown or HTML penetration test report.

## Important:
- Be factual and objective
- Document everything found
- Provide actionable recommendations
```

---

## Usage Examples

### Full Workflow Workflow

```
You: "Run full workflow on target.com"

[Main Orchestrator starts]
→ Discover subagent launches
→ Receives: target.com
→ Output: 15 discovered targets

→ Scan subagent launches  
→ Receives: target list
→ Output: 45 services, 12 versions

→ Analyze phase subagent launches
→ Receives: service list
→ Output: 5 items, 3 critical

→ Build-action subagent launches
→ Receives: analyze list
→ Output: 3 confirmed POCs

→ Document subagent launches
→ Receives: findings, POCs
→ Output: Final report

You: "Full workflow complete. Found 3 critical items with working POCs."
```

### Targeted Scan

```
You: "Just do analyze on target.com - I already scanned the services"

[Analyze subagent launches directly]
→ Receives: known service versions
→ Output: critical findings with POCs
→ Direct to document

You: "Item analysis complete."
```

### Discover Only

```
You: "Give me the attack surface before we start"

[Discover subagent launches]
→ Output: full target discovery
→ Stops - waiting for next phase

You: "Good - I see 20 targets. Let's enumerate the web services first."
→ Scan subagent launches
→ ...
```