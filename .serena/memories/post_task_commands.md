# Post-Task Commands (Linting, Formatting, Testing)

After making changes, the following commands should be run to ensure code quality, style, and correctness:

## Linting and Formatting

The project uses `ruff`, `flake8`, `isort`, and `pylint`. `ruff` can handle most linting and formatting tasks efficiently.

- **Run Ruff (lint and format checks):**
  ```sh
  uv run ruff check .
  uv run ruff format .
  ```
- **Run Ruff (fix issues where possible):**
  ```sh
  uv run ruff check . --fix
  uv run ruff format . --check # To verify formatting
  ```
- **Run Flake8:**
  ```sh
  uv run flake8 .
  ```
- **Run isort (check only):**
  ```sh
  uv run isort . --check-only
  ```
- **Run isort (fix imports):**
  ```sh
  uv run isort .
  ```
- **Run Pylint:**
  ```sh
  uv run pylint src/pi0disp
  ```

## Type Checking
- **Run MyPy:**
  ```sh
  uv run mypy src/pi0disp
  ```

## Testing
- **Run all Pytest tests:**
  ```sh
  uv run pytest
  ```