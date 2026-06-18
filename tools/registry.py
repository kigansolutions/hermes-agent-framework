"""
prompt-orchestrator — Tool Registry
====================================
Reference implementation of the uniform tool interface used by the
orchestrator. Any external capability (CLI binary, REST API, database,
library) is wrapped as a tool conforming to the same shape, so the
agent loop treats them all identically.

The class below is a **pattern**, not a domain-specific library. The
example tools wired up here (`curl_head`, `curl_get`, `whois`,
`check_http_methods`) are intentionally generic — every agent can
use them. The security-domain examples (nmap, nikto, nuclei, ...) are
included as **commented-out reference implementations** showing how
a domain-specific tool would slot in.

Adding a new tool is a three-step process:

    1. Add a method to `ToolRegistry` that wraps the external call.
    2. Register it in the `tools` dict at __init__.
    3. Add a matching JSON schema to `TOOL_SCHEMAS` so the LLM knows
       the tool's name, description, and parameter shape.

The schema follows the OpenAI function-calling convention, which is
what Claude Code, Hermes, and most agent frameworks consume.
"""

import subprocess
from typing import Any, Callable, Dict, List


class ToolRegistry:
    """Registry of tool wrappers the orchestrator can invoke."""

    def __init__(self):
        self.tools: Dict[str, Callable[..., str]] = {
            # ─── Generic tools (always available) ─────────────────
            "curl_head": self.curl_head,
            "curl_get": self.curl_get,
            "whois": self.run_whois,
            "check_http_methods": self.check_http_methods,
            # ─── Domain-specific reference implementations ───────
            # Uncomment the tools that match your domain. The
            # patterns shown here are how a security assessment
            # toolkit would integrate; other domains (research,
            # ops, content) follow the same shape.
            #
            # 'run_nmap': self.run_nmap,
            # 'run_nuclei': self.run_nuclei,
            # 'run_subfinder': self.run_subfinder,
            # 'run_gobuster': self.run_gobuster,
            # 'run_nikto': self.run_nikto,
        }

    # ─────────────────────────────────────────────────────────────
    # Generic tools
    # ─────────────────────────────────────────────────────────────

    def curl_head(self, url: str) -> str:
        """Send HEAD request to URL. Returns HTTP headers — server
        type, cookies, security headers, caching policies."""
        cmd = f"curl -s -I {url}"
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error: {e}"

    def curl_get(self, url: str, follow_redirects: bool = True) -> str:
        """Send GET request to URL and retrieve the response body.
        Useful for analyzing page structure, headers, and content."""
        redirect_flag = "-L" if follow_redirects else "-s"
        cmd = f"curl {redirect_flag} {url}"
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            return f"Response:\n{result.stdout[:5000]}"
        except Exception as e:
            return f"Error: {e}"

    def run_whois(self, domain: str) -> str:
        """Perform a WHOIS lookup. Returns registration info,
        nameservers, and contact details."""
        cmd = f"whois {domain}"
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.stdout[:5000]
        except Exception as e:
            return f"Error: {e}"

    def check_http_methods(self, url: str) -> str:
        """Check which HTTP methods are allowed (OPTIONS). Useful
        for identifying capabilities the server exposes."""
        cmd = f"curl -s -X OPTIONS {url} -I"
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error: {e}"

    # ─────────────────────────────────────────────────────────────
    # Domain-specific reference implementations (commented)
    # ─────────────────────────────────────────────────────────────
    #
    # The pattern below shows how a domain-specific tool is wired
    # in. Each method:
    #   1. Has a docstring (becomes the LLM-facing description)
    #   2. Builds a shell command from typed parameters
    #   3. Wraps subprocess.run with timeouts and error handling
    #   4. Returns the captured output as a string
    #
    # The matching *_SCHEMA dict at the bottom of the file gives
    # the LLM a typed view of the same tool so it knows what
    # arguments to pass.

    def run_nmap(self, target: str, ports: str = "1-1000", flags: str = "-sV") -> str:
        """[Reference] Port and service scan. Replace with the
        scanner that fits your domain."""
        cmd = f"nmap {flags} -p {ports} {target} -oG -"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            return f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: scan timed out"
        except Exception as e:
            return f"Error: {e}"

    def run_nuclei(self, target: str, severity: str = "medium,high,critical") -> str:
        """[Reference] Template-based finding scanner. Domain-specific."""
        cmd = f"nuclei -u {target} -severity {severity} -silent"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
            return f"Findings:\n{result.stdout}\n\nErrors:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: scan timed out"
        except Exception as e:
            return f"Error: {e}"

    def run_subfinder(self, domain: str) -> str:
        """[Reference] Passive enumeration. Domain-specific."""
        cmd = f"subfinder -d {domain} -silent"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            return f"Results:\n{result.stdout}"
        except Exception as e:
            return f"Error: {e}"

    def run_gobuster(self, target: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt",
                     threads: int = 10) -> str:
        """[Reference] Enumeration over a wordlist. Domain-specific."""
        cmd = f"gobuster dir -u {target} -w {wordlist} -t {threads}"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            return f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: scan timed out"
        except Exception as e:
            return f"Error: {e}"

    def run_nikto(self, target: str, port: str = "80") -> str:
        """[Reference] Web server scanner. Domain-specific."""
        cmd = f"nikto -h {target} -p {port}"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
            return f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: scan timed out"
        except Exception as e:
            return f"Error: {e}"


# ─── Schemas (LLM-facing) ────────────────────────────────────────
# Each schema follows the OpenAI function-calling convention. The
# LLM uses these to learn the tool's name, description, and
# parameter shape. Tools registered above but missing from this
# list will be invisible to the LLM.

CURL_HEAD_SCHEMA = {
    "type": "function",
    "function": {
        "name": "curl_head",
        "description": (
            "Send HEAD request to URL. Returns HTTP headers — server "
            "type, cookies, security headers, caching policies."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL"},
            },
            "required": ["url"],
        },
    },
}

CURL_GET_SCHEMA = {
    "type": "function",
    "function": {
        "name": "curl_get",
        "description": (
            "Send GET request to retrieve full page content. "
            "Useful for analyzing page structure and content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL"},
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Follow redirects (default: true)",
                    "default": True,
                },
            },
            "required": ["url"],
        },
    },
}

WHOIS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "whois",
        "description": (
            "Perform a WHOIS lookup. Returns registration info, "
            "nameservers, and contact details."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Target domain"},
            },
            "required": ["domain"],
        },
    },
}

HTTP_METHODS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_http_methods",
        "description": (
            "Check which HTTP methods are allowed (OPTIONS). "
            "Identifies server capabilities."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL"},
            },
            "required": ["url"],
        },
    },
}

# Domain-specific reference schemas — same shape as the generic
# ones, included to demonstrate the pattern. Comment out the
# imports and registrations above to activate them.
NMAP_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_nmap",
        "description": "[Reference] Port and service scan.",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target IP or hostname"},
                "ports": {"type": "string", "description": "Port range (default: 1-1000)", "default": "1-1000"},
                "flags": {"type": "string", "description": "Additional flags (default: -sV)", "default": "-sV"},
            },
            "required": ["target"],
        },
    },
}

NUCLEI_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_nuclei",
        "description": "[Reference] Template-based finding scanner.",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target URL"},
                "severity": {"type": "string", "description": "Severity filter (default: medium,high,critical)",
                             "default": "medium,high,critical"},
            },
            "required": ["target"],
        },
    },
}

SUBFINDER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_subfinder",
        "description": "[Reference] Passive enumeration.",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Target domain"},
            },
            "required": ["domain"],
        },
    },
}

GOBUSTER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_gobuster",
        "description": "[Reference] Enumeration over a wordlist.",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target URL"},
                "wordlist": {"type": "string", "description": "Path to wordlist",
                             "default": "/usr/share/wordlists/dirb/common.txt"},
                "threads": {"type": "string", "description": "Thread count (default: 10)", "default": "10"},
            },
            "required": ["target"],
        },
    },
}

NIKTO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_nikto",
        "description": "[Reference] Web server scanner.",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target URL or IP"},
                "port": {"type": "string", "description": "Port (default: 80)", "default": "80"},
            },
            "required": ["target"],
        },
    },
}


# ─── Active schema list ──────────────────────────────────────────
# The orchestrator ships with only the generic tools active. Domain
# schemas are commented out — uncomment to add them to the LLM's
# tool list at startup.

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    CURL_HEAD_SCHEMA,
    CURL_GET_SCHEMA,
    WHOIS_SCHEMA,
    HTTP_METHODS_SCHEMA,
    # Domain-specific reference schemas (uncomment to activate):
    # NMAP_SCHEMA,
    # NUCLEI_SCHEMA,
    # SUBFINDER_SCHEMA,
    # GOBUSTER_SCHEMA,
    # NIKTO_SCHEMA,
]


# ─── Singleton ──────────────────────────────────────────────────
# Imported as `from tools.registry import TOOL_REGISTRY, TOOL_SCHEMAS`
TOOL_REGISTRY = ToolRegistry()
