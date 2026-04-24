# YouTube動画制作ワークフロー

高校数学YouTube動画（スライド形式）の制作手順・ルール・注意事項。

---

## ディレクトリ構造

```
StudyList/
├── problems/
│   ├── slide.css                         # 全スライド共通CSS
│   └── youtube_redesign/                 # YouTube動画素材の置き場
│       ├── {stem}.html                   # スライドHTML
│       ├── {stem}_voice.md               # 音声台本 + YouTubeメタデータ
│       ├── {stem}_edit.md                # 動画編集指示（強調・グラフ等）
│       ├── ending_slide.png              # 共通エンディングスライド
│       └── output/                       # 生成物（.gitignore対象だが一部追跡）
│           ├── {stem}/                   # 動画ごとの中間ファイル
│           │   ├── slide_NN.png          # スクリーンショット
│           │   ├── slide_ruidai_hidden.png  # 類題解答非表示版
│           │   ├── audio_NN.wav          # スライドごとの音声
│           │   ├── audio_outro.wav       # アウトロ音声
│           │   ├── clip_NN.mp4           # スライドごとのクリップ
│           │   └── clip_outro.mp4        # エンディングクリップ
│           └── {stem}.mp4                # 完成動画
└── tools/
    ├── slide_to_video.py                 # メイン動画生成パイプライン
    ├── make_thumbnails.py                # サムネイル生成
    └── make_ending_slide.py              # エンディングスライド生成
```

---

## 動画制作の全体フロー

```
1. スライドHTML作成
       ↓
2. 音声台本（*_voice.md）作成
       ↓
3. 編集指示（*_edit.md）作成（任意）
       ↓
4. 動画生成（slide_to_video.py）
       ↓
5. サムネイル生成（make_thumbnails.py）
```

---

## Step 1: スライドHTML

### ファイル命名規則
`problems/youtube_redesign/{subject}_{topic}.html`
例: `math1_quadratic_discriminant.html`

### スライド構成（固定：全6枚）
| スライド番号 | バッジ | 内容 |
|---|---|---|
| ① | `<span class="badge">科目</span>` | 問題提示 |
| ② | `<span class="badge orange">よくある間違い</span>` | 落とし穴・ひっかけ |
| ③ | `<span class="badge green">本質ポイント</span>` | 解法の核心 |
| ④ | `<span class="badge">解説</span>` | 解法手順（ステップ） |
| ⑤ | `<span class="badge green">一般化</span>` | 発展・まとめ |
| ⑥ | `<span class="badge green">類題</span>` | 類題（解答は `.answer-box` `.answer-label` で囲む） |

### スライドHTMLの基本テンプレート
```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>タイトル</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <link rel="stylesheet" href="../slide.css">
  <style>
    :root { --accent: #カラーコード; }
    .key-box { background: ...; border-left: 6px solid var(--accent); border-radius: 0 10px 10px 0; padding: 16px 24px; margin: 10px 0; font-size: 22px; font-weight: 700; }
  </style>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]})"></script>
</head>
<body>
<!-- URLコメント（GitHub Pages URL） -->
<div id="progress-bar"></div>

<!-- ① 問題提示 -->
<section class="slide active">
  <div class="slide-header">
    <span class="badge">数学X</span>
    <span class="slide-title">スライドタイトル</span>
    <div class="meta"><span>★★★☆☆ 標準</span><span>偏差値55〜65</span></div>
  </div>
  ...
  <div class="slide-footer"></div>
</section>

<!-- ② ③ ④ ⑤ スライド（class="slide"、activeなし） -->

<!-- ⑥ 類題 -->
<section class="slide">
  <div class="slide-header">
    <span class="badge green">類題</span>
    <span class="slide-title">類題タイトル</span>
  </div>
  <div class="problem-box">問題文</div>
  <!-- 解答（動画では最初非表示にしてから表示） -->
  <div class="answer-label">答　え</div>
  <div class="answer-box">解答</div>
  <div class="slide-footer"></div>
</section>

<!-- ナビゲーション（変更不要） -->
<div id="nav">...</div>
<script>/* スライド切り替えJS */</script>
</body>
</html>
```

### CSSクラス一覧（font-size目安）
| クラス | 用途 | サイズ |
|---|---|---|
| `.problem-box` | 問題文 | 21px |
| `.step` | 解法ステップ | 20px |
| `.answer-box` | 答え | 20px |
| `.key-formula` | 重要公式 | 22px |
| `.key-box` | キーポイント（inline定義） | 22px |
| `.section-title` | セクション見出し | 18px |
| `.point-list` | 箇条書き | 18px |
| `.slide-title` | スライドタイトル | 24px |
| `.badge` | 科目バッジ | 15px |

> **注意**: インラインの `style="font-size:Xpx"` も同比率で設定すること。
> 旧サイズ 15→18, 16→20, 18→22 が基準。

### アクセントカラーの目安
| 科目 | カラー |
|---|---|
| 数学I | `#4285F4`（青）/ `#c05621`（オレンジ）|
| 数学II | `#22C55E`（緑）/ `#0EA5E9`（水色）|
| 数学III | `#A855F7`（紫）/ `#EC4899`（ピンク）|
| 数学A | `#4ADE80`（ライトグリーン）|
| 数学B | `#FB923C`（オレンジ）/ `#F59E0B`（アンバー）|
| 数学C | `#6366F1`（インディゴ）|

---

## Step 2: 音声台本（*_voice.md）

### ファイル命名規則
`problems/youtube_redesign/{stem}_voice.md`

### フォーマット
```markdown
# 【音声台本】{科目}｜{タイトル}

対象スライド：{stem}.html
難易度：標準（偏差値55〜65）

※ 数式はAI音声読み上げ向けに日本語表記へ変換済み

---

## スライド①　問題提示

（台本本文）

---

## スライド②　よくある間違い

（台本本文）

---

## スライド③　本質ポイント

（台本本文）

---

## スライド④　解説

（台本本文）

---

## スライド⑤　一般化

（台本本文）

---

## スライド⑥　類題

（問題提示部分）

（空行で区切る）

（解答解説部分）

---

## YouTube メタデータ

### 動画タイトル案（3案）
1. ...
2. ...
3. ...

### 説明欄
{説明文}
{タグ行（カンマ区切り）}
例: #高校数学, #大学受験, #数学解説, #判別式, #数学I

### サムネイル案
- **メインコピー**：
- **サブコピー**：
- **数式表示**：
- **配色イメージ**：

### 固定コメント案
（チャンネル登録・高評価の促し文 + 絵文字）
```

### 台本執筆ルール
- **数式は全て日本語読み**に変換する（TTS向け）
  - `x²` → `xの2乗`、`√2` → `ルート2`、`∫` → `積分`
  - `D/4` → `Dを4で割った値`
- **スライド⑥（類題）は空行で問題と解答を分ける**（`split_ruidai_script` が最初の空行で分割）
- タグはカンマ区切り: `#高校数学, #大学受験, ...`

---

## Step 3: 動画生成（slide_to_video.py）

### 使用API
**Google Cloud Text-to-Speech API**（`texttospeech.googleapis.com`）
- GCPコンソールで発行したAPIキーを使用
- GCPコンソール → 「APIとサービス」→「Cloud Text-to-Speech API」を有効化すること
- 無料枠：月100万文字（Neural2音声）、事実上制限なしで利用可能
- 声：`ja-JP-Neural2-B`（日本語Neural2）

### 必要な環境変数
```bash
export GOOGLE_API_KEY=your_gcp_console_key  # GCPコンソール（Cloud TTS有効化済み）
```

### 実行方法
```bash
# Linux環境（/opt/pw-browsers にChromiumがある場合）
GOOGLE_API_KEY=xxx PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 tools/slide_to_video.py

# 特定の動画のみ
GOOGLE_API_KEY=xxx PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 tools/slide_to_video.py --file problems/youtube_redesign/{stem}.html
```

### 動画生成の内部フロー
1. Playwright でHTML全スライドをスクリーンショット（1280×720）
2. 類題スライドは解答非表示版（`slide_ruidai_hidden.png`）も撮影
3. 台本を`## スライド①〜⑥`で分割してスライドと対応付け
4. Cloud TTS API で音声生成（`texttospeech.googleapis.com/v1/text:synthesize`）
5. ImageClip + AudioFileClip でクリップ作成
6. 類題スライド（⑥）の特殊処理:
   - **A**: 問題スライド（非表示）+ 問題部分の音声 + 「自分で解いてみてください」
   - **B**: 問題スライド（非表示）+ 3秒無音
   - **C**: 解答スライド（表示）+ 解答解説の音声
7. アウトロ: `ending_slide.png` + アウトロ音声（テンプレート文）
8. 全クリップを結合して最終MP4を出力

### TTS設定
```python
TTS_VOICE = 'ja-JP-Neural2-B'  # 日本語Neural2音声
TTS_RATE  = 24000               # サンプリングレート
GAP_SECONDS = 0.5               # スライド間の無音
```

### アウトロテンプレート（変数: `{title}`）
```
以上！いかがでしたでしょうか！
今回は「{title}」について見ていきました！
この動画が少しでも参考になった方、またこんな感じの高校数学の問題を今後も見たいよ！
って方はチャンネル登録や高評価してくれると嬉しいです！
また、この動画で疑問に思ったことやわからなかったこと、また解説して欲しいよって問題の
ある方はコメントで教えてもらえると助かります！
それでは今日の動画はここまで！ばいば〜い！！
```

---

## エンディングスライド

- ファイル: `problems/youtube_redesign/ending_slide.png`
- サイズ: 1280×720px
- 内容: 数学テーマの幾何学的背景 + 中央に半透明白パネル + 固定テキスト
  - 「動画を最後まで見てくれてありがとうございます！」
  - 「チャンネル登録・高評価で次の動画を見逃さずに！」
  - 「コメントもお待ちしています！」
- 再生成: `python3 tools/make_ending_slide.py`
- **全ての新規動画・4時間以上前に作成した動画に適用**

---

## サムネイル生成

```bash
python3 tools/make_thumbnails.py
```

- 出力: `problems/youtube_redesign/thumbnails/{stem}.png`
- 設定は `make_thumbnails.py` 内の `THUMBNAILS` 辞書に定義
- 1280×720px、科目タグ・メインコピー・数式ボックス・バッジ付き

---

## 動画を再組み立て（TTS不要）

スライドのCSS変更やエンディングスライド更新など、音声を変えずに動画を作り直す場合:

1. スクリーンショットを再撮影（Playwright）
2. 既存 `.wav` ファイルをそのまま使用
3. `ImageClip + AudioFileClip` でクリップを再エンコード
4. 正しい順序で結合:
   - 通常スライド: `clip_01〜05.mp4`
   - 類題: `clip_06a.mp4` → `clip_06b.mp4` → `clip_06.mp4`
   - アウトロ: `clip_outro.mp4`（ending_slide.png使用）

---

## ブランチ運用

- **開発ブランチ**: `claude/automate-slide-audio-workflow-bGcHa`
- **本番ブランチ**: `main`
- 作業完了後は `main` にマージしてプッシュ

---

## 既存動画一覧（15本）

| stem | 科目 | タイトル | エンディング |
|---|---|---|---|
| math1_quadratic_discriminant | 数学I | 放物線とx軸の交点条件（判別式） | 旧スライド |
| math1_quadratic_trap | 数学I | 二次不等式の恒等的成立 | ending_slide.png |
| math2_exponential_substitution | 数学II | 指数方程式（置換テクニック） | ending_slide.png |
| math2_log_substitution | 数学II | 対数方程式（置換テクニック） | ending_slide.png |
| math3_integral_squared | 数学III | 三角置換による定積分 | 旧スライド |
| math3_integration_by_parts | 数学III | 部分積分の連鎖（e^x sinx） | 旧スライド |
| mathA_circular_nonadjacent | 数学A | 円順列×余事象（隣り合わない） | 旧スライド |
| mathA_circular_probability | 数学A | 円順列×確率（男女交互） | ending_slide.png |
| mathB_recurrence_divide | 数学B | 漸化式（両辺を割る） | ending_slide.png |
| mathB_sum_recurrence | 数学B | Sn型漸化式 | ending_slide.png |
| mathC_complex_factorize | 数学C | 複素数の絶対値最大値 | ending_slide.png |
| mathC_complex_identity | 数学C | z+1/z=1 から z³+1/z³ | ending_slide.png |
| math2_trig_compose | 数学II | 三角関数の合成（sinθ+√3cosθ の最大・最小） | ending_slide.png |
| math2_derivative_maxmin | 数学II | 微分の最大・最小（端点を見落とす落とし穴） | ending_slide.png |
| mathA_conditional_prob | 数学A | 条件付き確率（P(A\|B)とP(B\|A)の取り違え） | ending_slide.png |

> **旧スライドの4本**（discriminant, integral_squared, integration_by_parts, circular_nonadjacent）は次回再生成時に ending_slide.png が自動適用される。

---

## フォントに関する注意

- Linuxローカル環境のフォント: `/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf` (IPAゴシック)
- **IPAゴシックは絵文字非対応**。`make_ending_slide.py` など PIL使用箇所で絵文字を使うと□に化ける
- スライドHTML側（ブラウザ）は絵文字使用可能

---

## ファイル追加時のチェックリスト

- [ ] `{stem}.html` — スライド6枚構成、類題は `.answer-box` で解答囲む
- [ ] `{stem}_voice.md` — 台本6セクション、類題は空行で問題/解答分割、YouTubeメタデータ付き
- [ ] `{stem}_edit.md` — 編集指示（強調・グラフ・サムネ案）
- [ ] `make_thumbnails.py` の `THUMBNAILS` 辞書にエントリ追加
- [ ] `README.md` の問題一覧テーブルに行追加
- [ ] 動画生成後、`git add -f` で output/*.mp4 を含めてコミット・プッシュ
