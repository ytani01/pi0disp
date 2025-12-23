# Tasks08: `samples/robot_face_animation2.py` の表情変化を等速にする実装タスクリスト

このタスクリストは、`Plan08.md` に基づき、`samples/robot_face_animation2.py` の表情変化を等速にするための具体的な実装ステップを定義します。

## 実行ステップ

- [ ] git checkout -b feature/equal-speed-face-change

### 1. `RobotFace` クラスへの属性追加と `__init__`, `set_target_state`, `update` メソッドの修正

- [ ] `RobotFace` クラスに以下の属性を追加する:
    - [ ] `_start_state: FaceState`
    - [ ] `_change_start_time: float`
    - [ ] `_change_duration: float`
    - [ ] `_is_changing: bool`
- [ ] `RobotFace` クラスの `__init__` メソッドのシグネチャを変更し、`change_duration: float = 0.5` を追加する。
    - [ ] `self._change_duration = change_duration` を追加する。
    - [ ] `self._is_changing = False` を追加する。
- [ ] `RobotFace.set_target_state` メソッドのシグネチャを `set_target_state(self, state: FaceState, duration: float | None = None)` に変更する。
    - [ ] `self._start_state = self.current_state.copy()` を追加する。
    - [ ] `self._change_start_time = time.time()` を追加する。
    - [ ] `self._change_duration = duration if duration is not None else self._change_duration` に修正する。
    - [ ] `self.target_state = state.copy()` は既存のまま。
    - [ ] `self._is_changing = True` に設定する。
- [ ] `RobotFace.update` メソッドのシグネチャを `update(self)` に変更し、`speed` 引数を削除する。
    - [ ] `if not self._is_changing: return` をメソッドの先頭に追加する。
    - [ ] `now = time.time()` を取得する。
    - [ ] `elapsed_time = now - self._change_start_time` を計算する。
    - [ ] `t_factor = min(1.0, max(0.0, elapsed_time / self._change_duration))` を計算する。
    - [ ] 各表情パラメータ (`mouth_curve`, `brow_tilt`, `mouth_open`, `left_eye_openness`, `left_eye_size`, `left_eye_curve`, `right_eye_openness`, `right_eye_size`, `right_eye_curve`) について、`lerp(self._start_state.parameter, self.target_state.parameter, t_factor)` を使用して `self.current_state` を更新する。
    - [ ] `self.current_gaze_x = lerp(self.current_gaze_x, self.target_gaze_x, 0.5)` はそのまま維持する (視線はこれまで通りの減速変化)。
    - [ ] `if t_factor >= 1.0:` ブロックを追加し、以下の処理を行う:
        - [ ] `self._is_changing = False` に設定する。
        - [ ] `self.current_state` を `self.target_state` と完全に一致させる（浮動小数点誤差対策）。

### 2. `RobotFaceApp` クラスの修正

- [ ] `RobotFaceApp` クラスの `__init__` メソッドのシグネチャに `face_change_duration: float = 0.5` 引数を追加する。
    - [ ] `self.face_change_duration = face_change_duration` を追加する。
    - [ ] `self.face = RobotFace(..., change_duration=self.face_change_duration, ...)` のように、`RobotFace` の初期化時に `change_duration` を渡すように修正する。
- [ ] `RobotFaceApp._handle_random_mood_update` メソッド内で `self.face.set_target_state` の呼び出し時に `duration=random.uniform(0.5, 1.5)` を指定する。
- [ ] `RobotFaceApp.play_interactive_face` メソッド内で `self.face.set_target_state` の呼び出し時に `duration=0.25` を指定する。
- [ ] `RobotFaceApp.main` メソッド内で `self.face.update(speed=0.5)` の `speed` 引数を削除し、`self.face.update()` と変更する。

### 3. `main` 関数の修正

- [ ] `main` 関数内で `RobotFaceApp` の初期化時に `face_change_duration=0.5` を渡すように調整する。

### 4. コードクオリティとテスト

- [ ] `mise run lint` を実行し、リンティングエラーを修正する。
- [ ] `mise run test` を実行し、既存のテストが壊れていないことを確認する。
- [ ] `mise run test` でエラーが発生した場合、エラーがなくなるまで修正を繰り返す。

### 5. 手動テスト

- [ ] コマンドライン引数ありモード (`uv run samples/robot_face_animation2.py -d '/o_o' '_O_O'`) で、表情が等速で変化することを確認する。
- [ ] インタラクティブモード (`uv run samples/robot_face_animation2.py -d`) で、顔の記号を入力した際に表情が等速で変化することを確認する。
- [ ] 異なる `face_change_duration` 値 (例: 1.0秒, 2.0秒) を設定した場合の表情変化の速度を確認する。

### 6. Git操作

- [ ] `git add samples/robot_face_animation2.py`
- [ ] `git commit -m "feat: Implement equal speed face change animation in robot_face_animation2.py"`
