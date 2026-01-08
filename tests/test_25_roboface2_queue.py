import queue
import time

from samples.roboface2 import RfGazeManager, RfParser, RobotFace


def test_gaze_manager_queue_init():
    """RfGazeManager が queue を持っていることを確認する。"""
    gm = RfGazeManager()
    assert hasattr(gm, "queue")
    assert isinstance(gm.queue, queue.Queue)


def test_gaze_manager_process_expression():
    """キュー経由で表情変更が処理されることを確認する。"""
    # このテストは実装前なので失敗するはず
    # RobotFace に紐付ける必要があるかもしれない
    parser = RfParser()
    initial_face = parser.parse("_OO_")
    face = RobotFace(initial_face, debug=True)

    face.start()
    try:
        # キューに新しい表情を送る
        face.gaze_manager.queue.put("^oo^")
        time.sleep(0.5)

        # 表情が更新されているか確認
        # RobotFace.updater.target_face が更新されているはず
        assert face.updater.target_face != initial_face
    finally:
        face.stop()


def test_gaze_manager_exit_command():
    """exit コマンドでスレッドが停止することを確認する。"""
    gm = RfGazeManager()
    gm.start()
    assert gm.is_alive()

    gm.queue.put("exit")
    time.sleep(0.5)
    assert not gm.is_alive()


def test_sequential_expression_processing():
    """複数の表情が順番に（アニメーションを待って）処理されることをテストする。"""
    parser = RfParser()
    # 初期表情 _OO_
    face = RobotFace(parser.parse("_OO_"), debug=True)

    face.start()
    try:
        # 3つの表情を立て続けに投入
        # 1. ^oo^ (0.9s) -> 2. >oo< (0.9s) -> 3. vOOv (0.9s)
        expressions = ["^oo^", ">oo<", "vOOv"]
        for expr in expressions:
            face.enqueue_face(expr)

        # 表情を変化させるための擬似描画ループを回す
        # これをしないと is_changing が False に戻らない
        start_time = time.time()
        processed_expressions = []

        while time.time() - start_time < 3.0:  # 合計3秒間監視
            face.update()
            current_target = face.updater.target_face
            # 現在処理中のターゲットを記録（重複排除）
            if (
                not processed_expressions
                or processed_expressions[-1] != current_target
            ):
                processed_expressions.append(current_target)

            time.sleep(0.05)

            # 記録されたターゲットの中に、投入した表情が順番に含まれているか 確認

            # [初期状態, ^oo^, >oo<, vOOv] のはず

            # ログ出力用

        print(
            f"DEBUG: Processed expressions count: {len(processed_expressions)}"
        )

        # 記録されたターゲット（重複排除済み）の中に、期待される表情が含まれているか
        # タイミングにより最初の "_OO_" が記録されない場合があるため、
        # expressions が順番に出現することを確認する。
        actual_idx = 0
        for expected in [parser.parse(e) for e in expressions]:
            # expected が出現するまで actual_idx を進める
            found = False
            while actual_idx < len(processed_expressions):
                if processed_expressions[actual_idx] == expected:
                    found = True
                    break
                actual_idx += 1
            assert found, f"Expression {expected} not found in sequence"

    finally:
        face.stop()
