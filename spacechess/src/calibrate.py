# calibrate.py - 交互式格子精确标定（左上角 + 右下角）
# 运行: python calibrate.py
# 每格点两下（左上角 → 右下角），完成后输出32格中心坐标表

import pygame, sys, os, json

BOARD_PNG = os.path.join(os.path.dirname(__file__), "..", "assets", "background", "board.png")

CELL_NAMES = [
    "格1 地球", "格2", "格3", "格4", "格5", "格6", "格7", "格8",
    "格9", "格10", "格11", "格12", "格13", "格14", "格15", "格16",
    "格17 空间站", "格18", "格19", "格20", "格21", "格22", "格23", "格24",
    "格25 实验室", "格26", "格27", "格28", "格29", "格30", "格31", "格32",
]

def main():
    pygame.init()
    raw = pygame.image.load(BOARD_PNG)
    W, H = raw.get_size()
    scale = 850 / H
    bw, bh = int(W * scale), int(H * scale)
    sh = bh + 130
    screen = pygame.display.set_mode((bw, sh))
    pygame.display.set_caption("格子标定 - 左上角+右下角")
    board = pygame.transform.smoothscale(raw, (bw, bh))

    fn_title = pygame.font.SysFont("Microsoft YaHei", 28, bold=True)
    fn_body  = pygame.font.SysFont("Microsoft YaHei", 20)
    fn_hint  = pygame.font.SysFont("Microsoft YaHei", 16)

    cells = {}     # idx -> {"tl": (x,y), "br": (x,y)}
    current = 0    # 当前格子索引 (0-31)
    phase   = 0    # 0=等待左上角, 1=等待右下角
    pending_tl = None

    clock = pygame.time.Clock()
    mouse_pos = (0, 0)

    while current < 32:
        clock.tick(30)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_BACKSPACE:
                    # 退回上一步
                    if phase == 1:
                        phase = 0
                        pending_tl = None
                    elif current > 0:
                        current -= 1
                        if current in cells:
                            del cells[current]
                        phase = 0
                        pending_tl = None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if my > bh:
                    continue
                if phase == 0:
                    pending_tl = (mx, my)
                    phase = 1
                else:
                    # 确保左上在右下左上方
                    x0, y0 = pending_tl
                    x1, y1 = mx, my
                    tl = (min(x0,x1), min(y0,y1))
                    br = (max(x0,x1), max(y0,y1))
                    cells[current] = {"tl": tl, "br": br}
                    current += 1
                    phase = 0
                    pending_tl = None

        # ── 绘制 ──────────────────────────────────────
        screen.fill((15, 18, 35))
        screen.blit(board, (0, 0))

        # 已完成的格子：绿色矩形
        for idx, cell in cells.items():
            tl, br = cell["tl"], cell["br"]
            cx = (tl[0]+br[0])//2
            cy = (tl[1]+br[1])//2
            pygame.draw.rect(screen, (0, 200, 80),
                             pygame.Rect(tl[0], tl[1], br[0]-tl[0], br[1]-tl[1]), 2)
            t = fn_hint.render(str(idx+1), True, (0,200,80))
            screen.blit(t, (cx-8, cy-8))

        # 鼠标位置辅助线
        mx, my = mouse_pos
        if my < bh:
            pygame.draw.line(screen, (200,200,100), (mx,0), (mx,bh), 1)
            pygame.draw.line(screen, (200,200,100), (0,my), (bw,my), 1)

        # 当前格子的预览框（拖拽过程）
        if phase == 1 and pending_tl:
            x0,y0 = pending_tl
            x1,y1 = mx, min(my, bh)
            pygame.draw.rect(screen, (255,220,0),
                             pygame.Rect(min(x0,x1), min(y0,y1),
                                         abs(x1-x0), abs(y1-y0)), 2)
            pygame.draw.circle(screen, (255,100,0), pending_tl, 5)

        # ── 底部说明区 ──────────────────────────────────
        bar_y = bh + 8
        pygame.draw.rect(screen, (25, 30, 55), (0, bh, bw, 130))

        if current < 32:
            step_text = f"第 {current+1}/32 格：{CELL_NAMES[current]}"
            t = fn_title.render(step_text, True, (255, 220, 50))
            screen.blit(t, (20, bar_y))

            if phase == 0:
                t = fn_body.render("▶ 第1步：点击该格子的 【左上角】", True, (100, 220, 255))
            else:
                t = fn_body.render("▶ 第2步：点击该格子的 【右下角】", True, (255, 150, 80))
            screen.blit(t, (20, bar_y + 40))

            hint = "Backspace=退回  ESC=退出"
            t = fn_hint.render(hint, True, (120, 120, 160))
            screen.blit(t, (20, bar_y + 80))

            prog = f"进度: {current}/32"
            t = fn_hint.render(prog, True, (150, 200, 150))
            screen.blit(t, (bw - 150, bar_y + 10))
        else:
            t = fn_title.render("✓ 全部32格标定完成！", True, (0, 230, 100))
            screen.blit(t, (20, bar_y + 30))

        pygame.display.flip()

    pygame.quit()

    # ── 计算中心坐标并输出 ──────────────────────────────
    centers = []
    for idx in range(32):
        if idx in cells:
            tl, br = cells[idx]["tl"], cells[idx]["br"]
            cx = ((tl[0]+br[0])/2) / scale
            cy = ((tl[1]+br[1])/2) / scale
        else:
            cx, cy = 0, 0
        centers.append((cx, cy))

    print("\n=== 标定完成：32格中心坐标（原始图片像素） ===")
    print("CELL_CENTERS_IMG = [")
    for i, (cx, cy) in enumerate(centers):
        print(f"    ({cx:.1f}, {cy:.1f}),  # 格{i+1} {CELL_NAMES[i]}")
    print("]")

    # 保存到文件
    out = {"scale": scale, "cells": {str(k): v for k, v in cells.items()}}
    _bg_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "background")
    _out = os.path.join(_bg_dir, "calibration.json")
    with open(_out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n数据已保存到 {_out}")
    print("\n请把上面的 CELL_CENTERS_IMG 数组粘贴到 ui.py 替换公式计算方式。")

if __name__ == "__main__":
    main()
