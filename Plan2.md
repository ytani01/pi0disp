# `tests/test_01_disp_base.py` 最終改善計画

`tests/test_01_disp_base.py` のテストスイートをさらに洗練させ、より標準的なユニットテストのパターンに準拠させるための最終改善案を提案します。

現在のテストコードは、各テストメソッド内で `_setup_pi_mock` ヘルパーを呼び出していますが、ほとんどのテストが `pigpio` への接続が成功する「ハッピーパス」を前提としています。この共通のセットアップを `setUp` メソッドに集約することで、テストコードの重複を減らし、各テストの意図をより明確にすることができます。

## 1. デフォルトのモックセットアップを `setUp` に移動

`setUp` メソッド内で、デフォルトの `pigpio` 接続成功状態をセットアップします。

-   `setUp` メソッドを修正し、`self._setup_pi_mock(connected=True)` を呼び出し、返されたモックインスタンスを `self.mock_pi_instance` に保存します。
-   これにより、各テストメソッドは、デフォルトで `pigpio` が接続された状態から開始されるようになります。

**修正後の `setUp` メソッド:**
```python
    def setUp(self):
        """各テストの前に実行されるセットアップ"""
        # ... 既存のセットアップ ...
        self.mock_pigpio = self.patcher_pigpio.start()
        self.mock_logger_getter = self.patcher_logger.start()

        self.addCleanup(self.patcher_pigpio.stop)
        self.addCleanup(self.patcher_logger.stop)

        # デフォルトで接続成功状態のpiモックをセットアップ
        self.mock_pi_instance = self._setup_pi_mock()
```

## 2. 各テストメソッドの簡素化

`setUp` でデフォルトのセットアップが行われるため、各テストメソッドから `_setup_pi_mock()` の呼び出しを削除します。

-   **ハッピーパスを前提とするテスト:**
    -   `test_init_success`
    -   `test_init_display`
    -   `test_set_rotation_to_90`
    -   `test_set_rotation_to_0`
    -   `test_display_resizes_image`
    -   `test_display_with_correct_size_image`
    -   `test_close_calls_pi_stop_when_connected`
    -   `test_close_does_not_call_pi_stop_when_not_connected`
    これらのテストから `_setup_pi_mock()` の行を削除します。`test_close_...` メソッドでは、`setUp` で作成された `self.mock_pi_instance` を直接利用するようにします。

-   **例外的なケースをテストするメソッド:**
    -   `test_init_pigpio_connection_error`: このテストは接続失敗をテストするため、`setUp` のデフォルト設定を上書きする `self._setup_pi_mock(connected=False)` の呼び出しを維持します。これにより、このテストが例外的なケースを扱っていることが明確になります。

**リファクタリング例 (`test_init_success`):**
```python
    def test_init_success(self):
        """インスタンス化が成功するケースのテスト"""
        # setUpでデフォルトのpi_mockがセットアップされている
        disp_base = DispBase(
            size=self.default_size,
            rotation=self.default_rotation,
            debug=False,
        )
        # ... アサーション ...
```

**リファクタリング例 (`test_close_calls_pi_stop_when_connected`):**
```python
    def test_close_calls_pi_stop_when_connected(self):
        """connected=Trueの場合にcloseがpi.stop()を呼び出すかをテスト"""
        # setUpでデフォルトのpi_mockがセットアップされている
        disp_base = DispBase(self.default_size, 0)
        disp_base.close()
        self.mock_pi_instance.stop.assert_called_once()
```

この計画により、テストコードの可読性と保守性がさらに向上します。
