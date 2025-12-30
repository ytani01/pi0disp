# Plan for "サンプルプログラムの作成"

この計画は、「サンプルプログラムの作成」トラックの各フェーズとタスクを詳述します。各タスクは、プロジェクトのワークフローガイドラインに従って実行されます。

## フェーズ 1: 基本的な表示サンプルプログラムの作成

このフェーズでは、`pi0disp` ライブラリを使用したディスプレイの初期化と、`Pillow` ライブラリによる基本的な図形描画を行うサンプルプログラムを作成します。

### タスク

- [ ] Task: ディスプレイの初期化と簡単な図形描画が正しく行われることを確認するテストコード(`tests/test_new_sample_basic.py`)を作成する。
- [ ] Task: 基本的な`ST7789V`の初期化、`PIL.Image`と`ImageDraw`を使った図形描画、そして`lcd.display()`による表示を行うサンプルプログラム(`samples/new_basic_usage.py`)を実装する。
- [ ] Task: Conductor - User Manual Verification '基本的な表示サンプルプログラムの作成' (Protocol in workflow.md)

## フェーズ 2: 部分更新サンプルプログラムの作成

このフェーズでは、`pi0disp` ライブラリの部分更新機能 (`display_region()`) を使用して、画面の一部のみを効率的に更新するサンプルプログラムを作成します。

### タスク

- [ ] Task: `ST7789V.display_region()` を使った部分更新が正しく行われることを確認するテストコード(`tests/test_new_sample_partial.py`)を作成する。
- [ ] Task: 既存の描画内容の一部を変更し、`lcd.display_region()` を使ってその変更領域のみをディスプレイに更新するサンプルプログラム(`samples/new_partial_update.py`)を実装する。
- [ ] Task: Conductor - User Manual Verification '部分更新サンプルプログラムの作成' (Protocol in workflow.md)
