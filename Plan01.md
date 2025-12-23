# `samples/robot_face_animation.py` リファクタリング計画書

## 1. 目的

`FaceState`と`EyeState`の階層構造を解消し、`FaceState`をフラットなデータ構造にすることで、コードの可読性とメンテナンス性を向上させる。

## 2. 変更内容

### 2.1. `EyeState`クラスの廃止

`EyeState`クラスを削除する。

### 2.2. `FaceState`クラスのフラット化

`FaceState`クラスを以下のように変更する。

**変更前:**
```python
@dataclass
class FaceState:
    mouth_curve: float = 0
    brow_tilt: float = 0
    mouth_open: float = 0
    left_eye: EyeState = field(default_factory=lambda: EyeState())
    right_eye: EyeState = field(default_factory=lambda: EyeState())
```

**変更後:**
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
`EyeState`のコンストラクタで行っていたロジック（`curve`の値による`openness`の設定）は、`FaceState`のインスタンス化時に直接値を設定するように変更する。

### 2.3. `RobotFace.MOODS`の更新

`FaceState`の変更に伴い、`RobotFace.MOODS`の定義を新しい`FaceState`の構造に合わせて更新する。`EyeState`のインスタンス化をなくし、各`left_eye_*`, `right_eye_*`フィールドに直接値を設定する。

**例（`wink-r`）:**

**変更前:**
```python
"wink-r": FaceState(
    mouth_curve=15,
    brow_tilt=0,
    left_eye=EyeState(curve=1),
    right_eye=EyeState(),
),
```

**変更後:**
```python
"wink-r": FaceState(
    mouth_curve=15,
    brow_tilt=0,
    left_eye_openness=0.0,
    left_eye_curve=1,
    # right_eyeはデフォルト値
),
```

### 2.4. `RobotFace`クラス内のメソッド修正

`FaceState`のフラット化に伴い、以下のメソッド内の`left_eye`, `right_eye`へのアクセス方法を修正する。

- `RobotFace.update()`
- `RobotFace._draw_one_eye()`
- `RobotFace._draw_eyes()`
- `FaceState.copy()`

**例 (`RobotFace.update`)**

**変更前:**
```python
c.left_eye.openness = lerp(
    c.left_eye.openness, t.left_eye.openness, speed
)
```

**変更後:**
```python
c.left_eye_openness = lerp(
    c.left_eye_openness, t.left_eye_openness, speed
)
```

### 2.5. `_draw_one_eye`の引数変更

`_draw_one_eye`は`EyeState`オブジェクトを引数に取っていたが、フラット化された`FaceState`のフィールドを直接受け取るように変更する。

**変更前:**
```python
def _draw_one_eye(self, draw, eye_x, eye_y, eye_state: EyeState, gaze_offset):
    # eye_state.size
    # eye_state.openness
    # ...
```

**変更後:**
```python
def _draw_one_eye(self, draw, eye_x, eye_y, eye_size, eye_openness, eye_curve, gaze_offset):
    # eye_size
    # eye_openness
    # ...
```

これに伴い、`_draw_eyes`メソッドからの呼び出しも修正する。

## 3. 作業手順

1. `EyeState`クラスを削除する。
2. `FaceState`クラスの定義をフラットな構造に変更する。
3. `FaceState.copy()`メソッドを新しい構造に合わせて修正する。
4. `RobotFace.MOODS`の定義を全面的に書き換える。
5. `RobotFace.update()`メソッド内の`left_eye`、`right_eye`へのアクセスを修正する。
6. `RobotFace._draw_one_eye()`メソッドのシグネチャと内部実装を修正する。
7. `RobotFace._draw_eyes()`メソッドから`_draw_one_eye()`を呼び出す部分を修正する。
8. 動作確認を行う。
