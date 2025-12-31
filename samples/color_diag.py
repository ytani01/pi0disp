import time

from PIL import Image, ImageDraw

from pi0disp import ST7789V


def test_colors(invert, bgr):
    print(f"Testing: invert={invert}, bgr={bgr}")
    try:
        with ST7789V(rotation=ST7789V.EAST, invert=invert, bgr=bgr) as lcd:
            img = Image.new("RGB", lcd.size, "black")
            draw = ImageDraw.Draw(img)

            w, h = lcd.size
            # 6つの帯を描画
            colors = [
                ("Red", (255, 0, 0)),
                ("Green", (0, 255, 0)),
                ("Blue", (0, 0, 255)),
                ("Yellow", (255, 255, 0)),
                ("White", (255, 255, 255)),
                ("Black", (0, 0, 0)),
            ]

            band_h = h // len(colors)
            for i, (name, rgb) in enumerate(colors):
                draw.rectangle((0, i * band_h, w, (i + 1) * band_h), fill=rgb)
                draw.text(
                    (10, i * band_h + 5),
                    f"{name} (inv={invert}, bgr={bgr})",
                    fill="white" if name != "White" else "black",
                )

            lcd.display(img)
            time.sleep(3)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_colors(invert=True, bgr=True)  # Default
    test_colors(invert=True, bgr=False)
    test_colors(invert=False, bgr=False)
    test_colors(invert=False, bgr=True)
