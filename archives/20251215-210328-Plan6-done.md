# `tests/test_02_disp_spi.py` の改善計画 (第2版)

## 1. モック戦略の簡素化と明確化

### 1.1 `DispBase.close` のパッチ方法の簡素化

-   現在 `setUp` で `pi0disp.disp.disp_base.DispBase.close` をパッチし、`side_effect` で `self.mock_pi_instance.stop()` を呼び出しているが、これは複雑さを増している。
-   代わりに、`DispSpi.close()` が `super().close()` を呼び出していることを直接アサートするために、`DispSpi.close` メソッド自体をパッチする。
-   `test_close` および `test_enter_exit_context_manager` で `DispSpi.close` を `patch.object` し、それが呼び出されたことをアサートする。

## 2. `_create_disp_spi_instance` ヘルパーの最適化

### 2.1 デフォルト値の処理の簡素化

-   `_create_disp_spi_instance` ヘルパーから `actual_channel`, `actual_speed_hz`, `actual_pin` の計算ロジックを削除する。
-   ヘルパーは渡された `channel`, `pin`, `speed_hz` をそのまま `DispSpi` コンストラクタに渡し、`DispSpi` クラス自身が持つデフォルト値処理に任せる。
-   これにより、`_create_disp_spi_instance` は `DispSpi` インスタンスを生成するラッパーとしての役割に集中できる。

## 3. テストの網羅性と正確性の向上

### 3.1 `test_init_success` で `DispBase.__init__` の呼び出しを検証

-   `DispSpi` が `DispBase` を継承していることを踏まえ、`test_init_success` の中で `DispSpi` が `super().__init__` を呼び出したことをアサートする。
    -   具体的には、`setUp` で `pi0disp.disp.disp_base.DispBase.__init__` をモックし、`test_init_success` の中で `mock_disp_base_init.assert_called_once_with(...)` を使用して、`size`, `rotation`, `debug` の引数が正しく渡されたことを検証する。

### 3.2 冗長なアサートの削除

-   `test_init_success` 内の `self.assertEqual(disp.pin, self.default_pin)` の重複しているアサートを一つ削除する。
