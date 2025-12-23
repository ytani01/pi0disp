# `samples/robot_face_animation3.py` リファクタリングタスクリスト (詳細版)

- [x] git checkout -b feature/Tasks07
- [x] `samples/robot_face_animation3.py` 内で、**設定セクション**をファイルの先頭近くに新設し、`MOODS`、`FaceStateParser` のマッピング (`BROW_MAP`, `EYE_MAP`, `MOUTH_MAP`)、`RobotFace` の `LAYOUT`, `COLORS` を移動・集約する。
    - 具体的には、`FaceState` クラスの直後に`MOODS`を定義する。
    - `FaceStateParser`クラスの`BROW_MAP`, `EYE_MAP`, `MOUTH_MAP`はクラス定数として維持し、`FaceStateParser`クラス自体を移動する。
    - `RobotFace`クラスの`LAYOUT`と`COLORS`はクラス定数として維持し、`RobotFace`クラス自体を移動する。
- [x] `RobotFace` クラスから `MOODS` 辞書を削除し、`__init__` メソッドから `mood` 引数を削除する。`set_target_mood` メソッドも削除する。
    - `RobotFace` の `__init__` メソッドのシグネチャを `__init__(self, initial_state: FaceState, size=240, debug=False)` に変更する。
- [x] `RobotFaceApp` クラスの `__init__` メソッドに `all_moods: dict[str, FaceState]` 引数を追加し、`MOODS` 辞書を外部から受け取るようにする。
    - `RobotFaceApp` の `__init__` メソッドのシグネチャを `__init__(self, output: DisplayOutput, screen_width: int, screen_height: int, bg_color: str, all_moods: dict[str, FaceState], init_mood: str = "neutral", face_sequence: list[FaceState] | None = None, debug=False)` に変更する。
    - `self.all_moods = all_moods` を追加する。
- [x] `RobotFaceApp` の `__init__` メソッド内で、`RobotFace` インスタンスを生成する際に、`init_mood` に対応する `FaceState` を `RobotFace` に渡すように修正する。
    - `self.face = RobotFace(self.all_moods[self.init_mood].copy(), size=face_size, debug=self.__debug)` に変更する。
- [x] `RobotFaceApp` クラスの `main` メソッド内で、ランダムな表情変更ロジックと視線変更ロジックをそれぞれ `_handle_random_mood_update`、`_handle_gaze_update` というプライベートヘルパーメソッドに分割する。
    - `_handle_random_mood_update(self)`: 表情変更ロジックをカプセル化する。
    - `_handle_gaze_update(self)`: 視線変更ロジックをカプセル化する。
    - `main` メソッドからはこれらの補助メソッドを呼び出すようにする。
- [x] `main` 関数内の `RobotFaceApp` の初期化箇所を修正し、`MOODS` 辞書を渡すように変更する。
    - 具体的には、`app = RobotFaceApp(...)` の呼び出しで `all_moods=MOODS` を追加する。
- [x] 各クラスや関数のインポート文、および利用箇所を修正し、依存関係を解決する。
- [x] `mise run lint` を実行し、リンティングエラーを修正する。
- [x] `mise run test` を実行し、既存のテストが壊れていないことを確認する。
- [x] 手動で動作確認を行う。
    *   コマンドライン引数あり: `uv run samples/robot_face_animation3.py -d '/o_o' '_O_O'` (シーケンス再生モード。`-d` オプションでデバッグログを確認)
    *   コマンドライン引数なし: `uv run samples/robot_face_animation3.py -d` (インタラクティブモード。`-d` オプションでデバッグログを確認)
- [x] `git add samples/robot_face_animation3.py`
- [x] `git commit -m "refactor: Refactor robot_face_animation3.py to clarify roles and improve extensibility"`
