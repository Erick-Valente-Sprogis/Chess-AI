import chess
import chess.polyglot
import math
import random
import time

from config import DEFAULT_TIME_LIMIT

piece_values = {
    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0,
}
piece_square_table = {
    chess.PAWN: [
        0,0,0,0,0,0,0,0,
        50,50,50,50,50,50,50,50,
        10,10,20,30,30,20,10,10,
        5,5,10,25,25,10,5,5,
        0,0,0,20,20,0,0,0,
        5,-5,-10,0,0,-10,-5,5,
        5,10,10,-20,-20,10,10,5,
        0,0,0,0,0,0,0,0,
    ],
    chess.KNIGHT: [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,0,0,0,0,-20,-40,
        -30,0,10,15,15,10,0,-30,
        -30,5,15,20,20,15,5,-30,
        -30,0,15,20,20,15,0,-30,
        -30,5,10,15,15,10,5,-30,
        -40,-20,0,5,5,0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ],
    chess.BISHOP: [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,0,0,0,0,0,0,-10,
        -10,0,5,10,10,5,0,-10,
        -10,5,5,10,10,5,5,-10,
        -10,0,10,10,10,10,0,-10,
        -10,10,10,10,10,10,10,-10,
        -10,5,0,0,0,0,5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ],
    chess.ROOK: [
        0,0,0,0,0,0,0,0,
        5,10,10,10,10,10,10,5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        0,0,0,5,5,0,0,0,
    ],
    chess.QUEEN: [
        -20,-10,-10,-5,-5,-10,-10,-20,
        -10,0,0,0,0,0,0,-10,
        -10,0,5,5,5,5,0,-10,
        -5,0,5,5,5,5,0,-5,
        0,0,5,5,5,5,0,-5,
        -10,5,5,5,5,5,0,-10,
        -10,0,5,0,0,0,0,-10,
        -20,-10,-10,-5,-5,-10,-10,-20,
    ],
    chess.KING: [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20,20,0,0,0,0,20,20,
        20,30,10,0,0,10,30,20,
    ],
}

_TT_EXACT      = 0
_TT_LOWERBOUND = 1
_TT_UPPERBOUND = 2
_TT_MAX_SIZE   = 1_000_000
_tt            = {}
_NMP_REDUCTION = 2

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
    pawn_files  = [chess.square_file(sq) for sq in pawns]
    file_set    = set(pawn_files)
    enemy_pawns = list(board.pieces(chess.PAWN, not color))
    for sq in pawns:
        f = chess.square_file(sq)
        r = chess.square_rank(sq)
        if pawn_files.count(f) > 1:
            score -= 0.25
        adj = {f - 1, f + 1} & set(range(8))
        if not adj & file_set:
            score -= 0.20
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
    if not board.pieces(chess.QUEEN, chess.WHITE) and not board.pieces(chess.QUEEN, chess.BLACK):
        return 0.0
    score = 0.0
    kf = chess.square_file(king_sq)
    kr = chess.square_rank(king_sq)
    friendly_pawns = board.pieces(chess.PAWN, color)
    enemy_pawns    = board.pieces(chess.PAWN, not color)
    shield_files   = [f for f in (kf - 1, kf, kf + 1) if 0 <= f <= 7]
    for f in shield_files:
        r1 = kr + 1 if color == chess.WHITE else kr - 1
        r2 = kr + 2 if color == chess.WHITE else kr - 2
        has_r1 = 0 <= r1 <= 7 and chess.square(f, r1) in friendly_pawns
        has_r2 = 0 <= r2 <= 7 and chess.square(f, r2) in friendly_pawns
        if has_r1:
            score += 0.15
        elif has_r2:
            score += 0.05
        file_has_friendly = any(chess.square_file(sq) == f for sq in friendly_pawns)
        file_has_enemy    = any(chess.square_file(sq) == f for sq in enemy_pawns)
        if not file_has_friendly:
            score -= 0.25 if not file_has_enemy else 0.10
    return score


def evaluate_board(board):
    if board.is_checkmate():
        return math.inf if board.turn == chess.BLACK else -math.inf
    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(3):
        return 0
    if board.is_repetition(2):
        return 0.3 if board.turn == chess.WHITE else -0.3
    total_value = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            val = piece_values[p.piece_type] + (
                piece_square_table[p.piece_type][sq if p.color else chess.square_mirror(sq)] / 100.0
            )
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
            victim   = board.piece_at(move.to_square)
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


def minimax(board, depth, alpha, beta, is_maximizing_player, deadline, tt, allow_null=True):
    if time.monotonic() >= deadline:
        raise _SearchTimeout()
    original_alpha, original_beta = alpha, beta
    z     = chess.polyglot.zobrist_hash(board)
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
    # Null Move Pruning
    if allow_null and depth >= _NMP_REDUCTION + 1 and not board.is_check():
        color = chess.WHITE if is_maximizing_player else chess.BLACK
        has_pieces = any(
            board.pieces(pt, color)
            for pt in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
        )
        if has_pieces:
            board.push(chess.Move.null())
            null_score = minimax(board, depth - 1 - _NMP_REDUCTION, alpha, beta,
                                 not is_maximizing_player, deadline, tt, allow_null=False)
            board.pop()
            if is_maximizing_player and null_score >= beta:
                return beta
            elif not is_maximizing_player and null_score <= alpha:
                return alpha
    legal = list(board.legal_moves)
    if tt_move is not None and tt_move in board.legal_moves:
        moves = [tt_move] + order_moves(board, [m for m in legal if m != tt_move])
    else:
        moves = order_moves(board, legal)
    best_val        = -math.inf if is_maximizing_player else math.inf
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
        flag = (
            _TT_EXACT if original_alpha < best_val < original_beta
            else (_TT_LOWERBOUND if best_val >= original_beta else _TT_UPPERBOUND)
        )
        tt[z] = (depth, best_val, flag, best_move_found)
    return best_val


def find_best_ai_move(board, time_limit=DEFAULT_TIME_LIMIT):
    book_moves = [
        m for m in _opening_book.get(chess.polyglot.zobrist_hash(board), [])
        if m in board.legal_moves
    ]
    if book_moves:
        return random.choice(book_moves)
    deadline           = time.monotonic() + time_limit
    is_white_turn      = board.turn == chess.WHITE
    initial_stack_size = len(board.move_stack)
    all_legal          = list(board.legal_moves)
    if not all_legal:
        return None
    best_move = order_moves(board, all_legal)[0]
    for depth in range(1, 20):
        if time.monotonic() >= deadline:
            break
        entry        = _tt.get(chess.polyglot.zobrist_hash(board))
        tt_root_move = entry[3] if entry else None
        if tt_root_move is not None and tt_root_move in board.legal_moves:
            legal = [tt_root_move] + order_moves(board, [m for m in all_legal if m != tt_root_move])
        else:
            legal = order_moves(board, all_legal)
        candidate_move = None
        best_value     = -math.inf if is_white_turn else math.inf
        best_moves     = []
        try:
            for move in legal:
                board.push(move)
                board_value = minimax(
                    board, depth - 1, -math.inf, math.inf,
                    board.turn == chess.WHITE, deadline, _tt
                )
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
