# Audit Report
**Project:** Unknown project
**Version:** unknown
**Date:** 2026-06-08 18:06
**Iteration:** 1

## Overall verdict: PASS

| Agent | Score | Max | Status |
|-------|-------|-----|--------|
| Agent 1 — Security & Architecture | 81 | 100 | ✓ |
| Agent 2 — Frontend/Backend Parity | 87 | 100 | ✓ |
| Agent 3 — Quality & Licensing | 93 | 100 | ✓ |
| **Average** | **87.0** | 100 | ✓ PASS |

Pass threshold: 85/100 average, each agent ≥ 70/100.

---

## Iteration history

| Iteration | Avg score | Verdict |
|-----------|-----------|---------|
| 1 | 87.0 | PASS |

---

## Agent outputs

### Agent 1 full output

```
I have everything I need. Here is the full Audit Agent 1 report.

---

SCORE: 81/100

BREAKDOWN:
S1: 13/15
S2: 15/15
S3: 8/10
S4: 2/5
S5: 5/5
A1: 16/20
A2: 7/10
A3: 8/10
A4: 7/10

---

FINDINGS:

**[MAJOR]** `scripts/audit_pipeline.py:25-32` — `except ImportError` block runs `subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic", "tenacity", "-q"])` at module import time. Any process that imports or `python scripts/audit_pipeline.py` runs auto-downloads arbitrary PyPI packages into whatever active environment is present, with no version pinning and no user consent. A yanked or compromised release of either package executes automatically. → Remove the auto-install block entirely. Add `anthropic` and `tenacity` to `pyproject.toml [project.optional-dependencies] dev`; fail with `sys.exit("Missing: pip install -e '.[dev]'")` if the import fails.

**[MAJOR]** `scripts/audit_pipeline.py:254` — `client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))` is evaluated unconditionally at module load time, before `USE_API` is checked and well before `main()` runs. Every invocation — including `--dry-run` and CLI mode — instantiates a client object with a blank key and no warning. The guard at line 416 (`if USE_API and not os.environ.get(...)`) arrives too late to prevent the object from being constructed. → Move client construction inside `call_agent()` or `_call_agent_api()`, gated on `if USE_API:`. Raise `ValueError` immediately if the key is absent when API mode is actually active.

**[MAJOR]** `pyproject.toml:9-18` — All ten production dependencies (`numpy`, `rich`, `PuLP`, `scikit-learn`, `torch`, `neat-python`, `jupyter`, `matplotlib`, `seaborn`, `plotly`) carry zero version constraints. `torch` is a repeat typosquatting target; an unpinned `pip install` always resolves to the latest release before PyPI can respond to a malicious upload. `environment.yml` is similarly unpinned. → Add lower-bound pinning (e.g. `torch>=2.2,<3`) for all deps. Run `pip-compile pyproject.toml -o requirements.lock` and commit the lock file; use it in CI.

**[MAJOR]** `scripts/generate_manifest.py:107` — `except Exception: pass` silently discards all errors from `json.loads(pkg.read_text(...))`. A malformed, zero-byte, or UTF-16 `package.json` produces an incomplete manifest with no diagnostic. `generate_manifest.py:215` and `:233` carry the same pattern in `extract_api_routes()` and `count_todos()` respectively. `generate_manifest.py:304` is a fourth instance in the main file-analysis loop. → Replace each with `except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e: warnings.warn(f"Skipped {path}: {e}")` or a `logging.warning(...)` call; never swallow multi-purpose exception blocks silently.

**[MINOR]** `src/sudoku/core/sudoku.py:78,83` — `get_cell(row, col)` and `set_cell(row, col, value)` perform no bounds check on `row`/`col`. An out-of-range index surfaces as a raw numpy `IndexError` (e.g. `index 10 is out of bounds for axis 0 with size 9`) with no hint about the valid range 0–8. → Add `if not (0 <= row <= 8 and 0 <= col <= 8): raise ValueError(f"row and col must be 0–8, got row={row}, col={col}")` at the top of both methods.

**[MINOR]** `src/sudoku/core/sudoku.py:103` — `from_string` validates string length then calls `int(ch)` in a list comprehension with no per-character check. A string like `"53X07000…"` raises `ValueError: invalid literal for int() with base 10: 'X'` with no position information. → Add `if not all(c.isdigit() for c in s): raise ValueError(f"String must contain digits 0–9 only")` after the length check, before the `int()` conversion.

**[MINOR]** `environment.yml:8` — `scipy` is declared as a conda dependency but is absent from `pyproject.toml`. A developer installing via `pip install -e .` will not get scipy, causing silent import failures once any module that needs it (likely `montecarlo` or `ml`) is implemented. → Add `scipy` to `pyproject.toml [project] dependencies`.

**[MINOR]** `src/sudoku/__init__.py:2` — `BaseSolver` is re-exported at the package root (`from sudoku.solvers.base import BaseSolver`). This is an abstract base class with no public-use case at the package root; it leaks solver implementation structure into the top-level API and will complicate future `__all__` hygiene. → Remove `BaseSolver` from `src/sudoku/__init__.py`; consumers who need it should import from `sudoku.solvers`.

---

AGENT_2_PROMPT:

You are Audit Agent 2 reviewing **sudoku-lab** at version **v0.0**.

Agent 1 scored **81/100**.

**Critical/Major issues found:**
- Auto-install of `anthropic`/`tenacity` via `subprocess.check_call` at import time (`scripts/audit_pipeline.py:25-32`) — supply chain risk
- Module-level Anthropic client construction with empty-string key fallback, fires unconditionally before `USE_API` is checked (`scripts/audit_pipeline.py:254`)
- All production deps in `pyproject.toml` and `environment.yml` carry zero version constraints; no lock file present
- Four silent `except Exception: pass` clauses in `scripts/generate_manifest.py` (lines 107, 215, 233, 304) — analysis failures produce incomplete manifests with no diagnostic

**Context you need:** sudoku-lab v0.0 is a **pure Python library** with no web server and no HTTP endpoints (manifest reports 0 API routes). The package surface is `src/sudoku/` with a `Sudoku` core class, a `BaseSolver` ABC, and eight empty stub modules (`benchmark`, `dl`, `game`, `generator`, `ml`, `montecarlo`, `viz`, `solvers` sub-items). Since the last audit cycle, `tests/test_base_solver.py` has been added with `IdentitySolver` and `AlwaysFailSolver` stubs and four benchmark tests.

**Specific things to check:**

1. **Import consistency** — does `src/sudoku/__init__.py` export exactly what the sub-packages expose? Verify `BaseSolver` is reachable as `from sudoku.solvers import BaseSolver` and as `from sudoku import BaseSolver`, and that neither import path is broken. Flag any mismatch.

2. **BaseSolver ↔ Sudoku contract** — does `BaseSolver.benchmark()` call `puzzle.copy()`, `result.is_solved()`, and `self.solve()` in a way that is consistent with the contracts documented in `README.md`? Specifically: does the benchmark time window correctly cover the solve, and does it handle the `ValueError` path without leaking time bias?

3. **Test coverage parity** — `tests/test_base_solver.py` now exists. Verify it covers: (a) the `ValueError` branch in `benchmark()`, (b) `n_runs > 1` accumulation, (c) the `total=0` edge case. Flag any gaps.

4. **`environment.yml` vs `pyproject.toml` divergence** — Agent 1 found that `scipy` appears in `environment.yml` but not in `pyproject.toml`. Check for any other dependency divergences (version conflicts, missing entries, conda-name vs pip-name differences like `pytorch` vs `torch`) that would produce different installed environments depending on install path.

5. **Stub module risk** — eight empty `__init__.py` stubs are importable but do nothing. Identify any that, given the architecture documented in `README.md` and `SESSION_HANDOFF.md`, could cause a silent `AttributeError` or `ImportError` when a caller does `from sudoku.montecarlo import SQASolver` or similar before the stub is filled in.
```

### Agent 2 full output

```
---

SCORE: 87/100

BREAKDOWN:
P1: 17/20
P2: 13/15
P3: 8/10
P4: 5/5
C1: 15/20
C2: 15/15
C3: 10/10
C4: 4/5

---

**Reviewer notes on scope adaptation:** sudoku-lab v0.0 has no frontend, no HTTP endpoints, and no async layer. P4/C2/C3 are scored N/A (full marks). "Parity" is interpreted as internal API contract consistency: export paths, BaseSolver↔Sudoku contract, test coverage symmetry with implementation, and dependency-list coherence.

---

FINDINGS:

**[MAJOR]** `tests/test_base_solver.py` — The `total=0` edge case (empty puzzle list passed to `benchmark([])`) has no test. The guard `if total else 0.0` at `base.py:43` and `if times else 0.0` at `base.py:44-46` are correct but completely unexercised. A future refactor that removes either guard would introduce a `ZeroDivisionError` with no regression baseline. → Add `test_benchmark_empty_puzzle_list()`: call `IdentitySolver().benchmark([])` and assert `total == 0`, `solve_rate == 0.0`, `solved == 0`, `mean_time_s == 0.0`.

**[MAJOR]** `src/sudoku/solvers/base.py` + `src/sudoku/benchmark/__init__.py` — Logic ownership ambiguity: `README.md` maps `src/sudoku/benchmark/` as the "Benchmarking harness" module, yet all timing, accumulation, and result-dict logic lives in `BaseSolver.benchmark()`. When `benchmark/` is eventually implemented, there is no stated boundary — developers will face a choice between extending `BaseSolver.benchmark()` (bad for multi-solver comparisons) or duplicating its logic in `benchmark/`. → Add a one-line docstring to `src/sudoku/benchmark/__init__.py` now: `"""Multi-solver comparison harness. Per-solver micro-benchmark lives in BaseSolver.benchmark()."""` This draws the boundary before the module is filled in.

**[MINOR]** `src/sudoku/solvers/base.py:28` — `puzzle.copy()` is called inside the `perf_counter` window (`t0` is set on line 26, `copy()` on line 28). Copy overhead is included in every timing sample. For a 9×9 numpy array the copy is sub-microsecond and practically negligible, but semantically the benchmark claims to measure `solve()` time. → Move `copy = puzzle.copy()` to before `t0 = time.perf_counter()`, then call `self.solve(copy)` inside the window.

**[MINOR]** `environment.yml` vs `pyproject.toml` — Three additional divergences beyond the `scipy` gap Agent 1 flagged: (1) `pytorch` is the conda-forge package name while `pyproject.toml` uses `torch` (the pip name); these install the same package but potentially different build variants (CPU-only vs. CUDA) depending on the resolved channel — developers on the two paths may get different hardware backends silently; (2) `pytest-cov` is in `pyproject.toml [dev]` but absent from `environment.yml`'s pip section — conda-path developers lose coverage tooling with no error; (3) `pytest` and `ruff` are listed as top-level pip extras in `environment.yml` but as `[project.optional-dependencies] dev` in `pyproject.toml` — the categorisation mismatch is cosmetic but makes the two files harder to keep in sync. → Add `pytest-cov` to `environment.yml` pip section; add a comment on the `pytorch` entry noting it installs as `torch`; align the `pytest`/`ruff` categories.

**[MINOR]** `tests/test_base_solver.py` — No test verifies that `benchmark()` does not mutate the caller's puzzle. The code correctly calls `puzzle.copy()` per run, but the isolation guarantee is not asserted. If a future solver were inadvertently called on the original, all subsequent runs in the same list loop would see a corrupted board. → Add `test_benchmark_does_not_mutate_input()`: snapshot `puzzle.to_string()` before calling `benchmark([puzzle])`, assert it is unchanged after.

**[MINOR]** `src/sudoku/montecarlo/__init__.py`, `src/sudoku/dl/__init__.py`, `src/sudoku/ml/__init__.py` — `SESSION_HANDOFF.md` names planned classes (`SQASolver`, AMP trainer, classical ML solvers) for these three modules. All three files are empty. `from sudoku.montecarlo import SQASolver` raises `ImportError: cannot import name 'SQASolver' from 'sudoku.montecarlo'` with no guidance that the class is planned but not yet implemented. For the other four stubs (`benchmark`, `game`, `generator`, `viz`) the situation is the same but less immediately misleading because the README does not name specific classes. → Add a one-line module docstring to each of the three named stubs listing planned exports and target version (e.g., `"""Quantum Monte Carlo solvers — SQASolver, PIMCSolver — planned for v0.2."""`).

**[MINOR]** `src/sudoku/core/sudoku.py` — The integer literal `9` appears 11 times across row/col range checks, box boundary slicing, `__repr__`, and shape validation. There is no `_BOARD_SIZE = 9` module-level constant. Any future non-standard board size requires a grep-and-replace through a file the user-visible API depends on. → Define `_BOARD_SIZE = 9` at the top of `sudoku.py` and substitute all occurrences.

---

AGENT_3_PROMPT:

You are Audit Agent 3 reviewing **sudoku-lab** at version **v0.0**.

Agent 1 scored **81/100**. Agent 2 scored **87/100**.

**Combined critical and major issues from both agents:**
- Auto-install of `anthropic`/`tenacity` via `subprocess.check_call` at import time (`scripts/audit_pipeline.py:25-32`) — supply chain risk [A1]
- Module-level Anthropic client construction with empty-string key fallback, fires before `USE_API` check (`scripts/audit_pipeline.py:254`) [A1]
- All production deps in `pyproject.toml` and `environment.yml` carry zero version constraints; no lock file present [A1]
- Four silent `except Exception: pass` clauses in `scripts/generate_manifest.py` (lines 107, 215, 233, 304) [A1]
- `tests/test_base_solver.py` missing `total=0` (empty puzzle list) edge case test — zero-division guard exists but is unexercised [A2]
- `BaseSolver.benchmark()` logic ownership conflicts with planned `src/sudoku/benchmark/` module — no boundary documented [A2]

**Context you need:** sudoku-lab v0.0 is a pure Python library. No web server, no HTTP endpoints, no frontend. Package surface: `src/sudoku/` with `Sudoku` core class, `BaseSolver` ABC, and eight stub modules. Two test files exist: `tests/test_core.py` (7 tests covering `Sudoku`) and `tests/test_base_solver.py` (4 tests covering `BaseSolver.benchmark()`). Dev tooling: `ruff`, `pytest`, `pytest-cov`. A `LICENSE` file is present (contents not shown to Agent 2 — verify it exists and identify the license type). No CI configuration was found in the file tree.

**Your task:** Review code quality and licensing, then produce the final `docs/AUDIT_REPORT.md`.

Specifically check:
1. **License file** — what license is declared? Are any dependencies (`torch`, `PuLP`, `neat-python`, `scikit-learn`, `scipy`) license-incompatible with the declared project license?
2. **Static analysis** — are there `ruff` findings beyond what Agents 1 and 2 flagged? Check for unused imports, missing type annotations on public APIs, and `TYPE_CHECKING` guard usage in `base.py`.
3. **Test coverage** — `test_core.py` covers 7 `Sudoku` methods; `test_base_solver.py` covers `benchmark()` but misses `total=0` and mutation isolation. What is the estimated line coverage percentage for `src/sudoku/`? Flag any non-empty module with zero test coverage.
4. **File size and function length** — `scripts/audit_pipeline.py` is 597 lines and `scripts/generate_manifest.py` is 520 lines. Are any functions in `src/sudoku/` over the 40-line limit? (Per `docs/AUDIT_PROMPTS.md`, the 300-line limit does NOT apply to `scripts/`.)
5. **TODO/FIXME density** — `PROJECT_MANIFEST.md` reports 2 files with TODO markers and 2 with FIXME markers. Locate them and assess whether any are blocking for v0.0 acceptance.
6. **Debug statements** — `audit_pipeline.py` has 40 `print()` calls and `generate_manifest.py` has 9. Per `docs/AUDIT_PROMPTS.md`, print statements in `scripts/` are intentional progress reporting and should NOT be flagged. Confirm no `print()` statements exist in `src/sudoku/` source files.
```

### Agent 3 full output

```
The write needs your approval. Here is the complete Agent 3 output to display while you decide:

---

```
SCORE: 93/100

BREAKDOWN:
Q1: 17/20
Q2: 10/10
Q3: 4/5
Q4: 7/10
Q5: 5/5
L1: 10/10
L2: 30/30
L3: 10/10

FINDINGS:
[MINOR] tests/test_core.py:2 – `import pytest` unused (ruff F401) → Remove the unused import.
[MINOR] pyproject.toml – [tool.ruff] only sets line-length; no [tool.ruff.lint] section means isort/naming/RUF rules disabled → Add [tool.ruff.lint] with select = ["E","F","I","N","RUF"].
[MINOR] src/sudoku/core/sudoku.py – display() (22 lines, primary user-facing method) has zero test coverage → Add test_display_runs_without_error() using Console(record=True).

LICENSE: MIT License — present, complete, 21 lines. All dependencies (numpy BSD-3, rich MIT, PuLP MIT, torch BSD-3, scikit-learn BSD-3, neat-python Apache-2.0, scipy BSD-3, matplotlib PSF, seaborn BSD-3, plotly MIT) are MIT-compatible. No GPL/AGPL anywhere in tree. L2 is a clean 30/30.

VERDICT: CONDITIONAL
REASON: Average agent score (87/100) clears the 85-point pass threshold and all agents score ≥70, but two P0 issues (auto-pip-install at import time, unpinned production deps with no lock file) must be resolved before the project can be declared audit-clean.

PRIORITY_FIX_LIST:
P0 (blockers):
  - Remove subprocess auto-install of anthropic/tenacity at import time (scripts/audit_pipeline.py:25-32)
  - Add version lower-bounds to all production deps in pyproject.toml; commit requirements.lock

P1 (this version):
  - Move Anthropic client construction inside _call_agent_api(), gate on USE_API (audit_pipeline.py:254)
  - Replace four except Exception: pass with scoped handlers + warnings.warn (generate_manifest.py:107,215,233,304)
  - Add test_benchmark_empty_puzzle_list() for total=0 edge case (tests/test_base_solver.py)
  - Add docstring to src/sudoku/benchmark/__init__.py documenting logic boundary

P2 (next version):
  - Add [tool.ruff.lint] select/ignore to pyproject.toml
  - Add test coverage for display() using Console(record=True)
  - Add test_benchmark_does_not_mutate_input()
  - Move puzzle.copy() before t0 = time.perf_counter() (base.py:26-28)
  - Add bounds checks to get_cell/set_cell (sudoku.py:78,83)
  - Add per-character validation to from_string (sudoku.py:103)
  - Align environment.yml and pyproject.toml deps

P3 (track as issues):
  - Remove BaseSolver from top-level __init__.py
  - Add docstrings to montecarlo/dl/ml stub __init__.py
  - Define _BOARD_SIZE = 9 constant in sudoku.py
  - Remove unused `import pytest` from tests/test_core.py
  - Triage docs/PROJECT_MANIFEST.md TODO placeholders
```

---

**Three-agent final average: (81 + 87 + 93) / 3 = 87/100 — CONDITIONAL PASS**

Once you approve the write, `docs/AUDIT_REPORT.md` will be replaced with the full consolidated report covering all three agents' findings, license analysis, and the priority fix list.
```

---

## Next steps for Claude Code

1. Open `docs/SESSION_HANDOFF.md` and update it with these audit results.
2. Fix all P0 blockers before any deployment or version promotion.
3. After P0 fixes, re-run `python scripts/audit_pipeline.py` to verify.
