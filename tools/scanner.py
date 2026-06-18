#!/usr/bin/env python3
"""
prompt-orchestrator — CLI Wrappers
===================================
Reference wrappers around a few common CLI tools. The same pattern
extends to any tool — network scanners, HTTP clients, linters,
formatters, package managers, anything with a CLI.

Each wrapper returns a dict with the tool name, subject, and a
parsable payload so the orchestrator can reason about results.

This module ships commented-out examples of domain-specific wrappers.
Uncomment the ones you need for your workflow, or write your own.
"""

import json
import os
import re
import socket
import subprocess


# ========================================
# Generic wrappers
# ========================================

def check_port(host: str, port: int, timeout: int = 3) -> bool:
    """Check if a TCP port is open on a host."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((host, port)) == 0
    except Exception:
        return False
    finally:
        sock.close()


def resolve_hostname(hostname: str) -> str:
    """Resolve a hostname to an IPv4 address."""
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        return None


def grab_banner(host: str, port: int, timeout: int = 5) -> str:
    """Grab a service banner from a host:port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
        return sock.recv(1024).decode("utf-8", errors="ignore")
    except Exception:
        return None
    finally:
        sock.close()


def run_curl(url: str, method: str = "GET", headers: dict = None,
             follow_redirects: bool = True, timeout: int = 30) -> dict:
    """Run a curl request and return a structured response."""
    cmd = ["curl", "-sS", "-X", method, "-w", "\\n%{http_code}"]
    if follow_redirects:
        cmd.append("-L")
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"tool": "curl", "url": url, "success": False, "error": "timeout"}

    parts = result.stdout.rsplit("\n", 1)
    body, status = parts[0], parts[1] if len(parts) > 1 else "?"
    return {
        "tool": "curl",
        "url": url,
        "status": status,
        "body": body[:5000],
        "success": result.returncode == 0,
    }


def run_whois(subject: str) -> dict:
    """Run a WHOIS lookup."""
    cmd = ["whois", subject]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {"tool": "whois", "subject": subject, "success": False, "error": str(e)}
    return {
        "tool": "whois",
        "subject": subject,
        "output": result.stdout[:5000],
        "success": result.returncode == 0,
    }


def run_dig(domain: str, record_type: str = "ANY") -> dict:
    """Run a DNS query."""
    cmd = ["dig", "+short", domain, record_type]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {"tool": "dig", "domain": domain, "success": False, "error": str(e)}
    records = [r for r in result.stdout.strip().split("\n") if r]
    return {
        "tool": "dig",
        "domain": domain,
        "record_type": record_type,
        "records": records,
        "success": result.returncode == 0,
    }


def run_http_methods(url: str) -> dict:
    """Send an OPTIONS request to discover allowed HTTP methods."""
    cmd = ["curl", "-sS", "-X", "OPTIONS", "-i", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return {"tool": "options", "url": url, "success": False, "error": str(e)}
    allow = None
    for line in result.stdout.split("\n"):
        if line.lower().startswith("allow:"):
            allow = line.split(":", 1)[1].strip()
            break
    return {
        "tool": "options",
        "url": url,
        "allow": allow,
        "success": result.returncode == 0,
    }


# ========================================
# Domain-specific wrappers (reference examples)
# ========================================
# The wrappers below are commented out by default. They demonstrate
# the pattern for a network-scanning workflow. Uncomment the ones
# you need, or use them as a template for your own.
#
# def run_nmap(subject: str, ports: str = "-", arguments: str = "-sV") -> dict:
#     """Network port + service scan."""
#     output_file = f"/tmp/nmap_{subject.replace('.', '_')}"
#     cmd = ["nmap", "-p", ports, arguments, subject, "-oA", output_file]
#     result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
#     services = []
#     for port, proto, service, version in re.findall(
#         r"(\d+)/(\w+)\s+open\s+(\S+)\s+(\S+)", result.stdout
#     ):
#         services.append({"port": int(port), "protocol": proto,
#                          "service": service, "version": version})
#     return {"tool": "nmap", "subject": subject,
#             "services": services, "open_count": len(services),
#             "raw": result.stdout[:5000]}
#
# def run_subfinder(domain: str) -> dict:
#     """Passive subdomain discovery."""
#     cmd = ["subfinder", "-d", domain, "-o", f"/tmp/subfinder_{domain}.txt"]
#     result = subprocess.run(cmd, capture_output=True, text=True)
#     domains = []
#     if result.returncode == 0:
#         try:
#             with open(f"/tmp/subfinder_{domain}.txt") as f:
#                 domains = [line.strip() for line in f if line.strip()]
#         except FileNotFoundError:
#             pass
#     return {"tool": "subfinder", "domain": domain,
#             "found": len(domains), "items": domains,
#             "success": result.returncode == 0}
#
# def run_nuclei(subject: str, severity: str = "critical,high,medium") -> dict:
#     """Template-based finding scanner."""
#     cmd = ["nuclei", "-u", subject, "-severity", severity,
#            "-silent", "-json", "-o", f"/tmp/nuclei_{subject}.json"]
#     result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
#     findings = []
#     try:
#         with open(f"/tmp/nuclei_{subject}.json") as f:
#             for line in f:
#                 if line.strip():
#                     findings.append(json.loads(line))
#     except FileNotFoundError:
#         pass
#     return {"tool": "nuclei", "subject": subject,
#             "findings": len(findings), "items": findings,
#             "severity": severity}


# ========================================
# Generic report formatter
# ========================================

def format_report_markdown(subject: str, findings: list, extras: dict = None) -> str:
    """Format a generic markdown report.

    Args:
        subject: the subject of the workflow (URL, identifier, file, etc.)
        findings: list of finding dicts with title / severity / description
        extras: optional dict of additional sections (services, references, …)
    """
    from datetime import datetime
    extras = extras or {}

    lines = [
        f"# Workflow Report: {subject}",
        "",
        "## Summary",
        f"- Subject: {subject}",
        f"- Date: {datetime.now().strftime('%Y-%m-%d')}",
        f"- Findings: {len(findings)}",
        "",
        "## Findings",
        "",
    ]

    for i, f in enumerate(findings, 1):
        lines.append(f"### {i}. {f.get('title', 'Unknown')}")
        lines.append(f"**Severity**: {f.get('severity', 'medium')}")
        lines.append(f"**Description**: {f.get('description', 'N/A')}")
        lines.append("")

    if extras:
        lines.append("## Details")
        lines.append("")
        lines.append("| Key | Value |")
        lines.append("|---|---|")
        for k, v in extras.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("1. Review findings by severity")
    lines.append("2. Document follow-up actions")
    lines.append("3. Re-verify after changes")
    lines.append("")

    return "\n".join(lines)


# ========================================
# CLI dispatch
# ========================================

def main():
    import sys
    print("prompt-orchestrator — CLI wrappers")
    print("Usage: python -m tools.scanner <tool> <subject>")
    print()
    print("Generic tools:")
    print("  check_port  <host> <port>")
    print("  resolve     <hostname>")
    print("  banner      <host> <port>")
    print("  curl        <url>")
    print("  whois       <subject>")
    print("  dig         <domain> [record_type]")
    print("  options     <url>")
    return


if __name__ == "__main__":
    main()
