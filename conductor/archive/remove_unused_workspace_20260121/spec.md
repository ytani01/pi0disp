# 仕様書: 未使用の UV ワークスペース設定の削除

## 概要
`pyproject.toml` に、現在は存在しない `app1` を参照する `[tool.uv.workspace]` 設定が残っています。この不要な設定を削除し、プロジェクトの構成ファイルをクリーンな状態にします。

## トラック種別
Chore (雑務)

## 機能要件
- `pyproject.toml` から `[tool.uv.workspace]` セクションを完全に削除する。

## 非機能要件
- 設定削除後も、`uv` によるパッケージ管理や依存関係の解決が正常に行われること。

## 完了定義 (Acceptance Criteria)
- `pyproject.toml` に `[tool.uv.workspace]` が存在しない。
- `uv sync` を実行してエラーが発生しない。
- `mise run test` および `mise run lint` が正常に完了する。
