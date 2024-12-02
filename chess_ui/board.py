import pandas as pd
import random
import threading
from PyQt6.QtWidgets import (QApplication, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout, QTextEdit, QScrollArea, QFrame, QListWidget)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import QTimer, Qt
import chess
import chess.svg
from stockfish import Stockfish
import time

#TODO WHEN BLUNDER MOVE BACK AND THEN WHEN CORRECT MOVE, PUSH AND THEN 
#figure out why it doesnt continue afte you get a move right
class ChessApp(QWidget):
    def __init__(self, puzzles_df=None, mode="puzzle"):
        super().__init__()
        self.mode = mode
        self.puzzles_df = puzzles_df
        self.current_move_index = 0
        self.move_history = []
        self.current_history_index = 0
        self.last_move = None
        self.engine = None
        self.thread_lock = threading.Lock()

        if mode == "bot":
            self.start_bot_game()
        elif mode == "analysis":
            self.start_analysis()
        else:
            self.load_random_puzzle()

        self.initUI()

    def start_analysis(self):
        self.board = chess.Board()
        self.is_white_to_move = True
        self.orientation = chess.WHITE
        self.awaiting_game_notation = True
        self.awaiting_orientation = True
        self.awaiting_best_move = False
        self.curr_best_move = None
        self.game_notation = None
        self.side = None
        self.curr_moves = []
        self.moves_analyzed = 0

    def handle_chat_input(self, user_input):
        if self.mode == "analysis":
            if self.awaiting_game_notation:
                self.move_history = self.parse_raw_san(user_input)
                self.awaiting_game_notation = False
                self.awaiting_orientation = True
                #return
            if self.awaiting_orientation:
                if user_input.upper() not in ("W", "B"):
                    self.add_to_chat("Coach", "Please enter W for White or B for Black.")
                    return
                self.side = chess.WHITE if user_input.upper() == "W" else chess.BLACK
                self.orientation = self.side
                self.add_to_chat("Coach", "Starting analysis...")
                self.awaiting_orientation = False
                threading.Thread(target=self.prepare_analysis).start()
                #return

            if self.awaiting_best_move:
                user_move = user_input.strip()
                if user_move.lower() == "answer":
                    self.add_to_chat("Coach", f"The best move here is {self.curr_best_move}")
                    self.awaiting_best_move = False
                    #threading.Thread(target=self.continue_analysis).start()
                    threading.Thread(target=self.analysis_walkthrough).start()
                elif chess.Move.from_uci(user_move) in self.board.legal_moves:
                    if user_move == self.curr_best_move:
                        self.add_to_chat("Coach", f"Correct! Good job finding the best move!")
                        self.awaiting_best_move = False
                        #threading.Thread(target=self.continue_analysis).start()
                        threading.Thread(target=self.analysis_walkthrough).start()
                    else:
                        self.add_to_chat("Coach", "That's not the best move. Try again, or type 'answer' to reveal it.")
                else:
                    self.add_to_chat("Coach", "Invalid move. Try again or type 'answer' to reveal the best move.")
                return

    def parse_raw_san(self, notation):
        moves = notation.split()
        return [move for move in moves if not move.endswith('.')]

    def prepare_analysis(self):
        self.engine = Stockfish(
            path="C:\\Users\\wei0c\\Desktop\\school\\7-1\\CS-6320-NLP\\stockfish\\stockfish-windows-x86-64-avx2.exe",
            depth=15,
            parameters={"Hash": 2048, "Skill Level": 20, "Threads": 3, "Minimum Thinking Time": 4, "UCI_Chess960": "false"}
        )
        self.uci_notation = []
        for san in self.move_history:
            move = self.board.parse_san(san)
            uci_move = move.uci()
            self.board.push(move)
            self.uci_notation.append(uci_move)
        self.curr_moves = []
        threading.Thread(target=self.analysis_walkthrough).start()

    def analysis_walkthrough(self):
        self.board.reset()
        last_move = None
        for move_idx, uci_move in enumerate(self.uci_notation[len(self.curr_moves):]):
            move_number = move_idx // 2 + 1
            best_move = self.engine.get_best_move()
            self.curr_moves.append(best_move)
            best_move_eval = self.engine.get_evaluation()
            curr_best_move_eval = [best_move_eval["type"], best_move_eval["value"]]
            self.curr_moves.append(uci_move)
            self.engine.set_position(self.curr_moves)

            if move_idx % 2 == 0:
                self.move_list.addItem(f"{move_number}. {self.board.san(chess.Move.from_uci(uci_move))}")
            else:
                current_row = self.move_list.count() - 1
                if current_row >= 0:  # Check if there are any items
                    last_item = self.move_list.item(current_row)
                    if last_item:  # Check if we got an item
                        last_item.setText(f"{last_item.text()} {self.board.san(chess.Move.from_uci(uci_move))}")
            self.board.push_uci(uci_move)
            self.update_board()
            self.moves_analyzed += 1
            self.current_history_index = self.moves_analyzed
            time.sleep(0.2) #can play with this

            if (self.side == chess.WHITE and move_idx % 2 == 1) or (self.side == chess.BLACK and move_idx % 2 == 0):
                continue

            curr_eval = self.engine.get_evaluation()
            player_move_eval = [curr_eval["type"], curr_eval["value"]]

            if curr_best_move_eval[0] != player_move_eval[0] or abs(curr_best_move_eval[1] - player_move_eval[1]) > 15: #play w this
                self.curr_best_move = best_move
                self.add_to_chat("Coach", "Here you made a blunder, can you find the best move?") #need to move the piece back and update the board (remove the move from move list)
                self.add_to_chat("Joe", f"{best_move}")
                self.awaiting_best_move = True
                break

    def load_random_puzzle(self):
        idx = random.randint(0, len(self.puzzles_df) - 1)
        self.fen = self.puzzles_df.iloc[idx]['FEN']
        self.correct_puzzle_moves = self.puzzles_df.iloc[idx]['Moves'].split(" ")
        self.current_move_index = 0
        self.move_history = []
        self.current_history_index = 0
        self.board = chess.Board(self.fen)
        self.last_move = None
        self.is_white_to_move = self.board.turn == chess.WHITE
        self.orientation = chess.BLACK if self.is_white_to_move else chess.WHITE

    def start_bot_game(self):
        self.white = random.randint(0, 10) % 2
        self.engine = Stockfish(
            path="C:\\Users\\wei0c\\Desktop\\school\\7-1\\CS-6320-NLP\\stockfish\\stockfish-windows-x86-64-avx2.exe",
            depth=10,
            parameters={"Hash": 2048, "UCI_Elo": "1800", "Threads": 2, "Minimum Thinking Time": 3, "UCI_Chess960": "false"}
        )
        self.board = chess.Board()
        self.last_move = None
        self.is_white_to_move = True

        self.move_history = []
        self.orientation = chess.WHITE if self.white else chess.BLACK

        if not self.white:
            threading.Thread(target=self.engine_move).start()

    def initUI(self):
        self.setWindowTitle("Chess Game" if self.mode == "bot" else "Chess Analysis")
        self.setMinimumSize(1300, 800)  # Increased window size to accommodate three panels

        main_layout = QHBoxLayout()
        
        # Left side - Chat area
        chat_container = QWidget()
        chat_layout = QVBoxLayout()
        
        chat_label = QLabel("Chat")
        chat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setMinimumWidth(300)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                color: black;
            }
        """)
        
        # Chat input
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(60)
        self.chat_input.setPlaceholderText("Chat with your opponent...")
        self.chat_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        # Send button
        self.chat_button = QPushButton("Send Message")
        self.chat_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        chat_layout.addWidget(chat_label)
        chat_layout.addWidget(self.chat_history)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.chat_button)
        chat_container.setLayout(chat_layout)
        
        # Middle - Chess board and move input
        board_container = QWidget()
        board_layout = QVBoxLayout()
        
        # Chess board
        self.svg_widget = QSvgWidget()
        board_layout.addWidget(self.svg_widget)
        
        # Turn indicator
        self.turn_label = QLabel(self.get_turn_message())
        self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        board_layout.addWidget(self.turn_label)
        
        # Move input
        move_input_container = QWidget()
        move_input_layout = QHBoxLayout()
        
        self.move_input = QTextEdit()
        self.move_input.setMaximumHeight(60)
        self.move_input.setPlaceholderText("Enter your move (e.g., e4, Nc3)...")
        self.move_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        self.submit_button = QPushButton("Make Move")
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        move_input_layout.addWidget(self.move_input)
        move_input_layout.addWidget(self.submit_button)
        move_input_container.setLayout(move_input_layout)
        board_layout.addWidget(move_input_container)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setEnabled(False)
        self.forward_button = QPushButton("Forward")
        self.forward_button.setEnabled(False)
        
        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.forward_button)
        board_layout.addLayout(nav_layout)
        
        if self.mode == "puzzle":
            self.skip_button = QPushButton("Skip Puzzle")
            board_layout.addWidget(self.skip_button)
            self.skip_button.clicked.connect(self.skip_puzzle)
        
        board_container.setLayout(board_layout)
        
        #move history on the right
        history_container = QWidget()
        history_layout = QVBoxLayout()
        
        history_label = QLabel("Move History")
        history_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        history_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.move_list = QListWidget()
        self.move_list.setMinimumWidth(150)
        self.move_list.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                color: black;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        
        history_layout.addWidget(history_label)
        history_layout.addWidget(self.move_list)
        history_container.setLayout(history_layout)
        
        # Add containers to main layout
        main_layout.addWidget(chat_container, 1)
        main_layout.addWidget(board_container, 2)
        main_layout.addWidget(history_container, 1)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.submit_button.clicked.connect(self.process_move)
        self.chat_button.clicked.connect(self.process_chat)
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        
        self.update_board()
        
        # Initial bot move if needed
        if self.mode == "puzzle":
            QTimer.singleShot(1000, self.computer_move)
        elif self.mode == "bot" and not self.white != self.is_white_to_move: #if user is white, then when black to move it moves
            self.engine_move()
            
        # use gpt for this later
        if self.mode == "analysis":
            self.add_to_chat("Coach", "Please give me your game notation:") #this is being called before initUI LOL
        elif self.mode == "puzzle":
            self.add_to_chat("Coach", "Here is a random puzzle, feel free to ask me any questions!")
        else:
            self.add_to_chat("Coach", "I see you want to put your skills to the test. As you coach, you can still ask me questions any time.")
    
    def process_move(self):
        move_text = self.move_input.toPlainText().strip()
        if not move_text:
            return
            
        self.move_input.clear()
        
        try:
            move = self.board.parse_san(move_text)
            if move in self.board.legal_moves:
                self.handle_legal_move(move, move_text)
            else:
                self.add_to_chat("System", "That move is not legal. Please try again.")
        except ValueError:
            self.add_to_chat("System", "Invalid move format. Please use SAN (e.g., 'e4' or 'Nc3')") #might change to prompt user to give moves in UCI

    def process_chat(self):
        chat_text = self.chat_input.toPlainText().strip()
        if chat_text:
            #PARSER HERE SEND TO PARSER HERE
            self.add_to_chat("You", chat_text)
            self.chat_input.clear()
            self.handle_chat_input(chat_text)
            
            if self.mode == "bot":
                self.add_to_chat("Bot", "I'm thinking about my response...")

    def handle_legal_move(self, move, move_san):
        if self.mode == "puzzle":
            if move_san == self.correct_puzzle_moves[self.current_move_index]:
                self.make_move(move, move_san)
                
                if self.current_move_index >= len(self.correct_puzzle_moves):
                    self.add_to_chat("System", "Puzzle completed! Well done!")
                    self.submit_button.setEnabled(False)
                else:
                    QTimer.singleShot(1500, self.computer_move)
            else:
                self.add_to_chat("System", "Incorrect move. Try again!")
        elif self.mode == "bot":  # Bot mode
            self.make_move(move, move_san)
            if not self.board.is_game_over():
                self.engine_move()
            else:
                self.add_to_chat("System", "Game Over!")
                self.submit_button.setEnabled(False)

    def make_move(self, move, move_uci): #this might be san lol
        # Handle move list display
        move_number = len(self.move_history) // 2 + 1
        if self.is_white_to_move:
            # White's move - add new row
            self.move_list.addItem(f"{move_number}. {self.board.san(chess.Move.from_uci(move_uci))}")
        else:
            # Black's move - append to existing row
            current_row = self.move_list.count() - 1
            if current_row >= 0:  # Check if there are any items
                last_item = self.move_list.item(current_row)
                if last_item:  # Check if we got an item
                    last_item.setText(f"{last_item.text()} {self.board.san(chess.Move.from_uci(move_uci))}")
            else:
                # Handle rare case where black moves first (in some puzzles)
                self.move_list.addItem(f"{move_number}... {self.board.san(chess.Move.from_uci(move_uci))}")
            
        # Update board state
        self.board.push(move)
        self.move_history.append(move)
        self.current_history_index = len(self.move_history)
        self.last_move = move
        self.update_board()
        
        # Update UI state
        self.back_button.setEnabled(True)
        self.is_white_to_move = not self.is_white_to_move
        self.turn_label.setText(self.get_turn_message())
        self.current_move_index += 1

    def add_to_chat(self, sender, message):
        self.chat_history.append(f"<b>{sender}:</b> {message}")
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )


    def get_llm_response(self, question, context): #placeholder
        import openai
        openai.api_key = open("C:\\Users\\wei0c\\Desktop\\school\\7-1\\CS-6320-NLP\\chess_ui\\openai_key.txt", "r").read()
        messages = [{"role": "system", "content": context}]
        messages.append({"role": "user", "content": question})
        response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                )
        return response.choices[0].message.content

    def get_transformer_response(self):
        
        response = "" #call transformer here
        return 

    def engine_move(self):
        if not self.is_white_to_move:
            self.engine.set_position(self.move_history)
            result = self.engine.get_best_move_time(3000)
            move = self.board.parse_san(result)
            self.make_move(move, result)

    def update_board(self):
        if self.last_move:
            svg_data = chess.svg.board(
                self.board, 
                orientation=self.orientation, 
                lastmove=self.last_move,
                size=700  # Make board larger to match new layout
            ).encode('utf-8')
        else:
            svg_data = chess.svg.board(
                self.board, 
                orientation=self.orientation,
                size=700
            ).encode('utf-8')
        self.svg_widget.load(svg_data)

        self.submit_button.setEnabled(self.current_history_index == len(self.move_history))
        
        self.back_button.setEnabled(self.current_history_index > 0)
        self.forward_button.setEnabled(self.current_history_index < len(self.move_history))

    def get_turn_message(self):
        if self.board.is_checkmate():
            return "Checkmate! " + ("Black" if self.board.turn else "White") + " wins!"
        elif self.board.is_stalemate():
            return "Game drawn by stalemate!"
        elif self.board.is_insufficient_material():
            return "Game drawn by insufficient material!"
        elif self.board.is_check():
            return "Check! " + ("White" if self.board.turn else "Black") + " to move"
        
        if self.mode == "bot":
            return "Your move" if self.is_white_to_move else "Bot is thinking..."
        return "White to move" if self.is_white_to_move else "Black to move"

    def go_back(self):
        if self.mode == "analysis":
            def back_thread():
                with self.thread_lock:
                    try:
                        self.current_history_index -= 1
                        self.board.pop()
                        self.last_move = self.board.peek() if self.board.move_stack else None
                        self.is_white_to_move = self.board.turn
                        self.update_board()
                    except Exception as e:
                        self.add_to_chat("System", f"Error during back operation: {e}")
            if self.current_history_index > 0:
                threading.Thread(target=back_thread).start()
        elif self.current_history_index > 0:
            self.current_history_index -= 1
            self.board.pop()
            self.last_move = self.board.peek() if self.board.move_stack else None
            self.is_white_to_move = self.board.turn
            self.update_board()
            
            # Update move list selection
            self.move_list.setCurrentRow(self.current_history_index // 2)
            
            # Update turn label
            self.turn_label.setText(self.get_turn_message())

    def go_forward(self):
        if self.mode == "analysis":
            def forward_thread():
                with self.thread_lock:
                    try:
                        move = self.board.parse_san(self.move_history[self.current_history_index])
                        self.board.push(move)
                        self.last_move = move
                        self.current_history_index += 1
                        self.is_white_to_move = self.board.turn
                        self.update_board()
                    except Exception as e:
                        self.add_to_chat("System", f"Error during forward operation: {e}")
            if self.current_history_index < self.moves_analyzed:
                threading.Thread(target=forward_thread).start()
        elif self.current_history_index < len(self.move_history):
            move = self.move_history[self.current_history_index]
            self.board.push(move)
            self.last_move = move
            self.current_history_index += 1
            self.is_white_to_move = self.board.turn
            self.update_board()
            
            # Update move list selection
            self.move_list.setCurrentRow(self.current_history_index // 2)
            
            # Update turn label
            self.turn_label.setText(self.get_turn_message())

    def skip_puzzle(self):
        if self.mode == "puzzle":
            self.load_random_puzzle()
            self.update_board()

            # Clear move list
            self.move_list.clear()

            # Reset UI elements
            self.turn_label.setText(self.get_turn_message())
            self.submit_button.setEnabled(True)
            self.move_input.clear()
            self.chat_input.clear()

            self.back_button.setEnabled(False)
            self.forward_button.setEnabled(False)

            self.add_to_chat("System", "New puzzle loaded! Make your first move.")

            QTimer.singleShot(1000, self.computer_move)

    def computer_move(self):
        if self.current_move_index < len(self.correct_puzzle_moves):
            computer_move = self.correct_puzzle_moves[self.current_move_index]
            move_obj = self.board.parse_san(computer_move)
            self.make_move(move_obj, computer_move)
            
            if not self.board.is_game_over():
                self.turn_label.setText(self.get_turn_message())
                self.move_input.setPlaceholderText("Your turn! Enter your move...")
            else:
                self.add_to_chat("System", "Puzzle completed!")
                self.submit_button.setEnabled(False)
