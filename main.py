# main.py - FASE 3 (IA com Minimax)
import pygame
import chess
import sys
import math # Usaremos math.inf para infinito
import random

# --- Configurações e Constantes ---
BOARD_SIZE = 640
INFO_HEIGHT = 60
WIDTH, HEIGHT = BOARD_SIZE, BOARD_SIZE + INFO_HEIGHT
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_SIZE // COLS
BOARD_OFFSET_Y = INFO_HEIGHT
SEARCH_DEPTH = 3 # Profundidade da busca da IA. CUIDADO: valores > 3 podem ser lentos.

# Cores e Símbolos (sem alterações)
# ... (as seções de cores e PIECE_SYMBOLS continuam as mesmas)
COLOR_LIGHT = (238, 238, 210); COLOR_DARK = (118, 150, 86); COLOR_PIECE_BLACK = (0, 0, 0)
COLOR_HIGHLIGHT = (255, 255, 51, 150); COLOR_MOVE_HINT = (170, 170, 170, 150)
COLOR_CAPTURE_HINT = (255, 0, 0, 150); COLOR_CHECK_HINT = (255, 0, 0, 100)
COLOR_MENU_TEXT = (255, 255, 255); COLOR_MENU_BG = (49, 46, 43)
PIECE_SYMBOLS = {'P':'♙','R':'♖','N':'♘','B':'♗','Q':'♕','K':'♔','p':'♟','r':'♜','n':'♞','b':'♝','q':'♛','k':'♚'}


# --- Funções de Desenho e Lógica (sem alterações) ---
# ... (todas as funções de 'get_drawing_coords' até 'draw_text' continuam as mesmas)
def get_drawing_coords(square_index, perspective):
    row, col = 7 - (square_index // 8), square_index % 8
    if perspective == chess.BLACK: return 7 - row, 7 - col
    return row, col
def draw_board(screen):
    for r in range(ROWS):
        for c in range(COLS):
            color = COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK
            pygame.draw.rect(screen, color, (c * SQUARE_SIZE, r * SQUARE_SIZE + BOARD_OFFSET_Y, SQUARE_SIZE, SQUARE_SIZE))
def draw_pieces(screen, board, font, perspective):
    for i in range(64):
        piece = board.piece_at(i)
        if piece:
            symbol = PIECE_SYMBOLS[piece.symbol()]
            row, col = get_drawing_coords(i, perspective)
            text_surface = font.render(symbol, True, COLOR_PIECE_BLACK)
            text_rect = text_surface.get_rect(center=(col * SQUARE_SIZE + SQUARE_SIZE//2, row * SQUARE_SIZE + SQUARE_SIZE//2 + BOARD_OFFSET_Y))
            screen.blit(text_surface, text_rect)
def draw_visual_aids(screen, board, perspective, selected_square, possible_moves):
    if board.is_check():
        king_square = board.king(board.turn)
        row, col = get_drawing_coords(king_square, perspective)
        check_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA); check_surface.fill(COLOR_CHECK_HINT)
        screen.blit(check_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE + BOARD_OFFSET_Y))
    if selected_square is not None:
        row, col = get_drawing_coords(selected_square, perspective)
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA); highlight_surface.fill(COLOR_HIGHLIGHT)
        screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE + BOARD_OFFSET_Y))
    for move in possible_moves:
        row, col = get_drawing_coords(move.to_square, perspective)
        center_pos = (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2 + BOARD_OFFSET_Y)
        color = COLOR_CAPTURE_HINT if board.is_capture(move) else COLOR_MOVE_HINT
        radius = SQUARE_SIZE // 4 if board.is_capture(move) else SQUARE_SIZE // 6
        pygame.draw.circle(screen, color, center_pos, radius)
def get_square_from_mouse(pos, perspective):
    x, y = pos
    if y < BOARD_OFFSET_Y: return None
    row, col = (y - BOARD_OFFSET_Y) // SQUARE_SIZE, x // SQUARE_SIZE
    if perspective == chess.BLACK: row, col = 7 - row, 7 - col
    return (7 - row) * 8 + col
def draw_info_panel(screen, font, board):
    pygame.draw.rect(screen, COLOR_MENU_BG, (0, 0, WIDTH, INFO_HEIGHT))
    move_text = f"Movimento: {board.fullmove_number}"; move_rect = pygame.Rect(15, 0, 200, INFO_HEIGHT)
    draw_text(screen, move_text, font, COLOR_MENU_TEXT, move_rect, align="left")
    turn_text = "Vez das Brancas" if board.turn == chess.WHITE else "Vez das Pretas"
    turn_rect = pygame.Rect(WIDTH - 215, 0, 200, INFO_HEIGHT)
    draw_text(screen, turn_text, font, COLOR_MENU_TEXT, turn_rect, align="right")
def draw_text(screen, text, font, color, rect, align="left"):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(centery=rect.centery)
    if align == "left": text_rect.left = rect.left
    elif align == "center": text_rect.centerx = rect.centerx
    elif align == "right": text_rect.right = rect.right
    screen.blit(text_surface, text_rect)


# --- LÓGICA DA IA (MINIMAX) ---

piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

def evaluate_board(board):
    """ Avalia a posição do tabuleiro. Positivo = vantagem das brancas, Negativo = vantagem das pretas. """
    if board.is_checkmate():
        return math.inf if board.turn == chess.BLACK else -math.inf
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    total_value = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            total_value += value if piece.color == chess.WHITE else -value
    return total_value

def minimax(board, depth, alpha, beta, is_maximizing_player):
    """ Algoritmo Minimax com poda Alfa-Beta. """
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    legal_moves = list(board.legal_moves)
    
    if is_maximizing_player:
        max_eval = -math.inf
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else: # Minimizando
        min_eval = math.inf
        for move in legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def make_ai_move(board):
    """ Escolhe o melhor movimento para a IA usando o Minimax. """
    best_move = None
    best_value = -math.inf if board.turn == chess.WHITE else math.inf
    
    # Este loop para encontrar o melhor movimento pode demorar um pouco.
    # Esta é a parte em que a IA está "pensando".
    for move in board.legal_moves:
        board.push(move)
        board_value = minimax(board, SEARCH_DEPTH - 1, -math.inf, math.inf, board.turn != chess.WHITE)
        board.pop()
        
        if board.turn == chess.WHITE: # Maximizador
            if board_value > best_value:
                best_value = board_value
                best_move = move
        else: # Minimizador
            if board_value < best_value:
                best_value = board_value
                best_move = move
    
    if best_move:
        # A IA já decidiu. Adicionamos uma pausa dramática aqui.
        pygame.time.delay(500) # Pausa por 500 milissegundos (meio segundo)
        board.push(best_move)
    else: 
        if list(board.legal_moves):
            board.push(random.choice(list(board.legal_moves)))

# --- Função Principal e Estados de Jogo (sem alterações) ---
# O resto do código, começando com a função main(), é idêntico à Fase 2.
# Colei abaixo por completude, mas não há mudanças nele.
def main():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Xadrez em Python")
    try:
        font_pieces = pygame.font.Font("dejavusans.ttf", int(SQUARE_SIZE * 0.75))
        font_ui = pygame.font.Font("dejavusans.ttf", 30)
    except FileNotFoundError:
        font_pieces = pygame.font.Font(None, int(SQUARE_SIZE * 0.9))
        font_ui = pygame.font.Font(None, 36)

    game_state = "MENU"
    game_mode = None
    board = chess.Board()
    player_color = None
    perspective = chess.WHITE
    selected_square = None
    possible_moves = []
    game_over_message = ""

    btn_height = 50; btn_width = WIDTH * 0.7; btn_x = (WIDTH - btn_width) / 2
    white_button = pygame.Rect(btn_x, HEIGHT * 0.3, btn_width, btn_height)
    black_button = pygame.Rect(btn_x, HEIGHT * 0.45, btn_width, btn_height)
    pvp_button = pygame.Rect(btn_x, HEIGHT * 0.6, btn_width, btn_height)
    play_again_button = pygame.Rect(btn_x, HEIGHT * 0.6, btn_width, btn_height)
    
    running = True
    while running:
        if game_state == "MENU":
            screen.fill(COLOR_MENU_BG)
            draw_text(screen, "Xadrez", font_ui, COLOR_MENU_TEXT, pygame.Rect(0, 0, WIDTH, HEIGHT*0.3), align="center")
            pygame.draw.rect(screen, COLOR_LIGHT, white_button); draw_text(screen, "Jogar de Brancas (vs IA)", font_ui, COLOR_PIECE_BLACK, white_button, align="center")
            pygame.draw.rect(screen, COLOR_DARK, black_button); draw_text(screen, "Jogar de Pretas (vs IA)", font_ui, COLOR_MENU_TEXT, black_button, align="center")
            pygame.draw.rect(screen, COLOR_MENU_BG, pvp_button, 2); draw_text(screen, "Jogador vs Jogador", font_ui, COLOR_MENU_TEXT, pvp_button, align="center")
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if white_button.collidepoint(pos): game_mode, player_color, perspective, game_state = "IA", chess.WHITE, chess.WHITE, "JOGANDO"
                    elif black_button.collidepoint(pos): game_mode, player_color, perspective, game_state = "IA", chess.BLACK, chess.BLACK, "JOGANDO"
                    elif pvp_button.collidepoint(pos): game_mode, player_color, perspective, game_state = "PvP", None, chess.WHITE, "JOGANDO"
        
        elif game_state == "JOGANDO":
            is_human_turn = (game_mode == "PvP") or (game_mode == "IA" and board.turn == player_color)
            if not is_human_turn and game_mode == "IA":
                make_ai_move(board)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN and is_human_turn:
                    clicked_square = get_square_from_mouse(event.pos, perspective)
                    if clicked_square is not None:
                        if selected_square is None:
                            piece = board.piece_at(clicked_square)
                            if piece and piece.color == board.turn:
                                selected_square = clicked_square
                                possible_moves = [m for m in board.legal_moves if m.from_square == selected_square]
                        else:
                            move = chess.Move(selected_square, clicked_square, promotion=chess.QUEEN)
                            if move not in board.legal_moves: move = chess.Move(selected_square, clicked_square)
                            if move in board.legal_moves:
                                board.push(move)
                                if game_mode == "PvP": perspective = board.turn
                            selected_square, possible_moves = None, []
            screen.fill(COLOR_MENU_BG)
            draw_info_panel(screen, font_ui, board)
            draw_board(screen)
            draw_visual_aids(screen, board, perspective, selected_square, possible_moves)
            draw_pieces(screen, board, font_pieces, perspective)
            if board.is_game_over():
                game_state = "FIM_DE_JOGO"
                if board.is_checkmate():
                    winner = "Brancas" if board.turn == chess.BLACK else "Pretas"
                    game_over_message = f"Xeque-mate! {winner} vencem."
                else: game_over_message = "Empate!"

        elif game_state == "FIM_DE_JOGO":
            screen.fill(COLOR_MENU_BG)
            draw_text(screen, game_over_message, font_ui, COLOR_MENU_TEXT, pygame.Rect(0, 0, WIDTH, HEIGHT*0.6), align="center")
            pygame.draw.rect(screen, COLOR_DARK, play_again_button)
            draw_text(screen, "Jogar Novamente", font_ui, COLOR_MENU_TEXT, play_again_button, align="center")
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_again_button.collidepoint(event.pos):
                        board.reset(); game_state = "MENU"; selected_square, possible_moves, game_mode, player_color = None, [], None, None; perspective = chess.WHITE
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()