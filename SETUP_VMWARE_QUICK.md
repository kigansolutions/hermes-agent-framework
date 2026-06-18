# PromptOrchestrator - VMware Quick Start Guide

Get PromptOrchestrator (Ultimate) running on VMware Workstation Pro in 15 minutes.

## Quick Overview

1. Download Kali Linux VM image
2. Import to VMware
3. Copy PromptOrchestrator files
4. Install OpenCode plugins
5. Run!

---

## Step 1: Get the VM (Kali Linux)

Download Kali Linux VMware image (EASIEST - all tools pre-installed):
```
https://www.kali.org/get-kali/#kali-virtual
```

Download the **VMware** OVA file.

### VMware Import
1. File → Import → Select downloaded OVA
2. VM auto-imports
3. Start VM
4. Login: `kali` / `kali`

### VM Settings (Adjust if needed)
| Setting | Minimum | Recommended |
|---------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8GB | 16GB |
| Disk | 60GB | 100GB |
| Network | NAT | NAT |

---

## Step 2: Install Dependencies

```bash
# Update
sudo apt update && sudo apt upgrade -y

# Install core packages
sudo apt install -y python3 python3-pip git curl wget

# Install PromptOrchestrator Python dependencies
pip3 install requests python-dotenv

# Install workflow tools
sudo apt install -y nmap nikto curl wget git

# Clone PromptOrchestrator
cd /opt
sudo mkdir aios
sudo chown $USER:$USER aios
cd aios

# Copy your PromptOrchestrator files here
# Or if using git:
git clone <your-repo-url> .
```

---

## Step 3: File Transfer Options

### Option A: Via Shared Folder (Easiest)
1. VM Settings > Options > Shared Folders
2. Enable "Always enabled"
3. Point to folder with PromptOrchestrator files
4. In VM: `cp /mnt/hgfs/SharedFolder/* /opt/aios/`

### Option B: Via SCP
```bash
# On host, find VM IP
# In VM: hostname -I

# From host:
scp -r PromptOrchestrator/* aios@<VM-IP>:/opt/aios/
```

### Option C: Via USB
1. Download as ZIP on host
2. Transfer via USB drive
3. Copy to VM

---

## Step 5: Configure

```bash
cd /opt/aios

# Copy example config
cp .env.example .env
nano .env
```

## Step 6: Install OpenCode Plugins (RECOMMENDED)

These plugins supercharge PromptOrchestrator with parallel execution, web scraping, and notifications:

```bash
# Install ocx (extension manager)
curl -fsSL https://ocx.sh | sh

# Add key plugins for PromptOrchestrator
ocx add kdcokenny/opencode-background-agents
ocx add firecrawl/opencode-firecrawl
ocx add kdcokenny/opencode-notify
```

### What Each Plugin Adds

| Plugin | Capability |
|--------|-------------|
| `opencode-background-agents` | Run nmap/nuclei scans in background |
| `opencode-firecrawl` | Web scraping for recon/OSINT |
| `opencode-notify` | Desktop notifications when scans complete |

---

## Step 7: Run PromptOrchestrator

### Interactive Mode
```bash
cd /opt/aios
python3 __main__.py -i
```

### Commands
```bash
# Full workflow
python3 __main__.py run workflow.com

# Just recon
python3 __main__.py recon target.com

# Just vulnerability scan
python3 __main__.py vuln target.com

# Generate report
python3 __main__.py report target.com
```

### Wiki Operations
```bash
# Search wiki
python3 __main__.py wiki search "vulnerability reference"

# Health check
python3 __main__.py wiki lint

# Update index
python3 __main__.py wiki index
```

---

## Step 8: OpenCode Integration (Optional)

For full AI agent capabilities:

```bash
# Install OpenCode
curl -fsSL https://ocx.sh | sh

# Start server
export OPENCODE_SERVER_PASSWORD="your_password"
nohup opencode serve --hostname 0.0.0.0 --port 4096 &

# Test
curl http://localhost:4096/health
```

---

## Plugin Usage

Once installed, use plugins like this:

```bash
# Background scanning (non-blocking)
delegate("Run nuclei on target.com", general)

# Web scraping for recon
# Uses Firecrawl to scrape target
```

---

## Troubleshooting

### Python not found
```bash
which python3
# If not found:
sudo apt install python3 python3-pip
```

### Module errors
```bash
# Install missing dependencies
pip3 install -r requirements.txt
```

### Permission errors
```bash
sudo chown -R $USER:$USER /opt/aios
```

---

## Usage in PromptOrchestrator

After running `python3 __main__.py -i`:

```
PromptOrchestrator> target target.com
PromptOrchestrator> pentest

# Or use individual commands:
PromptOrchestrator> recon target.com
PromptOrchestrator> vuln target.com
PromptOrchestrator> report target.com
```

---

## File Structure on VM

```
/opt/aios/
├── __main__.py           # Main entry
├── config.yaml         # Config
├── opencode.json      # Agent defs
├── README.md       # Full docs
├── knowledge/     # KB + Wiki
├── execution/    # Engine
├── tools/       # Scanner suite
├── skills/      # 11 skills
├── agents/      # Agent definitions
└── docs/       # Full documentation
```

---

## Next Steps

1. Read `/opt/aios/README.md` for full documentation
2. Review skills in `/opt/aios/skills/`
3. Configure `/opt/aios/config.yaml`
4. Start orchestrating!

---

**Ready to hack!** 🎯