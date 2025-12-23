# Plan10.md: ロボットの顔アニメーション改良計画 (再構築)

## 概要

`samples/robot_face_animation2.py` の機能を再改良し、ロボットの顔の表情変化が完了した後も、目がキョロキョロとランダムに動き続けるようにする。現在の問題点「表情が変換している間は目がキョロキョロ動くが、表情変化が完了すると目の動きが止まってしまう」を解決する。目の動きが視覚的に確認できるよう、特にデバッグログを工夫する。

## 問題点の再特定

前回の試みでは、`RobotFaceApp` クラスに導入した `_is_gazing_randomly` フラグと `_gaze_loop_end_time` が、視線キョロキョロ動作の期間を制限していたことが原因で、表情変化完了後に視線が停止していた。

-   **ランダムモード (`main`)**: `_handle_random_mood_update` が表情を設定するたびに `_is_gazing_randomly` と `_gaze_loop_end_time` がリセットされ、キョロキョロ動作が一定期間継続するが、次の表情変化までの間に `_gaze_loop_end_time` を過ぎると `_is_gazing_randomly` が `False` になり視線が止まる。
-   **インタラクティブモード (`play_interactive_face`)**: `play_interactive_face` メソッド内の `while self._is_gazing_randomly:` ループが `_gaze_loop_end_time` に到達すると終了するため、視線が止まる。

## 目標

-   アプリケーション実行中は、表情変化の有無に関わらず、目が常にキョロキョロと動き続けるようにする。
-   視線の動きが視覚的に明確に認識できるよう、移動範囲や頻度を調整可能にする。
-   デバッグログを強化し、視線のターゲット座標 (`target_gaze_x`) と現在の座標 (`current_gaze_x`) の両方、および描画時に使用される `gaze_offset` を確認できるようにする。

## 計画

### ステップ 1: 視線キョロキョロ動作の永続化

1.  **状態変数の削除と簡素化**:
    *   `RobotFaceApp` クラスから `self._is_gazing_randomly` および `self._gaze_loop_end_time` インスタンス変数を削除する。
    *   これらの変数を初期化しているコンストラクタ (`__init__`) の行も削除する。
    *   `_gaze_interval_min`, `_gaze_interval_max`, `_gaze_width_range_min`, `_gaze_width_range_max` は、視線動作のパラメータとして保持する。

2.  **`_handle_gaze_update` メソッドの再構築**:
    *   `_handle_gaze_update(self, now: float)` メソッド内の `_is_gazing_randomly` および `_gaze_loop_end_time` に関連する条件分岐とロジック（早期リターンや `_is_gazing_randomly = False` の設定など）をすべて削除する。
    *   `_handle_gaze_update` は、`now > self._next_gaze_time` の条件に基づいて、常に `target_gaze_x` を更新するようにする。これにより、視線が途切れることなくランダムに動き続ける。

3.  **`_handle_random_mood_update` からの関連ロジック削除**:
    *   `_handle_random_mood_update` メソッド内の `self._is_gazing_randomly = True` および `self._gaze_loop_end_time` の設定ロジックを削除する。表情変化は視線動作に影響を与えないようにする。

4.  **`play_interactive_face` メソッドの簡素化**:
    *   `play_interactive_face` メソッド内の `while self._is_gazing_randomly:` ループ全体を削除する。
    *   表情変化の待機ループ後 (`while time.time() - start_time < 0.25:`) に、`_is_gazing_randomly` と `_gaze_loop_end_time` を設定していた行も削除する。
    *   `play_interactive_face` は、単に表情を一度表示するだけのメソッドとする。視線動作は `RobotFaceApp.main` のメインループで共通して行われるようにする。

### ステップ 2: デバッグログの強化

1.  **`_handle_gaze_update` のログ強化**:
    *   `_handle_gaze_update` メソッドが `self.face.set_gaze(gaze)` を呼び出す際に、更新された `target_gaze_x` の値と、現在の `current_gaze_x` の値を比較できるようなデバッグログを追加する。
    *   例: `self.__log.debug("Gaze target changed to %s. Current gaze_x=%s", gaze, self.face.current_gaze_x)`

2.  **`RobotFace.update` のログ強化**:
    *   `RobotFace.update()` メソッド内で `self.current_gaze_x` が更新されるたびに、その新しい値と `target_gaze_x` の値をログに出力する。
    *   例: `self.__log.debug("Face gaze updated. current_gaze_x=%s, target_gaze_x=%s", self.current_gaze_x, self.target_gaze_x)`

3.  **`_draw_one_eye` のログ強化**:
    *   `RobotFace._draw_one_eye` メソッドが呼ばれる際に、実際に描画に適用される `gaze_offset` の値を出力する。
    *   例: `self.__log.debug("Drawing eye with gaze_offset=%s", gaze_offset)`

### ステップ 3: 視線移動の視覚的認識の調整

1.  **視線移動範囲の再検討**:
    *   現在の `_gaze_width_range_min = -10.0` と `_gaze_width_range_max = 10.0` での視覚的フィードバックを再確認する。必要であれば、これらの値をさらに広げる（例: `-15.0` から `15.0` など）。
    *   これにより、視覚的に「キョロキョロ」していることが明確に認識できるようにする。

2.  **更新頻度の調整**:
    *   `RobotFaceApp.main()` ループ内の `time.sleep(0.2)` が、視線変化の滑らかさに影響していないか再確認する。必要であれば、値を小さくする（例: `0.1` など）ことを検討する。

## トップレベルのプログラマー視点からの改善点

-   **単一責任の原則**: 視線のキョロキョロ動作を表情変化ロジックから完全に分離することで、各コンポーネントの責任がより明確になる。
-   **デバッグ容易性の向上**: 詳細なデバッグログにより、システムの内部状態と視覚的出力との間に乖離がある場合でも、原因の特定が容易になる。
-   **設定の柔軟性**: 視線移動のパラメータを `RobotFaceApp` の初期化時に設定できるようにしておくことで、将来的な調整やカスタマイズが容易になる。

## 作業項目 (TODO)

- [ ] **ステップ 1: 視線キョロキョロ動作の永続化**
    - [ ] `samples/robot_face_animation2.py` を開く。
    - [ ] `RobotFaceApp` クラスから `self._is_gazing_randomly` および `self._gaze_loop_end_time` インスタンス変数、およびコンストラクタでの初期化行を削除する。
    - [ ] `_handle_gaze_update(self, now: float)` メソッド内の `_is_gazing_randomly` および `_gaze_loop_end_time` に関連する条件分岐とロジックをすべて削除する。
    - [ ] `_handle_random_mood_update` メソッド内の `self._is_gazing_randomly = True` および `self._gaze_loop_end_time` の設定ロジックを削除する。
    - [ ] `play_interactive_face` メソッド内の `while self._is_gazing_randomly:` ループ全体を削除する。
    - [ ] `play_interactive_face` メソッド内の `_is_gazing_randomly` と `_gaze_loop_end_time` を設定していた行も削除する。

- [ ] **ステップ 2: デバッグログの強化**
    - [ ] `_handle_gaze_update` メソッドが `self.face.set_gaze(gaze)` を呼び出す際に、更新された `target_gaze_x` の値と、`self.face.current_gaze_x` の値を比較できるようなデバッグログを追加する。
    - [ ] `RobotFace.update()` メソッド内で `self.current_gaze_x` が更新されるたびに、その新しい値と `target_gaze_x` の値をログに出力する。
    - [ ] `RobotFace._draw_one_eye` メソッドが呼ばれる際に、実際に描画に適用される `gaze_offset` の値を出力する。

- [ ] **ステップ 3: 視線移動の視覚的認識の調整**
    - [ ] `_gaze_width_range_min` と `_gaze_width_range_max` の値をさらに広げる（例: `-15.0` から `15.0` など）ことを検討する。
    - [ ] `RobotFaceApp.main()` ループ内の `time.sleep(0.2)` を `0.1` などに小さくすることを検討する。

- [ ] **リンティングの実行 (中間チェック)**
    - [ ] `mise run lint` を実行し、リンティングエラーがないことを確認する。エラーがあれば修正する。

- [ ] **動作確認**
    - [ ] `samples/robot_face_animation2.py` を `--random --debug` オプションで実行し、デバッグログと実際の画面表示で、表情変化後も目がキョロキョロ動き続けることを確認する。

- [ ] **テストの実行**
    - [ ] `mise run test` を実行し、既存のテストがすべてパスすることを確認する。

---

この内容で `Plan10.md` を作成します。
以上の内容で進めてよろしいでしょうか？ [y/n]
