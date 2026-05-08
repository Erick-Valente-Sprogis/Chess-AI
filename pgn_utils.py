import datetime
import os

import chess
import chess.pgn

from config import SAVES_DIR


def export_pgn(board, game_mode, player_color, clock_config):
    os.makedirs(SAVES_DIR, exist_ok=True)
    game = chess.pgn.Game()
    node = game
    for move in board.move_stack:
        node = node.add_main_variation(move)
    white_name = "Jogador" if (game_mode == "PvP" or player_color == chess.WHITE) else "IA"
    black_name = "Jogador" if (game_mode == "PvP" or player_color == chess.BLACK) else "IA"
    game.headers["Event"]  = "Chess-AI"
    game.headers["Site"]   = "Local"
    game.headers["Date"]   = datetime.date.today().strftime("%Y.%m.%d")
    game.headers["White"]  = white_name
    game.headers["Black"]  = black_name
    game.headers["Result"] = board.result() if board.is_game_over() else "*"
    if clock_config:
        game.headers["TimeControl"] = str(clock_config)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"partida_{timestamp}.pgn"
    filepath  = os.path.join(SAVES_DIR, filename)
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
        board       = chess.Board()
        history_san = []
        for move in game.mainline_moves():
            history_san.append(board.san(move))
            board.push(move)
        return board, history_san, dict(game.headers)
    except Exception:
        return None
