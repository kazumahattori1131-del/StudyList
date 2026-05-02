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

## 動画一覧（全33本）

※ MP4列：✅ 生成済み、— 未生成

| stem | 科目 | タイトル | MP4 |
|---|---|---|---|
| math1-01_quadratic_discriminant | 数学I | 放物線とx軸の交点条件（判別式） | ✅ |
| math1-02_quadratic_trap | 数学I | 二次不等式の恒等的成立 | ✅ |
| math1-03_quadratic_axis | 数学I | 2次関数の最大・最小（定義域が動く場合分け） | ✅ |
| math1-04_quadratic_complete | 数学I | 平方完成と頂点（計算ミスをなくす） | ✅ |
| math1-05_absolute_inequality | 数学I | 絶対値と不等式（場合分けの考え方） | ✅ |
| math2-01_exponential_substitution | 数学II | 指数方程式（置換テクニック） | ✅ |
| math2-02_log_substitution | 数学II | 対数方程式（底の変換と置換） | ✅ |
| math2-03_trig_compose | 数学II | 三角関数の合成（sinθ+√3cosθ の最大・最小） | ✅ |
| math2-04_derivative_maxmin | 数学II | 微分の最大・最小（端点を見落とす落とし穴） | ✅ |
| math2-05_integral_area | 数学II | 定積分と面積（1/12公式・符号ミス） | ✅ |
| math2-06_logarithm_concept | 数学II | 対数の概念（指数から対数へ） | ✅ |
| math2-07_trig_unit_circle | 数学II | 三角関数の定義と単位円 | — |
| math2-08_vieta_formulas | 数学II | 解と係数の関係（ビエタの公式） | ✅ |
| math2-09_integral_area | 数学II | 積分と面積（正負の領域の分割） | — |
| math2-10_log_inequality | 数学II | 対数不等式（底の確認と不等号逆転） | ✅ |
| math3-01_integral_squared | 数学III | 三角置換による定積分 | ✅ |
| math3-02_integration_by_parts | 数学III | 部分積分の連鎖（e^x sinx） | ✅ |
| math3-03_riemann_integral | 数学III | 区分求積法（数列の極限を定積分に変換） | ✅ |
| mathA-01_circular_nonadjacent | 数学A | 円順列×余事象（隣り合わない） | ✅ |
| mathA-02_circular_probability | 数学A | 円順列×確率（男女交互） | ✅ |
| mathA-03_conditional_prob | 数学A | 条件付き確率（P(A\|B)とP(B\|A)の取り違え） | ✅ |
| mathA-04_repeated_trial | 数学A | 反復試行の確率（組み合わせの係数を忘れる落とし穴） | ✅ |
| mathB-01_recurrence_divide | 数学B | 漸化式（両辺を割る） | ✅ |
| mathB-02_sum_recurrence | 数学B | Sn型漸化式 | ✅ |
| mathB-03_recurrence_char | 数学B | 漸化式（特性方程式） | ✅ |
| mathB-04_sum_arithmetic_geometric | 数学B | 等差×等比型の和（差し引き法） | ✅ |
| mathB-05_vector_inner | 数学B | ベクトルの内積と大きさ（\|a+b\|の落とし穴） | ✅ |
| mathB-06_hypothesis_test | 数学B | 統計的な推測（仮説検定の考え方） | — |
| mathB-07_vector_magnitude | 数学B | ベクトルの大きさ（\|a+b\|は足し算できない） | ✅ |
| mathC-01_complex_factorize | 数学C | 複素数の絶対値最大値 | ✅ |
| mathC-02_complex_identity | 数学C | z+1/z=1 から z³+1/z³ | ✅ |
| mathC-03_complex_rotation | 数学C | 複素数の累乗とド・モアブルの定理 | ✅ |
| mathC-04_conic_sections | 数学C | 二次曲線（楕円の方程式） | — |

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
