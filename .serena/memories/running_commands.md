# Running Commands

The project's main entry point is a CLI tool. Sample scripts are also provided.
The `uv run` command is used to execute these.

## CLI Tool
- **Help:**
  ```sh
  uv run pi0disp --help
  ```
- **Available Commands:**
    - `ballanime`: Balls animation
    - `image`: Displays an image with optional gamma correction.
    - `off`: Turns off the display (sleep mode, backlight off).
    - `rgb`: Displays RGB circles.
    - `sleep`: Puts the display into sleep mode.
    - `wake`: Wakes up the display from sleep mode.

- **Example Usage:**
    - **Performance Demo (ballanime):**
      ```sh
      uv run pi0disp ballanime
      ```
      - Options:
        - Target FPS (e.g., 60): `uv run pi0disp ballanime --fps 60`
        - Number of balls (e.g., 5): `uv run pi0disp ballanime --num-balls 5`
        - SPI communication speed (e.g., 40MHz): `uv run pi0disp ballanime --speed 40000000`
    - **Turn off display:**
      ```sh
      uv run pi0disp off
      ```

## Library Usage Examples
- **Basic Usage Script:**
  ```sh
  uv run samples/basic_usage.py
  ```