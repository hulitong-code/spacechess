"""
星球圆形裁剪工具
- 显示 planet_1.jpg
- 鼠标拖拽画圆（按住左键=圆心，拖到边缘=半径）
- Enter 确认：批量裁剪全部 19 张，保存到 assets/planets/circles/
- R 键重置
"""

import os, sys
import pygame

ASSETS_DIR    = os.path.join(os.path.dirname(__file__), "..", "assets")
PLANET_DIR    = os.path.join(ASSETS_DIR, "planets")
CIRCLE_DIR    = os.path.join(ASSETS_DIR, "planets", "circles")
SOURCE_IMG    = os.path.join(PLANET_DIR, "planet_1.jpg")
CROP_SIZE     = 200   # 最终输出尺寸（正方形，然后代码里再圆形显示）

def run():
    pygame.init()
    raw_tmp = pygame.image.load(SOURCE_IMG)
    IW, IH = raw_tmp.get_size()

    # 缩放到适合屏幕展示（最大 1200px 宽）
    scale = min(1200 / IW, 900 / IH, 2.0)
    disp_w, disp_h = int(IW * scale), int(IH * scale)
    screen = pygame.display.set_mode((disp_w, disp_h + 60))
    pygame.display.set_caption("画圆选取星球区域 — 拖拽左键，Enter确认，R重置")

    raw = raw_tmp.convert()

    img_surf = pygame.transform.smoothscale(raw, (disp_w, disp_h))

    font = pygame.font.SysFont("microsoftyahei", 20) or pygame.font.SysFont(None, 22)

    center = None   # 显示坐标
    radius = 0
    dragging = False

    def hint(text, color=(220, 230, 255)):
        s = font.render(text, True, color)
        screen.blit(s, (10, disp_h + 16))

    clock = pygame.time.Clock()
    done  = False

    while not done:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                center   = ev.pos
                radius   = 0
                dragging = True

            elif ev.type == pygame.MOUSEMOTION and dragging:
                dx = ev.pos[0] - center[0]
                dy = ev.pos[1] - center[1]
                radius = int((dx**2 + dy**2) ** 0.5)

            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                dragging = False

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r:
                    center = None; radius = 0
                elif ev.key == pygame.K_RETURN and center and radius > 0:
                    done = True
                elif ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # ── 绘制 ──
        screen.fill((10, 10, 20))
        screen.blit(img_surf, (0, 0))

        # 提示栏
        pygame.draw.rect(screen, (20, 25, 50), pygame.Rect(0, disp_h, disp_w, 60))

        if center and radius > 0:
            # 半透明遮罩（圆外变暗）
            mask = pygame.Surface((disp_w, disp_h), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 140))
            pygame.draw.circle(mask, (0, 0, 0, 0), center, radius)
            screen.blit(mask, (0, 0))
            # 圆框
            pygame.draw.circle(screen, (255, 80, 80), center, radius, 2)
            # 圆心十字
            pygame.draw.line(screen, (255, 80, 80),
                             (center[0]-10, center[1]), (center[0]+10, center[1]), 1)
            pygame.draw.line(screen, (255, 80, 80),
                             (center[0], center[1]-10), (center[0], center[1]+10), 1)

            # 原图坐标（反算）
            orig_cx = int(center[0] / scale)
            orig_cy = int(center[1] / scale)
            orig_r  = int(radius / scale)
            hint(f"圆心({orig_cx},{orig_cy}) 半径{orig_r}px  |  Enter=确认裁剪  R=重置  Esc=退出")
        else:
            hint("按住左键拖拽画圆，覆盖星球区域")

        pygame.display.flip()
        clock.tick(60)

    # ── 用户确认，裁剪全部 ──
    orig_cx = int(center[0] / scale)
    orig_cy = int(center[1] / scale)
    orig_r  = int(radius / scale)

    print(f"裁剪参数：圆心=({orig_cx},{orig_cy})  半径={orig_r}px")

    try:
        from PIL import Image as PILImage
    except ImportError:
        print("需要 Pillow：pip install Pillow")
        pygame.quit(); sys.exit(1)

    os.makedirs(CIRCLE_DIR, exist_ok=True)
    ok, fail = 0, 0
    for pid in range(1, 20):
        src = os.path.join(PLANET_DIR, f"planet_{pid}.jpg")
        dst = os.path.join(CIRCLE_DIR, f"planet_{pid}.jpg")
        if not os.path.exists(src):
            print(f"  !! 找不到 {src}")
            fail += 1
            continue
        img = PILImage.open(src)
        box = (orig_cx - orig_r, orig_cy - orig_r,
               orig_cx + orig_r, orig_cy + orig_r)
        cropped = img.crop(box).resize((CROP_SIZE, CROP_SIZE), PILImage.LANCZOS)
        cropped.save(dst, "JPEG", quality=90)
        print(f"  OK planet_{pid}.jpg")
        ok += 1

    print(f"\n完成！{ok} 张成功，{fail} 张失败")
    print(f"图片已保存到 {CIRCLE_DIR}")

    # 在窗口里显示结果
    screen.fill((10, 10, 20))
    pygame.draw.rect(screen, (20, 25, 50), pygame.Rect(0, disp_h, disp_w, 60))
    # 用裁剪区域显示预览
    raw2 = pygame.image.load(SOURCE_IMG).convert()
    raw_crop = raw2.subsurface(pygame.Rect(
        max(0, orig_cx - orig_r), max(0, orig_cy - orig_r),
        min(orig_r*2, raw2.get_width()),
        min(orig_r*2, raw2.get_height())
    ))
    preview_size = min(300, disp_h - 20)
    preview = pygame.transform.smoothscale(raw_crop, (preview_size, preview_size))
    px = (disp_w - preview_size) // 2
    screen.blit(img_surf, (0, 0))
    mask2 = pygame.Surface((disp_w, disp_h), pygame.SRCALPHA)
    mask2.fill((0, 0, 0, 160))
    pygame.draw.circle(mask2, (0, 0, 0, 0), center, radius)
    screen.blit(mask2, (0, 0))
    pygame.draw.circle(screen, (80, 255, 80), center, radius, 3)
    f2 = font.render(f"Done! {ok} saved, press any key to exit", True, (80, 255, 80))
    screen.blit(f2, (10, disp_h + 16))
    pygame.display.flip()

    waiting = True
    while waiting:
        for ev in pygame.event.get():
            if ev.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False

    pygame.quit()

if __name__ == "__main__":
    run()
