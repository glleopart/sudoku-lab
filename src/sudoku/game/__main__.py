from sudoku.game.sudoku_game import SudokuGame


def main() -> None:
    print("Sudoku Lab")
    print("[e]asy  [m]edium  [h]ard")
    choice = input("> ").strip().lower()
    difficulty = {"e": "easy", "m": "medium", "h": "hard"}.get(choice, "easy")
    SudokuGame.from_preset(difficulty).show()


if __name__ == "__main__":
    main()
