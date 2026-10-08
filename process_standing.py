import json
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

standing_img_path = r"assets\knight_standing_reference.jpg"
img = Image.open(standing_img_path).convert("RGB")

width_cells = 84
height_cells = 116

# Center knight tight from head to toe (img size: 768 x 1376)
knight_tight = img.crop((80, 50, 688, 1330))

def process_standing_knight(img_in, width, height):
    sharp = img_in.filter(ImageFilter.UnsharpMask(radius=2.2, percent=220, threshold=2))
    sharp_np = np.array(sharp, dtype=np.float32)
    norm = sharp_np / 255.0
    lifted = np.power(norm, 0.82) * 255.0
    img_lifted = Image.fromarray(np.clip(lifted, 0, 255).astype(np.uint8))
    
    color_enh = ImageEnhance.Color(img_lifted)
    img_vibrant = color_enh.enhance(1.4)
    
    resized = img_vibrant.resize((width, height), Image.Resampling.LANCZOS)
    gray = resized.convert("L")
    gray_np = np.array(gray, dtype=np.float32)
    
    dy, dx = np.gradient(gray_np)
    magnitude = np.sqrt(dx**2 + dy**2)
    angle = np.arctan2(dy, dx) * 180 / np.pi
    
    artistic_ramp = " .`:-=+*#%@"
    
    rows = []
    
    for y in range(height):
        chars = []
        fg_colors = []
        bg_colors = []
        anatomy_row = []
        
        for x in range(width):
            r, g, b = resized.getpixel((x, y))[:3]
            lum = gray.getpixel((x, y))
            mag = magnitude[y, x]
            ang = angle[y, x]
            
            y_norm = y / float(height)
            x_norm = x / float(width)
            
            # Region detection based on coordinates and color
            is_red_cape = (r > 45 and r > g * 1.32 and r > b * 1.32)
            
            zone = "background"
            if 0.04 <= y_norm <= 0.17 and 0.38 <= x_norm <= 0.62:
                zone = "head_helm"
            elif 0.16 <= y_norm <= 0.34 and (x_norm < 0.38 or x_norm > 0.62) and not is_red_cape:
                zone = "pauldrons"
            elif 0.17 <= y_norm <= 0.40 and 0.35 <= x_norm <= 0.65:
                zone = "torso_cuirass"
            elif is_red_cape:
                zone = "cape_mantle"
            elif 0.34 <= y_norm <= 0.50 and 0.30 <= x_norm <= 0.70:
                if 0.46 <= x_norm <= 0.54:
                    zone = "weapon_sword"
                else:
                    zone = "arms_gauntlets"
            elif 0.40 <= y_norm <= 0.56 and 0.34 <= x_norm <= 0.66:
                if 0.47 <= x_norm <= 0.53:
                    zone = "weapon_sword"
                else:
                    zone = "waist_fauld"
            elif 0.50 <= y_norm <= 0.88 and 0.47 <= x_norm <= 0.53:
                zone = "weapon_sword"
            elif 0.54 <= y_norm <= 0.88 and 0.26 <= x_norm <= 0.74:
                zone = "legs_greaves"
            elif y_norm > 0.87 and 0.24 <= x_norm <= 0.76:
                zone = "feet_sabatons"
            elif y_norm > 0.93:
                zone = "ground_flagstone"
                
            # Glyph selection
            if zone == "weapon_sword" and 0.48 <= y_norm <= 0.88:
                if x_norm < 0.495:
                    ch = "/" if mag > 15 else "|"
                elif x_norm > 0.505:
                    ch = "\\" if mag > 15 else "|"
                else:
                    ch = "|"
            elif mag > 24:
                if -22.5 <= ang <= 22.5 or ang >= 157.5 or ang <= -157.5:
                    ch = "|"
                elif 22.5 < ang < 67.5 or -157.5 < ang < -112.5:
                    ch = "/"
                elif 67.5 <= ang <= 112.5 or -112.5 <= ang <= -67.5:
                    ch = "-"
                else:
                    ch = "\\"
            elif zone in ("torso_cuirass", "pauldrons", "legs_greaves") and mag > 14:
                ch = "=" if 45 <= abs(ang) <= 135 else "|"
            elif is_red_cape:
                if lum > 115:
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
                fg_r = min(255, int(r * 1.35 + 35))
                fg_g = max(0, int(g * 0.72))
                fg_b = max(0, int(b * 0.72))
                bg_r = max(0, int(r * 0.32))
                bg_g = max(0, int(g * 0.16))
                bg_b = max(0, int(b * 0.16))
            elif zone == "weapon_sword":
                fg_r = min(255, int(r * 1.3 + 40))
                fg_g = min(255, int(g * 1.32 + 45))
                fg_b = min(255, int(b * 1.38 + 55))
                bg_r = max(0, int(r * 0.25))
                bg_g = max(0, int(g * 0.28))
                bg_b = max(0, int(b * 0.32))
            elif zone in ("torso_cuirass", "head_helm", "pauldrons", "arms_gauntlets", "legs_greaves", "feet_sabatons"):
                fg_r = min(255, int(r * 1.25 + 28))
                fg_g = min(255, int(g * 1.28 + 32))
                fg_b = min(255, int(b * 1.32 + 38))
                bg_r = max(0, int(r * 0.22))
                bg_g = max(0, int(g * 0.24))
                bg_b = max(0, int(b * 0.28))
            else:
                fg_r = min(255, int(r * 1.1 + 12))
                fg_g = min(255, int(g * 1.1 + 12))
                fg_b = min(255, int(b * 1.1 + 12))
                bg_r = max(0, int(r * 0.20))
                bg_g = max(0, int(g * 0.20))
                bg_b = max(0, int(b * 0.20))
                
            chars.append(ch)
            fg_colors.append([fg_r, fg_g, fg_b])
            bg_colors.append([bg_r, bg_g, bg_b])
            anatomy_row.append(zone)
            
        rows.append({
            "text": "".join(chars),
            "fg": fg_colors,
            "bg": bg_colors,
            "anatomy": anatomy_row
        })
    return rows

standing_rows = process_standing_knight(knight_tight, width_cells, height_cells)

# Load existing high density json to update it
high_density_path = r"assets\ascii\characters\knight_high_density.json"
with open(high_density_path, "r", encoding="utf-8") as f:
    hd_data = json.load(f)

# Insert standing sentinel as the primary character
hd_data["standing_sentinel"] = {
    "id": "knight_standing_sentinel",
    "name": "The Standing Sentinel (Hero Pose)",
    "width": width_cells,
    "height": height_cells,
    "rows": standing_rows,
    "anatomy_zones": [
        "head_helm",
        "pauldrons",
        "torso_cuirass",
        "cape_mantle",
        "arms_gauntlets",
        "weapon_sword",
        "waist_fauld",
        "legs_greaves",
        "feet_sabatons"
    ]
}

with open(high_density_path, "w", encoding="utf-8") as f:
    json.dump(hd_data, f)

# Also update knight_data.js
with open(r"assets\ascii\characters\knight_data.js", "w", encoding="utf-8") as f:
    f.write(f"window.KNIGHT_DATA = {json.dumps(hd_data)};\n")

print("Updated knight_high_density.json and knight_data.js with standing_sentinel!")
