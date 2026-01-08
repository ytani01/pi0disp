import time
from unittest.mock import MagicMock, patch

from samples.roboface2 import (
    InteractiveMode,
    RfParser,
    RobotFace,
)


def test_gaze_manager_autonomous_movement():
    """視線マネージャが自律的に視線を動かすことをテストする。"""
    parser = RfParser()
    initial_face = parser.parse("_OO_")
    face = RobotFace(initial_face, size=240, debug=True)

    # 開始前の視線
    start_x = face.gaze_manager.current_x

    face.start()
    try:
        # しばらく待機して、視線が動くのを待つ
        # RfGazeManager は lerp で徐々に動く
        time.sleep(1.0)
        mid_x = face.gaze_manager.current_x

        # 視線が初期位置(0)から動いているはず（ターゲットがランダムに設定されるため）
        # ただし、運悪く0が選ばれる可能性もゼロではないので、数回試行するか、
        # ターゲットが設定されていることを確認する。
        assert face.gaze_manager.target_x != 0 or mid_x != start_x

        # ターゲットを手動で設定して追従を確認
        face.set_gaze(5.0)
        assert face.gaze_manager.target_x == 5.0
        time.sleep(0.5)
        end_x = face.gaze_manager.current_x
        # 5.0 に向かって近づいているはず
        assert abs(end_x - start_x) > 0

    finally:
        face.stop()


def test_robot_face_thread_lifecycle():
    """RobotFace のスレッド開始・停止ライフサイクルをテストする。"""
    parser = RfParser()
    face = RobotFace(parser.parse("_OO_"))

    assert not face.gaze_manager.is_alive()
    face.start()
    assert face.gaze_manager.is_alive()
    face.stop()
    time.sleep(0.2)
    assert not face.gaze_manager.is_alive()


def test_interactive_mode_background_draw():
    """InteractiveMode が入力待ちの間も描画を続けていることを確認する。"""
    # 実際には描画デバイスとして Mock を渡す
    mock_disp = MagicMock()
    mock_disp.width = 320
    mock_disp.height = 240

    mode = InteractiveMode(mock_disp, "black", debug=True)

    # input() を遅延させて、背景スレッドが動く時間を確保する
    def slow_input(prompt):
        time.sleep(0.5)
        return slow_input.inputs.pop(0)

    slow_input.inputs = ["_^^v", "q"]

    with patch("builtins.input", side_effect=slow_input):
        mode.run()

    # 全体更新(full=True)に変更したため、display が複数回呼ばれているはず
    print(f"DEBUG: display count = {mock_disp.display.call_count}")
    assert mock_disp.display.call_count > 1
