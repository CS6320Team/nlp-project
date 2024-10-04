import pandas as pd
import random
import sys
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import QTimer
import chess
import chess.svg

class ChessPuzzleApp(QWidget):
    def __init__(self, puzzles_df):
        super().__init__()
        self.puzzles_df = puzzles_df
        self.current_move_index = 0
        self.move_history = []  #store correct move sequence
        self.current_history_index = 0  #keep track of where the user is in the move sequence
        self.last_move = None  # Track the last move for highlighting
        self.load_random_puzzle()
        self.initUI()

    def load_random_puzzle(self):
        idx = random.randint(0, len(self.puzzles_df) - 1)
        self.fen = self.puzzles_df.iloc[idx]['FEN']
        self.moves = self.puzzles_df.iloc[idx]['Moves'].split(" ")
        self.current_move_index = 0
        self.move_history = []  # Reset move history when a new puzzle is loaded
        self.current_history_index = 0  # Reset history index
        self.board = chess.Board(self.fen)
        self.last_move = None  # Reset last move

        self.is_white_to_move = self.board.turn == chess.WHITE
        self.orientation = chess.BLACK if self.is_white_to_move else chess.WHITE

    def initUI(self):
        self.setWindowTitle("Chess Puzzle")

        layout = QVBoxLayout()

        self.svg_widget = QSvgWidget()
        layout.addWidget(self.svg_widget)

        self.move_label = QLabel("Enter your move:")
        layout.addWidget(self.move_label)
        self.move_input = QLineEdit(self)
        layout.addWidget(self.move_input)

        self.turn_label = QLabel(self.get_turn_message())
        layout.addWidget(self.turn_label)

        button_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("Back")
        self.back_button.setEnabled(False)  # Disabled initially because no moves to go back to
        button_layout.addWidget(self.back_button)
        self.back_button.clicked.connect(self.go_back)

        # Forward button
        self.forward_button = QPushButton("Forward")
        self.forward_button.setEnabled(False)  # Disabled because no future moves to go to
        button_layout.addWidget(self.forward_button)
        self.forward_button.clicked.connect(self.go_forward)

        layout.addLayout(button_layout)

        # Submit button
        self.submit_button = QPushButton("Submit Move")
        layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.check_move)

        # Skip puzzle button
        self.skip_button = QPushButton("Skip Puzzle")
        layout.addWidget(self.skip_button)
        self.skip_button.clicked.connect(self.skip_puzzle)

        self.setLayout(layout)
        self.update_board()

        # Computer plays the first move
        QTimer.singleShot(500, self.computer_move)

    def get_turn_message(self):
        return "White to move" if self.is_white_to_move else "Black to move"

    def update_board(self):
        # Highlight the last move, if any
        if self.last_move:
            svg_data = chess.svg.board(self.board, orientation=self.orientation, lastmove=self.last_move).encode('utf-8')
        else:
            svg_data = chess.svg.board(self.board, orientation=self.orientation).encode('utf-8')
        self.svg_widget.load(svg_data)

        # Enable/Disable submit button based on whether we're at the current state
        self.submit_button.setEnabled(self.current_history_index == len(self.move_history))

    def check_move(self):
        user_move = self.move_input.text()

        try:
            move = self.board.parse_san(user_move)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.move_history.append(move)  # Add player's move to history
                self.current_history_index = len(self.move_history)  # Move to the current position in history
                self.last_move = move  # Track the last move as a chess.Move object
                self.update_board()
                self.move_input.clear()
                self.current_move_index += 1

                # Enable back button after a valid move
                self.back_button.setEnabled(True)

                self.is_white_to_move = not self.is_white_to_move
                self.turn_label.setText(self.get_turn_message())

                if self.current_move_index >= len(self.moves):
                    if user_move == self.moves[self.current_move_index]:
                        self.move_label.setText("Puzzle completed!")
                        self.submit_button.setEnabled(False)
                    else:
                        self.move_label.setText("Incorrect move, try again:")
                        self.current_move_index -= 1
                else:
                    self.move_label.setText("Correct! Waiting for opponent's move...")
                    QTimer.singleShot(1500, self.computer_move)
            else:
                self.move_label.setText("Incorrect move, try again:")
                self.current_move_index -= 1
        except ValueError:
            self.move_label.setText("Invalid move, try again:")

    def computer_move(self):
        if self.current_move_index < len(self.moves):
            computer_move = self.moves[self.current_move_index]
            move_obj = self.board.parse_san(computer_move)
            self.board.push(move_obj)
            self.move_history.append(move_obj)  # Add computer's move to history
            self.current_history_index = len(self.move_history)  # Sync history index
            self.last_move = move_obj  # Track the computer's move as a chess.Move object
            self.update_board()

            # Enable the back button after the computer's move
            self.back_button.setEnabled(True)

            self.is_white_to_move = not self.is_white_to_move
            self.turn_label.setText(self.get_turn_message())
            self.current_move_index += 1

            if self.current_move_index >= len(self.moves):
                self.move_label.setText("Puzzle completed!")
                self.submit_button.setEnabled(False)

    def go_back(self):
        if self.current_history_index > 0:
            self.current_history_index -= 1
            last_move_undone = self.board.pop()  # Undo the last move
            self.last_move = self.board.peek() if self.board.move_stack else None  # Track the previous move
            self.update_board()

            # Enable forward button since we're moving back in history
            self.forward_button.setEnabled(True)

            # Disable back button if we've undone all moves
            if self.current_history_index == 0:
                self.back_button.setEnabled(False)

    def go_forward(self):
        if self.current_history_index < len(self.move_history):
            # Re-apply the move at the current history index
            move_obj = self.move_history[self.current_history_index]
            self.board.push(move_obj)
            self.last_move = move_obj  # Track the forward move for highlighting
            self.current_history_index += 1
            self.update_board()

            # Enable back button after going forward
            self.back_button.setEnabled(True)

            # Disable forward button if all moves are replayed
            if self.current_history_index >= len(self.move_history):
                self.forward_button.setEnabled(False)

    def skip_puzzle(self):
        self.load_random_puzzle()
        self.update_board()

        self.move_label.setText("Enter your move:")
        self.turn_label.setText(self.get_turn_message())
        self.submit_button.setEnabled(True)
        self.move_input.clear()

        self.back_button.setEnabled(False)  # Disable since no move history yet
        self.forward_button.setEnabled(False)

        QTimer.singleShot(1000, self.computer_move)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    puzzles_df = pd.read_csv("C:\\Users\\wei0c\\Desktop\\school\\7-1\\CS-6320-NLP\\lichess_db_puzzle.csv")

    window = ChessPuzzleApp(puzzles_df)
    window.show()

    sys.exit(app.exec())
