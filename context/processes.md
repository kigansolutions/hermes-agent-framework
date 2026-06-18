# Testing Workflows

## Web Application Penetration Testing

### Phase 1: Reconnaissance
1. Passive recon (OSINT)
2. Active reconnaissance (nmap, DNS enum)
3. Technology fingerprinting
4. Directory enumeration (gobuster, dirb)

### Phase 2: Vulnerability Assessment
1. Automated scanning (nikto, nuclei)
2. Manual testing for OWASP Top 10
3. Parameter fuzzing
4. JS analysis

### Phase 3: Exploitation
1. SQL injection exploitation
2. XSS payloads
3. Authentication bypass
4. IDOR exploitation

### Phase 4: Documentation
1. Screenshot evidence
2. Proof of concept
3. Impact assessment
4. Remediation steps

## Common Commands
### Port Scanning
```bash
nmap -sV -p- --script=vuln target.com
```

### Directory Busting
```bash
gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt
```

### SSL Analysis
```bash
testssl target.com
```

## Notes
- Always stay within scope
- Document everything
- Get permission screenshots
- Use safe payloads first