# `samples/robot_face_animation3.py` 改造タスクリスト (詳細版)

- [x] git checkout -b feature/Tasks06
- [x] `cp samples/robot_face_animation2.py samples/robot_face_animation3.py` を実行する。
- [x] `samples/robot_face_animation3.py` を開き、`RobotFaceApp` クラスに `play_interactive_face(self, target_state: FaceState)` メソッドを追加する。このメソッドは `RobotFaceApp.main` の `if self.face_sequence:` ブロックのロジック（表情設定とキョロキョロ動作）をコピーして、`target_state` を受け取るように修正したものにする。
- [x] `samples/robot_face_animation3.py` を開き、`RobotFaceApp.main` メソッドの `if self.face_sequence:` ブロックのロジックを、追加した `play_interactive_face` を呼び出すように修正し、重複を避ける。
- [x] `samples/robot_face_animation3.py` を開き、`main` 関数の `click` デコレータ `@click.argument("faces", nargs=-1)` はそのまま維持し、シグネチャも `def main(ctx, faces, debug):` のままにする。
- [x] `samples/robot_face_animation3.py` を開き、`main` 関数内に `FaceStateParser` のインスタンスを作成する。
- [x] `samples/robot_face_animation3.py` を開き、`main` 関数内の `RobotFaceApp` のコンストラクタ呼び出しで `init_mood="neutral"` のようにデフォルト `mood` を設定する。`face_sequence` は最初は `None` のままにしておく。
- [x] `samples/robot_face_animation3.py` を開き、`main` 関数内で `if faces:` ブロックを追加し、コマンドライン引数がある場合は `app.face_sequence` にパースした `FaceState` のリストを設定し、`app.main()` を呼び出す。
- [x] `samples/robot_face_animation3.py` を開き、`main` 関数内の `else:` ブロックに `while True:` ループを実装し、`input()` 関数でユーザー入力を受け取るインタラクティブモードのロジックを実装する。
- [x] `mise run lint` を実行し、リンティングエラーを修正する。
- [x] `mise run test` を実行し、既存のテストが壊れていないことを確認する。
- [x] 手動で動作確認を行う。
    *   コマンドライン引数あり: `uv run samples/robot_face_animation3.py -d '/o_o' '_O_O'` (シーケンス再生モード。`-d` オプションでデバッグログを確認)
    *   コマンドライン引数なし: `uv run samples/robot_face_animation3.py -d` (インタラクティブモード。`-d` オプションでデバッグログを確認)
- [x] `git add samples/robot_face_animation3.py`
- [x] `git commit -m "feat: Add interactive face control via input() fallback"`
