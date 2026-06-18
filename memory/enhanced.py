"""
PromptOrchestrator Enhanced Memory Manager
Complete memory system with all Agent Zero-like features
"""

import os
import sys
import sqlite3
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Try to import optional dependencies
try:
    from memory.vector import VECTOR_MEMORY, VectorMemory
except:
    VECTOR_MEMORY = None
    VectorMemory = None

try:
    from skills.manager import SKILLS_MANAGER, SkillsManager
except:
    SKILLS_MANAGER = None
    SkillsManager = None

try:
    from knowledge.base import KNOWLEDGE_BASE, KnowledgeBase
except:
    KNOWLEDGE_BASE = None
    KnowledgeBase = None

try:
    from integration.web_search import WEB_SEARCH, WebSearch
except:
    WEB_SEARCH = None
    WebSearch = None


DATABASE_PATH = os.environ.get('DATABASE_PATH', './data/aios.db')


class EnhancedMemory:
    """
    Complete memory system for PromptOrchestrator.
    Integrates:
    - SQLite structured memory
    - Vector memory (FAISS)
    - Skills system
    - Knowledge base
    - Web search
    """
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_all_tables()
        
        # Initialize components
        self.vector = VECTOR_MEMORY
        self.skills = SKILLS_MANAGER
        self.knowledge = KNOWLEDGE_BASE
        self.web_search = WEB_SEARCH
        
        print("✅ Enhanced Memory System Initialized")
    
    def _init_all_tables(self):
        """Initialize all database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Core facts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS core_facts (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Engagement state
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engagement_state (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                target TEXT,
                scope TEXT,
                phase TEXT DEFAULT 'recon',
                current_task TEXT,
                findings_summary TEXT,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Episodes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                episode_type TEXT,
                content TEXT NOT NULL,
                tool_used TEXT,
                outcome TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Findings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                target TEXT,
                title TEXT NOT NULL,
                severity TEXT,
                description TEXT,
                proof_of_concept TEXT,
                remediation TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Conversation summaries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                key_points TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cross-engagement memories (shared across engagements)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cross_memories (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                importance INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tool execution history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_history (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                arguments TEXT,
                result_preview TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # === Core Facts (Semantic) ===
    
    def set_fact(self, key: str, value: str, category: str = 'general'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO core_facts (key, value, category, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?, category = ?, updated_at = ?
        ''', (key, value, category, datetime.now().isoformat(), 
              value, category, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        # Also add to vector memory
        if self.vector:
            self.vector.add(f"{key}: {value}", category, {'type': 'fact'})
    
    def get_fact(self, key: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM core_facts WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_facts_by_category(self, category: str) -> Dict[str, str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM core_facts WHERE category = ?', (category,))
        results = dict(cursor.fetchall())
        conn.close()
        return results
    
    # === Engagement State (Working Memory) ===
    
    def start_engagement(self, user_id: str, target: str, scope: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO engagement_state (user_id, target, scope, phase, last_active)
            VALUES (?, ?, ?, 'recon', ?)
        ''', (user_id, target, scope, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        self.record_episode(user_id, 'engagement_start', 
                          f"Started engagement on {target}", 'system', 'started')
        
        # Add to vector memory
        if self.vector:
            self.vector.add(f"Engagement started on {target}", 'engagement', 
                          {'target': target, 'scope': scope})
    
    def update_engagement(self, user_id: str, **kwargs):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clauses = ['last_active = ?']
        values = [datetime.now().isoformat()]
        
        for key, value in kwargs.items():
            set_clauses.append(f'{key} = ?')
            values.append(value)
        
        values.append(user_id)
        
        cursor.execute(f'''
            UPDATE engagement_state 
            SET {', '.join(set_clauses)}
            WHERE user_id = ?
        ''', values)
        
        conn.commit()
        conn.close()
    
    def get_engagement(self, user_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT target, scope, phase, current_task, findings_summary, last_active
            FROM engagement_state 
            WHERE user_id = ?
            ORDER BY last_active DESC
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'target': result[0],
                'scope': result[1],
                'phase': result[2],
                'current_task': result[3],
                'findings_summary': result[4],
                'last_active': result[5]
            }
        return None
    
    # === Findings ===
    
    def add_finding(self, user_id: str, target: str, title: str, 
                   severity: str, description: str, 
                   proof_of_concept: str = None, remediation: str = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO findings (user_id, target, title, severity, 
                                description, proof_of_concept, remediation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, target, title, severity, description, 
              proof_of_concept, remediation))
        
        finding_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Add to vector memory for semantic search
        if self.vector:
            self.vector.add(
                f"Finding: {title} - {severity} - {description}", 
                'finding',
                {'target': target, 'severity': severity}
            )
        
        self.record_episode(user_id, 'finding', 
                          f"Found: {title} ({severity})", 'finding', 'recorded')
        
        return finding_id
    
    def get_findings(self, user_id: str, target: str = None, 
                    severity: List[str] = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT id, target, title, severity, description, status FROM findings WHERE user_id = ?'
        params = [user_id]
        
        if target:
            query += ' AND target = ?'
            params.append(target)
        
        if severity:
            query += f' AND severity IN ({",".join(["?"] * len(severity))})'
            params.extend(severity)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [{'id': r[0], 'target': r[1], 'title': r[2], 
                 'severity': r[3], 'description': r[4], 'status': r[5]} 
                for r in results]
    
    # === Episodes (Episodic Memory) ===
    
    def record_episode(self, user_id: str, episode_type: str, content: str,
                      tool_used: str = None, outcome: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO episodes (user_id, episode_type, content, tool_used, outcome)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, episode_type, content, tool_used, outcome))
        
        conn.commit()
        conn.close()
        
        # Add to vector memory
        if self.vector:
            self.vector.add(content, episode_type, {'user_id': user_id, 'outcome': outcome})
    
    def get_recent_episodes(self, user_id: str, limit: int = 20) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT episode_type, content, tool_used, outcome, timestamp
            FROM episodes
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'type': r[0], 'content': r[1], 'tool': r[2], 
                 'outcome': r[3], 'timestamp': r[4]} for r in results]
    
    # === Cross-Engagement Memory ===
    
    def add_cross_memory(self, user_id: str, content: str, 
                        category: str = 'general', importance: int = 1):
        """Add a memory that persists across engagements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cross_memories (user_id, content, category, importance)
            VALUES (?, ?, ?, ?)
        ''', (user_id, content, category, importance))
        
        conn.commit()
        conn.close()
        
        if self.vector:
            self.vector.add(content, category, {'importance': importance})
    
    def get_cross_memories(self, user_id: str, category: str = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT content, category, importance, created_at
                FROM cross_memories
                WHERE user_id = ? AND category = ?
                ORDER BY importance DESC, created_at DESC
            ''', (user_id, category))
        else:
            cursor.execute('''
                SELECT content, category, importance, created_at
                FROM cross_memories
                WHERE user_id = ?
                ORDER BY importance DESC, created_at DESC
                LIMIT 50
            ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'content': r[0], 'category': r[1], 'importance': r[2], 'created_at': r[3]} 
                for r in results]
    
    # === Tool History ===
    
    def record_tool_use(self, user_id: str, tool_name: str, 
                       arguments: dict, result_preview: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tool_history (user_id, tool_name, arguments, result_preview)
            VALUES (?, ?, ?, ?)
        ''', (user_id, tool_name, json.dumps(arguments), result_preview[:500]))
        
        conn.commit()
        conn.close()
    
    def get_tool_history(self, user_id: str, tool_name: str = None, 
                        limit: int = 20) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if tool_name:
            cursor.execute('''
                SELECT tool_name, arguments, result_preview, timestamp
                FROM tool_history
                WHERE user_id = ? AND tool_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, tool_name, limit))
        else:
            cursor.execute('''
                SELECT tool_name, arguments, result_preview, timestamp
                FROM tool_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{'tool': r[0], 'args': json.loads(r[1]) if r[1] else {}, 
                 'result': r[2], 'timestamp': r[3]} for r in results]
    
    # === Summarization ===
    
    def summarize_conversation(self, user_id: str) -> str:
        """Create a summary of the conversation for long-term memory"""
        
        episodes = self.get_recent_episodes(user_id, limit=50)
        findings = self.get_findings(user_id)
        
        if not episodes:
            return None
        
        summary_parts = []
        
        tool_uses = [e for e in episodes if e['tool']]
        if tool_uses:
            tools = list(set(t['tool'] for t in tool_uses[:10]))
            summary_parts.append(f"Ran {len(tool_uses)} tools: {', '.join(tools)}")
        
        if findings:
            by_severity = {}
            for f in findings:
                by_severity[f['severity']] = by_severity.get(f['severity'], 0) + 1
            summary_parts.append(f"Found {len(findings)} vulnerabilities: {by_severity}")
        
        summary = "; ".join(summary_parts)
        
        # Save summary
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversation_summaries (user_id, summary, key_points)
            VALUES (?, ?, ?)
        ''', (user_id, summary, json.dumps([e['content'] for e in episodes[:10]])))
        conn.commit()
        conn.close()
        
        # Add to cross-engagement memory
        self.add_cross_memory(user_id, summary, 'summary', importance=2)
        
        return summary
    
    # === Context Builder (THE KEY FUNCTION) ===
    
    def build_context_prompt(self, user_id: str, include_skills: bool = True,
                           include_knowledge: bool = True,
                           include_web_search: bool = False,
                           query: str = None) -> str:
        """
        Build comprehensive context prompt - this is the secret sauce.
        Combines all memory layers into context for the agent.
        """
        
        context_parts = []
        
        # 1. Core facts
        facts = self.get_facts_by_category('orchestrator')
        if facts:
            context_parts.append("=== PENTESTER PROFILE ===")
            for key, value in facts.items():
                context_parts.append(f"{key}: {value}")
        
        # 2. Current engagement
        engagement = self.get_engagement(user_id)
        if engagement:
            context_parts.append("\n=== CURRENT ENGAGEMENT ===")
            context_parts.append(f"Target: {engagement['target']}")
            context_parts.append(f"Scope: {engagement['scope'] or 'Not defined'}")
            context_parts.append(f"Phase: {engagement['phase']}")
            if engagement['current_task']:
                context_parts.append(f"Current Task: {engagement['current_task']}")
        
        # 3. Recent findings
        findings = self.get_findings(user_id)
        if findings:
            context_parts.append("\n=== FINDINGS SO FAR ===")
            for f in findings[:10]:
                context_parts.append(f"[{f['severity']}] {f['title']}: {f['description'][:150]}...")
        
        # 4. Recent activity (what we did)
        episodes = self.get_recent_episodes(user_id, limit=10)
        if episodes:
            context_parts.append("\n=== RECENT ACTIVITY ===")
            for ep in reversed(episodes):
                context_parts.append(f"- {ep['timestamp'][:19]}: {ep['content'][:100]}")
        
        # 5. Tool history
        tool_history = self.get_tool_history(user_id, limit=10)
        if tool_history:
            context_parts.append("\n=== TOOLS USED ===")
            for t in tool_history:
                args_str = ', '.join(f"{k}={v}" for k, v in list(t['args'].items())[:2])
                context_parts.append(f"- {t['tool']}({args_str})")
        
        # 6. Cross-engagement memories
        cross_mems = self.get_cross_memories(user_id, category='summary')
        if cross_mems:
            context_parts.append("\n=== PAST ENGAGEMENTS ===")
            for mem in cross_mems[:5]:
                context_parts.append(f"- {mem['content']}")
        
        # 7. Vector similarity search (if query provided)
        if query and self.vector:
            try:
                similar = self.vector.search(query, k=3)
                if similar:
                    context_parts.append("\n=== RELATED MEMORIES ===")
                    for sim in similar:
                        context_parts.append(f"- {sim['content'][:200]}")
            except:
                pass
        
        # 8. Skills (dynamic based on query)
        if include_skills and self.skills and query:
            relevant_skills = self.skills.get_relevant_skills(query)
            if relevant_skills:
                skill_prompt = self.skills.build_skill_prompt(relevant_skills[:3])
                context_parts.append(f"\n{skill_prompt}")
        
        # 9. Knowledge base (OWASP Web, API, LLM, Smart Contract, Tools)
        if include_knowledge and self.knowledge:
            # Add ALL OWASP references
            owasp_web = self.knowledge.get_owasp_web()
            if owasp_web and 'not found' not in owasp_web.lower():
                context_parts.append("\n=== OWASP TOP 10 WEB (2021) ===")
                context_parts.append(owasp_web[:2500])
            
            owasp_api = self.knowledge.get_owasp_api()
            if owasp_api and 'not found' not in owasp_api.lower():
                context_parts.append("\n=== OWASP API SECURITY TOP 10 (2023) ===")
                context_parts.append(owasp_api[:2500])
            
            owasp_llm = self.knowledge.get_owasp_llm()
            if owasp_llm and 'not found' not in owasp_llm.lower():
                context_parts.append("\n=== OWASP TOP 10 FOR LLM (2025) ===")
                context_parts.append(owasp_llm[:2500])
            
            owasp_sc = self.knowledge.get_owasp_smart_contract()
            if owasp_sc and 'not found' not in owasp_sc.lower():
                context_parts.append("\n=== OWASP SMART CONTRACT TOP 10 (2026) ===")
                context_parts.append(owasp_sc[:2500])
            
            # Add available tools info
            context_parts.append("\n=== AVAILABLE SECURITY TOOLS ===")
            context_parts.append("""
RECONNAISSANCE: nmap, masscan, subfinder, amass, gobuster, ffuf, dirb, whatweb
VULNERABILITY SCANNING: nikto, nuclei, wapiti, skipfish, arachni, zap
EXPLOITATION: sqlmap, xsstrike, dalfox, commix, hydra, john, hashcat
API TESTING: httpx, httpie, postman
BROWSER AUTOMATION: browser-harness (stealth Chrome)
WEB PROXY: caido, burpsuite, owasp-zap
SMART CONTRACT: slither, mythril, echidna, foundry
""")
        
        # 10. Web search (optional - for latest CVE info)
        if include_web_search and self.web_search and query:
            # Only do this for specific queries
            if any(kw in query.lower() for kw in ['cve', 'vulnerability', 'exploit', 'latest']):
                search_results = self.web_search.search_and_format(query)
                context_parts.append(f"\n{search_results}")
        
        return '\n'.join(context_parts)
    
    # === Smart Search ===
    
    def semantic_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search memories semantically using vector search"""
        if self.vector:
            return self.vector.search(query, k=k)
        return []


# Create global instance
MEMORY = EnhancedMemory()