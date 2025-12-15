# `DispBase` とサブクラスのコンストラクタ改善計画

`DispBase` とそのサブクラス (`DispSpi`, `ST7789V`) のコンストラクタのシグネチャを改善し、コードの可読性と堅牢性を向上させるためのリファクタリング案を提案します。

現在のコンストラクタは位置引数を使用していますが、これをキーワード専用引数（keyword-only arguments）に変更することで、引数の意味が明確になり、誤った順序で引数を渡すといった潜在的なバグを防ぐことができます。

## 1. `DispBase` コンストラクタの修正

-   `src/pi0disp/disp/disp_base.py` の `DispBase.__init__` メソッドのシグネチャを以下のように変更します。

    **変更前:**
    ```python
    def __init__(self, size: dict, rotation, debug=False):
    ```

    **変更後:**
    ```python
    def __init__(self, *, size: dict, rotation, debug=False):
    ```

## 2. `DispSpi` コンストラクタの修正

-   `DispBase` の変更に伴い、`src/pi0disp/disp/disp_spi.py` の `DispSpi.__init__` 内の `super()` 呼び出しをキーワード引数を使用するように修正します。

    **変更前:**
    ```python
    super().__init__(size, rotation, debug=debug)
    ```

    **変更後:**
    ```python
    super().__init__(size=size, rotation=rotation, debug=debug)
    ```

-   一貫性を保つため、`DispSpi.__init__` のシグネチャ自体もキーワード専用引数を使用するように変更します。

    **変更前:**
    ```python
    def __init__(self, bl_at_close: bool = False, channel: int = 0, ...):
    ```

    **変更後:**
    ```python
    def __init__(self, *, bl_at_close: bool = False, channel: int = 0, ...):
    ```

## 3. `ST7789V` コンストラクタの修正

-   `DispSpi` の変更に伴い、`src/pi0disp/disp/st7789v.py` の `ST7789V.__init__` 内の `super()` 呼び出しをキーワード引数を使用するように修正します。

    **変更前:**
    ```python
    super().__init__(bl_at_close, channel, pin, speed_hz, size, rotation, debug=debug)
    ```

    **変更後:**
    ```python
    super().__init__(bl_at_close=bl_at_close, channel=channel, pin=pin, speed_hz=speed_hz, size=size, rotation=rotation, debug=debug)
    ```

-   同様に、`ST7789V.__init__` のシグネチャもキーワード専用引数を使用するように変更します。

    **変更前:**
    ```python
    def __init__(self, bl_at_close: bool = False, channel: int = 0, ...):
    ```

    **変更後:**
    ```python
    def __init__(self, *, bl_at_close: bool = False, channel: int = 0, ...):
    ```

## 4. テストコードの修正

-   `DispBase` のコンストラクタ呼び出しを変更したことに伴い、`tests/test_01_disp_base.py` 内のすべての `DispBase` のインスタンス化を、キーワード引数を使用するように修正します。

    **変更例:**
    ```python
    # 変更前
    disp_base = DispBase(self.default_size, 0)

    # 変更後
    disp_base = DispBase(size=self.default_size, rotation=0)
    ```

この計画により、APIの使い方がより明確になり、将来の拡張やメンテナンスが容易になります。
