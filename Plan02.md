# `samples/robot_face_animation.py` インタラクティブ表情操作機能 計画書

## 1. 目的

`samples/robot_face_animation.py` に、コマンドラインから顔の各パーツ（目、眉、口）の状態を個別に、かつ簡易的に指定できるインタラクティブな操作機能を追加する。これにより、定義済みの `MOODS` パターン以外の表情を動的に生成できるようにする。

## 2. 現状のコードベース

直近のリファクタリングにより、`EyeState` は廃止され、`FaceState` は以下のフラットな構造になっている。

```python
@dataclass
class FaceState:
    mouth_curve: float = 0
    brow_tilt: float = 0
    mouth_open: float = 0
    left_eye_openness: float = 1.0
    left_eye_size: float = 8.0
    left_eye_curve: float = 0.0
    right_eye_openness: float = 1.0
    right_eye_size: float = 8.0
    right_eye_curve: float = 0.0
```

## 3. 提案内容：記号による表情指定

各パーツの代表的な状態を1文字の記号にマッピングし、コマンドラインから表情を簡易に指定できる仕組みを導入する。

### 3.1. パラメータ記号化案

| パーツ | オプション | 記号 | パラメータ | 値 | 意味 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 口 | `--mouth` | `^` | `mouth_curve` | 15 | 笑顔 |
| | | `_` | `mouth_curve` | 0 | 真顔 |
| | | `v` | `mouth_curve` | -10 | への字口 |
| | | `O` | `mouth_open` | 1.1 | 大きく開く |
| | | `o` | `mouth_open` | 0.85 | 小さく開く |
| 眉 | `--brow` | `/` | `brow_tilt` | 25 | 怒り眉 |
| | | `_` | `brow_tilt` | 0 | 普通 |
| | | `\` | `brow_tilt` | -10 | 下がり眉 |
| 左目 | `--left-eye` | `O` | `size`=8, `openness`=1 | 大きい開いた目 |
| | | `o` | `size`=6, `openness`=1 | 小さい開いた目 |
| | | `-` | `openness`=0, `curve`=0 | 閉じた目(直線) |
| | | `^` | `openness`=0, `curve`=1 | 閉じた目(上カーブ) |
| | | `v` | `openness`=0, `curve`=-1 | 閉じた目(下カーブ) |
| 右目 | `--right-eye`| (左目と同じ) | | | |

### 3.2. コマンドラインインターフェースの実装

`@click.command` で定義されている `main` 関数に、以下のオプションを追加する。

```python
@click.option('--left-eye', 'left_eye_str', type=str, help='Left eye symbol: O, o, -, ^, v')
@click.option('--right-eye', 'right_eye_str', type=str, help='Right eye symbol: O, o, -, ^, v')
@click.option('--mouth', 'mouth_str', type=str, help='Mouth symbol: ^, _, v, O, o')
@click.option('--brow', 'brow_str', type=str, help='Brow symbol: /, _, \')
```

- 引数で受け取った記号を、後述するパーサーで `FaceState` のパラメータに変換する。
- 引数が指定されなかった場合は、`MOODS` の `neutral` または引数で指定された初期 `mood` の状態をベースにする。
- 指定されたパーツのパラメータのみを上書きする。

### 3.3. 記号パーサーの実装

記号を `FaceState` のパラメータ辞書に変換するパーサークラス（例: `FaceStateParser`）を実装する。

```python
class FaceStateParser:
    EYE_MAP = {
        'O': {'size': 8.0, 'openness': 1.0, 'curve': 0.0},
        'o': {'size': 6.0, 'openness': 1.0, 'curve': 0.0},
        '-': {'size': 8.0, 'openness': 0.0, 'curve': 0.0},
        '^': {'size': 8.0, 'openness': 0.0, 'curve': 1.0},
        'v': {'size': 8.0, 'openness': 0.0, 'curve': -1.0},
    }
    # MOUTH_MAP, BROW_MAPも同様に定義

    def parse(self, left_eye_str=None, right_eye_str=None, ...):
        params = {}
        if left_eye_str:
            # EYE_MAPから値を取得し、'left_eye_' prefix をつけて params に追加
        # ... 他のパーツも同様
        return params
```

## 4. 実装方針

1.  `FaceStateParser` クラスを `samples/robot_face_animation.py` 内に実装する。記号とパラメータ値のマッピング辞書を含む。
2.  `main` 関数に `click` オプションを追加する。
3.  `main` 関数内で、引数として渡された記号を `FaceStateParser` でパースし、`FaceState` のパラメータ辞書を生成する。
4.  初期 `mood` からベースとなる `FaceState` を取得し、3で生成したパラメータ辞書で値を上書きする。
5.  生成した `FaceState` を `RobotFace` に設定してアニメーションを開始するように `RobotFaceApp` の初期化処理を修正する。`set_target_mood` を `set_target_state(state: FaceState)` のようなメソッドに変更するか、`RobotFace` のコンストラクタで `FaceState` を直接受け取れるようにする。
6.  インタラクティブな操作のため、アニメーションのループをなくし、指定された表情を一度だけ表示して終了するように変更する。（または、`--loop` のようなオプションを追加する）

```