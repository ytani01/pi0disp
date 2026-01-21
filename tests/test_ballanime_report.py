import os
from unittest.mock import patch

from click.testing import CliRunner

from pi0disp.commands.ballanime import ballanime


def test_ballanime_report_columns():
    """
    Test that the benchmark report includes the 'Mem (pig)' column.
    (This should fail until the code is updated)
    """
    runner = CliRunner()
    report_file = "ballanime-report.md"

    # Remove report file if exists
    if os.path.exists(report_file):
        os.remove(report_file)

    # Mock ST7789V and other internals to avoid actual hardware access
    with (
        patch("pi0disp.commands.ballanime.ST7789V") as MockLcd,
        patch("pi0disp.commands.ballanime._loop"),
        patch("pi0disp.commands.ballanime.BenchmarkTracker") as MockTracker,
    ):
        # Setup mock LCD size
        mock_lcd_inst = MockLcd.return_value.__enter__.return_value
        mock_lcd_inst.size.width = 320
        mock_lcd_inst.size.height = 240

        # Setup mock results
        mock_tracker_inst = MockTracker.return_value
        mock_tracker_inst.get_results.return_value = {
            "duration": 10.0,
            "avg_fps": 30.0,
            "avg_cpu": 10.0,
            "avg_pigpiod": 5.0,
            "avg_mem_ballanime": "10.0 MB",
            "avg_mem_pigpiod": "5.0 MB",
            "total_frames": 300,
        }

        # Invoke command with benchmark option
        result = runner.invoke(
            ballanime, ["--benchmark", "1", "--mode", "simple"]
        )
        if result.exit_code != 0:
            print(result.output)
            if result.exception:
                import traceback

                traceback.print_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )
        assert result.exit_code == 0

        # Check report file
        assert os.path.exists(report_file)
        with open(report_file, "r") as f:
            content = f.read()

        # Expected header: | Date | Mode | Balls | Target FPS | SPI | Avg FPS | CPU (App) | CPU (pigpiod) | Mem (App) | Mem (pig) |
        # Expected data row: | ... | ... | ... | ... | ... | ... | ... | ... | 10.0 MB | 5.0 MB |

        assert "Mem (pig)" in content
        assert "5.0 MB" in content
