import threading

import chess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QLineEdit, QPushButton

from chess_ui.chess_gui import ChessGUI, InputHandler


class ChatBox(QWidget):
    def __init__(self, parent: ChessGUI):
        super().__init__(parent)

        self.coach = parent.coach
        self.parent = parent
        self.input_handler = InputHandler()

        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Message input
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        threading.Thread(target=self.greet).start()

    def greet(self):
        greeting = self.parent.coach.generate_greeting(self.parent.username, self.parent.elo)
        self.chat_display.append(f"<b>MAGNUS:</b> {greeting}")

    def send_message(self):
        message = self.message_input.text().strip()
        if not message:
            return

        board = self.parent.chess_board.board
        self.chat_display.append(f"<b>You:</b> {message}")
        self.message_input.clear()

        # try to make a move
        try:
            move = chess.Move.from_uci(message)
            if self.parent.mode == "analysis":
                self.input_handler.input_received.emit(message)
                self.input_handler.user_input = move.uci()
            else:
                if not self.parent.chess_board.try_move(move):
                    self.chat_display.append(f"<b>MAGNUS:</b> Invalid move.")
                else:
                    self.chat_display.append(f"<b>MAGNUS:</b> Move made: {move}")
        except ValueError:
            classification = self.coach.classify_input(message)
            current_fen = board.fen()
            if classification["type"] == "make_move":
                turn = "White" if board.turn == chess.WHITE else "Black"
                move = self.coach.process_make_move(current_fen, classification.get("context", message), turn)
                if self.parent.chess_board.try_move(move):
                    self.chat_display.append(f"<b>MAGNUS:</b> Move made: {move}")
                else:
                    self.chat_display.append(f"<b>MAGNUS:</b> Failed to process move.")
            elif classification["type"] == "best_move":
                self.coach.stockfish.set_fen_position(board.fen())
                best_move = self.coach.stockfish.get_best_move()
                if self.parent.mode == "puzzle" and self.parent.puzzle_moves:
                    best_move = self.parent.puzzle_moves[0]
                self.chat_display.append(f"<b>MAGNUS:</b> The best move here is {best_move}")
            elif classification["type"] == "give_insight":
                commentary = self.coach.generate_commentary(
                    current_fen,
                    self.parent.chess_board.previous_fen,
                    board.peek().uci()
                )
                self.chat_display.append(f"<b>MAGNUS:</b> {commentary}")
            elif classification["type"] == "ask_question":
                response = self.coach.process_question(current_fen, classification["context"], self.parent.username,
                                                       self.parent.elo)
                self.chat_display.append(f"<b>MAGNUS:</b> {response}")
            else:
                response = self.coach.process_general_convo(classification["context"])
                self.chat_display.append(f"<b>MAGNUS:</b> {response}")
