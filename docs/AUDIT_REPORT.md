# Audit Report
**Project:** Unknown project
**Version:** unknown
**Date:** 2026-06-09 12:28
**Iteration:** 1

## Overall verdict: PASS

| Agent | Score | Max | Status |
|-------|-------|-----|--------|
| Agent 1 — Security & Architecture | 82 | 100 | ✓ |
| Agent 2 — Frontend/Backend Parity | 87 | 100 | ✓ |
| Agent 3 — Quality & Licensing | 89 | 100 | ✓ |
| **Average** | **86.0** | 100 | ✓ PASS |

Pass threshold: 85/100 average, each agent ≥ 70/100.

---

## Iteration history

| Iteration | Avg score | Verdict |
|-----------|-----------|---------|
| 1 | 86.0 | PASS |

---

## Agent outputs

### Agent 1 full output

```
I have everything I need. Here is the full audit report for **sudoku-lab v0.2**.

---

```
SCORE: 82/100

BREAKDOWN:
S1: 13/15
S2: 15/15
S3: 7/10
S4: 2/5
S5: 5/5
A1: 17/20
A2: 8/10
A3: 8/10
A4: 7/10
```

---

**Scoring rationale**

- **S1 (13/15):** No hardcoded secrets, `.env.example` present. Deduction for `scripts/audit_pipeline.py:254` — Anthropic client constructed at module scope with an empty-string key fallback; every invocation (including `--dry-run`) instantiates a live client object with no key and silently fails later.
- **S2 (15/15):** Local CLI/library — no web surface, no auth plane. Full marks.
- **S3 (7/10):** Three input-validation gaps remain unfixed (bounds, char validation, KeyError on bad preset).
- **S4 (2/5):** Auto-install and zero version pinning both unfixed from prior two audits.
- **S5 (5/5):** No network surface. Full marks.
- **A1 (17/20):** Win-overlay text rendered in controller (`sudoku_game.py`) rather than renderer (`renderer.py`). All other separation is clean.
- **A2 (8/10):** Unused `field` import in `state.py`; stale `Untitled.ipynb` artefact. New `solve/__main__.py` print statements are intentional CLI output — manifest tool false-positives on them.
- **A3 (8/10):** `BaseSolver` still re-exported at package root, leaking implementation detail.
- **A4 (7/10):** Four silent `except`/`pass` clauses in `generate_manifest.py` still unfixed; missing bounds checks in core API; bare `KeyError` in `from_preset`.

---

```
FINDINGS:

[MAJOR] scripts/audit_pipeline.py:28-32 – Auto-install of `anthropic` and `tenacity`
via `subprocess.check_call` fires at import time whenever the packages are missing.
UNFIXED from v0.0 and v0.1 audits. Any process running this script auto-downloads
arbitrary PyPI packages — unpinned, no hash verification, no user consent. A yanked
or compromised release executes automatically. → Remove the except-ImportError block;
add `anthropic` and `tenacity` to `pyproject.toml [project.optional-dependencies] dev`
and replace with `sys.exit("Missing: pip install -e '.[dev]'")` if the import fails.

[MAJOR] scripts/audit_pipeline.py:254 – `client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))`
is evaluated at module scope, unconditionally, before `USE_API` is ever checked.
UNFIXED from v0.0 and v0.1 audits. `--dry-run` mode still constructs an API client
with a blank key; the first real API call then raises an AuthenticationError with no
clear diagnostic. → Move client construction inside `call_agent()`, gated on
`if USE_API:`, and raise `ValueError("ANTHROPIC_API_KEY not set")` immediately when
key is absent and API mode is active.

[MAJOR] pyproject.toml:9-18 + environment.yml:5-21 – All production dependencies carry
zero version constraints. UNFIXED from v0.0 and v0.1 audits. `torch`, `neat-python`,
`PuLP`, `ipympl`, and `matplotlib` are all unpinned. No lock file present. A
`pip install -e .` on a new machine can silently resolve an incompatible or yanked
release. → Add lower-bound + upper-bound pins for every dependency
(e.g. `matplotlib>=3.8,<4`); run `pip-compile pyproject.toml` and commit the
resulting `requirements.txt` or `uv.lock`.

[MAJOR] scripts/generate_manifest.py:107,215,233,304 – Four bare `except Exception: pass`
(or `except Exception: pass`) clauses silently discard all errors from JSON parsing
(line 107), API route extraction (line 215), TODO counting (line 233), and generic
file analysis (line 304). UNFIXED from v0.0 and v0.1 audits. Manifest outputs can
be silently wrong with no diagnostic. → Replace each with a specific except that
emits a warning:
  `except (json.JSONDecodeError, OSError) as e: warnings.warn(f"Skipped: {e}")`

[MINOR] src/sudoku/game/sudoku_game.py:23 – `PRESET_MAP[difficulty.lower()]` raises a
bare `KeyError` for any unrecognised difficulty string (e.g. `from_preset("extreme")`
produces `KeyError: 'extreme'` with no hint of valid values). UNFIXED from v0.1 audit.
→ Replace with:
  `puzzle_str = PRESET_MAP.get(difficulty.lower())`
  `if puzzle_str is None: raise ValueError(f"Unknown difficulty {difficulty!r}; choose from {list(PRESET_MAP)}")`

[MINOR] src/sudoku/game/state.py:4 – `field` is imported from `dataclasses` but never
used. `completion_time: float | None = None` uses a plain default, not
`field(default=None)`. UNFIXED from v0.1 audit.
→ Change import to `from dataclasses import dataclass`.

[MINOR] src/sudoku/game/sudoku_game.py:67-79 – The "Solved!" win overlay is rendered
via `ax.text(...)` directly inside `SudokuGame._render()` rather than inside
`draw_board()` in `renderer.py`. UNFIXED from v0.1 audit. Any second rendering path
(export-to-PNG, screenshot in tests) would silently omit the overlay.
→ Add `solved_label: str | None = None` parameter to `draw_board()` and move the
`ax.text(...)` call there; pass `state.solved` label from `_render()`.

[MINOR] src/sudoku/core/sudoku.py:78,83 – `get_cell()` and `set_cell()` perform no
bounds check on `row`/`col`. UNFIXED from v0.1 audit. Out-of-range indices surface
as a raw numpy `IndexError` with no hint of the valid 0–8 range.
→ Add at the top of each method:
  `if not (0 <= row <= 8 and 0 <= col <= 8): raise ValueError(f"row and col must be 0–8, got row={row}, col={col}")`

[MINOR] src/sudoku/core/sudoku.py:103 – `from_string()` calls `int(ch)` inside a list
comprehension with no per-character pre-validation. UNFIXED from v0.1 audit. A string
containing a non-digit character (e.g. `'.'`, `'X'`) raises a generic
`ValueError: invalid literal for int()` with no position context.
→ Add before the `np.array(...)` line:
  `if not s.isdigit(): raise ValueError(f"String must contain only digits 0–9; got unexpected characters")`

[MINOR] src/sudoku/__init__.py:2 – `BaseSolver` is re-exported at the package root.
UNFIXED from v0.1 audit. It leaks a solver implementation detail into the top-level
public API; consumers should import from `sudoku.solvers`.
→ Remove `BaseSolver` from `src/sudoku/__init__.py`; keep only `Sudoku` and
`BacktrackingSolver` if convenience re-export is desired.

[MINOR] environment.yml:8 – `scipy` declared as a conda dependency but absent from
`pyproject.toml [project] dependencies`. UNFIXED from v0.1 audit. A `pip install -e .`
without conda will not install `scipy`, breaking any code that imports it.
→ Add `scipy` to `pyproject.toml [project] dependencies`.
```

---

```
AGENT_2_PROMPT:

You are Audit Agent 2 reviewing **sudoku-lab** at version **v0.2**.
Agent 1 scored **82/100**.

**Major issues found:**
- Auto-install of `anthropic`/`tenacity` via `subprocess.check_call` at import time
  (`scripts/audit_pipeline.py:28-32`) — unfixed supply-chain risk, third consecutive audit
- Module-level Anthropic client constructed with empty-string key fallback before
  `USE_API` is checked (`scripts/audit_pipeline.py:254`) — unfixed, third consecutive audit
- All production deps in `pyproject.toml` and `environment.yml` carry zero version
  constraints; no lock file — unfixed, third consecutive audit
- Four silent `except Exception: pass` clauses in `scripts/generate_manifest.py`
  (lines 107, 215, 233, 304) — unfixed, third consecutive audit

**Context you need:** sudoku-lab v0.2 is a **pure Python library** with no web server
and no HTTP endpoints (manifest reports 0 API routes). The new surface added in v0.2 is:
- `src/sudoku/solvers/backtracking.py` — `BacktrackingSolver` with MRV heuristic
- `src/sudoku/solvers/base.py` — `UnsolvableError(ValueError)` added; `benchmark()`
  now catches `UnsolvableError` specifically instead of broad `ValueError`; `__all__` added
- `src/sudoku/core/sudoku.py` — `to_array() -> np.ndarray` method added
- `src/sudoku/solve/__main__.py` — CLI entry point: `python -m sudoku.solve [easy|medium|hard|<81-char>]`
- `src/sudoku/solvers/__init__.py` — exports `BacktrackingSolver`
- `src/sudoku/__init__.py` — re-exports `BacktrackingSolver` (and still re-exports `BaseSolver`)
- `tests/test_backtracking.py` — 7 new solver tests (26 total, all pass)
- `notebooks/01_backtracking.ipynb` — benchmark notebook

**Specific things to check:**

1. **Solver API contract** — `BacktrackingSolver.solve(puzzle: Sudoku) -> Sudoku` must return
   a solved `Sudoku` (i.e. `result.is_solved()` is True) or raise `UnsolvableError`. Verify:
   (a) the return type annotation and the test `test_solves_easy/medium/hard` are consistent;
   (b) `solve()` never mutates its input (test `test_does_not_mutate_input` covers this —
   confirm it calls `puzzle.to_array()` which copies the board, not a reference);
   (c) the `BaseSolver.benchmark()` `solve_rate` field is computed against `result.is_solved()`,
   not just the absence of an exception — confirm this holds for the identity-solver test
   `test_benchmark_solve_rate_perfect`.

2. **`UnsolvableError` import paths** — The exception is defined in `sudoku.solvers.base`
   and re-exported in `sudoku.solvers.__init__` (via `BaseSolver` but not explicitly `UnsolvableError`).
   `tests/test_backtracking.py` imports `from sudoku.solvers.base import UnsolvableError`.
   `src/sudoku/solve/__main__.py` imports `from sudoku.solvers.base import UnsolvableError`.
   Verify that `UnsolvableError` is accessible from `sudoku.solvers` (the public package API)
   — if not, the `__init__.py` should export it explicitly so consumers don't have to
   reach into `base`.

3. **`to_array()` ownership** — `BacktrackingSolver.solve()` calls `puzzle.to_array()` to
   get a mutable numpy copy, mutates it, then constructs a new `Sudoku(board)`. Confirm
   `Sudoku.__init__` calls `arr.copy()` on the array passed to it, so the solver's local
   `board` variable and the returned `Sudoku` do not share backing memory.

4. **`benchmark()` narrowing** — `BaseSolver.benchmark()` now catches `UnsolvableError`
   only (not broad `ValueError`). Confirm the change does not leave unhandled exceptions for
   puzzles that raise `ValueError` from malformed input (e.g. wrong-shape board). Since
   `benchmark()` is designed to run over pre-validated `Sudoku` instances the restriction
   is intentional — confirm no test path exercises this gap.

5. **CLI arg handling** — `src/sudoku/solve/__main__.py:11` does
   `puzzle_str = PRESET_MAP.get(arg.lower(), arg)` and then checks `len(puzzle_str) != 81`.
   This means an unrecognised short string (e.g. "foo") falls through with a helpful error.
   Confirm the error message names the valid preset keys, not just the character count.

6. **`__all__` coverage** — `src/sudoku/solvers/base.py` exports `__all__ = ["BaseSolver", "UnsolvableError"]`.
   `src/sudoku/solvers/__init__.py` only re-exports `BaseSolver` and `BacktrackingSolver` —
   `UnsolvableError` is NOT in `__init__.py.__all__`. Flag this as a consistency gap:
   consumers who do `from sudoku.solvers import *` will not get `UnsolvableError`.
```
```

### Agent 2 full output

```
All six checks verified. Here is the complete Agent 2 report.

---

```
SCORE: 87/100

BREAKDOWN:
P1: 16/20
P2: 12/15
P3: 10/10
P4: 5/5
C1: 15/20
C2: 15/15
C3: 10/10
C4: 4/5
```

---

**Scoring rationale**

- **P1 (16/20):** The solver API contract (`solve(Sudoku) -> Sudoku | raise UnsolvableError`) is well-specified and fully tested. Deduct 4 because `UnsolvableError` — part of the API contract — is not accessible from the public package interface (`sudoku.solvers` or `sudoku`). Both the CLI and the test suite bypass the public surface by importing `from sudoku.solvers.base import UnsolvableError` directly. Any consumer that tries `from sudoku.solvers import UnsolvableError` gets an `ImportError`.
- **P2 (12/15):** New solver logic is correctly owned by `BacktrackingSolver`; MRV heuristic stays internal. Deduct 3 for the win overlay rendered in `SudokuGame._render()` rather than `renderer.py:draw_board()` — unfixed from v0.1 audit, third consecutive version with this placement issue.
- **P3 (10/10):** Data shapes are fully consistent end-to-end. `to_array()` returns `self._board.copy()`; `Sudoku.__init__` calls `arr.copy()`; no aliasing between the solver's working buffer and the returned `Sudoku`. `benchmark()` passes `puzzle.copy()` to solvers, protecting the benchmark inputs. `frozenset`/`set` types for `given_cells`/`conflicts` match between `GameState` and `draw_board()`.
- **P4 (5/5):** N/A — no i18n layer.
- **C1 (15/20):** `benchmark()` catches `UnsolvableError` only (intentional narrowing from `ValueError`). The narrowing is correct for pre-validated inputs and documented in the session handoff. No test exercises the gap where a solver raises a plain `ValueError` through `benchmark()`, confirming the gap is unexercised. Deduct 5 for the `UnsolvableError` export inconsistency — the exception is the primary failure mode of the solver contract, yet all import sites reach into the internal `sudoku.solvers.base` submodule rather than the public interface.
- **C2 (15/15):** N/A — no auth layer.
- **C3 (10/10):** `perf_counter()` is used in both the `UnsolvableError` except branch and the success branch of `benchmark()`, so timing is captured regardless of outcome. CLI timing is correct.
- **C4 (4/5):** `PRESET_MAP` is the single source of truth for preset names and is imported correctly in both `game/` and `solve/`. Deduct 1 because the CLI error message at `__main__.py:13` hardcodes `"easy/medium/hard"` as a literal string rather than deriving from `PRESET_MAP.keys()` — adding a fourth preset would silently produce a misleading error message.

---

```
FINDINGS:

[MAJOR] src/sudoku/solvers/__init__.py:4 – UnsolvableError is declared in
`base.py __all__` but not re-exported in `solvers/__init__.py.__all__`.
Neither `from sudoku.solvers import UnsolvableError` nor
`from sudoku import UnsolvableError` works; both tests/test_backtracking.py:6
and src/sudoku/solve/__main__.py:6 bypass the public package interface with
`from sudoku.solvers.base import UnsolvableError`. Any consumer that follows
the documented import pattern (`from sudoku.solvers import …`) cannot access
the exception that defines the solver failure contract.
→ Add `from .base import UnsolvableError` and `"UnsolvableError"` to `__all__`
in `src/sudoku/solvers/__init__.py`; also add to `src/sudoku/__init__.py __all__`
for top-level accessibility. Update both import sites to use the public path.

[MINOR] src/sudoku/solve/__main__.py:13 – CLI error message for an unrecognised
argument hardcodes `"easy/medium/hard"` and frames the problem as a character-
count mismatch (`"got N chars"`). For an input like `"extreme"` (len=7), the
user sees `"expected 81-char string or easy/medium/hard, got 7 chars"`, which
implies they passed a 7-character puzzle string rather than an unrecognised
preset name. The message also won't stay in sync if PRESET_MAP gains new keys.
→ Replace with:
  `valid = list(PRESET_MAP)`
  `if arg.lower() not in valid:`
  `    print(f"Error: unrecognised preset {arg!r}; valid presets: {valid} (or pass an 81-char string)")`
  `    sys.exit(1)`
  `elif len(puzzle_str) != 81:`
  `    print(f"Error: puzzle string must be 81 chars, got {len(puzzle_str)}")`
  `    sys.exit(1)`

[MINOR] src/sudoku/game/sudoku_game.py:67-79 – Win overlay (`"Solved!"` text
box) rendered directly in `SudokuGame._render()` rather than inside
`renderer.py:draw_board()`. UNFIXED from v0.1 and v0.0 audits. Any second
rendering path (export-to-PNG, headless screenshot, test fixture calling
`draw_board()` directly) silently omits the win overlay. `test_renderer_runs`
in tests/test_game.py calls `draw_board()` directly and would not catch this.
→ Add `solved_text: str | None = None` parameter to `draw_board()`; move the
`ax.text(...)` call there; pass `f"Solved!\n{moves} moves in {elapsed:.0f}s"`
from `_render()` when `state.solved` is True.

[MINOR] src/sudoku/solvers/base.py:38 (benchmark) – The narrowed
`except UnsolvableError` catch leaves any plain `ValueError` raised inside
`solve()` to propagate unhandled out of `benchmark()`. This is intentional for
pre-validated inputs, but no test exercises the gap (e.g. an `IdentitySolver`
called via `benchmark()` with an unsolved puzzle would raise plain `ValueError`,
not `UnsolvableError`, and crash the benchmark loop).
→ Document the assumption in a short docstring on `benchmark()`:
  `"""Run solver over puzzles. All items in puzzles must be pre-validated
  Sudoku instances; solvers are expected to raise UnsolvableError, not
  ValueError, for logical failures."""`
```

---

```
AGENT_3_PROMPT:

You are Audit Agent 3 reviewing **sudoku-lab** at version **v0.2**.
Agent 1 scored **82/100**. Agent 2 scored **87/100**.

**Combined critical issues from Agents 1 and 2:**
- Auto-install of `anthropic`/`tenacity` via `subprocess.check_call` at import
  time (`scripts/audit_pipeline.py:28-32`) — unfixed supply-chain risk, THIRD
  consecutive audit
- Module-level Anthropic client constructed with empty-string key fallback
  (`scripts/audit_pipeline.py:254`) — unfixed, THIRD consecutive audit
- All production deps in `pyproject.toml` and `environment.yml` carry zero
  version constraints; no lock file — unfixed, THIRD consecutive audit
- Four silent `except Exception: pass` clauses in `scripts/generate_manifest.py`
  (lines 107, 215, 233, 304) — unfixed, THIRD consecutive audit
- `UnsolvableError` not exported from `sudoku.solvers` or `sudoku` public
  packages; all consumers reach into `sudoku.solvers.base` directly — breaks
  the published solver API contract for exception handling

**Your task:** review code quality, static analysis cleanliness, test coverage,
file/function sizes, TODO density, debug statement density, and license
compliance. Then produce the final `docs/AUDIT_REPORT.md`.

**Key things to check:**

1. **Test coverage gap** — `benchmark()` with a non-`UnsolvableError` exception
   path is not exercised. `test_does_not_mutate_input` also implicitly covers
   non-mutation; verify no test is redundant or misleadingly named.

2. **`to_array()` test coverage** — new method in v0.2; `tests/test_core.py`
   has `test_get_set_cell_and_copy` but no explicit `test_to_array`. Check
   whether the backtracking tests provide sufficient coverage or a dedicated
   test is needed.

3. **File/function size** — `scripts/audit_pipeline.py` is 597 lines;
   `scripts/generate_manifest.py` is 520 lines. Per `docs/AUDIT_PROMPTS.md`,
   the 300-line limit does NOT apply to `scripts/`. Apply the standard 300-line
   limit only to `src/` and `tests/`.

4. **Debug statements** — `src/sudoku/solve/__main__.py` has 4 `print()`
   calls flagged by the manifest tool. Per `docs/AUDIT_PROMPTS.md`, `print()`
   in CLI entry points is intentional progress reporting, not debug output.
   Do NOT flag these.

5. **License** — `LICENSE` is MIT (21 lines). Verify every dependency in
   `pyproject.toml` and `environment.yml` is MIT/BSD/Apache-compatible.
   `PuLP` is MIT; `neat-python` is Apache-2.0; `torch` is BSD; `scipy` is
   BSD. Flag any GPL or AGPL dependency.

6. **TODO/FIXME density** — `docs/PROJECT_MANIFEST.md` is full of TODO
   placeholders (version still shows `v0.0`; tech stack not filled in; all
   file purposes say "TODO"). This is a manifest-tooling quality issue that
   inflates the TODO count, not a code quality issue — clarify in your scoring.

7. **Repeat findings** — The four `except Exception: pass` clauses in
   `generate_manifest.py` and the `BaseSolver` re-export at package root have
   been flagged in every audit since v0.0 and remain unfixed. Weight these
   heavily in your priority fix list and final verdict.

Produce the final `docs/AUDIT_REPORT.md` covering all three agents, the
iteration history, combined findings, a priority fix list (P0–P3), and
a clear PASS/FAIL/CONDITIONAL verdict with reasoning.
```
```

### Agent 3 full output

```
The write is blocked pending your approval. Please allow writing to `docs/AUDIT_REPORT.md` and I'll complete the report.

In the meantime, here is the full Agent 3 verdict:

---

**SCORE: 89/100**

```
BREAKDOWN:
Q1: 13/20  — multiple unfixed static issues; 3 items unresolved for 3rd consecutive audit
Q2: 10/10  — all src/ and tests/ files under 300 lines; scripts/ exempt per AUDIT_PROMPTS.md
Q3:  4/5   — no TODO/FIXME in source code; manifest tooling shows v0.0 after 3 versions (tooling issue, not code)
Q4:  7/10  — 26 passing tests; to_array() copy-isolation untested in test_core.py; benchmark() exception gap unexercised
Q5:  5/5   — all print() in CLI entry points only; none in library code
L1: 10/10  — MIT LICENSE present (21 lines)
L2: 30/30  — all deps MIT/BSD/Apache-2.0; no GPL or AGPL
L3: 10/10  — N/A (headers not required)
```

**Three-agent average: (82 + 87 + 89) / 3 = 86.0/100 — clears the 85 threshold numerically.**

**VERDICT: CONDITIONAL**
**REASON:** Numeric scores pass the 85/100 threshold, but four findings flagged in every audit since v0.0 remain unaddressed for the third consecutive version; v0.3 clearance requires resolving the auto-install supply-chain risk, module-level API client, bare `except`/`pass` clauses, and the `UnsolvableError` export gap.

**P0 (blockers — fix before v0.3):**
1. `scripts/audit_pipeline.py:28-32` — remove auto-install block; fail-fast on missing deps
2. `scripts/audit_pipeline.py:254` — move client construction inside `call_agent()`, gated on `USE_API`
3. `pyproject.toml` + `environment.yml` — add version bounds to all production deps; commit a lock file

**P1 (this version — fix before shipping v0.3):**
4. `scripts/generate_manifest.py:107,215,233,304` — replace four bare `except/pass` with `warnings.warn`
5. `src/sudoku/solvers/__init__.py` — export `UnsolvableError` from the public package surface; update import sites in tests and CLI
6. `docs/PROJECT_MANIFEST.md` — update version to v0.2; fill in tech stack
```

---

## Next steps for Claude Code

1. Open `docs/SESSION_HANDOFF.md` and update it with these audit results.
2. Fix all P0 blockers before any deployment or version promotion.
3. After P0 fixes, re-run `python scripts/audit_pipeline.py` to verify.
