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
import struct
import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright
from google import genai
from google.genai import types
from moviepy import VideoFileClip, concatenate_videoclips, ImageClip, AudioFileClip

# ── 設定 ──────────────────────────────────────────────────────────────────
CHROME_PATH  = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
KATEX_BASE   = 'file:///home/user/StudyList/problems/katex'
BASE_DIR     = Path('/home/user/StudyList/problems/youtube_redesign')
OUTPUT_DIR   = BASE_DIR / 'output'
ENDING_SLIDE = BASE_DIR / 'ending_slide.png'
TTS_MODEL    = 'gemini-3.1-flash-tts-preview'
TTS_VOICE    = 'Leda'
GAP_SECONDS  = 0.5
VIDEO_W, VIDEO_H = 1280, 720
VIDEO_FPS    = 24

TTS_PROMPT_PREFIX = """Read the following transcript based on the audio profile and director's note.

# Audio Profile
young Japanese voice (student-like)
calm, soft, natural tone
slightly informal, friendly
medium-low pitch, stable
natural pauses, slight hesitation OK
not robotic, not exaggerated
sounds like thinking aloud, not teaching

# Director's note
Style: The "Vocal Smile": The soft palate is raised to keep the tone bright, sunny, and explicitly inviting. Pace: Natural conversational pace. Accent: American (Gen).

## Scene:
after-school quiet classroom (Japanese high school)
solo narrator, thinking aloud while solving math problem
calm, relaxed atmosphere

## Sample Context:
high school math explanation
not lecture, thinking process spoken aloud
step-by-step reasoning
small pauses, light reactions (hmm, oh, I see)
answers unfold gradually

## Transcript:
"""

OUTRO_TEMPLATE = """以上！いかがでしたでしょうか！
今回は
「{title}」
について見ていきました！
この動画が少しでも参考になった方、またこんな感じの高校数学の問題を今後も見たいよ！って方はチャンネル登録や高評価してくれると嬉しいです！
また、この動画で疑問に思ったことやわからなかったこと、また解説して欲しいよって問題のある方はコメントで教えてもらえると助かります！
それでは今日の動画はここまで！ばいば〜い！！"""
# ─────────────────────────────────────────────────────────────────────────


def parse_audio_mime_type(mime_type: str) -> dict:
    """audio/L16;rate=24000 形式から bits_per_sample と rate を取得"""
    bits_per_sample = 16
    rate = 24000
    for param in mime_type.split(';'):
        param = param.strip()
        if param.lower().startswith('rate='):
            try:
                rate = int(param.split('=', 1)[1])
            except (ValueError, IndexError):
                pass
        elif param.startswith('audio/L'):
            try:
                bits_per_sample = int(param.split('L', 1)[1])
            except (ValueError, IndexError):
                pass
    return {'bits_per_sample': bits_per_sample, 'rate': rate}


def convert_to_wav(audio_data: bytes, mime_type: str,
                   gap_seconds: float = 0.0) -> bytes:
    """生 PCM → WAV ヘッダ付き。末尾に gap_seconds 秒の無音を追加"""
    params = parse_audio_mime_type(mime_type)
    bits_per_sample = params['bits_per_sample']
    sample_rate = params['rate']
    num_channels = 1
    bytes_per_sample = bits_per_sample // 8
    silence = b'\x00' * bytes_per_sample * int(sample_rate * gap_seconds)
    data = audio_data + silence
    data_size = len(data)
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', chunk_size, b'WAVE',
        b'fmt ', 16, 1, num_channels,
        sample_rate, byte_rate, block_align, bits_per_sample,
        b'data', data_size,
    )
    return header + data


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
        # バッジ要素のテキストが「類題」であることを確認（コメント等の誤検知を防ぐ）
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


def write_silence_wav(out_path: Path, duration: float, rate: int = 24000) -> None:
    """指定秒数の無音 WAV を生成"""
    import wave as _wave
    silence = b'\x00\x00' * int(rate * duration)
    with _wave.open(str(out_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(silence)


def screenshot_slides(html_path: Path, out_dir: Path) -> tuple[list[Path], Path | None]:
    """HTML の全スライドをスクリーンショット → (PNG リスト, 類題解答非表示PNG)"""
    with open(html_path) as f:
        html = f.read()

    slide_count  = len(re.findall(r'<section class="slide', html))
    ruidai_idx   = find_ruidai_index(html)
    tmp_path     = html_path.resolve().parent / '_tmp_preview.html'

    try:
        with open(tmp_path, 'w') as f:
            f.write(patch_html(html))

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
                # 類題スライドは解答非表示版を先に撮る
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
    text = re.sub(r'正(?!しく|式|規|確|解|直|午|月|論|比|弦|接|反|逆|面|答|法)',
                  'せい', text)
    text = re.sub(r'(?<![0-9])0(?![0-9.])', 'ゼロ', text)
    text = text.replace('f(x)', 'エフエックス')
    circled = {'①': 'いち', '②': 'に', '③': 'さん', '④': 'よん', '⑤': 'ご',
               '⑥': 'ろく', '⑦': 'なな', '⑧': 'はち', '⑨': 'きゅう', '⑩': 'じゅう'}
    for ch, reading in circled.items():
        text = text.replace(f'条件{ch}', f'条件{reading}')
    text = re.sub(r'(?<![0-9.])([1-9])(?![0-9.])',
                  lambda m: _DIGIT_JA[m.group(1)], text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def generate_audio(text: str, out_path: Path, client: genai.Client,
                   gap: float = GAP_SECONDS) -> None:
    """Gemini TTS (streaming) で音声生成 → WAV 保存"""
    prompt = TTS_PROMPT_PREFIX + normalize_for_tts(text)
    contents = [
        types.Content(
            role='user',
            parts=[types.Part.from_text(text=prompt)],
        )
    ]
    config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=['audio'],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=TTS_VOICE)
            )
        ),
    )

    max_retries = 12
    for attempt in range(max_retries):
        try:
            audio_data = b''
            mime_type = 'audio/L16;rate=24000'
            for chunk in client.models.generate_content_stream(
                model=TTS_MODEL,
                contents=contents,
                config=config,
            ):
                if chunk.parts is None:
                    continue
                part = chunk.parts[0]
                if part.inline_data and part.inline_data.data:
                    audio_data += part.inline_data.data
                    mime_type = part.inline_data.mime_type or mime_type

            if not audio_data:
                raise RuntimeError('音声データが空です')

            wav = convert_to_wav(audio_data, mime_type, gap_seconds=gap)
            out_path.write_bytes(wav)
            return

        except Exception as e:
            msg = str(e)
            if '429' in msg or '503' in msg or 'RESOURCE_EXHAUSTED' in msg:
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
    tmp   = clip_path.with_suffix('.tmp_audio.mp4')
    clip.write_videofile(str(clip_path), fps=VIDEO_FPS, codec='libx264',
                         audio_codec='aac', logger=None,
                         temp_audiofile=str(tmp))
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
    for idx, (img, script) in enumerate(pairs):
        i = idx + 1
        print(f'        [{i}/{len(pairs)}]', end='', flush=True)

        if idx == ruidai_idx and ruidai_hidden is not None:
            # 類題スライド: 問題提示 → 3秒無音 → 解説開始ナレーション → 解答解説
            problem_script, solution_script = split_ruidai_script(script)

            # A: 問題提示（解答非表示）
            audio_a = out_dir / f'audio_{i:02d}a.wav'
            clip_a  = out_dir / f'clip_{i:02d}a.mp4'
            intro_text = problem_script + '\nでは一度、自分で解いてみてください。'
            generate_audio(intro_text, audio_a, client)
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
            generate_audio('では、解説していきます。', audio_c, client)
            make_slide_clip(ruidai_hidden, audio_c, clip_c)

            # D: 解答解説（解答表示）
            audio_d = out_dir / f'audio_{i:02d}d.wav'
            clip_d  = out_dir / f'clip_{i:02d}.mp4'
            generate_audio(solution_script, audio_d, client)
            make_slide_clip(img, audio_d, clip_d)
            print(' 解答✓')

            clip_paths.extend([clip_a, clip_b, clip_c, clip_d])
        else:
            audio_path = out_dir / f'audio_{i:02d}.wav'
            clip_path  = out_dir / f'clip_{i:02d}.mp4'
            generate_audio(script, audio_path, client)
            print(' 音声✓', end='', flush=True)
            make_slide_clip(img, audio_path, clip_path)
            print(' 動画✓')
            clip_paths.append(clip_path)

    print('        [アウトロ]', end='', flush=True)
    outro_text  = OUTRO_TEMPLATE.format(title=title)
    outro_audio = out_dir / 'audio_outro.wav'
    outro_clip  = out_dir / 'clip_outro.mp4'
    generate_audio(outro_text, outro_audio, client, gap=0.0)
    ending = ENDING_SLIDE if ENDING_SLIDE.exists() else screenshots[-1]
    make_slide_clip(ending, outro_audio, outro_clip)
    print(' 音声✓ 動画✓')
    clip_paths.append(outro_clip)

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
        print(r)


if __name__ == '__main__':
    main()
