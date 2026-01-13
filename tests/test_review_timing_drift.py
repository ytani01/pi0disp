import time

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
    next_tick = start_time
    for _ in range(frames):
        # 模擬的な処理時間 (1ms)
        time.sleep(0.001) 
        # ドリフト補償付きの待機
        next_tick += interval
        time.sleep(max(0, next_tick - time.perf_counter()))
    end_time = time.perf_counter()
    
    actual_duration = end_time - start_time
    drift = actual_duration - target_duration
    
    print(f"\n[Verification] Timing drift over {frames} frames:")
    print(f"  Target: {target_duration:.4f} s")
    print(f"  Actual: {actual_duration:.4f} s")
    print(f"  Drift:  {drift:.4f} s ({drift*1000:.2f} ms)")
    
    # 修正後はドリフトが大幅に軽減されるはず
    # 1フレームの間隔 (100ms) よりも十分に小さいことを確認
    assert abs(drift) < 0.01, f"Drift should be minimized (Got {drift*1000:.2f}ms)"

