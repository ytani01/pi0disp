# Track Specification: subcommand_refactor_20260109

## Overview
`pi0disp` のサブコマンド（`coltest`, `image`, `rgb`）を、最新の `ST7789V` ドライバ仕様に合わせてリファクタリングする。
パフォーマンス追求よりもコードのシンプルさを重視し、ドライバの自動差分更新機能（Dirty Rectangle）を最大限に活用する構成に書き換える。

## Functional Requirements
- **動作の維持**: ユーザーから見たコマンドの挙動、引数、オプション、表示内容は一切変更しない（完全な後方互換性）。
- **シンプル化**: `RegionOptimizer` などを使用した複雑な手動領域計算を削除し、`lcd.display(image)` を呼び出すだけのシンプルな実装に移行する。
- **最新仕様への適合**: `ST7789V` ドライバを Context Manager (`with` 文) を用いて初期化するスタイルに統一する。

## Non-Functional Requirements
- **ログ出力の刷新**: `get_logger(__name__, debug)` を使用した最新のロギングスタイルを採用し、デバッグ情報の出力を整理する。
- **出力の区別**: 開発者向けのデバッグ情報はロガー（`__log.debug`）を使用し、ユーザー向けの計測結果や情報表示は `print` 文を使用してコンソールに出力する。

## Acceptance Criteria
- `pi0disp coltest` が正常に動作し、テストパターンが表示されること。
- `pi0disp image <file>` が正常に動作し、画像が表示されること。
- `pi0disp rgb` が正常に動作し、各色が順次表示されること。
- すべてのコマンドにおいて、引数やオプション（`--rst`, `--dc` 等）が従来どおり機能すること。
- コードが以前よりも簡潔になり、可読性が向上していること。

## Out of Scope
- 新機能の追加。
- 既存のパフォーマンス（描画速度）の劇的な向上（シンプルさを優先するため、必要以上の最適化は行わない）。
