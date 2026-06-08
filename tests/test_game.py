import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from sudoku.game.presets import EASY
from sudoku.game.renderer import draw_board
from sudoku.game.state import GameState

# Nearly-solved board: Wikipedia solution with (0,2) blanked — fill 4 to win
_NEARLY_SOLVED = (
    "530678912672195348198342567859761423426853791713924856961537284287419635345286179"
)


def test_state_from_string():
    state = GameState.from_string(EASY)
    assert len(state.given) > 0
    for r, c in state.given:
        assert state.puzzle.get_cell(r, c) != 0
    assert state.selected == (0, 0)
    assert state.moves == 0
    assert state.solved is False


def test_move_cursor_clamps():
    state = GameState.from_string(EASY)
    state.selected = (0, 0)
    state.move_cursor(-1, 0)
    assert state.selected == (0, 0)

    state.selected = (8, 8)
    state.move_cursor(1, 1)
    assert state.selected == (8, 8)

    state.selected = (4, 4)
    state.move_cursor(1, 0)
    assert state.selected == (5, 4)


def test_fill_given_rejected():
    state = GameState.from_string(EASY)
    given_cell = next(iter(state.given))
    original_value = state.puzzle.get_cell(*given_cell)
    state.selected = given_cell
    state.fill_cell(9 if original_value != 9 else 8)
    assert state.puzzle.get_cell(*given_cell) == original_value
    assert state.moves == 0


def test_fill_and_conflict():
    state = GameState.from_string(EASY)
    # Find a non-given cell and a value already in its row
    for r in range(9):
        for c in range(9):
            if (r, c) in state.given:
                continue
            # Find a value already present in this row
            for c2 in range(9):
                if (r, c2) in state.given:
                    dup_val = state.puzzle.get_cell(r, c2)
                    state.selected = (r, c)
                    state.fill_cell(dup_val)
                    conflicts = state.get_conflicts()
                    assert len(conflicts) > 0
                    assert (r, c) in conflicts
                    return
    pytest.skip("no suitable non-given cell found")


def test_win_detection():
    state = GameState.from_string(_NEARLY_SOLVED)
    # Blank cell is at (0, 2); correct fill value is 4
    state.selected = (0, 2)
    state.fill_cell(4)
    assert state.check_win() is True
    assert state.solved is True


def test_completion_time_set_on_win():
    state = GameState.from_string(_NEARLY_SOLVED)
    assert state.completion_time is None
    state.selected = (0, 2)
    state.fill_cell(4)
    state.check_win()
    assert state.completion_time is not None
    assert state.completion_time >= 0.0


def test_clear_cell():
    state = GameState.from_string(EASY)
    # Find a non-given cell
    for r in range(9):
        for c in range(9):
            if (r, c) not in state.given:
                state.selected = (r, c)
                state.fill_cell(5)
                assert state.puzzle.get_cell(r, c) == 5
                state.clear_cell()
                assert state.puzzle.get_cell(r, c) == 0
                break
        else:
            continue
        break

    # Given cell should not be cleared
    given_cell = next(iter(state.given))
    original_value = state.puzzle.get_cell(*given_cell)
    state.selected = given_cell
    state.clear_cell()
    assert state.puzzle.get_cell(*given_cell) == original_value


def test_renderer_runs():
    fig, ax = plt.subplots()
    state = GameState.from_string(EASY)
    draw_board(ax, state.puzzle, state.selected, state.given, set(), 10.0, 5)
    plt.close(fig)
