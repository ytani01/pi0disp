# -*- coding: utf-8 -*-
import pytest
from pi0disp.commands.ballanime import Ball
from pi0disp.utils.sprite import CircleSprite

def test_ball_inheritance():
    # BallがCircleSpriteを継承しているか
    ball = Ball(x=100, y=100, radius=20, speed=100, angle=0, fill_color=(255, 0, 0))
    assert isinstance(ball, CircleSprite)

def test_ball_dirty_region():
    ball = Ball(x=100, y=100, radius=20, speed=100, angle=0, fill_color=(255, 0, 0))
    
    # 初回描画
    ball.record_current_bbox()
    assert ball.prev_bbox == (80, 80, 120, 120)
    
    # 移動
    ball.cx += 10
    ball.cy += 5
    
    # dirty_region の計算
    # prev: (80, 80, 120, 120)
    # current: (90, 85, 130, 125)
    # merged: (80, 80, 130, 125)
    dirty = ball.get_dirty_region()
    assert dirty == (80, 80, 130, 125)
    
    # 記録更新
    ball.record_current_bbox()
    assert ball.get_dirty_region() is None
