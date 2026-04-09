# calibrate_tokens.py - 角色头像圆形标定工具
# 运行后逐一显示每个角色图片，你用两次点击标定头部圆圈：
#   第1次点击：头部圆心
#   第2次点击：圆形边缘（确定半径）
# 按 Enter 确认，按 R 重来，最终保存到 assets/token_crops.json

import pygame
import sys
import math
import json
import os

ASSETS_DIR  = os.path.join(os.path.dirname(__file__), "..", "assets")
PLAYERS_DIR = os.path.join(ASSETS_DIR, "players")
OUTPUT_JSON = os.path.join(ASSETS_DIR, "token_crops.json")

SCREEN_W, SCREEN_H = 900, 780
DISP_SIZE = 560   # 图片最大显示尺寸


def run():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("角色头像标定 – 圆心+边缘各点一次")
    clock  = pygame.time.Clock()

    try:
        font_big = pygame.font.SysFont("microsoftyahei", 22, bold=True)
        font_sm  = pygame.font.SysFont("microsoftyahei", 16)
    except Exception:
        font_big = pygame.font.SysFont(None, 26, bold=True)
        font_sm  = pygame.font.SysFont(None, 20)

    results = {}

    for pid in range(4):
        path = os.path.join(PLAYERS_DIR, f"player_{pid}.png")
        if not os.path.exists(path):
            print(f"[跳过] player_{pid}.png 不存在")
            continue

        src    = pygame.image.load(path).convert()
        orig_w, orig_h = src.get_size()
        scale  = DISP_SIZE / max(orig_w, orig_h)
        disp_w = int(orig_w * scale)
        disp_h = int(orig_h * scale)
        disp   = pygame.transform.smoothscale(src, (disp_w, disp_h))
        img_x  = (SCREEN_W - disp_w) // 2
        img_y  = 120

        center = None   # 屏幕坐标
        done   = False

        while not done:
            clock.tick(30)
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        center = None
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if center is not None:
                            # 用当前鼠标位置作为边缘确认
                            dx = mx - center[0]
                            dy = my - center[1]
                            r_screen = math.hypot(dx, dy)
                            cx_orig = int((center[0] - img_x) / scale)
                            cy_orig = int((center[1] - img_y) / scale)
                            r_orig  = max(1, int(r_screen / scale))
                            results[pid] = [cx_orig, cy_orig, r_orig]
                            done = True

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if center is None:
                        center = (mx, my)
                    else:
                        dx = mx - center[0]
                        dy = my - center[1]
                        r_screen = math.hypot(dx, dy)
                        cx_orig = int((center[0] - img_x) / scale)
                        cy_orig = int((center[1] - img_y) / scale)
                        r_orig  = max(1, int(r_screen / scale))
                        results[pid] = [cx_orig, cy_orig, r_orig]
                        done = True

            # ── 绘制 ──────────────────────────────
            screen.fill((10, 14, 30))
            screen.blit(disp, (img_x, img_y))

            # 计算当前预览圆（鼠标随动）
            if center is not None:
                dx = mx - center[0]
                dy = my - center[1]
                r_preview = int(math.hypot(dx, dy))
                pygame.draw.circle(screen, (255, 220, 0), center, max(1, r_preview), 2)
                pygame.draw.circle(screen, (255, 60,  0), center, 5)
                # 显示圆形裁剪预览（右侧小图）
                cx_orig = int((center[0] - img_x) / scale)
                cy_orig = int((center[1] - img_y) / scale)
                r_orig  = max(1, int(r_preview / scale))
                crop_rect = pygame.Rect(cx_orig - r_orig, cy_orig - r_orig,
                                        r_orig * 2, r_orig * 2)
                crop_rect = crop_rect.clip(pygame.Rect(0, 0, orig_w, orig_h))
                if crop_rect.width > 2 and crop_rect.height > 2:
                    crop_surf = src.subsurface(crop_rect)
                    preview_size = 120
                    ps = pygame.transform.smoothscale(crop_surf, (preview_size, preview_size))
                    # 做圆形遮罩
                    mask = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)
                    mask.fill((0, 0, 0, 0))
                    pygame.draw.circle(mask, (255,255,255,255),
                                       (preview_size//2, preview_size//2), preview_size//2)
                    ps_a = ps.convert_alpha()
                    ps_a.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                    px = SCREEN_W - preview_size - 20
                    py = 120
                    pygame.draw.rect(screen, (30,35,60),
                                     pygame.Rect(px-4, py-4, preview_size+8, preview_size+8),
                                     border_radius=4)
                    screen.blit(ps_a, (px, py))
                    t = font_sm.render("圆形预览", True, (160,180,220))
                    screen.blit(t, (px + preview_size//2 - t.get_width()//2, py + preview_size + 6))

            # 进度提示
            prog = font_big.render(
                f"玩家 {pid+1}/4    player_{pid}.png", True, (255, 215, 0))
            screen.blit(prog, (SCREEN_W//2 - prog.get_width()//2, 20))

            if center is None:
                hint = "① 点击头部圆心"
            else:
                hint = "② 移动到圆形边缘后：再次点击 或 按 Enter/Space 确认  |  R 重置"
            h = font_sm.render(hint, True, (200, 220, 255))
            screen.blit(h, (SCREEN_W//2 - h.get_width()//2, 60))

            pygame.display.flip()

    pygame.quit()

    # 保存结果
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n标定完成，已保存到 {OUTPUT_JSON}")
    print(json.dumps({str(k): v for k, v in results.items()}, indent=2))


if __name__ == "__main__":
    run()
