#!/usr/bin/env python3
"""
PromptOrchestrator Knowledge Base - Persistent memory across sessions
Stores target history, CVE cache, successful techniques, and learned patterns
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import re

class KnowledgeBase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.expanduser("~/.prompt_orchestrator/knowledge.db")
        
        # Expand the path
        db_path = os.path.expanduser(db_path)
        
        # Create directory
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Target history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                first_seen TEXT,
                last_seen TEXT,
                scope TEXT,
                notes TEXT,
                risk_level TEXT
            )
        """)
        
        # Findings per target
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                finding_type TEXT,
                severity TEXT,
                title TEXT,
                description TEXT,
                poc TEXT,
                status TEXT,
                discovered TEXT,
                patched TEXT,
                FOREIGN KEY (target_id) REFERENCES targets(id)
            )
        """)
        
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Services found
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                host TEXT,
                port INTEGER,
                service TEXT,
                version TEXT,
                state TEXT,
discovered TEXT
            )
        """)
        
        # Services found
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                host TEXT,
                port INTEGER,
                service TEXT,
                version TEXT,
                state TEXT,
                discovered TEXT
            )
        """)
        
        # Credentials found
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                username TEXT,
                password TEXT,
                hash TEXT,
                type TEXT,
                source TEXT
            )
        """)
        
        # Successful techniques
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS techniques (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                technique TEXT,
                description TEXT,
                success_score INTEGER,
                last_used TEXT
            )
        """)
        
        # CVE cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cve_cache (
                cve_id TEXT PRIMARY KEY,
                description TEXT,
                severity TEXT,
                cvss REAL,
                published TEXT,
                affected TEXT,
                refs TEXT,
                updated TEXT
            )
        """)
        
        # Target state (for resume)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pentest_state (
                target_id INTEGER PRIMARY KEY,
                phase TEXT,
                data TEXT,
                updated TEXT
            )
        """)
        
        # Tool definitions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                definition TEXT,
                created TEXT
            )
        """)
        
        # Notes / context
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                content TEXT,
                created TEXT
            )
        """)
        
        # Credentials found
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                username TEXT,
                password TEXT,
                hash TEXT,
                type TEXT,
                source TEXT,
                FOREIGN KEY (target_id) REFERENCES targets(id)
            )
        """)
        
        # Successful techniques
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS techniques (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                technique TEXT,
                description TEXT,
                success_score INTEGER,
                last_used TEXT
            )
        """)
        
        # CVE cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cve_cache (
                cve_id TEXT PRIMARY KEY,
                description TEXT,
                severity TEXT,
                cvss REAL,
                published TEXT,
                affected TEXT,
                refs TEXT,
                updated TEXT
            )
        """)
        
        # Target state (for resume)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pentest_state (
                target_id INTEGER PRIMARY KEY,
                phase TEXT,
                data TEXT,
                updated TEXT,
                FOREIGN KEY (target_id) REFERENCES targets(id)
            )
        """)
        
        # Tool definitions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                definition TEXT,
                created TEXT
            )
        """)
        
        # Notes / context
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                content TEXT,
                created TEXT,
                FOREIGN KEY (target_id) REFERENCES targets(id)
            )
        """)
        
        self.conn.commit()
    
    # Target operations
    def add_target(self, name: str, scope: str = None, notes: str = None) -> int:
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO targets (name, first_seen, last_seen, scope, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (name, now, now, scope, notes))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_target(self, name: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM targets WHERE name = ?", (name,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "first_seen": row[2],
            "last_seen": row[3],
            "scope": row[4],
            "notes": row[5],
            "risk_level": row[6]
        }
    
    def update_target_seen(self, name: str):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("UPDATE targets SET last_seen = ? WHERE name = ?", (now, name))
        self.conn.commit()
    
    def list_targets(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM targets ORDER BY last_seen DESC")
        return cursor.fetchall()
    
    # Finding operations
    def add_finding(self, target_id: int, finding_type: str, severity: str, 
                  title: str, description: str = None, poc: str = None, status: str = "open"):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO findings (target_id, finding_type, severity, title, description, poc, status, discovered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (target_id, finding_type, severity, title, description, poc, status, now))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_findings(self, target_id: int) -> list:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM findings WHERE target_id = ? ORDER BY 
            CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END
        """, (target_id,))
        return cursor.fetchall()
    
    def mark_finding_patched(self, finding_id: str):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE findings SET status = 'patched', patched = ? WHERE id = ?
        """, (now, finding_id))
        self.conn.commit()
    
    # Service operations
    def add_service(self, target_id: int, host: str, port: int, service: str, 
                  version: str = None, state: str = "open"):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO services (target_id, host, port, service, version, state, discovered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (target_id, host, port, service, version, state, now))
        self.conn.commit()
    
    def get_services(self, target_id: int) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM services WHERE target_id = ?", (target_id,))
        return cursor.fetchall()
    
    # Credential operations
    def add_credential(self, target_id: int, username: str, password: str = None, 
                    hash: str = None, type: str = " plaintext", source: str = None):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO credentials (target_id, username, password, hash, type, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (target_id, username, password, hash, type, source))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_credentials(self, target_id: int) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM credentials WHERE target_id = ?", (target_id,))
        return cursor.fetchall()
    
    # State operations
    def save_state(self, target_id: int, phase: str, data: dict):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO pentest_state (target_id, phase, data, updated)
            VALUES (?, ?, ?, ?)
        """, (target_id, phase, json.dumps(data), now))
        self.conn.commit()
    
    def load_state(self, target_id: int) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT phase, data FROM pentest_state WHERE target_id = ?", (target_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {"phase": row[0], "data": json.loads(row[1])}
    
    def get_state_phase(self, target_id: int) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT phase FROM pentest_state WHERE target_id = ?", (target_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    # Technique tracking
    def add_technique(self, target_id: int, technique: str, description: str = None, success: bool = True):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        
        # Check if exists
        cursor.execute("""
            SELECT id FROM techniques WHERE target_id = ? AND technique = ?
        """, (target_id, technique))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE techniques SET success_score = success_score + 1, last_used = ?
                WHERE id = ?
            """, (now, existing[0]))
        else:
            cursor.execute("""
                INSERT INTO techniques (target_id, technique, description, success_score, last_used)
                VALUES (?, ?, ?, ?, ?)
            """, (target_id, technique, description, 1 if success else 0, now))
        self.conn.commit()
    
    def get_successful_techniques(self, target_id: int) -> list:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM techniques WHERE target_id = ? AND success_score > 0
            ORDER BY success_score DESC
        """, (target_id,))
        return cursor.fetchall()
    
    # CVE cache operations
    def add_cve(self, cve_id: str, description: str, severity: str, 
               cvss: float, published: str, affected: str = None, refs: str = None):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cve_cache 
            (cve_id, description, severity, cvss, published, affected, references, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cve_id, description, severity, cvss, published, affected, refs, now))
        self.conn.commit()
    
    def get_cve(self, cve_id: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cve_cache WHERE cve_id = ?", (cve_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "cve_id": row[0],
            "description": row[1],
            "severity": row[2],
            "cvss": row[3],
            "published": row[4],
            "affected": row[5],
            "references": row[6],
            "updated": row[7]
        }
    
    def search_cve(self, query: str) -> list:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM cve_cache 
            WHERE cve_id LIKE ? OR description LIKE ? OR affected LIKE ?
            ORDER BY cvss DESC
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return cursor.fetchall()
    
    # Tool operations
    def save_tool(self, name: str, definition: dict):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO tools (name, definition, created)
            VALUES (?, ?, ?)
        """, (name, json.dumps(definition), now))
        self.conn.commit()
    
    def get_tool(self, name: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT definition FROM tools WHERE name = ?", (name,))
        row = cursor.fetchone()
        if not row:
            return None
        return json.loads(row[0])
    
    def list_tools(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, definition FROM tools")
        return [(r[0], json.loads(r[1])) for r in cursor.fetchall()]
    
    def delete_tool(self, name: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tools WHERE name = ?", (name,))
        self.conn.commit()
    
    # Notes
    def add_note(self, target_id: int, content: str):
        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO notes (target_id, content, created)
            VALUES (?, ?, ?)
        """, (target_id, content, now))
        self.conn.commit()
    
    def get_notes(self, target_id: int) -> list:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE target_id = ? ORDER BY created DESC", (target_id,))
        return cursor.fetchall()
    
    # Search across everything
    def search(self, query: str, target_name: str = None) -> dict:
        results = {
            "targets": [],
            "findings": [],
            "services": [],
            "cves": []
        }
        
        if target_name:
            target = self.get_target(target_name)
            if not target:
                return results
            target_id = target["id"]
            
            # Find findings
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM findings WHERE target_id = ? AND (
                    title LIKE ? OR description LIKE ?
                )
            """, (target_id, f"%{query}%", f"%{query}%"))
            results["findings"] = cursor.fetchall()
            
            # Find services
            cursor.execute("""
                SELECT * FROM services WHERE target_id = ? AND (
                    service LIKE ? OR version LIKE ?
                )
            """, (target_id, f"%{query}%", f"%{query}%"))
            results["services"] = cursor.fetchall()
        
        # Search CVE cache
        results["cves"] = self.search_cve(query)
        
        return results
    
    def close(self):
        self.conn.close()

    # ─── Generic vocabulary aliases (prompt-orchestrator rebrand) ──
    # Same logic, neutral naming. Original methods are kept for any
    # existing callers.

    def add_subject(self, name: str, scope: str = None, notes: str = None) -> int:
        return self.add_target(name, scope, notes)

    def get_subject(self, name: str):
        return self.get_target(name)

    def list_subjects(self) -> list:
        return self.list_targets()

    def get_reference(self, ref_id: str):
        return self.get_cve(ref_id)

    def search_reference(self, query: str) -> list:
        return self.search_cve(query)


# Simple CLI interface
def main():
    import sys
    kb = KnowledgeBase()
    
    if len(sys.argv) < 2:
        print("PromptOrchestrator Knowledge Base")
        print("Usage: python -m knowledge <command> [args]")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "target":
        if len(sys.argv) < 3:
            print("Targets:", kb.list_targets())
        else:
            name = sys.argv[2]
            target = kb.get_target(name)
            if target:
                print(f"Target: {target}")
                print(f"Findings: {kb.get_findings(target['id'])}")
                print(f"Services: {kb.get_services(target['id'])}")
            else:
                print(f"Target {name} not found")
    
    elif cmd == "add":
        name = sys.argv[2]
        scope = sys.argv[3] if len(sys.argv) > 3 else None
        kb.add_target(name, scope)
        print(f"Added target: {name}")
    
    elif cmd == "state":
        target = kb.get_target(sys.argv[2])
        if not target:
            print(f"Target {sys.argv[2]} not found")
            return
        state = kb.load_state(target['id'])
        print(f"State: {state}")
    
    elif cmd == "cve":
        if len(sys.argv) < 3:
            print("Usage: knowledge cve <cve-id>")
            return
        cve = kb.get_cve(sys.argv[2])
        print(f"CVE: {cve}")
    
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: knowledge search <query>")
            return
        results = kb.search(sys.argv[2])
        print(f"Results: {results}")
    
    else:
        print(f"Unknown command: {cmd}")
    
    kb.close()


if __name__ == "__main__":
    main()