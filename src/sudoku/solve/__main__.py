import sys
import time

from sudoku import BacktrackingSolver, Sudoku
from sudoku.game.presets import PRESET_MAP
from sudoku.solvers.base import UnsolvableError


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "easy"
    puzzle_str = PRESET_MAP.get(arg.lower(), arg)
    if len(puzzle_str) != 81:
        print(f"Error: expected 81-char string or easy/medium/hard, got {len(puzzle_str)} chars")
        sys.exit(1)
    puzzle = Sudoku.from_string(puzzle_str)
    print("Puzzle:")
    puzzle.display()
    solver = BacktrackingSolver()
    t0 = time.perf_counter()
    try:
        solution = solver.solve(puzzle)
        elapsed = time.perf_counter() - t0
        print(f"\nSolution ({elapsed * 1000:.1f} ms):")
        solution.display()
    except UnsolvableError as e:
        print(f"Unsolvable: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
