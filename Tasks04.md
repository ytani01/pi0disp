# `samples/robot_face_animation2.py` 改造タスクリスト

- [x] git checkout -b feature/Tasks04
- [x] `cp samples/robot_face_animation.py samples/robot_face_animation2.py` を実行する。
- [x] `samples/robot_face_animation2.py` の `RobotFaceApp.main` メソッド内の `if self.face_sequence:` ブロックのロジックを、Plan04.mdの擬似コードに基づいて書き換える。
- [x] `mise run lint` を実行し、リンティングエラーを修正する。
- [x] `mise run test` を実行し、既存のテストが壊れていないことを確認する。
- [x] 手動で動作確認を行う (`uv run samples/robot_face_animation2.py /o_o _O_O`)。
- [x] `git add samples/robot_face_animation2.py`
- [ ] `git commit -m "feat: Create robot_face_animation2 with gaze animation"`
