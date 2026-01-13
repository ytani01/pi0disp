import time

from samples.roboface import RfRenderer, RfState


def test_render_parts_performance_improvement():
    """
    RfRenderer.render_parts の改善率を検証する。
    キャッシュなし（パラメータ変更）とキャッシュありの状態を比較し、
    キャッシュによる高速化が有意であることを確認する。
    """
    size = 240
    screen_width = 320
    screen_height = 240
    face = RfState()
    gaze_x = 0.0
    iterations = 100

    renderer = RfRenderer(size=size)

    # 1. キャッシュなし (毎回 bg_color を変えて再生成を強制)
    start_time = time.perf_counter()
    bg_color: str | tuple[int, int, int]
    for i in range(iterations):
        # わずかに色を変えてキャッシュを無効化
        bg_color = (0, 0, i % 256)
        renderer.render_parts(face, gaze_x, screen_width, screen_height, bg_color)
    no_cache_duration = time.perf_counter() - start_time
    avg_no_cache = (no_cache_duration / iterations) * 1000

    # 2. キャッシュあり (同じパラメータで継続)
    # 初回でキャッシュを生成
    bg_color = "black"
    renderer.render_parts(face, gaze_x, screen_width, screen_height, bg_color)

    start_time = time.perf_counter()
    for _ in range(iterations):
        renderer.render_parts(face, gaze_x, screen_width, screen_height, bg_color)
    cached_duration = time.perf_counter() - start_time
    avg_cached = (cached_duration / iterations) * 1000

    improvement_ratio = avg_no_cache / avg_cached if avg_cached > 0 else float("inf")

    print("\n[Performance Comparison]")
    print(f"  Avg No-Cache: {avg_no_cache:.4f} ms")
    print(f"  Avg Cached:   {avg_cached:.4f} ms")
    print(f"  Improvement:  {improvement_ratio:.2f}x faster")

    # キャッシュにより少なくとも 1.5倍 (50%改善) 以上高速化されていることを期待
    # 環境によって差はあるが、ImageOps.pad と copy の差は歴然なはず
    assert improvement_ratio > 1.5, (
        f"Performance improvement too small: {improvement_ratio:.2f}x "
        f"(Cached: {avg_cached:.4f}ms, No-Cache: {avg_no_cache:.4f}ms)"
    )
