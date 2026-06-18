"""
prompt-orchestrator — Telegram Chat Front-End
=============================================
Reference Telegram bot that exposes the orchestrator over chat. Each
user gets an isolated session, a model backend (local or cloud), and
access to the same 5-layer memory the CLI uses.

The model backend is pluggable — by default the bot talks to any
OpenAI-compatible HTTP endpoint (Ollama, vLLM, OpenRouter, etc.).
The default backend here is Ollama for local/private operation.

This file was previously `opencode_bot.py` (tied to a specific CLI
binary). The pattern is unchanged; only the vendor-specific bits
have been replaced with a generic HTTP backend.
"""

import os
import sys
import json
import time
import subprocess
import requests
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Make project root importable so we can pull in the memory layer.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from memory.enhanced import MEMORY  # noqa: E402

load_dotenv()

# ─── Configuration ──────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:14b")

# Optional cloud backend (OpenAI-compatible)
CLOUD_BASE_URL = os.environ.get("CLOUD_BASE_URL", "")
CLOUD_MODEL = os.environ.get("CLOUD_MODEL", "")
CLOUD_API_KEY = os.environ.get("CLOUD_API_KEY", "")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "./data/orchestrator.db")

current_model = OLLAMA_MODEL  # default to local
MAX_TOOL_CALLS = 5


# ─── Default system prompt ──────────────────────────────────────
DEFAULT_SYSTEM_PROMPT = """You are prompt-orchestrator, an AI assistant that drives
multi-phase workflows against user-supplied subjects.

## Capabilities
- Full filesystem access (within the orchestrator's sandbox)
- Execute any shell command available on the host
- Read/write files
- Invoke any tool registered in `tools/registry.py`
- Search code with grep / glob
- Run multi-phase workflows from the skill registry

## Methodology
1. Discover — identify what's relevant
2. Scan — enumerate the operating surface
3. Analyze — reason about findings
4. Build — produce artifacts or take actions
5. Integrate — connect outputs to downstream systems
6. Document — produce the final report

## Memory
You have access to a 5-layer memory system:
1. Working memory — current engagement (subject, phase, scope)
2. Semantic memory — facts and findings (vector store)
3. Episodic memory — activity history (KV store)
4. Cross-engagement memory — persistent knowledge
5. Skill memory — dynamic tool prompts

Always reference memory before acting — it tells you what's already
known so you don't re-derive it.

## Output format
For each finding provide:
- Title
- Severity (Critical / High / Medium / Low / Info)
- Description
- Impact
- Evidence
- Follow-up

## Rules
- Verify scope before acting on a subject.
- Get confirmation before destructive operations.
- Document findings with evidence.
- Use non-destructive techniques first.
- Never fabricate output — say "I don't know" if you don't.
"""


# ─── Backend lifecycle ──────────────────────────────────────────
def ensure_backend() -> bool:
    """Make sure the active model backend is reachable. Returns True if OK."""
    global current_model
    if current_model.startswith("ollama") or current_model == OLLAMA_MODEL:
        try:
            requests.get(f"{OLLAMA_BASE_URL}/", timeout=2)
            return True
        except requests.RequestException:
            # Try to start Ollama in the background.
            try:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(3)
                requests.get(f"{OLLAMA_BASE_URL}/", timeout=2)
                return True
            except Exception:
                return False
    # Cloud backend — assume reachable if URL + key are set.
    return bool(CLOUD_BASE_URL and CLOUD_API_KEY)


def send_prompt(prompt: str, system: str = DEFAULT_SYSTEM_PROMPT) -> tuple[str, bool]:
    """Send a prompt to the active backend. Returns (response, ok)."""
    if current_model == OLLAMA_MODEL or current_model.startswith("ollama"):
        return _send_ollama(prompt, system)
    return _send_cloud(prompt, system)


def _send_ollama(prompt: str, system: str) -> tuple[str, bool]:
    """Talk to a local Ollama instance."""
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "system": system,
                "prompt": prompt,
                "stream": False,
            },
            timeout=300,
        )
        if resp.status_code != 200:
            return f"Error: backend returned {resp.status_code}", False
        return resp.json().get("response", "No response"), True
    except Exception as e:
        return f"Error: {e}", False


def _send_cloud(prompt: str, system: str) -> tuple[str, bool]:
    """Talk to an OpenAI-compatible cloud backend."""
    try:
        resp = requests.post(
            f"{CLOUD_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {CLOUD_API_KEY}"},
            json={
                "model": CLOUD_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
            timeout=300,
        )
        if resp.status_code != 200:
            return f"Error: backend returned {resp.status_code}", False
        data = resp.json()
        return data["choices"][0]["message"]["content"], True
    except Exception as e:
        return f"Error: {e}", False


# ─── Session manager ────────────────────────────────────────────
class OrchestratorSession:
    """One Telegram-user's orchestrator session."""

    def __init__(self):
        self.user_sessions: dict[str, dict] = {}

    def chat(self, user_id: int, message: str) -> str:
        """Send a message with full memory context."""
        user_id_str = str(user_id)

        # Build context from the 5-layer memory.
        context = MEMORY.build_context_prompt(
            user_id_str,
            include_skills=True,
            include_knowledge=True,
            include_web_search=True,
            query=message,
        )

        enhanced_prompt = f"""=== ORCHESTRATOR MEMORY CONTEXT ===
{context}

=== NEW USER REQUEST ===
{message}

Instructions:
1. Review the memory context above — what engagement is active,
   what's been done, what skills are relevant.
2. Execute the requested task using appropriate tools.
3. Record new findings in memory with severity labels.
4. Provide a comprehensive response.
"""

        MEMORY.record_episode(user_id_str, "user_message", message[:500])

        response, ok = send_prompt(enhanced_prompt)
        if ok:
            MEMORY.record_episode(
                user_id_str, "assistant_response", response[:500], outcome="success"
            )
        else:
            MEMORY.record_episode(
                user_id_str, "error", response[:200], outcome="error"
            )
        return response


SESSION = OrchestratorSession()


# ─── Command handlers ───────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    backend = "Local (Ollama)" if current_model == OLLAMA_MODEL else "Cloud"
    await update.message.reply_text(
        f"🎯 *prompt-orchestrator*\n\n"
        f"Backend: *{backend}*\n\n"
        f"5-layer memory:\n"
        f"• Working — current engagement\n"
        f"• Semantic — facts & findings\n"
        f"• Episodic — activity history\n"
        f"• Cross-engagement — persistent knowledge\n"
        f"• Skills — dynamic tool prompts\n\n"
        f"Commands:\n"
        f"/start — this message\n"
        f"/model — switch backend (local / cloud)\n"
        f"/subject <name> — start a new engagement\n"
        f"/status — current engagement\n"
        f"/phase <phase> — set phase\n"
        f"/findings — list findings\n"
        f"/help — help",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Commands*\n\n"
        "*Engagement:*\n"
        "/subject <name> — new engagement\n"
        "/status — current status\n"
        "/phase <phase> — set phase\n\n"
        "*Memory:*\n"
        "/findings — list findings\n"
        "/history — recent activity\n"
        "/memory <query> — semantic search\n"
        "/forget — clear memory\n\n"
        "*Skills:*\n"
        "/skills — show registered skills\n\n"
        "Or just chat naturally to invoke the orchestrator.",
        parse_mode="Markdown",
    )


async def subject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /subject <name>")
        return
    subject = " ".join(context.args)
    user_id = str(update.effective_user.id)
    MEMORY.start_engagement(user_id, subject)
    await update.message.reply_text(
        f"✅ *Engagement Started*\n\nSubject: `{subject}`\nPhase: discover\n\n"
        f"Memory initialized. What's the first action?",
        parse_mode="Markdown",
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    engagement = MEMORY.get_engagement(user_id)
    if not engagement:
        await update.message.reply_text("No active engagement. /subject <name> to start.")
        return
    findings = MEMORY.get_findings(user_id)
    tool_history = MEMORY.get_tool_history(user_id, limit=5)
    status_text = (
        f"📊 *Current Engagement*\n\n"
        f"Subject: `{engagement['subject']}`\n"
        f"Phase: {engagement['phase']}\n"
        f"Findings: {len(findings)}\n"
        f"Tools used: {len(tool_history)}\n"
        f"Last active: {engagement['last_active'][:19]}"
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def findings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    findings = MEMORY.get_findings(user_id)
    if not findings:
        await update.message.reply_text("No findings yet.")
        return
    response = "🔍 *Findings*\n\n"
    for f in findings[:10]:
        emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }.get(f.get("severity", "").lower(), "⚪")
        response += f"{emoji} {f['title']}\n"
    await update.message.reply_text(response, parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    episodes = MEMORY.get_recent_episodes(user_id, limit=15)
    if not episodes:
        await update.message.reply_text("No recent activity.")
        return
    response = "📜 *Recent Activity*\n\n"
    for ep in reversed(episodes):
        ts = ep["timestamp"][:19].replace("T", " ")
        response += f"• {ts}: {ep['content'][:80]}\n"
    await update.message.reply_text(response, parse_mode="Markdown")


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /memory <search query>")
        return
    query = " ".join(context.args)
    results = MEMORY.semantic_search(query, k=5)
    if not results:
        await update.message.reply_text(f"No memories found for: {query}")
        return
    response = f"🧠 *Memory Search: {query}*\n\n"
    for r in results:
        response += f"• {r['content'][:150]}...\n"
        response += f"  (similarity: {r.get('distance', 'N/A')})\n\n"
    await update.message.reply_text(response, parse_mode="Markdown")


async def skills_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from skills.manager import SKILLS_MANAGER  # late import — avoid loading at module-import time

    skills_list = SKILLS_MANAGER.list_skills()
    response = "🔧 *Available Skills*\n\n"
    for s in skills_list:
        response += f"*{s['name']}*\n{s['description'][:80]}...\n\n"
    await update.message.reply_text(response, parse_mode="Markdown")


async def phase_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /phase <discover|scan|analyze|build|integrate|document>"
        )
        return
    phase = context.args[0].lower()
    valid_phases = ["discover", "scan", "analyze", "build", "integrate", "document"]
    if phase not in valid_phases:
        await update.message.reply_text(f"Invalid phase. Use: {', '.join(valid_phases)}")
        return
    user_id = str(update.effective_user.id)
    MEMORY.update_engagement(user_id, phase=phase)
    await update.message.reply_text(f"✅ Phase updated to: *{phase}*", parse_mode="Markdown")


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch between local (Ollama) and cloud (OpenAI-compatible) backends."""
    global current_model

    if not context.args:
        current = "🔒 Local (Ollama)" if current_model == OLLAMA_MODEL else "☁️ Cloud"
        await update.message.reply_text(
            f"Current backend: *{current}*\n\n"
            f"Available backends:\n"
            f"• `local` — local Ollama (private)\n"
            f"• `cloud` — OpenAI-compatible cloud endpoint\n\n"
            f"Usage: `/model local` or `/model cloud`",
            parse_mode="Markdown",
        )
        return

    choice = context.args[0].lower()
    if choice in ("local", "ollama", "private"):
        current_model = OLLAMA_MODEL
        if not ensure_backend():
            await update.message.reply_text(
                "⚠️ Could not reach local Ollama. Is `ollama serve` running?"
            )
            return
        await update.message.reply_text(
            "✅ Switched to *Local (Ollama)* backend.\n\n"
            "🔒 Conversations stay on this machine.",
            parse_mode="Markdown",
        )
    elif choice in ("cloud", "remote"):
        if not (CLOUD_BASE_URL and CLOUD_API_KEY):
            await update.message.reply_text(
                "⚠️ Cloud backend not configured. Set CLOUD_BASE_URL and CLOUD_API_KEY."
            )
            return
        current_model = CLOUD_MODEL
        await update.message.reply_text(
            "✅ Switched to *Cloud* backend.\n\n"
            "☁️ Requests go to the configured endpoint.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "Unknown backend. Use `/model local` or `/model cloud`."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    await update.message.chat.send_action("typing")
    response = SESSION.chat(user_id, text)
    if len(response) > 4000:
        response = response[:4000] + "\n\n... (truncated)"
    await update.message.reply_text(response)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")


# ─── Entry point ────────────────────────────────────────────────
def main():
    print("🎯 Starting prompt-orchestrator with 5-layer memory...")

    if not ensure_backend():
        print(f"⚠️ Warning: backend '{current_model}' not reachable.")

    _ = MEMORY  # force memory init

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("subject", subject_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("findings", findings_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("skills", skills_command))
    app.add_handler(CommandHandler("phase", phase_command))
    app.add_handler(CommandHandler("model", model_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("✅ prompt-orchestrator running.")
    app.run_polling(poll_interval=1)


if __name__ == "__main__":
    main()
