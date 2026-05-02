# このリポジトリでの作業ルール

---

## 指示・学習事項の即時記録ルール（全セッション共通・例外なし）

**ユーザーから新しい指示・好み・ルール・落とし穴を受け取ったら、どのチャットセッションであっても、作業と並行してその場で記録し、コミット・プッシュまで完了させる。**
同じ指示を次のセッションで繰り返させないことが目的。後回し厳禁。

| 内容の種類 | 記録先 |
|---|---|
| ワークフロー・好み・制約（「〜してはいけない」「〜を使う」など） | `CLAUDE.md` |
| 技術的なバグ・落とし穴・エラーの原因と対策 | `PITFALLS.md` |

記録後は必ず `git commit && git push origin main`（または現在のブランチ → main へマージ）して、**必ず main に反映**すること。
feature ブランチだけでは次セッションで読み込まれないリスクがある。

---

## ブランチ・マージのルール

作業完了後、生成物や修正に問題がなければ **自動的に main へマージ・プッシュする**。ユーザーに確認を求めない。

動画生成が途中で停止した場合でも、**完成済みの分はその時点で main へマージ・プッシュする**。「現時点で作成完了しているものをmainにpush」の指示があった場合も同様。

---

## 新セッション開始時の必須確認（動画生成に関わる場合）

動画生成タスクを開始する前に、**必ず以下を確認してから作業に入る**こと。

### 1. PITFALLS.md を読む
`PITFALLS.md` に過去のバグと対策がまとめられている。特にセクション 3（Gemini TTS）は必読。

### 2. slide_to_video.py の TTS 設定を目視確認する
以下の3点を `grep` またはファイル先頭付近で確認する。

| 確認項目 | 正しい値 | 変えてはいけない理由 |
|---|---|---|
| `GEMINI_TTS_VOICE` | `'Leda'` | ユーザー指定。他の声に変えない |
| `GEMINI_TTS_STYLE_PREFIX` | 非空文字列（カタカナ語発音指示を含む） | 空にするとβ→ベート等の誤読が起きる |
| `generate_audio_gemini` 内の `contents=` | `GEMINI_TTS_STYLE_PREFIX + normalize_for_tts(text)` が入っている | **定義するだけでは反映されない（PITFALLS.md 3-8）** |

**確認コマンド例:**
```bash
grep -n "GEMINI_TTS_VOICE\|tts_text\|contents=tts" tools/slide_to_video.py
```
`contents=tts_text` または `GEMINI_TTS_STYLE_PREFIX +` が `generate_audio_gemini` 内に存在することを確認する。

### 3. アニメーション（_edit.md）の注意点
- `強調対象` は HTML の**実際の日本語テキスト**から引用する（LaTeX のみは不可）
- 対応する `方法`: `赤枠` / `丸枠` / `アンダーライン` / `矢印`
- `タイミング`: `77%` 形式が使える（数式が多いスライドは比率より % 指定が正確）
- 詳細は `PITFALLS.md` セクション 7 参照

---

## 動画生成・長時間タスクの注意事項

### タイムアウト前の自動再開確認
長時間かかるタスク（動画生成・音声生成など）を開始する前に、
Claude のコンテキスト制限に近づく可能性がある場合は、
**作業を再開するかどうかユーザーに確認してから**、自動再開スクリプトをあらかじめ仕込むこと。

例: 「このタスクは時間がかかります。タイムアウトに備えて自動再開スクリプトを仕込んでおきますか？」

### 再開スクリプトのパターン
`tools/resume_after_timeout.sh` が参考実装。
- sleep で待機 → 生成済みをスキップして未生成のみ実行 → コミット・プッシュ
- 常に `$GEMINI_API_KEY` 環境変数で APIキーを受け取る（ハードコード禁止）

---

## TTS / 動画生成

- Gemini TTS 無料クォータ: **100リクエスト/日**（`gemini-2.5-flash-preview-tts`）
- 音声キャッシュ機能あり（テキスト変更がなければ再生成しない）
- APIキーは環境変数 `GEMINI_API_KEY` で渡す
- 生成スクリプト: `tools/slide_to_video.py`

---

## ブランチ

開発ブランチ: `claude/add-video-animations-7vYC4`

---

## チャンネルのコアコンセプト（最重要・常に踏まえること）

> **「わからなかった問題がわかり、解けるようになる」**

すべての動画はこのコンセプトを軸に作る。解説の丁寧さ・落とし穴の提示・類題演習の充実は、
この「わかった → 解ける」の体験を視聴者に届けるためのものである。
コンテンツの改定・新規作成・タイトル検討のいずれの場面でも、**この軸がブレていないか**を常に確認する。

---

## YouTube 動画の需要・伸ばし方（データに基づく方針）

視聴データより、以下のパターンがヒットしやすいことが判明している。

### タイトルの鉄則：「反直感フック ＋ 具体的な恩恵」

| 要素 | 例 | 効果 |
|------|-----|------|
| 反直感フック | 「解の公式は使わない！」「2回やると元に戻る！」 | 常識を否定されて思わず見てしまう |
| 具体的な恩恵 | 「係数だけで瞬殺」「移項で一発解決」 | 「速く・簡単に解ける」メリットが伝わる |

```
【数学II・単元名】○○は使わない！△△だけで瞬殺する
【数学II・単元名】○○すると元に戻る！移項で一発解決
```

### 需要が高い単元の選び方

- **頻出＋落とし穴あり** の単元を優先する（解と係数の関係・微分の最大最小・指数方程式など）
- 「教科書通りにやると失点する」「習ったはずの公式が通用しない」角度で切ると差別化できる
- 検索需要が高い単元ほどタイトルの反直感フックが効きやすい

### 標準スライド構成（全8枚・確定フォーマット）

新規動画はすべて以下の構成で作る。math2-09（積分と面積）で完成した形式。

| # | スライド | 内容・ポイント |
|---|---------|--------------|
| ① | **フック** | 冒頭15〜20秒。「落とし穴の正体」を先にチラ見せ。グラフや対比で視覚化する |
| ② | 問題提示 | 問題文＋グラフ（余白に SVG インライン）。グラフは正・負の領域を色分け |
| ③ | よくある間違い | 典型的な誤答と「なぜ間違いか」の説明 |
| ④ | 本質ポイント | 正しい手順を4ステップで整理 |
| ⑤ | 解説 | ステップに沿って丁寧に計算 |
| ⑥ | 一般化 | 手順まとめ・注意点 |
| ⑦ | **類題** | 問題＋解答（解答にもグラフを入れる） |
| ⑧ | **まとめ** | 「今日の一言」で視聴維持率を改善 |

#### フックスライドの作り方
- 「積分したら0？」「解の公式は使わない？」など常識を否定する一文
- 左に計算・右にグラフの横並びレイアウトが効果的
- 答えは「正しくは〇〇」まで見せてしまう（タイトルとも連動）

#### グラフの入れ方（SVG インライン）
- 問題提示スライド（②）と類題解答（⑦）には必ず SVG グラフを入れる
- 正の領域は `fill="#bbf7d0"`（緑）、負の領域は `fill="#fecaca"`（赤）で色分け
- 面積の大きさをグラフ内にラベル（例: `1/6`, `5/6`）で表記する
- グラフは `display:flex` で解説テキストと横並びに配置する
- 参考実装: `math2-09_integral_area.html`

---

## 動画コンテンツ作成仕様（math2-10 を基準フォーマット）

> **参照ファイル**: `problems/youtube_redesign/math2-10_log_inequality.html`
> 新規動画は math2-10 の構造を骨格とする。

### ファイル配置

```
problems/youtube_redesign/math2-NN_slug.html
problems/youtube_redesign/math2-NN_slug_voice.md
problems/youtube_redesign/math2-NN_slug_edit.md
```

### HTML 骨格テンプレート

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>【数学II・単元名】タイトル</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <link rel="stylesheet" href="../slide.css">
  <style>
    :root { --accent: #XXXXXX; }
    .key-box   { background:#f5f3ff; border-left:6px solid var(--accent); border-radius:0 10px 10px 0;
                 padding:16px 24px; margin:10px 0; font-size:22px; font-weight:700; }
    .trap-box  { background:#fff5f5; border:2px solid #fc8181; border-radius:10px; padding:14px 24px; margin:10px 0; }
    .trap-title{ color:#c53030; font-weight:800; font-size:22px; margin-bottom:6px; }
    .ok-box    { background:#f0fff4; border:2px solid #48bb78; border-radius:10px; padding:14px 24px; margin:10px 0; }
    .step-box  { background:#fafafa; border:1.5px solid #d1d5db; border-radius:10px;
                 padding:12px 20px; margin:8px 0; font-size:20px; }
    .step-num  { display:inline-block; background:var(--accent); color:#fff; border-radius:50%;
                 width:28px; height:28px; text-align:center; line-height:28px; font-size:15px;
                 font-weight:700; margin-right:8px; }
    .rule-row  { display:flex; gap:16px; margin:8px 0; }
    .rule-card { flex:1; border-radius:10px; padding:14px 16px; font-size:19px; text-align:center; }
    .rule-inc  { background:#eff6ff; border:2px solid #3B82F6; }
    .rule-dec  { background:#fff5f5; border:2px solid #ef4444; }
    .graph-wrap{ display:flex; align-items:center; gap:24px; margin:0.8rem 0; }
  </style>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body,{delimiters:[
      {left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]})"></script>
</head>
<body>
<!--
https://kazumahattori1131-del.github.io/StudyList/problems/youtube_redesign/math2-NN_slug.html
-->
<div id="progress-bar"></div>
<!-- 8 section.slide blocks here（① active, ②〜⑧ not active） -->
<div id="nav">
  <button id="btn-prev">◀ 前へ</button>
  <span class="page-info" id="pinfo">1 / 8</span>
  <button id="btn-next">次へ ▶</button>
  <button id="btn-pdf" onclick="window.print()">⬇ PDF保存</button>
  <span class="hint">← → キーでも操作できます</span>
</div>
<script src="../slide.js"></script>
</body>
</html>
```

### アクセント色（単元カテゴリ別）

| カテゴリ | `--accent` | `.key-box` background |
|---|---|---|
| 対数・指数 | `#7C3AED`（紫） | `#f5f3ff` |
| 積分・微分 | `#0EA5E9`（青） | `#eff6ff` |
| 数列 | `#10B981`（緑） | `#f0fdf4` |
| 複素数・ベクトル | `#F59E0B`（橙） | `#fffbeb` |

### バッジカラー

| スライド | badge クラス | 表示テキスト例 |
|---|---|---|
| ① フック | `badge orange` | `落とし穴` |
| ② 問題提示 | `badge` | `数学II` |
| ③ よくある間違い | `badge orange` | `よくある間違い` |
| ④ 本質ポイント | `badge green` | `本質ポイント` |
| ⑤ 解説 | `badge` | `解説` |
| ⑥ 一般化 | `badge green` | `一般化` |
| ⑦ 類題 | `badge green` | `類題` |
| ⑧ まとめ | `badge green` | `まとめ` |


---

### スライド別レイアウト仕様

#### ① フック

```html
<section class="slide active">
  <div class="slide-header">
    <span class="badge orange">落とし穴</span>
    <span class="slide-title">○○が△△になる！</span>
  </div>
  <div style="font-size:22px; margin-top:0.6rem;">
    この問題、どう解きますか？
    <div class="problem-box" style="margin:10px 0; font-size:24px;">[問題式]</div>
  </div>
  <!-- 誤答 vs 正解の2カラム -->
  <div style="display:flex; gap:20px; margin-top:0.8rem;">
    <div class="trap-box" style="flex:1;">
      <div class="trap-title">❌ よくある誤答</div>
      <div style="font-size:20px; margin:6px 0;">[誤答の計算過程]</div>
      <div style="color:#c53030; font-size:17px;">真面目に公式を覚えた人がハマる罠！</div>
    </div>
    <div class="ok-box" style="flex:1;">
      <div style="color:#166534; font-weight:800; font-size:22px; margin-bottom:6px;">✅ 正しい答え</div>
      <div style="font-size:26px; font-weight:700; text-align:center; margin:8px 0;">[正解]</div>
      <div style="color:#166534; font-size:17px;">[なぜ違うか一言]</div>
    </div>
  </div>
  <div class="key-box" style="margin-top:12px; font-size:20px;">
    🔑 [核心を一言で]<br>
    <span style="font-size:17px; font-weight:400;">[補足]</span>
  </div>
  <div class="slide-footer"></div>
</section>
```

#### ② 問題提示

```html
<section class="slide">
  <div class="slide-header">
    <span class="badge">数学II</span>
    <span class="slide-title">単元名（テーマ）</span>
    <div class="meta"><span>★★★☆☆ 標準</span><span>偏差値55〜65</span></div>
  </div>
  <div class="problem-label">問　題</div>
  <div class="problem-box">[問題文]</div>
  <div class="graph-wrap">
    <div style="flex:1; font-size:19px; line-height:1.9;">
      💬 [グラフの読み方]<br>[解のイメージ]
    </div>
    <svg width="230" height="170" style="flex-shrink:0; border:1px solid #d1d5db; border-radius:8px; background:#fafafa;">
      [SVGグラフ（下記「SVGグラフ仕様」参照）]
    </svg>
  </div>
  <div style="font-size:18px; background:#f5f3ff; border-radius:8px; padding:10px 16px; margin-top:6px;">
    ⚠️ [注意点の一言]
  </div>
  <div class="slide-footer">出典：教科書例題・数学II（改題）</div>
</section>
```

#### ③ よくある間違い

```html
<section class="slide">
  <div class="slide-header">
    <span class="badge orange">よくある間違い</span>
    <span class="slide-title">「○○」と思い込む落とし穴</span>
  </div>
  <div style="font-size:19px; margin-bottom:8px;">「真面目に勉強した人」ほどハマる間違いを確認します。</div>
  <div class="trap-box">
    <div class="trap-title">❌ 間違った解法</div>
    <div style="font-size:20px; line-height:2; margin:6px 0;">[誤答の計算ステップ]</div>
    <div style="font-size:17px; color:#744;">⛔ 原因：[なぜ間違うか]</div>
  </div>
  <div style="margin-top:12px;">
    <strong style="font-size:19px;">○○と△△の関係（必須知識）</strong>
    <div class="rule-row" style="margin-top:8px;">
      <div class="rule-card rule-inc">[条件A]<br>→ [結果A]</div>
      <div class="rule-card rule-dec">[条件B]<br>→ [結果B]<br><strong style="color:#ef4444;">逆転！</strong></div>
    </div>
  </div>
  <div class="slide-footer"></div>
</section>
```


#### ④ 本質ポイント

```html
<section class="slide">
  <div class="slide-header">
    <span class="badge green">本質ポイント</span>
    <span class="slide-title">○○の4ステップ解法</span>
  </div>
  <div class="key-box">✅ この手順を身につければ、○○を<strong>X分以内</strong>に確実に解ける！</div>
  <div style="margin-top:12px;">
    <div class="step-box"><span class="step-num">1</span><strong>[ステップ1]</strong></div>
    <div class="step-box"><span class="step-num">2</span><strong>[ステップ2]</strong></div><!-- ← animation の主ターゲット -->
    <div class="step-box"><span class="step-num">3</span><strong>[ステップ3]</strong></div>
    <div class="step-box"><span class="step-num">4</span><strong>[ステップ4]</strong></div>
  </div>
  <div style="margin-top:10px; font-size:18px; background:#fef9c3; border:2px solid #fbbf24; border-radius:8px; padding:10px 16px;">
    💡 [模試での時間節約アドバイス]
  </div>
  <div class="slide-footer"></div>
</section>
```

#### ⑤ 解説

```html
<section class="slide">
  <div class="slide-header">
    <span class="badge">解説</span>
    <span class="slide-title">[問題式]を正しく解く</span>
  </div>
  <div style="margin-top:0.6rem;">
    <div class="step-box"><span class="step-num">1</span><strong>真数条件：</strong>[条件式]</div>
    <div class="step-box"><span class="step-num">2</span><strong>底を確認：</strong>[底の値] → <span style="color:#ef4444; font-weight:700;">単調○○</span></div>
    <div class="step-box">
      <span class="step-num">3</span>[変換の計算]<br>
      <!-- animation ターゲットには固有 id の span を振る（PITFALLS.md 7-1） -->
      　<span id="s5-flip">[アニメーションターゲット文字列]</span>
      <span style="color:var(--accent); font-weight:700;">[結果式]</span>
    </div>
    <!-- ステップ4は緑で強調 -->
    <div class="step-box" style="background:#f0fff4; border-color:#48bb78;">
      <span class="step-num" style="background:#166534;">4</span>
      [真数条件との共通部分]：$$\boxed{[答え]}$$
    </div>
  </div>
  <div class="slide-footer"></div>
</section>
```

#### ⑥ 一般化

```html
<section class="slide">
  <div class="slide-header">
    <span class="badge green">一般化</span>
    <span class="slide-title">○○の鉄則まとめ</span>
  </div>
  <div class="key-box" style="font-size:20px; line-height:1.8;">
    📌 [一般的な公式]：
    <div class="rule-row" style="margin-top:10px;">
      <div class="rule-card rule-inc" style="font-size:18px;"><strong>[条件A]</strong><br>→ [結果A]</div>
      <div class="rule-card rule-dec" style="font-size:18px;"><strong>[条件B]</strong><br>→ [結果B]<br><span style="color:#dc2626;">逆転！</span></div>
    </div>
  </div>
  <div style="margin-top:12px;">
    <strong style="font-size:19px;">試験で差がつくポイント</strong>
    <div class="step-box" style="margin-top:8px;">① <strong>[ポイント1]</strong></div>
    <div class="step-box">② <strong>[ポイント2]</strong></div>
  </div>
  <div style="margin-top:10px; background:#fef9c3; border:2px solid #fbbf24; border-radius:8px; padding:10px 16px; font-size:18px;">
    ⏱️ [実践効果の一言]
  </div>
  <div class="slide-footer"></div>
</section>
```

#### ⑦ 類題

```html
<section class="slide">
  <div class="slide-header">
    <span class="badge green">類題</span>
    <span class="slide-title">[類題のテーマ]</span>
  </div>
  <div class="problem-box" style="font-size:21px;">[類題の問題文]</div>
  <!-- class="step" は必須：解答エリアを初期非表示にする（PITFALLS.md 7-5） -->
  <div class="graph-wrap step" style="margin-top:8px;">
    <div style="flex:1; font-size:19px; line-height:2.1;">
      <div class="step-box" style="margin-bottom:4px;"><span class="step-num">1</span>[ステップ1]</div>
      <div class="step-box" style="margin-bottom:4px;"><span class="step-num">2</span>[ステップ2]</div>
      <div class="step-box" style="margin-bottom:4px;"><span class="step-num">3</span>[ステップ3]</div>
      <div class="step-box" style="background:#f0fff4; border-color:#48bb78;">
        <span class="step-num" style="background:#166534;">4</span>
        [共通部分] $$\boxed{[答え]}$$
      </div>
    </div>
    <svg width="210" height="170" style="flex-shrink:0; border:1px solid #d1d5db; border-radius:8px; background:#fafafa;">
      [SVGグラフ]
    </svg>
  </div>
  <div class="slide-footer"></div>
</section>
```

#### ⑧ まとめ

```html
<section class="slide">
  <div class="slide-header">
    <span class="badge green">まとめ</span>
    <span class="slide-title">今日の一言</span>
  </div>
  <div style="text-align:center; margin-top:2rem;">
    <div class="key-box" style="display:inline-block; text-align:left; max-width:640px; font-size:22px; line-height:2;">
      🔑 [単元の核心]<br>
      [条件A] → [結果A]<br>
      [条件B] → <span style="color:#dc2626;">[結果B]</span><br>
      <span style="font-size:18px; font-weight:400;">[習慣化の言葉]</span>
    </div>
    <div style="margin-top:1.2rem; background:#fff9e6; border:2px solid #fbbf24; border-radius:10px; padding:12px 20px; max-width:640px; display:inline-block; text-align:left; font-size:19px;">
      ⚠️ [忘れがちな注意点]
    </div>
  </div>
  <div style="text-align:center; margin-top:1.6rem; font-size:19px; color:#444;">
    次回も、入試で差がつく重要ポイントを解説します。お楽しみに！
  </div>
  <div class="slide-footer"></div>
</section>
```


---

### SVG グラフ仕様

#### 座標変換（対数・指数グラフ）

```
svgX = origin_x + x * scale_x
svgY = origin_y - y * scale_y   ← SVG は y 軸が下向きなのでマイナス
```

例：`origin=(30,90)` `scale=(40,40)` のとき
- `x=1, y=0` → `(70, 90)`
- `x=2, y=log_(1/2)2=-1` → `(110, 130)`

#### SVG テンプレート（スライド②用 230×170）

```html
<svg width="230" height="170" style="flex-shrink:0; border:1px solid #d1d5db; border-radius:8px; background:#fafafa;">
  <defs>
    <marker id="ah" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#555"/>
    </marker>
    <clipPath id="cl1"><rect x="0" y="0" width="230" height="170"/></clipPath>
  </defs>
  <!-- 解の領域（緑）: 不等式の解を polygon で塗る -->
  <polygon points="..." fill="#bbf7d0" opacity="0.55" clip-path="url(#cl1)"/>
  <!-- 軸 -->
  <line x1="10" y1="[oy]" x2="225" y2="[oy]" stroke="#555" stroke-width="1.5" marker-end="url(#ah)"/>
  <line x1="[ox]" y1="165" x2="[ox]" y2="5" stroke="#555" stroke-width="1.5" marker-end="url(#ah)"/>
  <!-- 曲線（手計算で数点を polyline に）-->
  <polyline points="..." fill="none" stroke="#7C3AED" stroke-width="2.5" clip-path="url(#cl1)"/>
  <!-- 基準線（解の境界：赤破線）-->
  <line x1="10" y1="[svgY_border]" x2="225" y2="[svgY_border]" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="5,4"/>
  <!-- 境界点（紫塗り）-->
  <circle cx="[svgX_border]" cy="[svgY_border]" r="5" fill="#7C3AED"/>
  <!-- x=1 の目盛り点 -->
  <circle cx="[svgX_1]" cy="[oy]" r="4" fill="#555"/>
  <!-- ラベル -->
  <text x="216" y="[oy+4]" font-size="11" fill="#555">x</text>
  <text x="[ox+3]" y="10" font-size="11" fill="#555">y</text>
  <text x="[ox+4]" y="35" font-size="11" fill="#7C3AED" font-weight="bold">y=log₁/₂x</text>
  <text x="[領域内]" y="155" font-size="11" fill="#166534" font-weight="bold">解の領域</text>
</svg>
```

**注意点:**
- 複数 SVG が同じページにある場合、`id="ah"` `id="cl1"` は `ah2`, `cl2` のように連番にする
- スライド⑦（類題）は `width="210"` を使う（`ah2`, `cl2` で命名）
- 解の領域: 正解範囲は `fill="#bbf7d0"`（緑）、不正解範囲があれば `fill="#fecaca"`（赤）

---

## voice.md フォーマット仕様

**参照ファイル**: `problems/youtube_redesign/math2-10_log_inequality_voice.md`

### ファイル冒頭

```markdown
# 【音声台本】数学II｜単元名（テーマ一言）

対象スライド：math2-NN_slug.html
難易度：標準（偏差値55〜65）

※ 数式はAI音声読み上げ向けに日本語表記へ変換済み

---
```

### スライドセクションの構造

```markdown
## スライド①　フック

[台本本文：スライド内は空行なしで1段落にまとめる]
[最初の一言はフックワードまたは問いかけ（「今日は〜」NG）]

---

## スライド②　問題提示

[台本本文]

---
```

### 重要ルール

- **スライド内に空行（`\n\n`）を入れない**（長い間が生じる → PITFALLS.md 1-7）
- スライド間は `---` で区切る
- 数式は完全にひらがな・カタカナで読む（例：`log_(1/2)x` → `2分の1を底とする x の対数`）
- 挨拶なし・即フックワードで始める

### スライド⑦（類題）の特殊ルール

```markdown
## スライド⑦　類題

[問題文の読み上げ（ここまでが「問題パート」）]

[解答・解説（空行1つで区切る → ここから「解答パート」）]
[解答パートの内部にも空行を入れない]
```

空行の直前までが `slide_ruidai_hidden.png`（解答非表示）で表示される。

---

## _edit.md フォーマット仕様

**参照ファイル**: `problems/youtube_redesign/math2-10_log_inequality_edit.md`

### ファイル冒頭

```markdown
# 【編集指示】数学II｜単元名（テーマ一言）

対象スライド：math2-NN_slug.html
対象台本：math2-NN_slug_voice.md

---
```

### セクション① 追い装飾指示

```markdown
## ① 追い装飾指示

### [Slide①　フック]

**強調①**
- 強調対象：`[HTMLの実際のテキスト（LaTeXは $...$ 形式で残してよい）]`
- 方法：赤枠 / 丸枠 / アンダーライン / 矢印
- アニメーション：zoom / slide_up / fade
- タイミング：[音声台本テキスト（引用符「」なし）] または [XX%]
- 理由：[なぜここにアニメーションをかけるか]
```

### タイミング指定の選び方

| 指定方法 | 使う場面 |
|---|---|
| テキスト直書き | 台本に一意な文字列がある場合 |
| `XX%` | テキスト検索が誤爆しやすい・動画確認後の修正 |

```
% の計算: (発火タイムスタンプ - スライド開始) / スライド尺 × 100
例: (3:18 - 2:31) / 61秒 = 47/61 ≈ 77%
```

### セクション② グラフ設計メモ

```markdown
## ② グラフ設計メモ

- スライド②のSVG：y = [関数]（単調増加/減少）、解の領域（[範囲]）を緑シェード
- スライド⑦のSVG：y = [関数]、解の領域（[範囲]）を緑シェード
- 両グラフとも y = [境界値] の基準線を赤破線で表示
- 解の境界点に紫の点を明示
```

### YouTube メタデータのセクション順（固定）

```
### タイトル（推奨案 + 案2〜5）
### 説明欄（概要のみ・答えは書かない）
### タイムスタンプ（▼目次 形式・各行にキーワードを入れて視聴者向けに記述）
### タグ（各タグの先頭に `#` を付けてカンマ区切り）
### サムネイル案（3案、推奨案に「（推奨）」）
### 固定コメント案（問いかけ形式・高評価誘導あり）
```


---

## YouTube メタデータの書き方ルール

_edit.md の「YouTube メタデータ」セクションを書く際は以下に従う。

### セクションの順番（固定）

```
### タイトル
### 説明欄
### タイムスタンプ
### タグ
### サムネイル案
### 固定コメント案
```

タグは各タグの先頭に `#` を付けてカンマ区切りで書く（例: `#高校数学, #大学受験, #数学II`）。
説明欄にタグを混在させない。

---

### タイトル形式（確定フォーマット）

```
【数学X・単元名】反直感フック！具体的な手法・恩恵
```

**実績ある成功パターン（参考必須）：**

| 動画 | タイトル | 効いた要素 |
|------|---------|-----------|
| math2-08（12回/1日） | 【数学II・解と係数の関係】解の公式は使わない！係数だけで式の値を瞬殺する | 公式否定フック＋「瞬殺」の速さ訴求 |
| 3-2（CTR 33.3%） | 【部分積分】∫eˣsinx dx｜2回やると元に戻る！移項で解く発展テクニック | 「元に戻る」という驚き＋テクニック名 |

**タイトルのルール：**
- `【数学II・単元名】` の形式は必ず守る（検索性のため）
- フックは「！」で締める（例：「使わない！」「元に戻る！」「爆死する！」）
- 恩恵は具体的な動詞で（「瞬殺」「一発解決」「マスター」など）
- LaTeX・数式記号は使わない。数式が必要なら Unicode か言葉で代替
- タイトルは70文字以内

**フックのパターン例：**
```
○○は使わない！△△だけで瞬殺する
○○すると元に戻る！移項で一発解決
○○を忘れると爆死する！正しい手順を解説
○○だけ見ても間違える！△△まで確認する
```

---

### サムネイル（確定フォーマット）

**成功パターンの構成：**
- **メインコピー**：フックワード（「爆死」「使わない」「元に戻る」など）を大きく
- **サブコピー**：単元名 or 「増減表だけでは不十分」など補足
- **数式表示**：具体的な式や答えを1行（例：`f(4)=16 を見落とすな`）
- **配色**：深緑 or 深青の背景・白文字・赤アクセント（正解対比）

**効果的な要素：**

| 要素 | 効果 | 具体例 |
|------|------|--------|
| 落とし穴ワード | 「自分も間違えたかも」と感じさせる | 「爆死」「0点」「見落とし」 |
| 正解との対比 | 「正しい答えが気になる」 | ❌0 → ✅8/3 |
| 具体的な数式 | 「この問題知ってる」と感じさせる | `∫₀³(x²−2x)dx = 0？` |

---

### 説明欄

- **概要・導入のみ**。何を学べるかを一言で示す程度にとどめる
- 解法・計算過程・答えは書かない（動画を見る動機を損なうため）
- LaTeX 不可。数式は Unicode か言葉で書く

---

### 固定コメント

- **問いかけ形式**で視聴者の思考を促す（「このとき最初に何と答えましたか？」）
- 解答・ヒントは一切書かない
- 「間違えた経験がある方はコメントで」と巻き込む一言を入れる
- 最後に高評価・チャンネル登録への誘導を入れる

---

## 動画品質の指針（ユーザー指示）

### 音声・スライド切り替えのテンポ
- スライド切り替え前後のセリフの**間隔が狭すぎる**場合は voice.md を修正する
  （各スライドの台本の文末に「。」で終わる文を置き、次スライドの頭も間を感じさせる書き出しにする）
- **ターゲット層は10代**。スライド①（フック）の音声は特に**テンポを速く**する。
  冒頭の無音・間は最小限にし、最初のスライドでの発話間隔は他のスライドより短めに設定する。
  voice.md のスライド①は文を短く区切り、テンポよく畳みかけるリズムで書く。

### 類題の解説
- 類題の解説は**簡潔すぎず**、計算の流れを一つひとつ丁寧に読み上げる量にする
- 極値・端点の代入値など、数値の確認をひとステップずつ声に出す

### 図・グラフの追加
- 文章だけでわかりにくい場合、**スライドの余白に図・グラフを配置**する
- HTML の `<svg>` インラインまたは Python (matplotlib) で静止画を生成して埋め込む方法が使える
- 必要性の判断は Claude が主体的に行い、適切と判断した場合は追加する

### 動画構成（YouTube Studio 分析に基づく改定方針）
- **フックスライド**：冒頭 15〜20 秒で「落とし穴の正体」を先にチラ見せして離脱を防ぐ
- **まとめスライド**：類題の後・アウトロの前に一言まとめを入れ、視聴維持率を改善する
- **サムネイル**：単元名だけでなく「〇〇すると爆死」系の落とし穴ワードと正解の対比を使う
- ※ math2-04 で試験実装済み。効果確認後に他の単元へ横展開する

---

## CTR・視聴維持率の戦略的アップデート（2026-04-29 確定）

以下の3点を **新作すべてに適用する**こと（既存フォーマットへの上乗せ）。

### 1. CTR最大化：サムネイルと冒頭1行の連動

- サムネイルで使う**強いワード**（「逆転」「爆死」「逆向き」など）を、
  Leda の**最初の一言に必ず採用**する。
- タイトルのフックワードも同じワードで統一し、サムネ→タイトル→台本冒頭が一貫する。
- ターゲットは「単元名の勉強」ではなく「模試直前の受験生の具体的な悩み」。
  例：「模試で答えが正反対になった」「時間が足りなかった」

### 2. 「京大生視点」の鋭利化

- 「よくある間違い」スライドで **「真面目に勉強した人ほどハマる」** という逆説フックを使う。
- 解説の冒頭に **「この解法を知れば試験で○分浮く」** など数値化した恩恵を提示する。
  例：「底の確認は2秒。ここを飛ばすと答えが丸ごと逆になる」
- 非効率な解法を先に示し、「効率的な正解」との対比で理解を深める。

### 3. 視聴維持率：冒頭15秒の密度

- **挨拶は完全に排除する**。Leda の最初の一言は「問いかけ」または「誤答の指摘」で始める。
  NG 例：「今日は〜について解説します」
  OK 例：「x が2より大きいと答えた方、要注意です」
- フックスライド（①）は誤答と正解の対比ボックスを横並びで配置し、
  「なぜ逆なのか」が15秒以内に伝わる視覚レイアウトにする。
- voice.md のスライド①はフックワードで始まる短い問いかけ文から入ること。

### 需要単元の選び方（4〜6月 模試直前期）

- 全統模試で頻出かつ **「底の確認忘れ」「符号ミス」「端点見落とし」** 等の典型ミスがある単元を優先
- 既存動画でカバーしていない盲点を選ぶ（重複厳禁）
- 検索クエリに「逆」「なぜ」「間違い」「爆死」が付きやすい単元ほど CTR が高い
- 実装済み例：対数不等式の不等号逆転（math2-10）

---

## ファイル命名規則

動画番号は **必ず2桁ゼロパディング** で統一する。

| NG | OK |
|---|---|
| `math2-1_vieta.html` | `math2-01_vieta.html` |
| `math2-9_integral_area.html` | `math2-09_integral_area.html` |

- 対象: `.html` / `_voice.md` / `_edit.md` / `output/*.mp4` / `output/*/` キャッシュディレクトリ
- リネーム手順: `git mv` でファイル移動 → `sed` でファイル内参照も更新
  ```bash
  # ファイル名のリネーム
  sed -i 's/\(math[^-]*-\)\([1-9]\)_/\10\2_/g' <対象ファイル>
  # 非アンダースコア区切り参照（コメント・スクリプト内など）
  sed -i 's/\(math[^-]*-\)\([1-9]\)\([^0-9_]\)/\10\2\3/g' <対象ファイル>
  ```
- `math2-10_` のように既に2桁の番号には影響しない（`10_` はパターンに一致しない）

---

## サムネイル生成（make_thumbnails.py）

### VS レイアウト（地獄 vs 天国）

`make_thumbnail_vs(stem, config)` で左右対比レイアウトのサムネイルを生成する。

**使用場面：**「正誤対比」「誤答 → 正解」の落とし穴系動画（最もCTRが高い）

**config キー一覧：**

| キー | 内容 |
|---|---|
| `bg_color` | 背景RGB（例: `(14, 6, 30)` 深紫） |
| `accent` | アクセント色RGB |
| `subject_tag` | 上部バッジ（`数学II・対数不等式`） |
| `badge_text` | 上部バッジ右の短テキスト（`模試頻出の罠`） |
| `top_copy` | 最上部大コピー（**10文字以内**） |
| `hell_label` | 左ボックスラベル（`よくある誤答`） |
| `hell_value` | 左ボックスメイン値（`x > 2`） |
| `hell_note` | 左ボックス補足（`底を確認しないと…`） |
| `heaven_label` | 右ボックスラベル（`正しい答え`） |
| `heaven_value` | 右ボックスメイン値（`0 < x < 2`） |
| `heaven_note` | 右ボックス補足（`底 1/2 → 不等号逆転`） |
| `bottom_copy` | 下部小テキスト（問題式と説明） |

`VS_THUMBNAILS` dict に追加して `__main__` ブロックで自動処理される。

### CTR サムネイル 3ルール（ユーザー確定方針）

1. **視覚的対比（地獄 vs 天国）**: 誤答（赤・暗）と正解（緑・明）を左右に並べる。アイコンは PIL で直描画（❌/✅ 絵文字不可 → PITFALLS.md 9-1）
2. **煽るコピーライティング**: `top_copy` は10文字以内の強いワード（「不等号が逆転！」「爆死する罠！」など）。モバイル3秒で読める量
3. **モバイル最適化**: 文字は大きく・少なく。`bottom_copy` の数式も ASCII で書く（`log(1/2)` 等。下付き Unicode 不可 → PITFALLS.md 9-1）

---

## ミスポイント集

`PITFALLS.md` を参照。動画生成スクリプト起動時に自動表示される。
