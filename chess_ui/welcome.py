from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QStackedLayout
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import sys


class WelcomeScreen(QWidget):
    def __init__(self, switch_to_main_app):
        super().__init__()
        self.switch_to_main_app = switch_to_main_app
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # Chess piece image
        chess_image = QLabel(self)
        pixmap = QPixmap("C:\\Users\\wei0c\\Desktop\\school\\7-1\\CS-6320-NLP\\chess_ui\\chess_piece.png")  # Path to your chess piece image
        pixmap = pixmap.scaled(60, 600, Qt.AspectRatioMode.KeepAspectRatio)
        #chess_image.setStyleSheet("background-color: black;") 
        chess_image.setPixmap(pixmap)
        chess_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(chess_image)

        # Welcome message
        welcome_label = QLabel("Welcome!")
        welcome_label.setStyleSheet("font-size: 48px; font-weight: bold; color: green;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)

        # Name input
        name_label = QLabel("Enter your name:")
        name_label.setStyleSheet("font-size: 18px; color: green;")
        self.name_input = QLineEdit(self)
        self.name_input.setStyleSheet("font-size: 16px; padding: 5px; border: 1px solid #BDC3C7; border-radius: 5px;")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # ELO input
        elo_label = QLabel("Enter your ELO:")
        elo_label.setStyleSheet("font-size: 18px; color: green;")
        self.elo_input = QLineEdit(self)
        self.elo_input.setPlaceholderText("e.g., 1200")
        self.elo_input.setStyleSheet("font-size: 16px; padding: 5px; border: 1px solid #BDC3C7; border-radius: 5px;")
        layout.addWidget(elo_label)
        layout.addWidget(self.elo_input)

        # Dropdown for mode selection
        mode_label = QLabel("Today I would like to:")
        mode_label.setStyleSheet("font-size: 18px; color: green;")
        self.mode_dropdown = QComboBox(self)
        self.mode_dropdown.addItems(["analyze a game", "train puzzles", "train against the computer"])
        self.mode_dropdown.setStyleSheet("font-size: 16px; padding: 5px; border: 1px solid #BDC3C7; border-radius: 5px;")
        layout.addWidget(mode_label)
        layout.addWidget(self.mode_dropdown)

        # Start button
        start_button = QPushButton("Start")
        start_button.setStyleSheet("""
            font-size: 18px; color: white; background-color: #2980B9; padding: 10px; border-radius: 5px;
            border: none; margin-top: 20px;
        """)
        start_button.clicked.connect(self.start_app)
        layout.addWidget(start_button)

        self.setLayout(layout)

    def start_app(self):
        name = self.name_input.text().strip()
        elo = self.elo_input.text().strip()
        mode = self.mode_dropdown.currentText()

        if not name or not elo.isdigit():
            error_message = QLabel("Please enter a valid name and numeric ELO.")
            error_message.setStyleSheet("color: red; font-size: 16px;")
            return

        self.switch_to_main_app(name, int(elo), mode)


class MainApp(QWidget):
    def __init__(self, name, elo, mode, puzzles_df=None):
        super().__init__()
        self.name = name
        self.elo = elo
        self.mode = mode
        self.puzzles_df = puzzles_df
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        welcome_message = QLabel(f"Hello {self.name} (ELO: {self.elo}), let's {self.mode}!")
        welcome_message.setStyleSheet("font-size: 20px; color: #2C3E50;")
        layout.addWidget(welcome_message)

        # Placeholder for initializing the appropriate mode
        mode_message = QLabel(f"Initializing {self.mode} mode...")
        mode_message.setStyleSheet("font-size: 18px; color: #34495E;")
        layout.addWidget(mode_message)

        self.setLayout(layout)


class App(QWidget):
    def __init__(self, puzzles_df=None):
        super().__init__()
        self.puzzles_df = puzzles_df
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Chess Application")
        self.setFixedSize(800, 600)  # Make the application wider

        # Stacked layout to switch between welcome screen and main app
        self.layout = QStackedLayout()

        # Welcome screen
        self.welcome_screen = WelcomeScreen(self.switch_to_main_app)
        self.layout.addWidget(self.welcome_screen)

        self.setLayout(self.layout)

    def switch_to_main_app(self, name, elo, mode):
        self.main_app = MainApp(name, elo, mode, self.puzzles_df)
        self.layout.addWidget(self.main_app)
        self.layout.setCurrentWidget(self.main_app)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    puzzles_df = None  # Replace with your puzzles DataFrame if needed
    main = App(puzzles_df)
    main.show()
    sys.exit(app.exec())
