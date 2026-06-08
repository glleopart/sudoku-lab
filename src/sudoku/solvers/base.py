from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sudoku.core.sudoku import Sudoku


class BaseSolver(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def solve(self, puzzle: "Sudoku") -> "Sudoku":
        ...

    def benchmark(self, puzzles: list["Sudoku"], n_runs: int = 1) -> dict:
        times: list[float] = []
        solved = 0
        for puzzle in puzzles:
            for _ in range(n_runs):
                t0 = time.perf_counter()
                try:
                    result = self.solve(puzzle.copy())
                    elapsed = time.perf_counter() - t0
                    if result.is_solved():
                        solved += 1
                except ValueError:
                    elapsed = time.perf_counter() - t0
                times.append(elapsed)

        total = len(puzzles) * n_runs
        return {
            "solver": self.name,
            "n_puzzles": len(puzzles),
            "n_runs": n_runs,
            "solved": solved,
            "total": total,
            "solve_rate": solved / total if total else 0.0,
            "mean_time_s": sum(times) / len(times) if times else 0.0,
            "min_time_s": min(times) if times else 0.0,
            "max_time_s": max(times) if times else 0.0,
        }
