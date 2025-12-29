# test_display.py
import os
import time

from PIL import Image

from pi0disp import ST7789V


def main():
    print("Starting display test...")
    try:
        with ST7789V() as lcd:
            image = Image.new("RGB", (lcd.size.width, lcd.size.height), "red")
            lcd.display(image)
            print(
                f"Displaying a red screen. PID: {os.getpid()}. The script will run for 60 seconds."
            )
            print(
                "To test the issue, find the process ID (PID) of this script with 'ps aux | grep test_display.py' and kill it using 'kill -9 <PID>'."
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
