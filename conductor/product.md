# Product Guide

## Initial Concept
- **Core Functionality**: Raspberry Pi上でST7789Vディスプレイを高速駆動するドライバ

### Overview
pi0dispは、Raspberry Pi、特にリソースに制約のあるRaspberry Pi Zero 2Wのようなモデルで、ST7789V搭載ディスプレイを効率的に駆動するために設計された、Python製の高速ディスプレイドライバライブラリです。本プロジェクトは、主にディスプレイの高速駆動に焦点を当てています。

### Key Features
*   **高速ディスプレイ駆動**: Raspberry Pi上でST7789Vディスプレイを効率的かつ高速に駆動します。
*   **Pythonベース**: Pythonで記述されており、開発者が容易に利用・拡張できます。
*   **互換性**: Raspberry Pi Zero 2Wを含む様々なRaspberry Piモデルに対応しています。
*   **表情アニメーションエンジン**: キューベースの非同期制御により、滑らかな視線移動と表情の変化を並行して処理可能です。
*   **インタラクティブ制御**: ヒストリー機能や複数表情の一括順次実行に対応した高度なCLIインタフェースを提供します。
