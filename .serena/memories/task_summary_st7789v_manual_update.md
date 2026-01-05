# Task Summary: Update ST7789V manual and fix display bug

## Accomplishments
1.  **Fixed a bug in `src/pi0disp/disp/st7789v.py`**:
    *   The `display(image)` method was calling `super().display(image)` for resizing, but since `Image.resize` is not in-place, the result was lost. Updated the method to capture the resized image.
2.  **Updated `docs/ST7789V-manual.md`**:
    *   Aligned `speed_hz` default value (8MHz) with the source code.
    *   Updated the API reference for the constructor.
    *   Ensured consistency with `bgr` vs `rgb` configuration.
3.  **Verification**:
    *   Ran `uv run ruff check .` and all checks passed.
    *   Ran `uv run pytest tests/test_03_st7789v.py` and all tests passed.

## Status
The task is complete. No further action is required for this specific request.
