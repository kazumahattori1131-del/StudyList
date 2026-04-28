#!/usr/bin/env python3
"""
test_animation.py
既存キャッシュ音声を使い、アニメーション付き動画を生成するテストスクリプト。
TTS API 不要。元動画を上書きしない（--suffix で別ファイルに出力）。
"""
import re
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from moviepy import VideoFileClip, concatenate_videoclips, ImageClip, AudioFileClip
from playwright.sync_api import sync_playwright

# ── 設定 ──────────────────────────────────────────────────────────────────
CHROME_PATH   = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
KATEX_BASE    = 'file:///home/user/StudyList/problems/katex'
BASE_DIR      = Path('/home/user/StudyList/problems/youtube_redesign')
OUTPUT_DIR    = BASE_DIR / 'output'
ENDING_SLIDE  = BASE_DIR / 'ending_slide.png'
VIDEO_W, VIDEO_H = 1280, 720
VIDEO_FPS     = 24
_CIRCLED = {'①':1,'②':2,'③':3,'④':4,'⑤':5,'⑥':6,'⑦':7,'⑧':8,'⑨':9,'⑩':10}


# ── ユーティリティ ────────────────────────────────────────────────────────

def patch_html(html: str) -> str:
    return (html
        .replace('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css',
                 f'{KATEX_BASE}/katex.min.css')
        .replace('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js',
                 f'{KATEX_BASE}/katex.min.js')
        .replace('https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js',
                 f'{KATEX_BASE}/auto-render.min.js'))


def wav_duration(wav_path: Path) -> float:
    with wave.open(str(wav_path), 'rb') as wf:
        return wf.getnframes() / wf.getframerate()


def find_ruidai_index(html: str) -> int | None:
    sections = re.split(r'(?=<section class="slide)', html)
    count = 0
    for s in sections:
        if not s.startswith('<section class="slide'):
            continue
        if re.search(r'class="badge[^"]*green[^"]*"[^>]*>\s*類題\s*<', s):
            return count
        count += 1
    return None


def split_ruidai_script(script: str) -> tuple[str, str]:
    parts = script.split('\n\n', 1)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else '')


def parse_voice_scripts(voice_path: Path) -> list[str]:
    content = voice_path.read_text()
    parts = re.split(r'^##\s+スライド[①②③④⑤⑥⑦⑧⑨⑩].*$', content, flags=re.MULTILINE)
    return [p.strip() for p in parts[1:] if p.strip()]


def parse_slide_labels(voice_path: Path) -> list[str]:
    content = voice_path.read_text()
    return re.findall(r'^##\s+スライド[①②③④⑤⑥⑦⑧⑨⑩]\s*[　\s]*(.+)$',
                      content, flags=re.MULTILINE)


# ── アノテーション解析 ────────────────────────────────────────────────────

def parse_animations_from_edit(edit_path: Path) -> dict[int, list[dict]]:
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
        for ann_m in re.finditer(r'\*\*強調[①②③④⑤⑥\d]+\*\*\s*\n((?:- .+\n?)+)', block_m.group(2)):
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
    plain = re.sub(r'\$[^$]+\$', ' ', target.strip('`'))
    plain = re.sub(r'[※→（）「」！？。、＊\*]', ' ', plain)
    return [w for w in plain.split() if len(w) >= 2]


def _find_bbox_in_page(page, keywords: list[str]) -> dict | None:
    for kw in keywords:
        safe = kw.replace('\\', '\\\\').replace("'", "\\'")
        bbox = page.evaluate(f"""(() => {{
            const slide = document.querySelector('.slide.active');
            if (!slide) return null;
            const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
            let node;
            while (node = walker.nextNode()) {{
                if (node.textContent.trim().includes('{safe}')) {{
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


# ── スクリーンショット + bbox ─────────────────────────────────────────────

def screenshot_slides(
    html_path: Path, out_dir: Path,
    animation_targets: dict[int, list[str]] | None = None,
) -> tuple[list[Path], Path | None, dict[int, list[dict | None]]]:
    html = html_path.read_text()
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
                executable_path=CHROME_PATH, headless=True,
                args=['--no-sandbox', '--allow-file-access-from-files',
                      '--lang=ja-JP', '--accept-lang=ja-JP'],
            )
            page = browser.new_page(
                viewport={'width': VIDEO_W, 'height': VIDEO_H}, locale='ja-JP'
            )
            page.goto(f'file://{tmp_path.resolve()}')
            page.wait_for_timeout(3000)
            page.evaluate("document.getElementById('nav').style.display='none'")
            for i in range(slide_count):
                slide_num = i + 1
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
                if animation_targets and slide_num in animation_targets:
                    slide_bboxes = []
                    for target in animation_targets[slide_num]:
                        kws = _extract_plain_keywords(target)
                        slide_bboxes.append(_find_bbox_in_page(page, kws) if kws else None)
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


# ── アノテーション描画 ────────────────────────────────────────────────────

def _find_timing_ratio(voice_script: str, timing_text: str) -> float:
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
    img = img.copy().convert('RGBA')
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']
    pad = 10
    color = (220, 20, 20, 235)
    lw = 4
    x0 = max(x - pad, 2);  y0 = max(y - pad, 2)
    x1 = min(x + w + pad, VIDEO_W - 2);  y1 = min(y + h + pad, VIDEO_H - 2)
    m = method.lower()
    if '丸' in m or '円' in m:
        draw.ellipse([x0, y0, x1, y1], outline=color, width=lw)
    elif '矢印' in m:
        ax, ay = max(0, x0 - 55), max(0, y0 - 55)
        draw.line([ax, ay, x0 + 12, y0 + 12], fill=color, width=lw)
        dx, dy = (x0 + 12) - ax, (y0 + 12) - ay
        length = (dx**2 + dy**2) ** 0.5
        if length > 0:
            ux, uy = dx / length, dy / length
            px, py = -uy, ux
            tip = (x0 + 12, y0 + 12)
            p1 = (tip[0] - ux*16 + px*8, tip[1] - uy*16 + py*8)
            p2 = (tip[0] - ux*16 - px*8, tip[1] - uy*16 - py*8)
            draw.polygon([tip, p1, p2], fill=color)
    else:
        draw.rectangle([x0, y0, x1, y1], outline=color, width=lw)
    return Image.alpha_composite(img, overlay).convert('RGB')


# ── クリップ生成 ──────────────────────────────────────────────────────────

def make_clip(img_path: Path, audio_path: Path, clip_path: Path) -> None:
    audio = AudioFileClip(str(audio_path))
    clip  = ImageClip(str(img_path), duration=audio.duration).with_audio(audio)
    tmp   = clip_path.with_suffix('.tmp_audio.mp4')
    clip.write_videofile(str(clip_path), fps=VIDEO_FPS, codec='libx264',
                         audio_codec='aac', logger=None, temp_audiofile=str(tmp),
                         ffmpeg_params=['-pix_fmt', 'yuv420p'])
    audio.close();  clip.close()


def make_clip_animated(img_path: Path, audio_path: Path, clip_path: Path,
                       annotations: list[dict], voice_script: str) -> None:
    audio = AudioFileClip(str(audio_path))
    total_dur = audio.duration
    timed = sorted(
        [(_find_timing_ratio(voice_script, a.get('timing', '')) * total_dur, a)
         for a in annotations],
        key=lambda x: x[0]
    )
    base = Image.open(img_path).convert('RGB')
    segments: list[tuple[float, Image.Image]] = [(0.0, base)]
    current = base
    for t, ann in timed:
        if ann.get('bbox'):
            current = _draw_annotation(current.convert('RGBA'), ann['bbox'], ann.get('method', '赤枠'))
            segments.append((t, current))
    clips = []
    for i, (start_t, img) in enumerate(segments):
        end_t = segments[i + 1][0] if i + 1 < len(segments) else total_dur
        dur = max(end_t - start_t, 0.05)
        clips.append(ImageClip(np.array(img), duration=dur))
    combined = concatenate_videoclips(clips).with_audio(audio)
    tmp = clip_path.with_suffix('.tmp_audio.mp4')
    combined.write_videofile(str(clip_path), fps=VIDEO_FPS, codec='libx264',
                             audio_codec='aac', logger=None, temp_audiofile=str(tmp),
                             ffmpeg_params=['-pix_fmt', 'yuv420p'])
    audio.close();  combined.close()


# ── メイン処理 ────────────────────────────────────────────────────────────

def process_cached(html_path: Path, suffix: str = '_animated') -> Path:
    stem = html_path.stem
    voice_path = html_path.parent / f'{stem}_voice.md'
    out_dir = OUTPUT_DIR / stem

    print(f'\n=== {stem} ===')

    edit_path = BASE_DIR / f'{stem}_edit.md'
    animations = parse_animations_from_edit(edit_path)
    animation_targets = {sn: [a['target'] for a in anns] for sn, anns in animations.items()}
    ann_total = sum(len(v) for v in animations.values())
    print(f'  追い装飾指示: {ann_total}件')

    print('  スライドキャプチャ + bbox 取得...')
    screenshots, ruidai_hidden, bboxes_by_slide = screenshot_slides(
        html_path, out_dir, animation_targets=animation_targets or None
    )
    for slide_num, anns in animations.items():
        for ann, bbox in zip(anns, bboxes_by_slide.get(slide_num, [])):
            ann['bbox'] = bbox
            if bbox is None:
                print(f'  [WARN] bbox 未検出 Slide{slide_num}: 「{ann.get("target","")[:40]}」')
    detected = sum(1 for anns in animations.values() for a in anns if a.get('bbox'))
    print(f'  {len(screenshots)}枚 / bbox 検出 {detected}/{ann_total}件')

    scripts    = parse_voice_scripts(voice_path)
    labels     = parse_slide_labels(voice_path)
    ruidai_idx = find_ruidai_index(html_path.read_text())
    pairs = list(zip(screenshots, scripts))
    clip_paths: list[Path] = []

    # イントロ（既存クリップをそのまま使用）
    intro_clip = out_dir / 'clip_intro.mp4'
    if intro_clip.exists():
        clip_paths.append(intro_clip)
        print('  [イントロ] 既存クリップ利用')

    for idx, (img, script) in enumerate(pairs):
        i = idx + 1
        label = labels[idx] if idx < len(labels) else f'スライド{i}'
        print(f'  [Slide{i} {label}]', end=' ', flush=True)

        if idx == ruidai_idx and ruidai_hidden is not None:
            problem_script, solution_script = split_ruidai_script(script)
            for sfx, aname, img_use in [
                ('a', f'audio_{i:02d}a.wav', ruidai_hidden),
                ('b', f'audio_{i:02d}b.wav', ruidai_hidden),
                ('c', f'audio_{i:02d}c.wav', ruidai_hidden),
                ('',  f'audio_{i:02d}d.wav', img),
            ]:
                cname = f'clip_{i:02d}{sfx}.mp4' if sfx else f'clip_{i:02d}.mp4'
                ap, cp = out_dir / aname, out_dir / cname
                if ap.exists():
                    make_clip(img_use, ap, cp)
                    clip_paths.append(cp)
            print('類題✓')
        else:
            ap = out_dir / f'audio_{i:02d}.wav'
            cp = out_dir / f'clip_{i:02d}.mp4'
            if not ap.exists():
                print('音声キャッシュなし → スキップ');  continue
            slide_anns = [a for a in animations.get(idx + 1, []) if a.get('bbox')]
            if slide_anns:
                make_clip_animated(img, ap, cp, slide_anns, script)
                print(f'アノテーション{len(slide_anns)}件✓')
            else:
                make_clip(img, ap, cp)
                print('✓')
            clip_paths.append(cp)

    # アウトロ
    outro_audio = out_dir / 'audio_outro.wav'
    outro_clip  = out_dir / 'clip_outro.mp4'
    ending = ENDING_SLIDE if ENDING_SLIDE.exists() else screenshots[-1]
    if outro_audio.exists():
        make_clip(ending, outro_audio, outro_clip)
        clip_paths.append(outro_clip)
        print('  [アウトロ] ✓')

    final_path = OUTPUT_DIR / f'{stem}{suffix}.mp4'
    print(f'\n  結合 → {final_path.name} ...', end='', flush=True)
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


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--suffix', default='_animated')
    args = parser.parse_args()
    result = process_cached(Path(args.file), suffix=args.suffix)
    print(f'\n出力: {result}')
