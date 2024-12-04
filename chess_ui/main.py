import os
import sys

import pandas as pd
from PyQt6.QtWidgets import QApplication
from dotenv import load_dotenv
from stockfish import Stockfish

from chess_ui.chess_home import ChessHomePageUI
from trainer.chess_coach import ChessCoach


def main():
    load_dotenv()

    app = QApplication(sys.argv)
    puzzle_data = pd.read_csv('lichess_puzzles.csv.zst')
    coach = ChessCoach(
        stockfish=Stockfish(r"C:\stockfish\stockfish-windows-x86-64-avx2.exe"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model="gpt-4o-mini",
        chess_model="Waterhorse/chessgpt-chat-v1"
    )
    home_page = ChessHomePageUI(puzzle_data, coach)
    home_page.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
