# 【編集指示】数学III｜定積分（三角置換の発展）

対象スライド：math3_integral_squared.html
対象台本：math3_integral_squared_voice.md

---

## ① 追い装飾指示

### [Slide②　ヒント]

**強調①**
- 強調対象：`積分範囲：$x: 0 \to 1$ のとき $\theta: 0 \to \dfrac{\pi}{4}$`
- 方法：黄色ハイライト
- アニメーション：fade
- タイミング：「積分範囲は x が 0 のとき θ イコール 0、x が 1 のとき θ イコール 4分のπ。」
- 理由：置換時の積分範囲変換を忘れる典型ミスを防ぐ

**強調②**
- 強調対象：`$x = \tan\theta$ とおくと $1 + x^2 = 1 + \tan^2\theta = \dfrac{1}{\cos^2\theta}$`
- 方法：赤枠
- アニメーション：zoom
- タイミング：「1 プラス xの2乗 イコール コサイン2乗θ分の1 になります。」
- 理由：置換によってどう変形されるかの核心式を際立たせる

---

### [Slide③　本質ポイント]

**強調①**
- 強調対象：`→ 半角公式で積分できる形に変換完了！`
- 方法：黄色ハイライト
- アニメーション：slide_up
- タイミング：「あ、きれいに化けましたね。分母の2乗が消えて、コサイン2乗θ の積分になります。」
- 理由：「変換完了」という達成感のタイミングで視覚強調する

---

## ② グラフ設計

- 目的：被積分関数の形と積分範囲を視覚化する
- 関数：y = 1/(1+x²)²
- 強調ポイント：x = 0〜1 の面積をシェード、x = 1 に縦線
- 使用スライド：①②

---

## ③ Pythonコード

ファイル名：`graph_integral_squared.png`

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 2.5, 400)
y = 1 / (1 + x**2)**2

x_fill = np.linspace(0, 1, 200)
y_fill = 1 / (1 + x_fill**2)**2

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x, y, 'b-', linewidth=2, label='y = 1/(1+x^2)^2')
ax.fill_between(x_fill, y_fill, alpha=0.4, color='blue',
                label='integral area (0 to 1)')
ax.axvline(1, color='r', linestyle='--', linewidth=1.2, label='x = 1')
ax.axvline(0, color='k', linewidth=0.8)
ax.set_xlabel('x', fontsize=12)
ax.set_ylabel('y', fontsize=12)
ax.set_title('y = 1 / (1 + x^2)^2', fontsize=13)
ax.set_xlim(-0.1, 2.5)
ax.set_ylim(-0.05, 1.1)
ax.grid(True, alpha=0.4)
ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig('graph_integral_squared.png', dpi=150)
plt.close()
```

---

## ④ サムネ案

- テキスト：「tanθ置換で一撃」
- 構図：左に `∫1/(1+x²)²dx` を大きく、右に `= π/8 + 1/4` を強調色で、背景は濃いオレンジ
- 狙い：数III の積分で詰まっている人が「一撃で解ける？」と思いクリックする
