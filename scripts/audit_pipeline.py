#!/usr/bin/env python3
"""
audit_pipeline.py — General-purpose 3-agent code audit orchestrator.

Usage:
    python scripts/audit_pipeline.py --manifest docs/PROJECT_MANIFEST.md
    python scripts/audit_pipeline.py --manifest docs/PROJECT_MANIFEST.md --max-iter 2
    python scripts/audit_pipeline.py --manifest docs/PROJECT_MANIFEST.md --dry-run

Requires:
    pip install anthropic tenacity

Environment:
    ANTHROPIC_API_KEY  — required
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import anthropic
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install anthropic tenacity")
    sys.exit(1)

# ── Configuration ────────────────────────────────────────────────────────────

PASS_THRESHOLD = 85          # average score required to pass
MIN_AGENT_SCORE = 70         # each individual agent must score at least this
MAX_FILE_CHARS = 8_000       # max chars per source file sent to agents
MAX_FILES = 40               # max number of source files included
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096

# File extensions to include in code collection
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".cpp", ".c", ".h", ".cs", ".rb", ".php", ".swift", ".kt",
    ".vue", ".svelte", ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml", ".env.example",
    ".md", ".txt", ".sh",
}

# Directories to always skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "migrations",
}

# ── File collection ───────────────────────────────────────────────────────────

def collect_files(root: Path, manifest_path: Path) -> dict[str, str]:
    """
    Walk the project tree and collect source file contents.
    Skips vendor dirs, truncates large files, caps total file count.
    Returns {relative_path: content}.
    """
    files = {}
    root = root.resolve()

    # Priority: files mentioned in the manifest come first
    priority_paths = extract_paths_from_manifest(manifest_path)

    all_paths = []
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root)
            parts = rel.parts
            if any(p in SKIP_DIRS for p in parts):
                continue
            if path.suffix.lower() in CODE_EXTENSIONS or path.name in {
                ".env.example", "Makefile", "Dockerfile", "docker-compose.yml"
            }:
                all_paths.append(rel)

    # Sort: priority files first, then alphabetical
    all_paths.sort(key=lambda p: (str(p) not in priority_paths, str(p)))
    all_paths = all_paths[:MAX_FILES]

    for rel in all_paths:
        full = root / rel
        try:
            content = full.read_text(encoding="utf-8", errors="replace")
            if len(content) > MAX_FILE_CHARS:
                content = (
                    content[:MAX_FILE_CHARS]
                    + f"\n\n... [TRUNCATED — {len(content)} chars total] ..."
                )
            files[str(rel)] = content
        except Exception as e:
            files[str(rel)] = f"[ERROR reading file: {e}]"

    return files


def extract_paths_from_manifest(manifest_path: Path) -> set[str]:
    """Pull file paths mentioned in PROJECT_MANIFEST.md."""
    if not manifest_path.exists():
        return set()
    text = manifest_path.read_text(encoding="utf-8", errors="replace")
    paths = set()
    for line in text.splitlines():
        stripped = line.strip().lstrip("│├└─ ").strip("`")
        if "/" in stripped and "." in stripped.split("/")[-1]:
            paths.add(stripped)
    return paths


def format_files_for_prompt(files: dict[str, str]) -> str:
    """Format collected files as a readable block for the LLM."""
    parts = []
    for path, content in files.items():
        parts.append(f"### File: {path}\n```\n{content}\n```")
    return "\n\n".join(parts)

# ── Agent system prompts ──────────────────────────────────────────────────────

AGENT_1_SYSTEM = """You are Audit Agent 1: Security & Architecture reviewer.
You review source code for security vulnerabilities and structural problems.
You are precise, adversarial, and specific — every finding names the file and
the exact issue. You output a structured report with a numeric score out of 100
and a prompt for Agent 2 at the end.

SCORING RUBRIC (100 points total):
- S1 Secrets management: 15 pts
- S2 Auth & authorization: 15 pts
- S3 Input validation & injection: 10 pts
- S4 Dependency security: 5 pts
- S5 Transport & CORS: 5 pts
- A1 Separation of concerns: 20 pts
- A2 Dead code & bloat: 10 pts
- A3 Module cohesion: 10 pts
- A4 Error handling: 10 pts

OUTPUT FORMAT (use exactly this structure):
SCORE: [number]/100
BREAKDOWN:
S1: [score]/15
S2: [score]/15
S3: [score]/10
S4: [score]/5
S5: [score]/5
A1: [score]/20
A2: [score]/10
A3: [score]/10
A4: [score]/10

FINDINGS:
[CRITICAL] file.py:23 – [issue description] → [fix]
[MAJOR] file.py:45 – [issue description] → [fix]
[MINOR] file.py:67 – [issue description] → [fix]

AGENT_2_PROMPT:
You are Audit Agent 2 reviewing [project name] at version [version].
Agent 1 scored [score]/100.
Critical issues found: [list]
Major issues found: [list]
Your task: review frontend/backend parity and data consistency.
"""

AGENT_2_SYSTEM = """You are Audit Agent 2: Frontend/Backend Parity reviewer.
You check whether the frontend and backend are consistent: API contracts,
data shapes, duplicated logic, and interface coverage. You receive Agent 1's
findings and score as context.

SCORING RUBRIC (100 points total):
- P1 API contract coverage: 20 pts
- P2 Logic ownership: 15 pts
- P3 Data shape consistency: 10 pts
- P4 i18n coverage: 5 pts (N/A=5 if no i18n)
- C1 Error handling parity: 20 pts
- C2 Auth state consistency: 15 pts
- C3 Loading/async state: 10 pts
- C4 Constants and enums: 5 pts

OUTPUT FORMAT (use exactly this structure):
SCORE: [number]/100
BREAKDOWN:
P1: [score]/20
P2: [score]/15
P3: [score]/10
P4: [score]/5
C1: [score]/20
C2: [score]/15
C3: [score]/10
C4: [score]/5

FINDINGS:
[CRITICAL] [file or endpoint] – [issue] → [fix]
[MAJOR] [file or endpoint] – [issue] → [fix]
[MINOR] [file or endpoint] – [issue] → [fix]

AGENT_3_PROMPT:
You are Audit Agent 3 reviewing [project name] at version [version].
Agent 1 scored [a1_score]/100. Agent 2 scored [a2_score]/100.
Combined critical issues: [list from both agents]
Your task: review code quality and licensing, then produce the final AUDIT_REPORT.md.
"""

AGENT_3_SYSTEM = """You are Audit Agent 3: Code Quality & Licensing reviewer.
You are the final auditor. You review code quality, static analysis findings,
test coverage, and license compliance. You produce the final verdict.

SCORING RUBRIC (100 points total):
- Q1 Static analysis cleanliness: 20 pts
- Q2 File and function size: 10 pts
- Q3 TODO/FIXME density: 5 pts
- Q4 Test coverage: 10 pts (N/A=5 if no tests planned)
- Q5 Debug statements: 5 pts
- L1 License file present: 10 pts
- L2 Dependency license compatibility: 30 pts
- L3 License headers: 10 pts (N/A=10 if not required)

OUTPUT FORMAT (use exactly this structure):
SCORE: [number]/100
BREAKDOWN:
Q1: [score]/20
Q2: [score]/10
Q3: [score]/5
Q4: [score]/10
Q5: [score]/5
L1: [score]/10
L2: [score]/30
L3: [score]/10

FINDINGS:
[CRITICAL] [file or package] – [issue] → [fix]
[MAJOR] [file or package] – [issue] → [fix]
[MINOR] [file or package] – [issue] → [fix]

VERDICT: PASS | FAIL | CONDITIONAL
REASON: [one sentence]

PRIORITY_FIX_LIST:
P0 (blockers): [list]
P1 (this version): [list]
P2 (next version): [list]
P3 (track as issues): [list]
"""

# ── API call with retry ───────────────────────────────────────────────────────

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20))
def call_agent(system: str, user_message: str, label: str) -> str:
    """Call Claude with retry logic. Returns the text response."""
    print(f"  Calling {label}...", end="", flush=True)
    start = time.time()
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    elapsed = time.time() - start
    print(f" done ({elapsed:.1f}s)")
    return response.content[0].text


# ── Score parsing ─────────────────────────────────────────────────────────────

def parse_score(agent_output: str) -> int:
    """Extract the numeric score from agent output."""
    for line in agent_output.splitlines():
        if line.startswith("SCORE:"):
            try:
                return int(line.split(":")[1].split("/")[0].strip())
            except (ValueError, IndexError):
                pass
    # Fallback: search for "SCORE: N/100" anywhere
    import re
    match = re.search(r"SCORE:\s*(\d+)\s*/\s*100", agent_output)
    if match:
        return int(match.group(1))
    return 0


def parse_agent2_prompt(agent1_output: str) -> str:
    """Extract the AGENT_2_PROMPT block from Agent 1's output."""
    marker = "AGENT_2_PROMPT:"
    idx = agent1_output.find(marker)
    if idx != -1:
        return agent1_output[idx + len(marker):].strip()
    return "Agent 1 completed review. See full output above."


def parse_agent3_prompt(agent2_output: str) -> str:
    """Extract the AGENT_3_PROMPT block from Agent 2's output."""
    marker = "AGENT_3_PROMPT:"
    idx = agent2_output.find(marker)
    if idx != -1:
        return agent2_output[idx + len(marker):].strip()
    return "Agent 2 completed review. See full output above."


# ── Report writing ────────────────────────────────────────────────────────────

def write_report(
    output_path: Path,
    manifest_path: Path,
    iteration: int,
    scores: list[int],
    outputs: list[str],
    verdict: str,
    history: list[dict],
):
    """Write the final AUDIT_REPORT.md."""
    avg = sum(scores) / len(scores) if scores else 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Read project name from manifest
    project_name = "Unknown project"
    version = "unknown"
    if manifest_path.exists():
        for line in manifest_path.read_text().splitlines():
            if line.startswith("# ") and not project_name.startswith("U"):
                continue
            if "**Project**" in line or "project:" in line.lower():
                project_name = line.split(":", 1)[-1].strip().strip("*").strip()
            if "**Version**" in line or "**Current version**" in line:
                version = line.split(":", 1)[-1].strip().strip("*").strip()

    report = f"""# Audit Report
**Project:** {project_name}
**Version:** {version}
**Date:** {now}
**Iteration:** {iteration}

## Overall verdict: {verdict}

| Agent | Score | Max | Status |
|-------|-------|-----|--------|
| Agent 1 — Security & Architecture | {scores[0] if len(scores) > 0 else "—"} | 100 | {"✓" if len(scores) > 0 and scores[0] >= MIN_AGENT_SCORE else "✗"} |
| Agent 2 — Frontend/Backend Parity | {scores[1] if len(scores) > 1 else "—"} | 100 | {"✓" if len(scores) > 1 and scores[1] >= MIN_AGENT_SCORE else "✗"} |
| Agent 3 — Quality & Licensing | {scores[2] if len(scores) > 2 else "—"} | 100 | {"✓" if len(scores) > 2 and scores[2] >= MIN_AGENT_SCORE else "✗"} |
| **Average** | **{avg:.1f}** | 100 | {"✓ PASS" if avg >= PASS_THRESHOLD else "✗ FAIL"} |

Pass threshold: {PASS_THRESHOLD}/100 average, each agent ≥ {MIN_AGENT_SCORE}/100.

---

## Iteration history

| Iteration | Avg score | Verdict |
|-----------|-----------|---------|
"""
    for h in history:
        report += f"| {h['iteration']} | {h['avg']:.1f} | {h['verdict']} |\n"

    report += "\n---\n\n## Agent outputs\n\n"
    for i, output in enumerate(outputs, 1):
        report += f"### Agent {i} full output\n\n```\n{output}\n```\n\n"

    report += """---

## Next steps for Claude Code

1. Open `docs/SESSION_HANDOFF.md` and update it with these audit results.
2. Fix all P0 blockers before any deployment or version promotion.
3. After P0 fixes, re-run `python scripts/audit_pipeline.py` to verify.
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"\n  Report written to: {output_path}")


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(manifest_path: Path, max_iterations: int, dry_run: bool):
    """Run the full 3-agent audit pipeline with retry loop."""

    # Validate environment
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    # Collect code
    root = manifest_path.parent.parent  # docs/ is one level below root
    if not root.exists():
        root = Path(".")

    print(f"\n{'='*60}")
    print(f"  Audit Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Root: {root}")
    print(f"  Max iterations: {max_iterations}")
    print(f"{'='*60}\n")

    print("Collecting source files...")
    files = collect_files(root, manifest_path)
    print(f"  Collected {len(files)} files")

    manifest_content = ""
    if manifest_path.exists():
        manifest_content = manifest_path.read_text(encoding="utf-8", errors="replace")

    code_block = format_files_for_prompt(files)

    if dry_run:
        print("\nDRY RUN — would send the following files to agents:")
        for path in files:
            print(f"  {path}")
        print(f"\nTotal characters: {sum(len(c) for c in files.values())}")
        return

    history = []
    final_scores = []
    final_outputs = []
    final_verdict = "FAIL"

    for iteration in range(1, max_iterations + 1):
        print(f"\n── Iteration {iteration}/{max_iterations} ──────────────────")

        # ── Agent 1 ──────────────────────────────────────────────────────────
        print("\nAgent 1 — Security & Architecture")
        a1_user = (
            f"PROJECT MANIFEST:\n```\n{manifest_content}\n```\n\n"
            f"SOURCE CODE:\n{code_block}"
        )
        a1_output = call_agent(AGENT_1_SYSTEM, a1_user, "Agent 1")
        a1_score = parse_score(a1_output)
        print(f"  Score: {a1_score}/100")

        # ── Agent 2 ──────────────────────────────────────────────────────────
        print("\nAgent 2 — Frontend/Backend Parity")
        a2_context = parse_agent2_prompt(a1_output)
        a2_user = (
            f"AGENT 1 CONTEXT:\n{a2_context}\n\n"
            f"AGENT 1 FULL OUTPUT:\n```\n{a1_output}\n```\n\n"
            f"PROJECT MANIFEST:\n```\n{manifest_content}\n```\n\n"
            f"SOURCE CODE:\n{code_block}"
        )
        a2_output = call_agent(AGENT_2_SYSTEM, a2_user, "Agent 2")
        a2_score = parse_score(a2_output)
        print(f"  Score: {a2_score}/100")

        # ── Agent 3 ──────────────────────────────────────────────────────────
        print("\nAgent 3 — Code Quality & Licensing")
        a3_context = parse_agent3_prompt(a2_output)
        a3_user = (
            f"AGENT 2 CONTEXT:\n{a3_context}\n\n"
            f"AGENT 1 SCORE: {a1_score}/100\n"
            f"AGENT 2 SCORE: {a2_score}/100\n\n"
            f"AGENT 1 OUTPUT:\n```\n{a1_output}\n```\n\n"
            f"AGENT 2 OUTPUT:\n```\n{a2_output}\n```\n\n"
            f"PROJECT MANIFEST:\n```\n{manifest_content}\n```\n\n"
            f"SOURCE CODE:\n{code_block}"
        )
        a3_output = call_agent(AGENT_3_SYSTEM, a3_user, "Agent 3")
        a3_score = parse_score(a3_output)
        print(f"  Score: {a3_score}/100")

        # ── Evaluate ──────────────────────────────────────────────────────────
        scores = [a1_score, a2_score, a3_score]
        avg = sum(scores) / 3
        all_pass_minimum = all(s >= MIN_AGENT_SCORE for s in scores)

        if avg >= PASS_THRESHOLD and all_pass_minimum:
            verdict = "PASS"
        elif any(s < MIN_AGENT_SCORE for s in scores):
            verdict = "FAIL"
        else:
            verdict = "CONDITIONAL"

        print(f"\n  ── Results ──")
        print(f"  Agent 1: {a1_score}/100")
        print(f"  Agent 2: {a2_score}/100")
        print(f"  Agent 3: {a3_score}/100")
        print(f"  Average: {avg:.1f}/100")
        print(f"  Verdict: {verdict}")

        history.append({"iteration": iteration, "avg": avg, "verdict": verdict})
        final_scores = scores
        final_outputs = [a1_output, a2_output, a3_output]
        final_verdict = verdict

        if verdict == "PASS":
            print(f"\n✓ PASSED after {iteration} iteration(s)")
            break

        if iteration < max_iterations:
            print(f"\n  Score below threshold ({avg:.1f} < {PASS_THRESHOLD})")
            print("  Review the findings and fix P0/P1 issues, then re-run.")
            print("  (Pipeline will retry automatically in next iteration)")
            time.sleep(2)

    # Write report
    report_path = manifest_path.parent / "AUDIT_REPORT.md"
    write_report(
        output_path=report_path,
        manifest_path=manifest_path,
        iteration=len(history),
        scores=final_scores,
        outputs=final_outputs,
        verdict=final_verdict,
        history=history,
    )

    # Exit code: 0 = pass, 1 = fail
    print(f"\nFinal verdict: {final_verdict}")
    sys.exit(0 if final_verdict == "PASS" else 1)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="3-agent automated code audit pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--manifest",
        default="docs/PROJECT_MANIFEST.md",
        help="Path to PROJECT_MANIFEST.md (default: docs/PROJECT_MANIFEST.md)",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=3,
        help="Maximum audit iterations before giving up (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be sent to agents, without calling the API",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=PASS_THRESHOLD,
        help=f"Pass score threshold (default: {PASS_THRESHOLD})",
    )

    args = parser.parse_args()

    global PASS_THRESHOLD
    PASS_THRESHOLD = args.threshold

    manifest_path = Path(args.manifest)
    if not manifest_path.exists() and not args.dry_run:
        print(f"WARNING: Manifest not found at {manifest_path}")
        print("  The audit will proceed without project context.")
        print("  Run `python scripts/generate_manifest.py` first for better results.")

    run_pipeline(
        manifest_path=manifest_path,
        max_iterations=args.max_iter,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
