#!/usr/bin/env python3
"""
slide_to_video.py
HTML slides + _voice.md scripts → MP4 videos

Usage:
    GEMINI_API_KEY=xxx python3 tools/slide_to_video.py
    GEMINI_API_KEY=xxx python3 tools/slide_to_video.py --file problems/youtube_redesign/math1_quadratic_discriminant.html
"""

import os
import re
import time
import wave
import base64
import argparse
import requests
from pathlib import Path

from playwright.sync_api import sync_playwright
from moviepy import VideoFileClip, concatenate_videoclips, ImageClip, AudioFileClip

# ── 設定 ──────────────────────────────────────────────────────────────────
CHROME_PATH  = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
KATEX_BASE   = 'file:///home/user/StudyList/problems/katex'
BASE_DIR     = Path('/home/user/StudyList/problems/youtube_redesign')
OUTPUT_DIR   = BASE_DIR / 'output'
TTS_VOICE    = 'ja-JP-Neural2-B'   # Google Cloud TTS: 日本語Neural2男性
TTS_RATE     = 24000               # Cloud TTS LINEAR16 出力サンプルレート
GAP_SECONDS  = 0.5                 # スライド切り替え後の無音 (秒)
CLOUD_TTS_URL = 'https://texttospeech.googleapis.com/v1/text:synthesize'
VIDEO_W, VIDEO_H = 1280, 720
VIDEO_FPS    = 24

# Gemini TTS へ渡すスタイル指示
TTS_STYLE = """Scene: after-school quiet classroom (Japanese high school)
solo narrator, thinking aloud while solving math problem
calm, relaxed atmosphere

Sample Context:
high school math explanation
not lecture, thinking process spoken aloud
step-by-step reasoning
small pauses, light reactions (hmm, oh, I see)
answers unfold gradually

Audio Profile:
young Japanese voice (student-like)
calm, soft, natural tone
slightly informal, friendly
medium-low pitch, stable
natural pauses, slight hesitation OK
not robotic, not exaggerated
sounds like thinking aloud, not teaching"""

OUTRO_TEMPLATE = """以上！いかがでしたでしょうか！
今回は
「{title}」
について見ていきました！
この動画が少しでも参考になった方、またこんな感じの高校数学の問題を今後も見たいよ！って方はチャンネル登録や高評価してくれると嬉しいです！
また、この動画で疑問に思ったことやわからなかったこと、また解説して欲しいよって問題のある方はコメントで教えてもらえると助かります！
それでは今日の動画はここまで！ばいば〜い！！"""
# ─────────────────────────────────────────────────────────────────────────


def patch_html(html: str) -> str:
    """CDN KaTeX URL → ローカルパスに差し替え"""
    return (html
        .replace('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css',
                 f'{KATEX_BASE}/katex.min.css')
        .replace('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js',
                 f'{KATEX_BASE}/katex.min.js')
        .replace('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js',
                 f'{KATEX_BASE}/auto-render.min.js'))


def screenshot_slides(html_path: Path, out_dir: Path) -> list[Path]:
    """HTML の全スライドをスクリーンショット → PNG リストを返す"""
    with open(html_path) as f:
        html = f.read()

    slide_count = len(re.findall(r'<section class="slide', html))
    tmp_path = html_path.resolve().parent / '_tmp_preview.html'

    try:
        with open(tmp_path, 'w') as f:
            f.write(patch_html(html))

        shots: list[Path] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=CHROME_PATH,
                headless=True,
                args=['--no-sandbox', '--allow-file-access-from-files',
                      '--lang=ja-JP', '--accept-lang=ja-JP'],
            )
            page = browser.new_page(viewport={'width': VIDEO_W, 'height': VIDEO_H})
            page.goto(f'file://{tmp_path.resolve()}')
            page.wait_for_timeout(3000)
            page.evaluate("document.getElementById('nav').style.display='none'")

            for i in range(slide_count):
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

    return shots


def parse_voice_scripts(voice_path: Path) -> list[str]:
    """_voice.md → スライドごとの台本リスト"""
    with open(voice_path) as f:
        content = f.read()

    parts = re.split(r'^##\s+スライド[①②③④⑤⑥⑦⑧⑨⑩].*$', content, flags=re.MULTILINE)
    return [p.strip() for p in parts[1:] if p.strip()]


def extract_title(voice_path: Path) -> str:
    """voice.md の1行目 `# 【音声台本】...` からタイトル部分を抽出"""
    with open(voice_path) as f:
        first_line = f.readline().strip()
    # "# 【音声台本】数学I｜放物線とx軸の交点条件（判別式）" → "放物線とx軸の交点条件（判別式）"
    m = re.search(r'[｜|](.+)$', first_line)
    if m:
        return m.group(1).strip()
    # フォールバック: # 以降を全部返す
    return first_line.lstrip('# ').strip()


def pcm_to_wav(pcm: bytes, wav_path: Path, rate: int = TTS_RATE,
               gap_seconds: float = 0.0) -> None:
    """Gemini の生 PCM (16bit mono) → WAV。gap_seconds 分の無音を末尾に追加"""
    silence = b'\x00\x00' * int(rate * gap_seconds)
    with wave.open(str(wav_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm + silence)


def generate_audio(text: str, out_path: Path, api_key: str,
                   gap: float = GAP_SECONDS) -> None:
    """Google Cloud TTS で音声生成 → WAV 保存（末尾に gap 秒の無音付き）。レート制限時はリトライ"""
    payload = {
        'input': {'text': text},
        'voice': {
            'languageCode': 'ja-JP',
            'name': TTS_VOICE,
        },
        'audioConfig': {
            'audioEncoding': 'LINEAR16',
            'sampleRateHertz': TTS_RATE,
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
            resp.raise_for_status()
            pcm = base64.b64decode(resp.json()['audioContent'])
            pcm_to_wav(pcm, out_path, gap_seconds=gap)
            return
        except requests.exceptions.RequestException as e:
            msg = str(e)
            if '429' in msg or '503' in msg:
                wait = 30 * (attempt + 1)
                print(f' [待機{wait}秒]', end='', flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f'音声生成: {max_retries}回リトライ後も失敗')


def make_slide_clip(img_path: Path, audio_path: Path, clip_path: Path) -> None:
    """画像 + 音声 → 動画クリップ (.mp4)"""
    audio = AudioFileClip(str(audio_path))
    clip  = ImageClip(str(img_path), duration=audio.duration).with_audio(audio)
    clip.write_videofile(str(clip_path), fps=VIDEO_FPS, codec='libx264',
                         audio_codec='aac', logger=None)
    audio.close()
    clip.close()


def process_one(html_path: Path, api_key: str) -> Path | None:
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
    screenshots = screenshot_slides(html_path, out_dir)
    print(f'        {len(screenshots)} 枚取得')

    scripts = parse_voice_scripts(voice_path)
    title   = extract_title(voice_path)
    print(f'  [2/3] 台本解析完了: {len(scripts)} セクション / タイトル: {title}')

    if len(screenshots) != len(scripts):
        print(f'  [WARN] スライド数({len(screenshots)}) ≠ 台本数({len(scripts)})、少ない方で処理')

    pairs = list(zip(screenshots, scripts))

    print('  [3/3] 音声生成 + クリップ作成...')
    clip_paths: list[Path] = []
    for i, (img, script) in enumerate(pairs, 1):
        print(f'        [{i}/{len(pairs)}]', end='', flush=True)
        audio_path = out_dir / f'audio_{i:02d}.wav'
        clip_path  = out_dir / f'clip_{i:02d}.mp4'

        generate_audio(script, audio_path, api_key)
        print(' 音声✓', end='', flush=True)

        make_slide_clip(img, audio_path, clip_path)
        print(' 動画✓')
        clip_paths.append(clip_path)

    # アウトロクリップ（最後のスライド画像 + アウトロ音声、無音なし）
    print('        [アウトロ]', end='', flush=True)
    outro_text  = OUTRO_TEMPLATE.format(title=title)
    outro_audio = out_dir / 'audio_outro.wav'
    outro_clip  = out_dir / 'clip_outro.mp4'
    generate_audio(outro_text, outro_audio, api_key, gap=0.0)
    make_slide_clip(screenshots[-1], outro_audio, outro_clip)
    print(' 音声✓ 動画✓')
    clip_paths.append(outro_clip)

    # 全クリップを結合
    final_path = OUTPUT_DIR / f'{stem}.mp4'
    print(f'  結合 → {final_path.name} ...', end='', flush=True)
    all_clips = [VideoFileClip(str(cp)) for cp in clip_paths]
    final = concatenate_videoclips(all_clips)
    final.write_videofile(str(final_path), fps=VIDEO_FPS, codec='libx264',
                          audio_codec='aac', logger=None)
    for c in all_clips:
        c.close()
    final.close()
    print(' 完了')

    return final_path


def main():
    parser = argparse.ArgumentParser(description='HTML スライド → MP4 動画生成')
    parser.add_argument('--file', help='対象 HTML ファイル（省略時は全ファイル）')
    args = parser.parse_args()

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise SystemExit('エラー: 環境変数 GEMINI_API_KEY を設定してください。')

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.file:
        html_files = [Path(args.file)]
    else:
        html_files = sorted(BASE_DIR.glob('*.html'))

    results = []
    for html_path in html_files:
        r = process_one(html_path, api_key)
        if r:
            results.append(r)

    print(f'\n=== 完了: {len(results)} 本の動画を生成 ===')
    for r in results:
        print(f'  {r}')


if __name__ == '__main__':
    main()
