# tests/conftest.py

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ._testbase_cli import (
    KEY_DOWN,
    KEY_ENTER,
    KEY_EOF,
    KEY_LEFT,
    KEY_RIGHT,
    KEY_UP,
    CLITestBase,
    InteractiveSession,
    cli_runner,
)

print(
    CLITestBase,
    InteractiveSession,
    cli_runner,
    KEY_UP,
    KEY_DOWN,
    KEY_ENTER,
    KEY_EOF,
    KEY_LEFT,
    KEY_RIGHT,
)


def pytest_addoption(parser):
    parser.addoption(
        "--duration",
        action="store",
        default=10,  # デフォルトは10秒
        type=int,
        help="パフォーマンス測定の実行時間 (秒)",
    )


@pytest.fixture(scope="session")
def duration(request):
    return request.config.getoption("--duration")


@pytest.fixture
def mock_pi_constructor():
    """Mock pigpio.pi constructor."""
    with patch("pigpio.pi") as mock:
        yield mock


@pytest.fixture
def mock_logger():
    """Mock get_logger."""
    with patch("pi0disp.disp.disp_base.get_logger") as mock:
        yield mock


@pytest.fixture
def mock_pi_instance(mock_pi_constructor):
    """Mock pigpio.pi instance."""
    mock_instance = MagicMock()
    mock_instance.connected = True
    # Default behavior for spi_open (used in DispSpi)
    mock_instance.spi_open.return_value = 0
    mock_pi_constructor.return_value = mock_instance
    return mock_instance


@pytest.fixture
def cli_mock_env():
    """
    共通CLIモック環境フィクスチャ。

    CliRunnerのインスタンス、pigpio.piのモック、Dynaconfのモックを提供する。
    """
    with (
        patch("pigpio.pi") as mock_pi_constructor,
        patch("pi0disp.disp.disp_conf.Dynaconf") as mock_dynaconf_class,
    ):
        mock_pi_instance = MagicMock()
        mock_pi_instance.connected = True
        mock_pi_instance.get_PWM_dutycycle.return_value = 0
        mock_pi_constructor.return_value = mock_pi_instance

        mock_dynaconf_instance = MagicMock()
        mock_dynaconf_instance.get.return_value = (
            MagicMock()
        )  # .spi.blなどの属性アクセスを可能にする
        mock_dynaconf_class.return_value = mock_dynaconf_instance

        runner = CliRunner()

        yield runner, mock_pi_instance, mock_dynaconf_instance
