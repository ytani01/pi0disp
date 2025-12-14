# Tech Stack

## Hardware
- Raspberry Pi (especially Raspberry Pi Zero 2W)
- ST7789V-based SPI display

## Software
- **Programming Language:** Python 3.11+
- **Core Libraries:**
    - `pigpio`: For efficient SPI communication.
    - `numpy`: For numerical operations and performance optimization.
    - `Pillow` (PIL): For image manipulation and drawing.
    - `cairosvg`: For SVG rendering.
    - `click`: For building command-line interfaces.

## Build and Dependency Management
- `hatchling`: Build backend.
- `hatch-vcs`: For version management using VCS.

## Development Tools
- `uv`: For running commands and dependency management (implied by `uv run` usage in README).
- `flake8`: Linter.
- `isort`: Import sorter.
- `mypy`: Static type checker.
- `pylint`: Static code analyzer.
- `pytest`: Testing framework.
- `ruff`: Fast linter and formatter.

## Operating System
- Linux (specifically Raspberry Pi OS for the target hardware)