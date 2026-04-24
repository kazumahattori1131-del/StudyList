#!/usr/bin/env python3
"""
make_thumbnails.py
各動画のサムネイル画像（1280×720）を生成する
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

FONT_PATH = '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'
OUT_DIR   = Path('/home/user/StudyList/problems/youtube_redesign/thumbnails')
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def draw_text_centered(draw, text, y, max_width, fnt, fill):
    """中央揃えで複数行テキストを描画。max_width を超える場合は折り返す"""
    lines = []
    for raw_line in text.split('\n'):
        # 行ごとに幅チェックして折り返し
        words = list(raw_line)
        line = ''
        for ch in words:
            test = line + ch
            if draw.textlength(test, font=fnt) > max_width:
                if line:
                    lines.append(line)
                line = ch
            else:
                line = test
        lines.append(line)

    for line in lines:
        lw = draw.textlength(line, font=fnt)
        draw.text(((W - lw) / 2, y), line, font=fnt, fill=fill)
        y += fnt.size + 8
    return y


def draw_rect_rounded(draw, xy, radius=20, fill=None, outline=None, width=3):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


def make_thumbnail(stem, config):
    """
    config keys:
      bg_color      : 背景色 (R,G,B)
      accent        : アクセント色
      subject_tag   : 科目タグ文字列  例「数学I」
      subject_color : タグ背景色
      main_text     : 大きなメインコピー（2行まで推奨）
      sub_text      : サブテキスト（小さい）
      formula       : 数式文字列（中央下寄り）
      badge_text    : 右上バッジ文字列 例「落とし穴あり」
      badge_color   : バッジ色
    """
    bg   = config['bg_color']
    acc  = config['accent']

    img  = Image.new('RGB', (W, H), bg)
    draw = ImageDraw.Draw(img)

    # ── 背景デコレーション ──────────────────────────────────────
    # 左帯
    draw.rectangle([0, 0, 12, H], fill=acc)
    # 右下三角形装飾
    draw.polygon([(W, H - 220), (W, H), (W - 320, H)], fill=acc + (40,) if len(acc) == 3 else acc)
    # 薄いグリッド線（数学っぽさ）
    grid_color = tuple(min(255, c + 20) for c in bg)
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # ── 科目タグ ────────────────────────────────────────────────
    tag_fnt  = font(32)
    tag_text = config['subject_tag']
    tag_w    = draw.textlength(tag_text, font=tag_fnt) + 32
    tag_col  = config.get('subject_color', acc)
    draw_rect_rounded(draw, [60, 40, 60 + tag_w, 40 + 52], radius=10, fill=tag_col)
    draw.text((60 + 16, 48), tag_text, font=tag_fnt, fill=(255, 255, 255))

    # ── バッジ（右上） ─────────────────────────────────────────
    if config.get('badge_text'):
        b_fnt   = font(28)
        b_text  = config['badge_text']
        b_col   = config.get('badge_color', (220, 50, 50))
        b_w     = draw.textlength(b_text, font=b_fnt) + 28
        bx      = W - b_w - 40
        draw_rect_rounded(draw, [bx, 36, bx + b_w, 36 + 48], radius=10, fill=b_col)
        draw.text((bx + 14, 44), b_text, font=b_fnt, fill=(255, 255, 255))

    # ── メインコピー ─────────────────────────────────────────────
    m_fnt = font(72)
    y = 140
    for line in config['main_text'].split('\n'):
        lw = draw.textlength(line, font=m_fnt)
        # 影
        draw.text(((W - lw) / 2 + 3, y + 3), line, font=m_fnt, fill=(0, 0, 0, 80))
        draw.text(((W - lw) / 2, y), line, font=m_fnt, fill=(255, 255, 255))
        y += m_fnt.size + 10

    # ── サブテキスト ─────────────────────────────────────────────
    if config.get('sub_text'):
        s_fnt  = font(38)
        s_text = config['sub_text']
        sw     = draw.textlength(s_text, font=s_fnt)
        draw.text(((W - sw) / 2, y + 16), s_text, font=s_fnt,
                  fill=tuple(min(255, c + 160) for c in bg))
        y += s_fnt.size + 24

    # ── 数式ボックス ─────────────────────────────────────────────
    if config.get('formula'):
        f_fnt  = font(52)
        f_text = config['formula']
        fw     = draw.textlength(f_text, font=f_fnt)
        box_x0 = (W - fw) / 2 - 30
        box_y0 = H - 160
        box_x1 = (W + fw) / 2 + 30
        box_y1 = H - 70
        draw_rect_rounded(draw, [box_x0, box_y0, box_x1, box_y1],
                          radius=14, fill=(0, 0, 0, 0),
                          outline=acc, width=3)
        draw.text(((W - fw) / 2, box_y0 + 14), f_text, font=f_fnt, fill=acc)

    out_path = OUT_DIR / f'{stem}.png'
    img.save(out_path, 'PNG')
    print(f'  保存: {out_path.name}')
    return out_path


THUMBNAILS = {
    'math1_quadratic_discriminant': dict(
        bg_color      = (18, 24, 48),
        accent        = (66, 133, 244),
        subject_tag   = '数学I',
        subject_color = (30, 90, 200),
        main_text     = 'x軸と\n「2点で交わる」条件',
        sub_text      = '判別式 D の使い方、わかってる？',
        formula       = 'D > 0 が鍵！',
        badge_text    = '落とし穴あり',
        badge_color   = (200, 50, 50),
    ),
    'math1_quadratic_trap': dict(
        bg_color      = (48, 18, 18),
        accent        = (234, 88, 12),
        subject_tag   = '数学I',
        subject_color = (180, 50, 10),
        main_text     = '判別式だけで\n解くと間違える！',
        sub_text      = 'ax²+2x+a > 0 がすべての x で成立する条件',
        formula       = 'a > 0 も必須！',
        badge_text    = '超頻出の落とし穴',
        badge_color   = (180, 30, 30),
    ),
    'math2_exponential_substitution': dict(
        bg_color      = (18, 40, 30),
        accent        = (34, 197, 94),
        subject_tag   = '数学II',
        subject_color = (20, 140, 60),
        main_text     = '指数方程式を\n2次方程式に変換',
        sub_text      = '4^x - 3×2^x - 4 = 0 を一発で解く！',
        formula       = 't = 2^x と置く',
        badge_text    = None,
        badge_color   = None,
    ),
    'math2_log_substitution': dict(
        bg_color      = (20, 38, 48),
        accent        = (14, 165, 233),
        subject_tag   = '数学II',
        subject_color = (10, 110, 180),
        main_text     = '対数方程式を\nスッキリ解く方法',
        sub_text      = '底の変換 × 置換で2次式に帰着！',
        formula       = 'log を t に置換',
        badge_text    = None,
        badge_color   = None,
    ),
    'math3_integral_squared': dict(
        bg_color      = (28, 18, 48),
        accent        = (168, 85, 247),
        subject_tag   = '数学III',
        subject_color = (110, 40, 200),
        main_text     = '三角置換で\n定積分を攻略',
        sub_text      = '∫1/(1+x²)² dx、三角置換で一気に解く！',
        formula       = 'x = tanθ と置く',
        badge_text    = '発展レベル',
        badge_color   = (120, 40, 200),
    ),
    'math3_integration_by_parts': dict(
        bg_color      = (28, 18, 48),
        accent        = (236, 72, 153),
        subject_tag   = '数学III',
        subject_color = (160, 30, 100),
        main_text     = '部分積分を\n2回やると元に戻る！',
        sub_text      = '∫e^x sinx dx — 不思議な積分の解き方',
        formula       = '元に戻す逆算テク',
        badge_text    = '発展レベル',
        badge_color   = (160, 30, 100),
    ),
    'mathA_circular_nonadjacent': dict(
        bg_color      = (24, 36, 24),
        accent        = (74, 222, 128),
        subject_tag   = '数学A',
        subject_color = (30, 150, 60),
        main_text     = '円順列で\n「隣り合わない」確率',
        sub_text      = '余事象を使えば計算が一気に楽になる！',
        formula       = '余事象 で攻める',
        badge_text    = None,
        badge_color   = None,
    ),
    'mathA_circular_probability': dict(
        bg_color      = (24, 36, 24),
        accent        = (16, 185, 129),
        subject_tag   = '数学A',
        subject_color = (10, 130, 80),
        main_text     = '円順列で\n男女交互に並ぶ確率',
        sub_text      = '固定→残りを並べる、が解法の核心！',
        formula       = '1人固定が鍵',
        badge_text    = None,
        badge_color   = None,
    ),
    'mathB_recurrence_divide': dict(
        bg_color      = (40, 28, 18),
        accent        = (251, 146, 60),
        subject_tag   = '数学B',
        subject_color = (180, 90, 20),
        main_text     = '漸化式は\n両辺を割るだけ！',
        sub_text      = '等差数列に帰着させる変形テクニック',
        formula       = 'b(n) = a(n)/2^n と置く',
        badge_text    = None,
        badge_color   = None,
    ),
    'mathB_sum_recurrence': dict(
        bg_color      = (40, 28, 18),
        accent        = (245, 158, 11),
        subject_tag   = '数学B',
        subject_color = (170, 100, 10),
        main_text     = 'Sₙ型漸化式を\n一般項に直す方法',
        sub_text      = 'n≧2 と n=1 の場合分けが落とし穴！',
        formula       = 'a(n) = S(n) - S(n-1)',
        badge_text    = '場合分け注意',
        badge_color   = (180, 80, 20),
    ),
    'mathC_complex_factorize': dict(
        bg_color      = (18, 18, 40),
        accent        = (99, 102, 241),
        subject_tag   = '数学C',
        subject_color = (60, 50, 200),
        main_text     = '複素数の絶対値\n最大値を因数分解で',
        sub_text      = '|z²-1| の最大値、|z-1|=1 の条件を活かす！',
        formula       = '|AB| = |A||B| を使う',
        badge_text    = '発展レベル',
        badge_color   = (80, 50, 200),
    ),
    'mathC_complex_identity': dict(
        bg_color      = (18, 18, 40),
        accent        = (129, 140, 248),
        subject_tag   = '数学C',
        subject_color = (70, 60, 210),
        main_text     = 'z + 1/z = 1 から\nz³+1/z³ を求める',
        sub_text      = '複素数の恒等式を連鎖させる解法！',
        formula       = '3乗は2段階で',
        badge_text    = '発展レベル',
        badge_color   = (80, 50, 200),
    ),
    'math2_trig_compose': dict(
        bg_color      = (15, 28, 48),
        accent        = (14, 165, 233),
        subject_tag   = '数学II',
        subject_color = (10, 110, 180),
        main_text     = 'sinとcosを\n1つにまとめる！',
        sub_text      = '三角関数の合成 — αの符号ミスに注意',
        formula       = 'sinθ+√3cosθ=2sin(θ+π/3)',
        badge_text    = '落とし穴あり',
        badge_color   = (200, 50, 50),
    ),
}


if __name__ == '__main__':
    print(f'サムネイル生成 → {OUT_DIR}')
    for stem, cfg in THUMBNAILS.items():
        make_thumbnail(stem, cfg)
    print('完了')
