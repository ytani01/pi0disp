# Plan 10: Refactor `tests/test_01_disp_base.py` to Pytest Style

`tests/` 以下のテストコード全体をレビューした結果、`tests/test_01_disp_base.py` がまだ古い `unittest.TestCase` スタイルで記述されていることが確認されました。
`tests/test_02_disp_spi.py` と同様に、これを `pytest` ネイティブなスタイルにリファクタリングすることで、プロジェクト全体のテストコードのスタイルを統一し、可読性と保守性を向上させます。

## 改善案

### 1. `tests/test_01_disp_base.py` のリファクタリング

- **`unittest.TestCase` の廃止**: クラスベースのテストから関数ベースのテストに変更します。
- **フィクスチャの導入**: `setUp` メソッドで行われている初期化処理（`pigpio` や `logger` のモック作成）を、`pytest.fixture` に置き換えます。
- **アサーションの変更**: `self.assertEqual`, `self.assertTrue` などを、標準の `assert` 文に置き換えます。
- **例外テストの変更**: `self.assertRaises` を `pytest.raises` に置き換えます。

### 2. 他のテストファイルについて

- `tests/test_00_conftest_01_basic.py`, `tests/test_00_conftest_02_interactive.py`: 既に `pytest` の機能（フィクスチャ、パラメータ化）を活用しており、大きな修正は不要と判断しました。
- `tests/_testbase_cli.py`: テスト基盤となるヘルパークラスであり、適切に実装されています。

## 検証計画

- `mise run test` を実行し、リファクタリング後の `tests/test_01_disp_base.py` がすべてのテストケースをパスすることを確認します。
