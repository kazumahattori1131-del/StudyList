#!/usr/bin/env python3
"""
slide_to_video.py
HTML slides + _voice.md scripts → MP4 videos

Usage:
    GOOGLE_API_KEY=xxx python3 tools/slide_to_video.py
    GOOGLE_API_KEY=xxx python3 tools/slide_to_video.py --file problems/youtube_redesign/{stem}.html

TTS: Google Cloud Text-to-Speech API (texttospeech.googleapis.com)
     GCPコンソールで発行したAPIキーを使用。Cloud Text-to-Speech APIを有効化すること。
"""

import os
import re
import time
import wave
import base64
import hashlib
import argparse
import requests
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from google import genai
from google.genai import types as genai_types
from playwright.sync_api import sync_playwright
from moviepy import VideoFileClip, concatenate_videoclips, ImageClip, AudioFileClip

# ── 設定 ──────────────────────────────────────────────────────────────────
CHROME_PATH   = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
KATEX_BASE    = 'file:///home/user/StudyList/problems/katex'
BASE_DIR      = Path('/home/user/StudyList/problems/youtube_redesign')
OUTPUT_DIR    = BASE_DIR / 'output'
ENDING_SLIDE  = BASE_DIR / 'ending_slide.png'
THUMBNAILS_DIR = BASE_DIR / 'thumbnails'
CLOUD_TTS_URL = 'https://texttospeech.googleapis.com/v1/text:synthesize'
# Cloud TTS 声の選択肢:
#   'ja-JP-Chirp3-HD-Leda'  ← Chirp3-HD 高品質（pitch非対応）
#   'ja-JP-Neural2-B'       ← Neural2 男性
TTS_VOICE     = 'ja-JP-Chirp3-HD-Leda'   # Cloud TTS フォールバック用
# Gemini TTS（AI Studio キーがある場合に優先使用）
# 声の選択肢: Kore / Aoede / Charon / Fenrir / Puck / Zephyr 等
GEMINI_TTS_MODEL = 'gemini-2.5-flash-preview-tts'
GEMINI_TTS_VOICE = 'Leda'          # 日本語教育コンテンツ向け
# Audio Profile: 若い日本語の声、落ち着いて自然、考えながら話す、ロボットっぽくない
GEMINI_TTS_STYLE = (
    "あなたは高校生・受験生に数学を解説する、若くて落ち着いた日本語の声です。"
    "以下の特徴を守って話してください：\n"
    "- 人間らしく自然な間とリズム（機械的・平坦にしない）\n"
    "- 考えながら話すような、少し呼吸を感じるテンポ\n"
    "- 親しみやすく、熱意が伝わるが押しつけがましくない口調\n"
    "- ポイントを強調するときはわずかに力を込める\n"
    "- 声の高さは中低程度で安定させる"
)
TTS_RATE      = 24000               # LINEAR16 出力サンプルレート
GAP_SECONDS   = 1.2                 # スライド切り替え後の無音（秒）

# ── API 使用量トラッキング ────────────────────────────────────────────────
# Gemini 2.5 Flash TTS 推定単価（参考: https://ai.google.dev/gemini-api/docs/pricing）
_COST_PER_1M_INPUT_TOKENS = 0.30   # $0.30/1M input tokens（概算）
_JPY_PER_USD               = 150   # 参考レート（適宜更新）
_usage: dict = {'api_calls': 0, 'cached_calls': 0, 'input_chars': 0, 'input_tokens': 0}
VIDEO_W, VIDEO_H = 1280, 720
VIDEO_FPS     = 24
# ─────────────────────────────────────────────────────────────────────────

# ── アノテーション（追い装飾）───────────────────────────────────────────────
_CIRCLED = {'①':1,'②':2,'③':3,'④':4,'⑤':5,'⑥':6,'⑦':7,'⑧':8,'⑨':9,'⑩':10}

INTRO_TEXT = """みなさんこんにちは！
このチャンネルでは、高校数学の典型問題・ひっかかりやすい問題を解説しています。
もしよろしければチャンネル登録よろしくお願いします！
では、今日の問題はこちらです！"""

OUTRO_TEMPLATE = """今回は「{title}」について解説しました。

この解法を知っておくだけで、入試本番で同じタイプの問題が出たとき、迷わず手が動きます。典型パターンをひとつひとつ押さえていけば、確実に点数が安定します。

役に立ったと感じた方は、チャンネル登録と高評価で応援してください！次回も、入試で差がつく重要ポイントを解説します。
疑問点や解説してほしい問題があれば、コメントで教えてもらえると助かります。それでは！"""


def parse_animations_from_edit(edit_path: Path) -> dict[int, list[dict]]:
    """_edit.md の「① 追い装飾指示」を解析 → {スライド番号(1-based): [spec, ...]}

    spec keys: target(強調対象), method(方法), animation(種類), timing(タイミングテキスト)
    """
    if not edit_path.exists():
        return {}
    text = edit_path.read_text()

    m = re.search(r'## ① 追い装飾指示(.+?)(?=\n## |\Z)', text, re.DOTALL)
    if not m:
        return {}
    section = m.group(1)

    result: dict[int, list[dict]] = {}
    for block_m in re.finditer(
        r'###\s+\[Slide([①②③④⑤⑥⑦⑧⑨⑩])[^\]]*\]\s*\n(.*?)(?=###\s+\[Slide|\Z)',
        section, re.DOTALL
    ):
        slide_num = _CIRCLED.get(block_m.group(1), 0)
        if not slide_num:
            continue
        anns = []
        for ann_m in re.finditer(r'\*\*強調\d+\*\*\s*\n((?:- .+\n?)+)', block_m.group(2)):
            spec: dict = {}
            for line in ann_m.group(1).splitlines():
                line = line.lstrip('- ').strip()
                if line.startswith('強調対象：'):
                    spec['target'] = line[5:].strip().strip('`')
                elif line.startswith('方法：'):
                    spec['method'] = line[3:].strip()
                elif line.startswith('アニメーション：'):
                    spec['animation'] = line[8:].strip()
                elif line.startswith('タイミング：'):
                    tm = re.search(r'「(.+?)」', line)
                    spec['timing'] = tm.group(1) if tm else ''
            if 'target' in spec and 'method' in spec:
                anns.append(spec)
        if anns:
            result[slide_num] = anns
    return result


def _extract_plain_keywords(target: str) -> list[str]:
    """強調対象から LaTeX($...$)を除いた検索キーワードを返す"""
    plain = re.sub(r'\$[^$]+\$', ' ', target.strip('`'))
    plain = re.sub(r'[※→（）「」！？。、＊\*]', ' ', plain)
    words = plain.split()
    return [w for w in words if len(w) >= 2]


def _find_bbox_in_page(page, keywords: list[str]) -> dict | None:
    """Playwright ページ内でキーワードに一致するテキストノードの親要素の bbox を返す"""
    for kw in keywords:
        safe_kw = kw.replace('\\', '\\\\').replace("'", "\\'")
        bbox = page.evaluate(f"""(() => {{
            const slide = document.querySelector('.slide.active');
            if (!slide) return null;
            const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
            let node;
            while (node = walker.nextNode()) {{
                if (node.textContent.trim().includes('{safe_kw}')) {{
                    let el = node.parentElement;
                    const inline = ['SPAN','EM','STRONG','SUP','SUB','KBD','A','CODE'];
                    while (el && inline.includes(el.tagName)) el = el.parentElement;
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    if (r.width < 4 || r.height < 4) return null;
                    return {{x: Math.round(r.left), y: Math.round(r.top),
                             w: Math.round(r.width), h: Math.round(r.height)}};
                }}
            }}
            return null;
        }})()""")
        if bbox:
            return bbox
    return None


def _find_timing_ratio(voice_script: str, timing_text: str) -> float:
    """台本内でタイミングテキストが現れる相対位置 (0.0–1.0) を返す"""
    if not timing_text:
        return 0.5
    idx = voice_script.find(timing_text)
    if idx == -1:
        for n in range(min(8, len(timing_text)), 2, -1):
            idx = voice_script.find(timing_text[:n])
            if idx != -1:
                break
    if idx == -1:
        return 0.5
    return idx / max(len(voice_script), 1)


def _draw_annotation(img: Image.Image, bbox: dict, method: str) -> Image.Image:
    """PIL Image にアノテーション（赤枠/丸枠/矢印）を描画して返す"""
    img = img.copy().convert('RGBA')
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']
    pad = 10
    color = (220, 20, 20, 235)
    lw = 4
    x0, y0, x1, y1 = x - pad, y - pad, x + w + pad, y + h + pad
    # 画面内に収める
    x0, y0 = max(x0, 2), max(y0, 2)
    x1, y1 = min(x1, VIDEO_W - 2), min(y1, VIDEO_H - 2)

    m_lower = method.lower()
    if '丸' in m_lower or '円' in m_lower:
        draw.ellipse([x0, y0, x1, y1], outline=color, width=lw)
    elif '矢印' in m_lower:
        ax, ay = max(0, x0 - 55), max(0, y0 - 55)
        draw.line([ax, ay, x0 + 12, y0 + 12], fill=color, width=lw)
        dx, dy = (x0 + 12) - ax, (y0 + 12) - ay
        length = (dx**2 + dy**2) ** 0.5
        if length > 0:
            ux, uy = dx / length, dy / length
            px, py = -uy, ux
            tip = (x0 + 12, y0 + 12)
            p1 = (tip[0] - ux * 16 + px * 8, tip[1] - uy * 16 + py * 8)
            p2 = (tip[0] - ux * 16 - px * 8, tip[1] - uy * 16 - py * 8)
            draw.polygon([tip, p1, p2], fill=color)
    else:
        # デフォルト：赤枠（四角）
        draw.rectangle([x0, y0, x1, y1], outline=color, width=lw)

    return Image.alpha_composite(img, overlay).convert('RGB')


def make_slide_clip_animated(img_path: Path, audio_path: Path, clip_path: Path,
                              annotations: list[dict], voice_script: str) -> None:
    """アノテーション付きスライドクリップを生成（アノテーションはタイミングで段階的に表示）"""
    audio = AudioFileClip(str(audio_path))
    total_dur = audio.duration

    # タイミング計算してソート
    timed = sorted(
        [(max(0.0, _find_timing_ratio(voice_script, a.get('timing', '')) * total_dur), a)
         for a in annotations],
        key=lambda x: x[0]
    )

    # ベース画像から始まり、アノテーションを順次追加したセグメントを作る
    base = Image.open(img_path).convert('RGB')
    segments: list[tuple[float, Image.Image]] = [(0.0, base)]
    current = base
    for t, ann in timed:
        bbox = ann.get('bbox')
        if not bbox:
            continue
        current = _draw_annotation(current.convert('RGBA'), bbox, ann.get('method', '赤枠'))
        segments.append((t, current))

    # 重複タイミングがある場合は最後のもので上書き（同秒に2つ以上来ない前提）
    clips = []
    for i, (start_t, img) in enumerate(segments):
        end_t = segments[i + 1][0] if i + 1 < len(segments) else total_dur
        dur = max(end_t - start_t, 0.05)
        clips.append(ImageClip(np.array(img), duration=dur))

    combined = concatenate_videoclips(clips).with_audio(audio)
    tmp = clip_path.with_suffix('.tmp_audio.mp4')
    combined.write_videofile(str(clip_path), fps=VIDEO_FPS, codec='libx264',
                             audio_codec='aac', logger=None,
                             temp_audiofile=str(tmp),
                             ffmpeg_params=['-pix_fmt', 'yuv420p'])
    audio.close()
    combined.close()


def pcm_to_wav(pcm: bytes, out_path: Path, gap_seconds: float = 0.0) -> None:
    """生 PCM（LINEAR16）→ WAV ファイル保存。末尾に gap_seconds 秒の無音を追加"""
    silence = b'\x00\x00' * int(TTS_RATE * gap_seconds)
    with wave.open(str(out_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(TTS_RATE)
        wf.writeframes(pcm + silence)


def patch_html(html: str) -> str:
    """CDN KaTeX URL → ローカルパスに差し替え"""
    return (html
        .replace('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css',
                 f'{KATEX_BASE}/katex.min.css')
        .replace('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js',
                 f'{KATEX_BASE}/katex.min.js')
        .replace('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js',
                 f'{KATEX_BASE}/auto-render.min.js'))


def find_ruidai_index(html: str) -> int | None:
    """「類題」バッジを持つスライドの 0-based インデックスを返す"""
    sections = re.split(r'(?=<section class="slide)', html)
    count = 0
    for section in sections:
        if not section.startswith('<section class="slide'):
            continue
        if re.search(r'class="badge[^"]*green[^"]*"[^>]*>\s*類題\s*<', section):
            return count
        count += 1
    return None


def split_ruidai_script(script: str) -> tuple[str, str]:
    """類題台本を問題提示部分と解答部分に最初の空行で分割"""
    parts = script.split('\n\n', 1)
    problem  = parts[0].strip()
    solution = parts[1].strip() if len(parts) > 1 else ''
    return problem, solution


def write_silence_wav(out_path: Path, duration: float) -> None:
    """指定秒数の無音 WAV を生成"""
    silence = b'\x00\x00' * int(TTS_RATE * duration)
    with wave.open(str(out_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(TTS_RATE)
        wf.writeframes(silence)


def screenshot_slides(
    html_path: Path, out_dir: Path,
    animation_targets: dict[int, list[str]] | None = None,
) -> tuple[list[Path], Path | None, dict[int, list[dict | None]]]:
    """HTML の全スライドをスクリーンショット → (PNG リスト, 類題解答非表示PNG, bboxes)

    animation_targets: {スライド番号(1-based): [強調対象テキスト, ...]}
    bboxes: {スライド番号(1-based): [bbox_or_None, ...]}
    """
    with open(html_path) as f:
        html = f.read()

    slide_count = len(re.findall(r'<section class="slide', html))
    ruidai_idx  = find_ruidai_index(html)
    tmp_path    = html_path.resolve().parent / '_tmp_preview.html'

    try:
        tmp_path.write_text(patch_html(html))

        shots: list[Path] = []
        ruidai_hidden: Path | None = None
        bboxes: dict[int, list[dict | None]] = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=CHROME_PATH,
                headless=True,
                args=['--no-sandbox', '--allow-file-access-from-files',
                      '--lang=ja-JP', '--accept-lang=ja-JP'],
            )
            page = browser.new_page(
                viewport={'width': VIDEO_W, 'height': VIDEO_H},
                locale='ja-JP',
            )
            page.goto(f'file://{tmp_path.resolve()}')
            page.wait_for_timeout(3000)
            page.evaluate("document.getElementById('nav').style.display='none'")

            for i in range(slide_count):
                slide_num = i + 1  # 1-based

                if i == ruidai_idx:
                    page.evaluate(
                        "document.querySelectorAll('.slide.active .step,"
                        " .slide.active .answer-label, .slide.active .answer-box')"
                        ".forEach(el => el.style.display='none')"
                    )
                    hidden_png = out_dir / 'slide_ruidai_hidden.png'
                    page.screenshot(path=str(hidden_png))
                    ruidai_hidden = hidden_png
                    page.evaluate(
                        "document.querySelectorAll('.slide.active .step,"
                        " .slide.active .answer-label, .slide.active .answer-box')"
                        ".forEach(el => el.style.display='')"
                    )

                # bbox 取得（アニメーション対象が指定されている場合）
                if animation_targets and slide_num in animation_targets:
                    slide_bboxes = []
                    for target in animation_targets[slide_num]:
                        keywords = _extract_plain_keywords(target)
                        bbox = _find_bbox_in_page(page, keywords) if keywords else None
                        slide_bboxes.append(bbox)
                    bboxes[slide_num] = slide_bboxes

                png = out_dir / f'slide_{i+1:02d}.png'
                page.screenshot(path=str(png))
                shots.append(png)

                if i < slide_count - 1:
                    page.keyboard.press('ArrowRight')
                    page.wait_for_timeout(350)

            browser.close()
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    return shots, ruidai_hidden, bboxes


def parse_voice_scripts(voice_path: Path) -> list[str]:
    """_voice.md → スライドごとの台本リスト"""
    with open(voice_path) as f:
        content = f.read()
    parts = re.split(r'^##\s+スライド[①②③④⑤⑥⑦⑧⑨⑩].*$', content, flags=re.MULTILINE)
    return [p.strip() for p in parts[1:] if p.strip()]


def parse_slide_labels(voice_path: Path) -> list[str]:
    """_voice.md のスライド見出し（例: 問題提示, よくある間違い）をリストで返す"""
    with open(voice_path) as f:
        content = f.read()
    return re.findall(r'^##\s+スライド[①②③④⑤⑥⑦⑧⑨⑩]\s*[　\s]*(.+)$',
                      content, flags=re.MULTILINE)


def wav_duration(wav_path: Path) -> float:
    """WAV ファイルの再生時間（秒）を返す"""
    with wave.open(str(wav_path), 'rb') as wf:
        return wf.getnframes() / wf.getframerate()


def fmt_ts(seconds: float) -> str:
    """秒数を M:SS または H:MM:SS 形式に変換"""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h > 0:
        return f'{h}:{m:02d}:{sec:02d}'
    return f'{m}:{sec:02d}'


def write_timestamps_to_edit(edit_path: Path, timestamps: list[tuple[str, float]]) -> None:
    """タイムスタンプを _edit.md の説明文とタグの間に書き込む（上書き更新）"""
    if not edit_path.exists():
        return

    ts_block = '▼目次\n' + '\n'.join(
        f'{fmt_ts(sec)} {label}' for label, sec in timestamps
    )

    text = edit_path.read_text()

    # 既存タイムスタンプブロックがあれば置換
    if '▼目次' in text:
        text = re.sub(r'▼目次\n(?:[^\n]+\n)*', ts_block + '\n', text)
    else:
        # 説明文コードブロック内の末尾タグ行の直前に挿入
        text = re.sub(
            r'(#[^\n]+\n(?:[^\n]*\n)*?)(\*\*タグ\*\*)',
            lambda m: m.group(1) + ts_block + '\n```\n\n---\n\n' + m.group(2),
            text,
            count=1,
        )
        # パターンに合わない場合は末尾に追記
        if '▼目次' not in text:
            text += f'\n---\n\n## タイムスタンプ\n\n```\n{ts_block}\n```\n'

    edit_path.write_text(text)


def extract_title(voice_path: Path) -> str:
    """voice.md の1行目からタイトルを抽出"""
    with open(voice_path) as f:
        first_line = f.readline().strip()
    m = re.search(r'[｜|](.+)$', first_line)
    if m:
        return m.group(1).strip()
    return first_line.lstrip('# ').strip()


_DIGIT_JA = {'0': 'ゼロ', '1': 'いち', '2': 'に', '3': 'さん', '4': 'よん',
             '5': 'ご', '6': 'ろく', '7': 'なな', '8': 'はち', '9': 'きゅう'}

def normalize_for_tts(text: str) -> str:
    """TTS に渡す前に発音問題を修正する"""
    text = re.sub(r'^-{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^※.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'正(?!し|式|規|確|解|直|午|月|論|比|弦|接|反|逆|面|答|法)', 'せい', text)
    text = re.sub(r'問(?!い)', 'もん', text)
    # 助数詞「つ」の正しい読み（数字変換より先に処理）
    for src, dst in [('1つ','ひとつ'),('2つ','ふたつ'),('3つ','みっつ'),
                     ('4つ','よっつ'),('5つ','いつつ'),('6つ','むっつ')]:
        text = text.replace(src, dst)
    # 省略記号の読み（+ … + → プラスてんてんてんプラス 等）
    text = re.sub(r'[＋+][\s　]*[…]{1}[\s　]*[＋+]', 'プラスてんてんてんプラス', text)
    text = re.sub(r'[…](?:\s*(?:プラス|[＋+]))', 'てんてんてんプラス', text)
    text = text.replace('…', 'てんてんてん')
    text = re.sub(r'(?<![0-9])0(?![0-9.])', 'ゼロ', text)
    text = text.replace('f(x)', 'エフエックス')
    # 数学変数アルファベットの読み仮名（英字以外に囲まれた a/b/c を対象）
    text = re.sub(r'(?<![a-zA-Z])a\(', 'エー(', text)
    text = re.sub(r'(?<![a-zA-Z])b\(', 'ビー(', text)
    text = re.sub(r'(?<![a-zA-Z])c\(', 'シー(', text)
    text = re.sub(r'(?<![a-zA-Zア-ン])a(?![a-zA-Z(])', 'エー', text)
    text = re.sub(r'(?<![a-zA-Zア-ン])b(?![a-zA-Z(])', 'ビー', text)
    circled = {'①': 'いち', '②': 'に', '③': 'さん', '④': 'よん', '⑤': 'ご',
               '⑥': 'ろく', '⑦': 'なな', '⑧': 'はち', '⑨': 'きゅう', '⑩': 'じゅう'}
    for ch, reading in circled.items():
        text = text.replace(f'条件{ch}', f'条件{reading}')
    text = re.sub(r'(?<![0-9.])([1-9])(?![0-9.])', lambda m: _DIGIT_JA[m.group(1)], text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def generate_audio_gemini(text: str, out_path: Path, gemini_key: str,
                          gap: float = GAP_SECONDS) -> None:
    """Gemini TTS で音声生成 → WAV 保存（AI Studio キー使用、最も自然な声質）"""
    client = genai.Client(api_key=gemini_key)
    max_retries = 8
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(
                model=GEMINI_TTS_MODEL,
                contents=normalize_for_tts(text),
                config=genai_types.GenerateContentConfig(
                    response_modalities=['AUDIO'],
                    speech_config=genai_types.SpeechConfig(
                        voice_config=genai_types.VoiceConfig(
                            prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                                voice_name=GEMINI_TTS_VOICE
                            )
                        )
                    )
                )
            )
            raw = resp.candidates[0].content.parts[0].inline_data.data
            pcm = raw if isinstance(raw, bytes) else base64.b64decode(raw)
            pcm_to_wav(pcm, out_path, gap_seconds=gap)
            # 使用量を記録
            _usage['api_calls'] += 1
            chars = len(normalize_for_tts(text))
            _usage['input_chars'] += chars
            meta = getattr(resp, 'usage_metadata', None)
            if meta and getattr(meta, 'prompt_token_count', None):
                _usage['input_tokens'] += meta.prompt_token_count
            else:
                _usage['input_tokens'] += chars // 4  # 推定: 1 token ≈ 4 文字
            return
        except Exception as e:
            err = str(e)
            if ('429' in err or '503' in err or '500' in err or 'INTERNAL' in err or 'RESOURCE_EXHAUSTED' in err):
                wait = min(30 * (attempt + 1), 120)
                print(f' [Gemini TTS {type(e).__name__} 待機{wait}秒]', end='', flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f'Gemini TTS: {max_retries}回リトライ後も失敗')


def _audio_cache_key(text: str, gap: float) -> str:
    """正規化済みテキスト + gap のハッシュ（キャッシュ判定用）"""
    normalized = normalize_for_tts(text)
    return hashlib.md5(f'{normalized}|gap={gap:.3f}'.encode()).hexdigest()


def generate_audio(text: str, out_path: Path, api_key: str,
                   gap: float = GAP_SECONDS, gemini_key: str = None) -> None:
    """音声生成 → WAV 保存。同じテキストの WAV が既にあればスキップ（API 節約）"""
    cache_file = out_path.with_suffix('.md5')
    current_key = _audio_cache_key(text, gap)
    if out_path.exists() and cache_file.exists():
        if cache_file.read_text().strip() == current_key:
            print(' [キャッシュ]', end='', flush=True)
            _usage['cached_calls'] += 1
            return
    if gemini_key:
        generate_audio_gemini(text, out_path, gemini_key, gap)
    else:
        _generate_audio_cloud(text, out_path, api_key, gap)
    cache_file.write_text(current_key)


def _generate_audio_cloud(text: str, out_path: Path, api_key: str,
                          gap: float = GAP_SECONDS) -> None:
    """Cloud TTS（GCP）で音声生成 → WAV 保存"""
    payload = {
        'input': {'text': normalize_for_tts(text)},
        'voice': {'languageCode': 'ja-JP', 'name': TTS_VOICE},
        'audioConfig': {
            'audioEncoding': 'LINEAR16',
            'sampleRateHertz': TTS_RATE,
            'speakingRate': 0.90,
        },
    }
    max_retries = 12
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                CLOUD_TTS_URL,
                params={'key': api_key},
                json=payload,
                timeout=60,
            )
            if resp.status_code in (429, 503):
                wait = 30 * (attempt + 1)
                print(f' [待機{wait}秒]', end='', flush=True)
                time.sleep(wait)
                continue
            if resp.status_code >= 400:
                raise RuntimeError(f'Cloud TTS APIエラー {resp.status_code}: {resp.text[:200]}')
            resp.raise_for_status()
            pcm = base64.b64decode(resp.json()['audioContent'])
            pcm_to_wav(pcm, out_path, gap_seconds=gap)
            return
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait = 30 * (attempt + 1)
                print(f' [待機{wait}秒]', end='', flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f'Cloud TTS: {max_retries}回リトライ後も失敗')


def make_slide_clip(img_path: Path, audio_path: Path, clip_path: Path) -> None:
    """画像 + 音声 → 動画クリップ (.mp4)"""
    audio = AudioFileClip(str(audio_path))
    clip  = ImageClip(str(img_path), duration=audio.duration).with_audio(audio)
    tmp   = clip_path.with_suffix('.tmp_audio.mp4')
    clip.write_videofile(str(clip_path), fps=VIDEO_FPS, codec='libx264',
                         audio_codec='aac', logger=None,
                         temp_audiofile=str(tmp),
                         ffmpeg_params=['-pix_fmt', 'yuv420p'])
    audio.close()
    clip.close()


def _log_usage(stem: str) -> None:
    """API 使用量をターミナルに表示し api_usage_log.jsonl に追記"""
    import json, datetime
    calls  = _usage['api_calls']
    cached = _usage['cached_calls']
    chars  = _usage['input_chars']
    tokens = _usage['input_tokens']
    cost_usd = tokens / 1_000_000 * _COST_PER_1M_INPUT_TOKENS
    cost_jpy = cost_usd * _JPY_PER_USD
    print(f'  📊 API使用: {calls}回呼び出し / {cached}回キャッシュ / '
          f'{chars:,}文字 / {tokens:,}トークン(推定) / '
          f'${cost_usd:.4f} ≈ ¥{cost_jpy:.1f}')
    log_path = Path(__file__).parent / 'api_usage_log.jsonl'
    record = {
        'ts': datetime.datetime.now().isoformat(timespec='seconds'),
        'stem': stem, 'api_calls': calls, 'cached_calls': cached,
        'input_chars': chars, 'input_tokens_est': tokens,
        'cost_usd_est': round(cost_usd, 6), 'cost_jpy_est': round(cost_jpy, 1),
    }
    with log_path.open('a') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def process_one(html_path: Path, api_key: str, gemini_key: str = None) -> Path | None:
    """HTML 1 ファイル → MP4"""
    # 使用量カウンターをリセット
    _usage['api_calls'] = _usage['cached_calls'] = _usage['input_chars'] = _usage['input_tokens'] = 0
    stem = html_path.stem
    voice_path = html_path.parent / f'{stem}_voice.md'

    if not voice_path.exists():
        print(f'[SKIP] 台本なし: {voice_path.name}')
        return None

    out_dir = OUTPUT_DIR / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'\n=== {stem} ===')

    # アニメーション指示を解析
    edit_path = BASE_DIR / f'{stem}_edit.md'
    animations = parse_animations_from_edit(edit_path)
    animation_targets = {
        slide_num: [a['target'] for a in anns]
        for slide_num, anns in animations.items()
    }

    print('  [1/3] スライドをキャプチャ中...')
    screenshots, ruidai_hidden, bboxes_by_slide = screenshot_slides(
        html_path, out_dir, animation_targets=animation_targets or None
    )
    # bboxes を各 annotation spec に付与
    for slide_num, anns in animations.items():
        slide_bboxes = bboxes_by_slide.get(slide_num, [])
        for ann, bbox in zip(anns, slide_bboxes):
            ann['bbox'] = bbox
            if bbox is None:
                print(f'  [WARN] bbox 未検出: Slide{slide_num} 「{ann.get("target","")[:30]}」')
    ann_count = sum(
        1 for anns in animations.values() for a in anns if a.get('bbox')
    )
    print(f'        {len(screenshots)} 枚取得'
          + (' / 類題非表示版あり' if ruidai_hidden else '')
          + (f' / アノテーション {ann_count}件' if ann_count else ''))

    scripts      = parse_voice_scripts(voice_path)
    slide_labels = parse_slide_labels(voice_path)
    title        = extract_title(voice_path)
    ruidai_idx   = find_ruidai_index(open(html_path).read())
    print(f'  [2/3] 台本解析完了: {len(scripts)} セクション / タイトル: {title}')

    if len(screenshots) != len(scripts):
        print(f'  [WARN] スライド数({len(screenshots)}) ≠ 台本数({len(scripts)})、少ない方で処理')

    pairs = list(zip(screenshots, scripts))

    print('  [3/3] 音声生成 + クリップ作成...')
    clip_paths: list[Path] = []
    timestamps: list[tuple[str, float]] = []   # (ラベル, 開始秒)
    elapsed = 0.0

    # イントロクリップ（サムネイル画像 + 固定イントロ音声）
    thumbnail = THUMBNAILS_DIR / f'{stem}.png'
    if thumbnail.exists():
        print('        [イントロ]', end='', flush=True)
        intro_audio = out_dir / 'audio_intro.wav'
        intro_clip  = out_dir / 'clip_intro.mp4'
        generate_audio(INTRO_TEXT, intro_audio, api_key, gap=0.0, gemini_key=gemini_key)
        make_slide_clip(thumbnail, intro_audio, intro_clip)
        print(' 音声✓ 動画✓')
        clip_paths.append(intro_clip)
        elapsed += wav_duration(intro_audio)
    else:
        print(f'  [WARN] サムネイルなし: {thumbnail.name}、イントロをスキップ')

    for idx, (img, script) in enumerate(pairs):
        i = idx + 1
        label = slide_labels[idx] if idx < len(slide_labels) else f'スライド{i}'
        print(f'        [{i}/{len(pairs)}]', end='', flush=True)
        timestamps.append((label, elapsed))

        if idx == ruidai_idx and ruidai_hidden is not None:
            problem_script, solution_script = split_ruidai_script(script)

            # A: 問題提示（解答非表示）
            audio_a = out_dir / f'audio_{i:02d}a.wav'
            clip_a  = out_dir / f'clip_{i:02d}a.mp4'
            generate_audio(problem_script + '\nでは一度、自分で解いてみてください。',
                           audio_a, api_key, gemini_key=gemini_key)
            make_slide_clip(ruidai_hidden, audio_a, clip_a)
            print(' 問題✓', end='', flush=True)

            # B: 3秒の無音（解答非表示のまま）
            silence_wav = out_dir / f'audio_{i:02d}b.wav'
            clip_b      = out_dir / f'clip_{i:02d}b.mp4'
            write_silence_wav(silence_wav, 3.0)
            make_slide_clip(ruidai_hidden, silence_wav, clip_b)

            # C: 解説開始ナレーション（解答非表示のまま）
            audio_c = out_dir / f'audio_{i:02d}c.wav'
            clip_c  = out_dir / f'clip_{i:02d}c.mp4'
            generate_audio('では、解説していきます。', audio_c, api_key, gemini_key=gemini_key)
            make_slide_clip(ruidai_hidden, audio_c, clip_c)

            # D: 解答解説（解答表示）
            audio_d = out_dir / f'audio_{i:02d}d.wav'
            clip_d  = out_dir / f'clip_{i:02d}.mp4'
            generate_audio(solution_script, audio_d, api_key, gemini_key=gemini_key)
            make_slide_clip(img, audio_d, clip_d)
            print(' 解答✓')

            clip_paths.extend([clip_a, clip_b, clip_c, clip_d])
            elapsed += (wav_duration(audio_a) + wav_duration(silence_wav)
                        + wav_duration(audio_c) + wav_duration(audio_d))
        else:
            audio_path = out_dir / f'audio_{i:02d}.wav'
            clip_path  = out_dir / f'clip_{i:02d}.mp4'
            generate_audio(script, audio_path, api_key, gemini_key=gemini_key)
            print(' 音声✓', end='', flush=True)
            slide_anns = [a for a in animations.get(idx + 1, []) if a.get('bbox')]
            if slide_anns:
                make_slide_clip_animated(img, audio_path, clip_path, slide_anns, script)
                print(f' 動画✓(アノテ{len(slide_anns)}件)')
            else:
                make_slide_clip(img, audio_path, clip_path)
                print(' 動画✓')
            clip_paths.append(clip_path)
            elapsed += wav_duration(audio_path)

    print('        [アウトロ]', end='', flush=True)
    outro_audio = out_dir / 'audio_outro.wav'
    outro_clip  = out_dir / 'clip_outro.mp4'
    generate_audio(OUTRO_TEMPLATE.format(title=title), outro_audio, api_key, gap=2.5, gemini_key=gemini_key)
    ending = ENDING_SLIDE if ENDING_SLIDE.exists() else screenshots[-1]
    make_slide_clip(ending, outro_audio, outro_clip)
    print(' 音声✓ 動画✓')
    clip_paths.append(outro_clip)

    final_path = OUTPUT_DIR / f'{stem}.mp4'
    print(f'  結合 → {final_path.name} ...', end='', flush=True)
    all_clips = [VideoFileClip(str(cp)) for cp in clip_paths]
    final = concatenate_videoclips(all_clips)
    final.write_videofile(str(final_path), fps=VIDEO_FPS, codec='libx264',
                          audio_codec='aac', logger=None,
                          ffmpeg_params=['-pix_fmt', 'yuv420p', '-movflags', '+faststart'])
    for c in all_clips:
        c.close()
    final.close()
    print(' 完了')

    # タイムスタンプを _edit.md に書き込む
    if edit_path.exists() and timestamps:
        write_timestamps_to_edit(edit_path, timestamps)
        print(f'  タイムスタンプ → {edit_path.name} に反映')

    _log_usage(stem)
    return final_path


def _show_preflight_checklist() -> None:
    """PITFALLS.md からチェックリスト項目を抽出して表示"""
    pitfalls = Path(__file__).parent.parent / 'PITFALLS.md'
    if not pitfalls.exists():
        return
    lines = pitfalls.read_text().splitlines()
    items = [l for l in lines if l.strip().startswith('- [ ]')]
    if not items:
        return
    print('─' * 60)
    print('【生成前チェックリスト】（PITFALLS.md より）')
    for item in items:
        print(f'  {item.strip()}')
    print('─' * 60)


def main():
    parser = argparse.ArgumentParser(description='HTML スライド → MP4 動画生成')
    parser.add_argument('--file', help='対象 HTML ファイル（省略時は全ファイル）')
    args = parser.parse_args()

    _show_preflight_checklist()

    gemini_key = os.environ.get('GEMINI_API_KEY')
    api_key    = os.environ.get('GOOGLE_API_KEY')
    if gemini_key:
        print('TTS: Gemini TTS (AI Studio) を使用')
    elif api_key:
        print('TTS: Cloud TTS (GCP) を使用')
    else:
        raise SystemExit('エラー: GEMINI_API_KEY または GOOGLE_API_KEY を設定してください。')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    html_files = [Path(args.file)] if args.file else sorted(BASE_DIR.glob('*.html'))

    results = []
    for html_path in html_files:
        r = process_one(html_path, api_key, gemini_key=gemini_key)
        if r:
            results.append(r)

    print(f'\n=== 完了: {len(results)} 本の動画を生成 ===')
    for r in results:
        print(r)


if __name__ == '__main__':
    main()
