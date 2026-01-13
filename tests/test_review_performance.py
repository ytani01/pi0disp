import time
import pytest
from PIL import Image
from samples.roboface import RfRenderer, RfState, RfConfig

def test_render_parts_baseline_performance():
    """
    RfRenderer.render_parts の実行時間を計測する。
    修正前は毎フレーム ImageOps.pad() と copy() が実行されるため、一定の時間がかかる。
    """
    size = 240
    screen_width = 320
    screen_height = 240
    bg_color = "black"
    
    renderer = RfRenderer(size=size)
    face = RfState()
    gaze_x = 0.0
    
    # 初回描画（キャッシュ生成等の影響を排除するため1回実行）
    renderer.render_parts(face, gaze_x, screen_width, screen_height, bg_color)
    
    # 複数回実行して平均時間を計測
    iterations = 100
    start_time = time.perf_counter()
    for _ in range(iterations):
        renderer.render_parts(face, gaze_x, screen_width, screen_height, bg_color)
    end_time = time.perf_counter()
    
    avg_duration_ms = ((end_time - start_time) / iterations) * 1000
    print(f"\n[Baseline] Average render_parts duration: {avg_duration_ms:.4f} ms")
    
    # 修正後のパフォーマンス検証
    # 背景キャッシュとオフセット描画により、大幅に高速化されているはず
    print(f"\n[Verification] Average render_parts duration: {avg_duration_ms:.4f} ms")
    assert avg_duration_ms < 0.8, f"Performance goal missed: {avg_duration_ms:.4f} ms (Target: < 0.8 ms)"
