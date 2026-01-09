# Specification: roboface テストの整理

## 1. 概要
`samples` ディレクトリ内の `roboface` 関連ファイルが `roboface.py` に統合されたことに伴い、関連するテストファイルを整理・修正する。

## 2. 機能要件
- `roboface1.py` と `roboface2.py` にのみ依存していたテストを削除する。
- `test_23_roboface2.py` を `test_roboface.py` のような適切な名前にリネームし、テスト対象を新しい `roboface.py` に変更する。
- `test_24_roboface2_thread.py`, `test_25_roboface2_queue.py`, `test_debug_roboface.py` の内容を確認し、不要であれば削除、必要であれば `roboface.py` を対象とするように修正する。

## 3. 受入基準
- `uv run test` を実行した際に、すべてのテストが成功すること。
- 古い `roboface` ファイル (`roboface1.py`, `roboface2.py`) を参照しているテストコードが残っていないこと。
