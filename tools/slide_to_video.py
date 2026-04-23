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
import wave
import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright
from google import genai
from google.genai import types
from moviepy import VideoFileClip, concatenate_videoclips, ImageClip, AudioFileClip

# ── 設定 ──────────────────────────────────────────────────────────────────
CHROME_PATH = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
KATEX_BASE  = 'file:///home/user/StudyList/problems/katex'
BASE_DIR    = Path('/home/user/StudyList/problems/youtube_redesign')
OUTPUT_DIR  = BASE_DIR / 'output'
TTS_MODEL   = 'gemini-2.5-flash-preview-tts'
TTS_VOICE   = 'Kore'
VIDEO_W, VIDEO_H = 1280, 720
VIDEO_FPS   = 24
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
    tmp_path = html_path.parent / '_tmp_preview.html'

    try:
        with open(tmp_path, 'w') as f:
            f.write(patch_html(html))

        shots: list[Path] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=CHROME_PATH,
                headless=True,
                args=['--no-sandbox', '--allow-file-access-from-files'],
            )
            page = browser.new_page(viewport={'width': VIDEO_W, 'height': VIDEO_H})
            page.goto(f'file://{tmp_path}')
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


def pcm_to_wav(pcm: bytes, wav_path: Path, rate: int = 24000) -> None:
    """Gemini が返す生 PCM (16bit mono) → WAV"""
    with wave.open(str(wav_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def generate_audio(text: str, out_path: Path, client: genai.Client) -> None:
    """Gemini TTS で音声生成 → WAV 保存"""
    response = client.models.generate_content(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=['AUDIO'],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=TTS_VOICE)
                )
            ),
        ),
    )
    pcm = response.candidates[0].content.parts[0].inline_data.data
    pcm_to_wav(pcm, out_path)


def make_slide_clip(img_path: Path, audio_path: Path, clip_path: Path) -> None:
    """画像 + 音声 → 動画クリップ (.mp4)"""
    audio = AudioFileClip(str(audio_path))
    clip  = ImageClip(str(img_path), duration=audio.duration).with_audio(audio)
    clip.write_videofile(str(clip_path), fps=VIDEO_FPS, codec='libx264',
                         audio_codec='aac', logger=None)
    audio.close()
    clip.close()


def process_one(html_path: Path, client: genai.Client) -> Path | None:
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
    print(f'  [2/3] 台本解析完了: {len(scripts)} セクション')

    if len(screenshots) != len(scripts):
        print(f'  [WARN] スライド数({len(screenshots)}) ≠ 台本数({len(scripts)})、少ない方で処理')

    pairs = list(zip(screenshots, scripts))

    print('  [3/3] 音声生成 + クリップ作成...')
    clip_paths: list[Path] = []
    for i, (img, script) in enumerate(pairs, 1):
        print(f'        [{i}/{len(pairs)}]', end='', flush=True)
        audio_path = out_dir / f'audio_{i:02d}.wav'
        clip_path  = out_dir / f'clip_{i:02d}.mp4'

        generate_audio(script, audio_path, client)
        print(' 音声✓', end='', flush=True)

        make_slide_clip(img, audio_path, clip_path)
        print(' 動画✓')
        clip_paths.append(clip_path)

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

    client = genai.Client(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.file:
        html_files = [Path(args.file)]
    else:
        html_files = sorted(BASE_DIR.glob('*.html'))

    results = []
    for html_path in html_files:
        r = process_one(html_path, client)
        if r:
            results.append(r)

    print(f'\n=== 完了: {len(results)} 本の動画を生成 ===')
    for r in results:
        print(f'  {r}')


if __name__ == '__main__':
    main()
