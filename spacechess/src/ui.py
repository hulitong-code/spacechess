# ui.py - 星际征途探索强手棋 pygame 界面

import os, math
import pygame
from data import BOARD, PLANETS, CELL_PLANET_ID, COLORS, MAX_PLAYERS
from game import GamePhase
import lang as _lang

# ─────────────────────────────
# 屏幕与棋盘常量
# ─────────────────────────────
SCREEN_W  = 1200
SCREEN_H  = 900

# 棋盘图片尺寸（原始 PNG 994×1000）
BOARD_PNG_W = 994
BOARD_PNG_H = 1000

BOARD_DISP_H    = SCREEN_H
BOARD_DISP_W    = int(BOARD_PNG_W * BOARD_DISP_H / BOARD_PNG_H)   # ~1193
BOARD_DISP_SCALE = BOARD_DISP_H / BOARD_PNG_H                      # 1.2
PANEL_X   = BOARD_DISP_W + 8
PANEL_W   = SCREEN_W - PANEL_X - 8

# 资源路径
ASSETS_DIR   = os.path.join(os.path.dirname(__file__), "..", "assets")
BG_DIR       = os.path.join(ASSETS_DIR, "background")
BOARD_PNG    = os.path.join(BG_DIR, "board.png")
BOARD_EN_PNG = os.path.join(BG_DIR, "board_en.png")

# ─────────────────────────────
# 格子的 Scratch 坐标（从 Scratch 项目直接提取）
# 索引 0 = 格子1（地球），索引 31 = 格子32（月球）
# ─────────────────────────────
SCRATCH_COORDS = [
    ( 259,  321), ( 259,  174), ( 259,   73), ( 259,  -25),
    ( 259, -127), ( 259, -226), ( 259, -333), ( 259, -433),
    ( 259, -538), ( 122, -536), (  19, -536), ( -82, -533),
    (-186, -533), (-290, -533), (-387, -533), (-490, -533),
    (-590, -533), (-590, -433), (-590, -334), (-590, -228),
    (-590, -130), (-590,  -30), (-590,   68), (-590,  171),
    (-590,  317), (-495,  317), (-390,  317), (-289,  317),
    (-185,  317), ( -87,  317), (  19,  317), ( 121,  319),
]

CELL_MARGIN_X = 69   # 棋盘图片左右边缘到格子中心的距离（像素，标定值）
CELL_MARGIN_Y = 75   # 棋盘图片上下边缘到格子中心的距离（像素，标定值）

def scratch_to_board_px(sx, sy):
    """Scratch坐标 → 屏幕像素坐标（棋盘上的格子中心）
    Scratch y轴向上为正，图片y轴向下为正：
      img_x = (259-sx) / 849 * (W-2*Mx) + Mx
      img_y = (sy+538) / 859 * (H-2*My) + My
    """
    Mx, My = CELL_MARGIN_X, CELL_MARGIN_Y
    img_x = (259 - sx) / 849 * (BOARD_PNG_W - 2 * Mx) + Mx
    img_y = (sy + 538) / 859 * (BOARD_PNG_H - 2 * My) + My
    return int(img_x * BOARD_DISP_SCALE), int(img_y * BOARD_DISP_SCALE)

# 32格中心坐标（4角标定 + 线性插值，原始图片像素，×BOARD_DISP_SCALE得屏幕坐标）
CELL_CENTERS_IMG = [
    ( 70.0, 928.2),  # 格1  地球
    ( 69.8, 821.0),  # 格2
    ( 69.7, 713.8),  # 格3
    ( 69.5, 606.6),  # 格4
    ( 69.4, 499.4),  # 格5
    ( 69.2, 392.2),  # 格6
    ( 69.1, 285.0),  # 格7
    ( 69.0, 177.8),  # 格8
    ( 68.8,  70.6),  # 格9
    (175.2,  70.8),  # 格10
    (281.6,  70.9),  # 格11
    (388.0,  71.0),  # 格12
    (494.4,  71.2),  # 格13
    (600.8,  71.3),  # 格14
    (707.2,  71.5),  # 格15
    (813.6,  71.6),  # 格16
    (920.0,  71.8),  # 格17 空间站
    (920.0, 178.1),  # 格18
    (920.0, 284.4),  # 格19
    (920.0, 390.8),  # 格20
    (920.0, 497.1),  # 格21
    (920.0, 603.4),  # 格22
    (920.0, 709.8),  # 格23
    (920.0, 816.1),  # 格24
    (920.0, 922.4),  # 格25 实验室
    (813.8, 923.1),  # 格26
    (707.5, 923.9),  # 格27
    (601.2, 924.6),  # 格28
    (495.0, 925.3),  # 格29
    (388.8, 926.0),  # 格30
    (282.5, 926.8),  # 格31
    (176.2, 927.5),  # 格32
]

def cell_center_px(cell_idx: int):
    """格子索引 (0-indexed) → 屏幕像素坐标（中心），使用标定坐标表"""
    ix, iy = CELL_CENTERS_IMG[cell_idx]
    return int(ix * BOARD_DISP_SCALE), int(iy * BOARD_DISP_SCALE)

# ─────────────────────────────
# 全局缓存（初始化后设置）
# ─────────────────────────────
_board_surf    = None    # 缩放后的棋盘背景
_planet_cache  = {}      # {planet_id: Surface}
_fonts         = {}
_player_tokens = [None] * MAX_PLAYERS   # 棋盘上用的圆形角色头像（小）
_player_icons  = [None] * MAX_PLAYERS   # 开始界面用的角色图（大）
_player_icons_dark = [None] * MAX_PLAYERS  # 压暗版本（开始界面非激活状态）
_debug_cells   = False        # 调试：显示格子中心校准线（按 D 切换）

PLANET_CIRCLE_DIR = os.path.join(ASSETS_DIR, "planets", "circles")

# 步进光圈动画状态
_step_flash: tuple | None = None   # (cx, cy, frames_left) 或 None
FLASH_TOTAL = 10                   # 光圈动画总帧数

PLAYERS_DIR = os.path.join(ASSETS_DIR, "players")

_TOKEN_R = max(10, int(18 * BOARD_DISP_SCALE))   # 棋盘棋子半径

# ─────────────────────────────
# 棋盘图片重载
# ─────────────────────────────
def _reload_board_surf():
    global _board_surf
    board_path = BOARD_EN_PNG if _lang.is_en() and os.path.exists(BOARD_EN_PNG) else BOARD_PNG
    if os.path.exists(board_path):
        raw = pygame.image.load(board_path).convert()
        _board_surf = pygame.transform.smoothscale(raw, (BOARD_DISP_W, BOARD_DISP_H))
    else:
        _board_surf = None


def reload_board_image():
    """语言切换后调用，重新加载对应语言的棋盘图片。"""
    _reload_board_surf()

# ─────────────────────────────
# 背景音乐
# ─────────────────────────────
_music_available = False
_music_on        = False

def init_music():
    global _music_available, _music_on
    try:
        pygame.mixer.init()
    except Exception:
        return
    for name in ["bgm.wav", "bgm.mp3", "bgm.ogg"]:
        path = os.path.join(BG_DIR, name)
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1)
                _music_available = True
                _music_on = True
            except Exception:
                pass
            break

def toggle_music():
    global _music_on
    if not _music_available:
        return
    if _music_on:
        pygame.mixer.music.pause()
        _music_on = False
    else:
        pygame.mixer.music.unpause()
        _music_on = True

def music_on():
    return _music_on

def music_available():
    return _music_available

def _make_circular(surf, diameter: int) -> pygame.Surface:
    """将 surf 缩放到 diameter×diameter 并裁成圆形（SRCALPHA）。"""
    sq = pygame.transform.smoothscale(surf, (diameter, diameter)).convert_alpha()
    mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    mask.fill((0, 0, 0, 0))
    pygame.draw.circle(mask, (255, 255, 255, 255), (diameter // 2, diameter // 2), diameter // 2)
    sq.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return sq

TOKEN_CROPS_JSON = os.path.join(ASSETS_DIR, "token_crops.json")

def _crop_head(src: pygame.Surface, cx: int, cy: int, r: int) -> pygame.Surface:
    """从原图裁出以 (cx,cy) 为中心、半径 r 的正方形区域。"""
    orig_w, orig_h = src.get_size()
    rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
    rect = rect.clip(pygame.Rect(0, 0, orig_w, orig_h))
    if rect.width < 2 or rect.height < 2:
        return src
    return src.subsurface(rect).copy()

def init_assets():
    """在 pygame.init() 之后调用，加载所有图片资源"""
    global _board_surf, _player_tokens, _player_icons, _player_icons_dark
    _reload_board_surf()

    # 读取头像标定数据（calibrate_tokens.py 生成）
    token_crops = {}
    if os.path.exists(TOKEN_CROPS_JSON):
        import json
        with open(TOKEN_CROPS_JSON, encoding="utf-8") as f:
            raw_crops = json.load(f)
        token_crops = {int(k): v for k, v in raw_crops.items()}

    # 加载最多 MAX_PLAYERS 个玩家角色图片
    token_diam = _TOKEN_R * 2   # 棋盘棋子直径
    icon_h     = 130                                        # 开始界面图标高度
    for i in range(MAX_PLAYERS):
        path = os.path.join(PLAYERS_DIR, f"player_{i}.png")
        if os.path.exists(path):
            src = pygame.image.load(path).convert()
            # 棋子：若有头像标定则只取头部，否则用全图
            if i in token_crops:
                cx, cy, r = token_crops[i]
                head = _crop_head(src, cx, cy, r)
            else:
                head = src
            _player_tokens[i] = _make_circular(head, token_diam)
            # 开始界面大图（保持比例，始终用全图）
            src_w, src_h = src.get_size()
            icon_w = int(src_w * icon_h / src_h)
            icon = pygame.transform.smoothscale(src, (icon_w, icon_h))
            _player_icons[i] = icon
            # 预生成压暗版（非激活状态，避免开始界面每帧分配）
            dark = icon.copy()
            overlay_s = pygame.Surface((icon_w, icon_h), pygame.SRCALPHA)
            overlay_s.fill((0, 0, 0, 170))
            dark.blit(overlay_s, (0, 0))
            _player_icons_dark[i] = dark

def _load_planet_circle(planet_id: int) -> pygame.Surface | None:
    """加载 assets/planets/circles/planet_{id}.jpg（圆形裁剪版星球图）"""
    key = ("circle", planet_id)
    if key not in _planet_cache:
        path = os.path.join(PLANET_CIRCLE_DIR, f"planet_{planet_id}.jpg")
        if os.path.exists(path):
            _planet_cache[key] = pygame.image.load(path).convert()
        else:
            _planet_cache[key] = None
    return _planet_cache[key]

def _draw_planet_circle(surface, planet_id: int, cx: int, cy: int, radius: int):
    """在 (cx, cy) 处绘制 radius 半径的圆形星球图，带光晕边框。"""
    raw = _load_planet_circle(planet_id)
    size = radius * 2
    if raw:
        img = pygame.transform.smoothscale(raw, (size, size)).convert_alpha()
        # 圆形遮罩：圆内不透明，圆外透明
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
        img.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(img, (cx - radius, cy - radius))
    else:
        # 无图时画占位圆
        pygame.draw.circle(surface, (30, 50, 110), (cx, cy), radius)
        draw_text(surface, "?", cx, cy, size=radius, color=(80, 100, 160), center=True)
    # 外圈光晕边框
    pygame.draw.circle(surface, (100, 140, 230), (cx, cy), radius, 2)
    pygame.draw.circle(surface, (60,  90, 160), (cx, cy), radius + 3, 1)

# ─────────────────────────────
# 星球卡弹窗
# ─────────────────────────────
def _lv_names():
    return [_lang.lv_name(i) for i in range(4)]

def draw_planet_card_popup(surface, game_state):
    """在涉及星球的阶段显示完整星球证书弹窗（纯文字大字排版）"""
    from game import GamePhase
    from data import PLANETS, CELL_PLANET_ID

    phase = game_state.phase
    if phase in (GamePhase.PLANET_PAY, GamePhase.PLANET_TRADE):
        pid = game_state.pending_pid
    elif phase in (GamePhase.PLANET_BUY, GamePhase.PLANET_UP):
        pid = CELL_PLANET_ID[game_state.current_player.pos]
    else:
        return
    if not pid or pid not in PLANETS:
        return

    pdata = PLANETS[pid]
    owner = game_state._find_planet_owner(pid)
    cur_lv = owner.planets[pid] if owner else -1
    LV_NAMES = _lv_names()

    # language-aware planet name
    planet_name = pdata.get("name_en", pdata["name"]) if _lang.is_en() else pdata["name"]
    planet_desc = pdata.get("desc_en", pdata["desc"])  if _lang.is_en() else pdata.get("desc", "")
    planet_facts = pdata.get("facts_en", pdata.get("facts", [])) if _lang.is_en() else pdata.get("facts", [])

    # ── 布局 ──
    PAD   = 28
    POP_W = 860
    POP_H = 930
    pop_x = (BOARD_DISP_W - POP_W) // 2
    pop_y = (SCREEN_H     - POP_H) // 2
    inner_w = POP_W - PAD * 2

    # 半透明遮罩
    overlay = pygame.Surface((BOARD_DISP_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 185))
    surface.blit(overlay, (0, 0))

    # 弹窗背景
    pygame.draw.rect(surface, (14, 18, 48),
                     pygame.Rect(pop_x, pop_y, POP_W, POP_H), border_radius=12)
    pygame.draw.rect(surface, COLORS["cell_border"],
                     pygame.Rect(pop_x, pop_y, POP_W, POP_H), 2, border_radius=12)

    lx = pop_x + PAD   # 左边距 x
    cx = pop_x + POP_W // 2   # 中心 x
    ty = pop_y + 22

    # ── 右上角星球圆形图 ──
    CIRCLE_R  = 65
    circle_cx = pop_x + POP_W - PAD - CIRCLE_R
    circle_cy = pop_y + PAD + CIRCLE_R + 8
    _draw_planet_circle(surface, pid, circle_cx, circle_cy, CIRCLE_R)
    # 描述文字可用宽度（避免与右上角圆形重叠）
    desc_max_w = POP_W - PAD * 2 - CIRCLE_R * 2 - 20

    # ── 星球名称 ──
    draw_text(surface, planet_name, cx, ty,
              size=45, bold=True, color=COLORS["text_gold"], center=True)
    ty += 60

    # ── 描述文字 ──
    desc = planet_desc
    if desc:
        ty = draw_multiline(surface, desc, lx, ty, size=30,
                            max_width=desc_max_w, color=(195, 215, 245))
        ty += 6

    # ── 分隔线 ──
    pygame.draw.line(surface, COLORS["cell_border"],
                     (lx, ty), (lx + inner_w, ty))
    ty += 12

    # ── 费用表 ──
    # 列 x 坐标（左对齐，数字列居中显示）
    ROW_H = 48
    C0 = lx              # 等级名
    C1 = lx + 210        # 探索费
    C2 = lx + 350        # 过路费
    C3 = lx + 490        # 收购费
    C4 = lx + 630        # 交公价

    # 表头
    hc = (140, 165, 210)
    draw_text(surface, _lang.t("col_lv"),       C0, ty, size=20, color=hc)
    draw_text(surface, _lang.t("col_exp_fee"),  C1, ty, size=20, color=hc)
    draw_text(surface, _lang.t("col_toll"),      C2, ty, size=20, color=hc)
    draw_text(surface, _lang.t("col_trade"),     C3, ty, size=20, color=hc)
    draw_text(surface, _lang.t("col_mtg"),       C4, ty, size=20, color=hc)
    ty += 30

    # 细分隔线
    pygame.draw.line(surface, (50, 65, 110),
                     (lx, ty), (lx + inner_w, ty))
    ty += 6

    # 数据行
    for lv_idx, lv_data in enumerate(pdata["levels"]):
        if lv_data["explore"] == 0 and lv_data["toll"] == 0 and lv_data["trade"] == 0:
            continue

        is_cur = (lv_idx == cur_lv)

        # 高亮行背景
        if is_cur:
            pygame.draw.rect(surface, (45, 58, 118),
                             pygame.Rect(lx - 4, ty - 3, inner_w + 8, ROW_H - 4),
                             border_radius=5)
            pygame.draw.rect(surface, (100, 130, 220),
                             pygame.Rect(lx - 4, ty - 3, inner_w + 8, ROW_H - 4),
                             1, border_radius=5)

        rc = (255, 225, 70) if is_cur else (210, 225, 255)
        trade_str = str(lv_data["trade"]) if lv_data["trade"] > 0 else "—"

        draw_text(surface, LV_NAMES[lv_idx],            C0, ty, size=24, bold=is_cur, color=rc)
        draw_text(surface, str(lv_data["explore"]),    C1, ty, size=24, bold=is_cur, color=rc)
        draw_text(surface, str(lv_data["toll"]),       C2, ty, size=24, bold=is_cur, color=rc)
        draw_text(surface, trade_str,                  C3, ty, size=24, bold=is_cur, color=rc)
        draw_text(surface, str(lv_data["mortgage"]),   C4, ty, size=24, bold=is_cur, color=rc)
        ty += ROW_H

    # ── 实验类型标注 ──
    ty += 6
    pygame.draw.line(surface, COLORS["cell_border"],
                     (lx, ty), (lx + inner_w, ty))
    ty += 10
    exps = pdata.get("experiments", [False, False, False])
    EXP_NAMES   = [_lang.exp_name(i) for i in range(3)]
    EXP_COLORS  = [(160, 110, 60), (60, 150, 230), (60, 190, 80)]   # 棕 蓝 绿
    EXP_DIM     = (90, 95, 110)
    done_exps   = owner.planet_exps.get(pid, [False, False, False]) if owner else [False, False, False]
    draw_text(surface, _lang.t("exp_label"), lx, ty, size=22, color=(140, 165, 210))
    draw_text(surface, _lang.t("exp_formula_p"),
              lx + get_font(22).size(_lang.t("exp_label"))[0] + 160, ty + 4,
              size=14, color=(120, 140, 120))
    ty += 28
    ex = lx + 4
    any_exp = False
    for i, (name, color) in enumerate(zip(EXP_NAMES, EXP_COLORS)):
        if exps[i]:
            any_exp = True
            if done_exps[i]:
                label = f"✓{name}"
                surf_e = get_font(20, bold=False).render(label, True, (100, 130, 100))
            else:
                label = f"○{name}"
                surf_e = get_font(20, bold=True).render(label, True, color)
            surface.blit(surf_e, (ex, ty))
            ex += surf_e.get_width() + 12
    if not any_exp:
        draw_text(surface, _lang.t("no_exp"), ex, ty, size=22, color=EXP_DIM)
    ty += 30

    # ── 趣味知识 ──
    facts = planet_facts
    if facts:
        pygame.draw.line(surface, COLORS["cell_border"],
                         (lx, ty), (lx + inner_w, ty))
        ty += 10
        draw_text(surface, _lang.t("fun_facts"), lx, ty, size=20,
                  bold=True, color=(255, 200, 80))
        ty += 28
        for fact in facts:
            ty = draw_multiline(surface, "• " + fact, lx + 4, ty,
                                size=21, max_width=inner_w - 4,
                                color=(195, 230, 200))
            ty += 4

    # ── 底部所有者 ──
    bot_y = pop_y + POP_H - 30
    pygame.draw.line(surface, COLORS["cell_border"],
                     (lx, bot_y - 6), (lx + inner_w, bot_y - 6))
    if owner:
        pc = COLORS["owned_p"][owner.id]
        draw_text(surface,
                  _lang.t("planet_owner", name=owner.name, lv=LV_NAMES[cur_lv]),
                  cx, bot_y + 4, size=15, color=pc, center=True)
    else:
        draw_text(surface, _lang.t("planet_no_owner"),
                  cx, bot_y + 4, size=15, color=(150, 170, 210), center=True)

# ─────────────────────────────
# 字体
# ─────────────────────────────
import re as _re

def _render_line_yellow_numbers(surface, text, x, y, size, color):
    """渲染一行文字，其中数字用黄色加粗高亮。"""
    fn  = get_font(size)
    fnb = get_font(size, bold=True)
    cx  = x
    for part in _re.split(r'(\d+)', text):
        if part.isdigit():
            surf = fnb.render(part, True, (255, 215, 0))
        else:
            surf = fn.render(part, True, color)
        surface.blit(surf, (cx, y))
        cx += surf.get_width()
def get_font(size: int, bold=False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fonts:
        for name in ["microsoftyahei", "msyh", "simhei", "simsun"]:
            try:
                _fonts[key] = pygame.font.SysFont(name, size, bold=bold)
                break
            except Exception:
                continue
        else:
            _fonts[key] = pygame.font.SysFont(None, size, bold=bold)
    return _fonts[key]

def draw_text(surface, text, x, y, size=14, color=None, bold=False, center=False):
    if color is None:
        color = COLORS["text_light"]
    font = get_font(size, bold)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
    surface.blit(surf, rect)

def draw_multiline(surface, text, x, y, size=14, color=None, line_spacing=4, max_width=0):
    if color is None:
        color = COLORS["text_light"]
    font = get_font(size)
    cy = y
    for paragraph in text.split("\n"):
        if max_width > 0 and font.size(paragraph)[0] > max_width:
            # Word-wrap first (works for English; Chinese falls through to char-wrap)
            words = paragraph.split()
            if len(words) > 1:
                line = ""
                for word in words:
                    test = (line + " " + word).strip()
                    if font.size(test)[0] > max_width:
                        if line:
                            surface.blit(font.render(line, True, color), (x, cy))
                            cy += font.get_height() + line_spacing
                        # Single word too wide — fall through to char-wrap
                        if font.size(word)[0] > max_width:
                            cur = ""
                            for ch in word:
                                if font.size(cur + ch)[0] > max_width:
                                    if cur:
                                        surface.blit(font.render(cur, True, color), (x, cy))
                                        cy += font.get_height() + line_spacing
                                    cur = ch
                                else:
                                    cur += ch
                            line = cur
                        else:
                            line = word
                    else:
                        line = test
                if line:
                    surface.blit(font.render(line, True, color), (x, cy))
                    cy += font.get_height() + line_spacing
            else:
                # Single long word (or Chinese text with no spaces) — char-wrap
                line = ""
                for ch in paragraph:
                    if font.size(line + ch)[0] > max_width:
                        if line:
                            surface.blit(font.render(line, True, color), (x, cy))
                            cy += font.get_height() + line_spacing
                        line = ch
                    else:
                        line += ch
                if line:
                    surface.blit(font.render(line, True, color), (x, cy))
                    cy += font.get_height() + line_spacing
        else:
            surface.blit(font.render(paragraph, True, color), (x, cy))
            cy += font.get_height() + line_spacing
    return cy

# ─────────────────────────────
# 按钮
# ─────────────────────────────
class Button:
    def __init__(self, rect, label, color=None, hover_color=None):
        self.rect        = pygame.Rect(rect)
        self.label       = label
        self.color       = color or COLORS["button"]
        self.hover_color = hover_color or COLORS["button_hover"]
        self.enabled     = True

    def draw(self, surface):
        mouse    = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse) and self.enabled
        c = self.hover_color if is_hover else self.color
        if not self.enabled:
            c = (60, 60, 70)
        pygame.draw.rect(surface, c, self.rect, border_radius=6)
        pygame.draw.rect(surface, COLORS["text_light"], self.rect, 1, border_radius=6)
        draw_text(surface, self.label,
                  self.rect.centerx, self.rect.centery,
                  size=22, bold=True, center=True)

    def is_clicked(self, event):
        return (self.enabled
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))

# ─────────────────────────────
# 骰子
# ─────────────────────────────
DOT_POS = {
    1: [(1,1)], 2: [(0,0),(2,2)], 3: [(0,0),(1,1),(2,2)],
    4: [(0,0),(2,0),(0,2),(2,2)], 5: [(0,0),(2,0),(1,1),(0,2),(2,2)],
    6: [(0,0),(2,0),(0,1),(2,1),(0,2),(2,2)],
}

def draw_die(surface, value: int, x: int, y: int, size=40):
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(surface, COLORS["dice_bg"], rect, border_radius=6)
    pygame.draw.rect(surface, COLORS["text_light"], rect, 1, border_radius=6)
    if value < 1 or value > 6:
        return
    margin = size // 6
    step   = (size - 2 * margin) // 2
    r      = max(3, size // 10)
    for gx, gy in DOT_POS[value]:
        pygame.draw.circle(surface, COLORS["dice_dot"],
                           (x + margin + gx * step, y + margin + gy * step), r)

def toggle_debug_cells():
    global _debug_cells
    _debug_cells = not _debug_cells

def _draw_cell_debug(surface):
    """调试用：绿色边框 + 红色十字准线 + 编号，按 D 切换"""
    # 格子大小 = 相邻格中心距 ≈ 107px（图片坐标），保证每格严格共享边
    # (928.2-70.6)/8 = 107.2px → half=53.6 → 屏幕 53.6×1.2 = 64px
    half = int(107.2 / 2 * BOARD_DISP_SCALE)   # 64 screen px
    for idx in range(32):
        cx, cy = cell_center_px(idx)
        # 绿色边框
        pygame.draw.rect(surface, (0, 220, 0),
                         pygame.Rect(cx - half, cy - half, half * 2, half * 2), 2)
        # 红色十字准线
        pygame.draw.line(surface, (255, 0, 0), (cx - 16, cy), (cx + 16, cy), 2)
        pygame.draw.line(surface, (255, 0, 0), (cx, cy - 16), (cx, cy + 16), 2)
        # 格子编号
        draw_text(surface, str(idx + 1), cx, cy, size=13,
                  color=(255, 255, 0), bold=True, center=True)

def trigger_step_flash(cell_idx: int):
    """玩家走到新格子时调用，启动光圈消散动画。"""
    global _step_flash
    cx, cy = cell_center_px(cell_idx)
    cx = max(50, min(BOARD_DISP_W - 50, cx))
    cy = max(50, min(SCREEN_H   - 50, cy))
    _step_flash = (cx, cy, FLASH_TOTAL)


def _draw_step_flash(surface):
    """绘制步进光圈，每帧自动递减。"""
    global _step_flash
    if _step_flash is None:
        return
    cx, cy, frames = _step_flash
    progress = 1 - frames / FLASH_TOTAL          # 0→1 随时间增大
    r      = int(22 + 28 * progress)             # 从小到大扩展
    alpha  = int(220 * (frames / FLASH_TOTAL))   # 从亮到暗消逝
    ring_surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
    pygame.draw.circle(ring_surf, (255, 255, 140, alpha),
                       (r + 3, r + 3), r, 4)
    surface.blit(ring_surf, ring_surf.get_rect(center=(cx, cy)))
    _step_flash = (cx, cy, frames - 1) if frames > 1 else None


# ─────────────────────────────
# 棋盘渲染
# ─────────────────────────────
def draw_board(surface, game_state, skip_pid=None):
    """绘制棋盘背景 + 格子高亮 + 玩家棋子"""

    # 1. 背景图片
    if _board_surf:
        surface.blit(_board_surf, (0, 0))
    else:
        # 备用：纯色背景
        pygame.draw.rect(surface, (20, 30, 60),
                         pygame.Rect(0, 0, BOARD_DISP_W, BOARD_DISP_H))
        draw_text(surface, "board.png not found",
                  BOARD_DISP_W // 2, BOARD_DISP_H // 2,
                  size=18, center=True)

    # 2. 在每个格子上叠加拥有者颜色标记（居中小圆点）
    for idx in range(32):
        pid = CELL_PLANET_ID[idx]
        if pid == 0:
            continue
        for p in game_state.players:
            if not p.bankrupt and pid in p.planets:
                cx, cy = cell_center_px(idx)
                r = max(7, int(17 * BOARD_DISP_SCALE))
                pygame.draw.circle(surface, COLORS["owned_p"][p.id], (cx, cy), r)
                pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r, 1)
                lv = p.planets[pid]
                draw_text(surface, str(lv + 1), cx, cy,
                          size=9, bold=True, center=True)
                break

    # 3. 玩家棋子
    _draw_tokens(surface, game_state, skip_pid=skip_pid)

    # 4. 步进光圈动画
    _draw_step_flash(surface)

    # 5. 调试：格子中心校准（按 D 切换）
    if _debug_cells:
        _draw_cell_debug(surface)


def _draw_tokens(surface, game_state, skip_pid=None):
    """在正确格子位置绘制玩家棋子，skip_pid 的棋子不渲染（拖拽时用）"""
    from collections import defaultdict
    cell_players = defaultdict(list)
    for p in game_state.players:
        if not p.bankrupt and p.id != skip_pid:
            cell_players[p.pos].append(p)

    for cell_idx, players_here in cell_players.items():
        cx, cy = cell_center_px(cell_idx)
        cx, cy = _cluster_center(cx, cy)
        n = len(players_here)
        offsets = _token_offsets(n)
        for i, player in enumerate(players_here):
            tx = cx + offsets[i][0]
            ty = cy + offsets[i][1]
            r  = _TOKEN_R
            color = COLORS["owned_p"][player.id]

            img = _player_tokens[player.id]
            if img:
                # 有角色图：玩家颜色厚圆圈 + 角色图
                pygame.draw.circle(surface, color, (tx, ty), r + 4)
                surface.blit(img, img.get_rect(center=(tx, ty)))
                pygame.draw.circle(surface, color, (tx, ty), r + 4, 5)
            else:
                # 回退：纯色圆圈+编号
                pygame.draw.circle(surface, color, (tx, ty), r)
                pygame.draw.circle(surface, (255, 255, 255), (tx, ty), r, 3)
                draw_text(surface, str(player.id + 1), tx, ty,
                          size=12, bold=True, color=(255, 255, 255), center=True)

            # 当前玩家：闪烁高亮圆圈
            if player.id == game_state.current_idx:
                t = pygame.time.get_ticks() / 1000.0
                pulse = (math.sin(t * math.pi / 0.3) + 1) / 2   # 0.0~1.0
                ring_r = r + 8 + int(pulse * 6)
                alpha  = int(140 + pulse * 115)
                rc = (255, 255, int(50 + pulse * 205))
                # 用临时 Surface 支持透明度（固定大小减少 GC 压力）
                sz = (ring_r + 4) * 2
                ring_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (*rc, alpha), (sz//2, sz//2), ring_r, 4)
                surface.blit(ring_surf, (tx - sz//2, ty - sz//2))


_s = 24   # token 偏移半格间距
_TOKEN_OFFSETS = {
    1: [(0, 0)],
    2: [(-_s, 0), (_s, 0)],
    3: [(-_s, -_s), (_s, -_s), (0, _s)],
    4: [(-_s, -_s), (_s, -_s), (-_s, _s), (_s, _s)],
    5: [(-_s, -_s), (_s, -_s), (0, 0), (-_s, _s), (_s, _s)],
    6: [(-_s, -_s), (_s, -_s), (-_s, 0), (_s, 0), (-_s, _s), (_s, _s)],
}
del _s


def _token_offsets(n):
    return _TOKEN_OFFSETS.get(n, _TOKEN_OFFSETS[6])


def _cluster_center(cx, cy):
    """将 token 群中心点限制在棋盘可视区域内，避免角落格子的 token 被裁剪。"""
    margin = 50
    cx = max(margin, min(BOARD_DISP_W - margin, cx))
    cy = max(margin, min(SCREEN_H   - margin, cy))
    return cx, cy


def _draw_single_token(surface, player_id, tx, ty):
    """在 (tx, ty) 绘制单个玩家棋子（供拖拽时复用）"""
    r     = _TOKEN_R
    color = COLORS["owned_p"][player_id]
    img   = _player_tokens[player_id]
    if img:
        pygame.draw.circle(surface, color, (tx, ty), r + 4)
        surface.blit(img, img.get_rect(center=(tx, ty)))
        pygame.draw.circle(surface, color, (tx, ty), r + 4, 5)
    else:
        pygame.draw.circle(surface, color, (tx, ty), r)
        pygame.draw.circle(surface, (255, 255, 255), (tx, ty), r, 3)
        draw_text(surface, str(player_id + 1), tx, ty,
                  size=12, bold=True, color=(255, 255, 255), center=True)


def get_token_pos(game_state, player_id: int):
    """返回玩家棋子在屏幕上的坐标（考虑同格偏移）"""
    from collections import defaultdict
    cell_players = defaultdict(list)
    for p in game_state.players:
        if not p.bankrupt:
            cell_players[p.pos].append(p)
    player       = game_state.players[player_id]
    players_here = cell_players[player.pos]
    cx, cy       = cell_center_px(player.pos)
    cx, cy       = _cluster_center(cx, cy)
    offsets      = _token_offsets(len(players_here))
    idx          = players_here.index(player) if player in players_here else 0
    ox, oy       = offsets[idx]
    return cx + ox, cy + oy


def nearest_cell(sx: int, sy: int) -> int:
    """屏幕坐标 → 最近格子索引（0-31）"""
    best_idx, best_d2 = 0, float('inf')
    for i in range(32):
        cx, cy = cell_center_px(i)
        d2 = (sx - cx) ** 2 + (sy - cy) ** 2
        if d2 < best_d2:
            best_d2, best_idx = d2, i
    return best_idx


def draw_reposition_overlay(surface, game_state, drag_pid, drag_pos):
    """REPOSITION 阶段：顶部提示条 + 目标格高亮 + 拖拽棋子"""
    from data import BOARD
    moves = game_state._reposition_moves
    cp    = game_state.current_player

    # 顶部半透明提示条
    bar = pygame.Surface((BOARD_DISP_W, 58), pygame.SRCALPHA)
    bar.fill((8, 16, 50, 215))
    surface.blit(bar, (0, 0))
    draw_text(surface,
              _lang.t("repo_title", name=cp.name, n=moves),
              BOARD_DISP_W // 2, 29,
              size=26, bold=True, color=(255, 220, 60), center=True)

    if drag_pid is None or drag_pos is None:
        return

    # 目标格高亮
    target   = nearest_cell(*drag_pos)
    tcx, tcy = cell_center_px(target)

    hl = pygame.Surface((BOARD_DISP_W, SCREEN_H), pygame.SRCALPHA)
    pygame.draw.circle(hl, (255, 220, 0, 80),  (tcx, tcy), 38)
    pygame.draw.circle(hl, (255, 220, 0, 220), (tcx, tcy), 38, 3)
    surface.blit(hl, (0, 0))
    target_cell = BOARD[target]
    target_name = _lang.loc_name(target_cell)
    draw_text(surface, target_name, tcx, tcy - 52,
              size=20, bold=True, color=(255, 235, 80), center=True)

    # 拖拽中的棋子跟随鼠标
    _draw_single_token(surface, drag_pid, drag_pos[0], drag_pos[1])


# ─────────────────────────────
# 右侧信息面板
# ─────────────────────────────
def draw_panel(surface, game_state, buttons, display_dice=None):
    pw = PANEL_W
    panel_rect = pygame.Rect(PANEL_X, 5, pw, SCREEN_H - 10)
    pygame.draw.rect(surface, COLORS["panel_bg"], panel_rect, border_radius=8)
    pygame.draw.rect(surface, COLORS["cell_border"], panel_rect, 1, border_radius=8)

    x  = PANEL_X + 10
    y  = 14
    lw = pw - 20

    # 标题（含音乐状态）
    title_str = _lang.t("panel_title")
    draw_text(surface, title_str,
              x + lw // 2, y, size=24, bold=True,
              color=COLORS["text_gold"], center=True)
    if music_available():
        music_str = _lang.t("music_on") if music_on() else _lang.t("music_off")
        draw_text(surface, music_str, x + lw - 2, y + 4, size=16,
                  color=(180, 210, 180) if music_on() else (140, 140, 140))
    y += 34

    # 当前玩家
    cp = game_state.current_player
    draw_text(surface, _lang.t("turn", name=cp.name),
              x, y, size=24, bold=True, color=COLORS["owned_p"][cp.id])
    y += 32

    # 骰子（支持动画帧传入 display_dice）
    d1, d2 = display_dice if display_dice else game_state.dice
    DIE_SZ = 56
    if d1 > 0:
        draw_die(surface, d1, x,            y, size=DIE_SZ)
        draw_die(surface, d2, x + DIE_SZ + 8, y, size=DIE_SZ)
        draw_text(surface, f"= {d1+d2}", x + DIE_SZ * 2 + 18, y + DIE_SZ // 2 - 12,
                  size=30, bold=True, color=COLORS["text_gold"])
    y += DIE_SZ + 14

    # 消息框
    MSG_H = 155
    pygame.draw.rect(surface, (10, 15, 40),
                     pygame.Rect(x - 4, y, lw + 8, MSG_H), border_radius=4)
    lines = game_state.message.split("\n")
    my = y + 6
    for i, line in enumerate(lines):
        if i == 0 and line.startswith("【"):
            # 星球名第一行：大字加粗高亮
            draw_text(surface, line, x, my, size=24, bold=True,
                      color=COLORS["text_gold"])
            my += get_font(24, bold=True).get_height() + 4
        else:
            # 普通行：自动换行 + 数字黄色
            font = get_font(22)
            if font.size(line)[0] > lw:
                cur = ""
                for ch in line:
                    if font.size(cur + ch)[0] > lw:
                        _render_line_yellow_numbers(surface, cur, x, my, 22, COLORS["text_light"])
                        my += font.get_height() + 2
                        cur = ch
                    else:
                        cur += ch
                if cur:
                    _render_line_yellow_numbers(surface, cur, x, my, 22, COLORS["text_light"])
                    my += font.get_height() + 2
            else:
                _render_line_yellow_numbers(surface, line, x, my, 22, COLORS["text_light"])
                my += font.get_height() + 4
    y += MSG_H + 10

    # 玩家状态（彩色分段渲染）
    draw_text(surface, _lang.t("players_status"), x, y, size=20,
              color=(150, 180, 220))
    y += 28
    fn  = get_font(22)
    fnb = get_font(22, bold=True)
    for p in game_state.players:
        name_c = COLORS["owned_p"][p.id]
        if p.bankrupt:
            name_c = (110, 70, 70)
            prefix = "✖ "
        elif p.id == game_state.current_idx:
            prefix = "▶ "
        else:
            prefix = "  "
        cx2 = x
        # 状态+名字
        s = fnb.render(prefix + p.name, True, name_c)
        surface.blit(s, (cx2, y))
        cx2 += s.get_width() + 10
        # 经费：¥ 金色 + 数值白色
        s = fn.render("¥", True, (255, 200, 50))
        surface.blit(s, (cx2, y))
        cx2 += s.get_width()
        s = fnb.render(str(p.funds), True, (255, 230, 120))
        surface.blit(s, (cx2, y))
        cx2 += s.get_width() + 10
        # 星球数：★ 蓝色 + 数值
        s = fn.render("★", True, (100, 180, 255))
        surface.blit(s, (cx2, y))
        cx2 += s.get_width()
        s = fnb.render(str(len(p.planets)), True, (160, 210, 255))
        surface.blit(s, (cx2, y))
        cx2 += s.get_width() + 10
        # 免费卡：◆ 绿色（有才显示）
        if p.keep_cards > 0:
            s = fn.render("◆", True, (80, 220, 120))
            surface.blit(s, (cx2, y))
            cx2 += s.get_width()
            s = fnb.render(str(p.keep_cards), True, (140, 240, 160))
            surface.blit(s, (cx2, y))
        y += 28
    y += 10

    # 当前玩家星球列表（大字体，彩色数据）
    draw_text(surface, _lang.t("player_planets", name=cp.name), x, y, size=20,
              color=(150, 180, 220))
    y += 28
    planets = game_state.get_player_planet_list(cp)
    fn  = get_font(18)
    fnb = get_font(18, bold=True)
    max_val = _lang.t("max_level")
    for pl in planets:
        # 第一行：星球名（加粗，单独占一行）
        pname = _lang.loc_name(pl)
        name_color = (255, 220, 80) if pl["can_exp"] else (150, 210, 255)
        draw_text(surface, f"  ◈ {pname}", x, y, size=22, bold=True, color=name_color)
        y += 28
        # 第二行：等级 + 可实验标记
        lv_color = (100, 220, 120) if pl["can_exp"] else (170, 180, 220)
        exp_tag = "  " + _lang.t("can_exp_tag") if pl["can_exp"] else ""
        draw_text(surface, f"    Lv{pl['level']}{exp_tag}", x, y, size=18, color=lv_color)
        y += 24
        # 第三行：彩色数据字段
        cx2 = x + 14
        fields = [
            (_lang.t("field_toll"),     str(pl["toll"]),                                         (255, 130, 70)),
            (_lang.t("field_upgrade"),  max_val if pl["upgrade"] == 0 else str(pl["upgrade"]),   (100, 210, 255)),
            (_lang.t("field_trade"),    "×" if pl["trade"] == -1 else str(pl["trade"]),          (255, 220, 60)),
            (_lang.t("field_mortgage"), str(pl["mortgage"]),                                      (160, 160, 160)),
        ]
        for lbl, val, col in fields:
            ls = fn.render(lbl, True, (130, 145, 180))
            surface.blit(ls, (cx2, y))
            cx2 += ls.get_width()
            vs = fnb.render(val, True, col)
            surface.blit(vs, (cx2, y))
            cx2 += vs.get_width()
        y += 22
        # 分隔线
        pygame.draw.line(surface, (50, 60, 100), (x, y + 4), (x + lw, y + 4))
        y += 12
    if not planets:
        draw_text(surface, "  " + _lang.t("no_planets"), x, y, size=22,
                  color=(100, 110, 140))
        y += 30
    y += 8

    # 按钮
    for btn in buttons:
        btn.draw(surface)

# ─────────────────────────────
# 卡片显示（弹窗）
# ─────────────────────────────
CARD_POP_W = 680
CARD_POP_H = 500

def draw_card_popup(surface, game_state):
    """展示当前抽到的卡片（纯文字排版，字号×1.6，支持多语言扩展）"""
    card = game_state.current_card
    if card is None:
        return

    kind = card.get("_type", "chance")
    kind_label = _lang.t("card_event") if kind == "event" else _lang.t("card_chance")
    kind_bg    = (160, 35, 35) if kind == "event" else (25, 115, 55)

    # Language-aware card text
    if _lang.is_en():
        card_name = card.get("name_en") or card["name"]
        card_desc = card.get("desc_en") or card["desc"]
    else:
        card_name = card["name"]
        card_desc = card["desc"]

    pop_x = (BOARD_DISP_W - CARD_POP_W) // 2
    pop_y = (SCREEN_H     - CARD_POP_H) // 2

    # 半透明遮罩
    overlay = pygame.Surface((BOARD_DISP_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    surface.blit(overlay, (0, 0))

    # 弹窗背景
    pygame.draw.rect(surface, (14, 18, 48),
                     pygame.Rect(pop_x, pop_y, CARD_POP_W, CARD_POP_H),
                     border_radius=14)
    pygame.draw.rect(surface, COLORS["cell_border"],
                     pygame.Rect(pop_x, pop_y, CARD_POP_W, CARD_POP_H),
                     2, border_radius=14)

    PAD = 44
    cx  = pop_x + CARD_POP_W // 2
    ty  = pop_y + 30

    # ── 种类标签（彩色胶囊）──
    tag_surf = get_font(26, bold=True).render(f"  {kind_label}  ", True, (255, 255, 255))
    tw, th   = tag_surf.get_size()
    tag_rx   = cx - tw // 2 - 8
    pygame.draw.rect(surface, kind_bg,
                     pygame.Rect(tag_rx, ty - 4, tw + 16, th + 8),
                     border_radius=22)
    surface.blit(tag_surf, (cx - tw // 2, ty))
    ty += th + 24

    # ── 卡片名称（42pt，金色，粗体，居中）──
    draw_text(surface, card_name, cx, ty,
              size=42, bold=True, color=COLORS["text_gold"], center=True)
    ty += 60

    # ── 分隔线 ──
    pygame.draw.line(surface, COLORS["cell_border"],
                     (pop_x + PAD, ty), (pop_x + CARD_POP_W - PAD, ty))
    ty += 22

    # ── 描述文字（29pt，全文显示，自动换行）──
    draw_multiline(surface, card_desc,
                   pop_x + PAD, ty,
                   size=29, line_spacing=10,
                   max_width=CARD_POP_W - PAD * 2,
                   color=(210, 228, 255))

# ─────────────────────────────
# 星球选择弹窗
# ─────────────────────────────
def draw_planet_picker(surface, game_state, title="选择一颗星球", picker_mode="", for_player_id=-1):
    ow, oh = 400, 300
    ox = (BOARD_DISP_W - ow) // 2
    oy = (SCREEN_H - oh) // 2
    overlay = pygame.Surface((BOARD_DISP_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 200))
    surface.blit(overlay, (0, 0))
    pygame.draw.rect(surface, (15, 20, 50),
                     pygame.Rect(ox, oy, ow, oh), border_radius=8)
    pygame.draw.rect(surface, COLORS["cell_border"],
                     pygame.Rect(ox, oy, ow, oh), 2, border_radius=8)
    draw_text(surface, title, ox + ow // 2, oy + 14,
              size=15, bold=True, color=COLORS["text_gold"], center=True)

    cp = game_state.current_player
    if picker_mode == "explore_free":
        planets = game_state.get_unclaimed_planet_list()
    elif for_player_id >= 0:
        planets = game_state.get_player_planet_list(game_state.players[for_player_id])
    else:
        planets = game_state.get_player_planet_list(cp)
    if picker_mode == "lab":
        planets = [pl for pl in planets if pl.get("has_exp") and pl["level"] < 4]
    elif picker_mode == "earth":
        planets = [pl for pl in planets if pl["upgrade"] > 0]
    buttons = []
    by = oy + 44
    for pl in planets:
        r = pygame.Rect(ox + 20, by, ow - 40, 32)
        pname = _lang.loc_name(pl)
        if picker_mode == "explore_free":
            label = pname + _lang.t("picker_cost", n=pl['explore'])
        elif picker_mode == "lab" and not pl.get("can_exp"):
            label = f"{pname} Lv{pl['level']}" + _lang.t("picker_lab_done")
        else:
            label = f"{pname} Lv{pl['level']}  {_lang.t('field_mortgage')}{pl['mortgage']}"
        if picker_mode == "lab" and not pl.get("can_exp"):
            # 已完成：灰色非按钮样式
            pygame.draw.rect(surface, (35, 38, 52), r, border_radius=5)
            pygame.draw.rect(surface, (60, 65, 80), r, 1, border_radius=5)
            draw_text(surface, label, r.centerx, r.centery,
                      size=14, color=(90, 100, 90), center=True)
        else:
            buttons.append((Button(r, label), pl["planet_id"]))
        by += 38
    if not planets:
        draw_text(surface, _lang.t("picker_no_planet"),
                  ox + ow // 2, oy + oh // 2,
                  size=14, center=True, color=(150, 160, 180))
    for btn, _ in buttons:
        btn.draw(surface)
    return buttons


# ─────────────────────────────
# 玩家选择弹窗（分享财富 / 互换星球）
# ─────────────────────────────
def draw_player_picker(surface, game_state, title="选择玩家"):
    """显示其他玩家选择弹窗，返回 [(Button, player_id), ...]"""
    others = [p for p in game_state.players
              if not p.bankrupt and p.id != game_state.current_player.id]
    ow = 380
    oh = 54 + len(others) * 52 + 20
    ox = (BOARD_DISP_W - ow) // 2
    oy = (SCREEN_H - oh) // 2
    overlay = pygame.Surface((BOARD_DISP_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 200))
    surface.blit(overlay, (0, 0))
    pygame.draw.rect(surface, (15, 20, 50), pygame.Rect(ox, oy, ow, oh), border_radius=8)
    pygame.draw.rect(surface, COLORS["cell_border"],
                     pygame.Rect(ox, oy, ow, oh), 2, border_radius=8)
    draw_text(surface, title, ox + ow // 2, oy + 16,
              size=15, bold=True, color=COLORS["text_gold"], center=True)
    buttons = []
    by = oy + 46
    for p in others:
        r     = pygame.Rect(ox + 20, by, ow - 40, 40)
        col   = COLORS["owned_p"][p.id]
        emoji = p.EMOJIS[p.id]
        n_planets = len(p.planets)
        label = f"{emoji} {p.name}   💰{p.funds}   🌍×{n_planets}"
        buttons.append((Button(r, label, color=col), p.id))
        by += 52
    for btn, _ in buttons:
        btn.draw(surface)
    return buttons

# ─────────────────────────────
# 实验类型选择弹窗
# ─────────────────────────────
_EXP_NAMES   = ["采集矿物", "水实验", "植物实验"]
_EXP_COLORS  = [(160, 110, 60), (60, 150, 230), (60, 190, 80)]   # 棕 蓝 绿
_EXP_BTN_COL = [(100,  65, 30), (30,  100, 160), (30, 120,  50)]  # 按钮底色

def draw_exp_type_picker(surface, title, planet_id, done_exps=None):
    """实验类型选择弹窗，已完成的实验显示为灰色不可点击。"""
    from data import PLANETS
    exps = PLANETS.get(planet_id, {}).get("experiments", [])
    all_types = [i for i, v in enumerate(exps) if v]   # 所有支持的实验类型
    if done_exps is None:
        done_exps = [False, False, False]
    exp_name_list = [_lang.exp_name(i) for i in range(3)]

    ROW_H = 48
    ow = 380
    oh = 54 + len(all_types) * (ROW_H + 10) + 10
    ox = (BOARD_DISP_W - ow) // 2
    oy = (SCREEN_H - oh) // 2

    overlay = pygame.Surface((BOARD_DISP_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 20, 200))
    surface.blit(overlay, (0, 0))
    pygame.draw.rect(surface, (15, 20, 50), pygame.Rect(ox, oy, ow, oh), border_radius=8)
    pygame.draw.rect(surface, COLORS["cell_border"], pygame.Rect(ox, oy, ow, oh), 2, border_radius=8)
    draw_text(surface, title, ox + ow // 2, oy + 18,
              size=16, bold=True, color=COLORS["text_gold"], center=True)
    draw_text(surface, _lang.t("exp_formula"),
              ox + ow // 2, oy + 36, size=13, color=(140, 160, 140), center=True)

    by = oy + 52
    for idx in all_types:
        r = pygame.Rect(ox + 20, by, ow - 40, ROW_H)
        if done_exps[idx]:
            # 已完成：灰色背景 + 已完成标签
            pygame.draw.rect(surface, (40, 45, 55), r, border_radius=6)
            pygame.draw.rect(surface, (70, 80, 90), r, 1, border_radius=6)
            draw_text(surface, _lang.t("exp_done_lbl", name=exp_name_list[idx]),
                      r.centerx, r.centery, size=20, color=(100, 120, 100), center=True)
        else:
            btn = Button(r, exp_name_list[idx],
                         color=_EXP_BTN_COL[idx],
                         hover_color=tuple(min(255, c + 40) for c in _EXP_BTN_COL[idx]))
            btn.draw(surface)
        by += ROW_H + 10

# ─────────────────────────────
# 开始界面
# ─────────────────────────────
def draw_start_screen(surface, selected_players):
    if _board_surf:
        dark = _board_surf.copy()
        dark.set_alpha(80)
        surface.fill((5, 10, 30))
        surface.blit(dark, (SCREEN_W // 2 - BOARD_DISP_W // 2, 0))
    else:
        surface.fill(COLORS["bg"])

    draw_text(surface, _lang.t("title"),
              SCREEN_W // 2, 110, size=32, bold=True,
              color=COLORS["text_gold"], center=True)
    draw_text(surface, _lang.t("select_players"),
              SCREEN_W // 2, 175, size=17,
              color=COLORS["text_light"], center=True)

    # ── 语言切换按钮 (右上角) ──
    zh_r  = pygame.Rect(SCREEN_W - 180, 20, 70, 36)
    en_r  = pygame.Rect(SCREEN_W - 100, 20, 70, 36)
    cur = _lang.get_lang()
    for r, code, label in [(zh_r, "zh", "中文"), (en_r, "en", "EN")]:
        active = (cur == code)
        bg = (60, 130, 220) if active else (30, 40, 70)
        border = (120, 180, 255) if active else (60, 80, 120)
        pygame.draw.rect(surface, bg,     r, border_radius=6)
        pygame.draw.rect(surface, border, r, 2, border_radius=6)
        draw_text(surface, label, r.centerx, r.centery,
                  size=18, bold=active, color=(255, 255, 255), center=True)

    # 6 个玩家角色图标（每行3个，分2行）
    SPACING  = 185
    icons_x0 = SCREEN_W // 2 - SPACING * 2
    icon_y   = 430   # 第1行图标垂直中心
    icon_areas = []

    for i in range(MAX_PLAYERS):
        n     = i + 1
        row   = i // 3
        col   = i %  3
        ix    = icons_x0 + col * SPACING
        iy    = icon_y + row * 220   # 第2行偏移220px
        color = COLORS["owned_p"][i]
        active = (n <= selected_players)
        img   = _player_icons[i]

        if img:
            iw, ih = img.get_size()
            img_x  = ix - iw // 2
            img_y  = iy - ih // 2

            if active:
                # 高亮边框
                pygame.draw.rect(surface, (255, 240, 80),
                                 pygame.Rect(img_x - 6, img_y - 6, iw + 12, ih + 12),
                                 3, border_radius=10)
                pygame.draw.rect(surface, color,
                                 pygame.Rect(img_x - 3, img_y - 3, iw + 6, ih + 6),
                                 3, border_radius=8)
                surface.blit(img, (img_x, img_y))
            else:
                # 使用预生成的压暗版本，避免每帧分配 Surface
                dark = _player_icons_dark[i] or img
                pygame.draw.rect(surface, (40, 45, 65),
                                 pygame.Rect(img_x - 3, img_y - 3, iw + 6, ih + 6),
                                 2, border_radius=8)
                surface.blit(dark, (img_x, img_y))

            click_rect = pygame.Rect(img_x, img_y, iw, ih)
        else:
            # 无图时退回圆圈
            R = 55
            if active:
                pygame.draw.circle(surface, color, (ix, iy), R)
                pygame.draw.circle(surface, (255, 240, 80), (ix, iy), R + 6, 3)
            else:
                pygame.draw.circle(surface, tuple(c // 5 for c in color), (ix, iy), R)
            draw_text(surface, str(n), ix, iy, size=40, bold=True,
                      color=(255,255,255) if active else (60,65,90), center=True)
            click_rect = pygame.Rect(ix - R, iy - R, R * 2, R * 2)

        # 玩家名
        name_color = color if active else (55, 60, 80)
        player_name = _lang.player_name(i)
        draw_text(surface, player_name, ix, iy + 95,
                  size=16, color=name_color, center=True)

        icon_areas.append((click_rect, n))

    # 当前选择人数 + 开始按钮（放在两行图标下方）
    bottom_y = icon_y + 220 + 130   # 第2行中心 + 名字偏移 + 间距
    draw_text(surface, _lang.t("n_players", n=selected_players),
              SCREEN_W // 2, bottom_y,
              size=22, bold=True, color=COLORS["text_gold"], center=True)

    start_r   = pygame.Rect(SCREEN_W // 2 - 120, bottom_y + 48, 240, 62)
    start_btn = Button(start_r, _lang.t("start_game"),
                       color=(50, 150, 60), hover_color=(70, 190, 80))
    start_btn.draw(surface)

    draw_text(surface, _lang.t("credits"),
              SCREEN_W // 2, SCREEN_H - 25, size=12,
              color=(80, 100, 140), center=True)

    return icon_areas, start_btn, zh_r, en_r

# ─────────────────────────────
# 游戏结束界面
# ─────────────────────────────
def draw_skip_notice(surface, game_state):
    """显示停走通知弹窗，返回确认按钮 Rect"""
    player = game_state.current_player
    emoji  = player.EMOJIS[player.id]
    msg    = game_state.message   # 由 game.py 设置好的完整说明

    POP_W, POP_H = 480, 160
    ox = (BOARD_DISP_W - POP_W) // 2
    oy = (SCREEN_H - POP_H) // 2

    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    box = pygame.Surface((POP_W, POP_H), pygame.SRCALPHA)
    box.fill((30, 20, 60, 240))
    pygame.draw.rect(box, (180, 120, 220), box.get_rect(), 2, border_radius=10)
    surface.blit(box, (ox, oy))

    draw_text(surface, f"{emoji}  " + _lang.t("skip_notice_title"),
              ox + POP_W // 2, oy + 24,
              size=20, bold=True, color=(200, 160, 255), center=True)

    # 自动换行显示原因
    fn = get_font(15)
    words = msg
    max_w = POP_W - 48
    wrapped = []
    line = ""
    for ch in words:
        test = line + ch
        if fn.size(test)[0] > max_w:
            wrapped.append(line)
            line = ch
        else:
            line = test
    if line:
        wrapped.append(line)

    ty = oy + 58
    for wline in wrapped[:3]:
        draw_text(surface, wline, ox + POP_W // 2, ty,
                  size=15, color=COLORS["text_light"], center=True)
        ty += 22

    btn_rect = pygame.Rect(ox + POP_W // 2 - 70, oy + POP_H - 46, 140, 34)
    pygame.draw.rect(surface, (80, 50, 140), btn_rect, border_radius=6)
    pygame.draw.rect(surface, (160, 120, 220), btn_rect, 1, border_radius=6)
    draw_text(surface, _lang.t("skip_notice_ok"), btn_rect.centerx, btn_rect.centery,
              size=15, bold=True, color=(240, 220, 255), center=True)
    return btn_rect


def draw_fund_notice(surface, game_state):
    """显示资金变动通知弹窗"""
    events = game_state.fund_events
    if not events:
        return

    PAD     = 28
    ROW_H   = 76   # 两行：原因行(~28px) + 数值行(~32px) + 间距
    TITLE_H = 44
    BTN_H   = 44
    POP_W   = 560
    POP_H   = TITLE_H + PAD + len(events) * ROW_H + PAD + BTN_H + PAD

    ox = (BOARD_DISP_W - POP_W) // 2
    oy = (SCREEN_H - POP_H) // 2

    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    box = pygame.Surface((POP_W, POP_H), pygame.SRCALPHA)
    box.fill((20, 28, 60, 240))
    pygame.draw.rect(box, (100, 160, 255), box.get_rect(), 2, border_radius=10)
    surface.blit(box, (ox, oy))

    # 标题
    draw_text(surface, _lang.t("fund_title"), ox + POP_W // 2, oy + TITLE_H // 2,
              size=22, bold=True, color=COLORS["text_gold"], center=True)

    cy = oy + TITLE_H + PAD
    font_amt = get_font(27, bold=True)
    for ev in events:
        delta = ev["after"] - ev["before"]
        color = (100, 220, 120) if delta >= 0 else (240, 100, 100)
        sign  = "+" if delta >= 0 else ""
        # 第一行：玩家名 + 原因
        label = f"{ev['name']}  {ev['reason']}"
        draw_text(surface, label, ox + PAD, cy, size=24,
                  color=COLORS["text_light"])
        # 第二行：变化数值
        amount_str = _lang.t("fund_amount", b=ev['before'], a=ev['after'], s=sign, d=abs(delta))
        draw_text(surface, amount_str, ox + PAD, cy + 34, size=27, bold=True,
                  color=color)
        cy += ROW_H

    # 确认按钮 rect (returned for main.py to draw the Button over it)
    btn_rect = pygame.Rect(ox + POP_W // 2 - 70, oy + POP_H - BTN_H - PAD // 2,
                           140, BTN_H)
    return btn_rect


def draw_game_over(surface, game_state):
    alive   = [p for p in game_state.players if not p.bankrupt]
    winner  = alive[0] if alive else None
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))
    cx, cy = SCREEN_W // 2, SCREEN_H // 2
    draw_text(surface, _lang.t("over_title"),
              cx, cy - 100, size=38, bold=True,
              color=COLORS["text_gold"], center=True)
    if winner:
        draw_text(surface, _lang.t("over_winner", name=winner.name),
                  cx, cy - 44, size=28, bold=True,
                  color=COLORS["owned_p"][winner.id], center=True)
    ranked = sorted(game_state.players,
                    key=lambda p: (p.bankrupt, -p.net_worth))
    for i, p in enumerate(ranked):
        draw_text(surface,
                  _lang.t("over_rank", i=i + 1, name=p.name, w=p.net_worth),
                  cx, cy + 10 + i * 32, size=17,
                  color=COLORS["owned_p"][p.id], center=True)
    r_rect = pygame.Rect(cx - 90, cy + 160, 180, 52)
    restart_btn = Button(r_rect, _lang.t("play_again"),
                         color=(50, 90, 180), hover_color=(70, 120, 220))
    restart_btn.draw(surface)
    return restart_btn


# ─────────────────────────────
# 调试输入弹窗（Ctrl+G 前进步数）
# ─────────────────────────────
def draw_debug_input(surface, buf: str):
    """显示调试步数输入弹窗，返回弹窗区域 Rect（供外部判断点击区域）"""
    ow, oh = 280, 100
    ox = (BOARD_DISP_W - ow) // 2
    oy = SCREEN_H // 2 - 60
    overlay = pygame.Surface((BOARD_DISP_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    pygame.draw.rect(surface, (20, 30, 70), pygame.Rect(ox, oy, ow, oh), border_radius=8)
    pygame.draw.rect(surface, COLORS["cell_border"], pygame.Rect(ox, oy, ow, oh), 2, border_radius=8)
    draw_text(surface, "[Debug] Advance spaces (Enter)",
              ox + ow // 2, oy + 14, size=13, color=(180, 200, 255), center=True)
    # 输入框
    box = pygame.Rect(ox + 30, oy + 38, ow - 60, 34)
    pygame.draw.rect(surface, (10, 15, 40), box, border_radius=4)
    pygame.draw.rect(surface, COLORS["text_gold"], box, 1, border_radius=4)
    display = buf if buf else " "
    draw_text(surface, display, box.centerx, box.centery,
              size=20, bold=True, color=COLORS["text_gold"], center=True)
    draw_text(surface, "Esc: cancel",
              ox + ow // 2, oy + oh - 12, size=11, color=(120, 130, 160), center=True)
    return pygame.Rect(ox, oy, ow, oh)
