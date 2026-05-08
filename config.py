import os
import pygame

PADDING = 70
BOARD_SIZE = 720
INFO_HEIGHT = 70
HISTORY_WIDTH = 300
DIFFICULTY_LEVELS = [
    ("Fácil",         0.5),
    ("Médio",         2.0),
    ("Difícil",       6.0),
    ("Muito Difícil", 15.0),
]
DEFAULT_TIME_LIMIT = 2.0
TIME_CONTROLS = [("∞", None), ("1'", 60), ("3'", 180), ("5'", 300), ("10'", 600)]
SAVES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")

MENU_WIDTH, MENU_HEIGHT = 700, 700
GAME_WIDTH  = BOARD_SIZE + HISTORY_WIDTH + PADDING
GAME_HEIGHT = BOARD_SIZE + INFO_HEIGHT + PADDING

ROWS, COLS   = 8, 8
SQUARE_SIZE  = BOARD_SIZE // COLS

COLOR_LIGHT        = (238, 238, 210)
COLOR_DARK         = (118, 150, 86)
COLOR_PIECE_BLACK  = (0, 0, 0)
COLOR_HIGHLIGHT    = (255, 255, 51, 150)
COLOR_LAST_MOVE    = (205, 170, 0, 100)
COLOR_MOVE_HINT    = (170, 170, 170, 150)
COLOR_CAPTURE_HINT = (255, 0, 0, 150)
COLOR_CHECK_HINT   = (255, 0, 0, 100)
COLOR_MENU_TEXT    = (255, 255, 255)
COLOR_MENU_BG      = (49, 46, 43)
COLOR_COORD        = (200, 200, 200)

PIECE_SYMBOLS = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
}
ANIM_DURATION = 0.15

BOARD_RECT         = pygame.Rect(PADDING, INFO_HEIGHT, BOARD_SIZE, BOARD_SIZE)
ACTION_PANEL_HEIGHT = 140
HISTORY_RECT       = pygame.Rect(BOARD_RECT.right, INFO_HEIGHT, HISTORY_WIDTH,
                                  GAME_HEIGHT - INFO_HEIGHT - ACTION_PANEL_HEIGHT)
ACTION_PANEL_RECT  = pygame.Rect(BOARD_RECT.right, HISTORY_RECT.bottom,
                                  HISTORY_WIDTH, ACTION_PANEL_HEIGHT)
_PAUSE_BTN_SIZE    = 48
PAUSE_BTN          = pygame.Rect(BOARD_RECT.centerx - _PAUSE_BTN_SIZE // 2,
                                  (INFO_HEIGHT - _PAUSE_BTN_SIZE) // 2,
                                  _PAUSE_BTN_SIZE, _PAUSE_BTN_SIZE)


def format_clock(seconds):
    if seconds is None:
        return "∞"
    m, s = divmod(max(0, int(seconds)), 60)
    return f"{m}:{s:02d}"
