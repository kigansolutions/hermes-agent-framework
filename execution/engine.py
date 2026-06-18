#!/usr/bin/env python3
"""
prompt-orchestrator — Execution Engine
========================================
Multi-phase workflow orchestration with parallel tool execution,
state persistence, and event callbacks. Drives a generic phase
tree (discover → scan → analyze → build → integrate → document)
against any subject — assessment targets, data pipelines, research
corpora, integration tasks, or anything else.

Domain-agnostic by design. The engine doesn't know what the tools
do — it just runs them, captures results, and persists state.

Phase vocabulary (legacy phase names are kept as aliases so older
configs keep working):
    discover     ← was: recon
    scan         ← was: enumeration
    analyze      ← was: vuln_analysis
    build        ← was: exploitation
    integrate    ← was: post_exploitation
    orchestrate  ← was: attack_chaining
    document     ← was: reporting
"""

import asyncio
import json
import os
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

# Import knowledge base
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from knowledge.knowledge import KnowledgeBase


# Phase enum — generic names. Legacy phase name aliases are kept as
# equal-value members so older configs (and older knowledge rows) keep
# working. The orchestrator layer translates new → legacy as needed.
class Phase(Enum):
    DISCOVER = "1"
    SCAN = "2"
    ANALYZE = "3"
    BUILD = "4"
    INTEGRATE = "5"
    ORCHESTRATE = "6"
    DOCUMENT = "7"
    # Legacy aliases (deprecated)
    RECON = "1"
    ENUMERATION = "2"
    VULN_ANALYSIS = "3"
    EXPLOITATION = "4"
    POST_EXPLOITATION = "5"
    ATTACK_CHAINING = "6"
    REPORTING = "7"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Finding:
    title: str
    severity: str
    description: str = None
    poc: str = None
    ref_id: str = None       # was: cve
    affected: str = None
    remediation: str = None
    phase: str = None
    verified: bool = False


@dataclass
class Service:
    host: str
    port: int
    service: str
    version: str = None
    state: str = "open"
    product: str = None


@dataclass
class Subject:
    name: str
    scope: list = field(default_factory=list)
    phase: str = "discover"
    findings: list = field(default_factory=list)
    services: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)
    notes: str = None


# Back-compat alias — older callers reference Target.
Target = Subject


class ExecutionEngine:
    def __init__(self, knowledge_base: KnowledgeBase = None, workspace: str = None):
        self.kb = knowledge_base or KnowledgeBase()
        self.workspace = workspace or os.path.expanduser("~/.prompt_orchestrator/workspace")
        os.makedirs(self.workspace, exist_ok=True)
        
        # Active pentests
        self.active_pentests = {}
        
        # Tool results cache
        self.results_cache = {}
        
        # Callbacks for events
        self.on_finding = None
        self.on_phase_complete = None
    
    def run_command(self, command: str, timeout: int = 300, 
                  working_dir: str = None) -> dict:
        """Run a shell command and return results"""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir
            )
            
            elapsed = time.time() - start_time
            
            return {
                "success": True,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "elapsed": elapsed,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout",
                "timeout": timeout,
                "command": command
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def run_parallel(self, commands: list, max_workers: int = 5) -> list:
        """Run multiple commands in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_cmd = {
                executor.submit(self.run_command, cmd): cmd 
                for cmd in commands
            }
            
            for future in as_completed(future_to_cmd):
                cmd = future_to_cmd[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = {"success": False, "error": str(e), "command": cmd}
                
                results.append(result)
        
        return results
    
    # ========================================
    # DISCOVER PHASE
    # ========================================
    def recon(self, target: str, passive_only: bool = False) -> dict:
        """Run discovery phase (legacy name; use discover() in new code)."""
        results = {
            "phase": "discover",
            "target": target,
            "passive_only": passive_only,
            "findings": [],
            "targets": [],
            "services": []
        }

        commands = []

        # Passive discovery
        commands.append(f"whois {target}")
        commands.append(f"dig +short {target} ANY")

        if not passive_only:
            # Active discovery
            commands.append(f"dig +short {target} A")
            commands.append(f"host -t MX {target}")

        # Execute in parallel
        print(f"[DISCOVER] Running {len(commands)} commands...")
        results["raw"] = self.run_parallel(commands)

        # Parse results
        # (In real implementation, parse JSON/grep output)

        # Save to knowledge base
        target_obj = self.kb.get_target(target)
        if not target_obj:
            target_id = self.kb.add_target(target, scope=None)
        else:
            target_id = target_obj["id"]

        self.kb.save_state(target_id, "discover", results)

        return results

    # ========================================
    # SCAN PHASE
    # ========================================
    def enumerate(self, target: str, hosts: list = None) -> dict:
        """Run scan phase (legacy name; use scan() in new code)."""
        results = {
            "phase": "scan",
            "target": target,
            "services": [],
            "versions": []
        }

        if not hosts:
            hosts = [target]

        commands = []

        for host in hosts:
            # Port + service scan
            commands.append(f"curl -sI http://{host}")
            commands.append(f"check_port {host} 443")

        # Execute
        print(f"[SCAN] Running {len(commands)} scans...")
        results["raw"] = self.run_parallel(commands)

        # Parse output
        for host in hosts:
            # Parse results (simplified)
            pass

        # Save
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "scan", results)

        return results

    # ========================================
    # ANALYZE PHASE
    # ========================================
    def vuln_scan(self, target: str, services: list = None,
                severity_filter: list = None) -> dict:
        """Run analyze phase (legacy name; use analyze() in new code)."""
        results = {
            "phase": "analyze",
            "target": target,
            "findings": []
        }

        if severity_filter is None:
            severity_filter = ["critical", "high", "medium"]

        commands = []

        # Reference lookup (primary)
        commands.append(f"curl -sS https://example.com/refs?subject={target} | jq '.'")

        # Banner grab + version compare
        commands.append(f"grab_banner {target} 443")

        if services:
            for svc in services:
                if svc.get("service") == "http" or svc.get("port") in [80, 443, 8080]:
                    commands.append(f"run_curl http://{target}:{svc.get('port')} -I")

        print(f"[ANALYZE] Running analysis commands...")
        results["raw"] = self.run_parallel(commands)

        # Parse output
        # (Parse and create Finding objects)

        # Save findings
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "analyze", results)

            for finding in results["findings"]:
                self.kb.add_finding(
                    target_obj["id"],
                    finding.get("type", "observation"),
                    finding.get("severity", "medium"),
                    finding.get("title"),
                    finding.get("description"),
                    finding.get("poc")
                )

        return results

    # ========================================
    # BUILD PHASE
    # ========================================
    def exploit(self, target: str, findings: list = None) -> dict:
        """Run build phase (legacy name; use build() in new code).

        In the original codebase this phase ran exploits against
        confirmed findings. In prompt-orchestrator it's repurposed
        to build artifacts / actions from analysis output — the
        same code path, neutral vocabulary.
        """
        results = {
            "phase": "build",
            "target": target,
            "built": [],
            "artifacts": []
        }

        if not findings:
            return results

        commands = []

        for finding in findings:
            if finding.get("severity") == "critical" and finding.get("poc"):
                # Run action / build script
                commands.append(finding["poc"])

        print(f"[BUILD] Running {len(commands)} build steps...")
        results["raw"] = self.run_parallel(commands)

        # Update knowledge base
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "build", results)

        return results

    # ========================================
    # INTEGRATE PHASE
    # ========================================
    def post_exploit(self, target: str, shells: list = None) -> dict:
        """Run integrate phase (legacy name; use integrate() in new code)."""
        results = {
            "phase": "integrate",
            "target": target,
            "artifacts": [],
            "outputs": [],
            "integrations": []
        }

        if not shells:
            return results

        commands = []

        for shell in shells:
            # Process outputs downstream
            if shell.get("kind") == "data":
                commands.append(f"curl -sS -X POST -d @- https://example.com/ingest < {target}_out.json")
            else:
                commands.append(f"echo 'integrate step for {target}' >> {target}_integrated.log")

        print(f"[INTEGRATE] Running integration steps...")
        results["raw"] = self.run_parallel(commands)

        # Save results
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "integrate", results)

        return results

    # ========================================
    # ORCHESTRATE PHASES (multi-stage chaining)
    # ========================================
    def chain_attacks(self, target: str, access_list: list = None) -> dict:
        """Orchestrate multi-stage workflows (legacy name; use orchestrate_phases() in new code)."""
        results = {
            "phase": "orchestrate",
            "target": target,
            "chains": [],
            "outcomes": {}
        }

        if not access_list:
            # Load from KB
            target_obj = self.kb.get_target(target)
            if target_obj:
                state = self.kb.load_state(target_obj["id"])
                if state:
                    access_list = state.get("data", {}).get("access", [])

        if not access_list:
            return results

        # Define multi-stage workflows
        chains = [
            {
                "id": "CH01",
                "name": "Analyze to document",
                "path": ["discover", "analyze", "build"],
                "outcome": "report"
            },
            {
                "id": "CH02",
                "name": "Ingest to summarize",
                "path": ["scan", "integrate"],
                "outcome": "summary"
            }
        ]

        # Execute chains
        for chain in chains:
            print(f"[ORCHESTRATE] Executing {chain['id']}: {chain['name']}")
            # (In real implementation, step through chain)
            results["chains"].append({
                "id": chain["id"],
                "status": "executed",
                "outcome": chain["outcome"]
            })

        # Save
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "orchestrate", results)

        return results

    # ========================================
    # DOCUMENT PHASE
    # ========================================
    def generate_report(self, target: str, format: str = "markdown") -> str:
        """Generate workflow report."""
        target_obj = self.kb.get_target(target)
        if not target_obj:
            return f"Subject {target} not found"

        findings = self.kb.get_findings(target_obj["id"])
        services = self.kb.get_services(target_obj["id"])
        state = self.kb.load_state(target_obj["id"])

        # Generate markdown
        report = f"""# Workflow Report: {target}

## Executive Summary
"""

        critical = sum(1 for f in findings if f[3] == "critical")
        high = sum(1 for f in findings if f[3] == "high")

        report += f"""
This workflow identified {critical + high} critical and high-severity items.

## Scope
- Subject: {target}
- Observed: {len(services)} services

## Findings Summary
| Severity | Count |
|----------|-------|
| Critical | {critical} |
| High | {high} |
| Medium | {sum(1 for f in findings if f[3] == 'medium')} |

"""

        # Findings detail
        report += "## Detailed Findings\n\n"

        for f in findings:
            report += f"""### {f[4]}
**Severity**: {f[3]}
**Description**: {f[5] or 'N/A'}
**Reference**: {f[6] or 'N/A'}

"""

        report += f"""
## Methodology
1. Discover
2. Scan
3. Analyze
4. Build
5. Integrate
6. Orchestrate
7. Document

## Recommendations
1. Address critical items first
2. Validate inputs at trust boundaries
3. Enable observability and alerting
4. Repeat the workflow on a recurring schedule
"""

        # Save report
        report_path = os.path.join(self.workspace, f"{target}_{datetime.now().strftime('%Y%m%d')}.md")
        with open(report_path, "w") as f:
            f.write(report)

        return report_path

    # ========================================
    # FULL WORKFLOW
    # ========================================
    def run_full_pentest(self, target: str, phases: list = None) -> dict:
        """Run complete workflow (legacy name; use run_full_workflow() in new code)."""
        if phases is None:
            phases = ["recon", "enum", "vuln", "exploit", "post", "chain", "report"]

        results = {
            "target": target,
            "phases": {},
            "completed": []
        }

        print(f"[WORKFLOW] Starting full workflow on {target}")

        for phase in phases:
            try:
                if phase == "recon":
                    print(f"[PHASE] Discover...")
                    results["phases"]["recon"] = self.recon(target)
                    results["completed"].append("recon")

                elif phase == "enum":
                    print(f"[PHASE] Scan...")
                    results["phases"]["enum"] = self.enumerate(target)
                    results["completed"].append("enum")

                elif phase == "vuln":
                    print(f"[PHASE] Analyze...")
                    results["phases"]["vuln"] = self.vuln_scan(target)
                    results["completed"].append("vuln")

                elif phase == "exploit":
                    print(f"[PHASE] Build...")
                    findings = results["phases"].get("vuln", {}).get("findings", [])
                    results["phases"]["exploit"] = self.exploit(target, findings)
                    results["completed"].append("exploit")

                elif phase == "post":
                    print(f"[PHASE] Integrate...")
                    shells = results["phases"].get("exploit", {}).get("artifacts", [])
                    results["phases"]["post"] = self.post_exploit(target, shells)
                    results["completed"].append("post")

                elif phase == "chain":
                    print(f"[PHASE] Orchestrate...")
                    access_list = results["phases"].get("post", {}).get("artifacts", [])
                    results["phases"]["chain"] = self.chain_attacks(target, access_list)
                    results["completed"].append("chain")

                elif phase == "report":
                    print(f"[PHASE] Document...")
                    report_path = self.generate_report(target)
                    results["phases"]["report"] = {"path": report_path}
                    results["completed"].append("report")

            except Exception as e:
                print(f"[ERROR] Phase {phase} failed: {e}")
                results["phases"][phase] = {"error": str(e)}

        print(f"[WORKFLOW] Complete! {len(results['completed'])}/{len(phases)} phases completed")

        return results

    # ========================================
    # RESUME / STATE MANAGEMENT
    # ========================================
    def get_state(self, target: str) -> Optional[dict]:
        """Get current workflow state."""
        target_obj = self.kb.get_target(target)
        if not target_obj:
            return None
        return self.kb.load_state(target_obj["id"])

    def resume(self, target: str) -> dict:
        """Resume workflow from saved state."""
        state = self.get_state(target)
        if not state:
            return {"error": "No saved state found"}

        current_phase = state.get("phase", "discover")

        # Determine next phase
        phase_order = ["discover", "scan", "analyze", "build",
                    "integrate", "orchestrate", "document"]

        try:
            current_idx = phase_order.index(current_phase)
            next_phases = phase_order[current_idx + 1:]
        except ValueError:
            next_phases = phase_order

        # Continue
        return self.run_full_pentest(target, next_phases)

    def stop(self, target: str):
        """Stop workflow and save state."""
        target_obj = self.kb.get_target(target)
        if target_obj:
            print(f"[STATE] Saved state for {target}")
            return {"saved": True}
        return {"saved": False}

    # ─── Generic vocabulary aliases (prompt-orchestrator rebrand) ──
    # These expose the same logic under the new phase names. The
    # original method names are kept as thin wrappers for backwards
    # compatibility with older configs.

    def run_full_workflow(self, subject: str, phases: list = None) -> dict:
        """Run the full workflow. Preferred entry point."""
        return self.run_full_pentest(subject, phases)

    def discover(self, subject: str) -> dict:
        return self.recon(subject)

    def analyze(self, subject: str, services: list = None) -> dict:
        return self.vuln_scan(subject, services)

    def build(self, subject: str, findings: list = None) -> dict:
        return self.exploit(subject, findings)

    def integrate(self, subject: str, artifacts: list = None) -> dict:
        return self.post_exploit(subject, artifacts)

    def orchestrate_phases(self, subject: str) -> dict:
        return self.chain_attacks(subject)


# CLI interface
def main():
    import sys
    
    if len(sys.argv) < 2:
        print("prompt-orchestrator — Execution Engine")
        print("Usage: python -m execution <command> [args]")
        return

    engine = ExecutionEngine()
    cmd = sys.argv[1]

    # Legacy phase names mapped to current methods.
    cmd_map = {
        "recon": engine.recon,
        "discover": engine.discover,
        "enum": engine.enumerate,
        "scan": engine.enumerate,
        "vuln": engine.vuln_scan,
        "analyze": engine.vuln_scan,
        "exploit": engine.exploit,
        "build": engine.exploit,
        "post": engine.post_exploit,
        "integrate": engine.post_exploit,
        "chain": engine.chain_attacks,
        "orchestrate": engine.chain_attacks,
    }

    if cmd in cmd_map:
        target = sys.argv[2] if len(sys.argv) > 2 else "localhost"
        print(cmd_map[cmd](target))

    elif cmd in ("pentest", "workflow"):
        if len(sys.argv) < 3:
            print("Usage: execution workflow <subject>")
            return
        result = engine.run_full_pentest(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "resume":
        if len(sys.argv) < 3:
            print("Usage: execution resume <subject>")
            return
        result = engine.resume(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "report":
        if len(sys.argv) < 3:
            print("Usage: execution report <subject>")
            return
        path = engine.generate_report(sys.argv[2])
        print(f"Report: {path}")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()