# Session Handoff — sudoku-lab

**Date:** 2026-06-09
**Last completed version:** v0.2 ✓ BUILT (awaiting audit)
**Next target version:** v0.3
**Version acceptance criterion:** TBD — define before next session

---

## What was done in v0.0

- pyproject.toml + environment.yml (all deps, hatchling build)
- src/sudoku/ package skeleton (9 modules)
- src/sudoku/core/sudoku.py — Sudoku class (board, validate, display, serialise)
- src/sudoku/solvers/base.py — abstract BaseSolver with benchmark()
- tests/test_core.py (7 tests) + tests/test_base_solver.py (4 tests)
- LICENSE (MIT), README.md
- docs/AUDIT_PROMPTS.md configured for tooling scripts

Audit: 87.0/100 avg (A1:81, A2:87, A3:93) — PASS

---

## What was done in v0.1

- Added ipympl to pyproject.toml and environment.yml
- src/sudoku/game/presets.py — EASY (35 givens), MEDIUM (30 givens, Wikipedia), HARD (20 givens, Inkala) + PRESET_MAP
- src/sudoku/game/state.py — GameState dataclass with from_string, move_cursor, fill_cell, clear_cell, get_conflicts, check_win
- src/sudoku/game/renderer.py — pure draw_board() function (matplotlib, Agg-safe)
- src/sudoku/game/sudoku_game.py — SudokuGame controller (key/click events, win overlay)
- src/sudoku/game/__main__.py — CLI entry point
- src/sudoku/game/__init__.py — public API export
- notebooks/00_game.ipynb — interactive Jupyter notebook (ipympl widget)
- tests/test_game.py — 7 headless tests (18 total, all pass)

Key implementation decisions:
- Coordinate system: y-axis upward, row 0 at top → cell (r,c) at y_bot = 8-r
- Conflict priority: conflict > selected > given > default (lightsalmon > gold > lightgray > white)
- given cells are immutable; fill/clear are no-ops on them
- check_win() sets state.solved = True as a side-effect

Audit: 87.3/100 avg — PASS (committed c74aa29)

---

## What was done in v0.2

- src/sudoku/solvers/base.py — added UnsolvableError(ValueError), changed benchmark() to catch UnsolvableError, added __all__
- src/sudoku/core/sudoku.py — added to_array() → np.ndarray
- src/sudoku/solvers/backtracking.py — BacktrackingSolver with MRV heuristic
- src/sudoku/solvers/__init__.py — exports BacktrackingSolver
- src/sudoku/__init__.py — exports BacktrackingSolver
- src/sudoku/solve/__init__.py — empty package
- src/sudoku/solve/__main__.py — CLI: python -m sudoku.solve [easy|medium|hard|<81-char>]
- tests/test_backtracking.py — 7 new tests (26 total, all pass)
- tests/test_base_solver.py — updated AlwaysFailSolver to raise UnsolvableError
- notebooks/01_backtracking.ipynb — solve all presets + benchmark DataFrame

Key implementation decisions:
- MRV (minimum remaining values / fail-first) heuristic selects most-constrained empty cell at each step
- UNSOLVABLE test fixture uses a board where cell (0,0) immediately has 0 candidates (not the naive "119..." board which would recurse deeply)
- benchmark() narrowed from ValueError to UnsolvableError to avoid silently swallowing other exceptions

Performance: EASY ~8ms, MEDIUM ~8ms, HARD ~12ms (all well under 5s acceptance criterion)

Audit: pending — run audit agents before closing v0.2

---

## Open blockers

None.

---

## Next session task list

TBD — decide v0.3 scope after v0.2 audit passes. Candidate ideas:
- Constraint propagation solver (AC-3 / naked singles / hidden singles) for comparison
- Puzzle generator (remove cells from solved board while maintaining unique solution)
- Difficulty scorer based on techniques required

Acceptance criterion for v0.3: TBD
