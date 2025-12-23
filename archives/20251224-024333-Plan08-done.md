# Plan08: `samples/robot_face_animation2.py` の表情変化を等速にするリファクタリング

## 1. 目的

現在の `samples/robot_face_animation2.py` におけるロボットの表情変化は、`lerp` 関数 (線形補間) を固定の `speed` 値 (`0.5`) で繰り返し適用しているため、目標の表情に近づくにつれて変化の速度が遅くなる特性を持っています。これは、自然な減速感を表現する場合には有効ですが、「N秒で表情を完全に切り替える」といった、より予測可能で一定の速度でのアニメーションが求められる場合があります。

本計画の目的は、`RobotFace` および `RobotFaceApp` クラスをリファクタリングし、表情の変化が開始から終了まで一定の速度で進行するように改善することです。これにより、アニメーションの制御性が向上し、より多様な表現が可能になります。

## 2. 現在の実装における課題

`RobotFace.update(speed=0.5)` メソッドは、以下の計算を繰り返し行います。
`current_value = current_value + (target_value - current_value) * speed`

この式において、`(target_value - current_value)` (目標値と現在値の差) が時間とともに減少するため、`current_value` が `target_value` に近づくにつれて、1ステップあたりの変化量も減少します。結果として、変化の初期は速く、終期は遅くなる、いわゆるイーズアウト（減速）のような挙動を示します。

## 3. 等速変化の設計

等速変化を実現するためには、変化開始時点のパラメータを記録し、経過時間に基づいて補間係数を計算するアプローチが必要です。

### 3.1. `FaceState` の拡張 (必要であれば)

現在の `FaceState` は表情の最終状態を表すため、変更は不要です。

### 3.2. `RobotFace` クラスの変更

`RobotFace` クラスは個々の表情パラメータの補間ロジックをカプセル化する役割を担うべきです。

*   **属性の追加**:
    *   `_start_state: FaceState`：表情変化が始まった瞬間の `FaceState` を保持します。
    *   `_change_start_time: float`：表情変化が始まったシステムのタイムスタンプを保持します。
    *   `_change_duration: float`：表情変化を完了するまでの目標時間（秒）を保持します。
    *   `_is_changing: bool`：現在表情が変化中であるかを示すフラグ。
*   **`__init__` メソッド**:
    *   `_change_duration` のデフォルト値を設定します（例: `0.5` 秒）。
*   **`set_target_state(self, state: FaceState, duration: float | None = None)` メソッドの変更**:
    *   現在の `self.current_state` を `self._start_state` にコピーします。
    *   `self.target_state` を新しい `state` に設定します。
    *   `self._change_start_time = time.time()` を設定します。
    *   `self._change_duration = duration if duration is not None else DEFAULT_DURATION` とします。
    *   `self._is_changing = True` に設定します。
*   **`update(self)` メソッドの変更**:
    *   `speed` 引数を削除します。
    *   `if not self._is_changing: return` で、変化中でなければ早期リターンします。
    *   `now = time.time()` を取得します。
    *   `elapsed_time = now - self._change_start_time` を計算します。
    *   補間係数 `t_factor = min(1.0, max(0.0, elapsed_time / self._change_duration))` を計算します。
    *   各表情パラメータ (`mouth_curve`, `brow_tilt` など) について、`lerp(self._start_state.parameter, self.target_state.parameter, t_factor)` を使用して `self.current_state` を更新します。
    *   もし `t_factor >= 1.0` ならば、`self._is_changing = False` に設定し、`self.current_state` を `self.target_state` と完全に一致させます。
*   **`set_gaze(self, x)` メソッド**:
    *   視線変更は表情変化とは独立して、現在の `lerp` メカニズムを維持するか、同様に等速変化に移行するか検討が必要です。今回は表情変化に焦点を当てるため、`gaze` は現状維持とします。

### 3.3. `RobotFaceApp` クラスの変更

`RobotFaceApp` は `RobotFace` の外部からの制御を担うべきです。

*   **`__init__` メソッド**:
    *   `face_change_duration: float` (表情変化のデフォルト時間) 引数を追加し、`RobotFace` の初期化時に渡せるようにします。
*   **`_handle_random_mood_update(self, now: float)` メソッドの変更**:
    *   `self.face.set_target_state(self.all_moods[new_mood])` の呼び出し時に、`duration` を指定できるようにします。これにより、ランダムな表情変化の速度も制御可能になります。
    *   例: `self.face.set_target_state(self.all_moods[new_mood], duration=random.uniform(0.5, 1.5))`
*   **`play_interactive_face(self, target_state: FaceState)` メソッドの変更**:
    *   `self.face.set_target_state(target_state)` の呼び出し時に、`duration` を指定します。これにより、インタラクティブな表情変化の速度も制御可能になります。
    *   例: `self.face.set_target_state(target_state, duration=0.25)` （現在の瞬時変化に相当する短い時間）
*   **`main(self)` メソッドの変更**:
    *   `self.face.update()` の `speed` 引数を削除します。

## 4. 影響範囲の特定

*   `RobotFace` クラス:
    *   `__init__` メソッド (duration の追加)
    *   `update` メソッド (ロジックの変更、`speed` 引数の削除)
    *   `set_target_state` メソッド (開始状態、時間管理ロジックの追加)
*   `RobotFaceApp` クラス:
    *   `__init__` メソッド (duration の引数追加、`RobotFace` への引き渡し)
    *   `_handle_random_mood_update` メソッド (`set_target_state` 呼び出し時の duration 指定)
    *   `play_interactive_face` メソッド (`set_target_state` 呼び出し時の duration 指定)
    *   `main` メソッド (`RobotFace.update()` 呼び出し時の `speed` 引数削除)
*   `main` 関数:
    *   `RobotFaceApp` の初期化時に `face_change_duration` を渡す。

## 5. テスト計画

*   **ユニットテスト**:
    *   `RobotFace.update()` が `_change_duration` に従って正しく補間を行うか。
    *   `t_factor` が `1.0` に達した後に `_is_changing` が `False` になり、`current_state` が `target_state` と一致するか。
    *   `set_target_state` が呼ばれたときに `_start_state`, `_change_start_time`, `_is_changing` が正しく設定されるか。
*   **手動テスト**:
    *   コマンドライン引数ありモード (`uv run samples/robot_face_animation2.py -d '/o_o' '_O_O'`) で、表情が等速で変化することを確認します。
    *   インタラクティブモード (`uv run samples/robot_face_animation2.py -d`) で、顔の記号を入力した際に表情が等速で変化することを確認します。
    *   異なる `duration` 値を設定した場合の表情変化の速度を確認します。

## 6. 実装ステップ

1.  `git checkout -b feature/equal-speed-face-change` で新しいブランチを作成します。
2.  `RobotFace` クラスに `_start_state`, `_change_start_time`, `_change_duration`, `_is_changing` 属性を追加します。
3.  `RobotFaceApp` クラスの `__init__` に `face_change_duration` 引数を追加します。
4.  `RobotFace` クラスの `__init__` メソッドで `_change_duration` のデフォルト値を設定します。
5.  `RobotFace.set_target_state` メソッドのシグネチャを変更し、`duration` 引数を追加、ロジックを更新します。
6.  `RobotFace.update` メソッドのシグネチャを変更し、`speed` 引数を削除、ロジックを時間ベースの補間に更新します。
7.  `RobotFaceApp._handle_random_mood_update` メソッド内で `self.face.set_target_state` の呼び出し時に `duration` を指定します。
8.  `RobotFaceApp.play_interactive_face` メソッド内で `self.face.set_target_state` の呼び出し時に `duration` を指定します。
9.  `RobotFaceApp.main` メソッド内で `self.face.update()` の `speed` 引数を削除します。
10. `main` 関数内で `RobotFaceApp` の初期化時に `face_change_duration` を渡します。
11. `uv run lint` を実行し、リンティングエラーを修正します。
12. `uv run test` を実行し、既存のテストが壊れていないことを確認します。
13. 手動テストを実行し、意図した等速変化が実現されていることを確認します。
14. 変更をコミットします。