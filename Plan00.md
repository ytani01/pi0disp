# samples/robot_face0.py の役割分担明確化計画

## 目的
`samples/robot_face_animation.py` のリファクタリング版として `samples/robot_face0.py` を新規作成し、`main` 関数と `RobotFaceApp` クラスの役割を明確化する。`main` 関数はコマンド引数の処理に専念し、アプリケーションの初期化および主要な動作ロジックは `RobotFaceApp` が担当するように変更する。既存の `samples/robot_face_animation.py` は変更しない。

## 修正計画

### 1. 新規ファイル `samples/robot_face0.py` の作成と初期化
*   `samples/robot_face_animation.py` の現在の内容を `samples/robot_face0.py` としてコピーする。

### 2. `RobotFaceApp.__init__` メソッドの拡張
`main` 関数で行っていた、アプリケーションの初期化に関する以下のロジックを `RobotFaceApp.__init__` メソッド内に移動させる。

*   **モード設定ロジックの移動**:
    *   `main` 関数の `selected_mode` を決定するロジック (`random` や `faces` 引数に基づいた `RandomMode`, `SequenceMode`, `InteractiveMode` のインスタンス化) を `RobotFaceApp.__init__` 内に移動する。
    *   `RobotFaceApp` のコンストラクタは、`random_mode_enabled: bool` と `face_sequence_cli_args: list[str] | None` の引数を受け取るように変更する。
    *   `mode: FaceMode` 引数は `RobotFaceApp.__init__` から削除する。

*   **`FaceConfig` 作成ロジックの移動**:
    *   `main` 関数で行っていた `FaceConfig` のインスタンス作成ロジックを `RobotFaceApp.__init__` 内に移動する。
    *   `RobotFaceApp` のコンストラクタは、`face_config: FaceConfig` 引数を受け取るように変更（既存）。

*   **依存性注入ロジックの移動**:
    *   `selected_mode` (`RandomMode`, `SequenceMode`, `InteractiveMode` のいずれか) に `app.face`, `app.parser`, `app.render_frame` を注入するロジックを `RobotFaceApp.__init__` 内に移動する。
    *   この際、`selected_mode` が `RobotFaceApp.__init__` 内で作成されるように変更するため、`selected_mode` のコンストラクタにこれらの依存関係を直接渡すか、`RobotFaceApp` の属性として設定する方法を検討する。今回は `RobotFaceApp` の属性として設定し、各 `FaceMode` のコンストラクタに `RobotFaceApp` のインスタンスそのものを渡す形に変更する（これにより、`FaceMode` が必要な属性にアクセスできるようになる）。

### 3. `main` 関数の簡素化
`main` 関数は、以下の処理のみを実行するように簡素化する。

*   `click` 引数 (`faces`, `random`, `debug`) のパース。
*   `create_output_device` の呼び出し。
*   `RobotFaceApp` のインスタンス生成（この際、`random` と `faces` の値を `RobotFaceApp` のコンストラクタに渡す）。
*   `app.main()` の呼び出し。

## 実施詳細 (Phase 1)

### タスク 1: 新規ファイル `samples/robot_face0.py` の作成

- [ ] `samples/robot_face_animation.py` の内容を `samples/robot_face0.py` にコピーして新規作成する。
- [ ] `samples/robot_face0.py` の `click.command` デコレータの引数を `robot_face0.py` に修正する。

### タスク 2: `RobotFaceApp.__init__` メソッドの修正 (`samples/robot_face0.py`)

- [ ] `samples/robot_face0.py` 内の `RobotFaceApp.__init__` のシグネチャを以下のように変更する:
    ```python
    def __init__(
        self,
        output: DisplayOutput,
        screen_width: int,
        screen_height: int,
        bg_color: str,
        random_mode_enabled: bool = False,
        face_sequence_cli_args: list[str] | None = None,
        face_config: FaceConfig = FaceConfig(),
        debug: bool = False,
    ) -> None:
    ```
- [ ] `samples/robot_face0.py` 内の `RobotFaceApp.__init__` 内で `selected_mode` を決定するロジックを実装する:
    ```python
    if random_mode_enabled:
        self.current_mode = RandomMode(...)
    elif face_sequence_cli_args:
        self.current_mode = SequenceMode(...)
    else:
        self.current_mode = InteractiveMode(...)
    ```
    （`RandomMode`, `SequenceMode`, `InteractiveMode` のコンストラクタには `robot_face=self.face`, `parser=self.parser`, `animation_config=self.face_config.animation_config`, `app_render_frame_callback=self.render_frame` などを渡す）
- [ ] `samples/robot_face0.py` 内の `RobotFaceApp.__init__` 内で、`selected_mode` への依存性注入ロジックを削除する（コンストラクタで直接渡す形にするため）。

### タスク 3: `main` 関数の修正 (`samples/robot_face0.py`)

- [ ] `samples/robot_face0.py` 内の `main` 関数から `FaceMode` のインスタンス化ロジックを削除する。
- [ ] `samples/robot_face0.py` 内の `main` 関数から `FaceConfig` のインスタンス作成ロジックを削除する。
- [ ] `samples/robot_face0.py` 内の `main` 関数から `selected_mode` への依存性注入ロジックを削除する。
- [ ] `samples/robot_face0.py` 内の `RobotFaceApp` のインスタンス化の際に、`random_mode_enabled` と `face_sequence_cli_args` （または `faces` と `random`）を `RobotFaceApp` のコンストラクタに渡すように修正する。

## 実施詳細 (Phase 2)

### タスク 4: `FaceMode` サブクラスのコンストラクタ修正 (`samples/robot_face0.py`)

- [ ] `samples/robot_face0.py` 内の `RandomMode`, `SequenceMode`, `InteractiveMode` のコンストラクタの引数を修正し、`robot_face`, `parser`, `animation_config`, `app_render_frame_callback` などを直接受け取るようにする。
- [ ] `samples/robot_face0.py` 内の `FaceMode` のコンストラクタも必要に応じて修正する。

### タスク 5: テストコードの作成と修正

- [ ] `tests/test_51_sample_robot_face_animation.py` の内容を `tests/test_51_sample_robot_face0.py` にコピーして新規作成する。
- [ ] `tests/test_51_sample_robot_face0.py` のインポートパスを `samples.robot_face_animation` から `samples.robot_face0` に修正する。
- [ ] `tests/test_51_sample_robot_face0.py` の `TestRobotFaceApp` フィクスチャと `TestMainCLI` のテストメソッドを、`RobotFaceApp` のコンストラクタの変更に合わせて修正する。
    *   `RobotFaceApp` のインスタンス化時に `mode` 引数を渡す代わりに、`random_mode_enabled` と `face_sequence_cli_args` を渡すように変更する。

## 評価基準

*   `samples/robot_face0.py` が新規作成され、`robot_face_animation.py` は変更されていないこと。
*   `samples/robot_face0.py` 内の `main` 関数がコマンド引数の処理と `RobotFaceApp` の呼び出しにのみ専念していること。
*   `samples/robot_face0.py` 内の `RobotFaceApp` がアプリケーションの初期化と主要なロジックを適切にカプセル化していること。
*   既存の機能が維持されていること（`samples/robot_face_animation.py` の機能）。
*   `tests/test_51_sample_robot_face0.py` が新規作成され、すべてのテストがパスすること。
*   Mypy の型チェックでエラーが発生しないこと。