# main.py - 星际征途探索强手棋 主程序入口

import sys
import os
import random
import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import lang as _lang
from data import COLORS, PLANETS
from game import GameState, GamePhase
from ui import (
    SCREEN_W, SCREEN_H, PANEL_X, PANEL_W, BOARD_DISP_W, BOARD_DISP_SCALE,
    CARD_POP_W, CARD_POP_H, _TOKEN_R,
    init_assets, init_music, toggle_music, toggle_debug_cells,
    reload_board_image,
    draw_board, draw_panel, draw_card_popup,
    draw_start_screen, draw_game_over, draw_planet_picker, draw_player_picker,
    draw_planet_card_popup, draw_fund_notice, draw_skip_notice,
    draw_exp_type_picker,
    draw_reposition_overlay, draw_debug_input,
    get_token_pos, nearest_cell,
    Button, draw_text,
    trigger_step_flash,
)

# ─────────────────────────────
# 按钮布局
# ─────────────────────────────
BTN_X = PANEL_X + 10
BTN_W = PANEL_W - 20
BTN_H = 54

def make_button(label, row, color=None):
    y = SCREEN_H - 300 + row * (BTN_H + 10)
    return Button((BTN_X, y, BTN_W, BTN_H), label, color=color)

# ─────────────────────────────
# 游戏主循环
# ─────────────────────────────
def run_game(num_players):
    gs = GameState(num_players)
    gs.message = _lang.t("msg_start", name=gs.current_player.name)
    clock  = pygame.time.Clock()
    screen = pygame.display.get_surface()

    picker_active = False
    picker_title  = ""
    picker_mode   = ""   # "mortgage" | "lab" | "exp_type" | "earth"
    pending_exp_pid = -1  # 等待选择实验类型时记录的星球 ID

    # ── 调配探索者拖拽状态 ────────────────────
    reposition_drag_pid = None   # 正在拖拽的玩家 id
    reposition_drag_pos = None   # 当前鼠标位置

    # ── 调试快捷键状态 ────────────────────────
    debug_input_active = False   # Ctrl+G 输入模式
    debug_input_buf    = ""      # 当前输入的数字字符串

    # ── 动画状态 ──────────────────────────────
    DICE_SPIN_FRAMES = 24   # 骰子滚动帧数 (~800ms @30fps)
    MOVE_STEP_FRAMES = 8    # 每格移动帧数 (~267ms @30fps)

    anim_phase  = None   # None | "dice" | "move" | "jail"
    anim_frame  = 0      # 当前阶段剩余帧
    anim_steps  = 0      # 剩余移动格数
    anim_dir    = 1      # 移动方向 +1/-1
    anim_earth  = 0      # 本次动画中经过地球次数
    anim_d1     = 0      # 动画中显示的骰子值
    anim_d2     = 0

    while True:
        clock.tick(30)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                toggle_music()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                toggle_debug_cells()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                _LANG_BTN = pygame.Rect(SCREEN_W - 90, SCREEN_H - 46, 80, 36)
                if _LANG_BTN.collidepoint(event.pos):
                    _lang.set_lang("en" if _lang.get_lang() == "zh" else "zh")
                    reload_board_image()
                    for p in gs.players:
                        p.name = _lang.player_name(p.id)

            # ── 调试快捷键 ──────────────────────────
            if event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                ctrl = mods & pygame.KMOD_CTRL
                if debug_input_active:
                    if event.key == pygame.K_ESCAPE:
                        debug_input_active = False
                        debug_input_buf    = ""
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if debug_input_buf.isdigit() and int(debug_input_buf) > 0:
                            anim_phase = None; anim_frame = 0
                            picker_active = False
                            reposition_drag_pid = None; reposition_drag_pos = None
                            gs.debug_advance(int(debug_input_buf))
                        debug_input_active = False
                        debug_input_buf    = ""
                    elif event.key == pygame.K_BACKSPACE:
                        debug_input_buf = debug_input_buf[:-1]
                    elif event.unicode.isdigit():
                        debug_input_buf += event.unicode
                elif ctrl and event.key == pygame.K_g:
                    if gs.phase != GamePhase.GAME_OVER:
                        debug_input_active = True
                        debug_input_buf    = ""
                elif ctrl and event.key == pygame.K_j:
                    if gs.phase != GamePhase.GAME_OVER:
                        anim_phase = None; anim_frame = 0
                        picker_active = False
                        reposition_drag_pid = None; reposition_drag_pos = None
                        gs.debug_goto_next("chance")
                elif ctrl and event.key == pygame.K_e:
                    if gs.phase != GamePhase.GAME_OVER:
                        anim_phase = None; anim_frame = 0
                        picker_active = False
                        reposition_drag_pid = None; reposition_drag_pos = None
                        gs.debug_goto_next("event")

        # ── 动画帧更新 ──────────────────────────
        if anim_phase == "dice":
            anim_frame -= 1
            anim_d1 = random.randint(1, 6)
            anim_d2 = random.randint(1, 6)
            if anim_frame <= 0:
                anim_d1, anim_d2 = gs.dice          # 定格为真实骰子值
                steps, direction, instant = gs.begin_roll()
                if instant == "jail":
                    anim_phase = "jail"
                    anim_frame = 30                  # 停留约1s显示消息
                elif steps > 0:
                    anim_phase = "move"
                    anim_steps = steps
                    anim_dir   = direction
                    anim_frame = MOVE_STEP_FRAMES
                    anim_earth = 0
                else:
                    anim_phase = None
                    gs.finish_roll(0)

        elif anim_phase == "jail":
            anim_frame -= 1
            if anim_frame <= 0:
                anim_phase = None
                gs.end_jail_turn()

        elif anim_phase == "move":
            anim_frame -= 1
            if anim_frame <= 0:
                player  = gs.current_player
                old_pos = player.pos
                player.pos = (player.pos + anim_dir) % 32
                # 经过地球检测（正向绕过0点 或 反向绕过0点）
                if anim_dir > 0 and player.pos < old_pos:
                    anim_earth += 1
                elif anim_dir < 0 and player.pos > old_pos:
                    anim_earth += 1
                anim_steps -= 1
                if anim_steps <= 0:
                    anim_phase = None
                    gs.finish_roll(anim_earth)
                else:
                    anim_frame = MOVE_STEP_FRAMES

        # ── 按钮列表（动画中隐藏按钮防误触）──────
        buttons = [] if anim_phase is not None else _make_buttons(gs)

        # ── 事件处理（仅在无动画时响应）──────────
        if anim_phase is None:
            if gs.phase == GamePhase.FUND_NOTICE:
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        # 计算确认按钮位置（与 draw_fund_notice 一致）
                        PAD, ROW_H, TITLE_H, BTN_H, POP_W = 28, 76, 44, 44, 560
                        POP_H = TITLE_H + PAD + len(gs.fund_events) * ROW_H + PAD + BTN_H + PAD
                        ox = (BOARD_DISP_W - POP_W) // 2
                        oy = (SCREEN_H - POP_H) // 2
                        btn_rect = pygame.Rect(ox + POP_W // 2 - 70,
                                               oy + POP_H - BTN_H - PAD // 2, 140, BTN_H)
                        if btn_rect.collidepoint(event.pos):
                            gs.confirm_fund_notice()
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        gs.confirm_fund_notice()

            elif gs.phase == GamePhase.GAME_OVER:
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        restart_rect = pygame.Rect(SCREEN_W // 2 - 90,
                                                   SCREEN_H // 2 + 160, 180, 52)
                        if restart_rect.collidepoint(event.pos):
                            return True

            elif gs.phase == GamePhase.REPOSITION:
                TOKEN_R = _TOKEN_R + 8
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        # 优先检查确认按钮
                        btn_hit = False
                        for btn, action in buttons:
                            if btn.is_clicked(event) and action == "reposition_ok":
                                gs.confirm_reposition()
                                reposition_drag_pid = None
                                reposition_drag_pos = None
                                btn_hit = True
                                break
                        if btn_hit:
                            continue
                        # 检查是否点中其他玩家棋子
                        for p in gs.players:
                            if p.bankrupt or p.id == gs.current_player.id:
                                continue
                            tx, ty = get_token_pos(gs, p.id)
                            if (event.pos[0]-tx)**2 + (event.pos[1]-ty)**2 <= TOKEN_R**2:
                                reposition_drag_pid = p.id
                                reposition_drag_pos = event.pos
                                break

                    elif event.type == pygame.MOUSEMOTION:
                        if reposition_drag_pid is not None:
                            reposition_drag_pos = event.pos

                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        if reposition_drag_pid is not None:
                            cell = nearest_cell(*event.pos)
                            gs.reposition_move(reposition_drag_pid, cell)
                            reposition_drag_pid = None
                            reposition_drag_pos = None

            elif picker_active:
                _PLAYER_MODES = ("give_fund_player", "swap_player")
                _SWAP_PLANET_MODES = ("swap_mine", "swap_theirs")
                for event in events:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        picker_active = False
                        pending_exp_pid = -1
                        if picker_mode in ("lab", "exp_type"):
                            gs.skip_lab()
                        elif picker_mode == "earth":
                            gs.skip_earth_upgrade()
                        elif picker_mode in ("explore_free", "give_fund_player",
                                             "swap_player", "swap_mine", "swap_theirs"):
                            gs._end_turn_or_extra()
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if picker_mode == "exp_type":
                            exp_btns = _get_exp_type_buttons(gs, pending_exp_pid)
                            for btn, exp_idx in exp_btns:
                                if btn.rect.collidepoint(event.pos):
                                    gs.do_experiment(pending_exp_pid, exp_idx)
                                    picker_active = False
                                    pending_exp_pid = -1
                                    break
                        elif picker_mode in _PLAYER_MODES:
                            player_btns = _get_player_picker_buttons(gs)
                            for btn, target_id in player_btns:
                                if btn.rect.collidepoint(event.pos):
                                    if picker_mode == "give_fund_player":
                                        gs.confirm_give_fund(target_id)
                                        picker_active = False
                                    elif picker_mode == "swap_player":
                                        gs.confirm_swap_target(target_id)
                                        picker_mode  = "swap_mine"
                                        picker_title = gs.message
                                    break
                        else:
                            for_pid = gs._swap_target_id if picker_mode == "swap_theirs" else -1
                            planet_btns = _get_picker_buttons(gs, picker_mode, for_player_id=for_pid)
                            for btn, pid in planet_btns:
                                if btn.rect.collidepoint(event.pos):
                                    if picker_mode == "mortgage":
                                        gs.mortgage_planet(pid)
                                        picker_active = (gs.phase == GamePhase.MORTGAGE)
                                    elif picker_mode == "lab":
                                        exp_types = gs.get_planet_exp_types(pid)
                                        if len(exp_types) > 1:
                                            pending_exp_pid = pid
                                            picker_mode  = "exp_type"
                                            picker_title = _lang.t("picker_exp_type", name=gs.current_player.name)
                                        else:
                                            gs.do_experiment(pid, exp_types[0] if exp_types else -1)
                                            picker_active = False
                                    elif picker_mode == "earth":
                                        gs.do_earth_upgrade(pid)
                                        picker_active = False
                                    elif picker_mode == "explore_free":
                                        gs.confirm_explore_free(pid)
                                        picker_active = False
                                    elif picker_mode == "swap_mine":
                                        gs.confirm_swap_my_planet(pid)
                                        picker_mode  = "swap_theirs"
                                        picker_title = gs.message
                                    elif picker_mode == "swap_theirs":
                                        gs.confirm_swap_complete(pid)
                                        picker_active = False
                                    break

            else:
                for event in events:
                    for btn, action in buttons:
                        if btn.is_clicked(event):
                            if action == "roll":
                                gs.roll_dice()
                                anim_phase = "dice"
                                anim_frame = DICE_SPIN_FRAMES
                                anim_d1    = random.randint(1, 6)
                                anim_d2    = random.randint(1, 6)
                            else:
                                _handle_action(gs, action)
                                if gs.phase == GamePhase.MORTGAGE:
                                    picker_active = True
                                    picker_title  = _lang.t("picker_mortgage")
                                    picker_mode   = "mortgage"
                                elif action == "lab" and gs.phase == GamePhase.LAB:
                                    all_plist = gs.get_player_planet_list(gs.current_player)
                                    show_planets = [
                                        pl for pl in all_plist
                                        if pl.get("has_exp") and pl["level"] < 4
                                    ]
                                    if show_planets:
                                        picker_active = True
                                        picker_title  = _lang.t("picker_lab")
                                        picker_mode   = "lab"
                                    else:
                                        gs.skip_lab()
                                elif action == "earth_upgrade" and gs.phase == GamePhase.EARTH_UPGRADE:
                                    up_planets = [
                                        pl for pl in gs.get_player_planet_list(gs.current_player)
                                        if pl["upgrade"] > 0
                                    ]
                                    if up_planets:
                                        picker_active = True
                                        picker_title  = _lang.t("picker_earth")
                                        picker_mode   = "earth"
                                    else:
                                        gs.skip_earth_upgrade()
                                elif gs.phase == GamePhase.EXPLORE_FREE:
                                    picker_active = True
                                    picker_title  = _lang.t("picker_explore")
                                    picker_mode   = "explore_free"
                                elif gs.phase == GamePhase.GIVE_FUND:
                                    picker_active = True
                                    picker_title  = gs.message
                                    picker_mode   = "give_fund_player"
                                elif gs.phase == GamePhase.SWAP_PLAYER:
                                    picker_active = True
                                    picker_title  = gs.message
                                    picker_mode   = "swap_player"
                            break

        # ── 绘制 ────────────────────────────────
        display_dice = (anim_d1, anim_d2) if anim_phase else None

        screen.fill((5, 8, 20))
        draw_board(screen, gs,
                   skip_pid=reposition_drag_pid if gs.phase == GamePhase.REPOSITION else None)

        if gs.phase != GamePhase.GAME_OVER:
            draw_panel(screen, gs, [btn for btn, _ in buttons],
                       display_dice=display_dice)

        if gs.phase == GamePhase.CARD and gs.current_card is not None:
            draw_card_popup(screen, gs)
            for btn, _ in buttons:
                btn.draw(screen)

        if gs.phase == GamePhase.REPOSITION:
            draw_reposition_overlay(screen, gs, reposition_drag_pid, reposition_drag_pos)
            for btn, _ in buttons:
                btn.draw(screen)

        _PLANET_PHASES = (GamePhase.PLANET_BUY, GamePhase.PLANET_PAY,
                          GamePhase.PLANET_UP,  GamePhase.PLANET_TRADE)
        if gs.phase in _PLANET_PHASES and anim_phase is None and not picker_active:
            draw_planet_card_popup(screen, gs)

        if picker_active:
            _PLAYER_MODES = ("give_fund_player", "swap_player")
            if picker_mode == "exp_type":
                done_exps = gs.current_player.planet_exps.get(pending_exp_pid, [False, False, False])
                draw_exp_type_picker(screen, picker_title, pending_exp_pid, done_exps=done_exps)
            elif picker_mode in _PLAYER_MODES:
                draw_player_picker(screen, gs, picker_title)
            elif picker_mode == "swap_theirs":
                draw_planet_picker(screen, gs, picker_title, picker_mode,
                                   for_player_id=gs._swap_target_id)
            else:
                draw_planet_picker(screen, gs, picker_title, picker_mode)

        if gs.phase == GamePhase.GAME_OVER:
            draw_game_over(screen, gs)

        if gs.phase == GamePhase.FUND_NOTICE and anim_phase is None:
            btn_rect = draw_fund_notice(screen, gs)
            if btn_rect:
                ok_btn = Button(btn_rect, _lang.t("fund_ok"),
                                color=(40, 140, 60), hover_color=(60, 180, 80))
                ok_btn.draw(screen)

        if gs.phase == GamePhase.SKIP_NOTICE and anim_phase is None:
            btn_rect = draw_skip_notice(screen, gs)
            if btn_rect:
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_rect.collidepoint(event.pos):
                            gs.confirm_skip_notice()

        if debug_input_active:
            draw_debug_input(screen, debug_input_buf)

        # 语言切换按钮（右下角，任何阶段均可点击）
        lang_label = "EN" if _lang.get_lang() == "zh" else "中文"
        lang_btn = Button((SCREEN_W - 90, SCREEN_H - 46, 80, 36), lang_label,
                          color=(35, 55, 110), hover_color=(55, 85, 160))
        lang_btn.draw(screen)

        pygame.display.flip()


def _get_exp_type_buttons(gs, planet_id):
    """实验类型选择弹窗的点击区域：所有支持类型按序布局，已完成的不生成可点击区域。"""
    from ui import _EXP_BTN_COL
    from data import PLANETS
    exps = PLANETS.get(planet_id, {}).get("experiments", [])
    all_types = [i for i, v in enumerate(exps) if v]
    done_exps = gs.current_player.planet_exps.get(planet_id, [False, False, False])
    ROW_H = 48
    ow    = 380
    oh    = 54 + len(all_types) * (ROW_H + 10) + 10
    ox    = (BOARD_DISP_W - ow) // 2
    oy    = (SCREEN_H - oh) // 2
    buttons = []
    by = oy + 52
    for idx in all_types:
        if not done_exps[idx]:
            r = pygame.Rect(ox + 20, by, ow - 40, ROW_H)
            buttons.append((Button(r, _lang.exp_name(idx), color=_EXP_BTN_COL[idx]), idx))
        by += ROW_H + 10
    return buttons


# ─────────────────────────────
# ─────────────────────────────
def _get_player_picker_buttons(gs):
    """玩家选择弹窗的点击区域（与 draw_player_picker 布局一致）"""
    others = [p for p in gs.players
              if not p.bankrupt and p.id != gs.current_player.id]
    ow = 380
    oh = 54 + len(others) * 52 + 20
    ox = (BOARD_DISP_W - ow) // 2
    oy = (SCREEN_H - oh) // 2
    buttons = []
    by = oy + 46
    for p in others:
        r = pygame.Rect(ox + 20, by, ow - 40, 40)
        buttons.append((Button(r, ""), p.id))
        by += 52
    return buttons


def _get_picker_buttons(gs, picker_mode="", for_player_id=-1):
    ow, oh = 400, 300
    ox = (BOARD_DISP_W - ow) // 2
    oy = (SCREEN_H - oh) // 2
    if picker_mode == "explore_free":
        planets = gs.get_unclaimed_planet_list()
    elif for_player_id >= 0:
        planets = gs.get_player_planet_list(gs.players[for_player_id])
    else:
        planets = gs.get_player_planet_list(gs.current_player)
    if picker_mode == "lab":
        planets = [pl for pl in planets if pl.get("has_exp") and pl["level"] < 4]
    elif picker_mode == "earth":
        planets = [pl for pl in planets if pl["upgrade"] > 0]
    buttons = []
    by = oy + 44
    for pl in planets:
        r = pygame.Rect(ox + 20, by, ow - 40, 32)
        if picker_mode == "lab" and not pl.get("can_exp"):
            pass  # 已完成的星球不生成点击区域
        else:
            buttons.append((Button(r, ""), pl["planet_id"]))
        by += 38
    return buttons


# ─────────────────────────────
# 按钮生成
# ─────────────────────────────
def _make_buttons(gs: GameState):
    phase = gs.phase
    btns  = []

    if phase == GamePhase.ROLL:
        btns.append((make_button(_lang.t("btn_roll"), 0, color=(50, 120, 200)), "roll"))

    elif phase == GamePhase.PLANET_BUY:
        btns.append((make_button(_lang.t("btn_buy"),  0, color=(40, 140, 60)),  "buy"))
        btns.append((make_button(_lang.t("btn_skip"), 1),                        "skip"))

    elif phase == GamePhase.PLANET_PAY:
        cp = gs.current_player
        row = 0
        if cp.keep_cards > 0:
            btns.append((make_button(_lang.t("btn_use_card", n=cp.keep_cards),
                                     row, color=(80, 60, 160)), "use_card"))
            row += 1
        btns.append((make_button(_lang.t("btn_pay"), row, color=(160, 60, 40)), "pay"))

    elif phase == GamePhase.PLANET_TRADE:
        pid = gs.pending_pid
        cost = 0
        if pid >= 0:
            owner = gs._find_planet_owner(pid)
            if owner is not None:
                lv = owner.planets[pid]
                cost = PLANETS[pid]["levels"][lv]["trade"]
        btns.append((make_button(_lang.t("btn_trade", cost=cost), 0, color=(40, 140, 120)), "trade"))
        btns.append((make_button(_lang.t("btn_skip_trade"),        1),                       "skip_trade"))

    elif phase == GamePhase.PLANET_UP:
        btns.append((make_button(_lang.t("btn_upgrade"), 0, color=(40, 140, 60)), "upgrade"))
        btns.append((make_button(_lang.t("btn_skip"),    1),                       "skip"))

    elif phase == GamePhase.EARTH_UPGRADE:
        btns.append((make_button(_lang.t("btn_earth_up"),  0, color=(180, 140, 20)), "earth_upgrade"))
        btns.append((make_button(_lang.t("btn_skip_earth"),1),                        "skip_earth"))

    elif phase == GamePhase.REPOSITION:
        moves = gs._reposition_moves
        if moves > 0:
            label = _lang.t("btn_repo_n", n=moves)
        else:
            label = _lang.t("btn_repo_0")
        btns.append((make_button(label, 0, color=(40, 140, 60)), "reposition_ok"))

    elif phase == GamePhase.CARD:
        # 确认按钮放在卡片弹窗内底部
        pop_y  = (SCREEN_H - CARD_POP_H) // 2
        btn_y  = pop_y + CARD_POP_H - 58
        card = gs.current_card
        # 事件卡12"一次机会" → 二选一
        if (card and card.get("_type") == "event" and card.get("id") == 12):
            r1 = pygame.Rect(BOARD_DISP_W // 2 - 215, btn_y, 200, 44)
            r2 = pygame.Rect(BOARD_DISP_W // 2 + 15,  btn_y, 200, 44)
            btns.append((Button(r1, _lang.t("btn_ch_roll"),
                                color=(50, 120, 200), hover_color=(70, 150, 230)), "chance_roll"))
            btns.append((Button(r2, _lang.t("btn_ch_draw"),
                                color=(20, 130, 60),  hover_color=(30, 160, 80)),  "chance_draw"))
        else:
            r = pygame.Rect(BOARD_DISP_W // 2 - 100, btn_y, 200, 44)
            btns.append((Button(r, _lang.t("btn_card_ok"),
                                color=(40, 140, 60), hover_color=(60, 180, 80)), "card_ok"))

    elif phase == GamePhase.LAB:
        btns.append((make_button(_lang.t("btn_lab"),     0, color=(100, 40, 160)), "lab"))
        btns.append((make_button(_lang.t("btn_skip_lab"),1),                       "skip_lab"))

    elif phase == GamePhase.MORTGAGE:
        btns.append((make_button(_lang.t("btn_mortgage"), 0, color=(160, 80, 40)), "mortgage"))

    elif phase == GamePhase.BANKRUPT:
        btns.append((make_button(_lang.t("btn_next"), 0), "next"))

    elif phase == GamePhase.FUND_NOTICE:
        pass   # 按钮由 draw loop 单独绘制

    return btns


# ─────────────────────────────
# 动作处理
# ─────────────────────────────
def _handle_action(gs: GameState, action: str):
    # "roll" 由 run_game 动画分支直接处理，不经过这里
    if   action == "buy":           gs.confirm_buy_planet()
    elif action == "skip":          gs._end_turn_or_extra()
    elif action == "pay":           gs.confirm_pay_toll(use_keep_card=False)
    elif action == "use_card":      gs.confirm_pay_toll(use_keep_card=True)
    elif action == "upgrade":       gs.confirm_upgrade_planet()
    elif action == "trade":         gs.confirm_trade()
    elif action == "skip_trade":    gs.skip_trade()
    elif action == "reposition_ok": gs.confirm_reposition()
    elif action == "earth_upgrade": pass   # 由弹窗处理
    elif action == "skip_earth":    gs.skip_earth_upgrade()
    elif action == "card_ok":       gs.apply_card()
    elif action == "chance_roll":   gs.apply_card_chance("roll")
    elif action == "chance_draw":   gs.apply_card_chance("draw")
    elif action == "skip_lab":      gs.skip_lab()
    elif action == "next":          gs._next_player()
    elif action == "fund_ok":       gs.confirm_fund_notice()
    # "lab", "mortgage", "earth_upgrade" 由弹窗处理，不在这里


# ─────────────────────────────
# 开始界面
# ─────────────────────────────
def run_start_screen():
    screen   = pygame.display.get_surface()
    clock    = pygame.time.Clock()
    selected = 2
    while True:
        clock.tick(30)
        screen.fill((5, 10, 30))
        icon_areas, start_btn, zh_r, en_r = draw_start_screen(screen, selected)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if zh_r.collidepoint(event.pos):
                    _lang.set_lang("zh")
                    reload_board_image()
                    continue
                if en_r.collidepoint(event.pos):
                    _lang.set_lang("en")
                    reload_board_image()
                    continue
                for rect, n in icon_areas:
                    if rect.collidepoint(event.pos):
                        selected = max(2, n)
                        break
            if start_btn.is_clicked(event):
                return selected


# ─────────────────────────────
# 程序入口
# ─────────────────────────────
def main():
    pygame.init()
    pygame.display.set_caption("Space Chess: Cosmic Explorer / 星际征途探索强手棋")
    pygame.display.set_mode((SCREEN_W, SCREEN_H))
    init_assets()   # 加载棋盘图片和字体
    init_music()    # 加载背景音乐（需 assets/bgm.mp3）

    while True:
        num_players = run_start_screen()
        restart = run_game(num_players)
        if not restart:
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
