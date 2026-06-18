"""
prompt-orchestrator — Tool Executor
====================================
Runs CLI tools and captures structured results. Pairs with the
memory layer to track which tools ran, when, and what they produced.

Domain-agnostic by design. The executor doesn't know what the tool
does — it just runs the command, captures stdout/stderr/duration, and
hands the result to the caller.
"""

import os
import json
import subprocess
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class ToolResult:
    tool: str
    command: str
    output: str
    exit_code: int
    duration: float
    timestamp: str

class ToolExecutor:
    """
    Executes external tools and captures structured results.
    Integrates with the memory layer for tracking and replay.
    """
    
    def __init__(self):
        self.history: List[ToolResult] = []
        
        # Tool definitions with descriptions and common commands
        self.tools = {
            # Reconnaissance
            'nmap': {
                'description': 'Port scanner and service detection',
                'category': 'reconnaissance',
                'install': 'apt install nmap',
                'example': 'nmap -sV -p- target.com'
            },
            'masscan': {
                'description': 'Fast port scanner',
                'category': 'reconnaissance', 
                'install': 'apt install masscan',
                'example': 'masscan -p1-65535 target.com --rate=10000'
            },
            'subfinder': {
                'description': 'Passive subdomain enumeration',
                'category': 'reconnaissance',
                'install': 'apt install subfinder',
                'example': 'subfinder -d target.com'
            },
            'amass': {
                'description': 'Subdomain enumeration',
                'category': 'reconnaissance',
                'install': 'apt install amass',
                'example': 'amass enum -d target.com'
            },
            'gobuster': {
                'description': 'Directory/DNS/VHost enumeration',
                'category': 'reconnaissance',
                'install': 'apt install gobuster',
                'example': 'gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt'
            },
            'ffuf': {
                'description': 'Fast web fuzzer',
                'category': 'reconnaissance',
                'install': 'apt install ffuf',
                'example': 'ffuf -u http://target.com/FUZZ -w wordlist.txt'
            },
            'whatweb': {
                'description': 'Web technology fingerprinting',
                'category': 'reconnaissance',
                'install': 'apt install whatweb',
                'example': 'whatweb target.com'
            },
            
            # Vulnerability Scanning
            'nikto': {
                'description': 'Web server vulnerability scanner',
                'category': 'vulnerability-scanning',
                'install': 'apt install nikto',
                'example': 'nikto -h target.com'
            },
            'nuclei': {
                'description': 'Template-based vulnerability scanner',
                'category': 'vulnerability-scanning',
                'install': 'apt install nuclei',
                'example': 'nuclei -u target.com -severity critical,high'
            },
            'wapiti': {
                'description': 'Black-box web vulnerability scanner',
                'category': 'vulnerability-scanning',
                'install': 'apt install wapiti',
                'example': 'wapiti -u target.com'
            },
            
            # Exploitation
            'sqlmap': {
                'description': 'SQL injection tool',
                'category': 'exploitation',
                'install': 'apt install sqlmap',
                'example': 'sqlmap -u "http://target.com/page.php?id=1"'
            },
            'xsstrike': {
                'description': 'XSS vulnerability scanner',
                'category': 'exploitation',
                'install': 'pip install xsstrike',
                'example': 'xsstrike -u target.com'
            },
            'hydra': {
                'description': 'Online password cracker',
                'category': 'exploitation',
                'install': 'apt install hydra',
                'example': 'hydra -L users.txt -P passwords.txt target.com ssh'
            },
            
            # API Testing
            'httpx': {
                'description': 'HTTP toolkit',
                'category': 'api-testing',
                'install': 'go install github.com/projectdiscovery/httpx@latest',
                'example': 'httpx -u target.com'
            },
            'httpie': {
                'description': 'CLI HTTP client',
                'category': 'api-testing',
                'install': 'pip install httpie',
                'example': 'http GET target.com/api/endpoint'
            },
            
            # Utilities
            'curl': {
                'description': 'HTTP client',
                'category': 'utility',
                'install': 'apt install curl',
                'example': 'curl -v target.com'
            },
            'wget': {
                'description': 'Download utility',
                'category': 'utility',
                'install': 'apt install wget',
                'example': 'wget -r target.com'
            }
        }
    
    def is_installed(self, tool: str) -> bool:
        """Check if a tool is installed"""
        try:
            result = subprocess.run(
                f'which {tool}',
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def get_tool_info(self, tool: str) -> Optional[Dict]:
        """Get information about a tool"""
        return self.tools.get(tool)
    
    def list_tools(self, category: str = None) -> List[Dict]:
        """List all available tools"""
        result = []
        for name, info in self.tools.items():
            if category is None or info['category'] == category:
                result.append({
                    'name': name,
                    'installed': self.is_installed(name),
                    **info
                })
        return result
    
    def execute(self, command: str, timeout: int = 300, 
                capture_output: bool = True) -> ToolResult:
        """Execute a command and return result"""
        
        start_time = datetime.now()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            tool_result = ToolResult(
                tool=command.split()[0] if command else 'unknown',
                command=command,
                output=result.stdout + result.stderr,
                exit_code=result.returncode,
                duration=duration,
                timestamp=datetime.now().isoformat()
            )
            
            self.history.append(tool_result)
            return tool_result
            
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                tool=command.split()[0] if command else 'unknown',
                command=command,
                output="Error: Command timed out",
                exit_code=-1,
                duration=duration,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                tool=command.split()[0] if command else 'unknown',
                command=command,
                output=f"Error: {str(e)}",
                exit_code=-1,
                duration=duration,
                timestamp=datetime.now().isoformat()
            )
    
    def get_history(self, tool: str = None, limit: int = 20) -> List[ToolResult]:
        """Get execution history"""
        if tool:
            return [r for r in self.history if r.tool == tool][-limit:]
        return self.history[-limit:]
    
    def parse_nmap_output(self, output: str) -> Dict:
        """Parse nmap grepable output"""
        results = {
            'hosts': [],
            'open_ports': [],
            'services': []
        }
        
        # Extract hosts
        for line in output.split('\n'):
            if 'Host:' in line and 'Ports:' in line:
                match = re.search(r'Host: ([\d.]+)', line)
                if match:
                    results['hosts'].append(match.group(1))
        
        return results
    
    def build_nmap_command(self, target: str, scan_type: str = 'basic',
                          ports: str = None, scripts: bool = False) -> str:
        """Build nmap command based on scan type"""
        
        base = 'nmap'
        
        if scan_type == 'basic':
            flags = '-sV -O'
        elif scan_type == 'stealth':
            flags = '-sS -T2 -f'
        elif scan_type == 'quick':
            flags = '-F'
        elif scan_type == 'full':
            flags = '-sV -sC -p- -A'
        elif scan_type == 'vuln':
            flags = '--script=vuln'
        else:
            flags = '-sV'
        
        if ports:
            flags += f' -p {ports}'
        
        return f'{base} {flags} {target}'
    
    def build_gobuster_command(self, target: str, mode: str = 'dir',
                              wordlist: str = None) -> str:
        """Build gobuster command"""
        
        if not wordlist:
            wordlist = '/usr/share/wordlists/dirb/common.txt'
        
        base = f'gobuster {mode} -u {target} -w {wordlist} -t 10'
        
        return base
    
    def build_nuclei_command(self, target: str, severity: str = 'medium,high,critical',
                            templates: str = None) -> str:
        """Build nuclei command"""
        
        base = f'nuclei -u {target} -severity {severity} -silent'
        
        if templates:
            base += f' -t {templates}'
        
        return base


# Create global instance
TOOL_EXECUTOR = ToolExecutor()


# Quick execution functions for the agent

def run_nmap(target: str, scan_type: str = 'basic') -> str:
    """Run nmap scan"""
    cmd = TOOL_EXECUTOR.build_nmap_command(target, scan_type)
    return TOOL_EXECUTOR.execute(cmd).output

def run_gobuster(target: str, wordlist: str = None) -> str:
    """Run gobuster directory scan"""
    cmd = TOOL_EXECUTOR.build_gobuster_command(target, wordlist=wordlist)
    return TOOL_EXECUTOR.execute(cmd).output

def run_nuclei(target: str, severity: str = 'high,critical') -> str:
    """Run nuclei vulnerability scan"""
    cmd = TOOL_EXECUTOR.build_nuclei_command(target, severity)
    return TOOL_EXECUTOR.execute(cmd).output

def run_sqlmap(target: str, parameter: str = None) -> str:
    """Run sqlmap"""
    cmd = f'sqlmap -u "{target}"'
    if parameter:
        cmd += f' -p {parameter}'
    return TOOL_EXECUTOR.execute(cmd, timeout=600).output

def check_tool_installed(tool: str) -> bool:
    """Check if tool is installed"""
    return TOOL_EXECUTOR.is_installed(tool)

def list_available_tools() -> List[Dict]:
    """List all tools with installation status"""
    return TOOL_EXECUTOR.list_tools()