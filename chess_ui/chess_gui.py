import threading
import time

import chess
from PyQt6.QtCore import Qt, QEventLoop, QObject, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QLabel, QVBoxLayout, QListWidget, QPushButton

from chess_ui.chat_box import ChatBox
from chess_ui.chess_board import ChessBoard
from trainer.chess_coach import ChessCoach


class InputHandler(QObject):
    input_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.user_input = None


class ChessGUI(QMainWindow):

    def __init__(self, options: dict):
        super().__init__()
        self.username = options["username"]
        self.elo = options["elo"]
        self.coach: ChessCoach = options["coach"]
        self.setWindowTitle(f"Chess GUI - {self.username}")
        self.mode = options["mode"]
        self.config = options["config"]
        self.puzzle_moves = []
        self.puzzle_turn = chess.WHITE

        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_splitter = self._create_left_splitter()
        right_widget = self._create_right_widget()

        splitter.addWidget(left_splitter)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 300])
        left_splitter.setSizes([50, 500, 200])

        main_layout.addWidget(splitter)

    def _create_left_splitter(self):
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        player_info_widget = self._create_player_info_widget()
        self.chess_board = ChessBoard(self)
        move_list_widget = self._create_move_list_widget()

        left_splitter.addWidget(player_info_widget)
        left_splitter.addWidget(self.chess_board)
        left_splitter.addWidget(move_list_widget)

        return left_splitter

    def _create_player_info_widget(self):
        player_info_widget = QWidget()
        player_info_layout = QHBoxLayout()
        player_info_widget.setLayout(player_info_layout)

        self.player_name_label = QLabel(f"Player: {self.username}")
        self.player_elo_label = QLabel(f"Elo: {self.elo}")
        self.turn_indicator = QLabel("White's Turn")

        player_info_layout.addWidget(self.player_name_label)
        player_info_layout.addWidget(self.player_elo_label)
        player_info_layout.addWidget(self.turn_indicator)

        return player_info_widget

    def _create_move_list_widget(self):
        move_list_widget = QWidget()
        move_list_layout = QVBoxLayout()
        move_list_widget.setLayout(move_list_layout)

        move_list_label = QLabel("Move List:")
        self.move_list = QListWidget()
        self.move_list.setMaximumHeight(200)

        move_list_layout.addWidget(move_list_label)
        move_list_layout.addWidget(self.move_list)

        return move_list_widget

    def _create_right_widget(self):
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        chat_label = QLabel("Chess Chat:")
        self.chat_box = ChatBox(self)
        right_layout.addWidget(chat_label)
        right_layout.addWidget(self.chat_box)

        button_layout = self._create_button_layout()
        right_layout.addLayout(button_layout)

        return right_widget

    def _create_button_layout(self):
        button_layout = QHBoxLayout()

        undo_button = QPushButton("Undo Move")
        undo_button.clicked.connect(self.undo_move)
        button_layout.addWidget(undo_button)

        reset_button = QPushButton("Reset Game")
        reset_button.clicked.connect(self.reset_game)
        button_layout.addWidget(reset_button)

        return button_layout

    def start_game(self):
        if self.mode == "analysis":
            target = self.start_analysis
        elif self.mode == "bot":
            target = self.start_bot
        elif self.mode == "puzzle":
            target = self.start_puzzle
        else:
            target = None

        if target:
            threading.Thread(target=target).start()

    def start_bot(self):
        stockfish = self.coach.stockfish
        stockfish.update_engine_parameters({
            "Threads": self.config["threads"],
            "Move Overhead": self.config["move_time"],
            "Skill Level": self.config["skill_level"],
            "UCI_Elo": self.config["bot_elo"]
        })

    def start_puzzle(self):
        puzzle = self.config["puzzle"]
        fen = str(puzzle["FEN"])
        self.puzzle_moves = list(puzzle["Moves"].split())  # solution
        self.chess_board.board.set_fen(fen)
        self.puzzle_turn = self.chess_board.board.turn
        self.turn_indicator.setText("White's Turn" if self.puzzle_turn == chess.WHITE else "Black's Turn")
        self.chess_board.update_board()

    def evaluate_move(self, move):
        board = self.chess_board.board
        board.push(move)

        engine = self.coach.stockfish
        engine.set_fen_position(board.fen())
        best_move_eval = engine.get_evaluation()
        board.pop()

        return best_move_eval["type"], best_move_eval["value"]

    def wait_for_move(self):
        loop = QEventLoop()
        self.chat_box.input_handler.input_received.connect(loop.quit)
        loop.exec()
        return self.chat_box.input_handler.user_input

    def analyze_move(self, move):
        try:
            eval_best = self.evaluate_move(chess.Move.from_uci(self.coach.stockfish.get_best_move()))
            eval_player = self.evaluate_move(chess.Move.from_uci(move))
        except ValueError:
            return False

        if self.chess_board.board.turn == self.config["color"] and (
                eval_best[0] != eval_player[0] or abs(eval_best[1] - eval_player[1]) > self.config["threshold"]):
            self.chat_box.chat_display.append(
                f"<b>MAGNUS:</b> Blunder detected on move {move}. Can you guess the best move?")
            self.chess_board.blunder = move
            self.chess_board.update_board()

            self.coach.stockfish.set_fen_position(self.chess_board.board.fen())
            best_move = self.coach.stockfish.get_best_move()
            user_move = self.wait_for_move()
            if user_move == best_move:
                return self.chess_board.try_move(chess.Move.from_uci(move))
            else:
                self.chat_box.chat_display.append(f"<b>MAGNUS:</b> That's not it. Let's try again.")
                return False
        else:
            return self.chess_board.try_move(chess.Move.from_uci(move))

    def start_analysis(self):
        moves = [*self.config["moves"]]
        while moves:
            move = moves.pop(0)
            if not self.analyze_move(move):
                moves.insert(0, move)
            else:
                self.chess_board.blunder = None
                self.chess_board.update_board()
            time.sleep(0.6)

    def update_move_list(self, move):
        # Add move to list
        self.move_list.addItem(str(move))  # todo: use SAN notation
        turn_text = "White's Turn" if self.chess_board.board.turn == chess.WHITE else "Black's Turn"
        self.turn_indicator.setText(turn_text)

    def undo_move(self):
        if self.mode == "analysis":
            return

        if len(self.chess_board.board.move_stack) <= 0:
            return

        self.chess_board.board.pop()
        self.chess_board.update_board()

        if self.move_list.count() > 0:
            self.move_list.takeItem(self.move_list.count() - 1)

        turn_text = "White's Turn" if self.chess_board.board.turn == chess.WHITE else "Black's Turn"
        self.turn_indicator.setText(turn_text)

    def reset_game(self):
        self.chess_board.board.reset()
        self.chess_board.update_board()
        self.move_list.clear()
        self.turn_indicator.setText("White's Turn")
