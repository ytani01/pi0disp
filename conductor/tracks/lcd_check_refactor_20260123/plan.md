# 実装計画: lcd_check コマンドのリファクタリング

## Phase 1: 準備と現状の事実確認 (Analysis & Red Phase) [checkpoint: 4ce91e6]
リファクタリング前に現状の挙動を「事実」として記録し、破壊的変更を防ぐためのテストを整備する。

- [x] Task: 新しい作業用ブランチ `refactor-lcd-check` を作成する [ce151a2]
- [x] Task: 現状の `lcd_check.py` の挙動（ウィザードの各ステップ、期待される出力画像等）を詳細に分析する [399fb6c]
- [x] Task: リファクタリング後の「理想のインターフェース」を定義し、それに合わせた失敗するテスト（Red）を作成する [399fb6c]
    - ウィザードのロジックが独立してテスト可能であることを検証するテストを含む
- [x] Task: Conductor - User Manual Verification 'Phase 1: 準備と現状の事実確認' (Protocol in workflow.md) [399fb6c]

## Phase 2: シンプルでスッキリとした構造への刷新 (Implementation - Green Phase) [checkpoint: 7d99f1b]
ロジックを分離し、可読性の高いクリーンなコードへ移行する。

- [x] Task: 共通の描画・検証インターフェース（シンプルな基底クラスまたはプロトコル）を定義する [f837deb]
- [x] Task: 各チェック項目（向き、反転、色順序）を独立したコンポーネントに抽出し、重複を排除する [8541a44]
- [x] Task: ウィザードの進行制御ロジックを、UI表示や設定保存から分離して再実装する [3facf79]
- [x] Task: `lcd_check.py` 本体のコードを大幅に削減し、各コンポーネントを呼び出すだけのシンプルな構造にする [428cf82]
- [ ] Task: Conductor - User Manual Verification 'Phase 2: シンプルでスッキリとした構造への刷新' (Protocol in workflow.md)

## Phase 3: 検証と品質確保 (Refactor & Verification)
自動テストと実際の動作確認により、リファクタリングの正当性を証明する。

- [x] Task: 作成した自動テストを実行し、すべてのステップのロジックが正しく機能することを「事実」として確認する [924455e]
- [x] Task: 画面キャプチャやデバッグログを活用し、実機に近い挙動が維持されていることを検証する [191044b]
- [x] Task: `mise run test` および `mise run lint` を実行し、プロジェクトの品質基準をすべてクリアする [eb95391]
- [ ] Task: Conductor - User Manual Verification 'Phase 3: 検証と品質確保' (Protocol in workflow.md)
