"""
prompt-orchestrator — Skills System
====================================
Dynamic skill loading from markdown files plus a small set of generic
builtins. Each skill wraps a tool invocation, a reasoning pattern, or
both. The orchestrator selects relevant skills per-query from triggers.
"""

import os
import json
import re
from typing import Dict, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Skill:
    name: str
    description: str
    triggers: List[str]
    prompt: str
    tools: List[str]
    category: str = "general"

class SkillsManager:
    """
    Skills system that loads relevant tools based on context.
    Similar to Agent Zero's SKILL.md system.
    """
    
    def __init__(self, skills_dir: str = "./skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}
        self._load_skills()
    
    def _load_skills(self):
        """Load all skills from the skills directory"""
        
        skills_dir = Path(self.skills_dir)
        if not skills_dir.exists():
            skills_dir = Path(__file__).parent.parent / "skills"
            if not skills_dir.exists():
                print(f"Skills directory not found: {self.skills_dir}")
                return
        
        for skill_file in skills_dir.glob("**/*.md"):
            try:
                skill = self._parse_skill_file(skill_file)
                if skill:
                    self.skills[skill.name] = skill
                    print(f"Loaded skill: {skill.name}")
            except Exception as e:
                print(f"Failed to load skill {skill_file}: {e}")
    
    def _parse_skill_file(self, file_path: Path) -> Optional[Skill]:
        """Parse a SKILL.md file"""
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        name = file_path.stem.replace('-', ' ').replace('_', ' ').title()
        
        description = ""
        triggers = []
        prompt_parts = []
        tools = []
        
        lines = content.split('\n')
        in_prompt = False
        in_tools = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('## Description'):
                continue
            elif line.startswith('## Triggers'):
                continue
            elif line.startswith('## Prompt'):
                in_prompt = True
                in_tools = False
                continue
            elif line.startswith('## Tools'):
                in_tools = True
                in_prompt = False
                continue
            elif line.startswith('#'):
                in_prompt = False
                in_tools = False
            
            if not line:
                continue
            
            if not in_prompt and not in_tools:
                description += line + " "
            elif in_prompt:
                prompt_parts.append(line)
            elif in_tools:
                if line.startswith('-') or line.startswith('*'):
                    tool = line.lstrip('-* ').strip()
                    if tool:
                        tools.append(tool)
        
        for word in name.lower().split():
            if word not in [w.lower() for w in triggers]:
                triggers.append(word)
        
        for tool in tools:
            for word in tool.lower().split():
                if word not in triggers:
                    triggers.append(word)
        
        prompt = '\n'.join(prompt_parts)
        
        if not prompt:
            prompt = f"You are a {name} expert. Use the available tools to help with {name.lower()} tasks."
        
        return Skill(
            name=name,
            description=description.strip(),
            triggers=list(set(triggers)),
            prompt=prompt,
            tools=tools,
            category=file_path.parent.name if file_path.parent.name != 'skills' else 'general'
        )
    
    def get_relevant_skills(self, query: str) -> List[Skill]:
        """Get skills relevant to a query"""
        
        query_lower = query.lower()
        relevant = []
        
        for skill in self.skills.values():
            for trigger in skill.triggers:
                if trigger.lower() in query_lower:
                    relevant.append(skill)
                    break
        
        if not relevant:
            relevant = list(self.skills.values())[:3]
        
        return relevant
    
    def build_skill_prompt(self, skills: List[Skill]) -> str:
        """Build a prompt from relevant skills"""
        
        if not skills:
            return ""
        
        prompt_parts = ["=== RELEVANT SKILLS ==="]
        
        for skill in skills:
            prompt_parts.append(f"\n## {skill.name}")
            prompt_parts.append(f"Description: {skill.description}")
            prompt_parts.append(f"Instructions: {skill.prompt}")
            if skill.tools:
                prompt_parts.append(f"Available tools: {', '.join(skill.tools)}")
        
        return '\n'.join(prompt_parts)
    
    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """Get a specific skill by name"""
        return self.skills.get(name)
    
    def list_skills(self) -> List[Dict]:
        """List all available skills"""
        return [
            {
                'name': s.name,
                'description': s.description,
                'category': s.category,
                'triggers': s.triggers[:5]
            }
            for s in self.skills.values()
        ]


# Built-in skills. Domain-agnostic — any domain-specific tooling should
# live in the markdown files under skills/ and be loaded from disk.
# These exist to ensure the orchestrator always has a few default
# capabilities registered even when no markdown skills are present.

BUILTIN_SKILLS = {
    'curl': Skill(
        name='HTTP testing',
        description='Generic HTTP request testing and analysis',
        triggers=['curl', 'http', 'request', 'headers', 'method'],
        prompt="""You are an HTTP testing expert using curl.

Common uses:
- GET: curl -s URL
- POST: curl -X POST -d "data" URL
- Headers: curl -I URL
- Cookies: curl -b "cookie" URL
- Auth: curl -u user:pass URL
- Follow redirects: curl -L URL
- Verbose: curl -v URL

Use curl to test endpoints, headers, and authentication.""",
        tools=['curl', 'wget'],
        category='testing',
    ),
    'file_ops': Skill(
        name='File operations',
        description='Read, write, search and edit files on the host filesystem',
        triggers=['file', 'read', 'write', 'edit', 'search', 'grep', 'find'],
        prompt="""You are a file-operations expert using standard Unix tools.

Common uses:
- Read: cat, less, head, tail
- Write/append: tee, sed -i, here-docs
- Search: grep -r, find, fd, rg
- Structured: jq, yq, csvkit
- Edit in place: sed -i, perl -pi, awk

Prefer non-destructive operations first; always confirm before
overwriting or deleting.""",
        tools=['cat', 'sed', 'awk', 'grep', 'find', 'jq'],
        category='filesystem',
    ),
    'shell': Skill(
        name='Shell automation',
        description='Compose shell pipelines, run scripts, manage processes',
        triggers=['shell', 'bash', 'pipeline', 'script', 'process', 'cron'],
        prompt="""You are a shell-automation expert.

Common patterns:
- Composable pipelines: cmd1 | cmd2 | cmd3
- Background work: nohup, screen, tmux, systemd-run
- Scheduling: cron, systemd timers, at
- Process control: ps, top, htop, pgrep, pkill
- Network: ss, netstat, ip, curl, nc

Prefer idempotent commands. Capture stdout/stderr separately so you
can debug failures.""",
        tools=['bash', 'zsh', 'cron', 'systemd-run', 'tmux'],
        category='automation',
    ),
    'git_ops': Skill(
        name='Git operations',
        description='Version-control operations: commit, branch, PR, review',
        triggers=['git', 'commit', 'branch', 'pr', 'merge', 'rebase'],
        prompt="""You are a git-operations expert.

Common workflow:
1. Inspect: git status, git log --oneline -10
2. Branch: git checkout -b feature/name
3. Stage: git add -p (interactive), git add path
4. Commit: git commit -m 'subject' with body explaining why
5. Push: git push -u origin feature/name
6. PR: gh pr create --fill --draft, then iterate on review

Always pull/rebase before pushing. Never force-push shared branches.""",
        tools=['git', 'gh'],
        category='version-control',
    ),
    'data_ops': Skill(
        name='Data operations',
        description='SQL, CSV, and structured-data manipulation',
        triggers=['sql', 'csv', 'data', 'query', 'database', 'sqlite'],
        prompt="""You are a data-operations expert.

Common patterns:
- SQL: psql, sqlite3, mysql — read-only first, transactions for writes
- CSV: csvkit (csvcut, csvgrep, csvstat), miller, xsv
- JSON: jq, jq -r for raw output, gron for flatten
- Parquet/Arrow: duckdb -c 'SELECT ... FROM file.parquet'
- Streaming: tail -f, awk, parallel

Validate assumptions about column types before running aggregates.""",
        tools=['psql', 'sqlite3', 'jq', 'duckdb', 'csvkit'],
        category='data',
    ),
}


SKILLS_MANAGER = SkillsManager()


for name, skill in BUILTIN_SKILLS.items():
    SKILLS_MANAGER.skills[name] = skill