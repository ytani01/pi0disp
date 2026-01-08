# Track: roboface2.py および pigpiod のCPU負荷最適化 - 実装計画

## Phase 1: 現状分析と評価基準の定義 [checkpoint: 454d0af]
- [x] Task: `roboface2.py` の現状のCPU負荷とメモリ使用量を測定する。
    - **測定結果 (10秒間、ランダムモード):**
        - `roboface2.py` (PID: 483328):
            - Average CPU: 0.00%
            - Max CPU: 0.00%
            - Average Memory (RSS): 29.86MB
            - Max Memory (RSS): 29.86MB
        - `pigpiod` (PID: 805):
            - Average CPU: 105.11%
            - Max CPU: 105.90%
            - Average Memory (RSS): 2.06MB
            - Max Memory (RSS): 2.06MB
    - [ ] `pigpiod` のCPU使用率（`htop` または `top` を使用）。
    - [ ] `roboface2.py` のプロセスCPU使用率とメモリ使用量。
    - [ ] フレームレート（可能な範囲で測定）。
    - [ ] 特定のシナリオ（例: ランダムモードで5分間実行）で測定。
- [x] Task: パフォーマンス測定スクリプトを作成する。
- [x] Task: 測定結果を文書化し、ベースラインとして設定する。
- [x] Task: `pigpiod` のCPU使用率、フレームレート、メモリ使用量の具体的な目標値を定義する。
- [x] Task: Conductor - User Manual Verification 'Phase 1: 現状分析と評価基準の定義' (Protocol in workflow.md)

## Phase 2: `pigpio` 操作の最適化
- [x] Task: `roboface2.py` および関連モジュールにおける `pigpio` GPIO操作の箇所を特定する。
- [x] Task: `pigpio` 操作の頻度を削減するためのコード変更案を検討する。
    - **決定案:** GPIO (DCピン) 操作の冗長な呼び出しを削除し、SPI送信と集約する。また、`roboface2.py` の部分更新領域を統合し、`set_window` の呼び出し回数を削減する。
- [x] Task: 変更案に基づいて`pigpio`操作を最適化する。
    - **最適化内容:**
        - `DispSpi` で `DC` ピンの状態をキャッシュし、不要な `pi.write` 呼び出しを削減。
        - `ST7789V.write_pixels` から冗長な `DC` 設定を削除。
        - `roboface2.py` の部分更新領域を統合し、通信回数を削減。
- [x] Task: 最適化後のパフォーマンスを測定し、ベースラインと比較する。
    - **測定結果 (10秒間、ランダムモード):**
        - `roboface2.py` (PID: 502322):
            - Average CPU: 0.00%
            - Max CPU: 0.00%
            - Average Memory (RSS): 29.89MB
        - `pigpiod` (PID: 500398):
            - Average CPU: 53.97% (改善前: 103.81%)
            - Max CPU: 66.70% (改善前: 105.90%)
            - Average Memory (RSS): 2.15MB
- [x] Task: Conductor - User Manual Verification 'Phase 2: `pigpio` 操作の最適化' (Protocol in workflow.md)

<h2>Phase 3: 通信オーバーヘッドと描画ロジックの最適化</h2>
- [ ] Task: `pigpiod` と `roboface2.py` 間のデータ転送メカニズムを分析する。
- [ ] Task: 通信オーバーヘッドを削減するためのアプローチ（例: データ構造の最適化、転送頻度の調整）を検討する。
- [ ] Task: `roboface2.py` 内部の画像処理および描画ロジックを分析する。
- [ ] Task: 新しい描画アルゴリズムやデータ構造（例: 変更領域のみの描画、効率的なバッファ管理）を導入し、`pigpio` への影響を最小限に抑える。
- [ ] Task: 変更後のパフォーマンスを測定し、ベースラインと比較する。
- [ ] Task: Conductor - User Manual Verification 'Phase 3: 通信オーバーヘッドと描画ロジックの最適化' (Protocol in workflow.md)

## Phase 4: 品質保証と最終確認
- [ ] Task: すべての単体テストおよび統合テストが成功することを確認する。
- [ ] Task: リントツール (`mise run lint`) および型チェックツール (`mypy`) でエラーが発生しないことを確認する。
- [ ] Task: 定義された受け入れ基準がすべて満たされていることを確認する。
- [ ] Task: 実際のハードウェアまたはモック環境での長時間動作確認を実施する。
- [ ] Task: コードの可読性と保守性が維持されていることを確認する。
- [ ] Task: プロジェクトドキュメント（`product.md`, `tech-stack.md` など）が必要に応じて更新されていることを確認する。
- [ ] Task: Conductor - User Manual Verification 'Phase 4: 品質保証と最終確認' (Protocol in workflow.md)
