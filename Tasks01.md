# `samples/robot_face_animation.py` リファクタリングタスクリスト

- [x] git checkout -b feature/Tasks01
- [x] `samples/robot_face_animation.py` の `EyeState` クラスを削除する。
- [x] `samples/robot_face_animation.py` の `FaceState` クラスの定義をフラットな構造に変更する。
- [x] `samples/robot_face_animation.py` の `FaceState.copy()` メソッドを新しい構造に合わせて修正する。
- [x] `mise run lint` を実行し、リンティングエラーを修正する。
- [x] `samples/robot_face_animation.py` の `RobotFace.MOODS` の定義を全面的に書き換える。
- [x] `samples/robot_face_animation.py` の `RobotFace.update()` メソッド内の `left_eye`、`right_eye` へのアクセスを修正する。
- [x] `mise run lint` を実行し、リンティングエラーを修正する。
- [x] `samples/robot_face_animation.py` の `RobotFace._draw_one_eye()` メソッドのシグネチャと内部実装を修正する。
- [x] `samples/robot_face_animation.py` の `RobotFace._draw_eyes()` メソッドから `_draw_one_eye()` を呼び出す部分を修正する。
- [x] `mise run lint` を実行し、リンティングエラーを修正する。
- [x] `mise run test` を実行し、テストが成功することを確認する。テストが失敗した場合は、エラーがなくなるまで修正する。
- [x] `git add .`
- [x] `git commit -m "refactor: Flatten FaceState structure in robot_face_animation.py"`
