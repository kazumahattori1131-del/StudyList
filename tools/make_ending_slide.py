#!/usr/bin/env python3
"""
make_ending_slide.py
エンディングスライド（1280×720）を生成する
共有された数学デザイン背景 + チャンネル登録テキストオーバーレイ
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'
OUT_PATH  = Path('/home/user/StudyList/problems/youtube_redesign/ending_slide.png')

W, H = 1280, 720

GREEN      = (45, 130, 90)       # メイングリーン
LIGHT_GREEN = (200, 230, 210)    # 薄いグリーン
PALE_GREEN  = (232, 245, 236)    # 極薄グリーン
GRAY        = (160, 160, 160)
LIGHT_GRAY  = (210, 210, 210)
DOT_GRAY    = (200, 200, 200)
BG          = (252, 252, 252)    # ほぼ白

def font(size):
    return ImageFont.truetype(FONT_PATH, size)

def make_ending_slide():
    img  = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(img, 'RGBA')

    # ─── 左上：円と幾何学的構成 ──────────────────────────────────
    cx, cy, r = 130, 180, 130
    # 大きい円
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=GREEN, width=2)
    # 内部の点と線（コンパス作図風）
    pts = [
        (cx - int(r*0.6), cy - int(r*0.5)),
        (cx + int(r*0.5), cy - int(r*0.3)),
        (cx + int(r*0.1), cy + int(r*0.7)),
        (cx - int(r*0.7), cy + int(r*0.2)),
    ]
    for p in pts:
        draw.ellipse([p[0]-5, p[1]-5, p[0]+5, p[1]+5], fill=GREEN)
    for i in range(len(pts)):
        for j in range(i+1, len(pts)):
            draw.line([pts[i], pts[j]], fill=GREEN, width=1)
    # 破線の円弧（外側）
    r2 = int(r * 1.3)
    for angle in range(0, 360, 15):
        a1 = math.radians(angle)
        a2 = math.radians(angle + 8)
        x1 = cx + int(r2 * math.cos(a1))
        y1 = cy + int(r2 * math.sin(a1))
        x2 = cx + int(r2 * math.cos(a2))
        y2 = cy + int(r2 * math.sin(a2))
        draw.line([(x1, y1), (x2, y2)], fill=LIGHT_GRAY, width=1)
    # 十字線
    draw.line([(cx - r - 30, cy), (cx + r + 30, cy)], fill=GRAY, width=1)
    draw.line([(cx, cy - r - 30), (cx, cy + r + 30)], fill=GRAY, width=1)
    # 左端の帯（部分的に切れた）
    draw.rectangle([-5, 100, 8, 300], fill=(*LIGHT_GREEN, 180))

    # ─── 右上：正弦波グラフ ──────────────────────────────────────
    gx, gy = 1100, 170  # グラフ中心
    # 軸
    draw.line([(gx - 180, gy), (gx + 180, gy)], fill=GRAY, width=1)
    draw.line([(gx, gy - 90), (gx, gy + 50)], fill=GRAY, width=1)
    # 矢印
    draw.polygon([(gx+180, gy), (gx+170, gy-4), (gx+170, gy+4)], fill=GRAY)
    draw.polygon([(gx, gy-90), (gx-4, gy-80), (gx+4, gy-80)], fill=GRAY)
    # 正弦波
    prev = None
    for px in range(gx - 160, gx + 170, 2):
        t  = (px - gx) / 80.0 * math.pi
        py = gy - int(55 * math.sin(t))
        if prev:
            draw.line([prev, (px, py)], fill=GREEN, width=2)
        prev = (px, py)
    # 右端グリッド（薄い斜線）
    for i in range(0, 80, 12):
        draw.line([(W - 50 + i, 0), (W + i, 80)], fill=LIGHT_GRAY, width=1)

    # ─── 左下：ベクトル座標系 ────────────────────────────────────
    vx, vy = 190, 570
    draw.line([(vx - 60, vy), (vx + 100, vy)], fill=GRAY, width=1)
    draw.line([(vx, vy + 60), (vx, vy - 100)], fill=GRAY, width=1)
    draw.polygon([(vx+100, vy), (vx+90, vy-4), (vx+90, vy+4)], fill=GRAY)
    draw.polygon([(vx, vy-100), (vx-4, vy-90), (vx+4, vy-90)], fill=GRAY)
    # ベクトル線
    draw.line([(vx, vy), (vx + 70, vy - 70)], fill=GREEN, width=2)
    draw.polygon([(vx+70, vy-70), (vx+55, vy-62), (vx+62, vy-55)], fill=GREEN)
    # 破線の四角
    for i in range(0, 75, 8):
        draw.point([(vx + i, vy - 70)], fill=DOT_GRAY)
        draw.point([(vx + 70, vy - i)], fill=DOT_GRAY)
    # 小さい点（装飾）
    draw.ellipse([vx-6, vy-6, vx+6, vy+6], fill=GREEN)
    draw.ellipse([55, 580, 65, 590], fill=(*GREEN, 200))

    # ─── 右下：円に内接する三角形 ────────────────────────────────
    tx, ty, tr = 1180, 560, 130
    # 大きい円（薄いグリーン塗り）
    draw.ellipse([tx-tr-60, ty-20, tx+tr-20, ty+tr+40],
                 fill=(*PALE_GREEN, 200), outline=None)
    # 外接円
    draw.ellipse([tx-tr, ty-tr, tx+tr, ty+tr], outline=LIGHT_GRAY, width=1)
    # 破線円
    for angle in range(0, 360, 15):
        a1 = math.radians(angle)
        a2 = math.radians(angle + 8)
        draw.line([
            (tx + int((tr+20)*math.cos(a1)), ty + int((tr+20)*math.sin(a1))),
            (tx + int((tr+20)*math.cos(a2)), ty + int((tr+20)*math.sin(a2))),
        ], fill=LIGHT_GRAY, width=1)
    # 三角形の頂点
    tri_pts = [
        (tx, ty - tr),
        (tx - int(tr*math.sin(math.radians(60))), ty + int(tr*0.5)),
        (tx + int(tr*math.sin(math.radians(60))), ty + int(tr*0.5)),
    ]
    draw.polygon(tri_pts, outline=GREEN, fill=None)
    for p in tri_pts:
        draw.ellipse([p[0]-5, p[1]-5, p[0]+5, p[1]+5], fill=GREEN)
    # 直角マーク
    base_x = (tri_pts[1][0] + tri_pts[2][0]) // 2
    base_y = tri_pts[1][1]
    draw.rectangle([base_x-10, base_y-12, base_x+10, base_y], outline=GRAY, width=1)

    # ─── 点線グリッドパターン（2か所）────────────────────────────
    for gx2, gy2 in [(430, 680), (830, 130)]:
        for di in range(5):
            for dj in range(4):
                draw.ellipse([gx2+di*18-2, gy2+dj*18-2,
                              gx2+di*18+2, gy2+dj*18+2], fill=DOT_GRAY)

    # ─── 散らばった円（装飾）─────────────────────────────────────
    draw.ellipse([108, 395, 124, 411], outline=GRAY, width=1)   # 小さい白丸
    draw.ellipse([645, 758, 661, 774], outline=GRAY, width=1)
    draw.ellipse([58, 570, 68, 580], fill=(*GREEN, 200))
    draw.ellipse([295, 720, 315, 740], fill=(*LIGHT_GREEN, 200))
    draw.ellipse([330, 710, 345, 725], fill=(*GREEN, 180))
    draw.ellipse([1295, 330, 1311, 346], fill=(*LIGHT_GREEN, 200))

    # ─── オーバーレイテキスト（中央） ────────────────────────────
    # 半透明の白いパネル
    panel_x0, panel_y0 = 360, 200
    panel_x1, panel_y1 = 920, 520
    draw.rounded_rectangle([panel_x0, panel_y0, panel_x1, panel_y1],
                            radius=24, fill=(255, 255, 255, 220))

    # メインメッセージ
    f_main = font(54)
    f_sub  = font(36)
    f_small = font(28)

    lines = [
        (f_main,  '動画を最後まで見てくれて',  (40, 40, 40)),
        (f_main,  'ありがとうございます！',      GREEN),
        (None,    '',                            None),
        (f_sub,   'チャンネル登録・高評価で',   (60, 60, 60)),
        (f_sub,   '次の動画を見逃さずに！',      (60, 60, 60)),
        (None,    '',                            None),
        (f_small, 'コメントもお待ちしています！', (100, 100, 100)),
    ]

    y = panel_y0 + 28
    for fnt, text, color in lines:
        if fnt is None:
            y += 12
            continue
        tw = draw.textlength(text, font=fnt)
        draw.text(((W - tw) / 2, y), text, font=fnt, fill=color)
        y += fnt.size + 10

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUT_PATH), 'PNG')
    print(f'保存: {OUT_PATH}')


if __name__ == '__main__':
    make_ending_slide()
