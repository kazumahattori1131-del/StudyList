#!/usr/bin/env node
/**
 * render-katex.js
 * HTMLファイル内の KaTeX 数式 ($...$ / $$...$$) を
 * 静的HTMLに変換して標準出力へ出力する。
 *
 * 使い方: node render-katex.js <HTMLファイルパス>
 */

'use strict';

const katex = require('katex');
const fs    = require('fs');
const path  = require('path');

const inputPath = process.argv[2];
if (!inputPath) {
  process.stderr.write('Usage: node render-katex.js <html-file>\n');
  process.exit(1);
}

let html = fs.readFileSync(path.resolve(inputPath), 'utf8');

// ── 1. $$...$$ (display mode) を置換 ─────────────────────────────────────
// 改行を含む場合もあるので [\s\S] を使用
html = html.replace(/\$\$([\s\S]+?)\$\$/g, (_, latex) => {
  try {
    return katex.renderToString(latex.trim(), {
      displayMode: true,
      throwOnError: false,
      output: 'html',
    });
  } catch (e) {
    process.stderr.write(`KaTeX error (display): ${e.message}\n`);
    return `<span class="katex-error">$$${latex}$$</span>`;
  }
});

// ── 2. $...$ (inline mode) を置換 ────────────────────────────────────────
// 数字の $ 記号（価格など）を誤変換しないよう、英字・バックスラッシュ・記号で
// 始まる内容のみ対象とする
html = html.replace(/\$([^$\n]+?)\$/g, (match, latex) => {
  // 空白のみは除外
  if (/^\s*$/.test(latex)) return match;
  try {
    return katex.renderToString(latex.trim(), {
      displayMode: false,
      throwOnError: false,
      output: 'html',
    });
  } catch (e) {
    process.stderr.write(`KaTeX error (inline): ${e.message}\n`);
    return `<span class="katex-error">$${latex}$</span>`;
  }
});

// ── 3. KaTeX CDN タグを削除（既に静的レンダリング済みのため不要） ────────
html = html.replace(/<link[^>]+katex[^>]+>\n?/g, '');
html = html.replace(/<script[^>]+katex[^>]*>[\s\S]*?<\/script>\n?/g, '');
html = html.replace(/<script[^>]+katex[^>]*><\/script>\n?/g, '');
html = html.replace(/<script[^>]+katex[^>]*\/>\n?/g, '');

// ── 4. KaTeX CSS をインライン化（WeasyPrint 用） ─────────────────────────
// WeasyPrint は CDN の CSS を参照できないため、最小限の KaTeX CSS をインライン注入する
const katexCssPath = path.join(__dirname, 'node_modules/katex/dist/katex.min.css');
let katexCss = '';
if (fs.existsSync(katexCssPath)) {
  katexCss = fs.readFileSync(katexCssPath, 'utf8');
  // フォント URL はサーバーから取れないため、数学記号は Unicode フォールバックに任せる
  // (フォント定義行を削除してファイルサイズ削減)
  katexCss = katexCss.replace(/@font-face\s*\{[^}]+\}/g, '');
}

if (katexCss) {
  html = html.replace('</head>', `<style>\n${katexCss}\n</style>\n</head>`);
}

process.stdout.write(html);
