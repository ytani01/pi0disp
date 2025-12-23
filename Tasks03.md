# `samples/robot_face_animation.py` インタラクティブ機能実装タスクリスト (詳細版)

- [x] git checkout -b feature/Tasks03
- [x] **`FaceStateParser` の実装:** `samples/robot_face_animation.py` の `FaceState` クラスの直後に `FaceStateParser` クラスを定義する。
- [x] `FaceStateParser` 内に `EYE_MAP`, `MOUTH_MAP`, `BROW_MAP` の3つのクラス変数を定義する。
- [x] `FaceStateParser` に `parse_face_string(self, face_str: str) -> FaceState` メソッドを実装する。このメソッドは文字列をパースして `FaceState` オブジェクトを返す。
- [x] **`RobotFace` クラスの修正:** `set_target_mood` の下に `set_target_state(self, state: FaceState)` メソッドを追加する。
- [x] **`RobotFaceApp` クラスの修正(1/2):** コンストラクタの引数に `init_mood: str` と `face_sequence: list[FaceState] | None = None` を追加し、インスタンス変数として保存する。
- [x] **`RobotFaceApp` クラスの修正(2/2):** `main` メソッドを修正し、`self.face_sequence` が存在する場合はシーケンスをループ再生し、存在しない場合は既存のランダム再生を行うロジックを実装する。
- [x] `mise run lint` を実行し、ここまでの変更で発生したリンティングエラーを修正する。
- [x] **`main` 関数の修正(1/2):** `@click.command` の下にある `@click.argument("mood", ...)` を `@click.argument("faces", nargs=-1)` に変更する。
- [x] **`main` 関数の修正(2/2):** `faces` 引数の有無で処理を分岐するロジックを実装する。`faces` があれば `FaceStateParser` でパースして `RobotFaceApp` に `face_sequence` を渡し、なければ従来の `mood` を使う処理（フォールバック）を実装する。
- [x] `mise run lint` を実行し、リンティングエラーを修正する。
- [x] `mise run test` を実行し、既存のテストが壊れていないことを確認する。
- [x] 手動で動作確認を行う (`uv run samples/robot_face_animation.py /o_o _O_O \^v^`)。
- [x] `git add .`
- [x] `git commit -m "feat: Add interactive face control via string arguments"`