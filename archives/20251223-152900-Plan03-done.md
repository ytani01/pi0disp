# `samples/robot_face_animation.py` インタラクティブ表情操作機能 計画書 (改訂版)

## 1. 目的

`samples/robot_face_animation.py` に、コマンドラインから複数の顔表情を簡易的な文字列で指定し、順番に表示する機能を追加する。これにより、インタラクティブな操作と簡単なアニメーション作成を両立させる。

## 2. 現状のコードベース

`FaceState` はフラットなデータ構造を持つ。

```python
@dataclass
class FaceState:
    mouth_curve: float = 0
    brow_tilt: float = 0
    mouth_open: float = 0
    # ... (eye parameters)
```

## 3. 提案内容：文字列による表情シーケンス指定

### 3.1. 表情文字列の定義

1つの顔表情を、**「眉、左目、口、右目」**のパーツに対応する4文字の記号列で表現する。

**フォーマット:** `"<brow><left_eye><mouth><right_eye>"`

**例:**
*   `_O_O`: 普通の眉、大きい開いた目、普通の口 → **普通の顔**
*   `/o_o`: 怒り眉、小さい開いた目、普通の口 → **怒った顔**
*   `\^v^`: 下がり眉、上カーブの閉じ目、への字口、上カーブの閉じ目 → **困り笑顔？**

### 3.2. パラメータ記号化案

各パーツと記号のマッピングは `Plan02.md` の案を踏襲する。

| パーツ | 記号 | パラメータ |
| :--- | :--- | :--- |
| 眉 (1文字目) | `/` | `brow_tilt` |
| | `_` | `brow_tilt` |
| | `\` | `brow_tilt` |
| 目 (2,4文字目) | `O` | `size`=8, `openness`=1 |
| | `o` | `size`=6, `openness`=1 |
| | `-` | `openness`=0, `curve`=0 |
| | `^` | `openness`=0, `curve`=1 |
| | `v` | `openness`=0, `curve`=-1 |
| 口 (3文字目) | `^` | `mouth_curve` |
| | `_` | `mouth_curve` |
| | `v` | `mouth_curve` |
| | `O` | `mouth_open` |
| | `o` | `mouth_open` |

### 3.3. コマンドラインインターフェース

`click` の `argument` を使い、可変長の表情文字列を受け取る。

```python
@click.argument('faces', nargs=-1)
def main(faces):
    # ...
```

**利用例:**
*   **1つの表情を表示:**
    ```bash
    uv run samples/robot_face_animation.py _O_O
    ```
*   **3つの表情を1秒間隔でループ表示:**
    ```bash
    uv run samples/robot_face_animation.py /o_o _O_O \^v^
    ```
*   **引数なしの場合は、既存のランダムな表情変化モードで動作する。**

## 4. 実装方針

1.  **`FaceStateParser` クラスの実装:**
    *   `parse_face_string(face_str: str) -> dict` のようなメソッドを実装する。このメソッドは、4文字の文字列を受け取り、`FaceState` のパラメータ辞書を返す。
    *   文字列が4文字でない場合や、未定義の記号が含まれる場合はエラーを出すか、デフォルト値でフォールバックする。

2.  **`main` 関数の修正:**
    *   `click` のデコレータを `@click.argument('faces', nargs=-1)` に変更する。
    *   `faces` 引数（表情文字列のタプル）を受け取る。
    *   `faces` が存在する場合:
        *   `FaceStateParser` を使って、各表情文字列を `FaceState` オブジェクトに変換し、リストに格納する。
        *   `RobotFaceApp` にこの `FaceState` のリストを渡して初期化する。
    *   `faces` が存在しない場合:
        *   これまで通り、`mood` を使ったランダムな表情変化モードで `RobotFaceApp` を初期化する。

3.  **`RobotFaceApp` の修正:**
    *   コンストラクタで `FaceState` のリスト `face_sequence` を受け取れるようにする。
    *   `main` メソッドを修正する。
        *   `face_sequence` が与えられている場合:
            *   リスト内の `FaceState` を順番に `RobotFace` のターゲットとして設定する。
            *   `time.sleep(1)` を挟みながらシーケンスを無限ループで表示する。
        *   `face_sequence` が与えられていない場合（従来モード）:
            *   既存のランダムな表情・視線変更ロジックを実行する。

4.  **`RobotFace` の修正:**
    *   `set_target_mood(mood_name)` に加え、`set_target_state(state: FaceState)` メソッドを実装するか、既存の `set_target_mood` を拡張して `FaceState` オブジェクトも受け取れるようにする。
