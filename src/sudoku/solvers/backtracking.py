from __future__ import annotations

import numpy as np

from sudoku.core.sudoku import Sudoku
from sudoku.solvers.base import BaseSolver, UnsolvableError


class BacktrackingSolver(BaseSolver):
    @property
    def name(self) -> str:
        return "backtracking"

    def _get_candidates(self, board: np.ndarray, row: int, col: int) -> set[int]:
        used = (
            set(board[row, :].tolist())
            | set(board[:, col].tolist())
            | set(board[(row // 3) * 3 : (row // 3) * 3 + 3,
                        (col // 3) * 3 : (col // 3) * 3 + 3].flatten().tolist())
        )
        used.discard(0)
        return set(range(1, 10)) - used

    def _solve(self, board: np.ndarray) -> bool:
        best_cell = None
        best_candidates: set[int] = set()

        for r in range(9):
            for c in range(9):
                if board[r, c] == 0:
                    candidates = self._get_candidates(board, r, c)
                    if not candidates:
                        return False
                    if best_cell is None or len(candidates) < len(best_candidates):
                        best_cell = (r, c)
                        best_candidates = candidates

        if best_cell is None:
            return True

        r, c = best_cell
        for value in best_candidates:
            board[r, c] = value
            if self._solve(board):
                return True
            board[r, c] = 0

        return False

    def solve(self, puzzle: Sudoku) -> Sudoku:
        board = puzzle.to_array()
        if not self._solve(board):
            raise UnsolvableError(f"{self.name}: no solution exists")
        return Sudoku(board)
