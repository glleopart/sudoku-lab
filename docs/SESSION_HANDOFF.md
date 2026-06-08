# Session Handoff — sudoku-lab

**Date:** 2026-06-08
**Last completed version:** v0.1 ✓ BUILT (awaiting audit)
**Next target version:** v0.2
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

Audit: pending — run audit agents before closing v0.1

---

## Open blockers

None.

---

## Next session task list

1. Run audit (security-auditor → parity-auditor → quality-auditor)
2. Fix any audit findings
3. Define v0.2 acceptance criterion (suggest: backtracking solver — `python -m sudoku.solve <puzzle>` solves a puzzle in < 1s and prints the solution)
4. Build v0.2

Suggested v0.2 scope (backtracking solver):
- src/sudoku/solvers/backtracking.py — BacktrackingSolver(BaseSolver) using recursive DFS with constraint propagation
- src/sudoku/solvers/__init__.py — export BacktrackingSolver
- src/sudoku/solve/__main__.py — CLI: read puzzle string arg, solve, print solution
- tests/test_backtracking.py — solves easy/medium/hard presets, benchmark passes
- Update notebooks/ with a solver demo notebook
