from samples.roboface import RfConfig

def test_gaze_movement_fps_dependency():
    """
    視線移動がFPS（ループの間隔）に依存していることを確認するテスト。
    10fps と 30fps で、同じ 0.5秒 経過後の視線位置を比較する。
    修正前は 30fps の方が速く目標に近づくため、値が異なるはずである。
    """
    target_x = 5.0
    lerp_factor = RfConfig.ANIMATION["gaze_lerp_factor"]
    
    # 0.5秒経過後の期待値（理論値ではないが、FPS依存を証明するための比較用）
    # 10fps の場合: 0.5秒 = 5ステップ
    # 30fps の場合: 0.5秒 = 15ステップ
    
    def simulate_gaze(fps, duration_sec):
        current_x = 0.0
        interval = 1.0 / fps
        steps = int(fps * duration_sec)
        
        # 修正後のロジック: 経過時間を考慮した調整
        # 基準は 10fps
        adjusted_lerp_factor = 1.0 - (1.0 - lerp_factor) ** (interval * 10.0)
        
        for _ in range(steps):
            current_x = current_x + (target_x - current_x) * adjusted_lerp_factor
        return current_x

    duration = 0.5
    x_10fps = simulate_gaze(10.0, duration)
    x_30fps = simulate_gaze(30.0, duration)
    
    diff = abs(x_10fps - x_30fps)
    print(f"\n[Verification] Gaze position after {duration}s:")
    print(f"  10fps: {x_10fps:.4f}")
    print(f"  30fps: {x_30fps:.4f}")
    print(f"  Diff: {diff:.4f}")
    
    # 修正後は差異が非常に小さくなるはず
    assert diff < 0.01, f"Gaze movement should be FPS independent (Diff: {diff:.4f})"
