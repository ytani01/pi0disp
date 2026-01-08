import time

import numpy as np

from samples.roboface2 import RfParser, RfRenderer, RobotFace


def test_renderer_consistency():
    """レンダラーが異なる状態に対して異なる画像を出力するか検証する。"""
    renderer = RfRenderer(size=240)
    parser = RfParser()

    # 1. ニュートラルな表情をレンダリング
    face1 = parser.parse("_OO_")
    img1 = renderer.render_parts(
        face1,
        gaze_offset_x=0,
        screen_width=320,
        screen_height=240,
        bg_color="black",
    )
    arr1 = np.array(img1)

    # 2. 別の表情（happy）をレンダリング
    face2 = parser.parse("_OOv")
    img2 = renderer.render_parts(
        face2,
        gaze_offset_x=0,
        screen_width=320,
        screen_height=240,
        bg_color="black",
    )
    arr2 = np.array(img2)

    # 3. 視線だけ変えてレンダリング
    img3 = renderer.render_parts(
        face1,
        gaze_offset_x=5.0,
        screen_width=320,
        screen_height=240,
        bg_color="black",
    )
    arr3 = np.array(img3)

    # 検証
    diff_face = np.any(arr1 != arr2)
    diff_gaze = np.any(arr1 != arr3)

    print(f"DEBUG: Face change detected in pixels: {diff_face}")
    print(f"DEBUG: Gaze change detected in pixels: {diff_gaze}")

    assert diff_face, (
        "Renderer output did not change when face state changed!"
    )
    assert diff_gaze, (
        "Renderer output did not change when gaze offset changed!"
    )


def test_robot_face_state_update():
    """RobotFace.update() が内部状態を実際に遷移させているか検証する。"""
    parser = RfParser()
    initial_face = parser.parse("_OO_")

    # コピーの挙動を確認
    copied_face = initial_face.copy()
    print(f"DEBUG: initial_face.brow ID: {id(initial_face.brow)}")
    print(f"DEBUG: copied_face.brow ID : {id(copied_face.brow)}")
    assert id(initial_face.brow) != id(copied_face.brow), (
        "Shallow copy detected! brow instances are shared."
    )

    robot = RobotFace(initial_face, size=240)

    target_face = parser.parse("vOOv")  # 眉を v (25.0) に変更
    robot.start_change(target_face, duration=0.1)

    print(f"DEBUG: Initial tilt: {robot.updater.current_face.brow.tilt}")

    # 少し時間を進めて更新
    time.sleep(0.05)
    robot.update()
    mid_tilt = robot.updater.current_face.brow.tilt
    print(f"DEBUG: Mid-way tilt: {mid_tilt}")

    time.sleep(0.1)
    robot.update()
    final_tilt = robot.updater.current_face.brow.tilt
    print(f"DEBUG: Final tilt: {final_tilt}")

    assert robot.updater.is_changing or final_tilt == target_face.brow.tilt
    assert mid_tilt != initial_face.brow.tilt, (
        "Internal state did not change after update!"
    )


if __name__ == "__main__":
    try:
        print("Running renderer consistency test...")
        test_renderer_consistency()
        print("Renderer test PASSED.")

        print("\nRunning state update test...")
        test_robot_face_state_update()
        print("State update test PASSED.")

        print(
            "\nAll debug tests PASSED. The core logic is working in isolation."
        )
    except AssertionError as e:
        print(f"\nTest FAILED: {e}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback

        traceback.print_exc()
