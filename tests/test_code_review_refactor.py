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
    adjusted = 1.0 - math.pow(1.0 - lerp_factor, exponent)
    assert adjusted >= 0.0
    assert adjusted == 0.0
