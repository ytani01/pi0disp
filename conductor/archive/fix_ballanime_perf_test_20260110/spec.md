# Specification: `spec.md`

## Overview
`tests/test_ballanime_perf.py` において、存在しない `--mode fast` が指定されている問題を修正し、現在実装されているすべての有効な描画モードのパフォーマンスを正しく比較できるようにテストを改善する。

## Functional Requirements
- **無効なモードの削除**: テストのパラメータから存在しない `fast` モードを削除する。
- **対象モードの拡充**: `simple`, `optimized`, `cairo`, `cairo-optimized` の4つのモードを比較対象として追加する。
- **計測の正確性**: 各モードで `ballanime` コマンドが正しく起動し、指定された時間（duration）性能計測が行われるようにする。

## Non-Functional Requirements
- **可観測性**: テスト実行時のログに、各モードの平均CPU使用率（アプリ本体および `pigpiod`）が明確に出力されること。
- **実装原則（推測厳禁）**: 修正および調査の過程において、推測に頼らずログや事実に基づいて動作を確認すること。特にプロセスの生存確認やエラー出力の有無を事実として捉えること。

## Acceptance Criteria
- [ ] `mise run test` (または `pytest tests/test_ballanime_perf.py`) を実行した際、すべてのテストケースがパスすること。
- [ ] テスト結果に `simple`, `optimized`, `cairo`, `cairo-optimized` の4つのモードの計測データが含まれていること。
- [ ] 各モードの計測結果（CPU使用率等）がログに正しく出力されていること。

## Out of Scope
- `ballanime` コマンド自体のロジック修正や最適化。
- メモリ使用量など、CPU使用率以外の指標の追加（本トラックでは既存のCPU計測の修正に注力する）。
