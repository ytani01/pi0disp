# Track Specification: Complete Lint Pass for `samples` and Integration

## Overview
`mise run lint` を実行した際に、プロジェクト全体（特に今回は `samples` ディレクトリ）でエラーが一切発生しない状態にする。直前のトラックで `src` の修正が完了しているため、今回は残存する `samples` のエラーを解消し、プロジェクト全体のリンター（ruff, basedpyright, mypy）の整合性を確保することを目的とする。

## Functional Requirements
- `samples` ディレクトリ配下の全ての Python ファイルにおいて、リンター（特に `basedpyright`）が報告するエラーをゼロにする。
- 主な修正対象：
    - `samples/lcd_check.py`: `set_rotation` への引数の型不整合（Noneの可能性）の解消。
- `mise run lint` を実行した際、`src`, `samples` の両方でエラーが発生しないことを確認する。
- 実行時の挙動（サンプルの動作）は変更しない。

## Non-Functional Requirements
- **型安全性**: `pyproject.toml` で定義された各ツールの設定を維持し、より厳格な指摘（basedpyrightのstandardモード等）に合わせてコードを修正する。
- **一貫性**: ツール間で指摘が矛盾する場合は、プロジェクトの標準設定を優先し、必要最小限の抑制（`# type: ignore` 等）に留める。
- **憶測厳禁**: 修正にあたっては現状の動作を確認し、事実に基づいて適切な型キャストやガード節を追加する。

## Acceptance Criteria
- [ ] `uv run basedpyright samples` の結果が `0 errors` になること。
- [ ] `mise run lint` が正常に終了し、全てのツール（ruff, basedpyright, mypy）がパスすること。
- [ ] サンプルプログラム（例: `samples/lcd_check.py`）が正常に動作すること。

## Out of Scope
- `tests` ディレクトリ配下のリンター適合（現状の `mise run lint` の対象外であるため）。
- 新機能の追加やサンプルの大幅な作り直し。
