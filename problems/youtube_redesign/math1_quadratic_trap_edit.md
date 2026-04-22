# 【編集指示】数学I｜二次不等式の恒等的成立（落とし穴）

対象スライド：math1_quadratic_trap.html
対象台本：math1_quadratic_trap_voice.md

---

## ① 追い装飾指示

### [Slide②　よくある間違い]

**強調①**
- 強調対象：`→ $a < -1$ を含めてしまっている！`
- 方法：赤枠
- アニメーション：zoom
- タイミング：「「これで完成」と思った人、少し待ってください。」
- 理由：よくある間違い答案の核心を視覚的に否定する

**強調②**
- 強調対象：`放物線が下に開くので、どこかで必ず $x$ 軸より下になる。`
- 方法：黄色ハイライト
- アニメーション：fade
- タイミング：「…下に開いた放物線ですね。x を大きくしていくと、必ず 0より小さくなります。」
- 理由：なぜ a < −1 が不適かの根拠を印象づける

---

### [Slide③　本質ポイント]

**強調①**
- 強調対象：`① $a > 0$（上に開く）`
- 方法：黄色ハイライト
- アニメーション：slide_up
- タイミング：「1つ目。上に開いていること。a が 0より大きい こと。」
- 理由：見落とされやすい条件①を単独で強調

**強調②**
- 強調対象：`この2条件の共通部分が答え。`
- 方法：赤枠
- アニメーション：fade
- タイミング：「2つの条件、セットで確認する。これが鉄則です。」
- 理由：「片方だけ見る」という落とし穴に対する解答を強調

---

## ② グラフ設計

- 目的：a < 0 のとき常に正になれない理由を視覚化
- 関数①：f(x) = −2x² + 2x − 2（a = −2、下に開く）
- 関数②：f(x) = 2x² + 2x + 2（a = 2、上に開く・x軸に交わらない）
- 強調ポイント：f₁が x 軸を下回る領域（赤シェード）、f₂が常に正（緑シェード）
- 使用スライド：②③

---

## ③ Pythonコード

ファイル名：`graph_always_positive.png`

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(-3, 3, 400)
f1 = -2*x**2 + 2*x - 2
f2 = 2*x**2 + 2*x + 2

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x, f1, 'r-', linewidth=2, label='a=-2  (opens down, NOT always > 0)')
ax.plot(x, f2, 'g-', linewidth=2, label='a=2   (opens up, always > 0)')
ax.axhline(0, color='k', linewidth=1)
ax.fill_between(x, f1, 0, where=(f1 < 0), alpha=0.2, color='red')
ax.fill_between(x, f2, 0, where=(f2 > 0), alpha=0.15, color='green')
ax.set_ylim(-10, 12)
ax.set_xlabel('x', fontsize=12)
ax.set_ylabel('f(x)', fontsize=12)
ax.set_title('f(x) = ax^2 + 2x + a', fontsize=13)
ax.grid(True, alpha=0.4)
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig('graph_always_positive.png', dpi=150)
plt.close()
```

---

## ④ サムネ案

- テキスト：「aの符号を忘れた？」
- 構図：左に下に開く放物線（赤）、右に「a > 0 必須」を太字で、背景は白〜薄赤グラデーション
- 狙い：「D < 0 だけ解いた」経験がある人が「あ、これだ」と反応する
