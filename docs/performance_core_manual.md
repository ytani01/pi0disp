# マニュアル: `performance_core` と関連ユーティリティ

## 概要
このドキュメントは、`pi0disp` ライブラリのパフォーマンス最適化の中核を担う `performance_core.ColorConverter` クラスと、それに関連する `utils` モジュールの便利な関数について解説します。これらのツールは、特にリソースが限られた Raspberry Pi 環境において、高速かつ効率的な描画を実現するために不可欠です。

---

## 1. `performance_core.ColorConverter` クラス
### 目的
RGB 形式のピクセルデータを、ST7789V ディスプレイがネイティブに扱う **RGB565** 形式のバイト列に高速に変換します。

### 主な機能
- **高速変換**: `NumPy` を利用したルックアップテーブル (LUT) により、Python のループ処理を回避し、C言語レベルの速度で色変換を実行します。
- **ガンマ補正**: ディスプレイの特性に合わせて画像の明るさを補正するガンマ補正機能を提供します。

### `ColorConverter` API
- `__init__(gamma=2.2)`: コンバータを初期化します。
- `set_gamma(gamma)`: ガンマ値を動的に変更します。
- `convert(rgb_array, apply_gamma=False)`: `NumPy` 配列 (RGB) を `bytes` (RGB565) に変換します。

---

## 2. `performance_core.RegionOptimizer` クラス
### 目的
複数の「汚れ」領域（Dirty Rectangles）を、オーバーラップや近接度合いに基づいてマージし、SPI 転送の回数を最小限に抑えます。

### 主な機能
- **領域マージ**: `merge_regions(regions, area_threshold=1.5)` メソッドにより、指定された矩形リスト `(x, y, w, h)` を最適化された少ない数の矩形に統合します。

---

## 3. `utils` モジュールの関連関数
### `pil_to_rgb565_bytes(img, apply_gamma=False)`
- **目的**: PIL (Pillow) の `Image` オブジェクトを直接 RGB565 のバイト列に変換します。内部で `ColorConverter` を利用しており、最も手軽で推奨される変換方法です。

### `merge_bboxes(bbox1, bbox2)`
- **目的**: 2つのバウンディングボックス（矩形領域）を、両方を包含する１つの大きなボックスに結合します。Dirty Rectangle（差分更新）処理で、複数の小さな更新領域をまとめて効率化する際に使用します。

### `clamp_region(region, width, height)`
- **目的**: 領域の座標が画面の物理的な境界（`width`, `height`）内に収まるように制限（クランプ）します。これにより、範囲外描画によるエラーを防ぎます。

---

## 3. 実用サンプルコード
これらの機能を使用した、より実践的なサンプルコードが `samples/` ディレクトリに用意されています。コードを読むことで、実際のアプリケーションでどのようにこれらのユーティリティを活用するかの理解が深まります。

- **[samples/sample_perf_core.py](https://github.com/your_repo/your_project/blob/develop/samples/sample_perf_core.py)**
  - このサンプルは、本マニュアルで解説した `ColorConverter`、`pil_to_rgb565_bytes`、`merge_bboxes`、`clamp_region` のすべての機能について、具体的な使い方を示しています。

リポジトリのパス `your_repo/your_project` の部分は、実際のプロジェクトのパスに置き換えてください。

---
作成日: 2026-01-09
最終更新日: 2026-01-09
