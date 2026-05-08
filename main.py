import pygame
import chess
import chess.pgn
import chess.polyglot
import sys
import math
import random
import threading
import time
import os
import datetime
import array

# --- Configurações e Constantes ---
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

def format_clock(seconds):
    if seconds is None: return "∞"
    m, s = divmod(max(0, int(seconds)), 60)
    return f"{m}:{s:02d}"

def export_pgn(board, game_mode, player_color, clock_config):
    os.makedirs(SAVES_DIR, exist_ok=True)
    game = chess.pgn.Game()
    node = game
    for move in board.move_stack:
        node = node.add_main_variation(move)
    white_name = "Jogador" if (game_mode == "PvP" or player_color == chess.WHITE) else "IA"
    black_name = "Jogador" if (game_mode == "PvP" or player_color == chess.BLACK) else "IA"
    game.headers["Event"] = "Chess-AI"
    game.headers["Site"] = "Local"
    game.headers["Date"] = datetime.date.today().strftime("%Y.%m.%d")
    game.headers["White"] = white_name
    game.headers["Black"] = black_name
    game.headers["Result"] = board.result() if board.is_game_over() else "*"
    if clock_config:
        game.headers["TimeControl"] = str(clock_config)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"partida_{timestamp}.pgn"
    filepath = os.path.join(SAVES_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        print(game, file=f, end="\n\n")
    return filepath, filename

def list_saves():
    if not os.path.isdir(SAVES_DIR):
        return []
    files = [f for f in os.listdir(SAVES_DIR) if f.endswith(".pgn")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(SAVES_DIR, f)), reverse=True)
    return files[:10]

def import_pgn(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            game = chess.pgn.read_game(f)
        if game is None:
            return None
        board = chess.Board()
        history_san = []
        for move in game.mainline_moves():
            history_san.append(board.san(move))
            board.push(move)
        return board, history_san, dict(game.headers)
    except Exception:
        return None

# Dimensões de tela separadas para Menu e Jogo
MENU_WIDTH, MENU_HEIGHT = 700, 700
GAME_WIDTH = BOARD_SIZE + HISTORY_WIDTH + PADDING
GAME_HEIGHT = BOARD_SIZE + INFO_HEIGHT + PADDING

ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_SIZE // COLS

# Cores
COLOR_LIGHT = (238, 238, 210); COLOR_DARK = (118, 150, 86); COLOR_PIECE_BLACK = (0, 0, 0)
COLOR_HIGHLIGHT = (255, 255, 51, 150); COLOR_MOVE_HINT = (170, 170, 170, 150)
COLOR_CAPTURE_HINT = (255, 0, 0, 150); COLOR_CHECK_HINT = (255, 0, 0, 100)
COLOR_MENU_TEXT = (255, 255, 255); COLOR_MENU_BG = (49, 46, 43); COLOR_COORD = (200, 200, 200)

PIECE_SYMBOLS = {'P':'♙','R':'♖','N':'♘','B':'♗','Q':'♕','K':'♔','p':'♟','r':'♜','n':'♞','b':'♝','q':'♛','k':'♚'}
ANIM_DURATION = 0.15

# Áreas da Tela (calculadas dinamicamente quando necessário)
BOARD_RECT = pygame.Rect(PADDING, INFO_HEIGHT, BOARD_SIZE, BOARD_SIZE)
ACTION_PANEL_HEIGHT = 140
HISTORY_RECT = pygame.Rect(BOARD_RECT.right, INFO_HEIGHT, HISTORY_WIDTH, GAME_HEIGHT - INFO_HEIGHT - ACTION_PANEL_HEIGHT)
ACTION_PANEL_RECT = pygame.Rect(BOARD_RECT.right, HISTORY_RECT.bottom, HISTORY_WIDTH, ACTION_PANEL_HEIGHT)
_PAUSE_BTN_SIZE = 48
PAUSE_BTN = pygame.Rect(BOARD_RECT.centerx - _PAUSE_BTN_SIZE // 2, (INFO_HEIGHT - _PAUSE_BTN_SIZE) // 2, _PAUSE_BTN_SIZE, _PAUSE_BTN_SIZE)

# --- Lógica da IA ---
piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
piece_square_table = {
    chess.PAWN: [0,0,0,0,0,0,0,0, 50,50,50,50,50,50,50,50, 10,10,20,30,30,20,10,10, 5,5,10,25,25,10,5,5, 0,0,0,20,20,0,0,0, 5,-5,-10,0,0,-10,-5,5, 5,10,10,-20,-20,10,10,5, 0,0,0,0,0,0,0,0],
    chess.KNIGHT: [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,0,0,0,-20,-40,-30,0,10,15,15,10,0,-30,-30,5,15,20,20,15,5,-30,-30,0,15,20,20,15,0,-30,-30,5,10,15,15,10,5,-30,-40,-20,0,5,5,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50],
    chess.BISHOP: [-20,-10,-10,-10,-10,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,10,10,5,0,-10,-10,5,5,10,10,5,5,-10,-10,0,10,10,10,10,0,-10,-10,10,10,10,10,10,10,-10,-10,5,0,0,0,0,5,-10,-20,-10,-10,-10,-10,-10,-10,-20],
    chess.ROOK: [0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0],
    chess.QUEEN: [-20,-10,-10,-5,-5,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5, 0,0,5,5,5,5,0,-5,-10,5,5,5,5,5,0,-10,-10,0,5,0,0,0,0,-10,-20,-10,-10,-5,-5,-10,-10,-20],
    chess.KING: [-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10, 20,20,0,0,0,0,20,20, 20,30,10,0,0,10,30,20]
}
# Transposition Table
_TT_EXACT = 0; _TT_LOWERBOUND = 1; _TT_UPPERBOUND = 2
_TT_MAX_SIZE = 1_000_000
_tt = {}

# Livro de Aberturas — sequências em UCI cobrindo as principais aberturas
_OPENING_LINES = [
    # === 1.e4 ===
    # Ruy Lopez
    ["e2e4","e7e5","g1f3","b8c6","f1b5"],
    ["e2e4","e7e5","g1f3","b8c6","f1b5","a7a6","b5a4"],
    ["e2e4","e7e5","g1f3","b8c6","f1b5","a7a6","b5a4","g8f6","e1g1"],
    # Italian Game
    ["e2e4","e7e5","g1f3","b8c6","f1c4"],
    ["e2e4","e7e5","g1f3","b8c6","f1c4","f8c5"],
    ["e2e4","e7e5","g1f3","b8c6","f1c4","g8f6","d2d4"],
    # Petrov Defense
    ["e2e4","e7e5","g1f3","g8f6"],
    ["e2e4","e7e5","g1f3","g8f6","f3e5","d7d6","e5f3"],
    # Four Knights
    ["e2e4","e7e5","g1f3","b8c6","b1c3","g8f6"],
    # King's Gambit
    ["e2e4","e7e5","f2f4"],
    ["e2e4","e7e5","f2f4","e5f4","g1f3"],
    # Sicilian Defense
    ["e2e4","c7c5","g1f3"],
    ["e2e4","c7c5","g1f3","d7d6","d2d4","c5d4","f3d4","g8f6","b1c3"],
    ["e2e4","c7c5","g1f3","b8c6","d2d4","c5d4","f3d4"],
    ["e2e4","c7c5","g1f3","e7e6","d2d4","c5d4","f3d4"],
    ["e2e4","c7c5","c2c3"],
    ["e2e4","c7c5","b1c3"],
    # French Defense
    ["e2e4","e7e6","d2d4","d7d5"],
    ["e2e4","e7e6","d2d4","d7d5","b1c3"],
    ["e2e4","e7e6","d2d4","d7d5","e4e5","c7c5"],
    ["e2e4","e7e6","d2d4","d7d5","b1d2"],
    # Caro-Kann
    ["e2e4","c7c6","d2d4","d7d5"],
    ["e2e4","c7c6","d2d4","d7d5","b1c3","d5e4","c3e4"],
    ["e2e4","c7c6","d2d4","d7d5","e4e5"],
    ["e2e4","c7c6","d2d4","d7d5","e4d5","c6d5","c2c4"],
    # Scandinavian
    ["e2e4","d7d5","e4d5","d8d5","b1c3"],
    # Pirc / Modern
    ["e2e4","d7d6","d2d4","g8f6","b1c3"],
    ["e2e4","g7g6","d2d4","f8g7","b1c3"],
    # === 1.d4 ===
    # Queen's Gambit
    ["d2d4","d7d5","c2c4"],
    ["d2d4","d7d5","c2c4","e7e6","b1c3","g8f6","g1f3"],
    ["d2d4","d7d5","c2c4","c7c6","b1c3","g8f6","g1f3"],
    ["d2d4","d7d5","c2c4","d5c4","g1f3","g8f6"],
    # King's Indian Defense
    ["d2d4","g8f6","c2c4","g7g6","b1c3","f8g7","e2e4"],
    ["d2d4","g8f6","c2c4","g7g6","b1c3","f8g7","e2e4","d7d6","g1f3","e8g8"],
    # Nimzo-Indian
    ["d2d4","g8f6","c2c4","e7e6","b1c3","f8b4"],
    ["d2d4","g8f6","c2c4","e7e6","b1c3","f8b4","d1c2"],
    # Queen's Indian
    ["d2d4","g8f6","c2c4","e7e6","g1f3","b7b6"],
    # Grünfeld Defense
    ["d2d4","g8f6","c2c4","g7g6","b1c3","d7d5"],
    ["d2d4","g8f6","c2c4","g7g6","b1c3","d7d5","c4d5","f6d5","e2e4"],
    # Benoni
    ["d2d4","g8f6","c2c4","c7c5","d4d5","e7e6"],
    # Dutch Defense
    ["d2d4","f7f5"],
    # London System
    ["d2d4","d7d5","g1f3","g8f6","c1f4"],
    ["d2d4","g8f6","g1f3","d7d5","c1f4"],
    ["d2d4","g8f6","g1f3","e7e6","c1f4"],
    # Trompowsky
    ["d2d4","g8f6","c1g5"],
    # === 1.c4 English ===
    ["c2c4","e7e5","b1c3"],
    ["c2c4","g8f6","b1c3"],
    ["c2c4","c7c5","g1f3"],
    # === 1.Nf3 Réti ===
    ["g1f3","d7d5","c2c4"],
    ["g1f3","g8f6","c2c4"],
    ["g1f3","g8f6","g2g3"],
]
def _build_opening_book():
    book = {}
    for line in _OPENING_LINES:
        board = chess.Board()
        for uci in line:
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                break
            if move not in board.legal_moves:
                break
            z = chess.polyglot.zobrist_hash(board)
            if z not in book:
                book[z] = []
            if move not in book[z]:
                book[z].append(move)
            board.push(move)
    return book
_opening_book = _build_opening_book()

def _pawn_structure_bonus(board, color):
    pawns = list(board.pieces(chess.PAWN, color))
    if not pawns:
        return 0.0
    score = 0.0
    pawn_files = [chess.square_file(sq) for sq in pawns]
    file_set = set(pawn_files)
    enemy_pawns = list(board.pieces(chess.PAWN, not color))
    for sq in pawns:
        f = chess.square_file(sq)
        r = chess.square_rank(sq)
        # Doubled pawn penalty
        if pawn_files.count(f) > 1:
            score -= 0.25
        # Isolated pawn penalty
        adj = {f - 1, f + 1} & set(range(8))
        if not adj & file_set:
            score -= 0.20
        # Passed pawn bonus (no enemy pawn on same/adjacent files ahead)
        ranks_ahead = range(r + 1, 8) if color == chess.WHITE else range(0, r)
        block_files = {f - 1, f, f + 1} & set(range(8))
        if not any(
            chess.square_file(esq) in block_files and chess.square_rank(esq) in ranks_ahead
            for esq in enemy_pawns
        ):
            adv = r if color == chess.WHITE else 7 - r
            score += 0.10 + adv * 0.05
    return score

def _king_safety_bonus(board, color):
    king_sq = board.king(color)
    if king_sq is None:
        return 0.0
    # King safety only matters when queens are present (middlegame)
    if not board.pieces(chess.QUEEN, chess.WHITE) and not board.pieces(chess.QUEEN, chess.BLACK):
        return 0.0
    score = 0.0
    kf = chess.square_file(king_sq)
    kr = chess.square_rank(king_sq)
    friendly_pawns = board.pieces(chess.PAWN, color)
    enemy_pawns = board.pieces(chess.PAWN, not color)
    shield_files = [f for f in (kf - 1, kf, kf + 1) if 0 <= f <= 7]
    for f in shield_files:
        r1 = kr + 1 if color == chess.WHITE else kr - 1
        r2 = kr + 2 if color == chess.WHITE else kr - 2
        has_r1 = 0 <= r1 <= 7 and chess.square(f, r1) in friendly_pawns
        has_r2 = 0 <= r2 <= 7 and chess.square(f, r2) in friendly_pawns
        if has_r1:
            score += 0.15   # pawn immediately in front
        elif has_r2:
            score += 0.05   # pawn one rank further back (weaker shield)
        # Open/semi-open file penalty near king
        file_has_friendly = any(chess.square_file(sq) == f for sq in friendly_pawns)
        file_has_enemy = any(chess.square_file(sq) == f for sq in enemy_pawns)
        if not file_has_friendly:
            score -= 0.25 if not file_has_enemy else 0.10
    return score

def evaluate_board(board):
    if board.is_checkmate(): return math.inf if board.turn == chess.BLACK else -math.inf
    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(3): return 0
    if board.is_repetition(2): return 0.3 if board.turn == chess.WHITE else -0.3
    total_value = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            val = piece_values[p.piece_type] + (piece_square_table[p.piece_type][sq if p.color else chess.square_mirror(sq)]/100.0)
            total_value += val if p.color == chess.WHITE else -val
    if board.turn == chess.WHITE:
        white_moves = board.legal_moves.count()
        board.push(chess.Move.null())
        black_moves = board.legal_moves.count()
        board.pop()
    else:
        black_moves = board.legal_moves.count()
        board.push(chess.Move.null())
        white_moves = board.legal_moves.count()
        board.pop()
    total_value += (white_moves - black_moves) * 0.05
    total_value += _pawn_structure_bonus(board, chess.WHITE) - _pawn_structure_bonus(board, chess.BLACK)
    total_value += _king_safety_bonus(board, chess.WHITE) - _king_safety_bonus(board, chess.BLACK)
    return total_value

def order_moves(board, moves):
    def score(move):
        s = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                s += piece_values[victim.piece_type] * 10 - piece_values[attacker.piece_type]
        if move.promotion:
            s += piece_values[move.promotion] * 10
        return s
    return sorted(moves, key=score, reverse=True)

class _SearchTimeout(Exception):
    pass

def quiescence(board, alpha, beta, is_maximizing_player, deadline):
    if time.monotonic() >= deadline:
        raise _SearchTimeout()
    stand_pat = evaluate_board(board)
    if is_maximizing_player:
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        for move in order_moves(board, list(board.legal_moves)):
            if not board.is_capture(move) and not move.promotion:
                continue
            board.push(move)
            score = quiescence(board, alpha, beta, False, deadline)
            board.pop()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha
    else:
        if stand_pat <= alpha:
            return alpha
        beta = min(beta, stand_pat)
        for move in order_moves(board, list(board.legal_moves)):
            if not board.is_capture(move) and not move.promotion:
                continue
            board.push(move)
            score = quiescence(board, alpha, beta, True, deadline)
            board.pop()
            if score <= alpha:
                return alpha
            beta = min(beta, score)
        return beta

def minimax(board, depth, alpha, beta, is_maximizing_player, deadline, tt):
    if time.monotonic() >= deadline:
        raise _SearchTimeout()
    original_alpha, original_beta = alpha, beta
    z = chess.polyglot.zobrist_hash(board)
    entry = tt.get(z)
    tt_move = None
    if entry is not None:
        e_depth, e_val, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == _TT_EXACT:
                return e_val
            elif e_flag == _TT_LOWERBOUND:
                alpha = max(alpha, e_val)
            else:
                beta = min(beta, e_val)
            if alpha >= beta:
                return e_val
    if board.is_game_over():
        return evaluate_board(board)
    if depth == 0:
        return quiescence(board, alpha, beta, is_maximizing_player, deadline)
    legal = list(board.legal_moves)
    if tt_move is not None and tt_move in board.legal_moves:
        moves = [tt_move] + order_moves(board, [m for m in legal if m != tt_move])
    else:
        moves = order_moves(board, legal)
    best_val = -math.inf if is_maximizing_player else math.inf
    best_move_found = None
    if is_maximizing_player:
        for move in moves:
            board.push(move)
            val = minimax(board, depth - 1, alpha, beta, False, deadline, tt)
            board.pop()
            if val > best_val:
                best_val = val; best_move_found = move
            alpha = max(alpha, val)
            if beta <= alpha:
                break
    else:
        for move in moves:
            board.push(move)
            val = minimax(board, depth - 1, alpha, beta, True, deadline, tt)
            board.pop()
            if val < best_val:
                best_val = val; best_move_found = move
            beta = min(beta, val)
            if beta <= alpha:
                break
    if len(tt) < _TT_MAX_SIZE:
        flag = _TT_EXACT if original_alpha < best_val < original_beta else (_TT_LOWERBOUND if best_val >= original_beta else _TT_UPPERBOUND)
        tt[z] = (depth, best_val, flag, best_move_found)
    return best_val

def find_best_ai_move(board, time_limit=DEFAULT_TIME_LIMIT):
    book_moves = [m for m in _opening_book.get(chess.polyglot.zobrist_hash(board), []) if m in board.legal_moves]
    if book_moves:
        return random.choice(book_moves)
    deadline = time.monotonic() + time_limit
    is_white_turn = board.turn == chess.WHITE
    initial_stack_size = len(board.move_stack)
    all_legal = list(board.legal_moves)
    if not all_legal:
        return None
    best_move = order_moves(board, all_legal)[0]
    for depth in range(1, 20):
        if time.monotonic() >= deadline:
            break
        entry = _tt.get(chess.polyglot.zobrist_hash(board))
        tt_root_move = entry[3] if entry else None
        if tt_root_move is not None and tt_root_move in board.legal_moves:
            legal = [tt_root_move] + order_moves(board, [m for m in all_legal if m != tt_root_move])
        else:
            legal = order_moves(board, all_legal)
        candidate_move = None
        best_value = -math.inf if is_white_turn else math.inf
        best_moves = []
        try:
            for move in legal:
                board.push(move)
                board_value = minimax(board, depth - 1, -math.inf, math.inf, board.turn == chess.WHITE, deadline, _tt)
                board.pop()
                if is_white_turn:
                    if board_value > best_value:
                        best_value = board_value; best_moves = [move]
                    elif board_value == best_value:
                        best_moves.append(move)
                else:
                    if board_value < best_value:
                        best_value = board_value; best_moves = [move]
                    elif board_value == best_value:
                        best_moves.append(move)
            if best_moves:
                candidate_move = random.choice(best_moves)
        except _SearchTimeout:
            while len(board.move_stack) > initial_stack_size:
                board.pop()
        if candidate_move:
            best_move = candidate_move
    return best_move

# --- Funções de Desenho e Lógica ---
def draw_text(screen, text, font, color, rect, align="left"):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(centery=rect.centery)
    if align == "left":
        text_rect.left = rect.left
    elif align == "center":
        text_rect.centerx = rect.centerx
    elif align == "right":
        text_rect.right = rect.right
    screen.blit(text_surface, text_rect)
def get_drawing_coords(square_index, perspective):
    row, col = 7 - (square_index // 8), square_index % 8
    if perspective == chess.BLACK:
        return 7 - row, 7 - col
    return row, col
def draw_board(screen):
    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(screen, COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK, (BOARD_RECT.left + c * SQUARE_SIZE, BOARD_RECT.top + r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
def draw_coordinates(screen, font, perspective):
    files, ranks = "abcdefgh", "12345678"
    if perspective == chess.BLACK:
        files = files[::-1]
        ranks = ranks[::-1]
    for i in range(8):
        file_text = font.render(files[i], True, COLOR_COORD)
        screen.blit(file_text, (BOARD_RECT.left + i*SQUARE_SIZE + (SQUARE_SIZE - file_text.get_width())//2, BOARD_RECT.bottom + 5))
        screen.blit(file_text, (BOARD_RECT.left + i*SQUARE_SIZE + (SQUARE_SIZE - file_text.get_width())//2, BOARD_RECT.top - PADDING//2 - file_text.get_height()//2))
        rank_text = font.render(ranks[i], True, COLOR_COORD)
        screen.blit(rank_text, (BOARD_RECT.left - PADDING//2 - rank_text.get_width()//2, BOARD_RECT.bottom - (i+1)*SQUARE_SIZE + (SQUARE_SIZE - rank_text.get_height())//2))
        screen.blit(rank_text, (BOARD_RECT.right + 5, BOARD_RECT.bottom - (i+1)*SQUARE_SIZE + (SQUARE_SIZE - rank_text.get_height())//2))
def draw_pieces(screen, board, font, perspective, anim=None):
    skip_sq = anim['to_square'] if anim else -1
    for i in range(64):
        if i == skip_sq:
            continue
        piece = board.piece_at(i)
        if piece:
            row, col = get_drawing_coords(i, perspective)
            symbol = PIECE_SYMBOLS[piece.symbol()]
            text_surface = font.render(symbol, True, COLOR_PIECE_BLACK)
            text_rect = text_surface.get_rect(center=(BOARD_RECT.left + col*SQUARE_SIZE + SQUARE_SIZE//2, BOARD_RECT.top + row*SQUARE_SIZE + SQUARE_SIZE//2))
            screen.blit(text_surface, text_rect)
    if anim:
        t = min(1.0, (time.monotonic() - anim['start']) / anim['duration'])
        t = t * t * (3 - 2 * t)  # smooth-step easing
        fx, fy = anim['from_center']; tx, ty = anim['to_center']
        cx, cy = int(fx + (tx - fx) * t), int(fy + (ty - fy) * t)
        surf = font.render(PIECE_SYMBOLS[anim['piece'].symbol()], True, COLOR_PIECE_BLACK)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))
def draw_visual_aids(screen, board, perspective, selected_square, possible_moves):
    if board.is_check():
        row, col = get_drawing_coords(board.king(board.turn), perspective)
        surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        surface.fill(COLOR_CHECK_HINT)
        screen.blit(surface, (BOARD_RECT.left + col*SQUARE_SIZE, BOARD_RECT.top + row*SQUARE_SIZE))
    if selected_square is not None:
        row, col = get_drawing_coords(selected_square, perspective)
        surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        surface.fill(COLOR_HIGHLIGHT)
        screen.blit(surface, (BOARD_RECT.left + col*SQUARE_SIZE, BOARD_RECT.top + row*SQUARE_SIZE))
    for move in possible_moves:
        row, col = get_drawing_coords(move.to_square, perspective)
        center = (BOARD_RECT.left + col*SQUARE_SIZE + SQUARE_SIZE//2, BOARD_RECT.top + row*SQUARE_SIZE + SQUARE_SIZE//2)
        color = COLOR_CAPTURE_HINT if board.is_capture(move) else COLOR_MOVE_HINT
        radius = SQUARE_SIZE//4 if board.is_capture(move) else SQUARE_SIZE//6
        pygame.draw.circle(screen, color, center, radius)
def get_square_from_mouse(pos, perspective):
    if not BOARD_RECT.collidepoint(pos): return None
    row = (pos[1] - BOARD_RECT.top) // SQUARE_SIZE
    col = (pos[0] - BOARD_RECT.left) // SQUARE_SIZE
    if perspective == chess.BLACK: row, col = 7 - row, 7 - col
    return (7 - row) * 8 + col
def draw_info_panel(screen, font, board, white_time=None, black_time=None, ai_thinking=False):
    pygame.draw.rect(screen, COLOR_MENU_BG, pygame.Rect(0, 0, BOARD_RECT.right, INFO_HEIGHT))
    draw_text(screen, f"Movimento: {board.fullmove_number}", font, COLOR_MENU_TEXT, pygame.Rect(PADDING, 0, 200, INFO_HEIGHT), "left")
    pygame.draw.rect(screen, COLOR_DARK, PAUSE_BTN, border_radius=6)
    bar_w, bar_h = 7, 24; bar_y = PAUSE_BTN.centery - bar_h // 2
    pygame.draw.rect(screen, COLOR_MENU_TEXT, (PAUSE_BTN.centerx - 11, bar_y, bar_w, bar_h))
    pygame.draw.rect(screen, COLOR_MENU_TEXT, (PAUSE_BTN.centerx + 4,  bar_y, bar_w, bar_h))
    if white_time is not None:
        half = INFO_HEIGHT // 2
        for clr, t, sym, row in [(chess.BLACK, black_time, "♟", 0), (chess.WHITE, white_time, "♙", half)]:
            r = pygame.Rect(BOARD_RECT.right - 200, row, 200, half)
            is_active = board.turn == clr and not ai_thinking
            if is_active:
                pygame.draw.rect(screen, (50, 80, 50) if clr == chess.WHITE else (80, 50, 50), r)
            txt_color = (255, 80, 80) if t is not None and t < 30 else COLOR_MENU_TEXT
            draw_text(screen, f"{sym} {format_clock(t)}", font, txt_color, r, "right")
    else:
        turn_text = "IA pensando..." if ai_thinking else ("Vez das Brancas" if board.turn == chess.WHITE else "Vez das Pretas")
        draw_text(screen, turn_text, font, COLOR_MENU_TEXT, pygame.Rect(BOARD_RECT.right - 200, 0, 200, INFO_HEIGHT), "right")
def draw_history_panel(screen, font, history_san, scroll_offset, selected_san_index=None):
    pygame.draw.rect(screen, COLOR_MENU_BG, HISTORY_RECT)
    title_rect = pygame.Rect(HISTORY_RECT.left, 0, HISTORY_RECT.width, INFO_HEIGHT)
    draw_text(screen, "Histórico", font, COLOR_MENU_TEXT, title_rect, "center")
    header_y = INFO_HEIGHT
    num_x = HISTORY_RECT.left + 5
    num_w = 38
    move_col_w = (HISTORY_RECT.width - num_w - 20) // 2
    white_x = num_x + num_w + 5
    black_x = white_x + move_col_w + 5
    white_header_rect = pygame.Rect(white_x, header_y, move_col_w, 32)
    black_header_rect = pygame.Rect(black_x, header_y, move_col_w, 32)
    draw_text(screen, "Brancas", font, COLOR_MENU_TEXT, white_header_rect, "left")
    draw_text(screen, "Pretas", font, COLOR_MENU_TEXT, black_header_rect, "left")
    y_offset = header_y + 32
    line_height = 28
    start_index = scroll_offset * 2
    move_number = (start_index // 2) + 1
    for i in range(start_index, len(history_san), 2):
        if y_offset + line_height > HISTORY_RECT.bottom: break
        white_move = history_san[i]; black_move = ""
        if i + 1 < len(history_san): black_move = history_san[i+1]
        num_r   = pygame.Rect(num_x,   y_offset, num_w,      line_height)
        white_r = pygame.Rect(white_x, y_offset, move_col_w, line_height)
        black_r = pygame.Rect(black_x, y_offset, move_col_w, line_height)
        if selected_san_index == i:
            pygame.draw.rect(screen, (70, 70, 120), white_r)
        elif selected_san_index == i + 1 and black_move:
            pygame.draw.rect(screen, (70, 70, 120), black_r)
        draw_text(screen, f"{move_number}.", font, COLOR_MENU_TEXT, num_r, "left")
        draw_text(screen, white_move, font, COLOR_MENU_TEXT, white_r, "left")
        draw_text(screen, black_move, font, COLOR_MENU_TEXT, black_r, "left")
        y_offset += line_height; move_number += 1
def draw_game_over_popup(screen, font_main, font_sub, message, btn_see, btn_again):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA); overlay.fill((0,0,0,180)); screen.blit(overlay,(0,0))
    pop_w, pop_h = 500, 250; pop_r = pygame.Rect((screen.get_width()-pop_w)//2, (screen.get_height()-pop_h)//2, pop_w, pop_h)
    pygame.draw.rect(screen, COLOR_MENU_BG, pop_r); pygame.draw.rect(screen, COLOR_MENU_TEXT, pop_r, 2)
    messages = message.split('\n'); main_msg = messages[0]; sub_msg = messages[1] if len(messages)>1 else ""
    msg_r = pygame.Rect(pop_r.x, pop_r.y, pop_r.width, pop_r.height * 0.4); draw_text(screen, main_msg, font_main, COLOR_MENU_TEXT, msg_r, "center")
    sub_r = pygame.Rect(pop_r.x, pop_r.y + 45, pop_r.width, pop_r.height * 0.4); draw_text(screen, sub_msg, font_sub, COLOR_COORD, sub_r, "center")
    pygame.draw.rect(screen, COLOR_DARK, btn_see); draw_text(screen, "Ver Tabuleiro", font_sub, COLOR_MENU_TEXT, btn_see, "center")
    pygame.draw.rect(screen, COLOR_DARK, btn_again); draw_text(screen, "Ir para o Menu", font_sub, COLOR_MENU_TEXT, btn_again, "center")
def draw_pause_menu(screen, font_title, font_btn, page="main", current_time_limit=DEFAULT_TIME_LIMIT):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    pop_w, pop_h = 480, 440
    pop_r = pygame.Rect((screen.get_width()-pop_w)//2, (screen.get_height()-pop_h)//2, pop_w, pop_h)
    pygame.draw.rect(screen, COLOR_MENU_BG, pop_r)
    pygame.draw.rect(screen, COLOR_MENU_TEXT, pop_r, 2)
    btn_w, btn_h, btn_gap = 400, 50, 12
    btn_x = pop_r.x + (pop_w - btn_w) // 2
    if page == "difficulty":
        title_r = pygame.Rect(pop_r.x, pop_r.y + 10, pop_r.width, 50)
        draw_text(screen, "Dificuldade", font_title, COLOR_MENU_TEXT, title_r, "center")
        btn_y0 = pop_r.y + 70
        btns = []
        for i, (label, tlimit) in enumerate(DIFFICULTY_LEVELS):
            btn = pygame.Rect(btn_x, btn_y0 + i*(btn_h+btn_gap), btn_w, btn_h)
            btns.append(btn)
            is_active = tlimit == current_time_limit
            bg = (180, 130, 40) if is_active else COLOR_DARK
            fg = COLOR_MENU_TEXT
            pygame.draw.rect(screen, bg, btn)
            if is_active:
                pygame.draw.rect(screen, COLOR_MENU_TEXT, btn, 2)
            draw_text(screen, label, font_btn, fg, btn, "center")
        back_btn = pygame.Rect(btn_x, btn_y0 + len(DIFFICULTY_LEVELS)*(btn_h+btn_gap), btn_w, btn_h)
        pygame.draw.rect(screen, COLOR_MENU_BG, back_btn, 2)
        draw_text(screen, "Voltar", font_btn, COLOR_MENU_TEXT, back_btn, "center")
        return btns, back_btn
    else:
        title_r = pygame.Rect(pop_r.x, pop_r.y + 10, pop_r.width, 50)
        draw_text(screen, "Pausa", font_title, COLOR_MENU_TEXT, title_r, "center")
        btn_y0 = pop_r.y + 80
        entries = [
            ("Retornar à Partida",      COLOR_DARK, COLOR_MENU_TEXT),
            ("Reiniciar Partida",        COLOR_DARK, COLOR_MENU_TEXT),
            ("Mudar Dificuldade",        COLOR_DARK, COLOR_MENU_TEXT),
            ("Exportar PGN",             COLOR_DARK, COLOR_MENU_TEXT),
            ("Voltar ao Menu Principal", COLOR_DARK, COLOR_MENU_TEXT),
        ]
        btns = []
        for i, (label, bg, fg) in enumerate(entries):
            btn = pygame.Rect(btn_x, btn_y0 + i*(btn_h+btn_gap), btn_w, btn_h)
            btns.append(btn)
            pygame.draw.rect(screen, bg, btn)
            draw_text(screen, label, font_btn, fg, btn, "center")
        return btns, None

def draw_promotion_popup(screen, font_pieces, to_sq, promoting_color, perspective):
    pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    draw_row, draw_col = get_drawing_coords(to_sq, perspective)
    x = BOARD_RECT.left + draw_col * SQUARE_SIZE
    step = 1 if draw_row == 0 else -1
    btns = []
    for i, pt in enumerate(pieces):
        y = BOARD_RECT.top + (draw_row + i * step) * SQUARE_SIZE
        btn = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(screen, COLOR_LIGHT, btn)
        pygame.draw.rect(screen, COLOR_PIECE_BLACK, btn, 3)
        sym = PIECE_SYMBOLS[chess.Piece(pt, promoting_color).symbol()]
        surf = font_pieces.render(sym, True, COLOR_PIECE_BLACK)
        screen.blit(surf, surf.get_rect(center=btn.center))
        btns.append((btn, pt))
    return btns

def draw_action_panel(screen, font):
    pygame.draw.rect(screen, COLOR_MENU_BG, ACTION_PANEL_RECT)
    action_btn_w, action_btn_h = ACTION_PANEL_RECT.width-20, 45; action_btn_x = ACTION_PANEL_RECT.left+10
    undo_button = pygame.Rect(action_btn_x, ACTION_PANEL_RECT.top + 10, action_btn_w, action_btn_h)
    reset_button = pygame.Rect(action_btn_x, undo_button.bottom + 10, action_btn_w, action_btn_h)
    pygame.draw.rect(screen, COLOR_DARK, undo_button); draw_text(screen, "Voltar Jogada", font, COLOR_MENU_TEXT, undo_button, "center")
    pygame.draw.rect(screen, COLOR_DARK, reset_button); draw_text(screen, "Reiniciar Jogo", font, COLOR_MENU_TEXT, reset_button, "center")
    return undo_button, reset_button

def _gen_sine(freq, ms, vol=0.3, decay=20.0, sample_rate=44100):
    n = int(sample_rate * ms / 1000)
    attack = int(sample_rate * 0.005)
    buf = array.array('h', [0] * n)
    for i in range(n):
        t = i / sample_rate
        env = math.exp(-decay * t) * min(1.0, i / max(1, attack))
        buf[i] = int(32767 * vol * env * math.sin(2 * math.pi * freq * t))
    return buf

def _make_sounds():
    sr = 44100
    gap = array.array('h', [0] * int(sr * 0.055))
    sounds = {}
    sounds['move']     = pygame.mixer.Sound(buffer=_gen_sine(800,  50, vol=0.30, decay=28))
    sounds['capture']  = pygame.mixer.Sound(buffer=_gen_sine(350,  80, vol=0.50, decay=18))
    sounds['check']    = pygame.mixer.Sound(buffer=_gen_sine(1047,120, vol=0.40, decay=12))
    sounds['game_end'] = pygame.mixer.Sound(buffer=_gen_sine(523, 130, vol=0.35, decay=10) + gap +
                                                    _gen_sine(415, 130, vol=0.35, decay=10) + gap +
                                                    _gen_sine(311, 220, vol=0.35, decay=7))
    return sounds

def make_anim(from_sq, to_sq, piece, perspective, flip_perspective=None):
    fr, fc = get_drawing_coords(from_sq, perspective)
    tr, tc = get_drawing_coords(to_sq, perspective)
    return {
        'piece': piece,
        'from_center': (BOARD_RECT.left + fc*SQUARE_SIZE + SQUARE_SIZE//2, BOARD_RECT.top + fr*SQUARE_SIZE + SQUARE_SIZE//2),
        'to_center':   (BOARD_RECT.left + tc*SQUARE_SIZE + SQUARE_SIZE//2, BOARD_RECT.top + tr*SQUARE_SIZE + SQUARE_SIZE//2),
        'to_square': to_sq,
        'start': time.monotonic(),
        'duration': ANIM_DURATION,
        'flip_perspective': flip_perspective,
    }

def _board_at(full_board, n):
    """Reconstruct board state after n half-moves from full_board.move_stack."""
    b = chess.Board()
    for m in list(full_board.move_stack)[:n]:
        b.push(m)
    return b

def main():
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init(); pygame.font.init()
    try:
        sounds = _make_sounds()
    except Exception:
        sounds = {}
    screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
    pygame.display.set_caption("Xadrez em Python")
    _font_path = (pygame.font.match_font('dejavusans') or
                  pygame.font.match_font('notosanssymbols2') or
                  pygame.font.match_font('notosanssymbols'))
    def load_font(size):
        if _font_path:
            return pygame.font.Font(_font_path, size)
        return pygame.font.Font(None, size)
    font_pieces = load_font(int(SQUARE_SIZE*0.75))
    font_ui = load_font(20)
    font_coords = load_font(16)
    font_popup = load_font(36)
    font_popup_sub = load_font(22)
    
    ai_move_to_make = None
    ai_thread = None
    ai_result = [None]

    state_vars = {}
    def reset_game():
        nonlocal screen, ai_move_to_make, ai_thread, ai_result
        screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
        ai_move_to_make = None
        ai_thread = None
        ai_result = [None]
        _clock = state_vars.get('clock_config')
        state_vars.update({'board':chess.Board(), 'game_state':"MENU", 'game_mode':None, 'player_color':None, 'perspective':chess.WHITE, 'selected_square':None, 'possible_moves':[], 'game_over_message':"", 'move_history_san':[], 'history_scroll_offset': 0, 'time_limit': state_vars.get('time_limit', DEFAULT_TIME_LIMIT), 'pause_page': "main", 'pending_promotion': None, 'clock_config': _clock, 'white_time': None, 'black_time': None, 'last_tick': None, 'toast_message': None, 'toast_until': 0.0, 'save_files': [], 'anim': None, 'analysis_index': None})
    reset_game()

    def draw_game_screen():
        screen.fill(COLOR_MENU_BG)
        _aidx = state_vars.get('analysis_index')
        _disp = _board_at(state_vars['board'], _aidx) if _aidx is not None else state_vars['board']
        draw_board(screen)
        draw_coordinates(screen, font_coords, state_vars['perspective'])
        draw_visual_aids(screen, _disp, state_vars['perspective'],
                         None if _aidx is not None else state_vars['selected_square'],
                         [] if _aidx is not None else state_vars['possible_moves'])
        draw_pieces(screen, _disp, font_pieces, state_vars['perspective'],
                    None if _aidx is not None else state_vars.get('anim'))
        thinking = ai_thread is not None and ai_thread.is_alive()
        draw_info_panel(screen, font_ui, _disp, state_vars.get('white_time'), state_vars.get('black_time'), thinking)
        _sel_san = (_aidx - 1) if _aidx is not None and _aidx > 0 else None
        draw_history_panel(screen, font_ui, state_vars['move_history_san'], state_vars['history_scroll_offset'], _sel_san)
        return draw_action_panel(screen, font_ui)

    running = True
    while running:
        current_state = state_vars['game_state']
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F5:
                    screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
                    state_vars['game_state'] = "REVISAO"
                elif e.key == pygame.K_ESCAPE:
                    if current_state == "JOGANDO":
                        state_vars['game_state'] = "PAUSE"; state_vars['pause_page'] = "main"; state_vars['last_tick'] = None
                    elif current_state == "PAUSE":
                        if state_vars.get('pause_page') == "difficulty":
                            state_vars['pause_page'] = "main"
                        else:
                            state_vars['game_state'] = "JOGANDO"
                    elif current_state == "PROMOCAO":
                        state_vars['pending_promotion'] = None
                        state_vars['game_state'] = "JOGANDO"
                    elif current_state == "CARREGAR":
                        state_vars['game_state'] = "MENU"
                    elif current_state == "REVISAO":
                        state_vars['analysis_index'] = None
                if e.key in (pygame.K_LEFT, pygame.K_RIGHT) and current_state == "REVISAO":
                    _hist_len = len(state_vars['move_history_san'])
                    _aidx = state_vars.get('analysis_index')
                    if _aidx is None:
                        _aidx = _hist_len
                    _new = max(0, _aidx - 1) if e.key == pygame.K_LEFT else min(_hist_len, _aidx + 1)
                    state_vars['analysis_index'] = _new
                    if _new > 0:
                        _sel_row = (_new - 1) // 2
                        _max_scroll = max(0, (_hist_len + 1) // 2 - 15)
                        _cs = state_vars['history_scroll_offset']
                        if _sel_row < _cs:
                            state_vars['history_scroll_offset'] = max(0, _sel_row)
                        elif _sel_row >= _cs + 15:
                            state_vars['history_scroll_offset'] = min(_max_scroll, _sel_row - 14)
            if e.type == pygame.MOUSEWHEEL and current_state in ["JOGANDO", "REVISAO"]:
                if HISTORY_RECT.collidepoint(pygame.mouse.get_pos()):
                    state_vars['history_scroll_offset'] -= e.y
                    max_scroll = max(0, (len(state_vars['move_history_san'])+1)//2 - 15)
                    state_vars['history_scroll_offset'] = max(0, min(state_vars['history_scroll_offset'], max_scroll))
            if e.type == pygame.MOUSEBUTTONDOWN:
                if current_state == "MENU":
                    btn_w,btn_h=400,60; menu_btn_x=(MENU_WIDTH-btn_w)//2
                    white_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.3,btn_w,btn_h); black_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.5,btn_w,btn_h); pvp_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.7,btn_w,btn_h)
                    tc_btn_w,tc_btn_h=110,40; tc_total=len(TIME_CONTROLS)*(tc_btn_w+8)-8; tc_x0=(MENU_WIDTH-tc_total)//2; tc_y=642
                    tc_clicked=False
                    for i,(_,secs) in enumerate(TIME_CONTROLS):
                        if pygame.Rect(tc_x0+i*(tc_btn_w+8),tc_y,tc_btn_w,tc_btn_h).collidepoint(e.pos):
                            state_vars['clock_config']=secs; tc_clicked=True; break
                    load_btn=pygame.Rect(menu_btn_x,558,btn_w,40); load_clicked=False
                    if not tc_clicked and load_btn.collidepoint(e.pos):
                        saves=list_saves()
                        if saves: state_vars['save_files']=saves; state_vars['game_state']="CARREGAR"
                        load_clicked=True
                    if not tc_clicked and not load_clicked and (white_btn.collidepoint(e.pos) or black_btn.collidepoint(e.pos) or pvp_btn.collidepoint(e.pos)):
                        _clock=state_vars.get('clock_config'); _t=float(_clock) if _clock else None
                        screen=pygame.display.set_mode((GAME_WIDTH,GAME_HEIGHT))
                        if white_btn.collidepoint(e.pos): state_vars.update(game_mode="IA",player_color=chess.WHITE,perspective=chess.WHITE,game_state="JOGANDO",white_time=_t,black_time=_t,last_tick=None)
                        elif black_btn.collidepoint(e.pos): state_vars.update(game_mode="IA",player_color=chess.BLACK,perspective=chess.BLACK,game_state="JOGANDO",white_time=_t,black_time=_t,last_tick=None)
                        elif pvp_btn.collidepoint(e.pos): state_vars.update(game_mode="PvP",perspective=chess.WHITE,game_state="JOGANDO",white_time=_t,black_time=_t,last_tick=None)
                elif current_state == "JOGANDO":
                    if PAUSE_BTN.collidepoint(e.pos):
                        state_vars['game_state'] = "PAUSE"; state_vars['pause_page'] = "main"; state_vars['last_tick'] = None
                        continue
                    is_human_turn=(state_vars['game_mode']=="PvP")or(state_vars['game_mode']=="IA" and state_vars['board'].turn==state_vars['player_color'])
                    if is_human_turn:
                        undo_button, reset_button = draw_action_panel(screen, font_ui)
                        if undo_button.collidepoint(e.pos):
                            state_vars['anim'] = None
                            if len(state_vars['move_history_san'])>0: state_vars['board'].pop(); state_vars['move_history_san'].pop()
                            if state_vars['game_mode']=="IA" and len(state_vars['move_history_san'])>0: state_vars['board'].pop(); state_vars['move_history_san'].pop()
                        elif reset_button.collidepoint(e.pos): reset_game(); continue
                        else:
                            sq=get_square_from_mouse(e.pos,state_vars['perspective'])
                            if sq is not None:
                                if state_vars['selected_square'] is None:
                                    p=state_vars['board'].piece_at(sq)
                                    if p and p.color==state_vars['board'].turn: state_vars['selected_square']=sq; state_vars['possible_moves']=[m for m in state_vars['board'].legal_moves if m.from_square==sq]
                                else:
                                    from_sq = state_vars['selected_square']
                                    promo_m = chess.Move(from_sq, sq, promotion=chess.QUEEN)
                                    norm_m  = chess.Move(from_sq, sq)
                                    if promo_m in state_vars['board'].legal_moves:
                                        state_vars['pending_promotion'] = (from_sq, sq)
                                        state_vars['game_state'] = "PROMOCAO"
                                    elif norm_m in state_vars['board'].legal_moves:
                                        _p = state_vars['board'].piece_at(from_sq)
                                        _cap = state_vars['board'].is_capture(norm_m)
                                        state_vars['move_history_san'].append(state_vars['board'].san(norm_m))
                                        state_vars['board'].push(norm_m)
                                        _snd = 'check' if state_vars['board'].is_check() else ('capture' if _cap else 'move')
                                        _s = sounds.get(_snd); _s and _s.play()
                                        _new_persp = state_vars['board'].turn if state_vars['game_mode']=="PvP" else None
                                        state_vars['anim'] = make_anim(from_sq, sq, _p, state_vars['perspective'], _new_persp)
                                    state_vars['selected_square'],state_vars['possible_moves']=None,[]
                elif current_state == "PROMOCAO":
                    if state_vars.get('pending_promotion'):
                        from_sq, to_sq = state_vars['pending_promotion']
                        btns = draw_promotion_popup(screen, font_pieces, to_sq, state_vars['board'].turn, state_vars['perspective'])
                        for btn, pt in btns:
                            if btn.collidepoint(e.pos):
                                m = chess.Move(from_sq, to_sq, promotion=pt)
                                if m in state_vars['board'].legal_moves:
                                    _p = state_vars['board'].piece_at(from_sq)
                                    _cap = state_vars['board'].is_capture(m)
                                    state_vars['move_history_san'].append(state_vars['board'].san(m))
                                    state_vars['board'].push(m)
                                    _snd = 'check' if state_vars['board'].is_check() else ('capture' if _cap else 'move')
                                    _s = sounds.get(_snd); _s and _s.play()
                                    _new_persp = state_vars['board'].turn if state_vars['game_mode']=="PvP" else None
                                    state_vars['anim'] = make_anim(from_sq, to_sq, _p, state_vars['perspective'], _new_persp)
                                state_vars['pending_promotion'] = None
                                state_vars['game_state'] = "JOGANDO"; state_vars['last_tick'] = None
                                break
                elif current_state == "FIM_DE_JOGO":
                    pop_btn_w,pop_btn_h=200,50; pop_btn_y=(GAME_HEIGHT-pop_btn_h)//2+60
                    see_board_btn=pygame.Rect((GAME_WIDTH-pop_btn_w*2-20)//2,pop_btn_y,pop_btn_w,pop_btn_h); again_popup_btn=pygame.Rect(see_board_btn.right+20,pop_btn_y,pop_btn_w,pop_btn_h)
                    if see_board_btn.collidepoint(e.pos): state_vars['game_state']="REVISAO"
                    elif again_popup_btn.collidepoint(e.pos): reset_game()
                elif current_state == "REVISAO":
                    btn_w,btn_h=400,40; _below=GAME_HEIGHT-BOARD_RECT.bottom; again_review_btn=pygame.Rect((BOARD_RECT.width-btn_w)//2+BOARD_RECT.left,BOARD_RECT.bottom+(_below-btn_h)//2,btn_w,btn_h)
                    if again_review_btn.collidepoint(e.pos):
                        reset_game()
                    elif HISTORY_RECT.collidepoint(e.pos):
                        _hist = state_vars['move_history_san']
                        _num_w = 38; _col_w = (HISTORY_RECT.width - _num_w - 20) // 2
                        _wx = HISTORY_RECT.left + 5 + _num_w + 5
                        _bx = _wx + _col_w + 5
                        _ry = e.pos[1] - (INFO_HEIGHT + 32)
                        if _ry >= 0:
                            _row = _ry // 28 + state_vars['history_scroll_offset']
                            _san_i = _row * 2 + (1 if e.pos[0] >= _bx else 0)
                            if _san_i < len(_hist):
                                state_vars['analysis_index'] = _san_i + 1
                                _sel_row = _san_i // 2
                                _max_scroll = max(0, (len(_hist) + 1) // 2 - 15)
                                _cs = state_vars['history_scroll_offset']
                                if _sel_row < _cs:
                                    state_vars['history_scroll_offset'] = max(0, _sel_row)
                                elif _sel_row >= _cs + 15:
                                    state_vars['history_scroll_offset'] = min(_max_scroll, _sel_row - 14)
                elif current_state == "CARREGAR":
                    saves=state_vars.get('save_files',[])
                    _bw2,_bh2,_bx2=500,40,(MENU_WIDTH-500)//2
                    _loaded=False
                    for i,fname in enumerate(saves[:10]):
                        _fb=pygame.Rect(_bx2,100+i*48,_bw2,_bh2)
                        if _fb.collidepoint(e.pos):
                            _result=import_pgn(os.path.join(SAVES_DIR,fname))
                            if _result:
                                _board,_hist,_hdrs=_result
                                screen=pygame.display.set_mode((GAME_WIDTH,GAME_HEIGHT))
                                state_vars.update(board=_board,move_history_san=_hist,game_state="REVISAO",perspective=chess.WHITE)
                                _wh=_hdrs.get("White",""); _bh=_hdrs.get("Black","")
                                if "IA" in _bh: state_vars.update(game_mode="IA",player_color=chess.WHITE)
                                elif "IA" in _wh: state_vars.update(game_mode="IA",player_color=chess.BLACK)
                                else: state_vars['game_mode']="PvP"
                            _loaded=True; break
                    if not _loaded:
                        _back2=pygame.Rect((MENU_WIDTH-200)//2,MENU_HEIGHT-60,200,40)
                        if _back2.collidepoint(e.pos): state_vars['game_state']="MENU"
                elif current_state == "PAUSE":
                    _page = state_vars.get('pause_page', 'main')
                    btns, secondary_btn = draw_pause_menu(screen, font_popup, font_ui, _page, state_vars.get('time_limit', DEFAULT_TIME_LIMIT))
                    if _page == "difficulty":
                        for i, btn in enumerate(btns):
                            if btn.collidepoint(e.pos):
                                _mode = state_vars['game_mode']; _color = state_vars['player_color']; _persp = state_vars['perspective']; _clock=state_vars.get('clock_config'); _t=float(_clock) if _clock else None
                                _tlimit = DIFFICULTY_LEVELS[i][1]
                                reset_game()
                                screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
                                state_vars.update(game_mode=_mode, player_color=_color, perspective=_persp, game_state="JOGANDO", time_limit=_tlimit, white_time=_t, black_time=_t, last_tick=None)
                                break
                        else:
                            if secondary_btn and secondary_btn.collidepoint(e.pos):
                                state_vars['pause_page'] = "main"
                    else:
                        resume_btn, restart_btn, diff_btn, export_btn, menu_btn = btns
                        if resume_btn.collidepoint(e.pos):
                            state_vars['game_state'] = "JOGANDO"
                        elif restart_btn.collidepoint(e.pos):
                            _mode = state_vars['game_mode']; _color = state_vars['player_color']; _persp = state_vars['perspective']; _tlimit = state_vars.get('time_limit', DEFAULT_TIME_LIMIT); _clock=state_vars.get('clock_config'); _t=float(_clock) if _clock else None
                            reset_game()
                            screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
                            state_vars.update(game_mode=_mode, player_color=_color, perspective=_persp, game_state="JOGANDO", time_limit=_tlimit, white_time=_t, black_time=_t, last_tick=None)
                        elif diff_btn.collidepoint(e.pos):
                            state_vars['pause_page'] = "difficulty"
                        elif export_btn.collidepoint(e.pos):
                            _, fname = export_pgn(state_vars['board'], state_vars.get('game_mode'), state_vars.get('player_color'), state_vars.get('clock_config'))
                            state_vars['toast_message'] = f"Salvo: {fname}"
                            state_vars['toast_until'] = time.monotonic() + 3.0
                            state_vars['game_state'] = "JOGANDO"
                        elif menu_btn.collidepoint(e.pos):
                            reset_game()

        if current_state == "JOGANDO" and state_vars.get('white_time') is not None:
            _now = time.monotonic(); _prev = state_vars.get('last_tick')
            if _prev is not None:
                _el = _now - _prev
                if state_vars['board'].turn == chess.WHITE:
                    state_vars['white_time'] = max(0.0, state_vars['white_time'] - _el)
                else:
                    state_vars['black_time'] = max(0.0, state_vars['black_time'] - _el)
            state_vars['last_tick'] = _now

        # Resolve animação concluída
        _anim = state_vars.get('anim')
        if _anim and time.monotonic() - _anim['start'] >= _anim['duration']:
            if _anim.get('flip_perspective') is not None:
                state_vars['perspective'] = _anim['flip_perspective']
            state_vars['anim'] = None

        if current_state == "JOGANDO":
            is_human_turn=(state_vars['game_mode']=="PvP") or (state_vars['game_mode']=="IA" and state_vars['board'].turn==state_vars['player_color'])
            if not is_human_turn and state_vars['game_mode']=="IA" and ai_move_to_make is None and ai_thread is None and not state_vars.get('anim'):
                board_copy = state_vars['board'].copy()
                _tlimit = state_vars.get('time_limit', DEFAULT_TIME_LIMIT)
                ai_result[0] = None
                ai_thread = threading.Thread(target=lambda: ai_result.__setitem__(0, find_best_ai_move(board_copy, _tlimit)), daemon=True)
                ai_thread.start()
            if ai_thread is not None and not ai_thread.is_alive():
                ai_move_to_make = ai_result[0]
                ai_result[0] = None
                ai_thread = None

        screen.fill(COLOR_MENU_BG)
        if current_state == "MENU":
            btn_w,btn_h=400,60; menu_btn_x=(MENU_WIDTH-btn_w)//2
            white_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.3,btn_w,btn_h); black_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.5,btn_w,btn_h); pvp_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.7,btn_w,btn_h)
            draw_text(screen,"Xadrez",font_popup,COLOR_MENU_TEXT,pygame.Rect(0,0,MENU_WIDTH,MENU_HEIGHT*0.3),"center")
            pygame.draw.rect(screen,COLOR_LIGHT,white_btn); draw_text(screen,"Jogar de Brancas (vs IA)",font_ui,COLOR_PIECE_BLACK,white_btn,"center")
            pygame.draw.rect(screen,COLOR_DARK,black_btn); draw_text(screen,"Jogar de Pretas (vs IA)",font_ui,COLOR_MENU_TEXT,black_btn,"center")
            pygame.draw.rect(screen,COLOR_MENU_BG,pvp_btn,2); draw_text(screen,"Jogador vs Jogador",font_ui,COLOR_MENU_TEXT,pvp_btn,"center")
            _saves_exist=bool(list_saves())
            _load_btn=pygame.Rect(menu_btn_x,558,btn_w,40)
            pygame.draw.rect(screen,COLOR_DARK if _saves_exist else (55,55,55),_load_btn)
            draw_text(screen,"Carregar Partida",font_ui,COLOR_MENU_TEXT if _saves_exist else (110,110,110),_load_btn,"center")
            draw_text(screen,"Relógio por jogador:",font_ui,COLOR_COORD,pygame.Rect(0,615,MENU_WIDTH,28),"center")
            tc_btn_w,tc_btn_h=110,40; tc_total=len(TIME_CONTROLS)*(tc_btn_w+8)-8; tc_x0=(MENU_WIDTH-tc_total)//2; tc_y=642
            for i,(label,secs) in enumerate(TIME_CONTROLS):
                tc_btn=pygame.Rect(tc_x0+i*(tc_btn_w+8),tc_y,tc_btn_w,tc_btn_h); is_sel=state_vars.get('clock_config')==secs
                pygame.draw.rect(screen,(180,130,40) if is_sel else COLOR_DARK,tc_btn)
                if is_sel: pygame.draw.rect(screen,COLOR_MENU_TEXT,tc_btn,2)
                draw_text(screen,label,font_ui,COLOR_MENU_TEXT,tc_btn,"center")
        elif current_state in ["JOGANDO", "REVISAO", "PROMOCAO"]:
            draw_game_screen()
            if current_state == "PROMOCAO" and state_vars.get('pending_promotion'):
                draw_promotion_popup(screen, font_pieces, state_vars['pending_promotion'][1], state_vars['board'].turn, state_vars['perspective'])
            if current_state == "REVISAO":
                btn_w,btn_h=400,40; _below=GAME_HEIGHT-BOARD_RECT.bottom; again_review_btn=pygame.Rect((BOARD_RECT.width-btn_w)//2+BOARD_RECT.left,BOARD_RECT.bottom+(_below-btn_h)//2,btn_w,btn_h)
                pygame.draw.rect(screen, COLOR_DARK, again_review_btn); draw_text(screen, "Ir para o Menu", font_ui, COLOR_MENU_TEXT, again_review_btn, "center")
                _aidx_r = state_vars.get('analysis_index'); _hlen = len(state_vars['move_history_san'])
                _pos_n = _aidx_r if _aidx_r is not None else _hlen
                pygame.draw.rect(screen, COLOR_MENU_BG, ACTION_PANEL_RECT)
                draw_text(screen, f"Posição  {_pos_n} / {_hlen}", font_ui, COLOR_COORD, pygame.Rect(ACTION_PANEL_RECT.x, ACTION_PANEL_RECT.y + 12, ACTION_PANEL_RECT.width, 28), "center")
                draw_text(screen, "← →  navegar   |   ESC: final", font_ui, COLOR_COORD, pygame.Rect(ACTION_PANEL_RECT.x, ACTION_PANEL_RECT.y + 50, ACTION_PANEL_RECT.width, 28), "center")
                draw_text(screen, "Clique no histórico para ir ao movimento", font_ui, COLOR_COORD, pygame.Rect(ACTION_PANEL_RECT.x, ACTION_PANEL_RECT.y + 88, ACTION_PANEL_RECT.width, 28), "center")
        elif current_state == "PAUSE":
            draw_game_screen()
            draw_pause_menu(screen, font_popup, font_ui, state_vars.get('pause_page', 'main'), state_vars.get('time_limit', DEFAULT_TIME_LIMIT))
        elif current_state == "FIM_DE_JOGO":
            draw_game_screen()
            pop_btn_w,pop_btn_h=200,50; pop_btn_y=(GAME_HEIGHT-pop_btn_h)//2+60
            see_board_btn=pygame.Rect((GAME_WIDTH-pop_btn_w*2-20)//2,pop_btn_y,pop_btn_w,pop_btn_h); again_popup_btn=pygame.Rect(see_board_btn.right+20,pop_btn_y,pop_btn_w,pop_btn_h)
            draw_game_over_popup(screen,font_popup,font_popup_sub,state_vars['game_over_message'],see_board_btn,again_popup_btn)
        elif current_state == "CARREGAR":
            screen.fill(COLOR_MENU_BG)
            draw_text(screen,"Carregar Partida",font_popup,COLOR_MENU_TEXT,pygame.Rect(0,20,MENU_WIDTH,60),"center")
            _saves=state_vars.get('save_files',[])
            if not _saves:
                draw_text(screen,"Nenhuma partida encontrada.",font_ui,COLOR_COORD,pygame.Rect(0,120,MENU_WIDTH,40),"center")
            else:
                _bw2,_bh2,_bx2=500,40,(MENU_WIDTH-500)//2
                for i,fname in enumerate(_saves[:10]):
                    _fb=pygame.Rect(_bx2,100+i*48,_bw2,_bh2)
                    pygame.draw.rect(screen,COLOR_DARK,_fb)
                    _label=fname.replace("partida_","").replace(".pgn","").replace("_","  ")
                    draw_text(screen,_label,font_ui,COLOR_MENU_TEXT,_fb,"center")
            _back2=pygame.Rect((MENU_WIDTH-200)//2,MENU_HEIGHT-60,200,40)
            pygame.draw.rect(screen,COLOR_MENU_BG,_back2,2)
            draw_text(screen,"Voltar",font_ui,COLOR_MENU_TEXT,_back2,"center")

        if state_vars.get('toast_until',0.0) > time.monotonic():
            _tmsg=state_vars.get('toast_message') or ''
            _tsurf=font_ui.render(_tmsg,True,COLOR_MENU_TEXT)
            _tw=_tsurf.get_width()+24; _tx=(screen.get_width()-_tw)//2
            _tbg=pygame.Surface((_tw,36),pygame.SRCALPHA); _tbg.fill((20,20,20,210))
            screen.blit(_tbg,(_tx,6)); screen.blit(_tsurf,_tsurf.get_rect(centerx=_tx+_tw//2,centery=24))

        pygame.display.flip()

        if ai_move_to_make and current_state == "JOGANDO" and not state_vars.get('anim'):
            _p = state_vars['board'].piece_at(ai_move_to_make.from_square)
            _cap = state_vars['board'].is_capture(ai_move_to_make)
            state_vars['move_history_san'].append(state_vars['board'].san(ai_move_to_make))
            state_vars['board'].push(ai_move_to_make)
            _snd = 'check' if state_vars['board'].is_check() else ('capture' if _cap else 'move')
            _s = sounds.get(_snd); _s and _s.play()
            state_vars['anim'] = make_anim(ai_move_to_make.from_square, ai_move_to_make.to_square, _p, state_vars['perspective'])
            ai_move_to_make = None
            
        if current_state=="JOGANDO" and state_vars.get('white_time') is not None:
            if state_vars['white_time'] <= 0:
                state_vars['game_state']="FIM_DE_JOGO"; state_vars['game_over_message']="Tempo esgotado!\nPretas vencem."
                _s=sounds.get('game_end'); _s and _s.play()
            elif state_vars['black_time'] <= 0:
                state_vars['game_state']="FIM_DE_JOGO"; state_vars['game_over_message']="Tempo esgotado!\nBrancas vencem."
                _s=sounds.get('game_end'); _s and _s.play()

        if current_state=="JOGANDO" and state_vars['board'].is_game_over():
            state_vars['game_state']="FIM_DE_JOGO"; b=state_vars['board']
            if b.is_checkmate(): w="Brancas" if not b.turn else "Pretas"; state_vars['game_over_message']=f"Xeque-mate!\n{w} vencem."
            elif b.is_stalemate(): state_vars['game_over_message']="Empate!\n(Rei Afogado)"
            elif b.is_insufficient_material(): state_vars['game_over_message']="Empate!\n(Material Insuficiente)"
            elif b.is_seventyfive_moves(): state_vars['game_over_message']="Empate!\n(Regra dos 75 Movimentos)"
            else: state_vars['game_over_message']="Empate!\n(Repetição)"
            _s=sounds.get('game_end'); _s and _s.play()
            
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()