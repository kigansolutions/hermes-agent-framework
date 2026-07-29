#!/usr/bin/env python3
"""Static smoke checks for the public Hermes reference framework.

These checks intentionally do not import modules or run live tools. Several
modules create local databases, shell out, or start browser integrations when
used. CI should prove the public export is parseable and documented without
exercising those runtime surfaces.
"""

from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]

PYTHON_FILES = [
    "execution/engine.py",
    "tools/executor.py",
    "integration/browser.py",
    "knowledge/knowledge.py",
]

REQUIRED_FILES = [
    "LICENSE",
    "docs/safety-policy.md",
    "requirements.txt",
    "requirements-optional.txt",
]

failed = False


def fail(message: str) -> None:
    global failed
    failed = True
    print(f"smoke validation: {message}", file=sys.stderr)


for rel_path in REQUIRED_FILES:
    if not (ROOT / rel_path).is_file():
        fail(f"missing required file: {rel_path}")

for rel_path in PYTHON_FILES:
    path = ROOT / rel_path
    if not path.is_file():
        fail(f"missing Python file: {rel_path}")
        continue
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as error:
        fail(f"{rel_path} does not compile: {error.msg}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
if "python -m prompt_orchestrator" in readme:
    fail("README still references the unavailable prompt_orchestrator module path")

safety_policy = (ROOT / "docs/safety-policy.md").read_text(encoding="utf-8") if (ROOT / "docs/safety-policy.md").is_file() else ""
for phrase in [
    "trusted local operator",
    "scope confirmation",
    "browser stealth",
    "credential-like memory",
]:
    if phrase not in safety_policy:
        fail(f"safety policy missing phrase: {phrase}")

if failed:
    sys.exit(1)

print(f"Smoke-validated {len(PYTHON_FILES)} Python file(s) and required safety docs.")
