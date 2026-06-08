import numpy as np
import pytest

from sudoku import Sudoku

SOLVED_STR = (
    "534678912"
    "672195348"
    "198342567"
    "859761423"
    "426853791"
    "713924856"
    "961537284"
    "287419635"
    "345286179"
)

PARTIAL_STR = (
    "530070000"
    "600195000"
    "098000060"
    "800060003"
    "400803001"
    "700020006"
    "060000280"
    "000419005"
    "000080079"
)

INVALID_STR = (
    "554678912"  # two 5s in first row
    "672195348"
    "198342567"
    "859761423"
    "426853791"
    "713924856"
    "961537284"
    "287419635"
    "345286179"
)


def test_init_empty():
    s = Sudoku()
    assert s._board.shape == (9, 9)
    assert s._board.sum() == 0


def test_init_with_board():
    board = np.ones((9, 9), dtype=int)
    s = Sudoku(board)
    assert s._board.sum() == 81


def test_from_string_and_to_string():
    s = Sudoku.from_string(SOLVED_STR)
    assert s.to_string() == SOLVED_STR


def test_validate_solved():
    s = Sudoku.from_string(SOLVED_STR)
    assert s.validate() is True


def test_validate_invalid():
    s = Sudoku.from_string(INVALID_STR)
    assert s.validate() is False


def test_is_solved():
    s = Sudoku.from_string(SOLVED_STR)
    assert s.is_solved() is True
    p = Sudoku.from_string(PARTIAL_STR)
    assert p.is_solved() is False


def test_get_set_cell_and_copy():
    s = Sudoku()
    s.set_cell(0, 0, 5)
    assert s.get_cell(0, 0) == 5
    c = s.copy()
    c.set_cell(0, 0, 9)
    assert s.get_cell(0, 0) == 5  # original unchanged
