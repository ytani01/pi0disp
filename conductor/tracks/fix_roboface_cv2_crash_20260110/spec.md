# Specification: `spec.md`

## Overview
`samples/roboface.py` において、OpenCVプレビューモード（`CV2Disp`）を使用する際に、メソッドの引数不足により発生する致命的なクラッシュ（`TypeError`）を修正します。

## Functional Requirements
- **`CV2Disp.display` のシグネチャ修正**: `RobotFace.draw` からの呼び出しに合わせて、`full: bool = False` 引数を受け取れるように修正します。
- **インターフェースの整合性**: `DisplayBase` で定義された抽象メソッドの期待される動作と一致させます。

## Non-Functional Requirements
- **堅牢性**: 無効な引数によるクラッシュを防ぎ、他の表示デバイス（LCD等）と同様のインターフェースを提供します。
- **実装原則（憶測厳禁）**: 修正および調査の過程において、推測に頼らず事実（ログ、スタックトレース、コードの定義）に基づいて原因を特定し、対処すること。

## Acceptance Criteria
- [ ] `CV2Disp.display` メソッドが `full` 引数を受け取るように定義されていること。
- [ ] 自動テスト（モックを使用）により、`CV2Disp.display` を `full` 引数付きで呼び出しても `TypeError` が発生しないことが確認されていること。
- [ ] `ruff` および `mypy` による静的解析でエラーが出ないこと。

## Out of Scope
- `review_result.md` に記載されている他の問題（重要度 HIGH, MEDIUM, LOW）の修正。
- OpenCV自体の描画ロジックの変更。
