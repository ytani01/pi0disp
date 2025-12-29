# test_display.py
import argparse
import os
import time

from PIL import Image

from pi0disp import ST7789V


def main():
    parser = argparse.ArgumentParser(
        description="ST7789V Display Test Script"
    )
    parser.add_argument(
        "--no-invert",
        action="store_false",
        dest="invert",
        help="Do not invert display colors (default: invert)",
    )
    parser.add_argument(
        "--no-bgr",
        action="store_false",
        dest="bgr",
        help="Use RGB color order instead of BGR (default: BGR)",
    )
    args = parser.parse_args()

    print("Starting display test...")
    try:
        with ST7789V(invert=args.invert, bgr=args.bgr) as lcd:
            image = Image.new("RGB", (lcd.size.width, lcd.size.height), "red")
            lcd.display(image)
            print(
                f"Displaying a red screen. PID: {os.getpid()}. "
                f"Invert: {args.invert}, BGR: {args.bgr}. "
                f"The script will run for 60 seconds."
            )
            print(
                "To test the issue, find the process ID (PID) of this script with "
                "'ps aux | grep test_display.py' and kill it using 'kill -9 <PID>'."
            )
            time.sleep(60)

            image = Image.new(
                "RGB", (lcd.size.width, lcd.size.height), "green"
            )
            lcd.display(image)
            time.sleep(5)

    except KeyboardInterrupt:
        print("Script interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Script finished.")


if __name__ == "__main__":
    main()
