import os
import time

from samples.roboface import RfParser, RfRenderer, RfState, RfUpdater

TMP_DIR = "/home/ytani/.gemini/tmp/c033fec850cc00bf431a0c373ea26cfd3e25f22f3dee519ec8caf7bbf9303d54"


def test_duration_zero_fix():
    """Task 1.1: duration=0.0 の際に即座に表情が切り替わることを確認する"""
    parser = RfParser()
    initial_face = parser.parse("_OO_")
    target_face = parser.parse("vOOv")

    updater = RfUpdater(initial_face)

    # duration=0.0 で開始
    updater.start_change(target_face, duration=0.0)

    # 現状のバグでは duration=0.0 はデフォルト値(0.9)に上書きされるため、
    # progress_rate は 0.0 に近いはず。
    # 期待値は 1.0。
    assert updater.progress_rate() == 1.0

    updater.update()
    assert updater.is_changing is False
    assert updater.current_face.brow.tilt == target_face.brow.tilt


def test_bg_color_string_fix():
    """Task 1.2: bg_color に文字列を指定した際、正しく反映されることを確認する"""
    renderer = RfRenderer(size=200)  # 200x200 face
    state = RfState()

    # 320x240 の画面に描画。背景色は "white" (255, 255, 255)
    img = renderer.render_parts(state, 0.0, 320, 240, "white")
    img.save(os.path.join(TMP_DIR, "test_bg_color_string.png"))

    pixel = img.getpixel((319, 239))
    assert pixel == (255, 255, 255)


def test_bg_cache_fix():
    """Task 1.3: bg_color が変更された際、キャッシュが更新されることを確認する"""
    renderer = RfRenderer(size=200)
    state = RfState()

    # 最初は黒で描画
    img1 = renderer.render_parts(state, 0.0, 240, 240, (0, 0, 0))
    assert img1.getpixel((0, 0)) == (0, 0, 0)

    # 次に赤で描画
    img2 = renderer.render_parts(state, 0.0, 240, 240, (255, 0, 0))
    img2.save(os.path.join(TMP_DIR, "test_bg_cache_update.png"))

    assert img2.getpixel((0, 0)) == (255, 0, 0)


def test_very_short_duration():
    """非常に短い duration でも動作することを確認する"""
    parser = RfParser()
    initial_face = parser.parse("_OO_")
    target_face = parser.parse("vOOv")
    updater = RfUpdater(initial_face)

    # 非常に短い duration (1ms)
    updater.start_change(target_face, duration=0.001)
    time.sleep(0.002)
    updater.update()

    assert updater.progress_rate() == 1.0
    assert updater.is_changing is False
