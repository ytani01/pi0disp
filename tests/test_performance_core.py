# -*- coding: utf-8 -*-
from pi0disp.utils.performance_core import RegionOptimizer


def test_region_optimizer_merge_overlapping():
    optimizer = RegionOptimizer()
    # 重なり合う2つの矩形 (x, y, w, h)
    regions = [(10, 10, 50, 50), (40, 40, 50, 50)]
    merged = optimizer.merge_regions(regions)
    assert len(merged) == 1
    assert merged[0] == (10, 10, 80, 80)


def test_region_optimizer_merge_separate():
    optimizer = RegionOptimizer()
    # 離れた2つの矩形
    regions = [(10, 10, 10, 10), (100, 100, 10, 10)]
    merged = optimizer.merge_regions(regions)
    assert len(merged) == 2


def test_region_optimizer_empty():
    optimizer = RegionOptimizer()
    assert optimizer.merge_regions([]) == []


def test_region_optimizer_single():
    optimizer = RegionOptimizer()
    assert optimizer.merge_regions([(10, 10, 10, 10)]) == [(10, 10, 10, 10)]


def test_region_optimizer_merge_with_threshold():
    optimizer = RegionOptimizer()
    # 少し離れているが、閾値内であればマージされる
    regions = [(10, 10, 10, 10), (25, 10, 10, 10)]
    # マージ後の面積増加が許容範囲内ならマージされるロジックにする予定
    merged = optimizer.merge_regions(regions, area_threshold=2.0)
    # (10, 10, 10, 10) と (25, 10, 10, 10) をマージすると (10, 10, 25, 10)
    # 元の合計面積: 200, マージ後: 250 -> 1.25倍なのでマージされるはず
    assert len(merged) == 1
    assert merged[0] == (10, 10, 25, 10)
