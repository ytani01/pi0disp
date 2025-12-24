# Plan01.md: `samples/robot_face.py` 新規作成計画

## 概要

`samples/robot_face_animation.py` ファイルをベースとし、その機能をリファクタリングした `samples/robot_face.py` を新規作成します。新しいファイルでは、グローバルな `main` 関数の責務をコマンド引数処理のみに限定し、アプリケーションのコアロジックおよび初期化処理を `RobotFaceApp` クラスに完全に委譲します。これにより、コードの見通しを良くし、保守性と拡張性を向上させます。

## 目標

- `RobotFaceApp` クラスをアプリケーションの主要なエントリポイントとする。
- `main` 関数は `RobotFaceApp` のインスタンス化と実行を調整する最小限の役割に留める。
- `FaceMode` サブクラスへの依存性注入の問題を解消し、よりクリーンな設計にする。

## 詳細計画

### ステップ 1: `RobotFaceApp.__init__` に `FaceConfig` の初期化を移管する

- **現状**: `main` 関数内で `FaceConfig` オブジェクトが明示的に作成され、`RobotFaceApp` のコンストラクタに渡されている。
- **変更点**: `samples/robot_face.py` に、上記機能を持つ `RobotFaceApp` の新しい実装を作成し、その `__init__` メソッド内で `FaceConfig` オブジェクトを初期化する。

### ステップ 2: `RobotFaceApp.__init__` に `create_output_device` の呼び出しを移管する

- **現状**: `main` 関数内で `create_output_device` が呼び出され、その結果が `RobotFaceApp` のコンストラクタに渡されている。
- **変更点**: `samples/robot_face.py` に、上記機能を持つ `RobotFaceApp` の新しい実装を作成し、その `__init__` メソッド内で `create_output_device` を呼び出し、出力デバイスを初期化する。

### ステップ 3: `RobotFaceApp.__init__` でモード選択ロジックを実装し、`FaceMode` インスタンスを適切に初期化する

- **現状**: `main` 関数内でコマンドライン引数に基づいて `FaceMode` のサブクラスが選択され、初期化されている。この際、`robot_face`, `parser`, `app_render_frame_callback` は仮の値で渡され、後で `main` 関数内で「暫定的な措置」として注入されている。
- **変更点**: `samples/robot_face.py` に、上記機能を持つ `RobotFaceApp` の新しい実装を作成し、その `__init__` メソッド内で、`mode_name` に基づいて適切な `FaceMode` サブクラスのインスタンスを生成し、`self.current_mode` に割り当てる。`FaceMode` サブクラスのコンストラクタには、`self.face`, `self.parser`, `self.render_frame` を直接渡す。

### ステップ 4: `FaceMode` サブクラスのコンストラクタから仮の引数 (`robot_face`, `parser`, `app_render_frame_callback`) を削除し、`RobotFaceApp` 内で生成した実際のオブジェクトを渡すように修正する

- **現状**: `FaceMode` およびそのサブクラスの `__init__` メソッドのシグネチャに `RobotFace | None`, `FaceStateParser | None`, `Callable[[], None] | None` のように `None` を許容する型ヒントが使用されている。
- **変更点**: `samples/robot_face.py` に、上記機能を持つ `FaceMode` クラスおよびそのサブクラス (`RandomMode`, `SequenceMode`, `InteractiveMode`) の新しい実装を作成し、コンストラクタから仮の引数 (`robot_face`, `parser`, `app_render_frame_callback`) を削除する。これらの引数は必須となり、`None` チェックが不要になる。

### ステップ 5: `main` 関数を簡素化し、コマンドライン引数のパース、`RobotFaceApp` のインスタンス生成、`app.main()` の呼び出しのみを行うようにする

- **現状**: `main` 関数が `output_device` の生成、`FaceMode` の選択と初期化、`FaceConfig` の生成、`RobotFaceApp` の初期化、および `FaceMode` インスタンスへの依存性注入まで行っている。
- **変更点**: `samples/robot_face.py` に新しい `main` 関数を作成する。この `main` 関数では、`click` によってパースされたコマンドライン引数を受け取り、これらの引数から適切な `mode_name` と `faces_arg` を導出し、`RobotFaceApp` のインスタンスを生成する。最終的に `app = RobotFaceApp(...)` と `app.main()` の呼び出しのみが残るようにする。

## 懸念事項

- `FaceMode` の `__init__` メソッドのシグネチャ変更により、現在 `None` を許容している箇所でコンパイルエラーが発生する可能性がある。これはステップ4で対処する。
- 依存性注入のパターンが変更されるため、各クラス間の結合度が適切に保たれるかを確認する必要がある。

## 完了基準

- 新しいファイル `samples/robot_face.py` が作成されていること。
- `samples/robot_face.py` 内の `main` 関数がコマンドライン引数処理と `RobotFaceApp` の初期化・実行のみに限定されていること。
- `samples/robot_face.py` 内の `RobotFaceApp` がアプリケーションの初期化、モード設定、オブジェクト生成、依存性管理を全て担当していること。
- `samples/robot_face.py` 内の `FaceMode` サブクラスが `RobotFaceApp` から必要な依存性を受け取る際、`None` チェックが不要になっていること。
- `samples/robot_face.py` が正常に動作すること。

## 次のステップ

上記計画に基づき、`samples/robot_face_animation.py` の内容をベースとして、新しいファイル `samples/robot_face.py` を作成し、コードの変更を実施します。