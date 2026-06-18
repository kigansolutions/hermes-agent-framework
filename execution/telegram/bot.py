import os
import json
import re
import requests
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from tools.registry import TOOL_SCHEMAS, TOOL_REGISTRY

load_dotenv()

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen3:14b')
DATABASE_PATH = os.environ.get('DATABASE_PATH', './data/aios.db')

MAX_TOOL_CALLS = 5

def load_context():
    context_files = {
        'business': './context/business.md',
        'products': './context/products.md',
        'processes': './context/processes.md',
        'goals': './context/goals.md'
    }
    
    context_parts = ["# Context OS\n"]
    for name, path in context_files.items():
        if os.path.exists(path):
            with open(path, 'r') as f:
                context_parts.append(f"## {name.upper()}\n{f.read()}\n")
    
    return '\n'.join(context_parts)

def load_recent_conversation(user_id, limit=10):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT role, message FROM conversations 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (str(user_id), limit))
    
    messages = cursor.fetchall()
    conn.close()
    
    return list(reversed(messages))

def save_message(user_id, role, message):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO conversations (user_id, role, message)
        VALUES (?, ?, ?)
    ''', (str(user_id), role, message))
    
    conn.commit()
    conn.close()

def chat_with_ollama(messages, tools=None):
    payload = {
        'model': OLLAMA_MODEL,
        'messages': messages,
        'stream': False,
    }
    
    if tools:
        payload['tools'] = tools
    
    try:
        response = requests.post(
            f'{OLLAMA_BASE_URL}/api/chat',
            json=payload,
            timeout=180
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f"HTTP {response.status_code}", 'message': {'content': response.text}}
    except Exception as e:
        return {'error': str(e), 'message': {'content': f"Connection error: {str(e)}"}}

def parse_tool_calls(response_json):
    message = response_json.get('message', {})
    
    tool_calls = message.get('tool_calls', [])
    
    if not tool_calls and 'function_call' in message:
        tool_calls = [message['function_call']]
    
    return tool_calls

def execute_tool_calls(tool_calls):
    results = []
    
    for tool_call in tool_calls:
        if isinstance(tool_call, dict):
            func_name = tool_call.get('function', {}).get('name', '')
            arguments = tool_call.get('function', {}).get('arguments', '{}')
        else:
            continue
        
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except:
                arguments = {}
        
        result = TOOL_REGISTRY.execute_tool(func_name, arguments)
        
        results.append({
            'tool_call_id': tool_call.get('id', 'unknown'),
            'name': func_name,
            'result': result[:3000]
        })
    
    return results

def run_agent(user_id, user_message, context_text):
    system_prompt = f"""You are a professional workflow assistant for prompt-orchestrator. You have access to a registry of CLI tools and orchestrate multi-phase workflows across domains.

{context_text}

Your role is to:
1. Help plan and execute multi-phase workflows on any subject
2. Run discovery tools (whois, DNS, HTTP probes, port scans, etc.)
3. Analyze tool output and identify actionable items
4. Produce structured output (findings, drafts, builds)
5. Document outcomes

AVAILABLE TOOLS (sample — see registry):
- run_whois: Domain / identifier registration lookup
- run_dig: DNS query
- run_curl: HTTP request
- check_port: TCP port check
- grab_banner: Service banner grab
- run_http_methods: Discover allowed HTTP methods
- resolve_hostname: DNS resolve

IMPORTANT RULES:
- Only use tools when necessary to gather information
- Always operate within explicit scope authorization
- Always explain what you're doing before running tools
- Analyze tool output thoroughly before reporting results
- Prefer safe, non-destructive operations first

When a user asks you to assess or analyze something, use the appropriate tools to gather information and analyze results. If they ask about something you need more information on, ask follow-up questions."""

    messages = [{'role': 'system', 'content': system_prompt}]
    
    history = load_recent_conversation(user_id)
    for role, msg in history:
        messages.append({'role': role, 'content': msg})
    
    messages.append({'role': 'user', 'content': user_message})
    
    tool_call_count = 0
    final_response = None
    
    while tool_call_count < MAX_TOOL_CALLS:
        response = chat_with_ollama(messages, TOOL_SCHEMAS)
        
        if 'error' in response:
            return f"Error: {response['error']}"
        
        assistant_message = response.get('message', {})
        content = assistant_message.get('content', '')
        
        tool_calls = parse_tool_calls(response)
        
        if tool_calls:
            tool_call_count += 1
            
            messages.append({'role': 'assistant', 'content': content})
            if content:
                messages.append({'role': 'assistant', 'content': str(tool_calls)})
            
            tool_results = execute_tool_calls(tool_calls)
            
            for tr in tool_results:
                result_msg = f"Tool: {tr['name']}\nResult:\n{tr['result']}"
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tr.get('tool_call_id', 'unknown'),
                    'content': tr['result']
                })
            
            if content.strip():
                final_response = content + "\n\n" + "\n\n".join([f"Executing {tr['name']}..." for tr in tool_results])
            else:
                final_response = "\n\n".join([f"Executing {tr['name']}..." for tr in tool_results])
        else:
            final_response = content
            messages.append({'role': 'assistant', 'content': content})
            break
    
    return final_response or "No response generated"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 *prompt-orchestrator — Workflow Assistant*\n\n"
        "AI-powered multi-phase workflow orchestration over a registry of CLI tools.\n\n"
        "I can help you with:\n"
        "• Discovery (whois, DNS, HTTP probes, port checks)\n"
        "• Analysis (banners, response parsing, reference lookup)\n"
        "• Web probing (curl, headers, HTTP methods)\n"
        "• Information gathering (DNS, registry, ASN)\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/tools - List available tools\n"
        "/scope <target> - Set the working subject\n"
        "/help - Show help\n\n"
        "Just describe what you want to do in plain language.",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Available Commands*\n\n"
        "/start - Start the bot\n"
        "/tools - Show available workflow tools\n"
        "/scope <target> - Define working subject\n"
        "/help - Show this help\n\n"
        "Example queries:\n"
        "• \"Look up the WHOIS record for example.com\"\n"
        "• \"Check which HTTP methods example.com allows\"\n"
        "• \"Resolve the hostname api.example.com\"\n"
        "• \"Check if port 443 is open on example.com\"",
        parse_mode='Markdown'
    )

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tools_list = """
🔧 *Available Tools*

*Discovery:*
• `run_whois` — Registration / identifier lookup
• `run_dig` — DNS query
• `resolve_hostname` — DNS resolve
• `check_port` — TCP port check

*Web Probing:*
• `run_curl` — HTTP request
• `grab_banner` — Service banner
• `run_http_methods` — Allowed HTTP methods
"""
    await update.message.reply_text(tools_list, parse_mode='Markdown')

async def scope_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /scope <target>")
        return
    
    target = ' '.join(context.args)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO metrics (name, value, unit, category, recorded_at) 
        VALUES (?, ?, ?, ?, ?)
    ''', ('scope_target', target, 'domain', 'scope', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Target scope set to: `{target}`", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    save_message(user_id, 'user', text)
    
    await update.message.chat.send_action('typing')
    
    context_text = load_context()
    response = run_agent(user_id, text, context_text)
    
    save_message(user_id, 'assistant', response[:4000])
    
    await update.message.reply_text(response[:4000])

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")

def main():
    print("🎯 Starting prompt-orchestrator bot...")
    print(f"Using model: {OLLAMA_MODEL}")
    print(f"Ollama endpoint: {OLLAMA_BASE_URL}")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("tools", tools_command))
    app.add_handler(CommandHandler("scope", scope_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(error_handler)

    print("✅ Bot started! Press Ctrl+C to stop.")
    app.run_polling(poll_interval=1)

if __name__ == '__main__':
    main()