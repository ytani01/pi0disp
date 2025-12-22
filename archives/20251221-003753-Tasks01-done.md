# タスクリスト: Plan01

`Plan01.md`で定義された修正を実行するための具体的なタスクリストです。

## ステップ1: `disp_base.py` のロガーを修正

- [x] `src/pi0disp/disp/disp_base.py` ファイルを開きます。
- [x] ファイル内の `self.__log` という文字列を `self._log` にすべて置換します。

## ステップ2: `disp_spi.py` のロガーを修正

- [x] `src/pi0disp/disp/disp_spi.py` ファイルを開きます。
- [x] `__init__`メソッドから `self.__log = get_logger(self.__class__.__name__, self.__debug)` の行を削除します。
- [x] ファイル内の残りの `self.__log` という文字列を `self._log` にすべて置換します。

## ステップ3: 動作検証

- [x] `mise run test` コマンドを実行し、すべてのテストがパスすることを確認します。