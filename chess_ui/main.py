import pandas as pd
import sys
from PyQt6.QtWidgets import QApplication
from add_threading import ChessApp

if __name__ == "__main__":
    app = QApplication(sys.argv)

    if len(sys.argv) != 2: #change this later to take in diff lengths, and diff bots
        print("Missing an argument!")
        exit()
    elif sys.argv[1] == "bot":
        window = ChessApp(mode="bot")
    elif sys.argv[1] == "analysis":
        window = ChessApp(mode = "analysis")
    else:
        puzzles_df = pd.read_csv("C:\\Users\\wei0c\\Desktop\\school\\7-1\\CS-6320-NLP\\lichess_db_puzzle.csv")
        window = ChessApp(puzzles_df, mode="puzzle")

    window.show()
    sys.exit(app.exec())
