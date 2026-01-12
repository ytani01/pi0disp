import time
import pytest
import queue
from samples.roboface import (
    RfState,
    RfParser,
    RfUpdater,
    RfAnimationEngine,
)

class TestRfAnimationEngine:
    def test_thread_lifecycle(self):
        """スレッドの開始と停止が確実に行われるか"""
        parser = RfParser()
        updater = RfUpdater(parser.parse("neutral"))
        engine = RfAnimationEngine(updater=updater, parser=parser)
        
        assert not engine.is_alive()
        engine.start()
        time.sleep(0.1)
        assert engine.is_alive()
        
        engine.stop()
        # engine.queue.put("exit") # 現在のstop()はフラグを立てるだけなのでキューにも入れる必要があるかもしれない
        engine.join(timeout=1.0)
        assert not engine.is_alive()

    def test_status_api(self):
        """ステータス監視APIの動作確認"""
        parser = RfParser()
        updater = RfUpdater(parser.parse("neutral"))
        engine = RfAnimationEngine(updater=updater, parser=parser)
        
        assert not engine.is_animating
        assert engine.queue_size == 0
        assert engine.last_error is None

    def test_error_handling_notification(self):
        """サブスレッド内でのエラー発生が検知可能か"""
        parser = RfParser()
        updater = RfUpdater(parser.parse("neutral"))
        engine = RfAnimationEngine(updater=updater, parser=parser)
        engine.start()
        
        # 不正な指示（4文字以外）を投入してパースエラーを誘発させる
        engine.queue.put("invalid_face_string") 
        
        time.sleep(0.5)
        # エラーが記録されているはず
        assert engine.last_error is not None
        
        # エラー後もスレッドが動いていることを確認
        assert engine.is_alive()
        
        engine.stop()
        engine.join()
            
        engine.stop()
        engine.join()
