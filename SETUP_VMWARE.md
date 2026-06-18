# PromptOrchestrator - Cybersecurity AI Operating System

This guide walks you through setting up PromptOrchestrator (Security AI Operating System) on a VMware Workstation Pro virtual machine.

PromptOrchestrator is an AI-powered penetration testing assistant that uses local open-weighted LLMs to help with web application security assessments.

## Prerequisites
- VMware Workstation Pro (Windows or Linux host)
- **Kali Linux 2024+ VM image (recommended)** or Ubuntu 22.04 LTS Server ISO
- At least 16GB RAM (32GB recommended)
- 8+ CPU cores recommended
- 100GB+ disk space

---

## Step 1: Create the Virtual Machine

### 1.1 Launch VMware Workstation Pro
1. Click **File > New Virtual Machine**
2. Select **Typical (recommended)** and click **Next**
3. Choose **Installer disc image file (iso)** and browse to your Ubuntu Server ISO
4. Click **Next**

### 1.2 Configure VM Settings
- **Guest operating system**: Linux
- **Version**: Ubuntu 64-bit
- **VM name**: OpenAIOS
- **Location**: Choose a location with 100GB+ free space

### 1.3 Hardware Settings
| Setting | Minimum | Recommended |
|---------|---------|-------------|
| Processors | 4 cores | 8 cores |
| Memory | 8GB | 16-32GB |
| Hard Disk | 60GB | 100GB+ |
| Network | NAT | NAT |

> **Important**: For local LLM inference, more CPU/RAM = better performance. 16GB minimum for 8B models, 32GB for 14B+ models.

### 1.4 Complete Installation
1. Click **Finish** to create the VM
2. Start the VM and install Ubuntu Server
3. Create a user account (e.g., `aios`)
4. Install OpenSSH server when prompted

---

## Step 2: Install Dependencies

### 2.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2.2 Install Required Packages
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv curl wget git ffmpeg build-essential
```

### 2.3 Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PromptOrchestrator dependencies
pip install python-telegram-bot python-dotenv requests beautifulsoup4

# Install optional but recommended dependencies
pip install faiss-cpu sentence-transformers

# For Docker: searxng (optional, for privacy-respecting search)
# See https://github.com/searxng/searxng
```

### 2.4 Install OpenCode (AI Agent)
```bash
# Install OpenCode CLI
curl -fsSL https://opencode.ai/install | sh

# Verify installation
opencode --version

# Set up password for API access
export OPENCODE_SERVER_PASSWORD="your_secure_password_here"

# Start OpenCode server in background
nohup opencode serve --hostname 0.0.0.0 --port 4096 > /var/log/opencode.log 2>&1 &

# Check if running
curl http://localhost:4096/health
```

### 2.5 Install Caido (Web Security Toolkit)
```bash
# Download Caido (https://caido.io)
# Caido is a lightweight web security auditing toolkit

# Option 1: Download from official site (requires account)
# Visit https://caido.io/downloads

# Option 2: Use caido-python SDK
pip install caido-sdk-client

# Set up authentication
export CAIDO_AUTH_TOKEN="your_caido_token"
```

### 2.6 Install Browser Harness (Browser Automation)
```bash
# Install browser-use/browser-harness for browser automation
cd /opt
git clone https://github.com/browser-use/browser-harness.git

# Install dependencies
cd browser-harness
pip install -r requirements.txt

# Install Chrome if not present
sudo apt install -y chromium-browser chromium-chromedriver

# Start Chrome with stealth flags (already in setup)
# The integration handles this automatically
```

### 2.7 Install Additional Tools
```bash
# Install SQLMap
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap

# Install JWT tools
pip install pyjwt cryptography

# Install XML tools
pip install xmltodict

# Install API testing
pip install httpie httpx
```

### 2.8 Install OpenCode (AI Agent)
```bash
# Install OpenCode CLI
curl -fsSL https://opencode.ai/install | sh

# Verify installation
opencode --version

# Set up password for API access (optional but recommended)
export OPENCODE_SERVER_PASSWORD="your_secure_password_here"

# Start OpenCode server in background
nohup opencode serve --hostname 0.0.0.0 --port 4096 > /var/log/opencode.log 2>&1 &

# Check if running
curl http://localhost:4096/health
```

### 2.6 Install Background Agents (for parallel task execution)
```bash
# Install OCX (plugin manager)
curl -fsSL https://ocx.sh | sh

# Add background-agents plugin for parallel scanning
ocx add kdco/background-agents --from https://registry.kdco.dev
```

### 2.7 Install Ollama (Optional - for private/sensitive mode)
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2.6 Start Ollama Service
```bash
ollama serve &
```

### 2.7 Pull Open-Weighted Models
```bash
# Recommended: Qwen3 14B (best performance/quality balance)
ollama pull qwen3:14b

# Alternative: Llama3.2 8B (for lower memory systems)
ollama pull llama3.2:8b

# For more powerful systems: Qwen3 32B
ollama pull qwen3:32b
```

Verify Ollama is running:
```bash
curl http://localhost:11434
```

---

## Step 3: Set Up OpenAIOS

### 3.1 Clone/Create the Project
```bash
cd /opt
sudo mkdir aios
sudo chown $USER aios
cd aios

# If you have the project files, copy them here
# Or create the directory structure as shown in SPEC.md
```

### 3.2 Configure Environment
```bash
cp .env.example .env
nano .env
```

Fill in your `.env` file:
```
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_ADMIN_ID=your_telegram_user_id
OPENCODE_SERVER=http://localhost:4096
OPENCODE_SERVER_PASSWORD=your_secure_password
DATABASE_PATH=./data/aios.db
```

### 3.3 Install OpenCode Plugins (RECOMMENDED)
These plugins supercharge PromptOrchestrator:

```bash
# Install ocx (extension manager)
curl -fsSL https://ocx.sh | sh

# Add key plugins
ocx add kdcokenny/opencode-background-agents
ocx add firecrawl/opencode-firecrawl  
ocx add kdcokenny/opencode-notify
```

| Plugin | Capability |
|--------|-------------|
| opencode-background-agents | Background parallel scanning |
| opencode-firecrawl | Web scraping for recon |
| opencode-notify | OS notifications |

### 3.3 Install Python Dependencies
```bash
pip3 install -r requirements.txt
```

### 3.4 Initialize Database
```bash
python3 data_os/db_setup.py
```

---

## Step 4: Set Up Telegram Bot

### 4.1 Create Bot via @BotFather
1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow instructions to name your bot
4. Copy the bot token

### 4.2 Get Your User ID
1. Search for @userinfobot
2. Send any message
3. Copy your user ID

---

## Step 5: Configure Cron Jobs

### 5.1 Create Log Directory
```bash
mkdir -p /opt/aios/logs
```

### 5.2 Edit Crontab
```bash
crontab -e
```

Add these lines:
```cron
# Daily data snapshot at 6 AM
0 6 * * * /opt/aios/cron/data_snapshot.sh >> /opt/aios/logs/cron.log 2>&1

# Daily brief at 7 AM
0 7 * * * /opt/aios/cron/daily_brief.sh >> /opt/aios/logs/cron.log 2>&1
```

---

## Step 6: Start the System

### 6.1 Start Ollama (if not running)
```bash
ollama serve &
```

### 6.2 Start Telegram Bot
```bash
cd /opt/aios
python3 execution/telegram/bot.py
```

### 6.3 Run in Background (Production)
```bash
# Using systemd (recommended)
sudo nano /etc/systemd/system/aios.service
```

Create `/etc/systemd/system/aios.service`:
```ini
[Unit]
Description=OpenAIOS Telegram Bot
After=network.target

[Service]
Type=simple
User=aios
WorkingDirectory=/opt/aios
ExecStart=/usr/bin/python3 execution/telegram/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable aios
sudo systemctl start aios
sudo systemctl status aios
```

---

## Step 7: Configure Context Files

Edit the files in `/opt/aios/context/`:
- `business.md` - Your company info
- `products.md` - Products and services
- `processes.md` - Business processes
- `goals.md` - Goals and metrics

---

## Usage

### Telegram Commands
| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/brief` | Generate daily brief |
| `/tasks` | List pending tasks |
| `/addtask <title>` | Add a task |
| `/complete <id>` | Complete a task |
| `/metric <name> <value>` | Record metric |
| `/query <question>` | Query data |

### Voice Notes
Send a voice note and the bot will transcribe and process it.

---

## Troubleshooting

### Ollama not responding
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama
pkill ollama
ollama serve &
```

### Bot not responding
```bash
# Check bot logs
tail -f logs/cron.log

# Restart bot
sudo systemctl restart aios
```

### Model too slow
- Reduce `OLLAMA_MODEL` to a smaller model (e.g., `llama3.2:8b`)
- Increase VM RAM
- Add more CPU cores

---

## Recommended Models

| Model | RAM Needed | Performance |
|-------|------------|-------------|
| llama3.2:8b | 8GB | Good |
| qwen3:14b | 16GB | Very Good |
| gemma3:12b | 14GB | Very Good |
| qwen3:32b | 32GB | Excellent |

All models are open-weighted and run completely offline via Ollama.