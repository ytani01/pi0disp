# `tests/test_01_disp_base.py` テストコード改善計画

以前の `Plan3.md` がテストプログラムの範囲を超えていたため却下されたことを踏まえ、今回は `tests/test_01_disp_base.py` のテストコード自体に限定した改善案を提案します。

現在のテストコードは既に高品質で明確ですが、テストインスタンスの生成方法に若干の重複が見られます。これをヘルパーメソッドでカプセル化することで、テストメソッドの記述をより簡潔にし、可読性を高めます。

## 1. `DispBase` インスタンス生成のためのヘルパーメソッド導入

`TestDispBase` クラス内に、`DispBase` インスタンスを生成するためのヘルパーメソッド `_create_disp_base_instance` を導入します。このメソッドは、`DispBase` コンストラクタへの共通の引数パターンをカプセル化し、各テストメソッドでの `DispBase` のインスタンス化を簡潔にします。

-   **`_create_disp_base_instance` ヘルパーメソッドの追加:**
    ```python
        def _create_disp_base_instance(self, size=None, rotation=None, debug=False):
            """
            テスト用のDispBaseインスタンスを生成するヘルパーメソッド。
            必要に応じてデフォルト値を使用し、setUpで設定されたモックを使用する。
            """
            if size is None:
                size = self.default_size
            if rotation is None:
                raise ValueError("rotation must be specified")
            return DispBase(size, rotation, debug)
    ```
    （注意: `DispBase` コンストラクタのシグネチャは、現在の `def __init__(self, size: dict, rotation, debug=False):` を維持します。）

## 2. 全テストメソッドの修正

`DispBase` をインスタンス化するすべてのテストメソッドを、新しく導入した `_create_disp_base_instance` ヘルパーメソッドを使用するように修正します。これにより、各テストメソッドのボディが簡潔になります。

対象となるテストメソッドは以下の通りです。

-   `test_init_success`
-   `test_init_pigpio_connection_error`
-   `test_init_display`
-   `test_set_rotation_to_90`
-   `test_set_rotation_to_0`
-   `test_display_resizes_image`
-   `test_display_with_correct_size_image`
-   `test_close_calls_pi_stop_when_connected`
-   `test_close_does_not_call_pi_stop_when_not_connected`

**リファクタリング例 (`test_init_success`):**

```python
    def test_init_success(self):
        """インスタンス化が成功するケースのテスト"""
        # setUpでデフォルトのpi_mockがセットアップされている
        disp_base = self._create_disp_base_instance(
            size=self.default_size, rotation=self.default_rotation, debug=False
        )
        # ... アサーション ...
```

**リファクタリング例 (`test_init_display`):**

```python
    def test_init_display(self):
        """init_displayが警告ログを出すことをテスト"""
        mock_logger = mock.Mock()
        self.mock_logger_getter.return_value = mock_logger

        disp_base = self._create_disp_base_instance(rotation=0) # sizeはデフォルト
        disp_base.init_display()

        mock_logger.warning.assert_called_once_with(
            "Please override this method."
        )
```

この計画により、テストコードの内部構造がさらに整理され、将来的なテストの追加や変更が容易になります。
