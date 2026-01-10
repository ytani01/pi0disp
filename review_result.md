# コードレビュー結果: `src/pi0disp/`

## 変更の概要
アニメーションと表示システムのメジャーリファクタリング。差分更新（Dirty Rectangle）の導入、Cairoによるアンチエイリアス描画、新しいSpriteベースのアーキテクチャ、ベンチマーク機能の強化。

## 指摘事項

### File: src/pi0disp/utils/sprite.py
#### L103: [重要度: 高] Sprite と RegionOptimizer 間の座標形式の不一致
`Sprite.get_dirty_region()` は `(x0, y0, x1, y1)` 形式のバウンディングボックスを返していますが、`performance_core.py` の `RegionOptimizer.merge_regions` や `ballanime.py` 内の描画ループは `(x, y, w, h)` 形式を期待しています。これにより、面積計算が誤り、差分更新が正しく動作しません。

修正案:
```python
     def get_dirty_region(self) -> Optional[Tuple[int, int, int, int]]:
         """
-        現在のフレームで再描画が必要な領域を計算します。
-        アンチエイリアスやサブピクセルシフトを考慮し、小さなマージンを含めます。
+        再描画が必要な領域を (x, y, w, h) 形式で計算します。
         """
         if not self._dirty and self.prev_bbox is not None:
             return None
         res = merge_bboxes(self.prev_bbox, self.bbox)
         if res is None:
             return None
 
-        # アンチエイリアスの安全のために2ピクセルのマージンを追加
-        return (res[0] - 2, res[1] - 2, res[2] + 2, res[3] + 2)
+        # (x, y, w, h) 形式で、2ピクセルのマージンを含めて返す
+        x0, y0, x1, y1 = res[0] - 2, res[1] - 2, res[2] + 2, res[3] + 2
+        return (x0, y0, x1 - x0, y1 - y0)
```

### File: src/pi0disp/commands/ballanime.py
#### L431: [重要度: 中] PIL から Cairo surface への変換が非効率
PIL 画像の `split()` と `merge()` を使用すると、複数の中間オブジェクトが生成され、NumPy 配列の直接操作に比べて非常に低速です。

修正案:
```python
     width, height = pil_image.size
-    r, g, b, a = pil_image.split()
-    bgra_image = Image.merge("RGBA", (b, g, r, a))
-    data = np.array(bgra_image)
+    data = np.array(pil_image)
+    # RGB(A) から BGRA への並び替え
+    data = data[:, :, [2, 1, 0, 3]]
 
     surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
```

#### L463: [重要度: 中] Cairo surface から PIL への変換が非効率
上記と同様に、アニメーションループ内で `split()` / `merge()` を使用すると FPS に大きな影響を与えます。

修正案:
```python
-    img = Image.fromarray(target_data[:, :, :3], "RGB")
-    b, g, r = img.split()
-    return Image.merge("RGB", (r, g, b))
+    # BGRA から RGB へ: チャンネル 2, 1, 0 を選択
+    return Image.fromarray(target_data[:, :, [2, 1, 0]], "RGB")
```

#### L511: [重要度: 中] パフォーマンスボトルネック: 冗長な ImageDraw 作成とボールのフィルタリング
最適化モードにおいて、マージされた領域ごとに `ImageDraw.Draw(frame_image)` を作成し、全 `balls` をループしています。領域数が多い場合、このオーバーヘッドが蓄積します。

修正案:
```python
-            for rx, ry, rw, rh in merged_regions:
-                # ... (中略) ...
-                # 2. その領域に関連するオブジェクトを再描画
-                draw = ImageDraw.Draw(frame_image)
-                for ball in balls:
+            # 1. まず全てのダーティリージョンに対して背景を更新
+            for rx, ry, rw, rh in merged_regions:
+                x1, y1 = max(0, rx), max(0, ry)
+                x2, y2 = min(screen_width, rx + rw), min(screen_height, ry + rh)
+                frame_image.paste(background.crop((x1, y1, x2, y2)), (x1, y1))
+
+            # 2. 1つの Draw オブジェクトを使用して関連するボールを一度に描画
+            draw = ImageDraw.Draw(frame_image)
+            for ball in balls:
+                # 全てのボールを描画（クリッピングは paste 段階で処理済み）
+                ball.draw(draw)
```

### File: src/pi0disp/disp/st7789v.py
#### L181: [重要度: 中] 頻繁なフルイメージのメモリコピー
差分が検出されるたびに `image.copy()` が呼び出されています。320x240 RGB 画像で約 230KB のコピーが毎フレーム発生し、Pi Zero のような環境では GC 負荷とメモリ帯域を圧迫します。

修正案:
```python
         self.write_pixels(pixel_bytes)
-
-        self._last_image = image.copy()
+        # キャッシュの変更領域のみを更新
+        if self._last_image:
+            self._last_image.paste(region_img, diff_bbox[:2])
+        else:
+            self._last_image = image.copy()
```

### File: src/pi0disp/commands/ballanime.py
#### L931: [重要度: 低] ベンチマークレポートのヘッダーとデータ行の不一致
ヘッダー行に `Mem (App)` しかありませんが、データ行には `avg_mem_pigpiod` も含まれるべきです。

修正案:
```python
-                        "| Date | Mode | Balls | Target FPS | SPI | Avg FPS | CPU (App) | CPU (pigpiod) | Mem (App) |\n"
+                        "| Date | Mode | Balls | Target FPS | SPI | Avg FPS | CPU (App) | CPU (pigpiod) | Mem (App) | Mem (pig) |\n"
...
-                    f"| {timestamp} | {mode} | {num_balls} | {fps} | {spi_mhz}M | {res['avg_fps']:.2f} | {res['avg_cpu']:.1f}% | {res['avg_pigpiod']:.1f}% | {res['avg_mem_ballanime']} |\n"
+                    f"| {timestamp} | {mode} | {num_balls} | {fps} | {spi_mhz}M | {res['avg_fps']:.2f} | {res['avg_cpu']:.1f}% | {res['avg_pigpiod']:.1f}% | {res['avg_mem_ballanime']} | {res['avg_mem_pigpiod']} |\n"
```
