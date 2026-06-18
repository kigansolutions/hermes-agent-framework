# PromptOrchestrator Workflows

Automated penetration testing workflows with subagent handoff.

## Workflow Structure

```
┌─────────────────┐     ┌─────────────────┐
│    RECON        │────>│   ENUMERATION   │────>│   VULN ANALYSIS   │────>│   EXPLOITATION   │────>│   POST-EXPLOIT   │────>│ ATTACK CHAIN │────>│   REPORTING   │
│ (Discovery)    │     │   (Services)    │     │   (Findings)     │     │   (Pwnage)       │     │  (Pivoting)     │     │ (Multistage)  │     │   (Docs)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
         │                     │                     │                     │                     │                     │                     │
         v                     v                     v                     v                     v                     v                     v
     Target List           Service Map          Vulnerabilities         Proof of Concept      Session Access        Attack Path         Final Report
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
- Enumeration of web services
- SSL certificate analysis
```

---

## Phase 1: Reconnaissance

Passive and active discovery of targets.

### Tools Used
- `amass` - DNS enumeration
- `theHarvester` - Email/employee discovery
- `whois` - Domain registration info
- `subfinder` - Subdomain discovery
- `httpx` - HTTP probing

### Workflow Template

```markdown
# RECON WORKFLOW: [TARGET]

## Passive Recon
Run passive discovery first (no direct contact):

### WHOIS Lookup
whois [target.com]

### DNS Enumeration (Passive)
amass enum -passive -d [target.com]

### Email/OSINT Discovery
theHarvester -d [target.com] -b all

### Subdomain Discovery (Passive)
subfinder -d [target.com] -silent

## Active Recon
After passive phase completes:

### DNS Brute Force
amass enum -active -d [target.com]

### HTTP Probing
httpx -domains [target.com] -threads 50

### Screenshot Web Services
gowitness report [target.com]

## 🔄 HANDOFF TO ENUMERATION

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
2. Service enumeration on HTTP/HTTPS
3. SSL certificate analysis
```

### Subagent Prompt

```
You are aReconnaissance subagent. Your role is to discover targets through passive and active recon.

Input: [TARGET_DOMAIN or TARGET_IP]
Output: Handoff document for enumeration phase

## Tasks:
1. Passive recon (no direct packets to target)
   - WHOIS lookup
   - DNS enumeration (amass -passive)
   - Email discovery (theHarvester)
   
2. Active recon (direct contact allowed)
   - Subdomain enumeration (amass -active)
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

## Phase 2: Enumeration

Service detection and version identification.

### Tools Used
- `nmap` - Port scanning
- `nuclei` - vulnerabilty scanning
- `nikto` - Web vulnerability scanner
- `whatweb` - Technology identification
- `wappy` - Wappalyzer alternative

### Workflow Template

```markdown
# ENUMERATION WORKFLOW: [TARGET_LIST]

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
whatweb [http://target]
wappy [http://target]

### SSL/TLS Analysis
sslscan [target]:443
testssl [target]

## Application Analysis
Framework and CMS identification:

### WordPress
wpscan --url [target] --enumerate vp

### Drupal
droopescan scan drupal -u [target]

### Custom Applications
nikto -h [target]

## 🔄 HANDOFF TO VULN ANALYSIS

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
1. Prioritize web vulnerabilities (80/443)
2. Check for known CVEs on discovered versions
3. Test for auth bypass on login portals
```

### Subagent Prompt

```
You are an Enumeration subagent. Your role is to identify services, versions, and attack surface.

Input: Handoff from Recon phase (target list)
Output: Handoff document for vulnerability analysis

## Tasks:
1. Port scanning
   - TCP full scan (all ports)
   - UDP scan (common ports)
   - Service version detection

2. Service enumeration
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

## Phase 3: Vulnerability Analysis / Exploitation

Vulnerability identification and exploitation.

### Tools Used
- `nuclei` - Vulnerability scanning
- `sqlmap` - SQL injection
- `x8` - HTTP parameter pollution
- `commix` - Command injection
- `gitleaks` - Secret detection
- `nikto` - Web vulnerabilities

### Workflow Template

```markdown
# VULN ANALYSIS WORKFLOW: [TARGET_LIST]

## Vulnerability Scanning
Automated vulnerability detection:

### Nuclei Scan
nuclei -u [target] -severity critical,high,medium -silent

### nuclei-templates-update
nuclei -ut

### Web Vuln Scan
nikto -h [target]

### Secret Detection
gitleaks detect --source=/path/to/repo
trufflehog filesystem /path/to/dir

## Manual Testing
Manual vulnerability verification:

### SQL Injection
sqlmap -u [target] --batch --level 5

### Command Injection
commix --url [target]

### IDOR Testing
Manual parameter manipulation

### Auth Bypass Testing
Testing login mechanisms

## Exploitation
POC development and exploitation:

### Proof of Concept
[Document exploit steps]

### Privilege Escalation
[Document privesc path]

## 🔄 HANDOFF TO EXPLOITATION (or Reporting if no vulns)

### Vulnerabilities Found
| CVE/Issue | Severity | Impact | Exploitable |
|----------|----------|--------|-------------|
| CVE-2021-41773 | Critical | RCE | Yes |
| SQL Injection | Critical | Data exfil | Yes |
| IDOR | Medium | Account takeover | Yes |

### Proofs of Concept
[Document exploit evidence]

### Recommended Next Steps
1. Develop POCs for critical findings
2. Test privilege escalation
3. Document business impact
```

### Subagent Prompt

You are a Vulnerability Analysis subagent. Your role is to find and validate security vulnerabilities.

Input: Handoff from Enumeration phase (service list, versions)
Output: Vulnerability findings with POCs or handoff to reporting

## Tasks:

1. Automated scanning
   - Nuclei scan with critical/high templates
   - Known CVE checking
   - Secret detection

2. Manual testing
   - SQL injection testing
   - Command injection testing
   - IDOR verification

3. Exploitation
   - Develop working POCs
   - Document impact
   - Calculate risk scores

## Output Format:
Vulnerability table with severity, impact, exploitability status, and POCs.

## Important:
- Verify ALL findings with working exploits
- Calculate real business impact
- Flag any critical vulnerabilities immediately

---

## Phase 5: Post-Exploitation

Privilege escalation, lateral movement, persistence, and data exfiltration.

### Tools Used
- `linpeas` / `winpeas` - Privilege escalation scripts
- `pspy` - Process monitoring
- `mimikatz` - Credential harvesting
- `certify` / `certipy` - Active Directory cert exploitation
- `bloodhound` / `sharphound` - AD analysis
- `impacket` - SMB/kerberos tools
- `proxychains` - Pivoting
- `chisel` - SOCKS tunneling
- `socat` / `nc` - Reverse shells
- `metasploit` - Post-exploitation框架
- `sliver` - C2 framework

### Workflow Template

```markdown
# POST-EXPLOITATION WORKFLOW: [TARGET]

## Privilege Escalation

### Linux Escalation
linpeas.sh

Check for:
- SUID/SGID binaries
- Writable cron jobs
- Sudo misconfigurations
- Kernel exploits
- Container escapes

### Windows Escalation
winPEAS.exe

Check for:
- AlwaysInstallElevated
- Unquoted service paths
- Token manipulation
- DLL hijacking
- Service misconfigurations

## Lateral Movement

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
- DCSync attack
- ACL abuse
- Trust exploitation

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
- mimikatz
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

## 🔄 HANDOFF TO ATTACK CHAINING

### Access Gained
| System | Access Level | Method |
|--------|--------------|--------|
| webserver | root | CVE-2021-41773 |
| dc01 | domain admin | DCSync |
| fileserver | smb user | lateral movement |

### Credentials Obtained
- user:admin:P@ssw0rd123
- svc_backup:LsasDump

### Recommended Next Steps
1. Combine access paths for maximum impact
2. Chain vulnerabilities for persistence
3. Assess data access across pivots
```

### Subagent Prompt

```
You are a POST-EXPLOITATION subagent. Your role is to escalate privileges, move laterally, and establish persistence.

Input: Handoff from Exploitation phase (confirmed shell/code execution)
Output: Handoff for attack chaining with access/credentials

## Tasks:
1. Privilege Escalation
   - Linux: linpeas, pspy, sudo misconfigs
   - Windows: winPEAS, token manipulation

2. Lateral Movement
   - SSH/WinRM/SMB pivoting
   - Kerberos attacks
   - Active Directory exploitation

3. Persistence
   - Linux: cron, SSH keys, PAM
   - Windows: registry, tasks, services

4. Credential Harvesting
   - mimikatz, lsassy
   - Database credentials

## Output Format:
Access table with:
- Systems accessed
- Access level (user/root)
- Credentials obtained
- Persistence established
```

---

## Phase 6: Attack Chaining

Combining multiple attack paths for maximum impact.

### Concept

Attack chaining combines individual vulnerabilities into multi-stage attack paths:

```
Vulnerability 1     Vulnerability 2     Vulnerability 3
     │                    │                    │
     v                    v                    v
SQL Injection    ──>  File Write    ──>    RCE
(user:webapp)        (webroot)            (www-data)
     │                    │                    │
     └──────────┬────────┘                   │
                v                             v
          Priv Esc                   Domain Admin
          (sudo)                     (via DCSync)
```

### Attack Paths

| Chain ID | Path | Impact | Difficulty |
|---------|------|--------|------------|
| CH01 | SQLi → File Write → RCE → Root | Full compromise | Medium |
| CH02 | XSS → Session Hijack → Admin → RCE | Account takeover | Medium |
| CH03 | IDOR → Data Theft → Priv Escalation | Data breach | Easy |
| CH04 | Phishing → VPN → Internal → AD | Domain admin | Hard |

### Workflow Template

```markdown
# ATTACK CHAINING WORKFLOW: [ACCESS_LIST]

## Map Available Access

### From Initial Compromise
| System | User | Path to Root |
|--------|------|--------------|
| web01 | www-data | (sudo) linpeas |

### From Lateral Movement
| System | User | Domain |
|--------|------|--------|
| dc01 | enterprise admin | CORP.LOCAL |

### Credentials
| Username | Password | Type | Used |
|----------|----------|------|------|
| admin | P@ssw0rd | Plaintext | Yes |
| svc_backup | GPMC2024! | Plaintext | No |

## Identify Attack Chains

### Chain 01: Web → Domain Admin
Path:
1. SQLi gives webapp user (DONE)
2. File write via INTO OUTFILE (DONE)
3. RCE via webshell (DONE)
4. linpeas finds sudo (IN PROGRESS)
5. Domain admin via DCSync (NEXT)

Impact: Full domain takeover
Risk: Critical

### Chain 02: User → Root
Path:
1. XSS steals admin session (DONE)
2. Admin panel access (DONE)
3. Upload RCE (NEXT)

Impact: Server compromise
Risk: High

## Execute Chains

### Chain 01 Execution
[Document each step with evidence]

### Chain 02 Execution
[Document each step with evidence]

## 🔄 HANDOFF TO REPORTING

### Chains Executed
| Chain | Impact | Systems | Status |
|-------|--------|---------|--------|
| CH01 | Domain Admin | 3 | SUCCESS |
| CH02 | Server RCE | 1 | PARTIAL |

### Business Impact
- Data exfiltrated: 10K records
- Systems compromised: 5
- Domain ownership: Achieved

### Recommended Next Steps
1. Document attack path in report
2. Recommend defensive controls
3. Prioritize remediation
```

### Subagent Prompt

```
You are an ATTACK CHAINING subagent. Your role is to combine individual vulnerabilities into multi-stage attack paths.

Input: Handoff from Post-Exploitation phase (access/credentials)
Output: Handoff for reporting with combined chains

## Tasks:
1. Map attack paths
   - Connect available access points
   - Identify paths to high-value targets
   - Calculate chain probability

2. Execute chains
   - Prioritize by impact
   - Chain vulnerabilities sequentially
   - Document each step

3. Assess impact
   - Business impact of combined access
   - Data access potential
   - Persistence capability

## Output Format:
Attack chain table with:
- Chain ID and description
- Steps in sequence
- Success/failure status
- Overall impact rating
```

---

## Phase 7: Reporting

Documentation and reporting.

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
1. Reconnaissance
2. Enumeration
3. Vulnerability Analysis
4. Exploitation
5. Post-Exploitation
6. Attack Chaining
7. Reporting
```

## Findings Summary

| ID | Vulnerability | Severity | Status |
|----|---------------|----------|--------|
| 01 | CVE-2021-41773 | Critical | Fixed |
| 02 | SQL Injection | Critical | Fixed |
| 03 | IDOR | Medium | Fixed |

## Detailed Findings

### Finding 01: CVE-2021-41773 (Apache RCE)
**Severity**: Critical
**CVSS**: 9.8
**Description**: [Description]
**Impact**: [Business impact]
**Proof of Concept**:
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
**Proof of Concept**:
```bash
sqlmap -u "http://target/login" --data "user=admin&pass=*"
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
You are a Reporting subagent. Your role is to document findings and create professional reports.

Input: Handoff from Exploitation phase (findings, POCs)
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

### Full Pentest Workflow

```
You: "Run full pentest on target.com"

[Main Orchestrator starts]
→ Recon subagent launches
→ Receives: target.com
→ Output: 15 discovered targets

→ Enumeration subagent launches  
→ Receives: target list
→ Output: 45 services, 12 versions

→ Vulnerability Analysis subagent launches
→ Receives: service list
→ Output: 5 vulnerabilities, 3 critical

→ Exploitation subagent launches
→ Receives: vuln list
→ Output: 3 confirmed POCs

→ Reporting subagent launches
→ Receives: findings, POCs
→ Output: Final report

You: "Full pentest complete. Found 3 critical vulnerabilities with working POCs."
```

### Targeted Scan

```
You: "Just do vuln analysis on target.com - I already enumerated the services"

[Vuln Analysis subagent launches directly]
→ Receives: known service versions
→ Output: critical findings with POCs
→ Direct to reporting

You: "Vulnerability analysis complete."
```

### Recon Only

```
You: "Give me the attack surface before we start"

[Recon subagent launches]
→ Output: full target discovery
→ Stops - waiting for next phase

You: "Good - I see 20 targets. Let's enumerate the web services first."
→ Enumeration subagent launches
→ ...
```