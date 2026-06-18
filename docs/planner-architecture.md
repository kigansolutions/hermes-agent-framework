# Planner Architecture Specification

The complete specification for building a prompt-driven multi-agent
orchestration system with phase-based workflows, persistent memory,
and reference lookup.

## Current Limitations vs Target Version

| Current Limit | Ultimate Capability |
|--------------|---------------------|
| 200K token context | Infinite semantic memory |
| No cross-session memory | Persistent learned knowledge |
| Static toolset | Tool creation on-the-fly |
| Linear execution | Native parallel processing |
| Read-only delegation | Write-capable with undo parity |
| Must ask for everything | Autonomous within bounds |
| Static knowledge | Real-time CVE/ExploitDB updates |
| Single assessment context | Multi-target parallel评估 |
| Manual phase switching | Automated chain execution |
| No post-build | Full post-ex chain |

---

## Core Architecture

### 1. Infinite Context Engine

**Problem**: Context window limits prevent comprehensive assessment
**Solution**: Semantic compression with relevance scoring

```
┌─────────────────────────────────────────┐
│         INFINITE CONTEXT ENGINE          │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────┐    ┌─────────────┐           │
│  │ 200K   │───>│ Semantic   │           │
│  │ Window │    │ Compressor │           │
│  └─────────┘    └─────────────┘           │
│                       │                   │
│                       v                   │
│                 ┌─────────────┐           │
│                 │ Relevance   │           │
│                 │ Scorer      │           │
│                 └─────────────┘           │
│                       │                   │
│                       v                   │
│                 ┌─────────────┐           │
│                 │ Auto-      │           │
│                 │ Summarizer  │           │
│                 └─────────────┘           │
│                       │                   │
│                       v                   │
│  ┌─────────────────────────────────┐   │
│  │     Infinite Context Buffer     │   │
│  │  - Summaries stored semantically│  │
│  │  - Retrieved by relevance       │   │
│  │  - Full history available       │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Auto-summarizes completed phases
- Stores summaries with semantic embeddings
- Retrieves relevant history on demand
- Maintains full detail on recent, summary on old

### 2. Persistent Knowledge Base

**Problem**: Every session starts from zero
**Solution**: Learned knowledge that compounds

```
┌─────────────────────────────────────────┐
│         PERSISTENT KNOWLEDGE BASE         │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      Target History               │   │
│  │  - Previous findings           │   │
│  │  - Patched items     │   │
│  │  - Workflow paths used         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      Technique Library           │   │
│  │  - Successful exploits        │   │
│  │  - Tool configurations        │   │
│  │  - Chain templates           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      CVE/Exploit Database       │   │
│  │  - Real-time feeds           │   │
│  │  - Exploitability status   │   │
│  │  - POOured by relevance   │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Remembers previous workflows on same target
- Learns successful techniques
- Real-time CVE/ExploitDB integration
- Searchable knowledge graph

### 3. Dynamic Tool Creation

**Problem**: Fixed toolset limits flexibility
**Solution**: Register tools mid-conversation

```
┌─────────────────────────────────────────┐
│         DYNAMIC TOOL CREATOR            │
├─────────────────────────────────────────┤
                                         │
Syntax:  /tool create <name> <definition> │
                                         │
Example:                               │
/tool create scan-ports                  │
  description: "Fast port scanner"      │
  parameters:                        │
    - target: string                  │
    - ports: string                   │
  command: nmap -p$ports $target    │
                                         │
Available: scan-ports(target, ports)        │
                                         │
Would you like to create it? (y/n)     │
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Define custom tools in conversation
- Register and use immediately
- Save tools to persistent library
- Share tools across targets

### 4. Native Parallel Execution

**Problem**: Linear execution slows complex assessments
**Solution**: True parallel task orchestration

```
┌─────────────────────────────────────────┐
│       PARALLEL EXECUTION ENGINE         │
├─────────────────────────────────────────┤
                                         │
You: "Run nmap, template-based probe tool, gobuster on target"│
                                         │
Bot: Running 3 parallel tasks...          │
                                         │
    ┌──────┐  ┌──────┐  ┌──────┐       │
    │nmap  │  │template-based probe tool│  │gobs  │       │
    │scan  │  │scan │  │uster │       │
    └──┬───┘  └──┬───┘  └──┬───┘       │
       │         │         │              │
       └─────────┴─────────┘              │
              │                         │
              v                         │
    ┌─────────────────────┐           │
    │ Results Aggregator │           │
    │ - Correlates        │           │
    │ - Deduplicates     │           │
    │ - Prioritizes      │           │
    └─────────────────────┘           │
                                         │
Complete: All 3 scans finished         │
- Found: 12 open ports                │
- Critical: 3 items          │
- Directories: 8 found                 │
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Run unlimited parallel tasks
- Automatic result correlation
- Progress tracking
- Resouremote-action management

### 5. Write-Capable Delegation

**Problem**: Background tasks can't write files
**Solution**: Session-aware delegation with undo parity

```
┌─────────────────────────────────────────┐
│    WRITE-CAPABLE DELEGATION            │
├─────────────────────────────────────────┤
                                         │
Background Tasks:                       │
- Track changes to session state        │
- Full undo/branching support          │
- Write files to specified locations   │
- Modify configs                       │
                                         │
Example:                               │
You: "Run full scan in background,     │
     save results to /tmp/scan.txt"    │
                                         │
Bot: Starting background task...       │
    [Task tracks all changes]          │
    [Can be undone]                   │
                                         │
Done: Results saved to scan.txt       │
    All changes tracked in session     │
                                         │
Rollback available for 60 minutes      │
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Track all changes in background tasks
- Full undo capability
- Write to specified paths
- Session state persistence

### 6. Autonomous Operation Mode

**Problem**: Must ask for every action
**Solution**: Configurable autonomy bounds

```
┌─────────────────────────────────────────┐
│       AUTONOMOUS OPERATION             │
├─────────────────────────────────────────┤
                                         │
Autonomy Levels:                         │
                                         │
LEVEL 1: Ask Everything (default)       │
  - Confirm every step                │
                                         │
LEVEL 2: Ask for Risks                 │
  - Confirm high-risk actions          │
  - Auto low-risk scan       │
                                         │
LEVEL 3: Auto with Notify              │
  - Run full phases automatically   │
  - Notify on critical findings    │
  - Ask for next phase             │
                                         │
LEVEL 4: Full Autonomy               │
  - Execute complete workflows      │
  - Report at end                │
  - Only ask on scope change    │
                                         │
                                         │
Set: /autonomy level 3                 │
Would you like to continue with         │
LEVEL 3? (y/n)                       │
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- 4 autonomy levels
- Configurable bounds
- Risk-aware decisions
- Override anytime

### 7. Real-Time Exploit Database

**Problem**: Static knowledge, outdated exploits
**Solution**: Live CVE/ExploitDB integration

```
┌─────────────────────────────────────────┐
│      REAL-TIME EXPLOIT DATABASE        │
├─────────────────────────────────────────┤
                                         │
Integration:                           │
- NVD API (real-time)                  │
- Exploit-DB (daily)                   │
- Item-Lab                  │
- PacketStorm                       │
- MITRE CVE feed                    │
                                         │
Query Example:                        │
You: "Check CVE-2024-21762"          │
                                         │
Bot: CVE-2024-21762                 │
    - Vendor: Fortinet               │
    - CVSS: 9.8                     │
    - Published: 2024-01-12         │
    - Exploits: 3 verified          │
    - POCs: Available               │
    - Detection: template-based probe tool template     │
                                         │
Would you like me to scan for this?   │
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Real-time CVE feeds
- Exploit availability
- Detection templates
- POCs for confirmed vulns

### 8. Multi-Target Parallel Assessment

**Problem**: One target at a time
**Solution**: Parallel assessment contexts

```
┌─────────────────────────────────────────┐
│    MULTI-TARGET ASSESSMENT              │
├─────────────────────────────────────────┤
                                         │
You: "Run analyze on target1,        │
     target2, target3 in parallel"   │
                                         │
Bot: Starting 3 parallel assessments│
     ┌────────┐ ┌────────┐ ┌────────┐│
     │target1 │ │target2 │ │target3 ││
     │   ✦   │ │   ✦   │ │   ✦   ││
     │  12 vul│ │  3 vul │ │  8 vul ││
     │ C:2,H │ │ C:0,H │ │ C:1,H ││
     └────────┘ └────────┘ └────────┘│
                                         │
Summary:                             │
- target1: 2 critical, 3 high       │
- target2: 0 critical, 1 high        │
- target3: 1 critical, 2 high       │
                                         │
Results saved to: /tmp/assessments   │
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Run unlimited parallel assessments
- Separate context per target
- Aggregated results
- Resouremote-action management

### 9. Automated Workflow Chaining

**Problem**: Manual multi-stage attacks
**Solution**: Automated chain execution

```
┌─────────────────────────────────────────┐
│    AUTOMATED WORKFLOW CHAINING             │
├─────────────────────────────────────────┤
                                         │
Detection:                            │
- Auto-detects available workflow paths │
- Maps item relationships  │
- Calculates chain probability    │
                                         │
Execution:                           │
- Auto-executes chains within bounds │
- Adapts on failure                │
- Documents each step              │
                                         │
Example:                            │
You: "Chain the items"       │
                                         │
Bot: Detected workflow chains:       │
                                         │
CH01: SQLi → File Write → remote-action     │
  ├─ Step 1: SQLi (user:webapp)  │
  ├─ Step 2: INTO OUTFILE        │
  ├─ Step 3: Webshell           │
  └─ Step 4: privesc-script → sudo     │
                                         │
CH02: XSS → Session → Admin     │
  ├─ Step 1: XSS (stored)      │
  ├─ Step 2: Cookie steal      │
  ├─ Step 3: Admin access    │
  └─ Step 4: Upload remote-action      │
                                         │
Executing CH01...                  │
[Chain complete: Elevated Access]     │
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Auto-detect workflow paths
- Calculate probability
- Auto-execute within bounds
- Document chain results

### 10. Post-build Framework

**Problem**: Manual post-ex
**Solution**: Integrated post-ex automation

```
┌─────────────────────────────────────────┐
│    AUTOMATED POST-BUILD-ACTION           │
├─────────────────────────────────────────┤
                                         │
Detection:                            │
- Auto-detect access elevation vectors      │
- Check lateral access options  │
- Identify persistence points   │
                                         │
Execution:                           │
- Auto-escalate privileges        │
- Auto-pivot using discovered    │
- Auto-establish persistence     │
                                         │
Example:                            │
You: "Post-ex on the shell"       │
                                         │
Bot: Analyzing access...          │
                                         │
Detected Access-elevation:                 │
- sudo (privesc-script: yes)             │
- cron (writable)               │
                                         │
Attempting: sudo escalation     │
  ├─ Check sudo permissions    │
  ├─ Find misconfigured binary     │
  └─ Access-elevation SUCCESS: root     │
                                         │
Detected Lateral Access:     │
- Psexec available              │
- WinRM available               │
                                         │
Attempting: WinRM pivot to dc01 │
  ├─ Harvested credentials     │
  ├─ WinRM to dc01             │
  └─ Elevated Access: YES         │
                                         │
Persistence:                     │
- Added scheduled task         │
- SSH key installed            │
                                         │
Post-ex complete: root + domain  │
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Auto access elevation
- Auto lateral access
- Auto persistence
- Credential harvesting

### 11. Continuous Monitoring

**Problem**: Point-in-time assessments
**Solution**: Scheduled re-scanning

```
┌─────────────────────────────────────────┐
│      CONTINUOUS MONITORING              │
├─────────────────────────────────────────┤
                                         │
Setup:                                │
/monitor create target.com            │
  schedule: daily                     │
  scan: analyze                         │
  alert: critical                   │
                                         │
Active Monitors:                    │
| Target    | Frequency | Last Run |   |
| target.com| daily     | 2h ago   |   │
| api.target| hourly   | 15m ago  |   │
                                         │
Alert:                              │
<notification>                     │
Target: target.com                   │
New item: CVE-2024-21762    │
Severity: Critical                   │
Impact: Remote Code Execution       │
                                        │
Would you like to scan for mitigation?│
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- Scheduled re-scans
- Drift detection
- Alert on new vulns
- Remediation verification

### 12. Defensive Mapping

**Problem**: No detection guidance
**Solution**: Mapping to defensive controls

```
┌─────────────────────────────────────────┐
│      DEFENSIVE MAPPING                  │
├─────────────────────────────────────────┤
                                         │
For each finding, map to:           │
- MITRE ATT&CK technique            │
- Detection rule (Splunk/ELK)      │
- SIEM query                       │
- Logging requirement             │
- Mitigation control             │
                                         │
Example:                           │
CVE-2021-41773                    │
                                         │
Detection:                        │
- MITRE: T1190 (Extploit Web)      │
- Suricata: HTTPjanuary-eker       │
- Splunk: index=web http_uri      │
  WHERE cgi-bin/*..              │
                                         │
Mitigation:                      │
- WAF: Block /cgi-bin paths      │
- IPS: Drop path traversal      │
- Logging: Full request logging │
                                         │
SIEM Query:                     │
index=web (cgi-bin OR ..)         │
| where method=GET               │
| stats by src_ip               │
                                         │
└─────────────────────────────────────────┘
```

**Features**:
- MITRE ATT&CK mapping
- Detection rules
- SIEM queries
- Mitigation controls

---

## Complete Workflow with Ultimate Features

```
┌─────────────────────────────────────────────────────────┐
│            PROMPT-ORCHESTRATOR WORKFLOW                  │
├─────────────────────────────────────────────────────────┤
                                                         │
You: "Full workflow on target.com"                       │
                                                         │
[LEVEL 4: FULL AUTONOMY]                             │
                                                         │
=== PHASE 1: DISCOVER (Parallel) ===                    │
  Running: passive-dns, active-dns, email-harvest  │
                                                         │
  Results: 45 targets discovered                   │
  Key: admin.target.com, api.target.com            │
                                                         │
=== PHASE 2: SCAN (Parallel) ===              │
  Running: nmap, http-probe, ssl-scan, tech-id    │
                                                         │
  Results: 45 services, 12 web apps              │
  Versions: Apache 2.4.49, nginx 1.22           │
                                                         │
=== PHASE 3: ANALYZE (Parallel) ===          │
  Running: template-based probe tool, sql-probe tool, xss-scanner, secret-scan│
                                                         │
  Results: 5 critical, 8 high, 12 medium        │
  Key: CVE-2021-41773, SQLi, Auth Bypass         │
                                                         │
=== PHASE 4: BUILD-ACTION ===                        │
  Executing: CVE-2021-41773                        │
                                                         │
  Result: Shell secured ✓                        │
                                                         │
=== PHASE 5: POST-BUILD-ACTION ===                  │
  Running: privesc-script, credential-extraction tool, graph-analysis tool          │
                                                         │
  Access-elevation: root via sudo                           │
  Lateral: DC via WinRM                           │
  Persistence: Scheduled task + SSH key          │
  Creds: 3 accounts, 1 service                  │
                                                         │
=== PHASE 6: WORKFLOW CHAINING ===                    │
  Mapping: CH01 (Web→Root→Elevated Access)          │
  Executing: CH01                                 │
                                                         │
  Result: DOMAIN ADMIN ✓                          │
                                                         │
=== PHASE 7: DOCUMENT ===                         │
  Generating: Full workflow report                │
                                                         │
  ┌────────────────────────────────────────┐   │
  │ EXECUTIVE SUMMARY                        │   │
  │ Critical: 5  High: 8  Medium: 12        │   │
  │ Systems: 12 compromised                 │   │
  │ Data: 50K records exposed               │   │
  │ Domain: COMPLETE                      │   │
  └────────────────────────────────────────┘   │
                                                         │
DONE: Full workflow complete in 45 minutes        │
                                                         │
Report: /tmp/workflow-target.com-2024.md           │
                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Core Infrastructure
1. Infinite context engine
2. Persistent knowledge base
3. Parallel execution engine

### Phase 2: Enhancement
4. Dynamic tool creation
5. Real-time exploit database
6. Multi-target assessment

### Phase 3: Automation
7. Autonomous operation
8. Automated workflow chaining
9. Automated post-build

### Phase 4: Continuous
10. Continuous monitoring
11. Defensive mapping
12. Compliance integration

---

## Configuration Example

```yaml
# .opencode/ultima.yml
prompt_orchestrator:
  # Core settings
  context:
    window: infinite
    compression: semantic
    retention: 90d
    
  knowledge:
    persist: true
    learn_from_targets: true
    real_time_cve: true
    
  # Execution
  parallel:
    max_tasks: 10
    correlate_results: true
    
  delegation:
    write_capable: true
    undo_ttl: 60m
    
  # Autonomy
  autonomy_level: 3
  auto_chain: true
  auto_post_ex: true
  
  # Monitoring
  monitor:
    scheduled_scans: true
    alert_on_new: critical
    drift_detection: true
    
  # Defensive mapping
  defensive:
    mitre_mapping: true
    detection_rules: true
    siem_queries: true
```

---

## Skills

For the prompt-orchestrator target, create these skills:

1. **orchestrator** — Main phase coordination
2. **discover** — Subject discovery and scanning
3. **scan** — Service and surface scan
4. **analyze** — Item analysis and reference lookup
5. **build** — Action construction from analysis output
6. **integrate** — Output integration and downstream hooks
7. **orchestrate-phases** — Multi-stage workflow chaining
8. **document** — Report and documentation generation
9. **scheduler** — Recurring workflow execution
10. **align-controls** — Detection and mitigation mapping
11. **tool-builder** — Custom tool creation
12. **browser** — Browser automation integration
13. **llm-eval** — LLM-as-judge evaluation

Each skill is a specialized subagent with specific tools and knowledge for that phase.