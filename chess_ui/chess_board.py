import time

import chess
import chess.pgn
import chess.svg
from PyQt6.QtCore import QRectF, QSize
from PyQt6.QtGui import QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QWidget

class ChessBoard(QWidget):
    def __init__(self, parent):
        from chess_ui.chess_gui import ChessGUI

        super().__init__(parent)
        self.blunder = None
        self.board = chess.Board()
        self.selected_square = None
        self.possible_moves = []
        self.parent: ChessGUI = parent
        self.previous_fen = self.board.fen()

        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().verticalPolicy()
        )

        self.svg_renderer = None
        self.update_board()

    def paintEvent(self, event):
        if not self.svg_renderer:
            return

        painter = QPainter(self)
        widget_width = self.width()
        widget_height = self.height()
        board_size = min(widget_width, widget_height)

        # Calculate offset to center the board
        x_offset = (widget_width - board_size) // 2
        y_offset = (widget_height - board_size) // 2

        self.svg_renderer.render(painter, QRectF(x_offset, y_offset, board_size, board_size))
        painter.end()

    def update_board(self):
        """Update the board visualization"""
        # Generate board SVG with possible move highlighting
        highlight_squares = [*self.possible_moves]
        if self.selected_square is not None:
            highlight_squares.append(self.selected_square)

        fill_dic = dict.fromkeys(highlight_squares, '#f0c1dcad')

        # blunder needs to be highlighted
        if self.blunder:
            blunder_move = chess.Move.from_uci(self.blunder)
            fill_dic[blunder_move.from_square] = '#fc002696'
            fill_dic[blunder_move.to_square] = '#fc002696'

        board_svg = chess.svg.board(
            board=self.board,
            size=600,
            coordinates=True,
            fill=fill_dic,
            lastmove=None if not self.board.move_stack else self.board.peek(),
            orientation=chess.WHITE
        )

        self.svg_renderer = QSvgRenderer(bytes(board_svg, encoding='utf-8'))
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse clicks on the board"""
        # Calculate board dimensions
        widget_width = self.width()
        widget_height = self.height()
        board_size = min(widget_width, widget_height)

        # Calculate square size
        square_size = board_size // 8

        # Calculate offsets
        x_offset = (widget_width - board_size) // 2
        y_offset = (widget_height - board_size) // 2

        # Get mouse click coordinates relative to board
        x = event.position().x() - x_offset
        y = event.position().y() - y_offset

        # Ensure click is within board
        if x < 0 or x >= board_size or y < 0 or y >= board_size:
            return

        # Convert pixel coordinates to chess square
        file = int(x // square_size)
        rank = 7 - int(y // square_size)

        # Convert to chess square notation
        square = chess.square(file, rank)

        # If no piece is currently selected
        if self.selected_square is None:
            # Check if a piece of the current player is on this square
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                # Find possible moves for this piece
                self.possible_moves = [
                    move.to_square for move in self.board.legal_moves
                    if move.from_square == square
                ]
                self.update_board()
        else:
            try:
                move = chess.Move(self.selected_square, square)
                if not self.try_move(move):
                    # Reset selection if invalid move
                    self.selected_square = None
                    self.possible_moves = []
                    self.update_board()
            except Exception as e:
                print(f"Move error: {e}")
                self.selected_square = None
                self.possible_moves = []
                self.update_board()

    def move(self, move) -> bool:
        if move and move in self.board.legal_moves:
            self.previous_fen = self.board.fen()
            # Perform the move
            self.board.push(move)
            # Reset selection and possible moves
            self.selected_square = None
            self.possible_moves = []
            self.update_board()
            # Signal move made to parent
            self.parent.update_move_list(move)
            return True
        return False

    def try_move(self, move) -> bool:
        if self.parent.mode == "puzzle":
            if not self.parent.puzzle_moves:
                self.parent.chat_box.chat_display.append(f"<b>MAGNUS:</b> Puzzle solved!")
                return False

            if self.board.turn == self.parent.puzzle_turn:
                if move.uci() == self.parent.puzzle_moves[0]:
                    self.parent.puzzle_moves.pop(0)
                else:
                    self.parent.chat_box.chat_display.append(f"<b>MAGNUS:</b> Incorrect move. Try again.")
                    return False

        if self.move(move):
            if self.parent.mode == "bot" and not self.board.is_game_over() and self.board.turn == chess.BLACK:
                time.sleep(0.5)
                self.parent.coach.stockfish.set_fen_position(self.board.fen())
                best_move = self.parent.coach.stockfish.get_best_move()
                self.move(chess.Move.from_uci(best_move))
            elif self.parent.mode == "puzzle":
                if not self.parent.puzzle_moves:
                    self.parent.chat_box.chat_display.append(f"<b>MAGNUS:</b> Puzzle solved!")
                else:
                    time.sleep(0.5)
                    best_move = self.parent.puzzle_moves[0]
                    self.parent.puzzle_moves.pop(0)
                    self.move(chess.Move.from_uci(best_move))
                    if not self.parent.puzzle_moves:
                        self.parent.chat_box.chat_display.append(f"<b>MAGNUS:</b> Puzzle solved!")
            return True
        return False

    def sizeHint(self):
        return QSize(600, 600)

    def minimumSizeHint(self):
        return QSize(400, 400)
