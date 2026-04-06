# StudyList — 数学スライド問題集

高校数学の問題をスライド形式で学習できるWebアプリです。
各ページはブラウザで直接開けるほか、PDF保存ボタンで印刷用PDFを出力できます。

---

## 問題一覧

### 数学I

| 難易度 | タイトル | URL |
|--------|---------|-----|
| 中級 | 二次不等式（連立不等式と整数解） | https://kazumahattori1131-del.github.io/StudyList/problems/math1/medium/quadratic_inequality.html |
| 中級 | 二次関数の最小値（パラメータ場合分け） | https://kazumahattori1131-del.github.io/StudyList/problems/math1/medium/quadratic_min_max_param.html |
| 発展 | 二次関数の最大・最小（軸の移動） | https://kazumahattori1131-del.github.io/StudyList/problems/math1/hard/quadratic_minmax_axis.html |

### 数学II

| 難易度 | タイトル | URL |
|--------|---------|-----|
| 中級 | 指数方程式（置換テクニック） | https://kazumahattori1131-del.github.io/StudyList/problems/math2/medium/exponential_equation.html |
| 中級 | 対数方程式（真数条件の確認） | https://kazumahattori1131-del.github.io/StudyList/problems/math2/medium/logarithmic_equation.html |
| 発展 | 接線と曲線が囲む面積 | https://kazumahattori1131-del.github.io/StudyList/problems/math2/hard/tangent_area.html |

### 数学III

| 難易度 | タイトル | URL |
|--------|---------|-----|
| 中級 | 置換積分法（基本テクニック） | https://kazumahattori1131-del.github.io/StudyList/problems/math3/medium/substitution_integral.html |
| 中級 | 定積分（部分積分法） | https://kazumahattori1131-del.github.io/StudyList/problems/math3/medium/integration_by_parts.html |
| 発展 | 三角置換による定積分 | https://kazumahattori1131-del.github.io/StudyList/problems/math3/hard/trig_substitution.html |

### 数学A

| 難易度 | タイトル | URL |
|--------|---------|-----|
| 中級 | 組合せ（余事象の利用） | https://kazumahattori1131-del.github.io/StudyList/problems/mathA/medium/combination_count.html |
| 中級 | 条件付き確率と余事象の融合 | https://kazumahattori1131-del.github.io/StudyList/problems/mathA/medium/probability_conditional.html |
| 発展 | 整数の性質・不定方程式 | https://kazumahattori1131-del.github.io/StudyList/problems/mathA/hard/diophantine_equation.html |

### 数学B

| 難易度 | タイトル | URL |
|--------|---------|-----|
| 中級 | 等差数列の和（和が初めてN超える項） | https://kazumahattori1131-del.github.io/StudyList/problems/mathB/medium/arithmetic_series.html |
| 中級 | 漸化式（特性方程式による解法） | https://kazumahattori1131-del.github.io/StudyList/problems/mathB/medium/recurrence_relation.html |
| 発展 | 数学的帰納法（Σk·2^k の証明） | https://kazumahattori1131-del.github.io/StudyList/problems/mathB/hard/induction_sum.html |

### 数学C

| 難易度 | タイトル | URL |
|--------|---------|-----|
| 中級 | 楕円と直線の接線 | https://kazumahattori1131-del.github.io/StudyList/problems/mathC/medium/conic_tangent.html |
| 中級 | ベクトルの内積と垂線の足 | https://kazumahattori1131-del.github.io/StudyList/problems/mathC/medium/vector_inner_product.html |
| 発展 | ド・モアブルの定理と三角関数の多倍角公式 | https://kazumahattori1131-del.github.io/StudyList/problems/mathC/hard/de_moivre_theorem.html |

### 融合問題（単元横断）

| 難易度 | タイトル | URL |
|--------|---------|-----|
| 発展 | 確率漸化式（数学A×B） | https://kazumahattori1131-del.github.io/StudyList/problems/cross/probability_recurrence.html |
| 発展 | 三角関数と積分・面積（数学II） | https://kazumahattori1131-del.github.io/StudyList/problems/cross/trig_integral_area.html |

---

## 開発メモ

新しい HTML ファイルを追加するときは、以下を必ず行うこと：

1. HTML ファイル内の `<body>` 直後にURLコメントを記載する
   ```html
   <!--
   https://kazumahattori1131-del.github.io/StudyList/problems/SUBJECT/LEVEL/FILENAME.html
   -->
   ```
2. この README の問題一覧テーブルに行を追加する
