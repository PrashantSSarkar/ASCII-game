import json
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

combat_img_path = r"assets\knight_combat_reference.jpg"
img = Image.open(combat_img_path).convert("RGB")

width_cells = 84
height_cells = 116

# Crop tight to frame the knight from raised sword tip down to sabatons
# Original size: 768 x 1376
# Knight spans x ~ 40 to 740, y ~ 100 to 1330
knight_tight = img.crop((40, 90, 740, 1340))

def process_combat_knight(img_in, width, height):
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
            
            is_red_cape = (r > 45 and r > g * 1.30 and r > b * 1.30)
            
            zone = "background"
            # Sword diagonal line detection: from hilt (x~0.30, y~0.48) to tip (x~0.88, y~0.12)
            # Line equation approx: y_norm ~= -0.6 * x_norm + 0.65
            expected_sword_y = -0.62 * x_norm + 0.66
            is_near_sword_line = abs(y_norm - expected_sword_y) < 0.045 and 0.18 <= x_norm <= 0.88 and 0.10 <= y_norm <= 0.54
            is_bright_steel = (lum > 110 and abs(r - g) < 25 and abs(g - b) < 25)
            
            if is_near_sword_line and is_bright_steel:
                zone = "weapon_sword"
            elif 0.10 <= y_norm <= 0.24 and 0.40 <= x_norm <= 0.58 and not is_red_cape:
                zone = "head_helm"
            elif 0.20 <= y_norm <= 0.38 and (x_norm < 0.42 or x_norm > 0.58) and not is_red_cape:
                zone = "pauldrons"
            elif 0.22 <= y_norm <= 0.46 and 0.36 <= x_norm <= 0.62 and not is_red_cape and zone != "weapon_sword":
                zone = "torso_cuirass"
            elif is_red_cape:
                zone = "cape_mantle"
            elif 0.36 <= y_norm <= 0.52 and 0.18 <= x_norm <= 0.48 and zone != "weapon_sword":
                zone = "arms_gauntlets"
            elif 0.44 <= y_norm <= 0.60 and 0.28 <= x_norm <= 0.66 and zone != "weapon_sword":
                zone = "waist_fauld"
            elif 0.56 <= y_norm <= 0.90 and (0.10 <= x_norm <= 0.45 or 0.55 <= x_norm <= 0.88):
                zone = "legs_greaves"
            elif y_norm > 0.88 and (0.06 <= x_norm <= 0.42 or 0.60 <= x_norm <= 0.94):
                zone = "feet_sabatons"
            elif y_norm > 0.93:
                zone = "ground_flagstone"
                
            # Glyph selection
            if zone == "weapon_sword":
                # Diagonal blade cutting edge
                ch = "/" if mag > 12 else "\\"
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
                # Glinting honed blade
                fg_r = min(255, int(r * 1.35 + 50))
                fg_g = min(255, int(g * 1.38 + 55))
                fg_b = min(255, int(b * 1.45 + 65))
                bg_r = max(0, int(r * 0.28))
                bg_g = max(0, int(g * 0.30))
                bg_b = max(0, int(b * 0.35))
            elif zone in ("torso_cuirass", "head_helm", "pauldrons", "arms_gauntlets", "legs_greaves", "feet_sabatons", "waist_fauld"):
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

print("Generating combat stance micro-ASCII matrix (84x116)...")
combat_rows = process_combat_knight(knight_tight, width_cells, height_cells)

# Load and update high density json
hd_path = r"assets\ascii\characters\knight_high_density.json"
with open(hd_path, "r", encoding="utf-8") as f:
    hd_data = json.load(f)

hd_data["combat_stance"] = {
    "id": "knight_combat_stance",
    "name": "Combat Ready Stance (Attack Posture)",
    "width": width_cells,
    "height": height_cells,
    "rows": combat_rows,
    "stance_type": "active_guard_slashing",
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

with open(hd_path, "w", encoding="utf-8") as f:
    json.dump(hd_data, f)

# Also update knight_data.js
with open(r"assets\ascii\characters\knight_data.js", "w", encoding="utf-8") as f:
    f.write(f"window.KNIGHT_DATA = {json.dumps(hd_data)};\n")

print("Saved combat_stance into knight_high_density.json and knight_data.js!")
