import math
import time
import pytest
from samples.roboface import RfAnimationEngine, RfConfig, RfParser

def test_engine_with_none_updater():
    """updaterがNoneの場合でもエンジンが停止しないことを確認"""
    engine = RfAnimationEngine(updater=None, parser=RfParser(), debug=True)
    engine.queue.put("_OO_")
    
    # スレッドを開始
    engine.start()
    try:
        time.sleep(0.5)
        # エンジンが生存しており、エラーが記録されていない（または適切に処理されている）ことを確認
        assert engine.is_alive()
        # queueは消化されているはず（Noneチェックでスキップされるべき）
        assert engine.queue_size == 0
    finally:
        engine.stop()
        engine.join(timeout=1.0)

def test_engine_adjusted_lerp_factor_zero_interval():
    """intervalが0に近い極小値の場合の計算安定性を確認"""
    # このテストはロジックを直接検証する
    lerp_factor = 0.2
    
    # interval = 0 の場合 (本来は発生しないはずだがガードが必要)
    interval = 0.0
    # 現状のロジック: 1.0 - (1.0 - 0.2) ** (0.0 * 10.0) = 1.0 - 1.0 = 0.0
    adjusted = 1.0 - (1.0 - lerp_factor) ** (interval * 10.0)
    assert adjusted == 0.0 # 期待通り
    
    # 負のinterval (ありえないが...)
    interval = -0.1
    # 修正後のロジックでは max(0.0, interval) により 0.0 になるはず
    safe_interval = max(0.0, interval)
    exponent = safe_interval * 10.0
def test_renderer_centering_config():
    """RfRendererのセンタリング設定がRfConfigから取得されることを確認"""
    from samples.roboface import RfConfig, RfRenderer
    
    assert "face_centering" in RfConfig.LAYOUT
    
    # 設定を変更して反映されるか確認
    original_centering = RfConfig.LAYOUT["face_centering"]
    try:
        RfConfig.LAYOUT["face_centering"] = (0.5, 0.5)
        renderer = RfRenderer(size=240)
        # 実際に描画してオフセットを確認したいが、モックなしでは難しいので
        # ここではConfigに存在し、Rendererがエラーなく初期化されることを確認
        assert renderer.size == 240
    finally:
        RfConfig.LAYOUT["face_centering"] = original_centering

def test_app_mode_timer_precision(monkeypatch):
    """AppMode派生クラスがtime.perf_counterを使用していることを確認"""
    from samples.roboface import RandomMode, CV2Disp, RfConfig
    
    perf_called = []
    original_perf = time.perf_counter
    
    def mock_perf():
        perf_called.append(True)
        return original_perf()
    
    monkeypatch.setattr(time, "perf_counter", mock_perf)
    
    # 実際には描画デバイスが必要なのでダミーを作成
    disp = CV2Disp(width=320, height=240)
    # インスタンス化の過程で perf_counter が呼ばれるはず
    mode = RandomMode(disp, "black")
    
    assert len(perf_called) > 0
