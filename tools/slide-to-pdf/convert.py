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
    (macOS: Homebrew で brew install --cask google-chrome)
    (Linux:  sudo apt install chromium-browser)
    (Windows: https://www.google.com/chrome/ からインストール)
"""

import subprocess
import sys
import os
import shutil
import time
import platform

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


def find_chrome() -> str | None:
    """インストール済みのChromeを探す"""
    for candidate in CHROME_CANDIDATES:
        if os.path.isabs(candidate):
            if os.path.isfile(candidate):
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return None


def convert(input_html: str, output_pdf: str) -> None:
    chrome = find_chrome()
    if chrome is None:
        print("エラー: Google Chrome / Chromium が見つかりません。")
        print("インストールしてから再実行してください。")
        print("  macOS:   brew install --cask google-chrome")
        print("  Ubuntu:  sudo apt install chromium-browser")
        print("  Windows: https://www.google.com/chrome/")
        sys.exit(1)

    abs_input = os.path.abspath(input_html)
    abs_output = os.path.abspath(output_pdf)

    if not os.path.isfile(abs_input):
        print(f"エラー: ファイルが見つかりません: {abs_input}")
        sys.exit(1)

    file_url = f"file://{abs_input}"

    print(f"変換開始: {abs_input}")
    print(f"出力先  : {abs_output}")
    print(f"ブラウザ: {chrome}")

    # Chrome ヘッドレスモードで PDF 出力
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=5000",   # JS実行(KaTeX)を5秒待つ
        f"--print-to-pdf={abs_output}",
        "--print-to-pdf-no-header",
        file_url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        print(f"エラー (exit {result.returncode}):")
        print(result.stderr)
        sys.exit(1)

    if not os.path.isfile(abs_output):
        print("エラー: PDFが生成されませんでした。")
        sys.exit(1)

    size_kb = os.path.getsize(abs_output) // 1024
    print(f"完了: {abs_output} ({size_kb} KB)")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    input_html = args[0]
    output_pdf = args[1] if len(args) >= 2 else input_html.replace(".html", ".pdf")

    convert(input_html, output_pdf)


if __name__ == "__main__":
    main()
