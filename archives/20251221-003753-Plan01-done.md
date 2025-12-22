# Plan01: `DispSpi`ロガーにおける`AttributeError`の修正
## 1. 問題分析

`tests/test_02_disp_spi.py`内のテスト`test_enter_exit_context_manager`が、`AttributeError: 'DispSpi' object has no attribute '_DispBase__log'`というエラーで失敗しています。

これは以下の原因によるものです。

1.  `DispBase`クラスはプライベートなロガー`self.__log`を初期化します。
2.  `DispSpi`クラスは`DispBase`を継承していますが、自身の`__init__`内で同じ名前のプライベートなロガー`self.__log`を**再度初期化**しています。
3.  `DispSpi`オブジェクトがコンテキストマネージャーとして使用される際、親クラスである`DispBase`の`__enter__`メソッドが呼び出されます。
4.  `DispBase.__enter__`メソッドは`self.__log`（名前マングリングにより`_DispBase__log`となる）にアクセスしようとしますが、`DispSpi`インスタンスには`_DispSpi__log`しか存在しないため、`AttributeError`が発生します。

## 2. 提案される解決策

最も効果的な解決策は、`DispBase`クラスでロガーの初期化を一元化し、サブクラスがそれを共有できるようにすることです。これにより、コードの重複を避け、一貫性を保つことができます。

この計画では、ロガーをプライベート属性（`__log`）から保護された属性（`_log`）に変更します。

## 3. 実行ステップ

### ステップ1: `src/pi0disp/disp/disp_base.py`の修正

-   **目的:** `__log`を`_log`に変更し、サブクラスからアクセス可能にする。
-   **行動:** `DispBase`クラス内で、`self.__log`のすべてのインスタンスを`self._log`に置換します。

```python
class DispBase(metaclass=ABCMeta):
    """Display Base."""
    # ...
    def __init__(
        self,
        # ...
    ):
        """Constractor."""
        self.__debug = debug
        self._log = get_logger(self.__class__.__name__, self.__debug)  # 変更: __log -> _log
        self._log.debug("size=%s,rotation=%s", size, rotation)  # 変更: __log -> _log
        # ... ファイル内の他のすべての出現箇所についても同様に修正します。
```

### ステップ2: `src/pi0disp/disp/disp_spi.py`の修正

-   **目的:** 不要なロガー初期化を削除し、親クラスのロガーを使用するようにする。
-   **行動:**
    1.  `DispSpi.__init__`内のロガーを初期化する行を削除します。
    2.  `self.__log`のすべてのインスタンスを`self._log`に置換します。

```python
class DispSpi(DispBase):
    """SPI Display."""
    # ...
    def __init__(
        self,
        # ...
    ):
        super().__init__(size, rotation, debug=debug)
        self.__debug = debug
        # self.__log = get_logger(self.__class__.__name__, self.__debug) # この行を削除
        self._log.debug("bl_at_close=%s", bl_at_close)  # 変更: __log -> _log
        # ... ファイル内の他のすべての出現箇所についても同様に修正します。
```