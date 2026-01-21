# Track Specification: Fix Lint Errors in `src`

## Overview
`mise run lint` を実行した際に `basedpyright` で検出される型エラー（32件）を解消し、`src` ディレクトリ配下のコードを厳密な型チェックに適合させる。これにより、プロジェクトの型安全性を向上させ、将来的なバグを未然に防ぐ。

## Functional Requirements
- `src/pi0disp` 配下の全ての Python ファイルにおいて、`basedpyright` が報告するエラーをゼロにする。
- 主な修正対象：
    - `None` チェックの追加（`if obj is not None:` 等）。
    - 型ヒントの改善（`Optional` の適切な使用、型アノテーションの追加）。
    - `Dynaconf` 設定値の取得時におけるデフォルト値の指定や型キャストの徹底。
- 実行時の挙動（ロジック）は変更しない。

## Non-Functional Requirements
- **型安全性**: `pyproject.toml` で定義された `basedpyright` の `standard` モードを維持し、抑制ルール（`type: ignore`）の使用は最小限に留める。
- **後方互換性**: 公開 API のシグネチャを変更する場合は、型定義のみを更新し、既存の利用側に影響を与えないようにする。
- **憶測厳禁**: 修正にあたっては設定ファイルや関連コードの挙動をファクトチェックし、根本原因を特定した上で対処する。

## Acceptance Criteria
- [ ] `uv run basedpyright src` を実行した際の結果が `0 errors` になること。
- [ ] `mise run lint` 内の他のツール（`ruff`, `mypy`）でもエラーが発生しないこと。
- [ ] 既存のテスト（`pytest tests`）が全てパスすること。

## Out of Scope
- `samples` ディレクトリ配下の修正（本トラック完了後に検討）。
- `tests` ディレクトリ配下のリンター適合。
- 大規模なリファクタリング（型修正に伴う軽微な整理は可）。
