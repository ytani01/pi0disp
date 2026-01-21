# Implementation Plan: lcd-check subcommand

`lcd_check` ロジックをコマンドとして統合し、キャプチャベースの自動テストを導入します。

## Phase 1: Setup and Branching
- [x] Task: 新しい作業ブランチ `feat/lcd-check-command` を作成する 9063df3
- [x] Task: 既存の `samples/lcd_check.py` の動作を再確認し、依存関係を整理する 9063df3

## Phase 2: Implementation of Core Logic & Command
- [x] Task: テストパターン描画ロジックを再利用可能な形で抽出する 9063df3
- [x] Task: `src/pi0disp/commands/lcd_check.py` を作成し、Click サブコマンドを定義する 9063df3
- [x] Task: `src/pi0disp/__main__.py` にサブコマンドを登録する 9063df3
- [x] Task: 詳細なデバッグログ（適用されている設定、計算された座標等）を実装する 9063df3

## Phase 3: Automated Testing & Verification
- [x] Task: 描画結果を検証する自動テスト（`tests/test_23_lcd_check_cmd.py`）を作成する 9063df3
    - [x] `ST7789V` のモックを使用し、`display()` に渡された `Image` オブジェクトのピクセル値を直接検証する
    - [x] 期待される RGB 帯が正しい Y 座標範囲に存在するかを「事実」として確認する
- [x] Task: `mise run lint` を実行し、静的解析の不備がないか確認する 9063df3
- [x] Task: `mise run test` を実行し、既存機能への影響がないことを確認する 9063df3

## Phase 4: Final Cleanup & Documentation
- [x] Task: README または `docs/` に `lcd-check` コマンドの使い方を追記する 9063df3
- [x] Task: 最終的な動作確認ログを記録し、ドキュメント化する 9063df3
