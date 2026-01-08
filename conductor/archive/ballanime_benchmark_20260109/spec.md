# Track Specification: ballanime_benchmark_20260109

## Overview
`src/pi0disp/commands/ballanime.py` に、実行パフォーマンスを計測するためのベンチマーク機能を追加する。これにより、`simple` モードと `fast` モードのそれぞれにおける FPS（描画速度）と CPU 負荷（ballanime 自身および pigpiod サーバー）を客観的に比較できるようにする。

## Functional Requirements
- `ballanime` コマンドに `--benchmark` オプションを追加する。
- `--benchmark` が指定された場合、プログラムは 10 秒間実行され、その間のパフォーマンスデータを収集する。
- 計測終了後、自動的にプログラムを終了し、以下の統計情報をコンソールに出力する。
    - 計測した平均 FPS
    - `ballanime` プロセスの平均 CPU 使用率 (%)
    - `pigpiod` プロセスの平均 CPU 使用率 (%)
- `pigpiod` プロセスは `psutil` を使用してシステム内から自動的に特定する。
- `--benchmark` 指定時でも、通常どおり画面にアニメーションが表示されること。

## Non-Functional Requirements
- パフォーマンス計測自体がシステム全体の負荷に大きな影響を与えないように実装する（計測誤差の最小化）。
- `psutil` がインストールされていない環境でも、ベンチマーク機能以外は動作するように考慮する（必要に応じて依存関係に追加）。

## Acceptance Criteria
- `pi0disp ballanime --mode simple --benchmark` を実行し、10秒後に結果が表示されて正常終了すること。
- `pi0disp ballanime --mode fast --benchmark` を実行し、10秒後に結果が表示されて正常終了すること。
- 表示される CPU 使用率に、`ballanime` と `pigpiod` の両方が含まれていること。

## Out of Scope
- 計測結果のファイル（CSV等）への保存（今回はコンソール出力のみ）。
- グラフ描画機能。
- 複数モードの一括自動計測。
