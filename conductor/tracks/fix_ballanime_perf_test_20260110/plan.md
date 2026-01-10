# Plan: `plan.md`

## Phase 1: Preparation and Failing Tests (Red Phase)
- [ ] Task: `tests/test_ballanime_perf.py` の現状の動作を詳細に分析し、無効なオプション指定時の挙動を確認する
- [ ] Task: `.gitignore` に `ballanime-report.md` を追加し、環境を整備する
- [ ] Task: `tests/test_ballanime_perf.py` を修正し、無効な `fast` モードを削除して `optimized`, `cairo`, `cairo-optimized` を追加する
- [ ] Task: プロセスが起動直後に終了していないことを検証するアサーションをテストに追加し、失敗を確認する
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Preparation and Failing Tests' (Protocol in workflow.md)

## Phase 2: Implementation and Verification (Green Phase)
- [ ] Task: テスト内のパラメータと `ballanime` コマンドの実装が一致していることを確認し、全モードでプロセスが正常に維持されるようにテストを調整する
- [ ] Task: `mise run test` を実行し、`test_ballanime_perf.py` がすべてのモード（4種類）でパスすることを確認する
- [ ] Task: ログ出力を確認し、各モードの平均CPU使用率が正しくレポートされていることを事実として確認する
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation and Verification' (Protocol in workflow.md)

## Phase 3: Final Integration and Quality Gate
- [ ] Task: `ballanime-report.md` に最新のパフォーマンス比較結果をまとめ、ドキュメントを更新する
- [ ] Task: プロジェクト全体のリンター（ruff）および型チェック（mypy）を実行し、新たな問題が導入されていないことを確認する
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Final Integration and Quality Gate' (Protocol in workflow.md)
