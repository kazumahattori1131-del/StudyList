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
    'math1-01_quadratic_discriminant': dict(
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
    'math1-02_quadratic_trap': dict(
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
    'math2-01_exponential_substitution': dict(
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
    'math2-02_log_substitution': dict(
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
    'math3-01_integral_squared': dict(
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
    'math3-02_integration_by_parts': dict(
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
    'mathA-01_circular_nonadjacent': dict(
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
    'mathA-02_circular_probability': dict(
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
    'mathB-01_recurrence_divide': dict(
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
    'mathB-02_sum_recurrence': dict(
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
    'mathB-03_recurrence_char': dict(
        bg_color      = (28, 16, 6),
        accent        = (251, 146, 60),
        subject_tag   = '数学B',
        subject_color = (180, 80, 15),
        main_text     = '等差でも等比でも\nない漸化式の解き方',
        sub_text      = 'a(n+1)=3a(n)-4、特性方程式で一発！',
        formula       = 'α = pα + q が鍵',
        badge_text    = '入試頻出',
        badge_color   = (180, 60, 10),
    ),
    'mathC-01_complex_factorize': dict(
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
    'mathC-02_complex_identity': dict(
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
    'math2-03_trig_compose': dict(
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
    'math2-04_derivative_maxmin': dict(
        bg_color      = (10, 30, 18),
        accent        = (34, 197, 94),
        subject_tag   = '数学II',
        subject_color = (15, 130, 55),
        main_text     = '端点を\n忘れると爆死！',
        sub_text      = '微分の最大・最小 — 増減表だけでは不十分',
        formula       = 'f(4)=16 を見落とすな',
        badge_text    = '落とし穴あり',
        badge_color   = (200, 50, 50),
    ),
    'mathA-03_conditional_prob': dict(
        bg_color      = (10, 30, 15),
        accent        = (74, 222, 128),
        subject_tag   = '数学A',
        subject_color = (20, 150, 60),
        main_text     = '「〜のとき」\nに騙されるな！',
        sub_text      = '条件付き確率 — P(A|B)とP(B|A)は別物',
        formula       = 'P(A|B) = P(A∩B)/P(B)',
        badge_text    = '落とし穴あり',
        badge_color   = (200, 50, 50),
    ),
    'mathB-04_sum_arithmetic_geometric': dict(
        bg_color      = (40, 28, 18),
        accent        = (251, 146, 60),
        subject_tag   = '数学B',
        subject_color = (180, 90, 20),
        main_text     = 'k×2^kの和を\n一発で解く！',
        sub_text      = 'Σk・2^k、差し引き法で攻略！',
        formula       = 'S と 2S を並べて引く',
        badge_text    = '入試頻出',
        badge_color   = (180, 60, 10),
    ),
    'math1-03_quadratic_axis': dict(
        bg_color      = (36, 18, 8),
        accent        = (192, 86, 33),
        subject_tag   = '数学I',
        subject_color = (150, 60, 20),
        main_text     = '軸が動く！\n最大・最小の場合分け',
        sub_text      = '定義域が動くと何が起きるか？',
        formula       = '軸が区間内 / 区間外で分類',
        badge_text    = '場合分け必須',
        badge_color   = (180, 60, 20),
    ),
    'math2-05_integral_area': dict(
        bg_color      = (10, 28, 18),
        accent        = (60, 160, 100),
        subject_tag   = '数学II',
        subject_color = (20, 120, 60),
        main_text     = '定積分と面積\n1/12公式を使いこなせ！',
        sub_text      = '符号ミス・絶対値の落とし穴',
        formula       = '∫|f(x)|dx ← 符号に注意！',
        badge_text    = '落とし穴あり',
        badge_color   = (200, 50, 50),
    ),
    'math3-03_riemann_integral': dict(
        bg_color      = (28, 18, 8),
        accent        = (160, 100, 40),
        subject_tag   = '数学III',
        subject_color = (140, 80, 20),
        main_text     = '数列の極限を\n定積分に変換！',
        sub_text      = '区分求積法の完全解説',
        formula       = 'lim(1/n)Σf(k/n)=∫₀¹f(x)dx',
        badge_text    = '入試頻出',
        badge_color   = (140, 70, 20),
    ),
    'mathA-04_repeated_trial': dict(
        bg_color      = (20, 14, 36),
        accent        = (130, 100, 220),
        subject_tag   = '数学A',
        subject_color = (100, 70, 180),
        main_text     = '反復試行の確率\nC(n,r)を忘れるな！',
        sub_text      = '組み合わせの係数が消える落とし穴',
        formula       = 'C(n,r)・pʳ・(1-p)ⁿ⁻ʳ',
        badge_text    = '落とし穴あり',
        badge_color   = (180, 50, 180),
    ),
    'mathB-05_vector_inner': dict(
        bg_color      = (38, 24, 10),
        accent        = (251, 146, 60),
        subject_tag   = '数学B',
        subject_color = (180, 90, 20),
        main_text     = '内積と|a+b|の\n計算ミスをなくす！',
        sub_text      = '二乗して開くだけで解ける',
        formula       = '|a+b|²=|a|²+2a·b+|b|²',
        badge_text    = '落とし穴あり',
        badge_color   = (180, 60, 10),
    ),
    'mathC-03_complex_rotation': dict(
        bg_color      = (28, 10, 22),
        accent        = (210, 80, 160),
        subject_tag   = '数学C',
        subject_color = (160, 50, 120),
        main_text     = 'ド・モアブルで\n複素数の累乗を攻略！',
        sub_text      = 'z^n を一発で求める！',
        formula       = '(cosθ+isinθ)ⁿ=cos(nθ)+isin(nθ)',
        badge_text    = '入試頻出',
        badge_color   = (160, 40, 120),
    ),
    'math1-04_quadratic_complete': dict(
        bg_color      = (36, 18, 8),
        accent        = (192, 86, 33),
        subject_tag   = '数学I',
        subject_color = (150, 60, 20),
        main_text     = '平方完成を\n完全マスター！',
        sub_text      = '符号ミス・定数処理ミスをゼロに',
        formula       = 'a(x-p)²+q の形に変形',
        badge_text    = '計算ミス撲滅',
        badge_color   = (180, 60, 20),
    ),
    'math1-05_absolute_inequality': dict(
        bg_color      = (36, 18, 8),
        accent        = (192, 86, 33),
        subject_tag   = '数学I',
        subject_color = (150, 60, 20),
        main_text     = '絶対値の不等式\n場合分けで完全攻略！',
        sub_text      = '|A| < k の図形的意味から理解する',
        formula       = '|A|<k ⟺ -k<A<k',
        badge_text    = '落とし穴あり',
        badge_color   = (200, 50, 50),
    ),
    'math2-06_logarithm_concept': dict(
        bg_color      = (10, 28, 18),
        accent        = (60, 160, 100),
        subject_tag   = '数学II',
        subject_color = (20, 120, 60),
        main_text     = '「対数」って\n何者なのか？',
        sub_text      = '指数から対数へ—定義から理解する',
        formula       = 'log_a b=c ⟺ aᶜ=b',
        badge_text    = '概念理解',
        badge_color   = (20, 140, 60),
    ),
    'math2-07_trig_unit_circle': dict(
        bg_color      = (10, 28, 38),
        accent        = (60, 140, 200),
        subject_tag   = '数学II',
        subject_color = (20, 100, 170),
        main_text     = '単位円から\n三角関数を定義する！',
        sub_text      = '第2〜4象限でも迷わない',
        formula       = 'P(cosθ, sinθ) on unit circle',
        badge_text    = '定義から理解',
        badge_color   = (20, 100, 180),
    ),
    'math2-08_vieta_formulas': dict(
        bg_color      = (18, 16, 56),
        accent        = (99, 102, 241),
        subject_tag   = '数学II',
        subject_color = (60, 60, 200),
        main_text     = '解かなくていい！\n解と係数の関係',
        sub_text      = 'α²+β² は係数から一行で求まる',
        formula       = 'α²+β² = (α+β)² − 2αβ',
        badge_text    = '受験頻出',
        badge_color   = (80, 60, 220),
    ),
    'mathB-06_hypothesis_test': dict(
        bg_color      = (38, 24, 10),
        accent        = (251, 146, 60),
        subject_tag   = '数学B',
        subject_color = (180, 90, 20),
        main_text     = '仮説検定を\n完全理解！',
        sub_text      = '新課程必須—「偶然か否か」を数学で判断',
        formula       = 'p値 < 有意水準 → 帰無仮説棄却',
        badge_text    = '新課程必須',
        badge_color   = (200, 80, 10),
    ),
    'mathC-04_conic_sections': dict(
        bg_color      = (28, 10, 22),
        accent        = (210, 80, 160),
        subject_tag   = '数学C',
        subject_color = (160, 50, 120),
        main_text     = '楕円の方程式\n焦点を求める！',
        sub_text      = '「距離の和が一定」から式を導く',
        formula       = 'x²/a²+y²/b²=1 の焦点',
        badge_text    = '入試頻出',
        badge_color   = (160, 40, 120),
    ),
}


def make_thumbnail_vs(stem, config):
    """
    「地獄 vs 天国」左右対比レイアウト（CTR最大化デザイン）

    config keys:
      bg_color      : 背景色 (R,G,B)
      accent        : アクセント色（中央・装飾）
      subject_tag   : 科目タグ
      subject_color : タグ背景色
      badge_text    : 右上バッジ
      badge_color   : バッジ色
      top_copy      : 上部メインコピー（≤10文字推奨）
      hell_label    : 左ボックスの小ラベル（例「よくある誤答」）
      hell_value    : 左ボックスのメイン値（例「x > 2」）
      heaven_label  : 右ボックスの小ラベル（例「正しい答え」）
      heaven_value  : 右ボックスのメイン値（例「0 < x < 2」）
      bottom_copy   : 下部小テキスト
    """
    bg  = config['bg_color']
    acc = config['accent']

    img  = Image.new('RGB', (W, H), bg)
    draw = ImageDraw.Draw(img)

    # 背景グリッド
    grid = tuple(min(255, c + 15) for c in bg)
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=grid, width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=grid, width=1)

    # 左帯
    draw.rectangle([0, 0, 10, H], fill=acc)

    # ── 科目タグ（左上）
    tag_fnt = font(30)
    tag_w   = draw.textlength(config['subject_tag'], font=tag_fnt) + 28
    draw_rect_rounded(draw, [52, 36, 52 + tag_w, 36 + 48],
                      radius=8, fill=config.get('subject_color', acc))
    draw.text((52 + 14, 43), config['subject_tag'], font=tag_fnt, fill=(255, 255, 255))

    # ── バッジ（右上）
    if config.get('badge_text'):
        b_fnt = font(28)
        b_w   = draw.textlength(config['badge_text'], font=b_fnt) + 28
        bx    = W - b_w - 36
        draw_rect_rounded(draw, [bx, 32, bx + b_w, 32 + 48],
                          radius=8, fill=config.get('badge_color', (200, 40, 40)))
        draw.text((bx + 14, 40), config['badge_text'], font=b_fnt, fill=(255, 255, 255))

    # ── トップコピー（中央）
    tc_fnt = font(82)
    tc     = config['top_copy']
    tc_w   = draw.textlength(tc, font=tc_fnt)
    draw.text(((W - tc_w) / 2 + 3, 103), tc, font=tc_fnt, fill=(0, 0, 0, 100))
    draw.text(((W - tc_w) / 2,     100), tc, font=tc_fnt, fill=(255, 255, 255))

    def draw_cross_icon(cx, cy, r, clr):
        """❌ の代替：円 + ×線を PIL で描画"""
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=clr, width=5)
        m = int(r * 0.55)
        draw.line([cx - m, cy - m, cx + m, cy + m], fill=clr, width=6)
        draw.line([cx + m, cy - m, cx - m, cy + m], fill=clr, width=6)

    def draw_check_icon(cx, cy, r, clr):
        """✅ の代替：円 + チェックマークを PIL で描画"""
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=clr, width=5)
        # チェック: 左下→中央底→右上
        m = int(r * 0.55)
        pts = [cx - m, cy + int(m * 0.1),
               cx - int(m * 0.1), cy + m,
               cx + m, cy - int(m * 0.7)]
        draw.line(pts, fill=clr, width=6)

    # ── 左ボックス（地獄）
    BOX_Y0, BOX_Y1 = 218, 560
    LX0, LX1 = 60, 570
    draw_rect_rounded(draw, [LX0, BOX_Y0, LX1, BOX_Y1], radius=18,
                      fill=(80, 10, 10), outline=(220, 50, 50), width=4)
    # × アイコン（PIL 描画）
    draw_cross_icon(LX0 + 52, BOX_Y0 + 48, 28, (255, 80, 80))
    # 小ラベル
    hl_fnt = font(30)
    hl_w   = draw.textlength(config['hell_label'], font=hl_fnt)
    draw.text(((LX0 + LX1) / 2 - hl_w / 2, BOX_Y0 + 20),
              config['hell_label'], font=hl_fnt, fill=(255, 120, 120))
    # メイン値
    hv_fnt = font(68)
    hv_w   = draw.textlength(config['hell_value'], font=hv_fnt)
    draw.text(((LX0 + LX1) / 2 - hv_w / 2, BOX_Y0 + 80),
              config['hell_value'], font=hv_fnt, fill=(255, 80, 80))
    # 補足テキスト
    if config.get('hell_note'):
        hn_fnt = font(26)
        hn_w   = draw.textlength(config['hell_note'], font=hn_fnt)
        draw.text(((LX0 + LX1) / 2 - hn_w / 2, BOX_Y0 + 168),
                  config['hell_note'], font=hn_fnt, fill=(200, 100, 100))

    # ── 中央矢印
    arr_fnt = font(72)
    arr_w   = draw.textlength('→', font=arr_fnt)
    draw.text((W / 2 - arr_w / 2, (BOX_Y0 + BOX_Y1) / 2 - 40),
              '→', font=arr_fnt, fill=acc)

    # ── 右ボックス（天国）
    RX0, RX1 = 710, W - 36
    draw_rect_rounded(draw, [RX0, BOX_Y0, RX1, BOX_Y1], radius=18,
                      fill=(10, 60, 20), outline=(50, 200, 80), width=4)
    # チェック アイコン（PIL 描画）
    draw_check_icon(RX0 + 52, BOX_Y0 + 48, 28, (80, 220, 80))
    # 小ラベル
    vl_fnt = font(30)
    vl_w   = draw.textlength(config['heaven_label'], font=vl_fnt)
    draw.text(((RX0 + RX1) / 2 - vl_w / 2, BOX_Y0 + 20),
              config['heaven_label'], font=vl_fnt, fill=(120, 255, 120))
    # メイン値
    vv_fnt = font(68)
    vv_w   = draw.textlength(config['heaven_value'], font=vv_fnt)
    draw.text(((RX0 + RX1) / 2 - vv_w / 2, BOX_Y0 + 80),
              config['heaven_value'], font=vv_fnt, fill=(80, 255, 120))
    # 補足テキスト
    if config.get('heaven_note'):
        vn_fnt = font(26)
        vn_w   = draw.textlength(config['heaven_note'], font=vn_fnt)
        draw.text(((RX0 + RX1) / 2 - vn_w / 2, BOX_Y0 + 168),
                  config['heaven_note'], font=vn_fnt, fill=(100, 220, 130))

    # ── ボトムコピー
    if config.get('bottom_copy'):
        bc_fnt = font(34)
        bc_w   = draw.textlength(config['bottom_copy'], font=bc_fnt)
        draw.text(((W - bc_w) / 2, BOX_Y1 + 22),
                  config['bottom_copy'], font=bc_fnt,
                  fill=tuple(min(255, c + 160) for c in bg))

    out_path = OUT_DIR / f'{stem}.png'
    img.save(out_path, 'PNG')
    print(f'  保存: {out_path.name}')
    return out_path


# 「地獄 vs 天国」レイアウトのサムネイル設定
VS_THUMBNAILS = {
    'math2-10_log_inequality': dict(
        bg_color     = (14, 6, 30),          # 深紫
        accent       = (168, 85, 247),        # 紫
        subject_tag  = '数学II・対数不等式',
        subject_color= (90, 30, 160),
        badge_text   = '模試頻出の罠',
        badge_color  = (180, 30, 30),
        top_copy     = '不等号が逆転！',       # 8文字 ✓
        hell_label   = 'よくある誤答',
        hell_value   = 'x > 2',
        hell_note    = '底を確認しないと…',
        heaven_label = '正しい答え',
        heaven_value = '0 < x < 2',
        heaven_note  = '底 1/2 → 不等号逆転',
        bottom_copy  = 'log(1/2) x > -1  |  底が1未満で答えが丸ごと逆になる',
    ),
    'mathB-07_vector_magnitude': dict(
        bg_color     = (10, 18, 38),         # 深紺
        accent       = (251, 146, 60),        # 橙
        subject_tag  = '数学B・ベクトル',
        subject_color= (160, 80, 10),
        badge_text   = '計算ミスの定番',
        badge_color  = (180, 60, 10),
        top_copy     = '|a+b|=5は間違い！',
        hell_label   = 'よくある誤答',
        hell_value   = '|a+b| = 5',
        hell_note    = '大きさをそのまま足した…',
        heaven_label = '正しい答え',
        heaven_value = '|a+b| = √21',
        heaven_note  = '二乗→内積展開→平方根',
        bottom_copy  = '|a|=3, |b|=2, a・b=4  |  大きさは足し算できない',
    ),
}


if __name__ == '__main__':
    print(f'サムネイル生成 → {OUT_DIR}')
    for stem, cfg in THUMBNAILS.items():
        make_thumbnail(stem, cfg)
    for stem, cfg in VS_THUMBNAILS.items():
        make_thumbnail_vs(stem, cfg)
    print('完了')
