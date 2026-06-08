# sudoku-lab

A research playground for solving Sudoku with classical, constraint-based, Monte Carlo, machine-learning, and deep-learning methods.

## Package layout

```
src/sudoku/
├── core/        Sudoku board class
├── solvers/     BaseSolver interface + implementations
├── game/        Interactive game loop
├── generator/   Puzzle generation
├── montecarlo/  PIMC (Suzuki-Trotter) and SQA (transverse-field Potts)
├── ml/          Classical ML solvers
├── dl/          Deep-learning solvers (AMP trainer)
├── benchmark/   Benchmarking harness
└── viz/         Visualisation helpers
```

## Sudoku class — public API

| Method | Description |
|---|---|
| `__init__(board=None)` | Create empty board or wrap existing 9×9 numpy array |
| `display()` | Pretty-print to terminal via Rich |
| `validate()` | Check no row/col/box has duplicate non-zero values |
| `is_solved()` | True if board is full and valid |
| `get_cell(row, col)` | Return value at position |
| `set_cell(row, col, value)` | Set value at position (0–9) |
| `copy()` | Return independent copy |
| `to_string()` | Serialise to 81-char string (row-major, 0=empty) |
| `from_string(s)` | Classmethod — parse 81-char string |
| `__repr__` | `Sudoku(filled=N/81)` |

## Install

```bash
# Create and activate environment
conda env create -f environment.yml
conda activate sudoku-lab

# Or install directly into an existing env
pip install -e .
```

## Quick start

```python
from sudoku import Sudoku

s = Sudoku.from_string(
    "530070000600195000098000060"
    "800060003400803001700020006"
    "060000280000419005000080079"
)
s.display()
```

## Tests

```bash
pytest tests/ -v
```
