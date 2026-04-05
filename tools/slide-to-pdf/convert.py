#!/usr/bin/env python3
"""
slide-to-pdf: HTMLスライドをPDFに変換するCLIツール

【使い方】
    python3 convert.py <HTMLファイルパス> [出力PDFパス]

【例】
    python3 convert.py ../../problems/math1/medium/quadratic_min_max_param.html
    python3 convert.py ../../problems/math2/medium/exponential_equation.html output.pdf

【仕組み】
    1. Node.js (render-katex.js) で数式を静的HTMLに事前レンダリング
    2. スライドごとに個別PDF化 (WeasyPrint)
    3. pypdf で全ページを結合

【必要条件】
    - Node.js v16 以上
    - Python 3.9 以上
    - pip install weasyprint pypdf
    - (初回のみ) cd tools/slide-to-pdf && npm install
"""

import re
import subprocess
import sys
import os
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
RENDER_KATEX_JS = SCRIPT_DIR / "render-katex.js"

# スライドページサイズ (slide.css の @page と同じ)
# 1280px / 96dpi = 13.33inch = 338.7mm
# 720px  / 96dpi =  7.5inch = 190.5mm
PAGE_WIDTH  = "339mm"
PAGE_HEIGHT = "191mm"


# ── ユーティリティ ──────────────────────────────────────────────────────────

def check_dependencies() -> None:
    """必要なツールの存在確認"""
    # Node.js
    result = subprocess.run(["node", "--version"], capture_output=True)
    if result.returncode != 0:
        _die("Node.js が見つかりません。https://nodejs.org/ からインストールしてください。")

    # katex
    if not (SCRIPT_DIR / "node_modules" / "katex").exists():
        _die(
            "katex がインストールされていません。\n"
            f"  cd {SCRIPT_DIR} && npm install"
        )

    # WeasyPrint
    try:
        import weasyprint  # noqa: F401
    except ImportError:
        _die("WeasyPrint がインストールされていません。\n  pip install weasyprint")

    # pypdf
    try:
        import pypdf  # noqa: F401
    except ImportError:
        _die("pypdf がインストールされていません。\n  pip install pypdf")


def _die(msg: str) -> None:
    print(f"エラー: {msg}")
    sys.exit(1)


# ── KaTeX 事前レンダリング ──────────────────────────────────────────────────

def prerender_katex(html_path: Path) -> str:
    """Node.js で数式を静的HTMLに変換して返す"""
    result = subprocess.run(
        ["node", str(RENDER_KATEX_JS), str(html_path)],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        _die(f"KaTeX レンダリングに失敗しました:\n{result.stderr}")
    if result.stderr:
        # 警告は表示するが続行
        for line in result.stderr.strip().splitlines():
            print(f"  警告: {line}")
    return result.stdout


# ── スライド分割 ────────────────────────────────────────────────────────────

def count_slides(html: str) -> int:
    # <section class="slide"> または <section class="slide active"> のみ対象
    return len(re.findall(r'<section\s[^>]*class="slide[" ]', html))


def build_single_slide_html(html: str, original_dir: Path, slide_index: int) -> str:
    """
    指定インデックスのスライドだけを表示するHTMLを返す。
    相対パス (slide.css / slide.js) を絶対パスに書き換えて WeasyPrint から参照できるようにする。
    """
    # 相対パスを絶対パスに変換
    def to_abs(m):
        attr  = m.group(1)  # href= or src=
        quote = m.group(2)  # " or '
        rel   = m.group(3)  # パス部分
        if rel.startswith(("http://", "https://", "//", "data:")):
            return m.group(0)
        abs_path = (original_dir / rel).resolve()
        return f'{attr}{quote}{abs_path}{quote}'

    html = re.sub(
        r'(href=|src=)(["\'])(?!http|//|data:)([^"\']+)\2',
        to_abs, html
    )

    inject = f"""
<style>
  #nav, #progress-bar {{ display: none !important; }}
  body {{
    background: #f0f4f8 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }}
  /* 全スライドを非表示にしたうえで対象だけ表示 */
  .slide {{
    display: none !important;
    opacity: 0 !important;
  }}
  .slide:nth-of-type({slide_index + 1}) {{
    display: flex !important;
    opacity: 1 !important;
    position: relative !important;
    top: auto !important;
    left: auto !important;
    width: {PAGE_WIDTH} !important;
    min-height: {PAGE_HEIGHT} !important;
    height: auto !important;           /* コンテンツ量に応じて伸縮 */
    overflow: visible !important;
    box-shadow: none !important;
    page-break-after: avoid !important;
    break-after: avoid !important;
    margin: 0 auto !important;
  }}
  /* answer-sheet の flex:1 を解除（WeasyPrint でのページ膨張を防ぐ） */
  .slide:nth-of-type({slide_index + 1}) .answer-sheet {{
    flex: none !important;
    min-height: 120px !important;
  }}
  /* 罫線の ::before 疑似要素を無効化（WeasyPrint の高さ計算を安定させる） */
  .slide:nth-of-type({slide_index + 1}) .answer-sheet::before {{
    display: none !important;
  }}
  /* slide-footer の margin-top:auto を固定値に（空白ページを防ぐ） */
  .slide:nth-of-type({slide_index + 1}) .slide-footer {{
    margin-top: 24px !important;
  }}
  * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
</style>
<style media="print">
  @page {{ size: {PAGE_WIDTH} auto; margin: 0; }}
</style>
"""
    return re.sub(r"</head>", inject + "</head>", html, count=1)


# ── PDF 生成 ────────────────────────────────────────────────────────────────

def slide_to_pdf(html: str, original_dir: Path, slide_index: int, out_path: str) -> None:
    from weasyprint import HTML as WP_HTML
    slide_html = build_single_slide_html(html, original_dir, slide_index)
    WP_HTML(string=slide_html, base_url=str(original_dir)).write_pdf(out_path)


def merge_pdfs(pdf_paths: list[str], output_path: str) -> None:
    from pypdf import PdfWriter
    writer = PdfWriter()
    for p in pdf_paths:
        writer.append(p)
    with open(output_path, "wb") as f:
        writer.write(f)


# ── メイン ──────────────────────────────────────────────────────────────────

def convert(input_html: str, output_pdf: str) -> None:
    check_dependencies()

    abs_input  = Path(input_html).resolve()
    abs_output = Path(output_pdf).resolve()

    if not abs_input.is_file():
        _die(f"ファイルが見つかりません: {abs_input}")

    print(f"入力   : {abs_input}")
    print(f"出力   : {abs_output}")

    # ── Step 1: KaTeX 事前レンダリング ──
    print("数式をレンダリング中...")
    rendered_html = prerender_katex(abs_input)

    slide_count = count_slides(rendered_html)
    if slide_count == 0:
        _die(".slide クラスの要素が見つかりません。")
    print(f"スライド: {slide_count} 枚")

    # ── Step 2: スライドごとにPDF化 ──
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_pages: list[str] = []

        for i in range(slide_count):
            print(f"  [{i+1:2d}/{slide_count}] 変換中...", end="\r")
            tmp_pdf = os.path.join(tmpdir, f"slide_{i:03d}.pdf")
            slide_to_pdf(rendered_html, abs_input.parent, i, tmp_pdf)
            if not os.path.isfile(tmp_pdf):
                _die(f"スライド {i+1} のPDF生成に失敗しました。")
            pdf_pages.append(tmp_pdf)

        # ── Step 3: 結合 ──
        print(f"\n結合中... ({slide_count} ページ)")
        merge_pdfs(pdf_pages, str(abs_output))

    from pypdf import PdfReader
    actual_pages = len(PdfReader(str(abs_output)).pages)
    size_kb = abs_output.stat().st_size // 1024
    note = f" ({slide_count}スライド)" if actual_pages != slide_count else ""
    print(f"完了: {abs_output} ({size_kb} KB, {actual_pages} ページ{note})")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    input_html = args[0]
    output_pdf = (
        args[1] if len(args) >= 2
        else re.sub(r"\.html$", ".pdf", input_html)
    )
    convert(input_html, output_pdf)


if __name__ == "__main__":
    main()
