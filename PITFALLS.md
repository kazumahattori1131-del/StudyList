# 動画制作 ミスポイント集

音声・スライド・動画生成で繰り返し発生したバグと対策をまとめる。
新しいミスが見つかったらここに追記すること。

---

## 1. 音声台本（_voice.md）

### 1-1. 類題スライドの分割構造

`split_ruidai_script()` は **最初の空行（`\n\n`）** で台本を2分割する。
- 空行より前 → 問題提示（解答非表示）
- 空行より後 → 解説（解答表示）

**NG：** 問題文を2段落目に書く（解説側に入ってしまう）
```
では類題です。          ← ここだけ problem になる

nを正の整数として...    ← solution 側に入り、解答が見えた状態で読まれる
```

**OK：** 問題文を問題パート内に1段落でまとめる
```
では類題を解いてみましょう。
nを正の整数として...    ← 問題文もここに含める（改行はOK、空行はNG）

今度の公比は3なので...   ← ここから解説（空行で区切る）
```

コードが自動で `\nでは一度、自分で解いてみてください。` を末尾に付加するので、
voice.md には「考えてみてください」系の文を書かなくてよい。

---

### 1-2. 変数名の読み仮名

類題で使う変数がHTMLと一致しているか確認する。

| 状況 | NG | OK |
|---|---|---|
| HTMLが $T$ を使っているのに | 「エスと3エスを並べて」 | 「ティーと3ティーを並べて」 |

### 1-3. 助数詞の表記

normalize_for_tts() で変換されるが、voice.md 側も正しく書いておく。

| NG | OK |
|---|---|
| 二つ / 2つ | ふたつ |
| 三つ / 3つ | みっつ |
| 1問 | いちもん（「問」→「もん」は自動変換） |

### 1-4. 省略記号の書き方

voice.md では `…` を使わず、明示的に書く。
normalize_for_tts() で変換されるが、voice.md に直書きする方が確実。

| NG | OK |
|---|---|
| `3の1乗＋…＋3のn乗` | `3の1乗プラスてんてんてんプラス3のn乗` |

---

## 2. normalize_for_tts()（slide_to_video.py）

### 2-1. 省略記号の正規表現

character class `[プラス]` は「プ」「ラ」「ス」の**1文字ずつ**にマッチする（単語ではない）。

**NG:**
```python
re.sub(r'[…][\s　]*[プラス＋+]', 'てんてんてんプラス', text)
```

**OK:**
```python
re.sub(r'[…](?:\s*(?:プラス|[＋+]))', 'てんてんてんプラス', text)
```

### 2-2. 助数詞変換は数字変換より先に行う

`('2つ', 'ふたつ')` の置換を先に行わないと、先に `2` → `に` に変換されて `につ` になる。

### 2-3. 正規表現の負の先読みで「正し（い/く）」を除外する

`正(?!し)` だと「正しい」も「正しく」も除外されず「せいしい」と読まれる。
`正(?!し|式|規|確|解|直|午|月|論|比|弦|接|反|逆|面|答|法)` のように `し` を1文字だけ
負の先読みに入れれば「正し…」系は全て除外される。

---

## 3. Gemini TTS API

### 3-1. system_instruction は TTS モデル非対応

`system_instruction` を渡すと、モデルがテキスト生成しようとして **500 INTERNAL** または
**400 INVALID_ARGUMENT（"Model tried to generate text"）** が返る。

**NG:**
```python
config=genai_types.GenerateContentConfig(
    system_instruction="...",       # ← これが原因
    response_modalities=['AUDIO'],
    ...
)
```

**OK:** `system_instruction` を削除し、`response_modalities=['AUDIO']` のみ指定する。

### 3-2. 500 エラーはリトライ対象に含める

デフォルトでは 429/503 のみリトライしていたが、Gemini TTS は 500 も返すことがある。
`'500' in err or 'INTERNAL' in err` も条件に追加する。

### 3-3. 短すぎるテキストで 400 エラーが出ることがある

1文字だけ（例: 「テスト」）送るとエラーになる場合がある。
テスト時は2文以上（「テスト。これはテストです。」）を使う。

---

## 4. Cloud TTS API（フォールバック用）

### 4-1. Chirp3-HD-Leda は pitch パラメータ非対応

`pitch: -1.5` などを audioConfig に含めると **400 Bad Request** が返る。
`speakingRate` のみ使用可。

### 4-2. DNS cache overflow（503）は一時的なもの

`texttospeech.googleapis.com` が 503 "DNS cache overflow" を返すことがある。
リトライで解決する。恒久的な問題ではない。

---

## 5. HTML スライド

### 5-1. color-mix() は Playwright Chromium で未サポートの場合がある

`color-mix(in srgb, ...)` が動かず背景が暗くなる。
`@supports` を使ってフォールバック色を必ず書く。

```css
.problem-box { background: #fff6ef; }   /* フォールバック */
@supports (color: color-mix(in srgb, red 8%, white)) {
  .problem-box { background: color-mix(in srgb, var(--accent) 8%, white); }
}
```

### 5-2. 暗背景ボックスのテキスト色を必ず指定する

`.key-box` など `background: #1c1008` のような暗い背景には `color: #fff` を必ず付ける。
未指定だと継承色（黒）になり、文字が見えなくなる。

### 5-3. KaTeX の \phantom で数式の縦揃えを行う

差し引き法の $2S$ の行を $S$ と揃えるには `\phantom{}` を使う。

```html
$2S = \phantom{1{\cdot}2^1 + {}} 1{\cdot}2^2 + \cdots$
```

---

## 6. 動画エンコード

### 6-1. QuickTime Player は yuv420p が必要

ffmpeg のデフォルト（yuv444p 等）は QuickTime で再生できない。
`write_videofile()` には必ず以下を渡す。

```python
ffmpeg_params=['-pix_fmt', 'yuv420p', '-movflags', '+faststart']
```

---

## 7. 台本チェックリスト（新規動画作成時）

新しい動画の voice.md を書き終えたら、以下を確認する。

- [ ] スライド⑥（類題）の問題部分と解説部分が **空行1行** で正しく区切られているか
- [ ] 類題の変数名が HTML の変数名と一致しているか（S / T / など）
- [ ] 助数詞が ふたつ / みっつ で書かれているか（2つ / 三つ は使わない）
- [ ] 「+…+」を「プラスてんてんてんプラス」と書いているか
- [ ] 暗背景ボックスに `color: #fff` が付いているか
- [ ] `@supports` フォールバックが CSS に書かれているか
- [ ] `write_videofile()` に `-pix_fmt yuv420p` が渡されているか（slide_to_video.py 側）
