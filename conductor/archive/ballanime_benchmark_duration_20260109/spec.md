# Track Specification: ballanime_benchmark_duration_20260109

## Overview
`ballanime` コマンドの `--benchmark` オプションを拡張し、計測時間をユーザーが指定できるようにする。これにより、短時間のクイックな計測や、長時間の詳細な計測を柔軟に行えるようにする。

## Functional Requirements
- `ballanime` コマンドの `--benchmark` オプションを、フラグから「整数値（秒数）」を受け取るオプションに変更する。
- 以下の動作をサポートする：
    - `--benchmark` を指定しない場合：通常のアニメーション実行（無限ループ）。
    - `--benchmark` のみを指定した場合（値なし）：デフォルトの **10秒間** 計測を行う。
    - `--benchmark 20` のように値を指定した場合：指定された **20秒間** 計測を行う。
- 指定された時間経過後に自動的に終了し、パフォーマンスレポートを表示する既存の機能を維持する。

## Non-Functional Requirements
- `BenchmarkTracker` クラスの `duration` パラメータを動的に変更できるようにリファクタリングする。
- ユーザーが 0 以下の数値を入力した場合は、エラーにするかデフォルト値にフォールバックする適切なバリデーションを行う。

## Acceptance Criteria
- `pi0disp ballanime --benchmark 5` を実行し、約 5 秒後に終了してレポートが表示されること。
- `pi0disp ballanime --benchmark` を実行し、約 10 秒後に終了してレポートが表示されること。
- `pi0disp ballanime`（オプションなし）を実行した際、自動終了せずに通常どおり動作し続けること。

## Out of Scope
- 小数点以下の秒数指定（整数のみとする）。
- 計測中の残り時間の表示。
