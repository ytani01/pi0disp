# `samples/robot_face_animation2.py` 改造計画書

## 1. 目的

`samples/robot_face_animation.py` をベースに、表情の表示間隔を延長し、その間に目がキョロキョロと動くアニメーションを追加することで、より生命感のある表現を実現する。

## 2. 改造ファイル

- **コピー元:** `samples/robot_face_animation.py`
- **コピー先:** `samples/robot_face_animation2.py`

## 3. 改造内容

### 3.1. 表情の表示間隔を5秒に延長

`RobotFaceApp.main` メソッド内のシーケンス再生ロジックを変更する。
現在の `time.sleep(1)` で1秒待機している部分を、後述する「目のキョロキョロ動作」を5秒間実行するロジックに置き換える。

### 3.2. 目のキョロキョロ動作の実装

`RobotFaceApp.main` のシーケンス再生ループ（`for state in itertools.cycle(self.face_sequence):` の内部）を以下のように改造する。

1.  **表情の設定:**
    *   `self.face.set_target_state(state)` を呼び出し、目標の表情を設定する。
    *   短いアニメーション（0.25秒程度）で目標の表情に変化させる。

2.  **視線アニメーションループ (約4.75秒間):**
    *   表情が変化した後、約4.75秒間の「視線アニメーション」ループを開始する。
    *   このループ内では、
        *   `0.5`秒から`1.5`秒ごとに `_next_gaze_time` を更新する。
        *   `_next_gaze_time` になったら、`RobotFace.GAZE_WIDTH` の範囲内でランダムな視線 `gaze` を生成し、`self.face.set_gaze(gaze)` を呼び出す。
        *   ループの各イテレーションで `self.face.update()` と `self.output.show()` を呼び出し、視線の滑らかな動きを描画する。
        *   短い `time.sleep()` (例: `0.05`秒) を入れる。

**`RobotFaceApp.main` の擬似コード:**

```python
def main(self):
    if self.face_sequence:
        # シーケンス再生モード
        for state in itertools.cycle(self.face_sequence):
            # 1. 表情を設定・変化させる
            self.face.set_target_state(state)
            start_time = time.time()
            while time.time() - start_time < 0.25:
                self.face.update(speed=0.5)
                # ... (描画処理) ...
                time.sleep(0.05)

            # 2. 約4.75秒間、視線を動かす
            gaze_loop_end_time = time.time() + 4.75
            self._next_gaze_time = time.time()
            while time.time() < gaze_loop_end_time:
                now = time.time()
                # 視線変更タイミングか？
                if now > self._next_gaze_time:
                    gaze = random.uniform(-self.GAZE_WIDTH, self.GAZE_WIDTH)
                    self.face.set_gaze(gaze)
                    self._next_gaze_time = now + random.uniform(0.5, 1.5)

                # 更新と描画
                self.face.update(speed=0.5) # 視線を滑らかに動かす
                # ... (描画処理) ...
                time.sleep(0.05)
    else:
        # ランダム再生モード (変更なし)
        # ...
```

## 4. 作業手順

1.  `git checkout develop` など、適切なブランチにいることを確認する。
2.  `cp samples/robot_face_animation.py samples/robot_face_animation2.py` コマンドを実行し、ファイルをコピーする。
3.  `samples/robot_face_animation2.py` を開き、以下の点を修正する。
    1.  ファイル冒頭の `click.command` の引数を `__file__.split("/")[-1]` になっているので、ファイル名が自動的に反映される。変更は不要。
    2.  `RobotFaceApp.main` メソッドを探す。
    3.  `if self.face_sequence:` ブロック内のロジックを、上記「3.2. 目のキョロキョロ動作の実装」で示した擬似コードに基づいて全面的に書き換える。
4.  `mise run lint` を実行し、構文エラーやスタイル違反がないか確認する。
5.  手動で動作確認を行う。
    ```bash
    uv run samples/robot_face_animation2.py /o_o _O_O
    ```
    上記コマンドで、2つの表情が5秒間隔で切り替わり、その間に目がキョロキョロと動くことを確認する。
6.  `git add samples/robot_face_animation2.py` を実行する。
7.  `git commit -m "feat: Create robot_face_animation2 with gaze animation"` でコミットする。
