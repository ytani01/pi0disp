# Implementation Plan: lcd-check subcommand

`lcd_check` ロジックをコマンドとして統合し、キャプチャベースの自動テストを導入します。

## Phase 1: Setup and Branching
- [x] Task: 新しい作業ブランチ `feat/lcd-check-command` を作成する
- [ ] Task: 既存の `samples/lcd_check.py` の動作を再確認し、依存関係を整理する

## Phase 2: Implementation of Core Logic & Command
- [x] Task: テストパターン描画ロジックを再利用可能な形で抽出する
- [x] Task: `src/pi0disp/commands/lcd_check.py` を作成し、Click サブコマンドを定義する
- [x] Task: `src/pi0disp/__main__.py` にサブコマンドを登録する
- [x] Task: 詳細なデバッグログ（適用されている設定、計算された座標等）を実装する

## Phase 3: Automated Testing & Verification
- [ ] Task: 描画結果を検証する自動テスト（`tests/test_23_lcd_check_cmd.py`）を作成する
    - [ ] `ST7789V` のモックを使用し、`display()` に渡された `Image` オブジェクトのピクセル値を直接検証する
    - [ ] 期待される RGB 帯が正しい Y 座標範囲に存在するかを「事実」として確認する
- [ ] Task: `mise run lint` を実行し、静的解析の不備がないか確認する
- [ ] Task: `mise run test` を実行し、既存機能への影響がないことを確認する

## Phase 4: Final Cleanup & Documentation
- [ ] Task: README または `docs/` に `lcd-check` コマンドの使い方を追記する
- [ ] Task: 最終的な動作確認ログを記録し、ドキュメント化する
