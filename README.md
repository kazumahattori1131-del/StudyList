# 高校数学 YouTube 動画制作リポジトリ

高校数学のひっかけ問題・典型問題を解説するYouTube動画の制作素材をまとめたリポジトリ。

---

## ディレクトリ構造

```
StudyList/
├── problems/
│   ├── slide.css                      # 全スライド共通CSS
│   ├── slide.js                       # スライドナビゲーションJS
│   └── youtube_redesign/              # YouTube動画素材（本番）
│       ├── {stem}.html                # スライドHTML（全6枚）
│       ├── {stem}_voice.md            # 音声台本 + YouTubeメタデータ
│       ├── {stem}_edit.md             # 動画編集指示
│       ├── ending_slide.png           # 共通エンディングスライド
│       ├── thumbnails/                # サムネイル画像（1280×720）
│       └── output/                    # 生成物（MP4・中間ファイル）
└── tools/
    ├── slide_to_video.py              # メイン動画生成パイプライン
    ├── make_thumbnails.py             # サムネイル生成
    └── make_ending_slide.py           # エンディングスライド生成
```

---

## 動画一覧（全15本）

| stem | 科目 | タイトル |
|---|---|---|
| math1_quadratic_discriminant | 数学I | 放物線とx軸の交点条件（判別式） |
| math1_quadratic_trap | 数学I | 二次不等式の恒等的成立 |
| math2_exponential_substitution | 数学II | 指数方程式（置換テクニック） |
| math2_log_substitution | 数学II | 対数方程式（底の変換と置換） |
| math2_trig_compose | 数学II | 三角関数の合成（sinθ+√3cosθ の最大・最小） |
| math2_derivative_maxmin | 数学II | 微分の最大・最小（端点を見落とす落とし穴） |
| math3_integral_squared | 数学III | 三角置換による定積分 |
| math3_integration_by_parts | 数学III | 部分積分の連鎖（e^x sinx） |
| mathA_circular_nonadjacent | 数学A | 円順列×余事象（隣り合わない） |
| mathA_circular_probability | 数学A | 円順列×確率（男女交互） |
| mathA_conditional_prob | 数学A | 条件付き確率（P(A\|B)とP(B\|A)の取り違え） |
| mathB_recurrence_divide | 数学B | 漸化式（両辺を割る） |
| mathB_sum_recurrence | 数学B | Sn型漸化式 |
| mathC_complex_factorize | 数学C | 複素数の絶対値最大値 |
| mathC_complex_identity | 数学C | z+1/z=1 から z³+1/z³ |

---

## 動画生成方法

詳細は [WORKFLOW.md](./WORKFLOW.md) を参照。

```bash
# 依存ライブラリのインストール
pip3 install playwright google-genai moviepy pillow cryptography

# Chromiumブラウザ（Linux環境 /opt/pw-browsers がある場合はスキップ）
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 -m playwright install chromium

# 動画生成（特定ファイル）
GOOGLE_API_KEY=your_gcp_key PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers \
  python3 tools/slide_to_video.py --file problems/youtube_redesign/{stem}.html

# サムネイル生成
python3 tools/make_thumbnails.py
```

---

## 難易度基準

| 難易度 | 偏差値目安 |
|--------|-----------|
| ★★★☆☆ 標準 | 55〜65 |
| ★★★★☆ 応用 | 65〜75 |
