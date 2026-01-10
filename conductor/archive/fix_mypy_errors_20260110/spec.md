# Specification: `spec.md`

## Overview
現在 `mise run test`（または `mypy` 直接実行）において多数検出されている型チェックエラーを完全に解消し、プロジェクト全体の型安全性を確保する。

## Functional Requirements
- **型エラーの解消**: `src/pi0disp/` および `tests/` ディレクトリ内のすべての Python ファイルに対して `mypy` を実行し、エラーをゼロにする。
- **適切な型ヒントの付与**: 型推論が不十分な箇所に対し、明示的な型ヒント（Type Annotations）を追加する。
- **設定の最適化**: プロジェクトの性質（Raspberry Pi 制御、画像処理、CLI）に合わせ、`pyproject.toml` や `setup.cfg` 内の `mypy` 設定を見直す。

## Non-Functional Requirements
- **コード品質の向上**: 型安全性を高めることで、実行時の予期せぬエラー（TypeError 等）を未然に防ぐ。
- **メンテナンス性の確保**: 型定義を明確にすることで、将来のリファクタリングや機能追加を容易にする。

## Acceptance Criteria
- [ ] `mise run test` (または `mypy .`) を実行した際、エラーが報告されないこと。
- [ ] 既存の単体テストがすべて通過すること。
- [ ] `mypy` の設定が現在のコードベースにとって適切であること。

## Out of Scope
- 新機能の追加。
- 型チェック以外のリントエラー（`ruff` 等）の修正（本トラックの主目的ではないため、型修正に伴うもの以外は除外）。
