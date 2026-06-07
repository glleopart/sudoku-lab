#!/usr/bin/env python3
"""
generate_manifest.py — Auto-generate PROJECT_MANIFEST.md for any codebase.

Usage:
    python scripts/generate_manifest.py
    python scripts/generate_manifest.py --root /path/to/project --output docs/PROJECT_MANIFEST.md
    python scripts/generate_manifest.py --update   # update existing manifest

This script walks the project tree, detects the tech stack, extracts exposed
surfaces (endpoints, exports, components), and produces a structured manifest
that the audit agents and build orchestrator can read.
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────────────────────

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "migrations", ".idea", ".vscode",
}

MAX_FILE_LINES_TO_ANALYZE = 500  # Don't deep-analyze files longer than this

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2",
    ".ttf", ".eot", ".pdf", ".zip", ".tar", ".gz", ".lock",
}


# ── Stack detection ───────────────────────────────────────────────────────────

def detect_stack(root: Path) -> dict:
    """Detect the tech stack from common config files."""
    stack = {
        "languages": [],
        "backend": [],
        "frontend": [],
        "database": [],
        "testing": [],
        "infra": [],
    }

    # Python
    if any(root.glob("*.py")) or (root / "requirements.txt").exists():
        stack["languages"].append("Python")
        req_file = root / "requirements.txt"
        if req_file.exists():
            reqs = req_file.read_text(errors="replace").lower()
            if "fastapi" in reqs:
                stack["backend"].append("FastAPI")
            if "flask" in reqs:
                stack["backend"].append("Flask")
            if "django" in reqs:
                stack["backend"].append("Django")
            if "sqlalchemy" in reqs:
                stack["database"].append("SQLAlchemy")
            if "motor" in reqs or "pymongo" in reqs:
                stack["database"].append("MongoDB/Motor")
            if "psycopg" in reqs:
                stack["database"].append("PostgreSQL")
            if "pytest" in reqs:
                stack["testing"].append("pytest")
            if "anthropic" in reqs:
                stack["backend"].append("Anthropic API")
            if "openai" in reqs:
                stack["backend"].append("OpenAI API")

    # Node / JS / TS
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(errors="replace"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            stack["languages"].append("JavaScript/TypeScript")
            if "react" in deps:
                stack["frontend"].append("React")
            if "vue" in deps:
                stack["frontend"].append("Vue")
            if "svelte" in deps:
                stack["frontend"].append("Svelte")
            if "next" in deps:
                stack["frontend"].append("Next.js")
            if "express" in deps:
                stack["backend"].append("Express")
            if "fastify" in deps:
                stack["backend"].append("Fastify")
            if "tailwindcss" in deps:
                stack["frontend"].append("Tailwind CSS")
            if "jest" in deps or "vitest" in deps:
                stack["testing"].append("Jest/Vitest")
            if "i18next" in deps:
                stack["frontend"].append("i18next")
            if "stripe" in deps:
                stack["backend"].append("Stripe")
        except Exception:
            pass

    # Go
    if (root / "go.mod").exists():
        stack["languages"].append("Go")

    # Rust
    if (root / "Cargo.toml").exists():
        stack["languages"].append("Rust")

    # Docker
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
        stack["infra"].append("Docker")

    # Remove duplicates
    for key in stack:
        stack[key] = list(dict.fromkeys(stack[key]))

    return stack


# ── File analysis ─────────────────────────────────────────────────────────────

def analyze_python_file(path: Path) -> dict:
    """Extract functions, classes, and imports from a Python file."""
    info = {"exports": [], "imports": [], "issues": [], "lines": 0}
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        info["lines"] = content.count("\n")

        if info["lines"] > MAX_FILE_LINES_TO_ANALYZE:
            info["issues"].append(f"File is {info['lines']} lines — consider splitting")

        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if not node.name.startswith("_"):
                    info["exports"].append(f"def {node.name}()")
            elif isinstance(node, ast.ClassDef):
                info["exports"].append(f"class {node.name}")

        # Simple import extraction
        for line in content.splitlines()[:50]:
            if line.startswith("import ") or line.startswith("from "):
                info["imports"].append(line.strip())

        # Check for common issues
        if "os.getenv" not in content and ".env" not in str(path):
            pass  # OK
        if re.search(r'(password|secret|api_key)\s*=\s*["\'][^"\']{4,}', content, re.I):
            info["issues"].append("POSSIBLE HARDCODED SECRET — review immediately")
        if "except:" in content or "except Exception:" in content:
            info["issues"].append("Bare except clause found")
        if content.count("print(") > 3:
            info["issues"].append(f"Debug print statements ({content.count('print(')} found)")

    except SyntaxError as e:
        info["issues"].append(f"SyntaxError: {e}")
    except Exception as e:
        info["issues"].append(f"Analysis error: {e}")

    return info


def analyze_js_ts_file(path: Path) -> dict:
    """Extract exports and basic issues from a JS/TS file."""
    info = {"exports": [], "imports": [], "issues": [], "lines": 0}
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        info["lines"] = content.count("\n")

        if info["lines"] > MAX_FILE_LINES_TO_ANALYZE:
            info["issues"].append(f"File is {info['lines']} lines — consider splitting")

        # Exported functions/components/constants
        for match in re.finditer(r"export\s+(default\s+)?(function|class|const|let|var)\s+(\w+)", content):
            info["exports"].append(match.group(3))

        # Imports
        for match in re.finditer(r"^import .+ from ['\"]([^'\"]+)['\"]", content, re.M):
            info["imports"].append(match.group(1))

        # Issues
        if "console.log" in content:
            count = content.count("console.log")
            info["issues"].append(f"{count} console.log statement(s) found")
        if ": any" in content or "as any" in content:
            info["issues"].append("TypeScript 'any' usage detected")
        if re.search(r'(password|secret|apiKey|api_key)\s*[:=]\s*["\'][^"\']{4,}', content, re.I):
            info["issues"].append("POSSIBLE HARDCODED SECRET — review immediately")

    except Exception as e:
        info["issues"].append(f"Analysis error: {e}")

    return info


def extract_api_routes(path: Path) -> list[str]:
    """Extract API routes from Python router files."""
    routes = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(
            r'@\w+\.(get|post|put|patch|delete|options)\(["\']([^"\']+)["\']',
            content, re.I
        ):
            routes.append(f"{match.group(1).upper()} {match.group(2)}")
    except Exception:
        pass
    return routes


def count_todos(root: Path) -> dict:
    """Count TODO/FIXME/HACK markers across the codebase."""
    counts = {"TODO": 0, "FIXME": 0, "HACK": 0, "XXX": 0}
    for marker in counts:
        try:
            result = subprocess.run(
                ["grep", "-r", f"--include=*.py", f"--include=*.ts",
                 f"--include=*.js", f"--include=*.tsx", f"--include=*.jsx",
                 "-l", marker, str(root)],
                capture_output=True, text=True, timeout=5
            )
            files = [l for l in result.stdout.splitlines() if l.strip()]
            counts[marker] = len(files)
        except Exception:
            pass
    return counts


# ── File tree ─────────────────────────────────────────────────────────────────

def build_file_tree(root: Path, prefix: str = "", max_depth: int = 4) -> str:
    """Build an ASCII file tree."""
    lines = []
    try:
        items = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name))
        items = [i for i in items if i.name not in SKIP_DIRS and not i.name.startswith(".")]
    except PermissionError:
        return ""

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{item.name}")
        if item.is_dir() and max_depth > 1:
            extension = "    " if is_last else "│   "
            subtree = build_file_tree(item, prefix + extension, max_depth - 1)
            if subtree:
                lines.append(subtree)

    return "\n".join(lines)


# ── Manifest generation ───────────────────────────────────────────────────────

def generate_manifest(root: Path, output_path: Path, existing: str = ""):
    """Generate the full PROJECT_MANIFEST.md."""
    print(f"Scanning: {root}")
    stack = detect_stack(root)
    todos = count_todos(root)

    # Collect file analysis
    file_entries = []
    all_routes = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        parts = rel.parts
        if any(p in SKIP_DIRS for p in parts) or any(p.startswith(".") for p in parts):
            continue
        if path.suffix in BINARY_EXTENSIONS:
            continue

        entry = {"path": str(rel), "exports": [], "issues": [], "routes": []}

        if path.suffix == ".py":
            info = analyze_python_file(path)
            entry["exports"] = info["exports"][:10]
            entry["issues"] = info["issues"]
            entry["lines"] = info.get("lines", 0)
            routes = extract_api_routes(path)
            entry["routes"] = routes
            all_routes.extend(routes)

        elif path.suffix in {".js", ".ts", ".jsx", ".tsx"}:
            info = analyze_js_ts_file(path)
            entry["exports"] = info["exports"][:10]
            entry["issues"] = info["issues"]
            entry["lines"] = info.get("lines", 0)

        else:
            try:
                entry["lines"] = path.read_text(errors="replace").count("\n")
            except Exception:
                entry["lines"] = 0

        file_entries.append(entry)

    # Read existing manifest for project name / description
    project_name = root.name
    project_desc = "TODO: Add one-sentence project description"
    current_version = "v0.0"
    license_type = "TODO"

    if existing:
        for line in existing.splitlines():
            if line.startswith("**Project name**"):
                v = line.split(":", 1)[-1].strip()
                if v and v != "TODO":
                    project_name = v
            if line.startswith("**Description**"):
                v = line.split(":", 1)[-1].strip()
                if v and v != "TODO":
                    project_desc = v
            if line.startswith("**Current version**"):
                v = line.split(":", 1)[-1].strip()
                if v:
                    current_version = v
            if line.startswith("**License**"):
                v = line.split(":", 1)[-1].strip()
                if v:
                    license_type = v

    # Build manifest content
    stack_str = ", ".join(
        stack.get("languages", []) +
        stack.get("backend", []) +
        stack.get("frontend", []) +
        stack.get("database", [])
    ) or "TODO"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    file_tree = build_file_tree(root)

    manifest = f"""# Project Manifest
*Generated by generate_manifest.py on {now}*
*Update this file manually after every build session.*

---

## Project overview

**Project name:** {project_name}
**Description:** {project_desc}
**Current version:** {current_version}
**License:** {license_type}
**Tech stack:** {stack_str}
**Privacy model:** TODO (public OSS / private / commercial SaaS)
**AI/ML layer:** {"Yes — see ai/ directory" if (root / "ai").exists() else "No (planned for future version)"}

---

## Tech stack detail

| Layer | Technology |
|-------|-----------|
| Languages | {", ".join(stack.get("languages", ["TODO"])) or "TODO"} |
| Backend | {", ".join(stack.get("backend", ["TODO"])) or "TODO"} |
| Frontend | {", ".join(stack.get("frontend", ["TODO"])) or "TODO"} |
| Database | {", ".join(stack.get("database", ["TODO"])) or "TODO"} |
| Testing | {", ".join(stack.get("testing", ["TODO"])) or "TODO"} |
| Infra | {", ".join(stack.get("infra", ["TODO"])) or "TODO"} |

---

## File tree

```
{file_tree}
```

---

## File registry

*One entry per source file. Update after every build session.*

"""

    for entry in file_entries:
        issues_str = ""
        if entry["issues"]:
            issues_str = "\n  - **Issues:** " + "; ".join(entry["issues"])

        exports_str = ""
        if entry["exports"]:
            exports_str = "\n  - **Exports:** " + ", ".join(f"`{e}`" for e in entry["exports"])

        routes_str = ""
        if entry["routes"]:
            routes_str = "\n  - **Routes:** " + ", ".join(f"`{r}`" for r in entry["routes"])

        manifest += f"""### `{entry["path"]}`
  - **Lines:** {entry.get("lines", "?")}
  - **Purpose:** TODO{exports_str}{routes_str}{issues_str}

"""

    # API surface summary
    if all_routes:
        manifest += "---\n\n## API surface\n\n"
        manifest += "| Method | Path |\n|--------|------|\n"
        for route in sorted(set(all_routes)):
            parts = route.split(" ", 1)
            if len(parts) == 2:
                manifest += f"| {parts[0]} | `{parts[1]}` |\n"

    # Code health summary
    manifest += f"""
---

## Code health snapshot

| Metric | Value |
|--------|-------|
| Total files analyzed | {len(file_entries)} |
| Files with issues | {sum(1 for e in file_entries if e["issues"])} |
| TODO markers (files) | {todos.get("TODO", 0)} |
| FIXME markers (files) | {todos.get("FIXME", 0)} |
| HACK markers (files) | {todos.get("HACK", 0)} |
| Known API routes | {len(set(all_routes))} |

---

## Security notes

- **Auth method:** TODO (JWT / session / API key / OAuth)
- **Secrets management:** TODO (describe .env usage)
- **CORS policy:** TODO (list allowed origins)
- **Rate limiting:** TODO (configured / not yet)

---

## Roadmap (summary)

| Version | Status | Description |
|---------|--------|-------------|
| v0.0 | TODO | Project skeleton |
| v0.1 | TODO | Core data model |
| ... | | |
| beta | TODO | Full audit pass |

*Update status to: planned / in-progress / complete*

---

## Architecture decision log

*Add entries when significant design decisions are made.*

| Date | Decision | Reason |
|------|----------|--------|
| {datetime.now().strftime("%Y-%m-%d")} | Manifest generated | Initial setup |

---

## Agent communication

*Updated by Claude Code and audit agents after each session.*

- **Last build session:** {now}
- **Last audit run:** N/A
- **Last audit score:** N/A
- **Blockers:** None documented yet
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest, encoding="utf-8")
    print(f"Manifest written to: {output_path}")
    print(f"  Files analyzed: {len(file_entries)}")
    print(f"  API routes found: {len(set(all_routes))}")
    print(f"  Files with issues: {sum(1 for e in file_entries if e['issues'])}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate PROJECT_MANIFEST.md from any codebase",
    )
    parser.add_argument(
        "--root", default=".", help="Project root directory (default: .)"
    )
    parser.add_argument(
        "--output",
        default="docs/PROJECT_MANIFEST.md",
        help="Output path (default: docs/PROJECT_MANIFEST.md)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing manifest (preserve manually added fields)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output)

    existing = ""
    if args.update and output.exists():
        existing = output.read_text(encoding="utf-8", errors="replace")
        print("Updating existing manifest...")
    else:
        print("Generating new manifest...")

    generate_manifest(root, output, existing)


if __name__ == "__main__":
    main()
