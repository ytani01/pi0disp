
import queue
import time
import threading
from samples.roboface2 import RfGazeManager, RfParser, RobotFace, RfState

def test_gaze_manager_queue_init():
    """RfGazeManager が queue を持っていることを確認する。"""
    gm = RfGazeManager()
    assert hasattr(gm, 'queue')
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
