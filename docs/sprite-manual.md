# Sprite システム利用マニュアル

`pi0disp` では、効率的なアニメーションや動的な UI 要素を実装するための共通基盤として `Sprite` システムを提供しています。

---

## そもそも Sprite (スプライト) とは？

コンピュータグラフィックスにおける **Sprite (スプライト)** とは、背景とは独立して画面上を動き回る、小さな図形やキャラクター画像などのオブジェクトを指します。

`pi0disp` の `Sprite` クラスを利用することで、以下のメリットが得られます：
- **位置管理の共通化**: すべての動く要素を `x`, `y` 座標で統一的に扱えます。
- **効率的な描画**: 変化があったスプライトの周囲だけを部分更新（Dirty Rectangle 最適化）することで、CPU 負荷を抑えつつ高い FPS を維持できます。
- **オブジェクト指向**: キャラクター、弾丸、UIパーツなどを個別のクラスとして定義し、メインループで一括管理できます。

---

## 目次
1. [設計思想と基本概念](#設計思想と基本概念)
    - [__slots__ による高速化](#__slots__-による高速化)
    - [Dirty Rectangle (差分更新) の仕組み](#dirty-rectangle-差分更新-の仕組み)
2. [クラスリファレンス](#クラスリファレンス)
3. [カスタムスプライトの実装例](#カスタムスプライトの実装例)
4. [メインループへの組み込み](#メインループへの組み込み)

---

## 設計思想と基本概念

### なぜ抽象クラスなのか
`Sprite` クラスは `abc.ABC` を継承した**抽象基底クラス**として設計されています。
これは、`Sprite` 自体は「座標管理」や「差分検知」といった共通ロジックのみを担当し、具体的な「描画（色や形）」は継承先のサブクラスに任せるためです。

### __slots__ による高速化
`pi0disp` の `Sprite` 関連クラスでは `__slots__` を積極的に使用しています。

#### __slots__ とは？
Python の通常のクラスは、インスタンス属性を `__dict__` という辞書形式で保持します。これは柔軟ですが、メモリ消費が大きく、アクセス速度もわずかに遅くなります。
`__slots__` を定義すると、属性を固定の配列形式で保持するようになり、**「メモリ消費の劇的な削減」**と**「属性アクセス（読み書き）の高速化」**が実現されます。これは大量のオブジェクトを動かすアニメーションにおいて非常に有効です。

#### 使い方のルール
`Sprite` を継承して新しいクラスを作る際は、以下のようにそのクラスで新しく追加する属性名を `__slots__` に記述してください。

```python
class MySprite(Sprite):
    # このクラスで使う属性だけをタプルで指定
    __slots__ = ("color", "name") 

    def __init__(self, x, y, width, height, color):
        super().__init__(x, y, width, height)
        self.color = color # 読み書きが高速化される
```
※ 継承元の `Sprite` で定義されている属性（`x`, `y` 等）を改めて書く必要はありません。

### Dirty Rectangle (差分更新) の仕組み
リソースの限られた環境で高い FPS を実現するために、変化のあった領域だけを送信する仕組みです。

1.  **状態変更の検知**: `x`, `y` 等が変更されると、自動的に内部で「変更あり」の状態になります。
2.  **更新領域の計算**: `get_dirty_region()` が「移動前後の位置を統合した矩形」を算出します。
3.  **状態の確定**: 描画後に `record_current_bbox()` を呼ぶことで、次のフレームに向けた位置情報の保存とフラグリセットを行います。

---

## クラスリファレンス

### Sprite (基底クラス)
| プロパティ/メソッド | 説明 |
| :--- | :--- |
| `x`, `y` | 左上座標。変更すると自動で Dirty 判定されます。 |
| `width`, `height` | サイズ。 |
| `bbox` | 現在の境界ボックス `(x1, y1, x2, y2)`。 |
| `get_dirty_region()` | 更新が必要な領域を `(x, y, w, h)` 形式で返します。不要なら `None`。 |
| `record_current_bbox()` | 現在の状態を確定させ、次フレームの準備をします。 |
| `update(delta_t)` | 【抽象】状態（位置など）を更新する処理を記述します。 |
| `draw(draw)` | 【抽象】Pillow を使用した描画処理を記述します。 |

### CircleSprite (円形スプライト)
`Sprite` を継承し、中心座標 (`cx`, `cy`) と半径 (`radius`) で操作可能です。

---

## カスタムスプライトの実装例

### 円形スプライト (ボール)
```python
class BallSprite(CircleSprite):
    __slots__ = ("color", "vx", "vy")

    def __init__(self, cx, cy, radius, color):
        super().__init__(cx, cy, radius)
        self.color = color
        self.vx, self.vy = 100.0, 80.0

    def update(self, delta_t):
        self.cx += self.vx * delta_t
        self.cy += self.vy * delta_t

    def draw(self, draw):
        draw.ellipse(self.bbox, fill=self.color)
```

### 画像スプライト (キャラクター等)
```python
class CharacterSprite(Sprite):
    __slots__ = ("image",)

    def __init__(self, x, y, image):
        super().__init__(x, y, image.width, image.height)
        self.image = image

    def draw(self, draw):
        draw._image.paste(self.image, (int(self.x), int(self.y)))
```

---

## メインループへの組み込み

```python
dirty_regions = []
for s in sprites:
    s.update(delta_t)
    region = s.get_dirty_region()
    if region:
        dirty_regions.append(region)

# (背景描画の後で)
for s in sprites:
    s.draw(draw)

if dirty_regions:
    optimized = RegionOptimizer.merge_regions(dirty_regions)
    for r in optimized:
        lcd.display_region(frame_image, *r)

for s in sprites:
    s.record_current_bbox()
```
