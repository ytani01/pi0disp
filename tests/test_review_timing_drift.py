import time
import pytest

def test_timing_drift_baseline():
    """
    単純な time.sleep(interval) によるループで累積誤差（ドリフト）が発生することを確認する。
    10fps で 50フレーム実行した場合、理想的な時間は 5.0秒 である。
    """
    fps = 10.0
    interval = 1.0 / fps
    frames = 50
    target_duration = frames * interval # 5.0s
    
    start_time = time.perf_counter()
    for _ in range(frames):
        # 模擬的な処理時間 (1ms)
        time.sleep(0.001) 
        # 単純な待機
        time.sleep(interval)
    end_time = time.perf_counter()
    
    actual_duration = end_time - start_time
    drift = actual_duration - target_duration
    
    print(f"\n[Baseline] Timing drift over {frames} frames:")
    print(f"  Target: {target_duration:.4f} s")
    print(f"  Actual: {actual_duration:.4f} s")
    print(f"  Drift:  {drift:.4f} s ({drift*1000:.2f} ms)")
    
    # ドリフトが発生している（5.0s を超えている）ことを確認
    # 50フレーム * 1ms 処理だけでも 50ms ズレるはず。
    assert drift > 0.04, f"Drift should be significant (Expected > 40ms, got {drift*1000:.2f}ms)"

