
from pi0disp.commands.ballanime import ballanime
from unittest.mock import patch, MagicMock


def test_ballanime_multiple_captures(cli_mock_env):
    runner, mock_pi, _ = cli_mock_env

    mock_lcd = MagicMock()
    mock_lcd.size.width = 240
    mock_lcd.size.height = 320

    with patch("pi0disp.commands.ballanime.ST7789V") as mock_st7789v_class, \
         patch("time.sleep") as mock_sleep, \
         patch("time.time") as mock_time, \
         patch("PIL.Image.Image.save") as mock_save:
        
        mock_st7789v_class.return_value.__enter__.return_value = mock_lcd
        
        # Generator to provide increasing time and eventually stop the loop
        def time_gen():
            yield 100.0 # FpsCounter.__init__
            yield 100.0 # _loop last_frame_time init
            
            # Loop 1
            yield 101.1 # current_time (triggers capture)
            yield 101.1 # FpsCounter.update
            yield 101.1 # wait_time check
            
            # Loop 2
            yield 102.2 # current_time (triggers capture)
            yield 102.2 # FpsCounter.update
            yield 102.2 # wait_time check
            
            # Stop
            raise KeyboardInterrupt
        
        mock_time.side_effect = time_gen()
        
        result = runner.invoke(ballanime, ["--capture-interval", "1.0"])
        assert result.exit_code == 0
        # Should have captured twice
        assert mock_save.call_count == 2






