import chess
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIntValidator, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QSlider, QGridLayout, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTextEdit, QSpinBox, QMessageBox
)

from chess_ui.chess_gui import ChessGUI
from chess_ui.filter_puzzle import PuzzleFilterWidget
from trainer.chess_coach import ChessCoach


class ChessHomePageUI(QMainWindow):
    def __init__(self, puzzle_data: pd.DataFrame, coach: ChessCoach):
        super().__init__()
        self.setWindowTitle("Chess Playground")
        self.setGeometry(100, 100, 1920, 1080)

        self.puzzle_data = puzzle_data
        self.coach = coach

        self.setAutoFillBackground(True)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setSpacing(20)

        self._create_header(main_layout)
        main_layout.addLayout(self._create_user_info())

        self.game_modes_tab = QTabWidget()
        main_layout.addWidget(self.game_modes_tab)

        self._create_tabs()

        start_game_btn = self._create_start_game_button()
        main_layout.addWidget(start_game_btn)

    @staticmethod
    def _create_header(layout):
        image_label = QLabel()
        image_label.setPixmap(QPixmap("./chess_piece.png").scaled(60, 600, Qt.AspectRatioMode.KeepAspectRatio))
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        title_label = QLabel("Welcome!")
        title_label.setStyleSheet("font-size: 48px; font-weight: bold; color: green;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title_label)

    def _create_user_info(self):
        user_info_layout = QHBoxLayout()

        username_label = QLabel("Username:")
        username_label.setStyleSheet("font-size: 18px; color: green;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setStyleSheet(
            "font-size: 16px; padding: 5px; border: 1px solid #BDC3C7; border-radius: 5px;")
        user_info_layout.addWidget(username_label)
        user_info_layout.addWidget(self.username_input)

        elo_label = QLabel("Elo Rating:")
        elo_label.setStyleSheet("font-size: 18px; color: green;")
        self.elo_input = QLineEdit()
        self.elo_input.setPlaceholderText("Enter your Elo rating (e.g., 1500)")
        self.elo_input.setStyleSheet("font-size: 16px; padding: 5px; border: 1px solid #BDC3C7; border-radius: 5px;")
        self.elo_input.setValidator(QIntValidator(0, 3000))
        user_info_layout.addWidget(elo_label)
        user_info_layout.addWidget(self.elo_input)

        return user_info_layout

    def _create_tabs(self):
        self.analysis_widget = self._create_analysis_tab()
        self.game_modes_tab.addTab(self.analysis_widget, "Analyze Game")

        self.bot_widget = self._create_bot_tab()
        self.game_modes_tab.addTab(self.bot_widget, "Play Against Bot")

        self.puzzle_widget = self._create_puzzle_tab()
        self.game_modes_tab.addTab(self.puzzle_widget, "Puzzle")

    def _create_analysis_tab(self):
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout(analysis_widget)

        color_layout = QHBoxLayout()
        color_label = QLabel("Select Player Color:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(["White", "Black"])
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_combo)
        analysis_layout.addLayout(color_layout)

        pgn_label = QLabel("Paste PGN Notation:")
        self.pgn_input = QTextEdit()
        self.pgn_input.setPlaceholderText("Enter PGN notation here...")
        analysis_layout.addWidget(pgn_label)
        analysis_layout.addWidget(self.pgn_input)

        return analysis_widget

    def _create_bot_tab(self):
        bot_widget = QWidget()
        bot_layout = QVBoxLayout(bot_widget)
        bot_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        options_grid = QGridLayout()

        strength_label = QLabel("Bot Strength:")
        self.strength_combo = QComboBox()
        self.strength_combo.addItems([
            "Beginner (1000)", "Intermediate (1500)", "Advanced (1800)", "Expert (2100)",
            "Master (2400)", "Grandmaster (2700)", "Stockfish (3000)"
        ])
        options_grid.addWidget(strength_label, 0, 0)
        options_grid.addWidget(self.strength_combo, 0, 1)

        time_label = QLabel("Move Time (ms):")
        self.move_time_input = QSpinBox()
        self.move_time_input.setRange(100, 5000)
        self.move_time_input.setValue(1000)
        options_grid.addWidget(time_label, 1, 0)
        options_grid.addWidget(self.move_time_input, 1, 1)

        threads_label = QLabel("Threads:")
        self.threads_input = QSpinBox()
        self.threads_input.setRange(1, 8)
        self.threads_input.setValue(2)
        options_grid.addWidget(threads_label, 2, 0)
        options_grid.addWidget(self.threads_input, 2, 1)

        skill_label = QLabel("Skill Level:")
        self.skill_slider = QSlider(Qt.Orientation.Horizontal)
        self.skill_slider.setRange(0, 20)
        self.skill_slider.setValue(10)
        self.skill_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        skill_value_label = QLabel("10")
        self.skill_slider.valueChanged.connect(lambda value: skill_value_label.setText(str(value)))
        options_grid.addWidget(skill_label, 3, 0)
        options_grid.addWidget(self.skill_slider, 3, 1)
        options_grid.addWidget(skill_value_label, 3, 2)

        bot_layout.addLayout(options_grid)

        return bot_widget

    def _create_puzzle_tab(self):
        puzzle_widget = QWidget()
        puzzle_layout = QVBoxLayout(puzzle_widget)

        self.puzzle_filter = PuzzleFilterWidget(self.puzzle_data)
        puzzle_layout.addWidget(self.puzzle_filter)

        return puzzle_widget

    def _create_start_game_button(self):
        start_game_btn = QPushButton("Start Game")
        start_game_btn.setStyleSheet("""
            font-size: 18px; color: white; background-color: #2980B9; padding: 10px; border-radius: 5px;
            border: none; margin-top: 20px;
        """)
        start_game_btn.clicked.connect(self.start_game)
        return start_game_btn

    def start_game(self):
        selected_tab = self.game_modes_tab.currentIndex()
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Username Required", "Please enter a username.")
            return

        try:
            elo = int(self.elo_input.text() or 1500)
        except ValueError:
            elo = 1500

        game_options = self._get_game_options(selected_tab, username, elo)
        if not game_options:
            return

        self.chess_gui = ChessGUI(game_options)
        self.setCentralWidget(self.chess_gui)
        self.chess_gui.start_game()

    def _get_game_options(self, selected_tab, username, elo):
        if selected_tab == 0:
            return self._get_analysis_options(username, elo)
        elif selected_tab == 1:
            return self._get_bot_options(username, elo)
        elif selected_tab == 2:
            return self._get_puzzle_options(username, elo)
        else:
            QMessageBox.warning(self, "Invalid Mode", "Please select a valid game mode.")
            return None

    def _get_analysis_options(self, username, elo):
        color_inp = self.color_combo.currentText()
        if color_inp not in ["White", "Black"]:
            QMessageBox.warning(self, "Invalid Color", "Please select a valid player color.")
            return None

        color = chess.WHITE if color_inp == "White" else chess.BLACK
        pgn_moves = [move for move in self.pgn_input.toPlainText().strip().split() if not move.endswith('.')]
        if not pgn_moves:
            QMessageBox.warning(self, "PGN Required", "Please paste a valid PGN.")
            return None

        uci_moves = []
        temp_board = chess.Board()
        for san in pgn_moves:
            move = temp_board.parse_san(san)
            uci_moves.append(move.uci())
            temp_board.push(move)

        return {
            "mode": "analysis",
            "config": {
                "color": color,
                "moves": uci_moves,
                "threshold": 80
            },
            "username": username,
            "elo": elo,
            "coach": self.coach
        }

    def _get_bot_options(self, username, elo):
        bot_strength = self.strength_combo.currentText()
        move_time = self.move_time_input.value()
        threads = self.threads_input.value()
        skill_level = self.skill_slider.value()

        bot_elo = int(bot_strength.split("(")[1].split(")")[0])

        return {
            "mode": "bot",
            "config": {
                "bot_elo": bot_elo,
                "move_time": move_time,
                "threads": threads,
                "skill_level": skill_level
            },
            "username": username,
            "elo": elo,
            "coach": self.coach
        }

    def _get_puzzle_options(self, username, elo):
        if not self.puzzle_filter.current_puzzle:
            QMessageBox.warning(self, "No Puzzle Selected", "Please select a puzzle to solve.")
            return None

        return {
            "mode": "puzzle",
            "config": {
                "puzzle": self.puzzle_filter.current_puzzle
            },
            "username": username,
            "elo": elo,
            "coach": self.coach
        }
