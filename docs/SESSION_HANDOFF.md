# Session Handoff — sudoku-lab

**Date:** 2026-06-08
**Last completed version:** v0.0
**Next target version:** v0.1
**Version acceptance criterion:**
> TBD — add a backtracking solver that passes `pytest tests/ -v`

---

## What was done last session

**v0.0 — scaffold + Sudoku core class**

- Created `pyproject.toml` (hatchling, all dependencies)
- Created `environment.yml` (conda-forge channels, pip extras)
- Created package skeleton: `src/sudoku/{core,solvers,game,generator,montecarlo,ml,dl,benchmark,viz}/`
- Implemented `src/sudoku/core/sudoku.py` — `Sudoku` class (9×9 numpy board, rich display, validate, is_solved, get/set_cell, copy, to_string, from_string, __repr__)
- Implemented `src/sudoku/solvers/base.py` — abstract `BaseSolver` with `benchmark()` helper
- Wired up `__init__.py` exports at core, solvers, and top-level package
- Added `tests/test_core.py` — 7 tests, all pass
- Added `README.md` with API table and install instructions

All acceptance criteria met:
```
python -c "from sudoku import Sudoku; s = Sudoku(); s.display()"  # ✓
pytest tests/ -v  # 7 passed
```

---

## Open blockers

None.

---

## Next session task list

Implement a backtracking solver as the first concrete `BaseSolver`:

1. `src/sudoku/solvers/backtracking.py` — `BacktrackingSolver(BaseSolver)`
   - Classic depth-first backtrack with MRV (minimum remaining values) heuristic
   - `name` property returns `"backtracking"`
   - `solve(puzzle) -> Sudoku` raises `ValueError` if unsolvable

2. Update `src/sudoku/solvers/__init__.py` to export `BacktrackingSolver`

3. Update `src/sudoku/__init__.py` to export `BacktrackingSolver`

4. `tests/test_backtracking.py` — tests:
   - Solves a known easy puzzle correctly
   - Solves a known hard puzzle correctly
   - Returns a board that passes `is_solved()`
   - Raises on an unsolvable puzzle
   - `benchmark()` returns correct keys and a solve_rate of 1.0

Acceptance criterion:
```
pytest tests/ -v  # all tests pass including new backtracking tests
```

---

## Architecture decisions

- Package layout: `src/sudoku/` imported by notebooks (not standalone scripts in notebooks)
- Board representation: 9×9 numpy int array, 0 = empty cell
- Solver interface: all solvers inherit BaseSolver, implement solve(board) → board
- Data format: CSV with 81-char string (row-major, 0 = empty) + difficulty label
- QMC: two approaches — PIMC (Suzuki-Trotter) and SQA (transverse-field Potts)
- DL training: shared trainer with AMP + gradient clipping + early stopping
