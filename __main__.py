#!/usr/bin/env python3
"""
prompt-orchestrator — CLI entry point
=====================================
A modular Python framework for orchestrating prompt-driven AI agents
against arbitrary subjects. The same engine drives multi-phase
workflows across any domain: subject assessments, data pipelines,
research automation, integration tasks, and more.

Run interactively:
    python -m prompt_orchestrator
    # or
    python __main__.py

Run a single command:
    python __main__.py run --subject example.com
    python __main__.py phase discover --subject example.com
"""

import argparse
import json
import os
import sys
import atexit

# Make project root importable when run as `python __main__.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from knowledge.knowledge import KnowledgeBase
from knowledge.wiki import KnowledgeWiki
from execution.engine import ExecutionEngine
from tools import scanner  # noqa: F401  — CLI wrapper module


PHASE_ALIASES = {
    # Accept old names from the previous version so existing configs keep working.
    "recon": "discover",
    "enum": "scan",
    "enumeration": "scan",
    "vuln": "analyze",
    "exploit": "build",
    "post": "integrate",
    "chain": "orchestrate-phases",
    "reporting": "document",
}


class Orchestrator:
    """Top-level façade. Holds the four core systems and exposes
    a small set of high-level workflow verbs."""

    def __init__(self, config: dict = None):
        self.config = config or {}

        # Initialize core systems
        self.kb = KnowledgeBase(
            self.config.get("knowledge_db", "~/.prompt_orchestrator/knowledge.db")
        )
        self.wiki = KnowledgeWiki(
            self.config.get("wiki_path", "~/.prompt_orchestrator/wiki")
        )
        self.engine = ExecutionEngine(
            knowledge_base=self.kb,
            workspace=self.config.get("workspace", "~/.prompt_orchestrator/workspace"),
        )

        # State
        self.current_subject = None
        self.autonomy_level = self.config.get("autonomy", 3)
        self.running = False

        print(f"[prompt-orchestrator] Initialized")
        print(f"[prompt-orchestrator] Knowledge base: {self.kb.db_path}")
        print(f"[prompt-orchestrator] Wiki: {self.wiki.wiki_path}")
        print(f"[prompt-orchestrator] Workspace: {self.engine.workspace}")
        print(f"[prompt-orchestrator] Autonomy level: {self.autonomy_level}")
        print("""
+------------------------------------------------------------+
|                                                            |
|   prompt-orchestrator                                      |
|                                                            |
|   Multi-phase workflow orchestration for prompt-driven     |
|   AI agents. Discover -> Scan -> Analyze -> Build ->       |
|   Integrate -> Document.                                   |
|                                                            |
+------------------------------------------------------------+
""")

    # ─── High-level workflow verbs ──────────────────────────────
    def run(self, subject: str, phases: list = None) -> dict:
        """Run the full workflow on a subject."""
        print(f"[prompt-orchestrator] Running workflow on {subject}")

        # Ensure subject is in the knowledge base.
        subject_obj = self.kb.get_subject(subject)
        if not subject_obj:
            self.kb.add_subject(subject)
            print(f"[prompt-orchestrator] Added subject: {subject}")

        # Map any legacy phase names.
        if phases:
            phases = [PHASE_ALIASES.get(p, p) for p in phases]

        if phases:
            return self.engine.run_full_workflow(subject, phases)
        return self.engine.run_full_workflow(subject)

    def discover(self, subject: str) -> dict:
        """Phase 1: discover."""
        return self.engine.discover(subject)

    def scan(self, subject: str) -> dict:
        """Phase 2: scan."""
        return self.engine.scan(subject)

    def analyze(self, subject: str) -> dict:
        """Phase 3: analyze."""
        return self.engine.analyze(subject)

    def build(self, subject: str, findings: list = None) -> dict:
        """Phase 4: build (produce artifacts / actions)."""
        return self.engine.build(subject, findings)

    def integrate(self, subject: str, artifacts: list = None) -> dict:
        """Phase 5: integrate (push outputs downstream)."""
        return self.engine.integrate(subject, artifacts)

    def orchestrate_phases(self, subject: str) -> dict:
        """Meta-phase: chain phases into a multi-stage workflow."""
        return self.engine.orchestrate_phases(subject)

    def report(self, subject: str) -> str:
        """Phase 6: document — generate the final report."""
        return self.engine.generate_report(subject)

    def resume(self, subject: str) -> dict:
        """Resume a previously paused workflow."""
        return self.engine.resume(subject)

    def stop(self, subject: str):
        """Stop a running workflow and persist state."""
        return self.engine.stop(subject)

    def search(self, query: str) -> dict:
        """Search the knowledge base."""
        return self.kb.search(query, self.current_subject)

    def reference(self, ref_id: str) -> dict:
        """Get a known-issue reference (was: cve())."""
        return self.kb.get_reference(ref_id)

    def subject_info(self, subject: str = None) -> dict:
        """Get info on the current subject."""
        subject = subject or self.current_subject
        if not subject:
            return {"error": "No subject specified"}
        subject_obj = self.kb.get_subject(subject)
        if not subject_obj:
            return {"error": f"Subject {subject} not found"}
        findings = self.kb.get_findings(subject_obj["id"])
        state = self.kb.load_state(subject_obj["id"])
        return {
            "name": subject,
            "first_seen": subject_obj["first_seen"],
            "last_seen": subject_obj["last_seen"],
            "findings": len(findings),
            "state": state,
        }

    def list_subjects(self) -> list:
        """List all known subjects."""
        return self.kb.list_subjects()

    def save_tool(self, name: str, definition: dict):
        """Save a custom tool definition."""
        self.kb.save_tool(name, definition)
        print(f"[prompt-orchestrator] Tool saved: {name}")

    def get_tool(self, name: str) -> dict:
        """Get a saved tool."""
        return self.kb.get_tool(name)

    def list_tools(self) -> list:
        """List saved tools."""
        return self.kb.list_tools()


def _resolve_phase(name: str) -> str:
    """Map a legacy or shorthand phase name to the canonical name."""
    return PHASE_ALIASES.get(name.lower(), name.lower())


def interactive():
    """Interactive REPL mode."""
    import readline

    orch = Orchestrator()

    print("""
Commands:
  subject <name>          Set current subject
  run                     Run full workflow on current subject
  discover / scan /
  analyze / build /
  integrate /
  orchestrate-phases /
  document                Run a specific phase
  resume                  Resume a paused workflow
  stop                    Stop and persist state
  reference <id>          Look up a known-issue reference
  search <query>          Search the knowledge base
  subjects                List known subjects
  quit / exit / q         Exit

Or just describe what you want to do in plain language.
""")

    while True:
        try:
            cmd = input("\nprompt-orchestrator> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("quit", "exit", "q"):
                print("[prompt-orchestrator] Shutting down...")
                break

            parts = cmd.split()
            action = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if action == "subject":
                if not args:
                    print(f"Current subject: {orch.current_subject}")
                else:
                    orch.current_subject = args[0]
                    info = orch.subject_info(args[0])
                    print(f"[prompt-orchestrator] Subject: {info}")

            elif action in ("run", "workflow"):
                if not orch.current_subject:
                    print("[prompt-orchestrator] No subject set. Use 'subject <name>' first.")
                    continue
                phases = [_resolve_phase(p) for p in args]
                result = orch.run(orch.current_subject, phases or None)
                print(json.dumps(result, indent=2))

            elif action in PHASE_ALIASES or action in (
                "discover", "scan", "analyze", "build",
                "integrate", "orchestrate-phases", "document",
            ):
                phase = _resolve_phase(action)
                method = getattr(orch, phase, None)
                if method is None:
                    print(f"Unknown phase: {phase}")
                    continue
                target = args[0] if args else orch.current_subject
                if not target:
                    print(f"[prompt-orchestrator] Usage: {action} <subject>")
                    continue
                result = method(target)
                print(json.dumps(result, indent=2))

            elif action == "resume":
                target = args[0] if args else orch.current_subject
                if not target:
                    print("[prompt-orchestrator] Usage: resume <subject>")
                    continue
                result = orch.resume(target)
                print(json.dumps(result, indent=2))

            elif action == "stop":
                target = args[0] if args else orch.current_subject
                if not target:
                    print("[prompt-orchestrator] Usage: stop <subject>")
                    continue
                orch.stop(target)
                print("[prompt-orchestrator] Stopped.")

            elif action == "report":
                target = args[0] if args else orch.current_subject
                if not target:
                    print("[prompt-orchestrator] Usage: report <subject>")
                    continue
                path = orch.report(target)
                print(f"[prompt-orchestrator] Report: {path}")

            elif action == "reference":
                if not args:
                    print("[prompt-orchestrator] Usage: reference <ref-id>")
                    continue
                ref = orch.reference(args[0])
                print(json.dumps(ref, indent=2))

            elif action == "search":
                if not args:
                    print("[prompt-orchestrator] Usage: search <query>")
                    continue
                result = orch.search(" ".join(args))
                print(json.dumps(result, indent=2))

            elif action == "subjects":
                for s in orch.list_subjects():
                    print(f"  - {s}")

            elif action == "help":
                print("""
subject <name>            Set current subject
run [phase ...]           Run full workflow (or specific phases)
discover / scan / analyze / build / integrate /
orchestrate-phases / document
                          Run a specific phase
resume <subject>          Resume a paused workflow
stop <subject>            Stop and persist state
reference <id>            Look up a known-issue reference
search <query>            Search the knowledge base
subjects                  List known subjects
quit                      Exit
""")

            else:
                print(f"[prompt-orchestrator] Unknown command: {action}")
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\n[prompt-orchestrator] Use 'quit' to exit")
        except Exception as e:
            print(f"[ERROR] {e}")


def main():
    parser = argparse.ArgumentParser(
        description="prompt-orchestrator — multi-phase workflow orchestration for prompt-driven AI agents",
    )
    parser.add_argument("command", nargs="?", help="Command to run (run / discover / scan / analyze / build / integrate / report / resume / search / subjects / wiki)")
    parser.add_argument("subject", nargs="?", help="Subject (URL, identifier, file path)")
    parser.add_argument("--phase", help="Specific phase to run")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--config", "-c", help="Path to config file")

    args = parser.parse_args()

    config = {}
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    orch = Orchestrator(config)

    if args.interactive or not args.command:
        interactive()
        return

    # One-shot command dispatch
    subject = args.subject

    if args.command == "run":
        if not subject:
            print("Error: subject required")
            return
        phases = [_resolve_phase(args.phase)] if args.phase else None
        result = orch.run(subject, phases)
        print(json.dumps(result, indent=2))

    elif args.command == "phase":
        if not args.phase:
            print("Usage: phase <phase-name> -- <subject>")
            return
        if not subject:
            print("Error: subject required")
            return
        phase = _resolve_phase(args.phase)
        method = getattr(orch, phase, None)
        if method is None:
            print(f"Unknown phase: {phase}")
            return
        result = method(subject)
        print(json.dumps(result, indent=2))

    elif args.command == "report":
        if not subject:
            print("Error: subject required")
            return
        path = orch.report(subject)
        print(f"Report: {path}")

    elif args.command == "resume":
        if not subject:
            print("Error: subject required")
            return
        result = orch.resume(subject)
        print(json.dumps(result, indent=2))

    elif args.command == "reference":
        if not subject:
            print("Error: reference id required")
            return
        ref = orch.reference(subject)
        print(json.dumps(ref, indent=2))

    elif args.command == "search":
        if not subject:
            print("Error: query required")
            return
        result = orch.search(subject)
        print(json.dumps(result, indent=2))

    elif args.command == "subjects":
        for s in orch.list_subjects():
            print(s)

    elif args.command == "wiki":
        if len(sys.argv) < 3:
            print("Usage: wiki <search|lint|index|page>")
            return
        wiki_cmd = sys.argv[2]
        if wiki_cmd == "search" and len(sys.argv) >= 4:
            query = " ".join(sys.argv[3:])
            results = orch.wiki.search(query)
            print(json.dumps(results, indent=2))
        elif wiki_cmd == "lint":
            issues = orch.wiki.lint()
            print(json.dumps(issues, indent=2))
        elif wiki_cmd == "index":
            orch.wiki._update_index()
            print("Index updated")
        elif wiki_cmd == "page" and len(sys.argv) >= 4:
            name = sys.argv[3]
            content = orch.wiki.get_page(name)
            if content:
                print(content)
            else:
                print("Page not found")
        else:
            print(f"Unknown wiki command: {wiki_cmd}")

    else:
        print(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
