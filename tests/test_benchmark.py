import time
from unittest.mock import patch

from click.testing import CliRunner

from pi0disp.commands.ballanime import BenchmarkTracker, ballanime


def test_benchmark_tracker_logic():
    """BenchmarkTracker のロジックテスト"""
    with patch("psutil.Process"), patch("psutil.process_iter"):
        tracker = BenchmarkTracker(duration=0.5)
        tracker.start()

        # 1秒待機してサンプリングを発生させる
        time.sleep(0.6)
        tracker.update()

        assert tracker.should_stop() is True
        results = tracker.get_results()
        assert results["duration"] >= 0.5
        assert results["total_frames"] == 1


def test_ballanime_benchmark_cli():
    """ballanime --benchmark の CLI 動作確認（モック使用）"""
    runner = CliRunner()

    # ST7789V, FONT, pigpio, draw_text などをモック化
    with (
        patch("pi0disp.commands.ballanime.ST7789V") as MockLCD,
        patch("pi0disp.commands.ballanime.draw_text") as MockDrawText,
        patch("PIL.ImageFont.truetype"),
        patch("pi0disp.commands.ballanime.BenchmarkTracker") as MockTracker,
    ):
        # draw_text のモック設定 (bboxを返す)
        MockDrawText.return_value = (0, 0, 10, 10)
        # LCDのサイズをモック
        mock_lcd_instance = MockLCD.return_value.__enter__.return_value
        mock_lcd_instance.size.width = 240
        mock_lcd_instance.size.height = 240
        # 10秒待たずにすぐ終了するように設定
        mock_instance = MockTracker.return_value
        mock_instance.should_stop.side_effect = [False, True]
        mock_instance.get_results.return_value = {
            "duration": 10.0,
            "avg_fps": 30.0,
            "avg_cpu": 10.0,
            "avg_pigpiod": 5.0,
            "avg_mem_ballanime": "10.0 MB",
            "avg_mem_pigpiod": "5.0 MB",
            "total_frames": 300,
        }

        result = runner.invoke(ballanime, ["--benchmark", "1", "--num-balls", "1"])

        assert result.exit_code == 0
        assert "--- Benchmark Results ---" in result.output
        assert "Avg FPS: 30.00" in result.output

    # 秒数指定ありのテスト
    with (
        patch("pi0disp.commands.ballanime.ST7789V") as MockLCD,
        patch("pi0disp.commands.ballanime.draw_text") as MockDrawText,
        patch("PIL.ImageFont.truetype"),
        patch("pi0disp.commands.ballanime.BenchmarkTracker") as MockTracker,
    ):
        MockDrawText.return_value = (0, 0, 10, 10)
        mock_lcd_instance = MockLCD.return_value.__enter__.return_value
        mock_lcd_instance.size.width = 240
        mock_lcd_instance.size.height = 240

        mock_instance = MockTracker.return_value
        mock_instance.should_stop.side_effect = [False, True]
        mock_instance.get_results.return_value = {
            "duration": 5.0,
            "avg_fps": 30.0,
            "avg_cpu": 10.0,
            "avg_pigpiod": 5.0,
            "avg_mem_ballanime": "10.0 MB",
            "avg_mem_pigpiod": "5.0 MB",
            "total_frames": 150,
        }

        result = runner.invoke(ballanime, ["--benchmark", "5", "--num-balls", "1"])
        assert result.exit_code == 0
        # BenchmarkTracker(duration=5) が呼ばれたことを確認
        MockTracker.assert_called_with(duration=5)
