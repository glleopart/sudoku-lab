# Project Manifest — sudoku-lab
*Last updated: 2025-06-07 — v0.0 (planned)*

---

## Project overview

**Project name:** sudoku-lab
**Description:** Comparative Sudoku solver framework implementing 10+ methodologies across classical, stochastic, Monte Carlo, ML, and DL approaches, with unified benchmarking and Jupyter notebook visualisations.
**Current version:** not yet initialised — awaiting new-project bootstrap
**License:** MIT
**Tech stack:** Python 3.11, numpy, PuLP, scikit-learn, PyTorch, neat-python, rich, jupyter
**Privacy model:** Public open source (portfolio project)
**AI/ML layer:** Yes — v0.6 (ML), v0.7 (DL), v0.8 (NEAT)
**Repository:** git@github-personal:glleopart/sudoku-lab (public)

---

## Tech stack detail

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.11+ |
| Package layout | src/sudoku/ | pyproject.toml |
| Environment | conda | environment.yml |
| Terminal UI | rich | latest |
| Classical/ILP | numpy, PuLP | latest |
| Monte Carlo | numpy, scipy | latest |
| ML | scikit-learn | latest |
| DL | PyTorch | 2.x |
| Neuroevolution | neat-python | latest |
| Notebooks | jupyter, matplotlib, seaborn, plotly | latest |
| Testing | pytest | latest |
| CI | GitHub Actions | — |

---

## Planned folder structure
sudoku-lab/
├── src/sudoku/
│   ├── core/           # Sudoku class, board, validation
│   ├── game/           # Rich TUI interactive game
│   ├── generator/      # Database generator + clue remover
│   ├── solvers/
│   │   ├── base.py     # Abstract BaseSolver
│   │   ├── classical/  # backtracking, random
│   │   ├── stochastic/ # PuLP ILP
│   │   ├── montecarlo/ # classical MC, PIMC, SQA
│   │   ├── ml/         # sklearn classifiers
│   │   └── dl/         # PyTorch, NEAT
│   ├── benchmark/      # Unified benchmarking harness
│   └── viz/            # Plotting utilities
├── notebooks/          # 00–07 Jupyter notebooks
├── data/raw/           # Generated sudoku CSVs
├── data/processed/     # Train/test splits
├── models/             # Saved ML/DL/NEAT checkpoints
├── outputs/            # Benchmark results, plots
├── tests/
├── docs/               # dev-infra coordination files
├── pyproject.toml
├── environment.yml
└── README.md

---

## File registry

*To be populated as files are created starting v0.0*

---

## Roadmap

| Version | Status | Description | Acceptance criterion |
|---------|--------|-------------|---------------------|
| v0.0 | planned | Skeleton + core Sudoku class | `from sudoku import Sudoku; Sudoku().display()` runs |
| v0.1 | planned | Interactive terminal game | Play a complete game in terminal |
| v0.2 | planned | Database generator | 1000 sudokus per difficulty in data/raw/ |
| v0.3 | planned | Classical solvers | Backtracking solves 100% of valid sudokus |
| v0.4 | planned | PuLP stochastic solver | PuLP solves 100%; time comparison shown |
| v0.5 | planned | MC solvers (classical + 2× QMC) | ≥80% easy solved; all convergence curves generated |
| v0.6 | planned | ML solvers | ≥70% cell accuracy on easy test set |
| v0.7 | planned | DL solvers | ≥85% cell accuracy on easy test set |
| v0.8 | planned | NEAT neuroevolution | ≥50% easy solved after 100 generations |
| v0.9 | planned | Unified benchmark notebook | All plots generated end-to-end |
| v1.0 | planned | Beta / public release | Audit ≥85, README complete, CI green |

---

## Security notes

- No secrets — no API keys, no credentials
- All data generated locally
- MIT licensed

---

## Agent communication

- **Last build session:** not yet started
- **Last audit run:** N/A
- **Blockers:** none
