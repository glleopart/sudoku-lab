# Session Handoff — sudoku-lab

**Date:** 2025-06-07
**Last completed version:** none — project not yet initialised
**Next target version:** v0.0
**Version acceptance criterion:**
> `from sudoku import Sudoku; Sudoku().display()` runs without error from the repo root.

---

## What was done last session

Nothing yet — this is the first session.

---

## Open blockers

None.

---

## Next session task list

1. Run `new-project sudoku-lab` in terminal
2. Build v0.0:
   - [ ] `pyproject.toml` — deps: numpy, rich, PuLP, scikit-learn, torch, neat-python, jupyter, pytest
   - [ ] `environment.yml` — conda env based on datascience, add project deps
   - [ ] `src/sudoku/__init__.py`
   - [ ] `src/sudoku/core/sudoku.py` — Sudoku class: 9×9 numpy board, validate(), display(), load(), save()
   - [ ] `src/sudoku/core/__init__.py`
   - [ ] `src/sudoku/solvers/base.py` — abstract BaseSolver with solve(), benchmark()
   - [ ] `tests/test_core.py` — test board init, validation, display
   - [ ] `README.md` — project title + placeholder

---

## Architecture decisions

- Package layout: `src/sudoku/` imported by notebooks (not standalone scripts in notebooks)
- Board representation: 9×9 numpy int array, 0 = empty cell
- Solver interface: all solvers inherit BaseSolver, implement solve(board) → board
- Data format: CSV with 81-char string (row-major, 0 = empty) + difficulty label
- QMC: two approaches — PIMC (Suzuki-Trotter) and SQA (transverse-field Potts)
- DL training: shared trainer with AMP + gradient clipping + early stopping
