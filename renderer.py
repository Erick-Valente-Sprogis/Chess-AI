import chess
import pygame
import time

from config import (
    BOARD_RECT, HISTORY_RECT, ACTION_PANEL_RECT, PAUSE_BTN,
    COLOR_LIGHT, COLOR_DARK, COLOR_PIECE_BLACK,
    COLOR_HIGHLIGHT, COLOR_LAST_MOVE, COLOR_MOVE_HINT, COLOR_CAPTURE_HINT, COLOR_CHECK_HINT,
    COLOR_MENU_BG, COLOR_MENU_TEXT, COLOR_COORD,
    PIECE_SYMBOLS, ANIM_DURATION, SQUARE_SIZE, ROWS, COLS,
    PADDING, INFO_HEIGHT, DIFFICULTY_LEVELS, DEFAULT_TIME_LIMIT,
    GAME_HEIGHT, format_clock,
)


def draw_text(screen, text, font, color, rect, align="left"):
    text_surface = font.render(text, True, color)
    text_rect    = text_surface.get_rect(centery=rect.centery)
    if align == "left":
        text_rect.left    = rect.left
    elif align == "center":
        text_rect.centerx = rect.centerx
    elif align == "right":
        text_rect.right   = rect.right
    screen.blit(text_surface, text_rect)


def get_drawing_coords(square_index, perspective):
    row, col = 7 - (square_index // 8), square_index % 8
    if perspective == chess.BLACK:
        return 7 - row, 7 - col
    return row, col


def draw_board(screen):
    for r in range(ROWS):
        for c in range(COLS):
            color = COLOR_LIGHT if (r + c) % 2 == 0 else COLOR_DARK
            pygame.draw.rect(screen, color,
                             (BOARD_RECT.left + c * SQUARE_SIZE,
                              BOARD_RECT.top  + r * SQUARE_SIZE,
                              SQUARE_SIZE, SQUARE_SIZE))


def draw_coordinates(screen, font, perspective):
    files = "abcdefgh"
    ranks = "12345678"
    if perspective == chess.BLACK:
        files = files[::-1]
        ranks = ranks[::-1]
    for i in range(8):
        ft = font.render(files[i], True, COLOR_COORD)
        screen.blit(ft, (BOARD_RECT.left + i * SQUARE_SIZE + (SQUARE_SIZE - ft.get_width()) // 2,
                         BOARD_RECT.bottom + 5))
        screen.blit(ft, (BOARD_RECT.left + i * SQUARE_SIZE + (SQUARE_SIZE - ft.get_width()) // 2,
                         BOARD_RECT.top - PADDING // 2 - ft.get_height() // 2))
        rt = font.render(ranks[i], True, COLOR_COORD)
        screen.blit(rt, (BOARD_RECT.left - PADDING // 2 - rt.get_width() // 2,
                         BOARD_RECT.bottom - (i + 1) * SQUARE_SIZE + (SQUARE_SIZE - rt.get_height()) // 2))
        screen.blit(rt, (BOARD_RECT.right + 5,
                         BOARD_RECT.bottom - (i + 1) * SQUARE_SIZE + (SQUARE_SIZE - rt.get_height()) // 2))


def draw_pieces(screen, board, font, perspective, anim=None):
    skip_sq = anim['to_square'] if anim else -1
    for i in range(64):
        if i == skip_sq:
            continue
        piece = board.piece_at(i)
        if piece:
            row, col = get_drawing_coords(i, perspective)
            symbol   = PIECE_SYMBOLS[piece.symbol()]
            surf     = font.render(symbol, True, COLOR_PIECE_BLACK)
            rect     = surf.get_rect(center=(
                BOARD_RECT.left + col * SQUARE_SIZE + SQUARE_SIZE // 2,
                BOARD_RECT.top  + row * SQUARE_SIZE + SQUARE_SIZE // 2,
            ))
            screen.blit(surf, rect)
    if anim:
        t = min(1.0, (time.monotonic() - anim['start']) / anim['duration'])
        t = t * t * (3 - 2 * t)
        fx, fy = anim['from_center']
        tx, ty = anim['to_center']
        cx = int(fx + (tx - fx) * t)
        cy = int(fy + (ty - fy) * t)
        surf = font.render(PIECE_SYMBOLS[anim['piece'].symbol()], True, COLOR_PIECE_BLACK)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))


def draw_visual_aids(screen, board, perspective, selected_square, possible_moves, last_move=None):
    if last_move is not None:
        surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        surface.fill(COLOR_LAST_MOVE)
        for sq in (last_move.from_square, last_move.to_square):
            row, col = get_drawing_coords(sq, perspective)
            screen.blit(surface, (BOARD_RECT.left + col * SQUARE_SIZE, BOARD_RECT.top + row * SQUARE_SIZE))
    if board.is_check():
        row, col = get_drawing_coords(board.king(board.turn), perspective)
        surface  = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        surface.fill(COLOR_CHECK_HINT)
        screen.blit(surface, (BOARD_RECT.left + col * SQUARE_SIZE, BOARD_RECT.top + row * SQUARE_SIZE))
    if selected_square is not None:
        row, col = get_drawing_coords(selected_square, perspective)
        surface  = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        surface.fill(COLOR_HIGHLIGHT)
        screen.blit(surface, (BOARD_RECT.left + col * SQUARE_SIZE, BOARD_RECT.top + row * SQUARE_SIZE))
    for move in possible_moves:
        row, col = get_drawing_coords(move.to_square, perspective)
        center   = (BOARD_RECT.left + col * SQUARE_SIZE + SQUARE_SIZE // 2,
                    BOARD_RECT.top  + row * SQUARE_SIZE + SQUARE_SIZE // 2)
        color    = COLOR_CAPTURE_HINT if board.is_capture(move) else COLOR_MOVE_HINT
        radius   = SQUARE_SIZE // 4    if board.is_capture(move) else SQUARE_SIZE // 6
        pygame.draw.circle(screen, color, center, radius)


def get_square_from_mouse(pos, perspective):
    if not BOARD_RECT.collidepoint(pos):
        return None
    row = (pos[1] - BOARD_RECT.top)  // SQUARE_SIZE
    col = (pos[0] - BOARD_RECT.left) // SQUARE_SIZE
    if perspective == chess.BLACK:
        row, col = 7 - row, 7 - col
    return (7 - row) * 8 + col


def draw_info_panel(screen, font, board, white_time=None, black_time=None, ai_thinking=False):
    pygame.draw.rect(screen, COLOR_MENU_BG, pygame.Rect(0, 0, BOARD_RECT.right, INFO_HEIGHT))
    draw_text(screen, f"Movimento: {board.fullmove_number}", font, COLOR_MENU_TEXT,
              pygame.Rect(BOARD_RECT.left, 0, 200, INFO_HEIGHT), "left")
    pygame.draw.rect(screen, COLOR_DARK, PAUSE_BTN, border_radius=6)
    bar_w, bar_h = 7, 24
    bar_y = PAUSE_BTN.centery - bar_h // 2
    pygame.draw.rect(screen, COLOR_MENU_TEXT, (PAUSE_BTN.centerx - 11, bar_y, bar_w, bar_h))
    pygame.draw.rect(screen, COLOR_MENU_TEXT, (PAUSE_BTN.centerx + 4,  bar_y, bar_w, bar_h))
    if white_time is not None:
        half = INFO_HEIGHT // 2
        for clr, t, sym, row in [(chess.BLACK, black_time, "♟", 0), (chess.WHITE, white_time, "♙", half)]:
            r        = pygame.Rect(BOARD_RECT.right - 200, row, 200, half)
            is_active = board.turn == clr and not ai_thinking
            if is_active:
                pygame.draw.rect(screen, (50, 80, 50) if clr == chess.WHITE else (80, 50, 50), r)
            txt_color = (255, 80, 80) if t is not None and t < 30 else COLOR_MENU_TEXT
            draw_text(screen, f"{sym} {format_clock(t)}", font, txt_color, r, "right")
    else:
        turn_text = ("IA pensando..." if ai_thinking
                     else ("Vez das Brancas" if board.turn == chess.WHITE else "Vez das Pretas"))
        draw_text(screen, turn_text, font, COLOR_MENU_TEXT,
                  pygame.Rect(BOARD_RECT.right - 200, 0, 200, INFO_HEIGHT), "right")


def draw_history_panel(screen, font, history_san, scroll_offset, selected_san_index=None):
    pygame.draw.rect(screen, COLOR_MENU_BG, HISTORY_RECT)
    title_rect = pygame.Rect(HISTORY_RECT.left, 0, HISTORY_RECT.width, INFO_HEIGHT)
    draw_text(screen, "Histórico", font, COLOR_MENU_TEXT, title_rect, "center")
    header_y   = INFO_HEIGHT
    num_x      = HISTORY_RECT.left + 5
    num_w      = 38
    move_col_w = (HISTORY_RECT.width - num_w - 20) // 2
    white_x    = num_x + num_w + 5
    black_x    = white_x + move_col_w + 5
    draw_text(screen, "Brancas", font, COLOR_MENU_TEXT, pygame.Rect(white_x, header_y, move_col_w, 32), "left")
    draw_text(screen, "Pretas",  font, COLOR_MENU_TEXT, pygame.Rect(black_x, header_y, move_col_w, 32), "left")
    y_offset    = header_y + 32
    line_height = 28
    start_index = scroll_offset * 2
    move_number = (start_index // 2) + 1
    for i in range(start_index, len(history_san), 2):
        if y_offset + line_height > HISTORY_RECT.bottom:
            break
        white_move = history_san[i]
        black_move = history_san[i + 1] if i + 1 < len(history_san) else ""
        num_r   = pygame.Rect(num_x,   y_offset, num_w,      line_height)
        white_r = pygame.Rect(white_x, y_offset, move_col_w, line_height)
        black_r = pygame.Rect(black_x, y_offset, move_col_w, line_height)
        if selected_san_index == i:
            pygame.draw.rect(screen, (70, 70, 120), white_r)
        elif selected_san_index == i + 1 and black_move:
            pygame.draw.rect(screen, (70, 70, 120), black_r)
        draw_text(screen, f"{move_number}.", font, COLOR_MENU_TEXT, num_r,   "left")
        draw_text(screen, white_move,        font, COLOR_MENU_TEXT, white_r, "left")
        draw_text(screen, black_move,        font, COLOR_MENU_TEXT, black_r, "left")
        y_offset    += line_height
        move_number += 1


def draw_game_over_popup(screen, font_main, font_sub, message, btn_see, btn_again):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    pop_w, pop_h = 500, 250
    pop_r = pygame.Rect((screen.get_width() - pop_w) // 2, (screen.get_height() - pop_h) // 2, pop_w, pop_h)
    pygame.draw.rect(screen, COLOR_MENU_BG, pop_r)
    pygame.draw.rect(screen, COLOR_MENU_TEXT, pop_r, 2)
    messages = message.split('\n')
    main_msg = messages[0]
    sub_msg  = messages[1] if len(messages) > 1 else ""
    draw_text(screen, main_msg, font_main, COLOR_MENU_TEXT,
              pygame.Rect(pop_r.x, pop_r.y, pop_r.width, int(pop_r.height * 0.4)), "center")
    draw_text(screen, sub_msg, font_sub, COLOR_COORD,
              pygame.Rect(pop_r.x, pop_r.y + 45, pop_r.width, int(pop_r.height * 0.4)), "center")
    pygame.draw.rect(screen, COLOR_DARK, btn_see)
    draw_text(screen, "Ver Tabuleiro", font_sub, COLOR_MENU_TEXT, btn_see, "center")
    pygame.draw.rect(screen, COLOR_DARK, btn_again)
    draw_text(screen, "Ir para o Menu", font_sub, COLOR_MENU_TEXT, btn_again, "center")


def draw_pause_menu(screen, font_title, font_btn, page="main", current_time_limit=DEFAULT_TIME_LIMIT):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    pop_w, pop_h = 480, 440
    pop_r  = pygame.Rect((screen.get_width() - pop_w) // 2, (screen.get_height() - pop_h) // 2, pop_w, pop_h)
    pygame.draw.rect(screen, COLOR_MENU_BG, pop_r)
    pygame.draw.rect(screen, COLOR_MENU_TEXT, pop_r, 2)
    btn_w, btn_h, btn_gap = 400, 50, 12
    btn_x = pop_r.x + (pop_w - btn_w) // 2
    if page == "difficulty":
        draw_text(screen, "Dificuldade", font_title, COLOR_MENU_TEXT,
                  pygame.Rect(pop_r.x, pop_r.y + 10, pop_r.width, 50), "center")
        btn_y0 = pop_r.y + 70
        btns   = []
        for i, (label, tlimit) in enumerate(DIFFICULTY_LEVELS):
            btn       = pygame.Rect(btn_x, btn_y0 + i * (btn_h + btn_gap), btn_w, btn_h)
            is_active = tlimit == current_time_limit
            bg        = (180, 130, 40) if is_active else COLOR_DARK
            pygame.draw.rect(screen, bg, btn)
            if is_active:
                pygame.draw.rect(screen, COLOR_MENU_TEXT, btn, 2)
            draw_text(screen, label, font_btn, COLOR_MENU_TEXT, btn, "center")
            btns.append(btn)
        back_btn = pygame.Rect(btn_x, btn_y0 + len(DIFFICULTY_LEVELS) * (btn_h + btn_gap), btn_w, btn_h)
        pygame.draw.rect(screen, COLOR_MENU_BG, back_btn, 2)
        draw_text(screen, "Voltar", font_btn, COLOR_MENU_TEXT, back_btn, "center")
        return btns, back_btn
    else:
        draw_text(screen, "Pausa", font_title, COLOR_MENU_TEXT,
                  pygame.Rect(pop_r.x, pop_r.y + 10, pop_r.width, 50), "center")
        btn_y0  = pop_r.y + 80
        entries = [
            "Retornar à Partida",
            "Reiniciar Partida",
            "Mudar Dificuldade",
            "Exportar PGN",
            "Voltar ao Menu Principal",
        ]
        btns = []
        for i, label in enumerate(entries):
            btn = pygame.Rect(btn_x, btn_y0 + i * (btn_h + btn_gap), btn_w, btn_h)
            pygame.draw.rect(screen, COLOR_DARK, btn)
            draw_text(screen, label, font_btn, COLOR_MENU_TEXT, btn, "center")
            btns.append(btn)
        return btns, None


def draw_promotion_popup(screen, font_pieces, to_sq, promoting_color, perspective):
    pieces   = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    draw_row, draw_col = get_drawing_coords(to_sq, perspective)
    x    = BOARD_RECT.left + draw_col * SQUARE_SIZE
    step = 1 if draw_row == 0 else -1
    btns = []
    for i, pt in enumerate(pieces):
        y   = BOARD_RECT.top + (draw_row + i * step) * SQUARE_SIZE
        btn = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(screen, COLOR_LIGHT, btn)
        pygame.draw.rect(screen, COLOR_PIECE_BLACK, btn, 3)
        sym  = PIECE_SYMBOLS[chess.Piece(pt, promoting_color).symbol()]
        surf = font_pieces.render(sym, True, COLOR_PIECE_BLACK)
        screen.blit(surf, surf.get_rect(center=btn.center))
        btns.append((btn, pt))
    return btns


def draw_action_panel(screen, font):
    pygame.draw.rect(screen, COLOR_MENU_BG, ACTION_PANEL_RECT)
    btn_w = ACTION_PANEL_RECT.width - 20
    btn_h = 45
    btn_x = ACTION_PANEL_RECT.left + 10
    undo_button  = pygame.Rect(btn_x, ACTION_PANEL_RECT.top + 10,            btn_w, btn_h)
    reset_button = pygame.Rect(btn_x, undo_button.bottom + 10, btn_w, btn_h)
    pygame.draw.rect(screen, COLOR_DARK, undo_button)
    draw_text(screen, "Voltar Jogada",  font, COLOR_MENU_TEXT, undo_button,  "center")
    pygame.draw.rect(screen, COLOR_DARK, reset_button)
    draw_text(screen, "Reiniciar Jogo", font, COLOR_MENU_TEXT, reset_button, "center")
    return undo_button, reset_button


def make_anim(from_sq, to_sq, piece, perspective, flip_perspective=None):
    fr, fc = get_drawing_coords(from_sq, perspective)
    tr, tc = get_drawing_coords(to_sq,   perspective)
    return {
        'piece':            piece,
        'from_center':      (BOARD_RECT.left + fc * SQUARE_SIZE + SQUARE_SIZE // 2,
                             BOARD_RECT.top  + fr * SQUARE_SIZE + SQUARE_SIZE // 2),
        'to_center':        (BOARD_RECT.left + tc * SQUARE_SIZE + SQUARE_SIZE // 2,
                             BOARD_RECT.top  + tr * SQUARE_SIZE + SQUARE_SIZE // 2),
        'to_square':        to_sq,
        'start':            time.monotonic(),
        'duration':         ANIM_DURATION,
        'flip_perspective': flip_perspective,
    }


def board_at(full_board, n):
    """Reconstruct board state after n half-moves from full_board.move_stack."""
    b = chess.Board()
    for m in list(full_board.move_stack)[:n]:
        b.push(m)
    return b
