#!/usr/bin/env python3
"""
slide-to-pdf: HTMLスライドをPDFに変換するCLIツール

使い方:
    python3 convert.py <HTMLファイルパス> [出力PDFパス]

例:
    python3 convert.py ../../problems/math1/medium/quadratic_min_max_param.html
    python3 convert.py ../../problems/math2/medium/exponential_equation.html output.pdf

必要条件:
    Google Chrome / Chromium がインストールされていること
    pypdf がインストールされていること (pip install pypdf)

    (macOS: brew install --cask google-chrome)
    (Linux: sudo apt install chromium-browser)
    (Windows: https://www.google.com/chrome/)
"""

import re
import subprocess
import sys
import os
import shutil
import tempfile
from pathlib import Path

# ブラウザの候補（優先順）
CHROME_CANDIDATES = [
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    # Linux
    "google-chrome",
    "google-chrome-stable",
    "chromium-browser",
    "chromium",
    # Windows
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

# 各スライドのページサイズ（slide.css の @page と合わせる）
PAGE_WIDTH  = "277mm"
PAGE_HEIGHT = "156mm"


def find_chrome() -> str | None:
    for candidate in CHROME_CANDIDATES:
        if os.path.isabs(candidate):
            if os.path.isfile(candidate):
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return None


def count_slides(html_text: str) -> int:
    """HTML から .slide クラスの要素数を返す"""
    return len(re.findall(r'class="[^"]*\bslide\b[^"]*"', html_text))


def build_single_slide_html(html_text: str, slide_index: int) -> str:
    """指定インデックスのスライドだけを表示する HTML を生成する"""

    # ナビ・プログレスバー非表示 + 対象スライドのみ表示 のスタイルを注入
    inject_css = f"""
<style>
  #nav, #progress-bar {{ display: none !important; }}
  body {{ background: #fff !important; overflow: visible !important; }}
  .slide {{
    display: none !important;
    opacity: 0 !important;
  }}
  .slide:nth-of-type({slide_index + 1}) {{
    display: flex !important;
    opacity: 1 !important;
    position: relative !important;
    top: auto !important; left: auto !important;
    width: {PAGE_WIDTH} !important;
    height: {PAGE_HEIGHT} !important;
    min-height: unset !important;
    box-shadow: none !important;
    page-break-after: avoid !important;
    break-after: avoid !important;
    margin: 0 !important;
  }}
  * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
</style>
<style media="print">
  @page {{ size: {PAGE_WIDTH} {PAGE_HEIGHT}; margin: 0; }}
</style>
"""

    # </head> の直前に注入
    modified = re.sub(r"</head>", inject_css + "</head>", html_text, count=1)
    return modified


def chrome_print_to_pdf(chrome: str, html_path: str, pdf_path: str) -> None:
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=5000",  # KaTeX レンダリング待ち (5秒)
        f"--print-to-pdf={pdf_path}",
        "--print-to-pdf-no-header",
        f"file://{html_path}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Chrome エラー (exit {result.returncode}):\n{result.stderr}")


def merge_pdfs(pdf_paths: list[str], output_path: str) -> None:
    try:
        from pypdf import PdfWriter
    except ImportError:
        print("エラー: pypdf がインストールされていません。")
        print("  pip install pypdf")
        sys.exit(1)

    writer = PdfWriter()
    for p in pdf_paths:
        writer.append(p)
    with open(output_path, "wb") as f:
        writer.write(f)


def convert(input_html: str, output_pdf: str) -> None:
    chrome = find_chrome()
    if chrome is None:
        print("エラー: Google Chrome / Chromium が見つかりません。")
        print("  macOS:   brew install --cask google-chrome")
        print("  Ubuntu:  sudo apt install chromium-browser")
        print("  Windows: https://www.google.com/chrome/")
        sys.exit(1)

    abs_input  = os.path.abspath(input_html)
    abs_output = os.path.abspath(output_pdf)

    if not os.path.isfile(abs_input):
        print(f"エラー: ファイルが見つかりません: {abs_input}")
        sys.exit(1)

    html_text = Path(abs_input).read_text(encoding="utf-8")
    slide_count = count_slides(html_text)

    if slide_count == 0:
        print("エラー: .slide クラスの要素が見つかりません。")
        sys.exit(1)

    print(f"入力   : {abs_input}")
    print(f"出力   : {abs_output}")
    print(f"スライド: {slide_count} 枚")
    print(f"ブラウザ: {chrome}")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_pages: list[str] = []

        for i in range(slide_count):
            print(f"  [{i+1}/{slide_count}] スライドを変換中...", end="\r")

            # 対象スライドだけ表示する HTML を一時ファイルに書き出す
            # (相対パス css/js が機能するよう、元ファイルと同じディレクトリに配置)
            tmp_html = os.path.join(os.path.dirname(abs_input), f"__tmp_slide_{i}.html")
            tmp_pdf  = os.path.join(tmpdir, f"slide_{i:03d}.pdf")

            try:
                slide_html = build_single_slide_html(html_text, i)
                Path(tmp_html).write_text(slide_html, encoding="utf-8")
                chrome_print_to_pdf(chrome, tmp_html, tmp_pdf)
            finally:
                if os.path.exists(tmp_html):
                    os.remove(tmp_html)

            if not os.path.isfile(tmp_pdf):
                print(f"\nエラー: スライド {i+1} の PDF が生成されませんでした。")
                sys.exit(1)

            pdf_pages.append(tmp_pdf)

        print(f"\n結合中... ({slide_count} ページ)")
        merge_pdfs(pdf_pages, abs_output)

    size_kb = os.path.getsize(abs_output) // 1024
    print(f"完了: {abs_output} ({size_kb} KB, {slide_count} ページ)")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    input_html = args[0]
    output_pdf = (
        args[1] if len(args) >= 2
        else input_html.replace(".html", ".pdf")
    )

    convert(input_html, output_pdf)


if __name__ == "__main__":
    main()
