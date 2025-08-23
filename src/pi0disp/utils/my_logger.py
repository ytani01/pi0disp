#
# (c) 2025 Yoichi Tanibayashi
#
"""
Custom logger configuration for the pi0disp package.

This module provides a simple function to get a configured logger instance
with a specific format and level.

Usage:
  log = get_logger(__name__, debug=True)
  log.debug("This is a debug message.")
"""
import inspect
from logging import (
    DEBUG, INFO, Formatter, Logger, StreamHandler, getLogger
)


def get_logger(name: str, debug: bool = False) -> Logger:
    """
    Configures and returns a logger instance.

    Args:
        name (str): The name for the logger, typically __name__.
        debug (bool): If True, the logger's level is set to DEBUG,
                      otherwise it defaults to INFO.

    Returns:
        Logger: The configured logger instance.
    """
    # Use the filename and the provided name to create a unique logger name
    try:
        filename = inspect.stack()[1].filename.split("/")[-1]
        logger_name = f"{filename}.{name}"
    except IndexError:
        logger_name = name

    logger = getLogger(logger_name)
    logger.setLevel(DEBUG if debug else INFO)

    # Prevent messages from being passed to the root logger
    logger.propagate = False

    # Avoid adding duplicate handlers if the logger is already configured
    if logger.hasHandlers():
        logger.handlers.clear()

    # Configure handler and formatter
    formatter = Formatter(
        "%(asctime)s %(levelname)s %(name)s.%(funcName)s:%(lineno)d> %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(DEBUG)  # Handler level should be low to pass all messages

    logger.addHandler(console_handler)

    return logger
