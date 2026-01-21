# Implementation Plan - lcd-check ウィザードへのインタラクティブ画面向き設定機能

このプランは、`pi0disp lcd-check --wizard` の冒頭に、キー入力で画面の向きをリアルタイムに調整し、`pi0disp.toml` に保存するフェーズを追加するものです。

## Phase 1: 向き確認用パターンの実装とスケーリング [checkpoint: 6d42d4d]
縦長・横長どちらでも正しく表示される確認用パターンを実装します。

- [x] Task: 確認用パターンの描画ロジック実装 (src/pi0disp/utils/lcd_test_pattern.py) [44fcbf3]
    - [x] `draw_orientation_pattern(width, height, rotation)` 関数を新規作成する。
    - [x] 画面サイズ（min(width, height)）に基づき、矢印と文字のサイズを自動スケーリングするロジックを実装する。
- [x] Task: 描画ロジックのテスト (TDD) [44fcbf3]
    - [x] 240x320（縦長）と 320x240（横長）の両方で、描画内容が画面内に収まっているかをキャプチャベースで検証するテストを記述する。
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: インタラクティブ回転調整フェーズの実装
キー入力に応じてリアルタイムに画面を更新するループを実装します。

- [x] Task: 回転調整ループのプロトタイプ実装 (src/pi0disp/commands/lcd_check.py) [33260e6]
    - [x] `run_orientation_wizard(disp, conf)` 関数を作成する。
    - [x] `click.getchar()` 等を使用し、`a, b, c, d, ENTER` の入力を受け付けるループを実装する。
- [x] Task: ループ動作のテスト [33260e6]
    - [x] `CliRunner` で入力をエミュレートし、指定されたキーに応じて `disp.set_rotation` が正しく呼ばれるかをテストする。
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: 設定の保存と色判定フェーズへの統合
決定した角度を `pi0disp.toml` に保存し、既存のウィザードに繋げます。

- [x] Task: `rotation` 設定の保存処理の実装 [f3aae31]
    - [x] `ENTER` 決定時に `update_toml_settings` を呼び出し、`rotation` を更新する。
- [x] Task: ウィザード全体の統合 [f3aae31]
    - [x] `lcd_check --wizard` の冒頭で `run_orientation_wizard` を呼び出し、戻り値の角度を後続の色判定フェーズに引き継ぐように修正する。
- [x] Task: 統合テスト [f3aae31]
    - [x] 回転決定 -> 保存 -> 色判定開始 の一連の流れが正しく動作することを検証する。
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md) [f3aae31]

## Phase 4: 最終調整とドキュメント更新
- [ ] Task: README.md / マニュアルの更新
    - [ ] ウィザードの新しい操作手順（a, b, c, d キー）について追記する。
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
