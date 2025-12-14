# Codebase Structure

The project has the following key directories and their purposes:

- `src/pi0disp/`: This is the main source directory for the `pi0disp` library and CLI tool.
    - `__main__.py`: Contains the entry point for the `pi0disp` CLI tool.
    - `disp/`: Likely contains the core display driver implementation (e.g., `st7789v.py`).
    - `commands/`: Contains the implementations for the various CLI subcommands (e.g., `ballanime.py`, `rgb.py`, `off.py`).
    - `utils/`: Contains utility functions and modules, such as:
        - `performance_core.py`: Implements general optimization features like memory pools, region optimization, and performance monitoring.
        - `sprite.py`: Likely for sprite-related functionalities.
        - `mylogger.py`: Custom logging utility.
        - `click_utils.py`: Utilities related to the `click` CLI framework.
        - `utils.py`: General utility functions.
- `samples/`: Contains example Python scripts demonstrating how to use the `pi0disp` library and its features.
- `tests/`: Contains unit and integration tests for the project.
    - `_pigpio_mock.py`: Suggests a mock for the `pigpio` library for testing purposes.
    - `_testbase_cli.py`: Base classes or utilities for CLI testing.
- `docs/`: Contains documentation files, images, and possibly resources.
- `archives/`: Placeholder for archived files.

This structure indicates a well-organized project with clear separation of concerns between core logic, CLI commands, utilities, examples, and tests.