# `tests/test_01_disp_base.py` 再改善計画

`tests/test_01_disp_base.py` の可読性と堅牢性をさらに向上させるため、以下のリファクタリング案を提案します。

現在のテストコードは、`DispBase` のインスタンス化が `MagicMock` のデフォルトの挙動に暗黙的に依存しており、セットアップの意図が不明確になる可能性があります。そこで、テストの前提条件をより明確にするための改善を行います。

## 1. `pigpio` モック設定のヘルパーメソッド導入

`pigpio` のモック設定をカプセル化するヘルパーメソッド `_setup_pi_mock` を導入します。
このメソッドは、`pigpio.pi()` が返すモックインスタンスを作成し、その `connected` 属性を引数で設定できるようにします。
これにより、各テストでのモックのセットアップが簡潔かつ明確になります。

```python
    def _setup_pi_mock(self, connected=True):
        """pigpioモックをセットアップするヘルパー"""
        mock_pi_instance = mock.Mock()
        mock_pi_instance.connected = connected
        self.mock_pigpio.pi.return_value = mock_pi_instance
        return mock_pi_instance
```

## 2. 全テストメソッドのリファクタリング

`_setup_pi_mock` ヘルパーメソッドを利用して、`DispBase` をインスタンス化するすべてのテストメソッドをリファクタリングします。
これにより、`DispBase` がインスタンス化可能であるための前提条件 (`pi.connected` が `True` であることなど) が、各テストコードで明示的に示されるようになります。

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

### リファクタリング例 (`test_init_success`)

```python
    def test_init_success(self):
        """インスタンス化が成功するケースのテスト"""
        self._setup_pi_mock(connected=True)

        disp_base = DispBase(
            size=self.default_size,
            rotation=self.default_rotation,
            debug=False,
        )

        self.mock_pigpio.pi.assert_called_once()
        # ...以下のアサーションは同様...
```

### リファクタリング例 (`test_close_does_not_call_pi_stop_when_not_connected`)

```python
    def test_close_does_not_call_pi_stop_when_not_connected(self):
        """connected=Falseの場合にcloseがpi.stop()を呼び出さないかをテスト"""
        mock_pi_instance = self._setup_pi_mock(connected=True)

        disp_base = DispBase(self.default_size, 0)
        disp_base.pi.connected = False  # 実行時の状態を動的に変更

        disp_base.close()
        mock_pi_instance.stop.assert_not_called()
```
