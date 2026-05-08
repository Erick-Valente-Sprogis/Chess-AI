import sys
import threading
import time

import chess
import pygame

from config import (
    MENU_WIDTH, MENU_HEIGHT, GAME_WIDTH, GAME_HEIGHT,
    BOARD_RECT, HISTORY_RECT, ACTION_PANEL_RECT, PAUSE_BTN,
    COLOR_MENU_BG, COLOR_MENU_TEXT, COLOR_DARK, COLOR_LIGHT,
    COLOR_PIECE_BLACK, COLOR_COORD,
    DIFFICULTY_LEVELS, DEFAULT_TIME_LIMIT, TIME_CONTROLS,
    SAVES_DIR, SQUARE_SIZE,
)
from ai import find_best_ai_move
from renderer import (
    draw_text, draw_board, draw_coordinates, draw_pieces,
    draw_visual_aids, get_square_from_mouse,
    draw_info_panel, draw_history_panel,
    draw_game_over_popup, draw_pause_menu,
    draw_promotion_popup, draw_action_panel,
    make_anim, board_at,
)
from sounds import make_sounds
from pgn_utils import export_pgn, list_saves, import_pgn


def main():
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    pygame.font.init()
    try:
        sounds = make_sounds()
    except Exception:
        sounds = {}

    screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
    pygame.display.set_caption("Xadrez em Python")

    _font_path = (
        pygame.font.match_font('dejavusans') or
        pygame.font.match_font('notosanssymbols2') or
        pygame.font.match_font('notosanssymbols')
    )

    def load_font(size):
        if _font_path:
            return pygame.font.Font(_font_path, size)
        return pygame.font.Font(None, size)

    font_pieces    = load_font(int(SQUARE_SIZE * 0.75))
    font_ui        = load_font(20)
    font_coords    = load_font(16)
    font_popup     = load_font(36)
    font_popup_sub = load_font(22)

    ai_move_to_make = None
    ai_thread       = None
    ai_result       = [None]

    state_vars = {}

    def reset_game():
        nonlocal screen, ai_move_to_make, ai_thread, ai_result
        screen          = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
        ai_move_to_make = None
        ai_thread       = None
        ai_result       = [None]
        _clock = state_vars.get('clock_config')
        state_vars.update({
            'board':                chess.Board(),
            'game_state':           "MENU",
            'game_mode':            None,
            'player_color':         None,
            'perspective':          chess.WHITE,
            'selected_square':      None,
            'possible_moves':       [],
            'game_over_message':    "",
            'move_history_san':     [],
            'history_scroll_offset': 0,
            'time_limit':           state_vars.get('time_limit', DEFAULT_TIME_LIMIT),
            'pause_page':           "main",
            'pending_promotion':    None,
            'clock_config':         _clock,
            'white_time':           None,
            'black_time':           None,
            'last_tick':            None,
            'toast_message':        None,
            'toast_until':          0.0,
            'save_files':           [],
            'anim':                 None,
            'analysis_index':       None,
            'analysis_board_cache': None,
        })

    reset_game()

    def draw_game_screen():
        screen.fill(COLOR_MENU_BG)
        _aidx = state_vars.get('analysis_index')
        if _aidx is not None:
            _cache = state_vars.get('analysis_board_cache')
            if _cache is None or _cache[0] != _aidx:
                _cache = (_aidx, board_at(state_vars['board'], _aidx))
                state_vars['analysis_board_cache'] = _cache
            _disp = _cache[1]
        else:
            _disp = state_vars['board']
        _last_move = _disp.peek() if _disp.move_stack else None
        draw_board(screen)
        draw_coordinates(screen, font_coords, state_vars['perspective'])
        draw_visual_aids(screen, _disp, state_vars['perspective'],
                         None if _aidx is not None else state_vars['selected_square'],
                         []   if _aidx is not None else state_vars['possible_moves'],
                         last_move=_last_move)
        draw_pieces(screen, _disp, font_pieces, state_vars['perspective'],
                    None if _aidx is not None else state_vars.get('anim'))
        thinking = ai_thread is not None and ai_thread.is_alive()
        draw_info_panel(screen, font_ui, _disp,
                        state_vars.get('white_time'), state_vars.get('black_time'), thinking)
        _sel_san = (_aidx - 1) if _aidx is not None and _aidx > 0 else None
        draw_history_panel(screen, font_ui, state_vars['move_history_san'],
                           state_vars['history_scroll_offset'], _sel_san)
        return draw_action_panel(screen, font_ui)

    running = True
    while running:
        current_state = state_vars['game_state']

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F5:
                    screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
                    state_vars['game_state'] = "REVISAO"
                elif e.key == pygame.K_ESCAPE:
                    if current_state == "JOGANDO":
                        state_vars['game_state'] = "PAUSE"
                        state_vars['pause_page'] = "main"
                        state_vars['last_tick']  = None
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
                    _aidx     = state_vars.get('analysis_index')
                    if _aidx is None:
                        _aidx = _hist_len
                    _new = max(0, _aidx - 1) if e.key == pygame.K_LEFT else min(_hist_len, _aidx + 1)
                    state_vars['analysis_index'] = _new
                    if _new > 0:
                        _sel_row   = (_new - 1) // 2
                        _max_scroll = max(0, (_hist_len + 1) // 2 - 15)
                        _cs        = state_vars['history_scroll_offset']
                        if _sel_row < _cs:
                            state_vars['history_scroll_offset'] = max(0, _sel_row)
                        elif _sel_row >= _cs + 15:
                            state_vars['history_scroll_offset'] = min(_max_scroll, _sel_row - 14)

            if e.type == pygame.MOUSEWHEEL and current_state in ("JOGANDO", "REVISAO"):
                if HISTORY_RECT.collidepoint(pygame.mouse.get_pos()):
                    state_vars['history_scroll_offset'] -= e.y
                    max_scroll = max(0, (len(state_vars['move_history_san']) + 1) // 2 - 15)
                    state_vars['history_scroll_offset'] = max(
                        0, min(state_vars['history_scroll_offset'], max_scroll)
                    )

            if e.type == pygame.MOUSEBUTTONDOWN:
                if current_state == "MENU":
                    btn_w, btn_h = 400, 60
                    menu_btn_x   = (MENU_WIDTH - btn_w) // 2
                    white_btn = pygame.Rect(menu_btn_x, MENU_HEIGHT * 0.3, btn_w, btn_h)
                    black_btn = pygame.Rect(menu_btn_x, MENU_HEIGHT * 0.5, btn_w, btn_h)
                    pvp_btn   = pygame.Rect(menu_btn_x, MENU_HEIGHT * 0.7, btn_w, btn_h)
                    tc_btn_w, tc_btn_h = 110, 40
                    tc_total = len(TIME_CONTROLS) * (tc_btn_w + 8) - 8
                    tc_x0    = (MENU_WIDTH - tc_total) // 2
                    tc_y     = 642
                    tc_clicked = False
                    for i, (_, secs) in enumerate(TIME_CONTROLS):
                        if pygame.Rect(tc_x0 + i * (tc_btn_w + 8), tc_y, tc_btn_w, tc_btn_h).collidepoint(e.pos):
                            state_vars['clock_config'] = secs
                            tc_clicked = True
                            break
                    load_btn     = pygame.Rect(menu_btn_x, 558, btn_w, 40)
                    load_clicked = False
                    if not tc_clicked and load_btn.collidepoint(e.pos):
                        saves = list_saves()
                        if saves:
                            state_vars['save_files'] = saves
                            state_vars['game_state'] = "CARREGAR"
                        load_clicked = True
                    if not tc_clicked and not load_clicked and (
                        white_btn.collidepoint(e.pos) or
                        black_btn.collidepoint(e.pos) or
                        pvp_btn.collidepoint(e.pos)
                    ):
                        _clock = state_vars.get('clock_config')
                        _t     = float(_clock) if _clock else None
                        screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
                        if white_btn.collidepoint(e.pos):
                            state_vars.update(game_mode="IA", player_color=chess.WHITE,
                                              perspective=chess.WHITE, game_state="JOGANDO",
                                              white_time=_t, black_time=_t, last_tick=None)
                        elif black_btn.collidepoint(e.pos):
                            state_vars.update(game_mode="IA", player_color=chess.BLACK,
                                              perspective=chess.BLACK, game_state="JOGANDO",
                                              white_time=_t, black_time=_t, last_tick=None)
                        elif pvp_btn.collidepoint(e.pos):
                            state_vars.update(game_mode="PvP", perspective=chess.WHITE,
                                              game_state="JOGANDO",
                                              white_time=_t, black_time=_t, last_tick=None)

                elif current_state == "JOGANDO":
                    if PAUSE_BTN.collidepoint(e.pos):
                        state_vars['game_state'] = "PAUSE"
                        state_vars['pause_page'] = "main"
                        state_vars['last_tick']  = None
                        continue
                    is_human_turn = (
                        state_vars['game_mode'] == "PvP" or
                        (state_vars['game_mode'] == "IA" and
                         state_vars['board'].turn == state_vars['player_color'])
                    )
                    if is_human_turn:
                        undo_button, reset_button = draw_action_panel(screen, font_ui)
                        if undo_button.collidepoint(e.pos):
                            state_vars['anim'] = None
                            if len(state_vars['move_history_san']) > 0:
                                state_vars['board'].pop()
                                state_vars['move_history_san'].pop()
                            if state_vars['game_mode'] == "IA" and len(state_vars['move_history_san']) > 0:
                                state_vars['board'].pop()
                                state_vars['move_history_san'].pop()
                        elif reset_button.collidepoint(e.pos):
                            reset_game()
                            continue
                        else:
                            sq = get_square_from_mouse(e.pos, state_vars['perspective'])
                            if sq is not None:
                                if state_vars['selected_square'] is None:
                                    p = state_vars['board'].piece_at(sq)
                                    if p and p.color == state_vars['board'].turn:
                                        state_vars['selected_square'] = sq
                                        state_vars['possible_moves']  = [
                                            m for m in state_vars['board'].legal_moves
                                            if m.from_square == sq
                                        ]
                                else:
                                    from_sq = state_vars['selected_square']
                                    promo_m = chess.Move(from_sq, sq, promotion=chess.QUEEN)
                                    norm_m  = chess.Move(from_sq, sq)
                                    if promo_m in state_vars['board'].legal_moves:
                                        state_vars['pending_promotion'] = (from_sq, sq)
                                        state_vars['game_state']        = "PROMOCAO"
                                    elif norm_m in state_vars['board'].legal_moves:
                                        _p   = state_vars['board'].piece_at(from_sq)
                                        _cap = state_vars['board'].is_capture(norm_m)
                                        state_vars['move_history_san'].append(
                                            state_vars['board'].san(norm_m))
                                        state_vars['board'].push(norm_m)
                                        _snd = ('check'   if state_vars['board'].is_check()
                                                else 'capture' if _cap else 'move')
                                        _s = sounds.get(_snd)
                                        if _s: _s.play()
                                        _new_persp = (state_vars['board'].turn
                                                      if state_vars['game_mode'] == "PvP" else None)
                                        state_vars['anim'] = make_anim(
                                            from_sq, sq, _p, state_vars['perspective'], _new_persp)
                                    state_vars['selected_square'] = None
                                    state_vars['possible_moves']  = []

                elif current_state == "PROMOCAO":
                    if state_vars.get('pending_promotion'):
                        from_sq, to_sq = state_vars['pending_promotion']
                        btns = draw_promotion_popup(screen, font_pieces, to_sq,
                                                    state_vars['board'].turn, state_vars['perspective'])
                        for btn, pt in btns:
                            if btn.collidepoint(e.pos):
                                m = chess.Move(from_sq, to_sq, promotion=pt)
                                if m in state_vars['board'].legal_moves:
                                    _p   = state_vars['board'].piece_at(from_sq)
                                    _cap = state_vars['board'].is_capture(m)
                                    state_vars['move_history_san'].append(state_vars['board'].san(m))
                                    state_vars['board'].push(m)
                                    _snd = ('check'   if state_vars['board'].is_check()
                                            else 'capture' if _cap else 'move')
                                    _s = sounds.get(_snd)
                                    if _s: _s.play()
                                    _new_persp = (state_vars['board'].turn
                                                  if state_vars['game_mode'] == "PvP" else None)
                                    state_vars['anim'] = make_anim(
                                        from_sq, to_sq, _p, state_vars['perspective'], _new_persp)
                                state_vars['pending_promotion'] = None
                                state_vars['game_state']        = "JOGANDO"
                                state_vars['last_tick']         = None
                                break

                elif current_state == "FIM_DE_JOGO":
                    pop_btn_w, pop_btn_h = 200, 50
                    pop_btn_y = (GAME_HEIGHT - pop_btn_h) // 2 + 60
                    see_board_btn  = pygame.Rect((GAME_WIDTH - pop_btn_w * 2 - 20) // 2,
                                                 pop_btn_y, pop_btn_w, pop_btn_h)
                    again_popup_btn = pygame.Rect(see_board_btn.right + 20,
                                                  pop_btn_y, pop_btn_w, pop_btn_h)
                    if see_board_btn.collidepoint(e.pos):
                        state_vars['game_state'] = "REVISAO"
                    elif again_popup_btn.collidepoint(e.pos):
                        reset_game()

                elif current_state == "REVISAO":
                    btn_w, btn_h = 400, 40
                    _below       = GAME_HEIGHT - BOARD_RECT.bottom
                    again_btn    = pygame.Rect(
                        (BOARD_RECT.width - btn_w) // 2 + BOARD_RECT.left,
                        BOARD_RECT.bottom + (_below - btn_h) // 2,
                        btn_w, btn_h,
                    )
                    if again_btn.collidepoint(e.pos):
                        reset_game()
                    elif HISTORY_RECT.collidepoint(e.pos):
                        _hist  = state_vars['move_history_san']
                        _num_w = 38
                        _col_w = (HISTORY_RECT.width - _num_w - 20) // 2
                        _wx    = HISTORY_RECT.left + 5 + _num_w + 5
                        _bx    = _wx + _col_w + 5
                        _ry    = e.pos[1] - (HISTORY_RECT.top + 32)
                        if _ry >= 0:
                            _row   = _ry // 28 + state_vars['history_scroll_offset']
                            _san_i = _row * 2 + (1 if e.pos[0] >= _bx else 0)
                            if _san_i < len(_hist):
                                state_vars['analysis_index'] = _san_i + 1
                                _sel_row   = _san_i // 2
                                _max_scroll = max(0, (len(_hist) + 1) // 2 - 15)
                                _cs        = state_vars['history_scroll_offset']
                                if _sel_row < _cs:
                                    state_vars['history_scroll_offset'] = max(0, _sel_row)
                                elif _sel_row >= _cs + 15:
                                    state_vars['history_scroll_offset'] = min(_max_scroll, _sel_row - 14)

                elif current_state == "CARREGAR":
                    saves = state_vars.get('save_files', [])
                    _bw, _bh, _bx = 500, 40, (MENU_WIDTH - 500) // 2
                    _loaded = False
                    for i, fname in enumerate(saves[:10]):
                        fb = pygame.Rect(_bx, 100 + i * 48, _bw, _bh)
                        if fb.collidepoint(e.pos):
                            result = import_pgn(f"{SAVES_DIR}/{fname}")
                            if result:
                                _board, _hist, _hdrs = result
                                screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
                                state_vars.update(board=_board, move_history_san=_hist,
                                                  game_state="REVISAO", perspective=chess.WHITE)
                                _wh = _hdrs.get("White", "")
                                _bh2 = _hdrs.get("Black", "")
                                if "IA" in _bh2:
                                    state_vars.update(game_mode="IA", player_color=chess.WHITE)
                                elif "IA" in _wh:
                                    state_vars.update(game_mode="IA", player_color=chess.BLACK)
                                else:
                                    state_vars['game_mode'] = "PvP"
                            _loaded = True
                            break
                    if not _loaded:
                        back_btn = pygame.Rect((MENU_WIDTH - 200) // 2, MENU_HEIGHT - 60, 200, 40)
                        if back_btn.collidepoint(e.pos):
                            state_vars['game_state'] = "MENU"

                elif current_state == "PAUSE":
                    _page = state_vars.get('pause_page', 'main')
                    btns, secondary_btn = draw_pause_menu(
                        screen, font_popup, font_ui, _page,
                        state_vars.get('time_limit', DEFAULT_TIME_LIMIT)
                    )
                    if _page == "difficulty":
                        for i, btn in enumerate(btns):
                            if btn.collidepoint(e.pos):
                                _mode   = state_vars['game_mode']
                                _color  = state_vars['player_color']
                                _persp  = state_vars['perspective']
                                _clock  = state_vars.get('clock_config')
                                _t      = float(_clock) if _clock else None
                                _tlimit = DIFFICULTY_LEVELS[i][1]
                                reset_game()
                                screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
                                state_vars.update(game_mode=_mode, player_color=_color,
                                                  perspective=_persp, game_state="JOGANDO",
                                                  time_limit=_tlimit, white_time=_t,
                                                  black_time=_t, last_tick=None)
                                break
                        else:
                            if secondary_btn and secondary_btn.collidepoint(e.pos):
                                state_vars['pause_page'] = "main"
                    else:
                        resume_btn, restart_btn, diff_btn, export_btn, menu_btn = btns
                        if resume_btn.collidepoint(e.pos):
                            state_vars['game_state'] = "JOGANDO"
                        elif restart_btn.collidepoint(e.pos):
                            _mode   = state_vars['game_mode']
                            _color  = state_vars['player_color']
                            _persp  = state_vars['perspective']
                            _tlimit = state_vars.get('time_limit', DEFAULT_TIME_LIMIT)
                            _clock  = state_vars.get('clock_config')
                            _t      = float(_clock) if _clock else None
                            reset_game()
                            screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
                            state_vars.update(game_mode=_mode, player_color=_color,
                                              perspective=_persp, game_state="JOGANDO",
                                              time_limit=_tlimit, white_time=_t,
                                              black_time=_t, last_tick=None)
                        elif diff_btn.collidepoint(e.pos):
                            state_vars['pause_page'] = "difficulty"
                        elif export_btn.collidepoint(e.pos):
                            _, fname = export_pgn(state_vars['board'], state_vars.get('game_mode'),
                                                  state_vars.get('player_color'),
                                                  state_vars.get('clock_config'))
                            state_vars['toast_message'] = f"Salvo: {fname}"
                            state_vars['toast_until']   = time.monotonic() + 3.0
                            state_vars['game_state']    = "JOGANDO"
                        elif menu_btn.collidepoint(e.pos):
                            reset_game()

        # Clock tick
        if current_state == "JOGANDO" and state_vars.get('white_time') is not None:
            _now  = time.monotonic()
            _prev = state_vars.get('last_tick')
            if _prev is not None:
                _el = _now - _prev
                if state_vars['board'].turn == chess.WHITE:
                    state_vars['white_time'] = max(0.0, state_vars['white_time'] - _el)
                else:
                    state_vars['black_time'] = max(0.0, state_vars['black_time'] - _el)
            state_vars['last_tick'] = _now

        # Resolve completed animation
        _anim = state_vars.get('anim')
        if _anim and time.monotonic() - _anim['start'] >= _anim['duration']:
            if _anim.get('flip_perspective') is not None:
                state_vars['perspective'] = _anim['flip_perspective']
            state_vars['anim'] = None

        # Start AI thread
        if current_state == "JOGANDO":
            is_human_turn = (
                state_vars['game_mode'] == "PvP" or
                (state_vars['game_mode'] == "IA" and
                 state_vars['board'].turn == state_vars['player_color'])
            )
            if (not is_human_turn and state_vars['game_mode'] == "IA"
                    and ai_move_to_make is None and ai_thread is None
                    and not state_vars.get('anim')):
                board_copy  = state_vars['board'].copy()
                _tlimit     = state_vars.get('time_limit', DEFAULT_TIME_LIMIT)
                ai_result[0] = None
                ai_thread = threading.Thread(
                    target=lambda: ai_result.__setitem__(0, find_best_ai_move(board_copy, _tlimit)),
                    daemon=True,
                )
                ai_thread.start()
            if ai_thread is not None and not ai_thread.is_alive():
                ai_move_to_make = ai_result[0]
                ai_result[0]    = None
                ai_thread       = None

        # --- Draw ---
        screen.fill(COLOR_MENU_BG)

        if current_state == "MENU":
            btn_w, btn_h = 400, 60
            menu_btn_x   = (MENU_WIDTH - btn_w) // 2
            white_btn = pygame.Rect(menu_btn_x, MENU_HEIGHT * 0.3, btn_w, btn_h)
            black_btn = pygame.Rect(menu_btn_x, MENU_HEIGHT * 0.5, btn_w, btn_h)
            pvp_btn   = pygame.Rect(menu_btn_x, MENU_HEIGHT * 0.7, btn_w, btn_h)
            draw_text(screen, "Xadrez", font_popup, COLOR_MENU_TEXT,
                      pygame.Rect(0, 0, MENU_WIDTH, int(MENU_HEIGHT * 0.3)), "center")
            pygame.draw.rect(screen, COLOR_LIGHT, white_btn)
            draw_text(screen, "Jogar de Brancas (vs IA)", font_ui, COLOR_PIECE_BLACK, white_btn, "center")
            pygame.draw.rect(screen, COLOR_DARK, black_btn)
            draw_text(screen, "Jogar de Pretas (vs IA)", font_ui, COLOR_MENU_TEXT, black_btn, "center")
            pygame.draw.rect(screen, COLOR_MENU_BG, pvp_btn, 2)
            draw_text(screen, "Jogador vs Jogador", font_ui, COLOR_MENU_TEXT, pvp_btn, "center")
            _saves_exist = bool(list_saves())
            _load_btn    = pygame.Rect(menu_btn_x, 558, btn_w, 40)
            pygame.draw.rect(screen, COLOR_DARK if _saves_exist else (55, 55, 55), _load_btn)
            draw_text(screen, "Carregar Partida", font_ui,
                      COLOR_MENU_TEXT if _saves_exist else (110, 110, 110), _load_btn, "center")
            draw_text(screen, "Relógio por jogador:", font_ui, COLOR_COORD,
                      pygame.Rect(0, 615, MENU_WIDTH, 28), "center")
            tc_btn_w, tc_btn_h = 110, 40
            tc_total = len(TIME_CONTROLS) * (tc_btn_w + 8) - 8
            tc_x0    = (MENU_WIDTH - tc_total) // 2
            tc_y     = 642
            for i, (label, secs) in enumerate(TIME_CONTROLS):
                tc_btn = pygame.Rect(tc_x0 + i * (tc_btn_w + 8), tc_y, tc_btn_w, tc_btn_h)
                is_sel = state_vars.get('clock_config') == secs
                pygame.draw.rect(screen, (180, 130, 40) if is_sel else COLOR_DARK, tc_btn)
                if is_sel:
                    pygame.draw.rect(screen, COLOR_MENU_TEXT, tc_btn, 2)
                draw_text(screen, label, font_ui, COLOR_MENU_TEXT, tc_btn, "center")

        elif current_state in ("JOGANDO", "REVISAO", "PROMOCAO"):
            draw_game_screen()
            if current_state == "PROMOCAO" and state_vars.get('pending_promotion'):
                draw_promotion_popup(screen, font_pieces,
                                     state_vars['pending_promotion'][1],
                                     state_vars['board'].turn, state_vars['perspective'])
            if current_state == "REVISAO":
                btn_w, btn_h = 400, 40
                _below       = GAME_HEIGHT - BOARD_RECT.bottom
                again_btn    = pygame.Rect(
                    (BOARD_RECT.width - btn_w) // 2 + BOARD_RECT.left,
                    BOARD_RECT.bottom + (_below - btn_h) // 2,
                    btn_w, btn_h,
                )
                pygame.draw.rect(screen, COLOR_DARK, again_btn)
                draw_text(screen, "Ir para o Menu", font_ui, COLOR_MENU_TEXT, again_btn, "center")
                _aidx_r = state_vars.get('analysis_index')
                _hlen   = len(state_vars['move_history_san'])
                _pos_n  = _aidx_r if _aidx_r is not None else _hlen
                pygame.draw.rect(screen, COLOR_MENU_BG, ACTION_PANEL_RECT)
                draw_text(screen, f"Posição  {_pos_n} / {_hlen}", font_ui, COLOR_COORD,
                          pygame.Rect(ACTION_PANEL_RECT.x, ACTION_PANEL_RECT.y + 12,
                                      ACTION_PANEL_RECT.width, 28), "center")
                draw_text(screen, "← →  navegar   |   ESC: final", font_ui, COLOR_COORD,
                          pygame.Rect(ACTION_PANEL_RECT.x, ACTION_PANEL_RECT.y + 50,
                                      ACTION_PANEL_RECT.width, 28), "center")
                draw_text(screen, "Clique no histórico para ir ao movimento", font_ui, COLOR_COORD,
                          pygame.Rect(ACTION_PANEL_RECT.x, ACTION_PANEL_RECT.y + 88,
                                      ACTION_PANEL_RECT.width, 28), "center")

        elif current_state == "PAUSE":
            draw_game_screen()
            draw_pause_menu(screen, font_popup, font_ui,
                            state_vars.get('pause_page', 'main'),
                            state_vars.get('time_limit', DEFAULT_TIME_LIMIT))

        elif current_state == "FIM_DE_JOGO":
            draw_game_screen()
            pop_btn_w, pop_btn_h = 200, 50
            pop_btn_y = (GAME_HEIGHT - pop_btn_h) // 2 + 60
            see_board_btn   = pygame.Rect((GAME_WIDTH - pop_btn_w * 2 - 20) // 2,
                                          pop_btn_y, pop_btn_w, pop_btn_h)
            again_popup_btn = pygame.Rect(see_board_btn.right + 20, pop_btn_y, pop_btn_w, pop_btn_h)
            draw_game_over_popup(screen, font_popup, font_popup_sub,
                                 state_vars['game_over_message'],
                                 see_board_btn, again_popup_btn)

        elif current_state == "CARREGAR":
            screen.fill(COLOR_MENU_BG)
            draw_text(screen, "Carregar Partida", font_popup, COLOR_MENU_TEXT,
                      pygame.Rect(0, 20, MENU_WIDTH, 60), "center")
            _saves = state_vars.get('save_files', [])
            if not _saves:
                draw_text(screen, "Nenhuma partida encontrada.", font_ui, COLOR_COORD,
                          pygame.Rect(0, 120, MENU_WIDTH, 40), "center")
            else:
                _bw, _bh, _bx = 500, 40, (MENU_WIDTH - 500) // 2
                for i, fname in enumerate(_saves[:10]):
                    fb = pygame.Rect(_bx, 100 + i * 48, _bw, _bh)
                    pygame.draw.rect(screen, COLOR_DARK, fb)
                    label = fname.replace("partida_", "").replace(".pgn", "").replace("_", "  ")
                    draw_text(screen, label, font_ui, COLOR_MENU_TEXT, fb, "center")
            back_btn = pygame.Rect((MENU_WIDTH - 200) // 2, MENU_HEIGHT - 60, 200, 40)
            pygame.draw.rect(screen, COLOR_MENU_BG, back_btn, 2)
            draw_text(screen, "Voltar", font_ui, COLOR_MENU_TEXT, back_btn, "center")

        # Toast notification
        if state_vars.get('toast_until', 0.0) > time.monotonic():
            _tmsg  = state_vars.get('toast_message') or ''
            _tsurf = font_ui.render(_tmsg, True, COLOR_MENU_TEXT)
            _tw    = _tsurf.get_width() + 24
            _tx    = (screen.get_width() - _tw) // 2
            _tbg   = pygame.Surface((_tw, 36), pygame.SRCALPHA)
            _tbg.fill((20, 20, 20, 210))
            screen.blit(_tbg,  (_tx, 6))
            screen.blit(_tsurf, _tsurf.get_rect(centerx=_tx + _tw // 2, centery=24))

        pygame.display.flip()

        # Apply AI move
        if ai_move_to_make and current_state == "JOGANDO" and not state_vars.get('anim'):
            _p   = state_vars['board'].piece_at(ai_move_to_make.from_square)
            _cap = state_vars['board'].is_capture(ai_move_to_make)
            state_vars['move_history_san'].append(state_vars['board'].san(ai_move_to_make))
            state_vars['board'].push(ai_move_to_make)
            _snd = ('check' if state_vars['board'].is_check() else 'capture' if _cap else 'move')
            _s   = sounds.get(_snd)
            if _s: _s.play()
            state_vars['anim'] = make_anim(
                ai_move_to_make.from_square, ai_move_to_make.to_square,
                _p, state_vars['perspective']
            )
            ai_move_to_make = None

        # Clock timeout
        if current_state == "JOGANDO" and state_vars.get('white_time') is not None:
            if state_vars['white_time'] <= 0:
                state_vars['game_state']       = "FIM_DE_JOGO"
                state_vars['game_over_message'] = "Tempo esgotado!\nPretas vencem."
                _s = sounds.get('game_end')
                if _s: _s.play()
            elif state_vars['black_time'] <= 0:
                state_vars['game_state']       = "FIM_DE_JOGO"
                state_vars['game_over_message'] = "Tempo esgotado!\nBrancas vencem."
                _s = sounds.get('game_end')
                if _s: _s.play()

        # Game over detection
        if current_state == "JOGANDO" and state_vars['board'].is_game_over():
            state_vars['game_state'] = "FIM_DE_JOGO"
            b = state_vars['board']
            if b.is_checkmate():
                w = "Brancas" if not b.turn else "Pretas"
                state_vars['game_over_message'] = f"Xeque-mate!\n{w} vencem."
            elif b.is_stalemate():
                state_vars['game_over_message'] = "Empate!\n(Rei Afogado)"
            elif b.is_insufficient_material():
                state_vars['game_over_message'] = "Empate!\n(Material Insuficiente)"
            elif b.is_seventyfive_moves():
                state_vars['game_over_message'] = "Empate!\n(Regra dos 75 Movimentos)"
            else:
                state_vars['game_over_message'] = "Empate!\n(Repetição)"
            _s = sounds.get('game_end')
            if _s: _s.play()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
