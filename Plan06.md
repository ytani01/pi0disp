# `samples/robot_face_animation3.py` 改造計画書 (改訂版)

## 1. 目的

`samples/robot_face_animation2.py` をベースに、コマンドライン引数による表情指定は維持しつつ、引数が指定されなかった場合に `input()` 関数によるインタラクティブな表情操作へフォールバックする機能を追加する。これにより、柔軟な操作性を提供する。

## 2. 改造ファイル

- **コピー元:** `samples/robot_face_animation2.py`
- **コピー先:** `samples/robot_face_animation3.py`

## 3. 改造内容

### 3.1. コマンドライン引数の維持と `input()` によるインタラクティブモードへのフォールバック

*   `main` 関数の `click` デコレータ `@click.argument('faces', nargs=-1)` はそのまま維持する。
*   `main` 関数内で、`faces` 引数に値が**ない**場合（タプルが空の場合）にのみ、`input()` ループによるインタラクティブモードに移行する。
*   `faces` 引数に値がある場合（コマンドラインで表情が指定された場合）は、既存のシーケンス再生モードで動作する。

### 3.2. 入力文字列のパースと表情の適用（インタラクティブモード時）

インタラクティブモードでは、ユーザーが `input("顔の記号 (例: _O_O, qで終了): ")` で入力した文字列を `FaceStateParser` でパースし、得られた `FaceState` オブジェクトを `RobotFaceApp` に渡して表示する。

### 3.3. 表示間隔とキョロキョロ動作の維持

インタラクティブモードでユーザーが入力した表情は、5秒間表示し、その間に目がランダムにキョロキョロする動作を維持する。これは `RobotFaceApp` の `play_interactive_face` メソッド（後述）に集約する。

### 3.4. 終了条件（インタラクティブモード時）

ユーザーが `q` や空文字列などの特定の入力をした際に、インタラクティブモードのループを終了する。

## 4. `main` 関数の擬似コード

```python
@click.command(__file__.split("/")[-1])
@click.argument('faces', nargs=-1) # 引数を維持
@click_common_opts(__version__)
def main(ctx, faces, debug): # faces引数を維持
    """Main."""
    __log = get_logger(__name__, debug)
    __log.info("faces=%s", faces)

    app = None
    try:
        output_device = create_output_device(debug=debug)
        parser = FaceStateParser() # parserをここで初期化

        # RobotFaceAppの初期化 (face_sequence は後で設定する)
        app = RobotFaceApp(
            output_device,
            320,  # SCREEN_WIDTH
            240,  # SCREEN_HEIGHT
            "black",  # BG_COLOR
            debug=debug,
            init_mood="neutral" # デフォルト mood を設定
        )

        if faces:
            # コマンドライン引数がある場合: シーケンス再生モード
            face_sequence = [parser.parse_face_string(f) for f in faces]
            app.face_sequence = face_sequence # appにシーケンスを設定
            app.main() # 既存のmainメソッドでシーケンス再生
        else:
            # コマンドライン引数がない場合: インタラクティブモード
            while True:
                user_input = input("顔の記号 (例: _O_O, qで終了): ").strip()
                if user_input.lower() == 'q' or not user_input:
                    break # 終了

                try:
                    target_face_state = parser.parse_face_string(user_input)
                    # RobotFaceAppに新しいメソッド `play_interactive_face(FaceState)` を仮定する
                    app.play_interactive_face(target_face_state)

                except ValueError as e:
                    __log.error(f"入力エラー: {e}")
                except Exception as e:
                    __log.error(errmsg(e))

    except KeyboardInterrupt:
        print("\nEnd.")
    except Exception as e:
        __log.error(errmsg(e))
    finally:
        if app:
            app.end()
```

## 5. 実装方針

1.  `cp samples/robot_face_animation2.py samples/robot_face_animation3.py` を実行する。
2.  `samples/robot_face_animation3.py` を開き、以下の点を修正する。
    1.  `main` 関数の `click` デコレータ `@click.argument("faces", nargs=-1)` はそのまま維持し、シグネチャも `def main(ctx, faces, debug):` のままにする。
    2.  `main` 関数内に `FaceStateParser` のインスタンスを作成する。
    3.  `RobotFaceApp` のコンストラクタ呼び出しで `init_mood="neutral"` のようにデフォルト `mood` を設定する。`face_sequence` は最初は `None` のままにしておく。
    4.  `main` 関数内で `if faces:` ブロックを追加し、コマンドライン引数がある場合は `app.face_sequence` にパースした `FaceState` のリストを設定し、`app.main()` を呼び出す。
    5.  `else:` ブロックに `while True:` ループを実装し、`input()` 関数でユーザー入力を受け取るインタラクティブモードのロジックを実装する。
    6.  `RobotFaceApp` に、生成された `FaceState` オブジェクトを引数として受け取り、5秒間のアニメーション（目のキョロキョロ動作を含む）を実行する新しいメソッド `play_interactive_face(self, target_state: FaceState)` を追加する。このメソッドは `RobotFaceApp.main` の `if self.face_sequence:` ブロックのロジック（表情設定とキョロキョロ動作）を再利用する形にする。
    7.  `RobotFaceApp.main` メソッドの `if self.face_sequence:` ブロックのロジックを、新しく追加した `play_interactive_face` を呼び出すように修正し、重複を避ける。
3.  `mise run lint` を実行し、構文エラーやスタイル違反がないか確認する。
4.  手動で動作確認を行う。
    *   コマンドライン引数あり: `uv run samples/robot_face_animation3.py /o_o _O_O` (シーケンス再生モード)
    *   コマンドライン引数なし: `uv run samples/robot_face_animation3.py` (インタラクティブモード)
5.  `git add samples/robot_face_animation3.py` を実行する。
6.  `git commit -m "feat: Add interactive face control via input() fallback"` でコミットする。
