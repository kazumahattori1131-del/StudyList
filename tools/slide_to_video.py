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
VIDEO_W, VIDEO_H = 1280, 720
VIDEO_FPS     = 24
# ─────────────────────────────────────────────────────────────────────────

INTRO_TEXT = """みなさんこんにちは！
このチャンネルでは、高校数学の典型問題・ひっかかりやすい問題を解説しています。
もしよろしければチャンネル登録よろしくお願いします！
では、今日の問題はこちらです！"""

OUTRO_TEMPLATE = """今回は「{title}」について解説しました。

この解法を知っておくだけで、入試本番で同じタイプの問題が出たとき、迷わず手が動きます。典型パターンをひとつひとつ押さえていけば、確実に点数が安定します。

役に立ったと感じた方は、チャンネル登録と高評価で応援してください！次回も、入試で差がつく重要ポイントを解説します。
疑問点や解説してほしい問題があれば、コメントで教えてもらえると助かります。それでは！"""


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


def screenshot_slides(html_path: Path, out_dir: Path) -> tuple[list[Path], Path | None]:
    """HTML の全スライドをスクリーンショット → (PNG リスト, 類題解答非表示PNG)"""
    with open(html_path) as f:
        html = f.read()

    slide_count = len(re.findall(r'<section class="slide', html))
    ruidai_idx  = find_ruidai_index(html)
    tmp_path    = html_path.resolve().parent / '_tmp_preview.html'

    try:
        tmp_path.write_text(patch_html(html))

        shots: list[Path] = []
        ruidai_hidden: Path | None = None

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

    return shots, ruidai_hidden


def parse_voice_scripts(voice_path: Path) -> list[str]:
    """_voice.md → スライドごとの台本リスト"""
    with open(voice_path) as f:
        content = f.read()
    parts = re.split(r'^##\s+スライド[①②③④⑤⑥⑦⑧⑨⑩].*$', content, flags=re.MULTILINE)
    return [p.strip() for p in parts[1:] if p.strip()]


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


def process_one(html_path: Path, api_key: str, gemini_key: str = None) -> Path | None:
    """HTML 1 ファイル → MP4"""
    stem = html_path.stem
    voice_path = html_path.parent / f'{stem}_voice.md'

    if not voice_path.exists():
        print(f'[SKIP] 台本なし: {voice_path.name}')
        return None

    out_dir = OUTPUT_DIR / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'\n=== {stem} ===')

    print('  [1/3] スライドをキャプチャ中...')
    screenshots, ruidai_hidden = screenshot_slides(html_path, out_dir)
    print(f'        {len(screenshots)} 枚取得'
          + (' / 類題非表示版あり' if ruidai_hidden else ''))

    scripts    = parse_voice_scripts(voice_path)
    title      = extract_title(voice_path)
    ruidai_idx = find_ruidai_index(open(html_path).read())
    print(f'  [2/3] 台本解析完了: {len(scripts)} セクション / タイトル: {title}')

    if len(screenshots) != len(scripts):
        print(f'  [WARN] スライド数({len(screenshots)}) ≠ 台本数({len(scripts)})、少ない方で処理')

    pairs = list(zip(screenshots, scripts))

    print('  [3/3] 音声生成 + クリップ作成...')
    clip_paths: list[Path] = []

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
    else:
        print(f'  [WARN] サムネイルなし: {thumbnail.name}、イントロをスキップ')

    for idx, (img, script) in enumerate(pairs):
        i = idx + 1
        print(f'        [{i}/{len(pairs)}]', end='', flush=True)

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
        else:
            audio_path = out_dir / f'audio_{i:02d}.wav'
            clip_path  = out_dir / f'clip_{i:02d}.mp4'
            generate_audio(script, audio_path, api_key, gemini_key=gemini_key)
            print(' 音声✓', end='', flush=True)
            make_slide_clip(img, audio_path, clip_path)
            print(' 動画✓')
            clip_paths.append(clip_path)

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
