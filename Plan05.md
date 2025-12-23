# `samples/robot_face_animation3.py` 改造計画書

## 1. 目的

`samples/robot_face_animation2.py` をベースに、コマンドライン引数による表情指定から `input()` 関数によるインタラクティブな表情操作へ変更する。これにより、実行中にリアルタイムで表情を変化させられるようにする。

## 2. 改造ファイル

- **コピー元:** `samples/robot_face_animation2.py`
- **コピー先:** `samples/robot_face_animation3.py`

## 3. 改造内容

### 3.1. コマンドライン引数の廃止と `input()` による入力へ変更

`main` 関数の `click` デコレータ `@click.argument('faces', nargs=-1)` を削除し、`mood` 引数を復活させるか、あるいは完全に `input()` ベースのループにするかを検討する。
今回は、完全に `input()` ベースとし、`main` 関数の `faces` 引数を削除します。
`main` 関数内で無限ループを設け、ユーザーからの入力を `input("顔の記号 (例: _O_O, qで終了): ")` で受け取るように変更します。

### 3.2. 入力文字列のパースと表情の適用

ユーザーが入力した文字列を `FaceStateParser` でパースし、得られた `FaceState` オブジェクトを `RobotFace` のターゲット状態として設定します。

### 3.3. 表示間隔とキョロキョロ動作の維持

ユーザーが入力した表情は、`samples/robot_face_animation2.py` と同様に、5秒間表示し、その間に目がランダムにキョロキョロする動作を維持します。

### 3.4. 終了条件

ユーザーが `q` や空文字列などの特定の入力をした際に、アプリケーションが終了するようにします。

## 4. `main` 関数の擬似コード

```python
@click.command(__file__.split("/")[-1])
@click_common_opts(__version__)
def main(ctx, debug): # faces引数は削除
    """Main."""
    __log = get_logger(__name__, debug)

    app = None
    try:
        output_device = create_output_device(debug=debug)
        parser = FaceStateParser() # parserをここで初期化

        # RobotFaceAppの初期化
        app = RobotFaceApp(
            output_device,
            320,  # SCREEN_WIDTH
            240,  # SCREEN_HEIGHT
            "black",  # BG_COLOR
            debug=debug,
            # face_sequence はここでは渡さない
            # init_mood は必要であればデフォルト値 'neutral' を渡す
        )

        while True:
            # ユーザーからの入力を受け取る
            user_input = input("顔の記号 (例: _O_O, qで終了): ").strip()
            if user_input.lower() == 'q' or not user_input:
                break # 終了

            try:
                # 入力をパースしてFaceStateを生成
                target_face_state = parser.parse_face_string(user_input)
                
                # RobotFaceAppにターゲットの状態を設定し、アニメーションを開始
                # RobotFaceAppのmainメソッドを直接呼ぶのではなく、
                # アニメーション処理をappオブジェクト内で実行する新しいメソッドを作成するか、
                # mainメソッドを汎用的にするか検討が必要。
                # ここではRobotFaceAppに新しいメソッド `display_face(FaceState)` を仮定する。
                app.display_face(target_face_state)

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
    1.  `main` 関数の `click` デコレータから `@click.argument("faces", nargs=-1)` を削除する。
    2.  `main` 関数のシグネチャから `faces` 引数を削除する。
    3.  `main` 関数内に `FaceStateParser` のインスタンスを作成する。
    4.  `RobotFaceApp` のコンストラクタ呼び出しから `face_sequence` 引数を削除する。`init_mood` 引数は必要に応じて `neutral` などのデフォルト値を設定する。
    5.  `main` 関数内に `while True:` ループを実装し、`input()` 関数でユーザー入力を受け取る。
    6.  ユーザー入力が `q` または空文字列の場合、ループを抜けて終了する。
    7.  ユーザー入力が存在する場合、`FaceStateParser.parse_face_string()` で `FaceState` オブジェクトを生成する。
    8.  `RobotFaceApp` に、生成された `FaceState` オブジェクトを引数として受け取り、5秒間のアニメーション（目のキョロキョロ動作を含む）を実行する新しいメソッド（例: `play_interactive_face(self, target_state: FaceState)`) を追加する。
    9.  `RobotFaceApp.main` メソッドは、この新しいインタラクティブモードでは呼び出されないため、`RobotFaceApp.main` メソッドのロジックは既存のランダムモードとシーケンスモードのみをサポートするように維持するか、インタラクティブモード用のロジックと統合するかを検討する。今回は`play_interactive_face`を追加し、`main`関数からこのメソッドを呼び出す形とする。
3.  `mise run lint` を実行し、構文エラーやスタイル違反がないか確認する。
4.  手動で動作確認を行う。
    ```bash
    uv run samples/robot_face_animation3.py
    ```
    プロンプトが表示され、入力した顔の記号に基づいて表情が変化し、5秒間目がキョロキョロする挙動を確認する。
5.  `git add samples/robot_face_animation3.py` を実行する。
6.  `git commit -m "feat: Add interactive face control via input()"` でコミットする。
