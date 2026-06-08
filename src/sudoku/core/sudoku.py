from __future__ import annotations

import numpy as np
from rich.console import Console
from rich.table import Table


class Sudoku:
    def __init__(self, board: np.ndarray | None = None) -> None:
        if board is None:
            self._board = np.zeros((9, 9), dtype=int)
        else:
            arr = np.asarray(board, dtype=int)
            if arr.shape != (9, 9):
                raise ValueError(f"Board must be 9×9, got {arr.shape}")
            if not np.all((arr >= 0) & (arr <= 9)):
                raise ValueError("All cell values must be 0–9")
            self._board = arr.copy()

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def display(self, console: Console | None = None) -> None:
        console = console or Console()
        table = Table(show_header=False, box=None, padding=(0, 1))
        for _ in range(9):
            table.add_column(justify="center", no_wrap=True)

        for r in range(9):
            row_vals = []
            for c in range(9):
                val = self._board[r, c]
                cell = str(val) if val != 0 else "·"
                # vertical box separators
                if c in (3, 6):
                    row_vals.append(f"[dim]|[/dim] {cell}")
                else:
                    row_vals.append(cell)
            table.add_row(*row_vals)
            # horizontal box separators
            if r in (2, 5):
                table.add_row(*["[dim]─[/dim]"] * 9)

        console.print(table)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> bool:
        """Return True if no row/column/box contains duplicate non-zero values."""
        for i in range(9):
            if not self._unique_nonzero(self._board[i, :]):
                return False
            if not self._unique_nonzero(self._board[:, i]):
                return False
        for br in range(3):
            for bc in range(3):
                box = self._board[br * 3 : br * 3 + 3, bc * 3 : bc * 3 + 3]
                if not self._unique_nonzero(box.flatten()):
                    return False
        return True

    @staticmethod
    def _unique_nonzero(values: np.ndarray) -> bool:
        nz = values[values != 0]
        return len(nz) == len(set(nz.tolist()))

    def is_solved(self) -> bool:
        """Return True if board is completely and correctly filled."""
        if np.any(self._board == 0):
            return False
        return self.validate()

    # ------------------------------------------------------------------
    # Cell access
    # ------------------------------------------------------------------

    def get_cell(self, row: int, col: int) -> int:
        return int(self._board[row, col])

    def set_cell(self, row: int, col: int, value: int) -> None:
        if not (0 <= value <= 9):
            raise ValueError(f"Value must be 0–9, got {value}")
        self._board[row, col] = value

    # ------------------------------------------------------------------
    # Copy / serialisation
    # ------------------------------------------------------------------

    def copy(self) -> "Sudoku":
        return Sudoku(self._board)

    def to_string(self) -> str:
        return "".join(str(v) for v in self._board.flatten())

    @classmethod
    def from_string(cls, s: str) -> "Sudoku":
        s = s.strip()
        if len(s) != 81:
            raise ValueError(f"String must be 81 characters, got {len(s)}")
        board = np.array([int(ch) for ch in s], dtype=int).reshape(9, 9)
        return cls(board)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        filled = int(np.sum(self._board != 0))
        return f"Sudoku(filled={filled}/81)"
