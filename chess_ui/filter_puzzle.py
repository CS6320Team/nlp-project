from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QPushButton, QTextEdit, QLabel, QSpinBox, QComboBox, QMessageBox
)


class PuzzleFilterWidget(QWidget):
    def __init__(self, puzzle_data):
        super().__init__()
        self.current_puzzle = None
        self.puzzle_data = puzzle_data

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Filters Group Box
        self.filters_group = QGroupBox("Filter Options")
        filters_layout = QVBoxLayout()
        self.filters_group.setLayout(filters_layout)
        main_layout.addWidget(self.filters_group)

        # Rating Filter
        filters_layout.addLayout(self.create_rating_filter())

        # Themes Filter
        filters_layout.addLayout(self.create_themes_filter())

        # Buttons (Random Puzzle and Reset)
        button_layout = QHBoxLayout()
        self.random_puzzle_btn = QPushButton("Random Puzzle")
        self.random_puzzle_btn.clicked.connect(self.select_random_puzzle)
        button_layout.addWidget(self.random_puzzle_btn)

        self.reset_filters_btn = QPushButton("Reset Filters")
        self.reset_filters_btn.clicked.connect(self.reset_filters)
        button_layout.addWidget(self.reset_filters_btn)

        filters_layout.addLayout(button_layout)

        # Puzzle Display Area
        self.puzzle_display = QTextEdit()
        self.puzzle_display.setReadOnly(True)
        self.puzzle_display.setPlaceholderText("Puzzle details will appear here...")
        main_layout.addWidget(self.puzzle_display)

    def create_rating_filter(self):
        rating_layout = QHBoxLayout()
        rating_label = QLabel("Rating:")
        max_rating = self.puzzle_data['Rating'].max()
        min_rating = self.puzzle_data['Rating'].min()

        self.min_rating_input = QSpinBox()
        self.min_rating_input.setRange(min_rating, max_rating)
        self.min_rating_input.setPrefix("Min: ")
        self.min_rating_input.setValue(min_rating)

        self.max_rating_input = QSpinBox()
        self.max_rating_input.setRange(min_rating, max_rating)
        self.max_rating_input.setPrefix("Max: ")
        self.max_rating_input.setValue(max_rating)

        rating_layout.addWidget(rating_label)
        rating_layout.addWidget(self.min_rating_input)
        rating_layout.addWidget(self.max_rating_input)
        return rating_layout

    def create_themes_filter(self):
        themes_layout = QHBoxLayout()
        themes_label = QLabel("Themes:")
        self.themes_combo = QComboBox()

        # Extract unique themes
        all_themes = set()
        for themes_str in self.puzzle_data.get('Themes', []):
            all_themes.update(themes_str.split())

        self.themes_combo.addItem("All Themes")
        self.themes_combo.addItems(sorted(all_themes))

        themes_layout.addWidget(themes_label)
        themes_layout.addWidget(self.themes_combo)
        return themes_layout

    def reset_filters(self):
        self.min_rating_input.setValue(0)
        self.max_rating_input.setValue(3000)
        self.themes_combo.setCurrentIndex(0)
        self.puzzle_display.clear()
        self.current_puzzle = None

    def select_random_puzzle(self):
        # Copy of data to filter
        filtered_puzzles = self.puzzle_data.copy()

        # Apply rating filter
        min_rating = self.min_rating_input.value()
        max_rating = self.max_rating_input.value()
        filtered_puzzles = filtered_puzzles[
            (filtered_puzzles['Rating'] >= min_rating) &
            (filtered_puzzles['Rating'] <= max_rating)
            ]

        # Apply theme filter
        selected_theme = self.themes_combo.currentText()
        if selected_theme != "All Themes":
            filtered_puzzles = filtered_puzzles[
                filtered_puzzles['Themes'].str.contains(selected_theme)
            ]

        # Display random puzzle or warning
        if not filtered_puzzles.empty:
            self.current_puzzle = filtered_puzzles.sample(1).iloc[0].to_dict()
            display_text = (
                f"<b>Puzzle ID:</b> {self.current_puzzle['PuzzleId']}<br>"
                f"<b>FEN:</b> {self.current_puzzle['FEN']}<br>"
                f"<b>Rating:</b> {self.current_puzzle['Rating']}<br>"
                f"<b>Themes:</b> {self.current_puzzle['Themes']}<br>"
                f"<b>Game URL:</b> {self.current_puzzle['GameUrl']}"
            )
            self.puzzle_display.setText(display_text)
            print(self.current_puzzle['Moves'])
        else:
            QMessageBox.warning(self, "No Puzzles", "No puzzles match the selected criteria.")
