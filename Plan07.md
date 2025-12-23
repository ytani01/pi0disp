# `samples/robot_face_animation3.py` リファクタリング計画書 (`Plan07.md`)

## 1. 目的

`samples/robot_face_animation3.py` のコードについて、「役割分担の明確化」と「拡張性」を重視したリファクタリングを実施する。これにより、コードの可読性、保守性、再利用性を向上させ、将来的な機能追加や変更に強い構造を確立する。**ファイル分割は行わず、単一ファイル内での改善に注力する。**

## 2. 方針

1.  **関心の分離 (Separation of Concerns)**: クラス内の役割を明確にし、密結合を解消する。
2.  **設定とロジックの分離**: 設定値やマッピングデータ（例: `MOODS`, `BROW_MAP` など）をコードの特定セクションに集約し、管理しやすくする。
3.  **可読性の向上**: 長大なメソッドを補助メソッドに分割し、適切なコメントを追加する。

## 3. リファクタリング内容 (詳細)

### 3.1. クラス責任の明確化と再編成

*   **`FaceStateParser`**:
    *   `BROW_MAP`, `EYE_MAP`, `MOUTH_MAP` はクラス定数として維持する。
*   **`RobotFace`**:
    *   `MOODS` 辞書を `RobotFace` クラスの**外**に移動し、`RobotFaceApp` クラスの初期化時に渡されるようにする。これにより、`RobotFace` は描画と状態管理のみに専念し、利用可能な表情プリセットの知識は持たなくなる。
    *   `set_target_mood` メソッドを削除し、`RobotFaceApp` 側で `FaceState` オブジェクトを直接 `set_target_state` に渡すように変更する。
    *   描画に必要な `LAYOUT` や `COLORS` などの定数は `RobotFace` 内に維持する。
*   **`RobotFaceApp`**:
    *   `FaceStateParser` のインスタンスを保持し、ユーザー入力のパースを自身で行う。
    *   `MOODS` 辞書を初期化時に受け取り、ランダム表情選択やデフォルト表情設定に使用する。
    *   `play_interactive_face` メソッドは `RobotFace` の `update` および `draw` メソッドを適切に呼び出す高レベルなアニメーションロジックを担当する。
    *   `main` メソッドは、シーケンス再生とランダム再生、インタラクティブモードの全体的な流れを制御する。特に、ランダム再生モードのロジック（表情変更、視線変更）は、専用の補助メソッド（例: `_handle_random_mood_update`, `_handle_gaze_update`）に分割し、`main` メソッドの可読性を向上させる。

### 3.3. 設定の集約

*   `MOODS` 辞書、`FaceStateParser` のマッピングデータ (`BROW_MAP`, `EYE_MAP`, `MOUTH_MAP`)、`RobotFace` の `LAYOUT` および `COLORS` 定数は、ファイルの先頭近くの専用セクションに集約し、一目で設定がわかるように配置する。これにより、将来的に設定ファイルを読み込む形式への移行も容易になる。

### 3.4. ヘルパー関数の組織化

*   `lerp` 関数は `FaceState` の近く、または専用のヘルパー関数セクションに移動し、明確にする。
*   `create_output_device` 関数は、`DisplayOutput` クラス群の直後に配置し、関連性を明確にする。

## 4. 実施手順 (ハイレベル)

1.  新しいブランチ `feature/Plan07` を作成する。
2.  `samples/robot_face_animation3.py` 内で、**設定セクション**をファイルの先頭近くに新設し、`MOODS`（`RobotFace` から移動）、`FaceStateParser` のマッピング (`BROW_MAP`, `EYE_MAP`, `MOUTH_MAP`)、`RobotFace` の `LAYOUT`, `COLORS` を移動・集約する。
3.  `RobotFace` クラスから `MOODS` 辞書を削除し、`__init__` メソッドから `mood` 引数を削除する。`set_target_mood` メソッドも削除する。
4.  `RobotFaceApp` クラスの `__init__` メソッドに `moods: dict[str, FaceState]` 引数を追加し、`MOODS` 辞書を外部から受け取るようにする。
5.  `RobotFaceApp` の `__init__` メソッド内で、`RobotFace` インスタンスを生成する際に、`init_mood` に対応する `FaceState` を `RobotFace` に渡すように修正する。
6.  `RobotFaceApp.main` メソッド内のランダム再生モードのロジック（表情変更、視線変更）を、`_handle_random_mood_update`, `_handle_gaze_update` といった補助メソッドに分割する。
7.  `main` 関数内の `RobotFaceApp` の初期化箇所を修正し、`MOODS` 辞書を渡すように変更する。
8.  各クラスや関数のインポート文、および利用箇所を修正し、依存関係を解決する。
9.  `mise run lint` および `mise run test` を実行し、リンティングエラーとテストの失敗がないことを確認する。
10. 手動で動作確認を行い、リファクタリング後も機能が正常であることを確認する。
11. 変更をコミットする。