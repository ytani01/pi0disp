# Plan 7: Improve `tests/test_02_disp_spi.py`

ユーザーの要望に基づき、`tests/test_02_disp_spi.py` のコード品質を向上させるための改善案をまとめました。

## 概要

現状のテストコードは機能していますが、Pythonのベストプラクティスに反する箇所や、保守性を下げる記述が見受けられます。これらを修正し、より堅牢で読みやすいテストコードにします。

## 改善案

### 1. ミュータブルなデフォルト引数の修正 [重要]

`_create_disp_spi_instance` メソッドにおいて、辞書型 (`dict`) をデフォルト引数として使用しています。これはPythonにおけるアンチパターンであり、予期せぬ副作用（前回のテスト実行時の変更が残るなど）を引き起こす可能性があります。

- **現状**:
  ```python
  def _create_disp_spi_instance(
      self,
      size={"width": 240, "height": 320},  # <--- Mutable default argument!
      # ...
      pin={"dc": 24, "rst": 25, "bl": 23}, # <--- Mutable default argument!
      # ...
  ):
  ```
- **修正案**: デフォルト値を `None` にし、メソッド内部でデフォルト値を設定するように変更します。

### 2. テストメソッドの分割と明確化

`test_close` メソッド内で、`bl_at_close=False` の場合と `bl_at_close=True` の場合の両方をテストしています。テストメソッドは「1つのメソッドにつき1つの振る舞い」をテストするのが理想的です。

- **修正案**:
  - `test_close_with_bl_off` (または `test_close_default`)
  - `test_close_with_bl_on`
  のようにメソッドを分割します。

### 3. コンテキストマネージャテストの検証強化

`test_enter_exit_context_manager` において、`__enter__` の戻り値を受け取っていません（`_` で捨てている）。また、正しくインスタンスが返されているか検証していません。

- **修正案**: `as disp` として受け取り、`assertIsInstance(disp, DispSpi)` などの検証を追加します。

### 4. Docstringの追加

各テストメソッドに Docstring がなく、テストの意図（何を検証したいのか）が一目でわかりにくくなっています。

- **修正案**: 各テストメソッドに、日本語で簡潔な Docstring を追加します。

### 5. 型ヒントの追加

`_create_disp_spi_instance` などのヘルパーメソッドに型ヒントを追加し、可読性と開発体験（IDEの補完など）を向上させます。

## 将来的な検討事項（今回は対象外）

- **`DispBase` モックの簡素化**: 現在 `setUp` で `DispBase.__init__` をパッチし、`side_effect` で初期化処理を模倣していますが、これは `DispBase` の内部実装と強く結合しています。将来的には、より疎結合な方法（依存注入など）へのリファクタリングが望ましいです。

## 次のステップ

上記の改善案に基づき、リファクタリングを実行します。
