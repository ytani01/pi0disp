# Testing Commands

The project uses `pytest` for testing.

To run all tests:
```sh
uv run pytest
```
or
```sh
pytest
```
(if `pytest` is in the environment's PATH)

To run tests with verbose output:
```sh
uv run pytest -v
```
or
```sh
pytest -v
```

To run a specific test file:
```sh
uv run pytest tests/test_00_conftest_01_basic.py
```
or
```sh
pytest tests/test_00_conftest_01_basic.py
```