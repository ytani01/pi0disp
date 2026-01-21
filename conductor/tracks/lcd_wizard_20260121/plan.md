# Implementation Plan - lcd-check 対話型設定ウィザード

このプランは、ユーザーが実機を見ながら設定（BGR, Invert）を特定できる対話型ウィザードを `pi0disp lcd-check --wizard` として実装するものです。

## Phase 1: 判定ロジックとシミュレーションの基盤整備 [checkpoint: 43e4838]
このフェーズでは、設定値と「見え方」を相互変換する純粋なロジックを実装し、テストで検証します。

- [x] Task: 判定マトリックスの定義とテストデータの作成 (src/pi0disp/utils/lcd_test_pattern.py) (5912953)
    - [x] `bgr`, `invert` の各組み合わせに対し、期待される「見え方」を定義するデータ構造を作成する。
- [x] Task: 設定判定ロジックの実装とテスト (TDD) (5912953)
    - [x] ユーザーの回答（色、背景、文字）から `(bgr, invert)` を返す関数のテストを記述する。
    - [x] 判定ロジック本体を実装する。
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md) (43e4838)

## Phase 2: ウィザード UI (CLI) の実装 [checkpoint: f760f3f]
Click を使用して対話型インターフェースを構築します。

- [x] Task: 対話型プロンプトのテスト (tests/test_23_lcd_check_cmd.py) (f760f3f)
    - [x] `click.testing.CliRunner` を使い、入力に対するモック応答をシミュレートするテストを記述する。
- [x] Task: `lcd-check --wizard` オプションの追加と実装 (f760f3f)
    - [x] `src/pi0disp/commands/lcd_check.py` に `--wizard` オプションを追加する。
    - [x] 質問の順序と各質問に対するバリデーションを実装する。
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md) (f760f3f)

## Phase 3: 設定ファイルの自動更新機能
判定結果を `pi0disp.toml` に反映する機能を実装します。

- [ ] Task: 設定ファイル更新ロジックのテスト (TDD)
    - [ ] `pi0disp.toml` が存在する場合/しない場合、既存の値を上書きする場合のテストを記述する。
- [ ] Task: 設定保存機能の実装
    - [ ] ユーザーに保存の確認 (`[y/N]`) を行い、許可された場合のみ `pi0disp.toml` を更新する。
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: 最終統合テストとドキュメント更新
- [ ] Task: 統合テストの実施
    - [ ] 実際のコマンドフローを通じた結合テスト（モック環境）を実行する。
- [ ] Task: README.md および docs/ の更新
    - [ ] `lcd-check --wizard` の使い方をドキュメントに追加する。
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
