#!/usr/bin/env python3
#
# (c) 2025 Yoichi Tanibayashi
#
"""
Rotation Check Sample for pi0disp.
Displays shapes and text to verify rotation and coordinates.
"""
import time
from PIL import Image, ImageDraw, ImageFont
from pi0disp.disp.st7789v import ST7789V

def draw_test_pattern(width, height, rotation):
    """Create a test image for the given size and rotation."""
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)
    
    # 1. Outer Border
    draw.rectangle([0, 0, width - 1, height - 1], outline="white", width=2)
    
    # 2. Diagonal Lines
    draw.line([0, 0, width - 1, height - 1], fill="gray", width=1)
    draw.line([width - 1, 0, 0, height - 1], fill="gray", width=1)
    
    # 3. Central Circle
    center_x, center_y = width // 2, height // 2
    r = min(width, height) // 4
    draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], 
                 outline="yellow", width=3)
    
    # 4. Directional Arrow (pointing to Top-Right of the current view)
    draw.line([center_x, center_y, width - 20, 20], fill="red", width=5)
    draw.text((width - 60, 25), "TOP-RIGHT", fill="red")

    # 5. Text Information
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except Exception:
        font = None

    info_text = [
        f"Rotation: {rotation} deg",
        f"Size: {width} x {height}",
        "Center: (W/2, H/2)"
    ]
    
    y_offset = center_y + r + 10
    for i, line in enumerate(info_text):
        draw.text((center_x - 60, y_offset + i * 20), line, fill="cyan", font=font)

    # 6. Corner markers
    draw.text((5, 5), "0,0", fill="white")
    draw.text((width - 50, height - 15), f"{width-1},{height-1}", fill="white")

    return image

def main():
    print("Starting Rotation Check...")
    
    # Initialize display (default rotation from config)
    disp = ST7789V(debug=True)
    
    try:
        rotations = [0, 90, 180, 270]
        
        for rot in rotations:
            print(f"Testing Rotation: {rot} degrees...")
            
            # Set rotation
            disp.set_rotation(rot)
            
            # Get current size (updated by set_rotation via DispBase)
            w = disp.size.width
            h = disp.size.height
            
            # Create and show image
            image = draw_test_pattern(w, h, rot)
            disp.display(image)
            
            print(f"  Display Size: {w}x{h}")
            time.sleep(5) # Wait for 5 seconds per rotation
            
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        disp.close()
        print("Done.")

if __name__ == "__main__":
    main()
