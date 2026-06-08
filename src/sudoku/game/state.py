from __future__ import annotations

import time
from dataclasses import dataclass, field

from sudoku.core.sudoku import Sudoku


@dataclass
class GameState:
    puzzle: Sudoku
    given: frozenset[tuple[int, int]]
    selected: tuple[int, int]
    moves: int
    start_time: float
    solved: bool

    @classmethod
    def from_string(cls, s: str) -> GameState:
        puzzle = Sudoku.from_string(s)
        given = frozenset(
            (r, c)
            for r in range(9)
            for c in range(9)
            if puzzle.get_cell(r, c) != 0
        )
        return cls(
            puzzle=puzzle,
            given=given,
            selected=(0, 0),
            moves=0,
            start_time=time.time(),
            solved=False,
        )

    def move_cursor(self, dr: int, dc: int) -> None:
        r, c = self.selected
        self.selected = (max(0, min(8, r + dr)), max(0, min(8, c + dc)))

    def fill_cell(self, value: int) -> None:
        if self.solved:
            return
        r, c = self.selected
        if (r, c) in self.given:
            return
        self.puzzle.set_cell(r, c, value)
        self.moves += 1

    def clear_cell(self) -> None:
        if self.solved:
            return
        r, c = self.selected
        if (r, c) in self.given:
            return
        self.puzzle.set_cell(r, c, 0)

    def get_conflicts(self) -> set[tuple[int, int]]:
        conflicts: set[tuple[int, int]] = set()
        for r in range(9):
            for c in range(9):
                v = self.puzzle.get_cell(r, c)
                if v == 0:
                    continue
                if any(self.puzzle.get_cell(r, c2) == v for c2 in range(9) if c2 != c):
                    conflicts.add((r, c))
                    continue
                if any(self.puzzle.get_cell(r2, c) == v for r2 in range(9) if r2 != r):
                    conflicts.add((r, c))
                    continue
                br, bc = (r // 3) * 3, (c // 3) * 3
                if any(
                    self.puzzle.get_cell(br + i, bc + j) == v
                    for i in range(3)
                    for j in range(3)
                    if (br + i, bc + j) != (r, c)
                ):
                    conflicts.add((r, c))
        return conflicts

    def check_win(self) -> bool:
        if self.puzzle.is_solved():
            self.solved = True
            return True
        return False
