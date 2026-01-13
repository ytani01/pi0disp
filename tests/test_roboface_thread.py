import time
from samples.roboface import (
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

    def test_infinite_loop_bug_reproduction(self):
        """不正なデータ(int)投入時に無限ループに陥らず、次の指示を処理できるか"""
        parser = RfParser()
        updater = RfUpdater(parser.parse("neutral"))
        engine = RfAnimationEngine(updater=updater, parser=parser)
        engine.start()
        
        # 1. 不正なデータ(int)を投入
        engine.queue.put(123) 
        time.sleep(0.2)
        
        # 2. その後、正常なコマンドを投入
        engine.queue.put("happy")
        
        # 正常に処理されれば、一定時間内にアニメーションが開始されるはず
        # (無限ループバグがある場合、ここで 'happy' が永遠に取り出されない)
        success = False
        start_time = time.time()
        while time.time() - start_time < 2.0:
            if engine.is_animating or engine.queue_size == 0:
                # 少なくともキューから取り出されていれば、ループは回っている
                success = True
                break
            time.sleep(0.1)
            
        try:
            assert success, "Engine is likely stuck in an infinite loop due to non-string input"
        finally:
            engine.stop()
            engine.join(timeout=1.0)
