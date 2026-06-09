import pytest

from sudoku import BacktrackingSolver, Sudoku
from sudoku.game.presets import EASY, HARD, MEDIUM
from sudoku.solvers.base import UnsolvableError

# Row 0 holds digits 1-8 (missing 9); col 0 has 9 in row 1; top-left box also
# covers {1,2,9} — so cell (0,0) has no candidates, forcing immediate False.
UNSOLVABLE = "012345678" + "900000000" + "0" * 63


@pytest.fixture
def solver() -> BacktrackingSolver:
    return BacktrackingSolver()


def test_solver_name(solver: BacktrackingSolver) -> None:
    assert solver.name == "backtracking"


def test_solves_easy(solver: BacktrackingSolver) -> None:
    solution = solver.solve(Sudoku.from_string(EASY))
    assert solution.is_solved()


def test_solves_medium(solver: BacktrackingSolver) -> None:
    solution = solver.solve(Sudoku.from_string(MEDIUM))
    assert solution.is_solved()


def test_solves_hard(solver: BacktrackingSolver) -> None:
    solution = solver.solve(Sudoku.from_string(HARD))
    assert solution.is_solved()


def test_raises_on_unsolvable(solver: BacktrackingSolver) -> None:
    with pytest.raises(UnsolvableError):
        solver.solve(Sudoku.from_string(UNSOLVABLE))


def test_solution_consistent_with_input(solver: BacktrackingSolver) -> None:
    puzzle = Sudoku.from_string(MEDIUM)
    solution = solver.solve(puzzle)
    board_in = puzzle.to_array()
    board_out = solution.to_array()
    for r in range(9):
        for c in range(9):
            if board_in[r, c] != 0:
                assert board_out[r, c] == board_in[r, c]


def test_does_not_mutate_input(solver: BacktrackingSolver) -> None:
    puzzle = Sudoku.from_string(HARD)
    original = puzzle.to_array().copy()
    solver.solve(puzzle)
    assert (puzzle.to_array() == original).all()
