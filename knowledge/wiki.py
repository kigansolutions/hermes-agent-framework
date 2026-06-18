#!/usr/bin/env python3
"""
prompt-orchestrator — Knowledge Wiki
======================================
Persistent markdown wiki with incremental synthesis — the
Karpathy LLM-Wiki pattern adapted for runtime reference data.

Concepts:
- Sources: immutable inputs (scan results, CVE feeds, findings)
- Wiki: synthesized markdown pages (summaries, entity pages)
- Schema: configuration telling the LLM how to maintain the wiki

The wiki compounds over time rather than re-deriving from scratch
each session.
"""

import json
import os
import re
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

class KnowledgeWiki:
    def __init__(self, wiki_path: str = None):
        """
        Initialize LLM Wiki at specified path.
        
        Structure:
        wiki/
        ├── raw/           # Immutable sources
        ├── wiki/          # LLM-generated pages
        ├── schema.md      # Schema for LLM agent
        ├── index.md       # Catalog of wiki pages
        └── log.md        # Chronological activity log
        """
        if wiki_path is None:
            wiki_path = os.path.expanduser("~/.prompt_orchestrator/wiki")
        
        self.wiki_path = Path(wiki_path)
        self.raw_path = self.wiki_path / "raw"
        self.wiki_pages_path = self.wiki_path / "wiki"
        
        # Create directories
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.wiki_pages_path.mkdir(parents=True, exist_ok=True)
        
        # Path to index and log
        self.index_path = self.wiki_path / "index.md"
        self.log_path = self.wiki_path / "log.md"
        self.schema_path = self.wiki_path / "schema.md"
        
        # Initialize files
        self._init_files()
        
        # Initialize database for structured data
        self.db_path = os.path.expanduser("~/.prompt_orchestrator/knowledge.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()
    
    def _init_files(self):
        """Initialize index, log, and schema files"""
        # Create index if not exists
        if not self.index_path.exists():
            self.index_path.write_text("""# Wiki Index

## Overview
This is the prompt-orchestrator knowledge wiki - a persistent, compounding reference base.

## Categories
- [[Targets]] - Pentest targets and their history
- [[Findings]] - Vulnerabilities discovered
- [[Techniques]] - Successful exploitation techniques
- [[CVEs]] - CVE database
- [[Tools]] - Tool definitions and usage
- [[Credentials]] - Harvested credentials

## Recent Pages
(Last updated: {datetime.now().isoformat()})
""")
        
        # Create log if not exists
        if not self.log_path.exists():
            self.log_path.write_text("""# Activity Log

Append-only record of wiki activity.

## Format
Use `## [YYYY-MM-DD] <operation> | <description>` format for parseable entries.

""")
        
        # Create schema if not exists
        if not self.schema_path.exists():
            self.schema_path.write_text("""# prompt-orchestrator Wiki Schema

## Architecture
- **raw/** - Immutable source documents (scan outputs, CVE feeds)
- **wiki/** - LLM-generated markdown pages
- **index.md** - Catalog of wiki pages
- **log.md** - Activity log

## Page Types

### Entity Pages
Target pages, vulnerability pages, technique pages.
Format: `[target-name].md`, `[cve-id].md`, `[technique-name].md`

### Concept Pages
Synthesized pages combining multiple sources.
Format: `[concept-name].md`

### Summary Pages
Brief overviews of targets or topics.
Format: `[topic]-summary.md`

## Operations

### Ingest
1. Read source file
2. Extract key information
3. Create/update entity pages
4. Update index.md
5. Append to log.md

### Query
1. Read index.md to find relevant pages
2. Read relevant pages
3. Synthesize answer
4. File useful answers as new pages

### Lint
1. Check for contradictions
2. Check for stale information
3. Check for orphan pages
4. Check for missing cross-references

## Cross-Reference Format
Use double-bracket links: `[[Target Name]]`
Use CVE links: `CVE-2021-1234`

## Naming Conventions
- Targets: lowercase with dashes: `target-com.md`
- CVEs: standard format: `CVE-2021-41773.md`
- Techniques: lowercase with dashes: `sql-injection.md`
""")
    
    def _init_db(self):
        """Initialize database"""
        cursor = self.conn.cursor()
        
        # Targets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                first_seen TEXT,
                last_seen TEXT,
                risk_level TEXT
            )
        """)
        
        # Findings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY,
                target_id INTEGER,
                severity TEXT,
                title TEXT,
                description TEXT,
                poc TEXT,
                status TEXT DEFAULT 'open'
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
                affected TEXT
            )
        """)
        
        self.conn.commit()
    
    # ========================================
    # INGEST OPERATIONS
    # ========================================
    
    def ingest_nmap(self, target: str, output: str) -> dict:
        """Ingest nmap scan results"""
        self._log("ingest", f"nmap scan for {target}")
        
        # Parse nmap output (simplified - grep for open ports)
        open_ports = []
        for line in output.split('\n'):
            match = re.match(r'(\d+)/(tcp|udp)\s+open\s+(\S+)\s+(.+)', line)
            if match:
                port, proto, service, version = match.groups()
                open_ports.append({
                    "port": port,
                    "protocol": proto,
                    "service": service,
                    "version": version.strip()
                })
                
                # Save to DB
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO services (target_id, host, port, service, version, state, discovered)
                    VALUES ((SELECT id FROM targets WHERE name = ?), ?, ?, ?, ?, 'open', ?)
                """, (target, target, port, service, version, datetime.now().isoformat()))
        
        self.conn.commit()
        
        # Create/update target wiki page
        self._update_target_page(target, open_ports)
        self._update_index()
        self._log("ingest", f"nmap: {len(open_ports)} services")
        
        return {"services": open_ports}
    
    def ingest_nuclei(self, target: str, findings: list) -> dict:
        """Ingest nuclei scan results"""
        self._log("ingest", f"nuclei scan for {target}")
        
        # Save findings to DB
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM targets WHERE name = ?", (target,))
        row = cursor.fetchone()
        
        if not row:
            cursor.execute("INSERT INTO targets (name, first_seen, last_seen) VALUES (?, ?, ?)",
                        (target, datetime.now().isoformat(), datetime.now().isoformat()))
            cursor.execute("SELECT id FROM targets WHERE name = ?", (target,))
            row = cursor.fetchone()
        
        target_id = row[0]
        
        saved = []
        for f in findings:
            cursor.execute("""
                INSERT INTO findings (target_id, severity, title, description, status)
                VALUES (?, ?, ?, ?, 'open')
            """, (target_id, f.get('severity', 'medium'), f.get('title', 'Unknown'), f.get('description', '')))
            saved.append(f.get('title'))
        
        self.conn.commit()
        
        # Create finding pages
        for f in findings:
            self._create_finding_page(target, f)
        
        self._update_index()
        self._log("ingest", f"nuclei: {len(findings)} findings")
        
        return {"findings": saved}
    
    def ingest_cve(self, cve_id: str, data: dict):
        """Ingest CVE data"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cve_cache (cve_id, description, severity, cvss, published, affected)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cve_id, data.get('description', ''), data.get('severity', 'UNKNOWN'),
             data.get('cvss', 0.0), data.get('published', ''), data.get('affected', '')))
        self.conn.commit()
        
        # Create CVE wiki page
        self._create_cve_page(cve_id, data)
        self._update_index()
        self._log("ingest", f"CVE {cve_id}")
    
    # ========================================
    # WIKI PAGE OPERATIONS
    # ========================================
    
    def _update_target_page(self, target: str, services: list):
        """Create/update target wiki page"""
        filename = f"{target.replace('.', '-')}.md"
        page_path = self.wiki_pages_path / filename
        
        # Get existing findings
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM targets WHERE name = ?", (target,))
        row = cursor.fetchone()
        
        findings = []
        if row:
            cursor.execute("SELECT title, severity FROM findings WHERE target_id = ?", (row[0],))
            findings = cursor.fetchall()
        
        content = f"""# {target}

## Overview
Target discovered: {datetime.now().strftime('%Y-%m-%d')}

## Services
| Port | Service | Version |
|------|---------|---------|
"""
        for s in services:
            content += f"| {s['port']} | {s['service']} | {s.get('version', 'N/A')} |\n"
        
        content += f"""
## Findings
| Severity | Title |
|----------|-------|
"""
        for f in findings:
            content += f"| {f[1]} | {f[0]} |\n"
        
        content += """
## Notes
- Add notes here

## Related
- [[CVEs]] - Related CVEs
- [[Techniques]] - Techniques for this target
"""
        
        page_path.write_text(content)
    
    def _create_finding_page(self, target: str, finding: dict):
        """Create vulnerability page"""
        # Sanitize title for filename
        title_clean = re.sub(r'[^a-zA-Z0-9]', '-', finding.get('title', 'unknown'))
        filename = f"{target.replace('.', '-')}-{title_clean[:50]}.md"
        page_path = self.wiki_pages_path / filename
        
        content = f"""# {finding.get('title', 'Unknown')}

## Target
[[{target}]]

## Severity
{finding.get('severity', 'medium').upper()}

## Description
{finding.get('description', 'N/A')}

## Proof of Concept
```
{finding.get('poc', 'No POC available')}
```

## References
{finding.get('references', '')}

## Related
- [[{target}]] - Target page
- [[Findings]] - All findings
"""
        
        page_path.write_text(content)
    
    def _create_cve_page(self, cve_id: str, data: dict):
        """Create CVE wiki page"""
        filename = f"{cve_id.replace(':', '-')}.md"
        page_path = self.wiki_pages_path / filename
        
        content = f"""# {cve_id}

## Severity
{data.get('severity', 'UNKNOWN').upper()} (CVSS: {data.get('cvss', 'N/A')})

## Description
{data.get('description', 'N/A')}

## Affected
{data.get('affected', 'Unknown')}

## Published
{data.get('published', 'Unknown')}

## References
- {data.get('references', 'N/A')}

## Related
- [[Vulnerabilities]] - All vulnerabilities
"""
        
        page_path.write_text(content)
    
    def _update_index(self):
        """Update index.md with current wiki pages"""
        pages = []
        
        for f in self.wiki_pages_path.glob("*.md"):
            rel_path = f"wiki/{f.name}"
            content = f.read_text()
            
            # Get first heading
            heading = "Untitled"
            match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if match:
                heading = match.group(1)
            
            # Get last modified
            modified = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d')
            
            pages.append((rel_path, heading, modified))
        
        # Sort by modified date
        pages.sort(key=lambda x: x[2], reverse=True)
        
        # Write index
        content = """# Wiki Index

## Overview
prompt-orchestrator persistent knowledge base.

## Pages
| Page | Title | Modified |
|------|-------|----------|
"""
        for path, title, modified in pages:
            content += f"| [{path}]({path}) | {title} | {modified} |\n"
        
        content += f"""
## Stats
- Total pages: {len(pages)}
- Last updated: {datetime.now().isoformat()}

## Operations
- Ingest: Add new scan results
- Query: Search wiki pages
- Lint: Health check
"""
        
        self.index_path.write_text(content)
    
    def _log(self, operation: str, description: str):
        """Append to activity log"""
        entry = f"\n## [{datetime.now().strftime('%Y-%m-%d')}] {operation} | {description}"
        
        with open(self.log_path, "a") as f:
            f.write(entry)
    
    # ========================================
    # QUERY OPERATIONS
    # ========================================
    
    def search(self, query: str) -> list:
        """Search wiki for query"""
        results = []
        
        for f in self.wiki_pages_path.glob("*.md"):
            content = f.read_text()
            if query.lower() in content.lower():
                results.append({
                    "file": f.name,
                    "path": str(f)
                })
        
        return results
    
    def get_page(self, name: str) -> str:
        """Get wiki page content"""
        # Try different extensions
        for ext in ['.md', '']:
            page_path = self.wiki_pages_path / f"{name}{ext}"
            if page_path.exists():
                return page_path.read_text()
        
        return None
    
    def get_target_summary(self, target: str) -> dict:
        """Get target summary"""
        # Load from DB
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM targets WHERE name = ?", (target,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        target_id = row[0]
        
        # Get findings
        cursor.execute("SELECT COUNT(*) FROM findings WHERE target_id = ?", (target_id,))
        finding_count = cursor.fetchone()[0]
        
        # Get critical findings
        cursor.execute("SELECT COUNT(*) FROM findings WHERE target_id = ? AND severity = 'critical'", (target_id,))
        critical = cursor.fetchone()[0]
        
        return {
            "name": target,
            "first_seen": row[2],
            "last_seen": row[3],
            "risk_level": row[4],
            "findings_total": finding_count,
            "findings_critical": critical
        }
    
    # ========================================
    # LINT OPERATIONS  
    # ========================================
    
    def lint(self) -> dict:
        """Health check the wiki"""
        issues = {
            "orphans": [],
            "stale": [],
            "missing_refs": [],
            "duplicates": []
        }
        
        # Find orphan pages (no links to them)
        all_content = ""
        for f in self.wiki_pages_path.glob("*.md"):
            all_content += f.read_text() + "\n"
        
        for f in self.wiki_pages_path.glob("*.md"):
            content = f.read_text()
            
            # Check for broken links (simple check)
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            for link in links:
                # Check if target exists
                link_file = self.wiki_pages_path / f"{link.replace('[', '').replace(']', '')}.md"
                if not link_file.exists() and not link.startswith('http'):
                    issues["missing_refs"].append(f"{f.name} -> {link}")
            
            # Check for stale (no updates in 30 days)
            age_days = (datetime.now().timestamp() - f.stat().st_mtime) / 86400
            if age_days > 30 and "summary" not in f.name:
                issues["stale"].append(f.name)
        
        # Check for duplicate findings
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT title, COUNT(*) as cnt 
            FROM findings 
            GROUP BY title 
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        issues["duplicates"] = [d[0] for d in duplicates]
        
        self._log("lint", f"found {len(issues['missing_refs'])} issues")
        
        return issues


def main():
    import sys
    
    wiki = KnowledgeWiki()
    
    if len(sys.argv) < 2:
        print("prompt-orchestrator Wiki")
        print("Usage: python -m wiki <command> [args]")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: wiki search <query>")
            return
        results = wiki.search(sys.argv[2])
        for r in results:
            print(f"  {r['file']}")
    
    elif cmd == "lint":
        issues = wiki.lint()
        print(json.dumps(issues, indent=2))
    
    elif cmd == "index":
        wiki._update_index()
        print("Index updated")
    
    elif cmd == "page":
        if len(sys.argv) < 3:
            print("Usage: wiki page <name>")
            return
        content = wiki.get_page(sys.argv[2])
        if content:
            print(content)
        else:
            print("Page not found")
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()