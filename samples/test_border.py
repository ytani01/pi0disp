import time
from PIL import Image, ImageDraw
from pi0disp import ST7789V

def main():
    try:
        with ST7789V(debug=False) as lcd:
            print(f"Display size: {lcd.size.width}x{lcd.size.height}")
            print(f"Rotation: {lcd.rotation}")
            
            # Create a test image with a white border
            img = Image.new("RGB", lcd.size, "black")
            draw = ImageDraw.Draw(img)
            
            # White border (1px)
            draw.rectangle([0, 0, lcd.size.width-1, lcd.size.height-1], outline="white")
            
            # Red crosshair
            draw.line([0, lcd.size.height//2, lcd.size.width-1, lcd.size.height//2], fill="red")
            draw.line([lcd.size.width//2, 0, lcd.size.width//2, lcd.size.height-1], fill="green")
            
            # Corner indicators
            # Top-Left: Red square
            draw.rectangle([0, 0, 10, 10], fill="red")
            # Top-Right: Green square
            draw.rectangle([lcd.size.width-11, 0, lcd.size.width-1, 10], fill="green")
            # Bottom-Left: Blue square
            draw.rectangle([0, lcd.size.height-11, 10, lcd.size.height-1], fill="blue")
            # Bottom-Right: White square
            draw.rectangle([lcd.size.width-11, lcd.size.height-11, lcd.size.width-1, lcd.size.height-1], fill="white")
            
            print("Displaying border test image for 10 seconds...")
            lcd.display(img)
            time.sleep(10)
            
            # Rotation test
            for rot in [0, 90, 180, 270]:
                print(f"Testing rotation {rot}...")
                lcd.set_rotation(rot)
                # Re-create image for new size
                img = Image.new("RGB", lcd.size, "black")
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, lcd.size.width-1, lcd.size.height-1], outline="white")
                draw.text((10, 10), f"Rot: {rot}", fill="yellow")
                lcd.display(img)
                time.sleep(3)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
