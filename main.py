import pygame
import chess
import sys
import math
import random

# --- Configurações e Constantes ---
PADDING = 40
BOARD_SIZE = 640
INFO_HEIGHT = 60
HISTORY_WIDTH = 240
SEARCH_DEPTH = 3

# Dimensões de tela separadas para Menu e Jogo
MENU_WIDTH, MENU_HEIGHT = 600, 600
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

# Áreas da Tela (calculadas dinamicamente quando necessário)
BOARD_RECT = pygame.Rect(PADDING, INFO_HEIGHT, BOARD_SIZE, BOARD_SIZE)
ACTION_PANEL_HEIGHT = 120
HISTORY_RECT = pygame.Rect(BOARD_RECT.right, INFO_HEIGHT, HISTORY_WIDTH, GAME_HEIGHT - INFO_HEIGHT - ACTION_PANEL_HEIGHT)
ACTION_PANEL_RECT = pygame.Rect(BOARD_RECT.right, HISTORY_RECT.bottom, HISTORY_WIDTH, ACTION_PANEL_HEIGHT)

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
def evaluate_board(board):
    if board.is_checkmate(): return math.inf if board.turn == chess.BLACK else -math.inf
    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(2): return 0
    total_value = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            val = piece_values[p.piece_type] + (piece_square_table[p.piece_type][sq if p.color else chess.square_mirror(sq)]/100.0)
            total_value += val if p.color == chess.WHITE else -val
    return total_value
def minimax(board, depth, alpha, beta, is_maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)
    if is_maximizing_player:
        max_eval = -math.inf
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
def find_best_ai_move(board):
    best_moves = []
    best_value = -math.inf if board.turn == chess.WHITE else math.inf
    for move in board.legal_moves:
        board.push(move)
        board_value = minimax(board, SEARCH_DEPTH - 1, -math.inf, math.inf, not board.turn)
        board.pop()
        if board.turn == chess.WHITE:
            if board_value > best_value:
                best_value = board_value
                best_moves = [move]
            elif board_value == best_value:
                best_moves.append(move)
        else:
            if board_value < best_value:
                best_value = board_value
                best_moves = [move]
            elif board_value == best_value:
                best_moves.append(move)
    return random.choice(best_moves) if best_moves else None

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
def draw_pieces(screen, board, font, perspective):
    for i in range(64):
        piece = board.piece_at(i)
        if piece:
            row, col = get_drawing_coords(i, perspective)
            symbol = PIECE_SYMBOLS[piece.symbol()]
            text_surface = font.render(symbol, True, COLOR_PIECE_BLACK)
            text_rect = text_surface.get_rect(center=(BOARD_RECT.left + col*SQUARE_SIZE + SQUARE_SIZE//2, BOARD_RECT.top + row*SQUARE_SIZE + SQUARE_SIZE//2))
            screen.blit(text_surface, text_rect)
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
def draw_info_panel(screen, font, board):
    info_rect = pygame.Rect(0, 0, BOARD_RECT.right, INFO_HEIGHT)
    pygame.draw.rect(screen, COLOR_MENU_BG, info_rect)
    move_text = f"Movimento: {board.fullmove_number}"
    move_r = pygame.Rect(PADDING, 0, 200, INFO_HEIGHT)
    draw_text(screen, move_text, font, COLOR_MENU_TEXT, move_r, "left")
    turn_text = "Vez das Brancas" if board.turn == chess.WHITE else "Vez das Pretas"
    turn_r = pygame.Rect(BOARD_RECT.right - 200, 0, 200, INFO_HEIGHT)
    draw_text(screen, turn_text, font, COLOR_MENU_TEXT, turn_r, "right")
def draw_history_panel(screen, font, history_san, scroll_offset):
    pygame.draw.rect(screen, COLOR_MENU_BG, HISTORY_RECT)
    title_rect = pygame.Rect(HISTORY_RECT.left, 0, HISTORY_RECT.width, INFO_HEIGHT)
    draw_text(screen, "Histórico", font, COLOR_MENU_TEXT, title_rect, "center")
    header_y = INFO_HEIGHT
    white_header_rect = pygame.Rect(HISTORY_RECT.left + 35, header_y, 70, 30)
    black_header_rect = pygame.Rect(HISTORY_RECT.left + 125, header_y, 70, 30)
    draw_text(screen, "Brancas", font, COLOR_MENU_TEXT, white_header_rect, "left")
    draw_text(screen, "Pretas", font, COLOR_MENU_TEXT, black_header_rect, "left")
    y_offset = header_y + 30
    line_height, max_visible_lines = 25, (HISTORY_RECT.height - (y_offset - HISTORY_RECT.top)) // 25
    start_index = scroll_offset * 2
    move_number = (start_index // 2) + 1
    for i in range(start_index, len(history_san), 2):
        if y_offset + line_height > HISTORY_RECT.bottom: break
        white_move = history_san[i]; black_move = ""
        if i + 1 < len(history_san): black_move = history_san[i+1]
        num_r = pygame.Rect(HISTORY_RECT.left+5, y_offset, 30, line_height)
        white_r = pygame.Rect(HISTORY_RECT.left+35, y_offset, 70, line_height)
        black_r = pygame.Rect(HISTORY_RECT.left+125, y_offset, 70, line_height)
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
def draw_action_panel(screen, font):
    pygame.draw.rect(screen, COLOR_MENU_BG, ACTION_PANEL_RECT)
    action_btn_w, action_btn_h = ACTION_PANEL_RECT.width-20, 45; action_btn_x = ACTION_PANEL_RECT.left+10
    undo_button = pygame.Rect(action_btn_x, ACTION_PANEL_RECT.top + 10, action_btn_w, action_btn_h)
    reset_button = pygame.Rect(action_btn_x, undo_button.bottom + 10, action_btn_w, action_btn_h)
    pygame.draw.rect(screen, COLOR_DARK, undo_button); draw_text(screen, "Voltar Jogada", font, COLOR_MENU_TEXT, undo_button, "center")
    pygame.draw.rect(screen, COLOR_DARK, reset_button); draw_text(screen, "Reiniciar Jogo", font, COLOR_MENU_TEXT, reset_button, "center")
    return undo_button, reset_button

def main():
    pygame.init(); pygame.font.init()
    screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
    pygame.display.set_caption("Xadrez em Python")
    try:
        font_pieces = pygame.font.Font("dejavusans.ttf", int(SQUARE_SIZE*0.75)); font_ui = pygame.font.Font("dejavusans.ttf", 20)
        font_coords = pygame.font.Font("dejavusans.ttf", 16); font_popup = pygame.font.Font("dejavusans.ttf", 36)
        font_popup_sub = pygame.font.Font("dejavusans.ttf", 22)
    except FileNotFoundError:
        font_pieces=pygame.font.Font(None,int(SQUARE_SIZE*0.9)); font_ui=pygame.font.Font(None,24); font_coords=pygame.font.Font(None,18)
        font_popup=pygame.font.Font(None,40); font_popup_sub=pygame.font.Font(None,26)
    
    state_vars = {}
    def reset_game():
        nonlocal screen
        screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
        state_vars.update({'board':chess.Board(), 'game_state':"MENU", 'game_mode':None, 'player_color':None, 'perspective':chess.WHITE, 'selected_square':None, 'possible_moves':[], 'game_over_message':"", 'move_history_san':[], 'history_scroll_offset': 0})
    reset_game()

    def draw_game_screen():
        screen.fill(COLOR_MENU_BG); draw_board(screen); draw_coordinates(screen,font_coords,state_vars['perspective'])
        draw_visual_aids(screen,state_vars['board'],state_vars['perspective'],state_vars['selected_square'],state_vars['possible_moves'])
        draw_pieces(screen,state_vars['board'],font_pieces,state_vars['perspective'])
        draw_info_panel(screen,font_ui,state_vars['board']); draw_history_panel(screen,font_ui,state_vars['move_history_san'],state_vars['history_scroll_offset'])
        return draw_action_panel(screen, font_ui)

    ai_move_to_make = None
    running = True
    while running:
        current_state = state_vars['game_state']
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.MOUSEWHEEL and current_state in ["JOGANDO", "REVISAO"]:
                if HISTORY_RECT.collidepoint(pygame.mouse.get_pos()):
                    state_vars['history_scroll_offset'] -= e.y
                    max_scroll = max(0, (len(state_vars['move_history_san'])+1)//2 - 15)
                    state_vars['history_scroll_offset'] = max(0, min(state_vars['history_scroll_offset'], max_scroll))
            if e.type == pygame.MOUSEBUTTONDOWN:
                if current_state == "MENU":
                    btn_w,btn_h=400,60; menu_btn_x=(MENU_WIDTH-btn_w)//2
                    white_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.3,btn_w,btn_h); black_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.5,btn_w,btn_h); pvp_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.7,btn_w,btn_h)
                    if white_btn.collidepoint(e.pos) or black_btn.collidepoint(e.pos) or pvp_btn.collidepoint(e.pos):
                        screen=pygame.display.set_mode((GAME_WIDTH,GAME_HEIGHT))
                        if white_btn.collidepoint(e.pos): state_vars.update(game_mode="IA",player_color=chess.WHITE,perspective=chess.WHITE,game_state="JOGANDO")
                        elif black_btn.collidepoint(e.pos): state_vars.update(game_mode="IA",player_color=chess.BLACK,perspective=chess.BLACK,game_state="JOGANDO")
                        elif pvp_btn.collidepoint(e.pos): state_vars.update(game_mode="PvP",perspective=chess.WHITE,game_state="JOGANDO")
                elif current_state == "JOGANDO":
                    is_human_turn=(state_vars['game_mode']=="PvP")or(state_vars['game_mode']=="IA" and state_vars['board'].turn==state_vars['player_color'])
                    if is_human_turn:
                        undo_button, reset_button = draw_action_panel(screen, font_ui)
                        if undo_button.collidepoint(e.pos):
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
                                    m=chess.Move(state_vars['selected_square'],sq,promotion=chess.QUEEN)
                                    if m not in state_vars['board'].legal_moves: m=chess.Move(state_vars['selected_square'],sq)
                                    if m in state_vars['board'].legal_moves:
                                        state_vars['move_history_san'].append(state_vars['board'].san(m)); state_vars['board'].push(m)
                                        if state_vars['game_mode']=="PvP": state_vars['perspective']=state_vars['board'].turn
                                    state_vars['selected_square'],state_vars['possible_moves']=None,[]
                elif current_state == "FIM_DE_JOGO":
                    pop_btn_w,pop_btn_h=200,50; pop_btn_y=(GAME_HEIGHT-pop_btn_h)//2+60
                    see_board_btn=pygame.Rect((GAME_WIDTH-pop_btn_w*2-20)//2,pop_btn_y,pop_btn_w,pop_btn_h); again_popup_btn=pygame.Rect(see_board_btn.right+20,pop_btn_y,pop_btn_w,pop_btn_h)
                    if see_board_btn.collidepoint(e.pos): state_vars['game_state']="REVISAO"
                    elif again_popup_btn.collidepoint(e.pos): reset_game()
                elif current_state == "REVISAO":
                    btn_w,btn_h=400,50; again_review_btn=pygame.Rect((BOARD_RECT.width-btn_w)//2+BOARD_RECT.left,BOARD_RECT.bottom+5,btn_w,btn_h)
                    if again_review_btn.collidepoint(e.pos): reset_game()

        if current_state == "JOGANDO":
            is_human_turn=(state_vars['game_mode']=="PvP") or (state_vars['game_mode']=="IA" and state_vars['board'].turn==state_vars['player_color'])
            if not is_human_turn and state_vars['game_mode']=="IA" and ai_move_to_make is None:
                ai_move_to_make = find_best_ai_move(state_vars['board'])

        screen.fill(COLOR_MENU_BG)
        if current_state == "MENU":
            btn_w,btn_h=400,60; menu_btn_x=(MENU_WIDTH-btn_w)//2
            white_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.3,btn_w,btn_h); black_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.5,btn_w,btn_h); pvp_btn=pygame.Rect(menu_btn_x,MENU_HEIGHT*0.7,btn_w,btn_h)
            draw_text(screen,"Xadrez",font_popup,COLOR_MENU_TEXT,pygame.Rect(0,0,MENU_WIDTH,MENU_HEIGHT*0.3),"center")
            pygame.draw.rect(screen,COLOR_LIGHT,white_btn); draw_text(screen,"Jogar de Brancas (vs IA)",font_ui,COLOR_PIECE_BLACK,white_btn,"center")
            pygame.draw.rect(screen,COLOR_DARK,black_btn); draw_text(screen,"Jogar de Pretas (vs IA)",font_ui,COLOR_MENU_TEXT,black_btn,"center")
            pygame.draw.rect(screen,COLOR_MENU_BG,pvp_btn,2); draw_text(screen,"Jogador vs Jogador",font_ui,COLOR_MENU_TEXT,pvp_btn,"center")
        elif current_state in ["JOGANDO", "REVISAO"]:
            draw_game_screen()
            if current_state == "REVISAO":
                btn_w,btn_h=400,50; again_review_btn=pygame.Rect((BOARD_RECT.width-btn_w)//2+BOARD_RECT.left,BOARD_RECT.bottom+5,btn_w,btn_h)
                pygame.draw.rect(screen, COLOR_DARK, again_review_btn); draw_text(screen, "Ir para o Menu", font_ui, COLOR_MENU_TEXT, again_review_btn, "center")
        elif current_state == "FIM_DE_JOGO":
            draw_game_screen()
            pop_btn_w,pop_btn_h=200,50; pop_btn_y=(GAME_HEIGHT-pop_btn_h)//2+60
            see_board_btn=pygame.Rect((GAME_WIDTH-pop_btn_w*2-20)//2,pop_btn_y,pop_btn_w,pop_btn_h); again_popup_btn=pygame.Rect(see_board_btn.right+20,pop_btn_y,pop_btn_w,pop_btn_h)
            draw_game_over_popup(screen,font_popup,font_popup_sub,state_vars['game_over_message'],see_board_btn,again_popup_btn)
        
        pygame.display.flip()
        
        if ai_move_to_make:
            pygame.time.delay(500)
            state_vars['move_history_san'].append(state_vars['board'].san(ai_move_to_make))
            state_vars['board'].push(ai_move_to_make)
            ai_move_to_make = None
            
        if current_state=="JOGANDO" and state_vars['board'].is_game_over():
            state_vars['game_state']="FIM_DE_JOGO"; b=state_vars['board']
            if b.is_checkmate(): w="Brancas" if not b.turn else "Pretas"; state_vars['game_over_message']=f"Xeque-mate!\n{w} vencem."
            elif b.is_stalemate(): state_vars['game_over_message']="Empate!\n(Rei Afogado)"
            elif b.is_insufficient_material(): state_vars['game_over_message']="Empate!\n(Material Insuficiente)"
            elif b.is_seventyfive_moves(): state_vars['game_over_message']="Empate!\n(Regra dos 75 Movimentos)"
            else: state_vars['game_over_message']="Empate!\n(Repetição)"
            
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()