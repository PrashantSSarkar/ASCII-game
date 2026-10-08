import json
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

img_path = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d\.user_uploaded\media_1791446766256.png"
full_img = Image.open(img_path).convert("RGB")

# Crop 1: The Focused Knight (x from 360 to 690, y from 0 to 360)
knight_crop = full_img.crop((360, 0, 690, 360))

def process_grid_v3(img, width, height):
    # 1. Unsharp mask for crisp steel bevels and blade line
    sharp = img.filter(ImageFilter.UnsharpMask(radius=2.0, percent=200, threshold=2))
    
    # 2. Lift shadows slightly so dark armor plates aren't crushed into pure black
    sharp_np = np.array(sharp, dtype=np.float32)
    # Gamma lift on dark tones
    norm = sharp_np / 255.0
    lifted = np.power(norm, 0.78) * 255.0
    img_lifted = Image.fromarray(np.clip(lifted, 0, 255).astype(np.uint8))
    
    # 3. Enhance color saturation for crimson cape
    color_enh = ImageEnhance.Color(img_lifted)
    img_vibrant = color_enh.enhance(1.4)
    
    # 4. Resize to target micro-grid
    img_resized = img_vibrant.resize((width, height), Image.Resampling.LANCZOS)
    gray = img_resized.convert("L")
    gray_np = np.array(gray, dtype=np.float32)
    
    # Sobel gradient calculation
    dy, dx = np.gradient(gray_np)
    magnitude = np.sqrt(dx**2 + dy**2)
    angle = np.arctan2(dy, dx) * 180 / np.pi
    
    artistic_ramp = " .`:-=+*#%@"
    
    rows = []
    for y in range(height):
        chars = []
        fg_colors = []
        bg_colors = []
        for x in range(width):
            r, g, b = img_resized.getpixel((x, y))[:3]
            lum = gray.getpixel((x, y))
            mag = magnitude[y, x]
            ang = angle[y, x]
            
            # Region classifications
            is_red_cape = (r > 50 and r > g * 1.3 and r > b * 1.3)
            is_steel_plate = (lum > 25 and abs(r - g) < 22 and abs(g - b) < 22 and not is_red_cape)
            
            # Glyph selection
            if mag > 24:
                # Strong edge -> crisp directional glyph
                if -22.5 <= ang <= 22.5 or ang >= 157.5 or ang <= -157.5:
                    ch = "|"
                elif 22.5 < ang < 67.5 or -157.5 < ang < -112.5:
                    ch = "/"
                elif 67.5 <= ang <= 112.5 or -112.5 <= ang <= -67.5:
                    ch = "-"
                else:
                    ch = "\\"
            elif is_steel_plate and mag > 14:
                ch = "=" if 45 <= abs(ang) <= 135 else "|"
            elif is_red_cape:
                if lum > 110:
                    ch = "~"
                elif lum > 65:
                    ch = "s"
                else:
                    ch = "%"
            else:
                idx = int((lum / 255.0) * (len(artistic_ramp) - 1))
                ch = artistic_ramp[idx]
            
            # Colors
            if is_red_cape:
                fg_r = min(255, int(r * 1.3 + 35))
                fg_g = max(0, int(g * 0.75))
                fg_b = max(0, int(b * 0.75))
                bg_r = max(0, int(r * 0.32))
                bg_g = max(0, int(g * 0.18))
                bg_b = max(0, int(b * 0.18))
            elif is_steel_plate:
                # Steel highlight & plate shading
                fg_r = min(255, int(r * 1.2 + 25))
                fg_g = min(255, int(g * 1.22 + 28))
                fg_b = min(255, int(b * 1.28 + 35))
                bg_r = max(0, int(r * 0.22))
                bg_g = max(0, int(g * 0.24))
                bg_b = max(0, int(b * 0.28))
            else:
                fg_r = min(255, int(r * 1.15 + 18))
                fg_g = min(255, int(g * 1.15 + 18))
                fg_b = min(255, int(b * 1.15 + 18))
                bg_r = max(0, int(r * 0.22))
                bg_g = max(0, int(g * 0.22))
                bg_b = max(0, int(b * 0.22))
                
            chars.append(ch)
            fg_colors.append([fg_r, fg_g, fg_b])
            bg_colors.append([bg_r, bg_g, bg_b])
            
        rows.append({
            "text": "".join(chars),
            "fg": fg_colors,
            "bg": bg_colors
        })
    return rows

print("Generating enhanced Knight Focus matrix v3 (96x80)...")
knight_matrix = process_grid_v3(knight_crop, 96, 80)

print("Generating enhanced Battlefield Scene matrix v3 (160x80)...")
scene_matrix = process_grid_v3(full_img, 160, 80)

data = {
    "metadata": {
        "title": "High-Density Micro-ASCII Knight Draft 2 (Enhanced v3)",
        "description": "Ultra-detailed micro-glyph character and scene matrix based on the Weary Sentinel reference artwork",
        "reference_dimensions": [720, 360],
    },
    "scene": {
        "id": "weary_knight_battlefield_scene",
        "width": 160,
        "height": 80,
        "rows": scene_matrix
    },
    "character_focus": {
        "id": "weary_knight_portrait",
        "width": 96,
        "height": 80,
        "rows": knight_matrix
    }
}

output_path = r"assets\ascii\characters\knight_high_density.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f)

js_content = f"window.KNIGHT_DATA = {json.dumps(data)};\n"
with open(r"assets\ascii\characters\knight_data.js", "w", encoding="utf-8") as f:
    f.write(js_content)

print("Saved enhanced v3 JSON and JS datasets successfully!")
