"""
prompt-orchestrator — Memory Manager
=====================================
Persistent memory across agent sessions.

Layers:
- Working Memory: current session context
- Episodic Memory: past interactions and items
- Semantic Memory: facts about the orchestrator, subjects, methodology
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

DATABASE_PATH = os.environ.get('DATABASE_PATH', './data/aios.db')


class MemoryManager:
    """
    Multi-layer memory system for prompt-orchestrator:
    - Working Memory: Current session context
    - Episodic Memory: Past interactions and items
    - Semantic Memory: Facts about the orchestrator, subjects, methodology
    """
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_memory_tables()
    
    def _init_memory_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Core facts - semantic memory
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS core_facts (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Engagement state - current working memory
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engagement_state (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                target TEXT,
                scope TEXT,
                phase TEXT DEFAULT 'discover',
                current_task TEXT,
                findings_summary TEXT,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Episodic memory - past interactions
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
        
        # Findings database
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
        
        conn.commit()
        conn.close()
    
    # === Core Facts (Semantic Memory) ===
    
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
            VALUES (?, ?, ?, 'discover', ?)
        ''', (user_id, target, scope, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        self.record_episode(user_id, 'engagement_start', 
                          f"Started engagement on {target}", 'system', 'started')
    
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
    
    def add_finding(self, user_id: str, target: str, title: str, 
                   severity: str, description: str, 
                   proof_of_concept: str = None, remediation: str = None):
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
    
    # === Context Builder ===
    
    def build_context_prompt(self, user_id: str) -> str:
        """Build a comprehensive context prompt for the agent"""
        
        context_parts = []
        
        # Core facts
        facts = self.get_facts_by_category('orchestrator')
        if facts:
            context_parts.append("=== PENTESTER PROFILE ===")
            for key, value in facts.items():
                context_parts.append(f"{key}: {value}")
        
        # Current engagement
        engagement = self.get_engagement(user_id)
        if engagement:
            context_parts.append("\n=== CURRENT ENGAGEMENT ===")
            context_parts.append(f"Target: {engagement['target']}")
            context_parts.append(f"Scope: {engagement['scope'] or 'Not defined'}")
            context_parts.append(f"Phase: {engagement['phase']}")
            if engagement['current_task']:
                context_parts.append(f"Current Task: {engagement['current_task']}")
        
        # Recent findings
        findings = self.get_findings(user_id)
        if findings:
            context_parts.append("\n=== FINDINGS SO FAR ===")
            for f in findings[:10]:
                context_parts.append(f"[{f['severity']}] {f['title']}: {f['description'][:200]}...")
        
        # Recent episodes (what we did)
        episodes = self.get_recent_episodes(user_id, limit=10)
        if episodes:
            context_parts.append("\n=== RECENT ACTIVITY ===")
            for ep in reversed(episodes):
                context_parts.append(f"- {ep['timestamp']}: {ep['content']}")
        
        return '\n'.join(context_parts)
    
    # === Summarization ===
    
    def summarize_conversation(self, user_id: str):
        """Create a summary of the conversation for long-term memory"""
        
        episodes = self.get_recent_episodes(user_id, limit=50)
        findings = self.get_findings(user_id)
        
        if not episodes:
            return None
        
        summary_parts = []
        
        # Summarize activity
        tool_uses = [e for e in episodes if e['tool']]
        if tool_uses:
            summary_parts.append(f"Ran {len(tool_uses)} tools: {', '.join(set(t['tool'] for t in tool_uses[:5]))}")
        
        # Summarize findings
        if findings:
            by_severity = {}
            for f in findings:
                by_severity[f['severity']] = by_severity.get(f['severity'], 0) + 1
            summary_parts.append(f"Found {len(findings)} vulnerabilities: {by_severity}")
        
        summary = "; ".join(summary_parts)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversation_summaries (user_id, summary, key_points)
            VALUES (?, ?, ?)
        ''', (user_id, summary, json.dumps([e['content'] for e in episodes[:10]])))
        conn.commit()
        conn.close()
        
        return summary


MEMORY = MemoryManager()