# Plan09.md: ロボットの顔アニメーション改良計画

## 概要

`samples/robot_face_animation2.py` の機能を拡張し、ロボットの顔の表情変化が完了した後、その表情を維持しつつ、目がキョロキョロとランダムに動くようにする。この目のキョロキョロ動作は、アプリケーションの全モード（ランダム再生、シーケンス再生、インタラクティブモード）で利用可能とする。

## 現状分析と課題

現在の `samples/robot_face_animation2.py` は以下の特徴を持つ：
- `RobotFace` クラスが顔の状態 (`FaceState`) 管理と描画ロジックをカプセル化。
- `RobotFaceApp` クラスがアプリケーション全体のロジック、特に表情変化と視線移動のタイミングを管理。
- `RobotFace.update()` メソッドが `current_state` を `target_state` に線形補間し、表情変化をアニメーションする。この変化は `_is_changing` フラグによって制御される。
- 視線移動は `RobotFace.set_gaze()` で行われ、`RobotFace.current_gaze_x` と `RobotFace.target_gaze_x` の線形補間によって滑らかにアニメーションする。
- 目のキョロキョロ動作のロジックは `RobotFaceApp.play_interactive_face()` メソッド内に存在し、主にインタラクティブモードでのみ利用されている。
- `RobotFaceApp.main()` メソッド内のランダム再生モードでは、`_handle_gaze_update()` が独立して視線移動をトリガーするが、これは表情変化の完了とは直接連動していない。

課題：
- 表情変化と目のキョロキョロ動作の連動が不十分。表情変化が完了した後にキョロキョロ動作を開始する共通のメカニズムがない。
- 目のキョロキョロ動作のロジックが、インタラクティブモードに限定されている部分があるため、汎用性がない。

## 計画

### ステップ 1: 目のキョロキョロ動作のロジックの共通化と状態管理の改善

1.  **`RobotFaceApp` に視線制御の状態を導入**:
    *   `self._is_gazing_randomly: bool` を追加し、ランダムな視線移動を許可するかどうかを制御する。
    *   `self._gaze_loop_end_time: float` を追加し、ランダムな視線移動をいつまで続けるかを管理する。
    *   `self._gaze_interval_min`, `self._gaze_interval_max` を追加し、視線移動の間隔を制御する。
    *   `self._gaze_width_range_min`, `self._gaze_width_range_max` を追加し、視線移動のX座標の範囲を制御する。
    *   これらの設定は `RobotFaceApp` のコンストラクタで初期化する。

2.  **共通の視線更新メソッドの作成**:
    *   `RobotFaceApp._handle_gaze_update(self, now: float)` を拡張し、`self._is_gazing_randomly` が `True` の場合にのみ視線移動を行うようにする。
    *   このメソッドは `self._gaze_loop_end_time` が過ぎた場合に `self._is_gazing_randomly` を `False` にリセットするロジックも含む。

### ステップ 2: 表情変化の完了検出とキョロキョロ動作の開始

1.  **`RobotFace.update()` の戻り値の変更**:
    *   `RobotFace.update()` がブーリアン値（`_is_changing` の新しい状態）を返すように変更し、表情変化が完了したかどうかを呼び出し元に通知できるようにする。
    *   または、`RobotFace` に `is_changing()` プロパティを追加し、現在の状態を確認できるようにする。今回は後者を採用。

2.  **`RobotFaceApp` で表情変化完了を検知し、キョロキョロ動作を開始**:
    *   `RobotFaceApp.main()` および `RobotFaceApp.play_interactive_face()` のループ内で、`self.face.is_changing()` が `False` になったことを検知する。
    *   検知したら、`self._is_gazing_randomly` を `True` に設定し、`self._gaze_loop_end_time` を未来の適切な時刻に設定して、目のキョロキョロ動作を開始させる。
    *   既存の `RobotFaceApp.play_interactive_face()` 内の視線ループロジックは削除し、共通メソッドに置き換える。

### ステップ 3: 全モードでの統合

1.  **`RobotFaceApp.main()` での統合**:
    *   `self._handle_random_mood_update()` が新しい表情を設定した後、`_is_gazing_randomly` を `True` に設定し、キョロキョロ動作を開始させる。
    *   メインループ内で `self._handle_gaze_update()` を常に呼び出すようにする。

2.  **`RobotFaceApp.play_interactive_face()` での統合**:
    *   表情変化の待機ループの後、`self._is_gazing_randomly` を `True` に設定し、`_gaze_loop_end_time` を設定する。
    *   その後の描画ループでは、`self._handle_gaze_update()` を呼び出すように変更する。

### ステップ 4: 微調整と確認

1.  **視線移動の頻度と範囲の調整**:
    *   `RobotFaceApp` のコンストラクタで初期化された `_gaze_interval_min`, `_gaze_interval_max`, `_gaze_width_range_min`, `_gaze_width_range_max` を用いて、キョロキョロ動作の自然さを調整する。
    *   特に `GAZE_WIDTH` を廃止し、`_gaze_width_range_min`, `_gaze_width_range_max` を使用する。

2.  **デバッグログの追加**:
    *   各状態遷移や重要な処理でデバッグログを追加し、動作確認を容易にする。

3.  **テスト**:
    *   すべてのモード（ランダム、シーケンス、インタラクティブ）で、表情変化完了後に目がキョロキョロと動き出すことを確認する。
    *   表情が切り替わる際に、視線が適切にリセットされるか、または新しい表情に追従するかを確認する。

## トップレベルのプログラマー視点からの追加改善点 (今回のスコープ外だが考慮すべき点)

- **イベントシステム**: 表情変化完了などのイベントを発行し、それを購読する形で目のキョロキョロ動作を開始させるイベントシステムを導入することで、`RobotFaceApp` 内の結合度をさらに低減できる。これは将来的な機能拡張（例えば、特定の表情が特定のキョロキョロパターンを誘発するなど）を容易にする。
- **設定の外部化**: `MOODS`, `LAYOUT`, `COLORS` といった定数を外部設定ファイル（例えば TOML 形式）から読み込むようにする。これにより、コードの変更なしに顔の見た目や表情パターンを柔軟に調整できるようになる。既存の `MyConf` クラスを利用することを検討。
- **アニメーションカーブ**: `lerp` による線形補間だけでなく、イージング関数を導入することで、表情変化や視線移動の動きに自然さや表現力を加えることができる。

## 作業項目 (TODO)

- [ ] `RobotFaceApp` に視線制御用の状態変数 (`_is_gazing_randomly`, `_gaze_loop_end_time`, `_gaze_interval_min`, `_gaze_interval_max`, `_gaze_width_range_min`, `_gaze_width_range_max`) を追加する。
- [ ] `RobotFaceApp._handle_gaze_update()` を拡張し、`_is_gazing_randomly` に基づいて視線移動を行い、必要に応じて `_is_gazing_randomly` をリセットするロジックを追加する。
- [ ] `RobotFace` に `is_changing` プロパティを追加し、表情変化中かどうかを外部から確認できるようにする。
- [ ] `RobotFaceApp.main()` 内で、`_handle_random_mood_update()` が新しい表情を設定した後、キョロキョロ動作を開始するように設定する。
- [ ] `RobotFaceApp.play_interactive_face()` 内の既存の視線ループロジックを削除し、共通の視線更新ロジックを利用するように変更する。
- [ ] `RobotFaceApp.main()` および `RobotFaceApp.play_interactive_face()` のループ内で、`self._handle_gaze_update()` を常に呼び出すようにする。
- [ ] `GAZE_WIDTH` を廃止し、`_gaze_width_range_min`, `_gaze_width_range_max` を使用するように `_handle_gaze_update` を修正する。
- [ ] 各状態遷移や重要な処理にデバッグログを追加する。
- [ ] すべてのモードで動作確認を行う。
