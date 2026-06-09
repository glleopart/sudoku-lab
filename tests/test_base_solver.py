"""Tests for BaseSolver via a minimal concrete stub."""
import pytest
from sudoku import Sudoku
from sudoku.solvers import BaseSolver
from sudoku.solvers.base import UnsolvableError

SOLVED_STR = (
    "534678912672195348198342567"
    "859761423426853791713924856"
    "961537284287419635345286179"
)
PARTIAL_STR = (
    "530070000600195000098000060"
    "800060003400803001700020006"
    "060000280000419005000080079"
)


class IdentitySolver(BaseSolver):
    """Returns the puzzle unchanged — only works on already-solved boards."""
    @property
    def name(self) -> str:
        return "identity"

    def solve(self, puzzle: Sudoku) -> Sudoku:
        if not puzzle.is_solved():
            raise ValueError("IdentitySolver only accepts solved puzzles")
        return puzzle


class AlwaysFailSolver(BaseSolver):
    """Always raises UnsolvableError — simulates an unsolvable puzzle."""
    @property
    def name(self) -> str:
        return "always_fail"

    def solve(self, puzzle: Sudoku) -> Sudoku:
        raise UnsolvableError("No solution")


def test_benchmark_returns_expected_keys():
    solver = IdentitySolver()
    result = solver.benchmark([Sudoku.from_string(SOLVED_STR)])
    assert set(result.keys()) == {
        "solver", "n_puzzles", "n_runs", "solved",
        "total", "solve_rate", "mean_time_s", "min_time_s", "max_time_s"
    }


def test_benchmark_solve_rate_perfect():
    solver = IdentitySolver()
    result = solver.benchmark([Sudoku.from_string(SOLVED_STR)], n_runs=3)
    assert result["solve_rate"] == 1.0
    assert result["solved"] == 3


def test_benchmark_handles_unsolvable():
    solver = AlwaysFailSolver()
    result = solver.benchmark([Sudoku.from_string(PARTIAL_STR)])
    assert result["solve_rate"] == 0.0
    assert result["solved"] == 0


def test_benchmark_solver_name():
    solver = IdentitySolver()
    result = solver.benchmark([Sudoku.from_string(SOLVED_STR)])
    assert result["solver"] == "identity"
