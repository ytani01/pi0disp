# Tasks09.md: ロボットの顔アニメーション改良タスクリスト

## ブランチ作成と切り替え

- [x] gitブランチ `feature/Tasks09` を作成し、そのブランチに切り替える。

## 目のキョロキョロ動作の共通化と状態管理の改善

### 1. `RobotFaceApp` に視線制御の状態を導入

- [x] `samples/robot_face_animation2.py` を開く。
- [x] `RobotFaceApp` クラスのコンストラクタ (`__init__`) に以下のインスタンス変数を追加する:
    - [x] `self._is_gazing_randomly: bool = False`
    - [x] `self._gaze_loop_end_time: float = 0.0`
    - [x] `self._gaze_interval_min: float = 0.5`
    - [x] `self._gaze_interval_max: float = 2.0`
    - [x] `self._gaze_width_range_min: float = -10.0`
    - [x] `self._gaze_width_range_max: float = 10.0`
- [x] 既存の `self.GAZE_WIDTH` を削除する。

### 2. 共通の視線更新メソッドの拡張

- [x] `samples/robot_face_animation2.py` を開く。
- [x] `RobotFaceApp._handle_gaze_update(self, now: float)` メソッドを修正する。
    - [x] メソッドの冒頭に `if not self._is_gazing_randomly: return` を追加する。
    - [x] `if now > self._gaze_loop_end_time:` の条件で `self._is_gazing_randomly = False` を設定し、`return` するロジックを追加する。
    - [x] `gaze = random.uniform(-self.GAZE_WIDTH, self.GAZE_WIDTH)` の行を `gaze = random.uniform(self._gaze_width_range_min, self._gaze_width_range_max)` に変更する。
    - [x] `self._next_gaze_time = now + random.uniform(0.5, 2.0)` の行を `self._next_gaze_time = now + random.uniform(self._gaze_interval_min, self._gaze_interval_max)` に変更する。
- [x] `RobotFaceApp.GAZE_WIDTH` の定義を削除する。

### 3. リンティングの実行 (中間チェック)

- [x] `mise run lint` を実行し、リンティングエラーがないことを確認する。エラーがあれば修正する。

## 表情変化の完了検出とキョロキョロ動作の開始

### 4. `RobotFace` に `is_changing` プロパティを追加

- [x] `samples/robot_face_animation2.py` を開く。
- [x] `RobotFace` クラスに以下のプロパティを追加する:
    ```python
    @property
    def is_changing(self) -> bool:
        """Is face changing?"""
        return self._is_changing
    ```

### 5. `RobotFaceApp` で表情変化完了を検知し、キョロキョロ動作を開始

- [x] `samples/robot_face_animation2.py` を開く。
- [x] `RobotFaceApp._handle_random_mood_update(self, now: float)` メソッドを修正する。
    - [x] 新しい表情が設定された後 (`self.face.set_target_state()` の後)、`self._is_gazing_randomly = True` を設定する。
    - [x] `self._gaze_loop_end_time = now + random.uniform(5.0, 10.0)` のように、キョロキョロ動作の終了時刻を設定する。（期間は適宜調整）
- [x] `RobotFaceApp.play_interactive_face()` メソッドを修正する。
    - [x] 表情変化の待機ループ (`while time.time() - start_time < 0.25:`) の直後（またはループ内で `self.face.is_changing` が `False` になったことを検知した時点）に、以下のロジックを追加する:
        - [x] `self._is_gazing_randomly = True`
        - [x] `self._gaze_loop_end_time = time.time() + 4.75` （現在の `play_interactive_face` のキョロキョロ動作期間に合わせる）

### 6. リンティングの実行 (中間チェック)

- [x] `mise run lint` を実行し、リンティングエラーがないことを確認する。エラーがあれば修正する。

## 全モードでの統合

### 7. `RobotFaceApp.main()` での統合

- [x] `samples/robot_face_animation2.py` を開く。
- [x] `RobotFaceApp.main()` メソッドの `while True` ループ内で、`self._handle_gaze_update(now)` を常に呼び出すようにする。

### 8. `RobotFaceApp.play_interactive_face()` での統合

- [x] `samples/robot_face_animation2.py` を開く。
- [x] `RobotFaceApp.play_interactive_face()` メソッド内の既存の約4.75秒間の視線ループ (`while time.time() < gaze_loop_end_time:`) を削除する。
- [x] 削除したループの代わりに、その後の描画ループ内で `self._handle_gaze_update(now)` を呼び出すように変更する。これにより、共通の視線更新ロジックが使用される。

## 微調整と確認

### 9. デバッグログの追加

- [x] `samples/robot_face_animation2.py` を開く。
- [x] `RobotFaceApp` および `RobotFace` の主要な状態遷移 (`set_target_state`、`update` の完了時など) や、`_handle_gaze_update` が視線を更新する際などに `self.__log.debug(...)` を用いてデバッグログを追加し、動作確認を容易にする。

### 10. リンティングの実行 (最終チェック)

- [x] `mise run lint` を実行し、リンティングエラーがないことを確認する。エラーがあれば修正する。

### 11. 動作確認とテスト (失敗)

- [x] `samples/robot_face_animation2.py` を以下のモードで実行し、期待通りに動作することを確認する:
    - [ ] `python samples/robot_face_animation2.py --random` (ランダムモード): 表情変化後に目がキョロキョロ動くことを確認。（現状、画面上では確認できず、失敗）
    - [ ] `python samples/robot_face_animation2.py _O_O /O_O _O_O` (シーケンスモード): 各表情表示後に目がキョロキョロ動くことを確認。
    - [ ] `python samples/robot_face_animation2.py` (インタラクティブモード) で、`_O_O` などと入力し、表情変化後に目がキョロキョロ動くことを確認。
- [ ] すべてのモードで、表情変化が完了した後に目がキョロキョロと動き出すことを確認する。
- [ ] 表情が切り替わる際に、視線が適切にリセットされるか、または新しい表情に追従するかを確認する。
- [ ] 最後に `mise run test` を実行し、既存のテストがすべてパスすることを確認する。

**このタスクリストは、目的の動作確認ができなかったため、「失敗」とみなし終了します。**
