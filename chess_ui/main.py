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
    open_api_key = os.getenv("OPENAI_API_KEY")
    if open_api_key is None:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    puzzle_path = os.getenv("LICHESS_PUZZLE_DATASET_PATH")
    if puzzle_path is None or not os.path.exists(puzzle_path):
        raise ValueError("LICHESS_PUZZLE_DATASET_PATH environment variable is not set")

    stockfish_path = os.getenv("STOCKFISH_PATH")
    if stockfish_path is None or not os.path.exists(stockfish_path):
        raise ValueError("STOCKFISH_PATH environment variable is not set")

    openai_model = os.getenv("OPENAI_MODEL")
    if openai_model is None:
        raise ValueError("OPENAI_MODEL environment variable is not set")

    puzzle_data = pd.read_csv(puzzle_path)
    coach = ChessCoach(
        stockfish=Stockfish(stockfish_path),
        openai_api_key=open_api_key,
        openai_model=openai_model,
        chess_model="Waterhorse/chessgpt-chat-v1"
    )
    home_page = ChessHomePageUI(puzzle_data, coach)
    home_page.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
