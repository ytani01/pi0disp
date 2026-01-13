import os
import time

from samples.roboface import RfParser, RobotFace


def test_visual_capture():
    """
    [事実確認]
    アニメーション中のフレームをキャプチャし、画像として保存する。
    """
    output_dir = "tmp/roboface_capture"
    os.makedirs(output_dir, exist_ok=True)

    parser = RfParser()
    initial_face = parser.parse("neutral")
    robot = RobotFace(initial_face, size=240)

    # 変化開始 (0.5秒かけて happy に)
    target_face = parser.parse("happy")
    robot.start_change(target_face, duration=0.5)

    # 5フレーム分キャプチャ
    for i in range(5):
        robot.update()
        # 画像を取得
        img = robot.get_parts_image(320, 240, (0, 0, 0))
        # 保存
        file_path = f"{output_dir}/frame_{i}.png"
        img.save(file_path)
        print(f"Captured: {file_path} (progress: {robot.updater.progress_rate():.2f})")

        time.sleep(0.1)

    # 最後に完了状態をキャプチャ
    time.sleep(0.1)
    robot.update()
    img_final = robot.get_parts_image(320, 240, (0, 0, 0))
    img_final.save(f"{output_dir}/frame_final.png")

    # ファイルが生成されたことを確認
    assert os.path.exists(f"{output_dir}/frame_0.png")
    assert os.path.exists(f"{output_dir}/frame_final.png")
