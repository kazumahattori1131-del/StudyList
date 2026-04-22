# 【編集指示】数学I｜放物線とx軸の交点条件（判別式）

対象スライド：math1_quadratic_discriminant.html
対象台本：math1_quadratic_discriminant_voice.md

---

## ① 追い装飾指示

### [Slide②　よくある間違い]

**強調①**
- 強調対象：`$D > 0$（等号なし）`
- 方法：赤枠
- アニメーション：zoom
- タイミング：「つまり、「2点で交わる」は D が 0より大きい、等号なし、です。」
- 理由：最頻出ミスの核心（等号の有無）を目で見せる

**強調②**
- 強調対象：`$D = 0$：接する（1点のみ）`
- 方法：黄色ハイライト
- アニメーション：fade
- タイミング：「D がゼロのとき。これは「接する」、1点でギリギリ触れるだけ。」
- 理由：等号なしの根拠を対比で示す

---

### [Slide③　本質ポイント]

**強調①**
- 強調対象：`→ $a$ の2次不等式として因数分解して解く`
- 方法：黄色ハイライト
- アニメーション：slide_up
- タイミング：「aの2乗 マイナス a マイナス 2 が 0より大きい、この不等式を解けばいい。」
- 理由：指数ではなく「不等式として解く」方向転換を強調

---

### [Slide④　解説]

**強調①**
- 強調対象：`$$a < -1 \quad \text{または} \quad a > 2$$`
- 方法：赤枠
- アニメーション：zoom
- タイミング：「これが答えです。」
- 理由：最終答えを明確に視覚定着させる

---

## ② グラフ設計

- 目的：D/4 = a²−a−2 > 0 の解の範囲を視覚化する
- 関数：y = a² − a − 2
- 強調ポイント：根 a = −1, a = 2、y > 0 の領域（緑シェード）、y ≤ 0 の領域（赤シェード）
- 使用スライド：③④

---

## ③ Pythonコード

ファイル名：`graph_discriminant_condition.png`

```python
import numpy as np
import matplotlib.pyplot as plt

a = np.linspace(-2.5, 3.5, 400)
y = a**2 - a - 2

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(a, y, 'b-', linewidth=2)
ax.axhline(0, color='k', linewidth=0.8)
ax.fill_between(a, y, 0, where=(y > 0), alpha=0.25, color='green', label='y > 0')
ax.fill_between(a, y, 0, where=(y <= 0), alpha=0.15, color='red', label='y <= 0')
ax.plot([-1, 2], [0, 0], 'ro', markersize=9, zorder=5)
ax.annotate('a = -1', xy=(-1, 0), xytext=(-2.0, 1.8), fontsize=11,
            arrowprops=dict(arrowstyle='->', color='gray'))
ax.annotate('a = 2', xy=(2, 0), xytext=(2.4, 1.8), fontsize=11,
            arrowprops=dict(arrowstyle='->', color='gray'))
ax.set_xlabel('a', fontsize=12)
ax.set_ylabel('y', fontsize=12)
ax.set_title('y = a^2 - a - 2  (D/4 condition)', fontsize=13)
ax.grid(True, alpha=0.4)
ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig('graph_discriminant_condition.png', dpi=150)
plt.close()
```

---

## ④ サムネ案

- テキスト：「等号なし！」
- 構図：左に `D > 0` を大きく、右に ❌ `D ≥ 0` をバツ印付き、背景はオレンジ
- 狙い：「≧0 じゃないの？」と思っている視聴者が思わずタップする
