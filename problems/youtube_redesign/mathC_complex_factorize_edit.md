# 【編集指示】数学C｜複素数の絶対値の最大値（因数分解で一瞬）

対象スライド：mathC_complex_factorize.html
対象台本：mathC_complex_factorize_voice.md

---

## ① 追い装飾指示

### [Slide②　ヒント]

**強調①**
- 強調対象：`絶対値の積の性質：$|z^2-1| = |z-1|\cdot|z+1|$`
- 方法：黄色ハイライト
- アニメーション：slide_up
- タイミング：「絶対値の積の性質より、z の2乗 マイナス 1 の絶対値 イコール z マイナス 1 の絶対値 かける z プラス 1 の絶対値。」
- 理由：因数分解と絶対値の積が結びつく核心変形を際立たせる

**強調②**
- 強調対象：`→ 後は $|z+1|$（$z$ から点 $-1$ までの距離）の最大値を考えるだけ。`
- 方法：赤枠
- アニメーション：fade
- タイミング：「代入すると z の2乗 マイナス 1 の絶対値 イコール z プラス 1 の絶対値 になります。」
- 理由：問題が大幅に簡略化されたことをこのタイミングで印象づける

---

### [Slide③　本質ポイント]

**強調①**
- 強調対象：`→ 円上の点から $(-1, 0)$ への最大距離を求める！`
- 方法：赤枠
- アニメーション：zoom
- タイミング：「つまり、この円上の点から マイナス1コンマ0 への最大距離を求めればいい。」
- 理由：抽象的な複素数問題が幾何的な距離問題に変換されたことを強調する

---

## ② グラフ設計

- 目的：|z−1|=1 の円と点 (−1, 0) の位置関係・最大距離を視覚化
- 関数：円 |z−1|=1（中心 (1, 0)、半径 1）
- 強調ポイント：点 (−1, 0)、最大距離点 z = 2、両点間の距離線（長さ 3）
- 使用スライド：③④

---

## ③ Pythonコード

ファイル名：`graph_complex_circle.png`

```python
import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7, 7))

theta = np.linspace(0, 2*np.pi, 400)
cx, cy, r = 1, 0, 1
ax.plot(cx + r*np.cos(theta), cy + r*np.sin(theta),
        'b-', linewidth=2, label='|z - 1| = 1')
ax.plot(cx, cy, 'b+', markersize=12, markeredgewidth=2)

ax.plot(-1, 0, 'rs', markersize=11, label='(-1, 0)')
ax.annotate('(-1, 0)', xy=(-1, 0), xytext=(-1.6, 0.25), fontsize=11)

ax.plot(2, 0, 'go', markersize=11, label='z = 2  (max)')
ax.annotate('z = 2', xy=(2, 0), xytext=(2.1, 0.2), fontsize=11)

ax.annotate('', xy=(2, 0), xytext=(-1, 0),
            arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
ax.text(0.4, -0.2, 'distance = 3', color='green', fontsize=11)

ax.set_xlim(-2.5, 3.5)
ax.set_ylim(-2, 2)
ax.set_aspect('equal')
ax.axhline(0, color='k', linewidth=0.5)
ax.axvline(0, color='k', linewidth=0.5)
ax.grid(True, alpha=0.4)
ax.set_xlabel('Re', fontsize=12)
ax.set_ylabel('Im', fontsize=12)
ax.set_title('Complex plane: max |z+1| on circle |z-1|=1', fontsize=12)
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig('graph_complex_circle.png', dpi=150)
plt.close()
```

---

## ④ サムネ案

- テキスト：「因数分解で一瞬！」
- 構図：左に `|z²−1|`、中央に `=(因数分解)` 矢印、右に `= |z+1|` と答え `= 3`、背景はピンク〜紫
- 狙い：「直接計算しようとして計算地獄に陥った」人が「そんな方法があるのか」と感じる
