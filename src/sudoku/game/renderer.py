from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    import matplotlib.axes
    from sudoku.core.sudoku import Sudoku


def draw_board(
    ax: matplotlib.axes.Axes,
    puzzle: Sudoku,
    selected: tuple[int, int],
    given_cells: frozenset[tuple[int, int]],
    conflicts: set[tuple[int, int]],
    elapsed_s: float,
    moves: int,
) -> None:
    ax.cla()

    for r in range(9):
        for c in range(9):
            y_bot = 8 - r
            if (r, c) in conflicts:
                color = "lightsalmon"
            elif (r, c) == selected:
                color = "gold"
            elif (r, c) in given_cells:
                color = "lightgray"
            else:
                color = "white"
            ax.add_patch(mpatches.Rectangle((c, y_bot), 1, 1, color=color, zorder=0))

            value = puzzle.get_cell(r, c)
            if value != 0:
                ax.text(
                    c + 0.5,
                    y_bot + 0.5,
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=16,
                    color="black" if (r, c) in given_cells else "royalblue",
                    fontweight="bold" if (r, c) in given_cells else "normal",
                    zorder=1,
                )

    for pos in range(10):
        lw = 2.5 if pos in (0, 3, 6, 9) else 0.5
        ax.plot([pos, pos], [0, 9], color="black", linewidth=lw, zorder=2)
        ax.plot([0, 9], [pos, pos], color="black", linewidth=lw, zorder=2)

    ax.set_xlim(0, 9)
    ax.set_ylim(0, 9)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Sudoku Lab  |  {elapsed_s:.0f}s  |  {moves} moves", fontsize=12)
