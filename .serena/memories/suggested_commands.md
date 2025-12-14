# Suggested Commands for Development

This document outlines essential commands for developing within the `pi0disp` project.

## Setup
- **Install `pigpio` daemon and library:**
  ```sh
  sudo apt update
  sudo apt install pigpio
  ```
- **Start `pigpio` daemon:**
  ```sh
  sudo systemctl start pigpiod
  ```
- **Clone the repository:**
  ```sh
  git clone <repository_url>
  cd pi0disp
  ```
- **Create and activate Python virtual environment (if not using `uv` directly):**
  ```sh
  python -m venv .venv
  source .venv/bin/activate
  ```
- **Install dependencies (including development dependencies):**
  ```sh
  pip install -e . --group dev
  ```
  (Note: `uv` is implicitly used for running commands and often for managing dependencies if installed and configured globally. The `pip install` command is still standard.)

## Running the Project

All project-specific commands should be run using `uv run`.

- **Run basic usage example:**
  ```sh
  uv run samples/basic_usage.py
  ```
- **Get help for the CLI tool:**
  ```sh
  uv run pi0disp --help
  ```
- **Run ball animation demo:**
  ```sh
  uv run pi0disp ballanime --fps 60 --num-balls 5
  ```
- **Turn off the display:**
  ```sh
  uv run pi0disp off
  ```

## Code Quality and Testing

- **Run all tests:**
  ```sh
  uv run pytest
  ```
- **Run ruff (lint and format checks):**
  ```sh
  uv run ruff check .
  ```
- **Run ruff (apply fixes and format):**
  ```sh
  uv run ruff check . --fix
  uv run ruff format .
  ```
- **Run mypy (type checking):**
  ```sh
  uv run mypy src/pi0disp
  ```
- **Run isort (sort imports):**
  ```sh
  uv run isort .
  ```
- **Run flake8 (additional linting):**
  ```sh
  uv run flake8 .
  ```
- **Run pylint (static analysis):**
  ```sh
  uv run pylint src/pi0disp
  ```

## Git Commands

Standard Git commands are used for version control.
- `git status`
- `git add .`
- `git commit -m "Your message"`
- `git pull`
- `git push` (if you have push access to the remote repository)

This concludes the initial onboarding process.