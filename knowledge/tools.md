# PromptOrchestrator Tools Reference

Comprehensive list of tools available for security testing.

---

## Discovery

### Network Scanning
| Tool | Description | Install |
|------|-------------|---------|
| `nmap` | Port scanning, service detection | `apt install nmap` |
| `masscan` | Fast port scanner | `apt install masscan` |
| `rustscan` | Modern port scanner | `cargo install rustscan` |

### DNS Enumeration
| Tool | Description | Install |
|------|-------------|---------|
| `subfinder` | Passive subdomain enumeration | `apt install subfinder` |
| `amass` | Subdomain enumeration | `apt install amass` |
| `assetfinder` | Find related domains | `go install github.com/tomnomnom/assetfinder@latest` |
| `fierce` | DNS scanner | `apt install fierce` |
| `dnsenum` | DNS enumeration | `apt install dnsenum` |

### Directory Enumeration
| Tool | Description | Install |
|------|-------------|---------|
| `gobuster` | Directory/DNS/VHost enum | `apt install gobuster` |
| `ffuf` | Fast web fuzzer | `apt install ffuf` |
| `dirb` | Directory scanner | `apt install dirb` |
| `dirbuster` | GUI directory scanner | `apt install dirbuster` |
| `wfuzz` | Web fuzzer | `apt install wfuzz` |

### Technology Detection
| Tool | Description | Install |
|------|-------------|---------|
| `whatweb` | Web technology fingerprinting | `apt install whatweb` |
| `wappalyzer` | Technology stack detection | CLI available |
| `builtwith` | Technology lookup | API |

---

## Vulnerability Scanning

### Web Scanners
| Tool | Description | Install |
|------|-------------|---------|
| `nikto` | Web server scanner | `apt install nikto` |
| `nuclei` | Template-based scanner | `apt install nuclei` |
| `wapiti` | Black-box vulnerability scanner | `apt install wapiti` |
| `skipfish` | Discovery scanner | `apt install skipfish` |
| `arachni` | Web application scanner | `apt install arachni` |
| `w3af` | Web application attack framework | `apt install w3af` |
| ` OWASP ZAP` | Web proxy + scanner | `apt install zaproxy` |

### Specific Vulnerability
| Tool | Vulnerability | Install |
|------|---------------|---------|
| `sqlmap` | SQL Injection | `apt install sqlmap` |
| `xsser` | XSS | `apt install xsser` |
| `xsstrike` | XSS | `pip install xsstrike` |
| `dalfox` | XSS | `go install github.com/hahwul/dalfox@latest` |
| `commix` | Command Injection | `apt install commix` |
| `ssrfmap` | SSRF | `git clone` |
| `jwt_tool` | JWT attacks | `git clone` |

---

## Exploitation

### Password Attacks
| Tool | Description | Install |
|------|-------------|---------|
| `hydra` | Online password cracker | `apt install hydra` |
| `john` | Password cracker | `apt install john` |
| `hashcat` | GPU password recovery | `apt install hashcat` |
| `cewl` | Wordlist generator | `apt install cewl` |

### Network Exploitation
| Tool | Description | Install |
|------|-------------|---------|
| `responder` | LLMNR/NBT-NS poisoner | `apt install responder` |
| `mitmproxy` | MITM proxy | `apt install mitmproxy` |
| `ettercap` | MITM suite | `apt install ettercap-graphical` |

### Web Exploitation
| Tool | Description | Install |
|------|-------------|---------|
| `burpsuite` | Web testing platform | `apt install burpsuite` |
| `caido` | Lightweight web auditing | Download from caido.io |
| `beef` | Browser exploitation | `apt install beef-xss` |

---

## Post-Exploitation

| Tool | Description | Install |
|------|-------------|---------|
| `metasploit` | Exploitation framework | `apt install metasploit-framework` |
| `meterpreter` | Advanced payload | Part of Metasploit |
| `mimikatz` | Credential dumping | `apt install mimikatz` |
| `linpeas` | Linux privilege escalation | `curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh` |
| `winpeas` | Windows privilege escalation | Download from PEASS |

---

## API Testing

| Tool | Description | Install |
|------|-------------|---------|
| `httpx` | HTTP toolkit | `go install github.com/projectdiscovery/httpx@latest` |
| `httpie` | CLI HTTP client | `pip install httpie` |
| `restler` | REST API fuzzer | Microsoft GitHub |
| `cherrytree` | Notes | `apt install cherrytree` |

---

## Mobile Testing

| Tool | Description | Install |
|------|-------------|---------|
| `jadx` | Java decompiler | `apt install jadx` |
| `frida` | Dynamic instrumentation | `pip install frida-tools` |
| `apktool` | APK reverse engineering | `apt install apktool` |

---

## Smart Contract Testing

| Tool | Description | Install |
|------|-------------|---------|
| `slither` | Static analysis | `pip install slither-analyzer` |
| `mythril` | Security analysis | `pip install mythril` |
| `echidna` | Fuzzing | `pip install eth-abi` |
| `remix` | IDE | remix.ethereum.org |
| `hardhat` | Development framework | `npm install -g hardhat` |
| `foundry` | Testing framework | `curl -L https://foundry.paradigm.xyz | bash` |

---

## LLM/AI Security

| Tool | Description | Install |
|------|-------------|---------|
| `gptfuzzer` | LLM fuzzing | `git clone` |
| `llm-fuzz` | LLM fuzzing | `pip install` |
| `leakpilot` | Prompt injection | `pip install` |

---

## Reporting

| Tool | Description | Install |
|------|-------------|---------|
| `faraday` | Collaborative penetration testing | `docker run faradaysec/faraday` |
| `dradis` | Reporting framework | `apt install dradis` |
| `cherrytree` | Notes/documentation | `apt install cherrytree` |
| `obsidian` | Knowledge management | Download |
| `pandoc` | Document conversion | `apt install pandoc` |

---

## Quick Install Script

```bash
#!/bin/bash
# PromptOrchestrator Tools Installation

# Core tools
sudo apt update
sudo apt install -y nmap masscan gobuster ffuf dirb nikto nuclei wapiti sqlmap hydra john hashcat curl wget git python3 python3-pip

# Wordlists
sudo apt install -y wordlists
sudo wget -q https://github.com/danielmiessler/SecLists/archive/refs/heads/master.zip -O /tmp/seclists.zip
sudo unzip -o /tmp/seclists.zip -d /usr/share/wordlists/
rm /tmp/seclists.zip

# Subdomain enum
sudo wget -q https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip -O /tmp/subfinder.zip
sudo unzip -o /tmp/subfinder.zip -d /tmp/
sudo mv /tmp/subfinder/subfinder /usr/local/bin/
rm -rf /tmp/subfinder*

# HTTP tools
sudo pip3 install httpx httpie

# Additional
sudo apt install -y whatweb dnsenum fierce responder

# Nuclei templates
nuclei -upd

echo "✅ Tools installed!"
```