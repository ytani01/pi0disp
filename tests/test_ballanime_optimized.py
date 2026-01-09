# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
from pi0disp.commands.ballanime import _loop, Ball, FpsCounter

def test_optimized_mode_calls_display_region():
    # LCDのモック
    lcd = MagicMock()
    lcd.size.width = 320
    lcd.size.height = 240
    
    # 背景画像
    bg = Image.new("RGB", (320, 240), (0, 0, 0))
    
    # ボール (1つ)
    ball = Ball(x=100, y=100, radius=20, speed=100, angle=0, fill_color=(255, 0, 0))
    balls = [ball]
    
    # FPSカウンター
    fps_counter = MagicMock()
    fps_counter.fps_text = "FPS: 30"
    
    # 1フレームだけ実行するように tracker を調整
    tracker = MagicMock()
    tracker.should_stop.side_effect = [False, True]
    
    # _loop を optimized モードで実行
    # 注: _loop 内で無限ループを避けるため tracker.should_stop を使う
    with patch("time.sleep"): # 待ち時間をスキップ
        _loop(lcd, bg, balls, fps_counter, None, 30.0, mode="optimized", tracker=tracker)
    
    # display_region が呼ばれたか確認
    # simpleモードなら display() が呼ばれ、optimizedなら display_region() が呼ばれるはず
    assert lcd.display_region.called
    assert not lcd.display.called
