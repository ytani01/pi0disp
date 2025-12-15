# tests/conftest.py

from unittest.mock import MagicMock, patch

import pytest

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
