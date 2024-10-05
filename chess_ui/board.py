import pandas as pd
import random
import sys
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import QTimer
import chess
import chess.svg

#using stockfish and maia should be the same, just diff bots, perhaps have diff command line argument
#possibly have something that says check if user or comp is in check
#after a puzzle, allow user to see what traits are
#or sort puzzles by traits
#"i want to train on opening puzzles"
#add stockfish eval bar??

#holy moly puzzles are working
#engine should be ez, the majority of logic is in puzzles
class ChessApp(QWidget):
    def __init__(self, puzzles_df=None, mode="puzzle"):
        super().__init__()
        self.mode = mode 
        self.puzzles_df = puzzles_df
        self.current_move_index = 0
        self.move_history = [] #store moves made by computer and user
        self.current_history_index = 0
        self.last_move = None
        
        self.engine = None
        if mode == "bot":
            self.start_bot_game()
        else:
            self.load_random_puzzle()
        self.initUI()

    def load_random_puzzle(self): #eventually sort by elo, let user report elo to start
        idx = random.randint(0, len(self.puzzles_df) - 1)
        self.fen = self.puzzles_df.iloc[idx]['FEN']
        self.correct_puzzle_moves = self.puzzles_df.iloc[idx]['Moves'].split(" ")
        print(self.correct_puzzle_moves)
        self.current_move_index = 0
        self.move_history = []
        self.current_history_index = 0
        self.board = chess.Board(self.fen)
        self.last_move = None
        self.is_white_to_move = self.board.turn == chess.WHITE
        self.orientation = chess.BLACK if self.is_white_to_move else chess.WHITE

    def start_bot_game(self): #change this later to start at a random color
        self.board = chess.Board()
        self.last_move = None
        self.is_white_to_move = True
        self.orientation = chess.WHITE
        self.engine = chess.engine.SimpleEngine.popen_uci("path/to/stockfish")  # Change this to your Stockfish path

    def initUI(self):
        self.setWindowTitle("Chess Game" if self.mode == "bot" else "Chess Puzzle")

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
        
        self.back_button = QPushButton("Back")
        self.back_button.setEnabled(False)
        button_layout.addWidget(self.back_button)
        self.back_button.clicked.connect(self.go_back)

        self.forward_button = QPushButton("Forward")
        self.forward_button.setEnabled(False)
        button_layout.addWidget(self.forward_button)
        self.forward_button.clicked.connect(self.go_forward)

        layout.addLayout(button_layout)

        self.submit_button = QPushButton("Submit Move")
        layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.check_move)

        if self.mode == "puzzle":
            self.skip_button = QPushButton("Skip Puzzle")
            layout.addWidget(self.skip_button)
            self.skip_button.clicked.connect(self.skip_puzzle)

        self.setLayout(layout)
        self.update_board()

        if self.mode == "puzzle":
            QTimer.singleShot(1000, self.computer_move)
        else:
            self.engine_move()

    def get_turn_message(self):
        if self.mode == "bot":
            return "Your move" if self.is_white_to_move else "Bot is thinking..."
        return "White to move" if self.is_white_to_move else "Black to move"

    def update_board(self):
        if self.last_move:
            svg_data = chess.svg.board(self.board, orientation=self.orientation, lastmove=self.last_move).encode('utf-8')
        else:
            svg_data = chess.svg.board(self.board, orientation=self.orientation).encode('utf-8')
        self.svg_widget.load(svg_data)

        self.submit_button.setEnabled(self.current_history_index == len(self.move_history))

    def check_move(self):
        user_move = self.move_input.text()
        try:
            move = self.board.parse_san(user_move)
            if move in self.board.legal_moves:
                if self.mode == "bot":
                    self.board.push(move)
                    self.move_history.append(move)
                    self.current_history_index = len(self.move_history)
                    self.last_move = move
                    self.update_board()
                    self.move_input.clear()
                    self.current_move_index += 1

                    self.back_button.setEnabled(True)

                    self.is_white_to_move = not self.is_white_to_move
                    self.turn_label.setText(self.get_turn_message())
                    #have end of game check

                if self.mode == "puzzle":
                    #self.current_move_index += 1
                    print(self.current_move_index)
                    print(self.correct_puzzle_moves[self.current_move_index])
                    if user_move == self.correct_puzzle_moves[self.current_move_index]:
                        self.board.push(move)
                        self.move_history.append(move)
                        self.current_history_index = len(self.move_history)
                        self.last_move = move
                        self.update_board()
                        self.move_input.clear()
                        self.current_move_index += 1

                        self.back_button.setEnabled(True)

                        self.is_white_to_move = not self.is_white_to_move
                        self.turn_label.setText(self.get_turn_message())
                        if self.current_move_index >= len(self.correct_puzzle_moves):
                            self.turn_label.setText(self.get_turn_message())
                            self.move_label.setText("Puzzle completed!")
                            self.submit_button.setEnabled(False)
                        else:
                            self.move_label.setText("Correct! Waiting for opponent's move...")
                            QTimer.singleShot(1500, self.computer_move)
                    else:
                        self.move_label.setText("Incorrect move, try again:") 
                        #self.current_move_index -= 1        
                else:
                    self.engine_move()
            else:
                self.move_label.setText("Incorrect move, try again:")
                

        except ValueError: #does it even ever reach here
            self.move_label.setText("Invalid move, try again:")

    def computer_move(self): #this is for puzzle response to correct user move
        if self.current_move_index < len(self.correct_puzzle_moves):
            computer_move = self.correct_puzzle_moves[self.current_move_index]
            move_obj = self.board.parse_san(computer_move)
            self.board.push(move_obj)
            self.move_history.append(move_obj)
            self.current_history_index = len(self.move_history)
            self.last_move = move_obj
            self.update_board()

            self.back_button.setEnabled(True)

            self.is_white_to_move = not self.is_white_to_move
            self.turn_label.setText(self.get_turn_message())
            self.current_move_index += 1

    def engine_move(self): #fix this later, we ensure puzzle works, load up a maia or stockfish
        if not self.is_white_to_move:
            result = self.engine.play(self.board, chess.engine.Limit(time=1.0)) #time can change here
            self.board.push(result.move)
            self.last_move = result.move
            self.update_board()

            self.is_white_to_move = not self.is_white_to_move
            self.turn_label.setText(self.get_turn_message())

            if self.board.is_game_over():
                self.move_label.setText("Game over!")
                self.submit_button.setEnabled(False)

    def skip_puzzle(self): #we good here
        if self.mode == "puzzle":
            self.load_random_puzzle()
            self.update_board()

            self.move_label.setText("Enter your move:")
            self.turn_label.setText(self.get_turn_message())
            self.submit_button.setEnabled(True)
            self.move_input.clear()

            self.back_button.setEnabled(False)
            self.forward_button.setEnabled(False)

            QTimer.singleShot(1000, self.computer_move)

    def go_back(self): #works
        if self.current_history_index > 0:
            self.current_history_index -= 1
            last_move_undone = self.board.pop()
            self.last_move = self.board.peek() if self.board.move_stack else None
            self.update_board()

            self.forward_button.setEnabled(True)

            if self.current_history_index == 0:
                self.back_button.setEnabled(False)

    def go_forward(self): #works
        if self.current_history_index < len(self.move_history):
            move_obj = self.move_history[self.current_history_index]
            self.board.push(move_obj)
            self.last_move = move_obj
            self.current_history_index += 1
            self.update_board()

            self.back_button.setEnabled(True)

            if self.current_history_index >= len(self.move_history):
                self.forward_button.setEnabled(False)