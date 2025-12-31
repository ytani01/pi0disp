"""Tests for ST7789V display driver."""

from pi0disp import ST7789V, DispSize, SpiPins


def create_st7789v_instance(invert=None, bgr=None):
    return ST7789V(
        pin=SpiPins(rst=25, dc=24, bl=23),
        size=DispSize(240, 320),
        rotation=0,
        invert=invert,
        bgr=bgr,
    )


def test_init_success(mock_pi_instance):
    disp = create_st7789v_instance()
    assert disp.pi == mock_pi_instance


def test_color_settings(mock_pi_instance):
    """invert と bgr の設定が正しく保持されるかテスト."""
    # 明示的に True/False を指定
    disp = create_st7789v_instance(invert=True, bgr=True)
    assert disp._invert is True
    assert disp._bgr is True

    disp2 = create_st7789v_instance(invert=False, bgr=False)
    assert disp2._invert is False
    assert disp2._bgr is False


def test_madctl_bgr_bit(mock_pi_instance):
    """MADCTL (0x36) 命令の BGR ビット (Bit 3) が bgr 設定を反映しているかテスト."""
    # bgr=True の場合、Bit 3 が 1 になるはず
    disp = create_st7789v_instance(bgr=True)
    mock_pi_instance.spi_write.reset_mock()
    # set_rotation で MADCTL が発行される
    disp.set_rotation(0)

    # MADCTL (0x36) を探す
    madctl_calls = [
        i
        for i, call in enumerate(mock_pi_instance.spi_write.call_args_list)
        if call[0][1] == [0x36]
    ]
    assert len(madctl_calls) > 0

    # 次の書き込みがパラメータ
    param_call = mock_pi_instance.spi_write.call_args_list[
        madctl_calls[0] + 1
    ]
    param_value = param_call[0][1][0]
    assert param_value & 0x08  # BGR bit should be set

    # bgr=False の場合、Bit 3 が 0 になるはず
    disp2 = create_st7789v_instance(bgr=False)
    mock_pi_instance.spi_write.reset_mock()
    disp2.set_rotation(0)
    madctl_calls2 = [
        i
        for i, call in enumerate(mock_pi_instance.spi_write.call_args_list)
        if call[0][1] == [0x36]
    ]
    param_call2 = mock_pi_instance.spi_write.call_args_list[
        madctl_calls2[0] + 1
    ]
    param_value2 = param_call2[0][1][0]
    assert not (param_value2 & 0x08)  # BGR bit should NOT be set


def test_invon_off_commands(mock_pi_instance):
    """invert 設定に応じて INVON (0x21) / INVOFF (0x20) が呼ばれるかテスト."""
    # invert=True -> INVON (0x21)
    disp = create_st7789v_instance(invert=True)
    mock_pi_instance.spi_write.reset_mock()
    disp.init_display()
    calls = [c[0][1] for c in mock_pi_instance.spi_write.call_args_list]
    assert [0x21] in calls
    assert [0x20] not in calls

    # invert=False -> INVOFF (0x20)
    disp2 = create_st7789v_instance(invert=False)
    mock_pi_instance.spi_write.reset_mock()
    disp2.init_display()
    calls2 = [c[0][1] for c in mock_pi_instance.spi_write.call_args_list]
    assert [0x20] in calls2
    assert [0x21] not in calls2


def test_set_rotation(mock_pi_instance):
    disp = create_st7789v_instance()
    disp.set_rotation(ST7789V.EAST)
    assert disp.rotation == 90
    assert disp.size == DispSize(320, 240)


def test_close(mock_pi_instance):
    disp = create_st7789v_instance()
    mock_pi_instance.reset_mock()
    disp.close()
    # DISPOFF(0x28), SLPIN(0x10) が呼ばれることを確認
    calls = [c[0][1] for c in mock_pi_instance.spi_write.call_args_list]
    assert [0x28] in calls
    assert [0x10] in calls
