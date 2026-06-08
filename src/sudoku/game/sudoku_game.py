from __future__ import annotations

import time

import matplotlib.pyplot as plt

from sudoku.game.presets import PRESET_MAP
from sudoku.game.renderer import draw_board
from sudoku.game.state import GameState


class SudokuGame:
    def __init__(self, puzzle_str: str) -> None:
        self.state = GameState.from_string(puzzle_str)
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        plt.tight_layout()
        self._render()

    @classmethod
    def from_preset(cls, difficulty: str = "easy") -> SudokuGame:
        return cls(PRESET_MAP[difficulty.lower()])

    def show(self) -> None:
        plt.show()

    def _on_key(self, event) -> None:
        key = event.key
        if key == "up":
            self.state.move_cursor(-1, 0)
        elif key == "down":
            self.state.move_cursor(1, 0)
        elif key == "left":
            self.state.move_cursor(0, -1)
        elif key == "right":
            self.state.move_cursor(0, 1)
        elif key in "123456789":
            self.state.fill_cell(int(key))
            self.state.check_win()
        elif key in ("0", "delete", "backspace"):
            self.state.clear_cell()
        elif key == "q":
            plt.close(self.fig)
            return
        self._render()

    def _on_click(self, event) -> None:
        if event.inaxes is not self.ax or event.xdata is None or event.ydata is None:
            return
        col = max(0, min(8, int(event.xdata)))
        row = max(0, min(8, 8 - int(event.ydata)))
        self.state.selected = (row, col)
        self._render()

    def _render(self) -> None:
        elapsed = self.state.completion_time if self.state.solved else time.time() - self.state.start_time
        draw_board(
            self.ax,
            self.state.puzzle,
            self.state.selected,
            self.state.given,
            self.state.get_conflicts(),
            elapsed,
            self.state.moves,
        )
        if self.state.solved:
            self.ax.text(
                4.5,
                4.5,
                f"Solved!\n{self.state.moves} moves in {elapsed:.0f}s",
                ha="center",
                va="center",
                fontsize=20,
                color="darkgreen",
                fontweight="bold",
                bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.9),
                zorder=10,
            )
        self.fig.canvas.draw_idle()
