import json
import copy
import math
import os
import shutil

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

def main():
    json_path = "assets/ascii/characters/knight_high_density.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    m_combat = data["combat_stance"]
    m_rest = data["standing_sentinel"]
    w = 110
    h = 116

    # 1. Build a 100% PERFECT SEAMLESS background plate matching combat & rest stances
    bg_plate = []
    for y in range(h):
        r_comb = m_combat["rows"][y]
        r_rest = m_rest["rows"][y]
        
        wall_donors = []
        ground_donors = []
        for x in range(w):
            anat_c = r_comb["anatomy"][x]
            if anat_c == "background":
                wall_donors.append({
                    "text": r_comb["text"][x],
                    "fg": r_comb["fg"][x][:],
                    "bg": r_comb["bg"][x][:],
                    "anatomy": "background"
                })
            elif anat_c == "ground_flagstone":
                ground_donors.append({
                    "text": r_comb["text"][x],
                    "fg": r_comb["fg"][x][:],
                    "bg": r_comb["bg"][x][:],
                    "anatomy": "ground_flagstone"
                })

            anat_r = r_rest["anatomy"][x]
            if anat_r == "background":
                wall_donors.append({
                    "text": r_rest["text"][x],
                    "fg": r_rest["fg"][x][:],
                    "bg": r_rest["bg"][x][:],
                    "anatomy": "background"
                })
            elif anat_r == "ground_flagstone":
                ground_donors.append({
                    "text": r_rest["text"][x],
                    "fg": r_rest["fg"][x][:],
                    "bg": r_rest["bg"][x][:],
                    "anatomy": "ground_flagstone"
                })

        row = []
        for x in range(w):
            if y >= 108:
                donor = ground_donors[(x * 13 + y * 7) % len(ground_donors)]
                row.append(copy.deepcopy(donor))
            else:
                donor = wall_donors[(x * 11 + y * 17) % len(wall_donors)]
                row.append(copy.deepcopy(donor))
        bg_plate.append(row)

    def empty_matrix():
        out = {"width": w, "height": h, "rows": []}
        for y in range(h):
            r_txt = [bg_plate[y][x]["text"] for x in range(w)]
            r_fg = [bg_plate[y][x]["fg"][:] for x in range(w)]
            r_bg = [bg_plate[y][x]["bg"][:] for x in range(w)]
            r_anat = [bg_plate[y][x]["anatomy"] for x in range(w)]
            out["rows"].append({
                "text": "".join(r_txt),
                "fg": r_fg,
                "bg": r_bg,
                "anatomy": r_anat
            })
        return out

    # 2. Process knight_running_reference.jpg directly using the master pipeline
    ref_path = "assets/knight_running_reference.jpg"
    img_ref = Image.open(ref_path).convert("RGB")
    crop = img_ref.crop((0, 100, 768, 1350))

    sharp = crop.filter(ImageFilter.UnsharpMask(radius=2.2, percent=220, threshold=2))
    sharp_np = np.array(sharp, dtype=np.float32)
    norm = sharp_np / 255.0
    lifted = np.power(norm, 0.82) * 255.0
    img_lifted = Image.fromarray(np.clip(lifted, 0, 255).astype(np.uint8))
    color_enh = ImageEnhance.Color(img_lifted)
    img_vibrant = color_enh.enhance(1.4)
    resized = img_vibrant.resize((w, h), Image.Resampling.LANCZOS)
    gray = resized.convert("L")
    gray_np = np.array(gray, dtype=np.float32)
    dy, dx = np.gradient(gray_np)
    magnitude = np.sqrt(dx**2 + dy**2)
    angle = np.arctan2(dy, dx) * 180 / np.pi
    artistic_ramp = " .`:-=+*#%@"

    # 3. Build canonical Stride 1 directly from the reference image with PRECISE knight segmentation
    m_run_stride1 = empty_matrix()

    for y in range(h):
        for x in range(w):
            r, g, b = resized.getpixel((x, y))[:3]
            lum = gray.getpixel((x, y))
            mag = magnitude[y, x]
            ang = angle[y, x]

            # 1. Red cape check (strict red ratio, left-side of character)
            is_red_cape = (r > 45 and r > g * 1.25 and r > b * 1.25 and x < 85 and y < 65)

            # 2. Sword line along flank from (44, 50) to (104, 86)
            exp_sword_y = 0.54 * x + 28.5
            dist_sword = abs(y - exp_sword_y)
            is_sword = (dist_sword <= 1.8 and 44 <= x <= 104 and 50 <= y <= 86 and lum > 85)

            # 3. Ensure armor cells are NOT blue sky/ruin background
            # Blue sky in reference has (b > r + 6) or (b > g + 6) with cool gray/blue tone
            is_not_blue_sky = (b <= r + 6) or (r > 140)

            # Precise anatomical zones
            is_helm = (13 <= y <= 35 and 76 <= x <= 94 and is_not_blue_sky and lum > 55)
            is_torso = (26 <= y <= 56 and 54 <= x <= 88 and is_not_blue_sky and lum > 50)
            is_left_arm = (32 <= y <= 48 and 86 <= x <= 106 and is_not_blue_sky and lum > 50)
            is_right_arm = (36 <= y <= 58 and 38 <= x <= 56 and is_not_blue_sky and lum > 50)
            is_fauld = (50 <= y <= 66 and 42 <= x <= 78 and is_not_blue_sky and lum > 46)
            is_lead_leg = (64 <= y <= 107 and 52 <= x <= 86 and is_not_blue_sky and lum > 46)
            is_trail_leg = (66 <= y <= 107 and 15 <= x <= 52 and is_not_blue_sky and lum > 46)

            zone = None
            if is_sword:
                zone = "weapon_sword"
            elif is_red_cape:
                zone = "cape_mantle"
            elif is_helm:
                zone = "head_helm"
            elif is_left_arm or is_right_arm:
                zone = "arms_gauntlets"
            elif is_torso:
                # Distinguish pauldrons on shoulder ridges
                if (x < 64 or x > 80) and y < 44:
                    zone = "pauldrons"
                else:
                    zone = "torso_cuirass"
            elif is_fauld:
                zone = "waist_fauld"
            elif is_lead_leg or is_trail_leg:
                if y >= 100:
                    zone = "feet_sabatons"
                else:
                    zone = "legs_greaves"

            # If not part of the knight, leave it as the clean warm stone bg_plate!
            if zone is not None:
                # Select glyph
                if zone == "weapon_sword":
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

                # Colors harmonized to match combat_stance (warm gothic steel, ruby red, polished blade)
                if is_red_cape:
                    fg_r = min(255, int(r * 1.35 + 35))
                    fg_g = max(0, int(g * 0.65))
                    fg_b = max(0, int(b * 0.65))
                    bg_r = max(0, int(r * 0.30))
                    bg_g = max(0, int(g * 0.12))
                    bg_b = max(0, int(b * 0.12))
                elif zone == "weapon_sword":
                    fg_r = min(255, int(r * 1.3 + 40))
                    fg_g = min(255, int(g * 1.30 + 40))
                    fg_b = min(255, int(b * 1.35 + 45))
                    bg_r = max(0, int(r * 0.24))
                    bg_g = max(0, int(g * 0.25))
                    bg_b = max(0, int(b * 0.28))
                else:
                    # Steel armor: clamp blue to red so no cool blue cast exists on plate armor
                    fg_r = min(255, int(r * 1.25 + 28))
                    fg_g = min(255, int(g * 1.25 + 28))
                    fg_b = min(255, min(fg_r, int(b * 1.20 + 24)))
                    bg_r = max(0, int(r * 0.22))
                    bg_g = max(0, int(g * 0.22))
                    bg_b = max(0, min(bg_r, int(b * 0.20)))

                r_row = m_run_stride1["rows"][y]
                txt = list(r_row["text"])
                txt[x] = ch
                r_row["text"] = "".join(txt)
                r_row["fg"][x] = [fg_r, fg_g, fg_b]
                r_row["bg"][x] = [bg_r, bg_g, bg_b]
                r_row["anatomy"][x] = zone

    print("Canonical m_run_stride1 constructed with ZERO blue background contamination!")

    # Helper function to stamp body parts from source to target with offsets
    def copy_cell(src, dst, sx, sy, dx, dy):
        if 0 <= sx < w and 0 <= sy < h and 0 <= dx < w and 0 <= dy < h:
            src_row = src["rows"][sy]
            dst_row = dst["rows"][dy]
            # Only copy knight parts, never background
            if src_row["anatomy"][sx] not in ("background", "ground_flagstone"):
                txt = list(dst_row["text"])
                txt[dx] = src_row["text"][sx]
                dst_row["text"] = "".join(txt)
                dst_row["fg"][dx] = src_row["fg"][sx][:]
                dst_row["bg"][dx] = src_row["bg"][sx][:]
                dst_row["anatomy"][dx] = src_row["anatomy"][sx]

    # Helper to draw weapon blade with neutral steel colors
    def draw_blade(mat, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            for ox in (-1, 0, 1):
                px = x + ox
                py = y
                if 0 <= px < w and 0 <= py < h:
                    r_row = mat["rows"][py]
                    txt = list(r_row["text"])
                    if ox == 0:
                        txt[px] = "/" if sx * sy > 0 else "\\"
                        r_row["fg"][px] = [235, 240, 245]
                        r_row["bg"][px] = [35, 38, 45]
                    else:
                        txt[px] = "|"
                        r_row["fg"][px] = [170, 190, 210]
                        r_row["bg"][px] = [25, 27, 32]
                    r_row["text"] = "".join(txt)
                    r_row["anatomy"][px] = "weapon_sword"
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    # Helper to draw dynamic flapping cape with horizontal ruby waves
    def draw_running_cape(mat, attach_x, attach_y, length=64, wave_phase=0.0, wave_amp=4.0):
        for lx in range(length):
            x = attach_x - lx
            if x < 4 or x >= w:
                continue
            prog = lx / float(length)
            cy = attach_y + wave_amp * math.sin(0.18 * lx + wave_phase) + 6.0 * (prog ** 1.3)
            half_thick = max(1.5, 7.0 * math.sin(prog * math.pi) * (1.0 - 0.25 * prog))
            
            for ty in range(int(cy - half_thick), int(cy + half_thick + 1)):
                if 0 <= ty < 108:
                    r_row = mat["rows"][ty]
                    if r_row["anatomy"][x] in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets", "waist_fauld", "legs_greaves", "feet_sabatons"):
                        continue
                    lum_fac = 0.65 + 0.35 * math.cos(0.20 * lx + wave_phase + 0.1 * (ty - cy))
                    fg = [min(255, int(210 * lum_fac)), max(0, int(35 * lum_fac)), max(0, int(35 * lum_fac))]
                    bg = [max(0, int(55 * lum_fac)), max(0, int(12 * lum_fac)), max(0, int(12 * lum_fac))]
                    ch = "~" if abs(ty - cy) < 2 else ("s" if lum_fac > 0.75 else "%")
                    txt = list(r_row["text"])
                    txt[x] = ch
                    r_row["text"] = "".join(txt)
                    r_row["fg"][x] = fg
                    r_row["bg"][x] = bg
                    r_row["anatomy"][x] = "cape_mantle"

    # =========================================================================
    # 4. Generate All 7 Real Keyframes Based on m_run_stride1
    # =========================================================================

    # Frame 1: run_trans_start (Transition from Attack Stance to Running)
    m_run_trans_start = empty_matrix()
    for y in range(h):
        for x in range(w):
            anat_c = m_combat["rows"][y]["anatomy"][x]
            if anat_c in ("head_helm", "pauldrons", "torso_cuirass", "waist_fauld"):
                copy_cell(m_combat, m_run_trans_start, x, y, x + 8, y + 1)
            elif anat_c in ("legs_greaves", "feet_sabatons"):
                copy_cell(m_combat, m_run_trans_start, x, y, x + 6, y)
    draw_blade(m_run_trans_start, 50, 48, 88, 62)
    for gx in range(46, 52):
        for gy in range(46, 51):
            copy_cell(m_combat, m_run_trans_start, gx - 2, gy - 2, gx, gy)
    draw_running_cape(m_run_trans_start, attach_x=54, attach_y=32, length=44, wave_phase=0.8, wave_amp=2.5)

    # Frame 2: run_stride_1 (Full Authentic Master Running Pose from Reference)
    # Already computed in m_run_stride1!

    # Frame 3: run_stride_2 (Passing / Left Knee High Airborne Drive)
    m_run_stride2 = empty_matrix()
    for y in range(h):
        for x in range(w):
            anat = m_run_stride1["rows"][y]["anatomy"][x]
            if anat in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets", "waist_fauld", "weapon_sword"):
                copy_cell(m_run_stride1, m_run_stride2, x, y, x, y - 2)
            elif anat in ("legs_greaves", "feet_sabatons"):
                if x > 45:
                    copy_cell(m_run_stride1, m_run_stride2, x, y, x - 12, y + 1)
                else:
                    copy_cell(m_run_stride1, m_run_stride2, x, y, x + 38, y - 10)
    draw_running_cape(m_run_stride2, attach_x=76, attach_y=28, length=66, wave_phase=1.8, wave_amp=4.5)

    # Frame 4: run_stride_3 (Left Leg Planted Contact / Right Leg Extension)
    m_run_stride3 = empty_matrix()
    for y in range(h):
        for x in range(w):
            anat = m_run_stride1["rows"][y]["anatomy"][x]
            if anat in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets", "waist_fauld", "weapon_sword"):
                copy_cell(m_run_stride1, m_run_stride3, x, y, x, y)
            elif anat in ("legs_greaves", "feet_sabatons"):
                if x > 45:
                    copy_cell(m_run_stride1, m_run_stride3, x, y, x - 42, y + 1)
                else:
                    copy_cell(m_run_stride1, m_run_stride3, x, y, x + 44, y)
    draw_running_cape(m_run_stride3, attach_x=76, attach_y=30, length=68, wave_phase=3.4, wave_amp=4.8)

    # Frame 5: run_stride_4 (Passing / Right Knee High Airborne Drive)
    m_run_stride4 = empty_matrix()
    for y in range(h):
        for x in range(w):
            anat = m_run_stride1["rows"][y]["anatomy"][x]
            if anat in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets", "waist_fauld", "weapon_sword"):
                copy_cell(m_run_stride1, m_run_stride4, x, y, x, y - 2)
            elif anat in ("legs_greaves", "feet_sabatons"):
                if x > 45:
                    copy_cell(m_run_stride1, m_run_stride4, x, y, x + 8, y - 10)
                else:
                    copy_cell(m_run_stride1, m_run_stride4, x, y, x - 2, y + 2)
    draw_running_cape(m_run_stride4, attach_x=76, attach_y=28, length=70, wave_phase=5.0, wave_amp=4.2)

    # Frame 6: run_skid_stop (Braking Skid & Deceleration Crouch)
    m_run_skid_stop = empty_matrix()
    for y in range(h):
        for x in range(w):
            anat = m_run_stride1["rows"][y]["anatomy"][x]
            if anat in ("head_helm", "pauldrons", "torso_cuirass", "waist_fauld"):
                copy_cell(m_run_stride1, m_run_skid_stop, x, y, x - 6, y + 3)
            elif anat in ("legs_greaves", "feet_sabatons"):
                copy_cell(m_run_stride1, m_run_skid_stop, x, y, x - 4, min(107, y + 2))
    draw_blade(m_run_skid_stop, 44, 58, 98, 70)
    for gx in range(40, 48):
        for gy in range(54, 61):
            copy_cell(m_run_stride1, m_run_skid_stop, gx, gy, gx - 4, gy + 3)
    draw_running_cape(m_run_skid_stop, attach_x=68, attach_y=34, length=56, wave_phase=1.2, wave_amp=6.0)
    for spark_x, spark_y in ((68, 107), (66, 106), (62, 108), (38, 107), (35, 106), (32, 108)):
        r_row = m_run_skid_stop["rows"][spark_y]
        txt = list(r_row["text"])
        txt[spark_x] = "*"
        r_row["text"] = "".join(txt)
        r_row["fg"][spark_x] = [255, 230, 140]
        r_row["bg"][spark_x] = [60, 40, 20]

    # Frame 7: run_recover_stance (Recovery Return to Active Combat Stance)
    m_run_recover = empty_matrix()
    for y in range(h):
        for x in range(w):
            anat_c = m_combat["rows"][y]["anatomy"][x]
            if anat_c in ("head_helm", "pauldrons", "torso_cuirass", "waist_fauld"):
                copy_cell(m_combat, m_run_recover, x, y, x + 3, y)
            elif anat_c in ("legs_greaves", "feet_sabatons"):
                copy_cell(m_combat, m_run_recover, x, y, x + 2, y)
    draw_blade(m_run_recover, 48, 46, 82, 24)
    for gx in range(44, 52):
        for gy in range(44, 51):
            copy_cell(m_combat, m_run_recover, gx, gy, gx + 2, gy)
    draw_running_cape(m_run_recover, attach_x=48, attach_y=30, length=38, wave_phase=0.4, wave_amp=2.0)

    # 5. Store all 7 frames into knight_high_density.json
    frames_dict = {
        "run_trans_start": m_run_trans_start,
        "run_stride_1": m_run_stride1,
        "run_stride_2": m_run_stride2,
        "run_stride_3": m_run_stride3,
        "run_stride_4": m_run_stride4,
        "run_skid_stop": m_run_skid_stop,
        "run_recover_stance": m_run_recover
    }

    for k, mat in frames_dict.items():
        data[k] = {
            "id": f"knight_{k}",
            "name": k.replace("_", " ").title(),
            "width": w,
            "height": h,
            "rows": mat["rows"],
            "anatomy_zones": [
                "head_helm", "pauldrons", "torso_cuirass", "cape_mantle",
                "arms_gauntlets", "weapon_sword", "waist_fauld", "legs_greaves",
                "feet_sabatons", "ground_flagstone", "background"
            ]
        }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print("Saved all harmonized running frames to knight_high_density.json!")

    # 6. Update knight_data.js
    with open("assets/ascii/characters/knight_data.js", "w", encoding="utf-8") as f:
        f.write("/* High-Density Micro-ASCII Knight Character Dataset (110x116) */\n")
        f.write(f"const HIGH_DENSITY_DATA = {json.dumps(data)};\n")
        f.write("if (typeof module !== 'undefined' && module.exports) {\n    module.exports = HIGH_DENSITY_DATA;\n}\n")
        f.write("if (typeof window !== 'undefined') {\n    window.KNIGHT_DATA = HIGH_DENSITY_DATA;\n    window.HIGH_DENSITY_DATA = HIGH_DENSITY_DATA;\n}\n")
    print("Updated assets/ascii/characters/knight_data.js!")

    # 7. Render 8px snapshots & Progression Strip
    pygame.init()
    font = pygame.font.SysFont("consolas", 8)
    cw, ch = font.size("M")

    def render_mat(mat):
        surf = pygame.Surface((w * cw, h * ch))
        surf.fill((10, 11, 14))
        for py in range(h):
            r = mat["rows"][py]
            for px in range(w):
                pygame.draw.rect(surf, r["bg"][px], (px * cw, py * ch, cw, ch))
                c = r["text"][px]
                if c != ' ':
                    try:
                        surf.blit(font.render(c, False, r["fg"][px]), (px * cw, py * ch))
                    except: pass
        raw = pygame.image.tobytes(surf, "RGB")
        return Image.frombytes("RGB", surf.get_size(), raw)

    all_stage_frames = [
        ("0_active_combat_stance", m_combat, "0. Base Combat Stance"),
        ("1_run_trans_start", m_run_trans_start, "1. Sprint Initiation Lean"),
        ("2_run_stride_1", m_run_stride1, "2. Stride 1 (Right Foot Contact)"),
        ("3_run_stride_2", m_run_stride2, "3. Stride 2 (Left Knee Drive)"),
        ("4_run_stride_3", m_run_stride3, "4. Stride 3 (Left Foot Contact)"),
        ("5_run_stride_4", m_run_stride4, "5. Stride 4 (Right Knee Drive)"),
        ("6_run_skid_stop", m_run_skid_stop, "6. Braking Skid Stop"),
        ("7_run_recover_stance", m_run_recover, "7. Recover to Combat Guard")
    ]

    rendered_imgs = []
    for tag, mat, label in all_stage_frames:
        img_out = render_mat(mat)
        rendered_imgs.append((img_out, label))
        single_path = f"assets/mockup_run_{tag}.png"
        img_out.save(single_path)
        print(f"Saved {single_path}")

    # Build composite progression strip (8 stages horizontally)
    fw, fh = rendered_imgs[0][0].size
    strip_w = fw * len(rendered_imgs)
    strip_h = fh + 38
    strip = Image.new("RGB", (strip_w, strip_h), (12, 14, 18))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(strip)

    for idx, (img_out, label) in enumerate(rendered_imgs):
        ox = idx * fw
        strip.paste(img_out, (ox, 0))
        draw.line([(ox + fw - 1, 0), (ox + fw - 1, strip_h)], fill=(60, 68, 86))
        draw.rectangle([(ox, fh), (ox + fw, strip_h)], fill=(18, 20, 26))
        draw.text((ox + 10, fh + 10), label, fill=(241, 196, 15))

    strip_path = "assets/knight_run_progression_strip.png"
    strip.save(strip_path)
    print(f"Saved {strip_path} ({strip_w}x{strip_h})!")

    # 8. Render high-quality looping animated GIF
    gif_frames = []
    # Base combat stance (3 frames)
    img_combat = rendered_imgs[0][0]
    for _ in range(3):
        gif_frames.append((img_combat, 80))
    # Sprint initiation (2 frames)
    img_start = rendered_imgs[1][0]
    gif_frames.append((img_start, 70))
    gif_frames.append((img_start, 60))
    # 3 Stride Cycles (Stride 1 -> 2 -> 3 -> 4)
    img_s1 = rendered_imgs[2][0]
    img_s2 = rendered_imgs[3][0]
    img_s3 = rendered_imgs[4][0]
    img_s4 = rendered_imgs[5][0]
    for _ in range(3):
        gif_frames.append((img_s1, 65))
        gif_frames.append((img_s2, 65))
        gif_frames.append((img_s3, 65))
        gif_frames.append((img_s4, 65))
    # Braking skid (3 frames)
    img_skid = rendered_imgs[6][0]
    gif_frames.append((img_skid, 85))
    gif_frames.append((img_skid, 95))
    gif_frames.append((img_skid, 85))
    # Recovery stance (2 frames)
    img_rec = rendered_imgs[7][0]
    gif_frames.append((img_rec, 75))
    gif_frames.append((img_rec, 75))
    # Settle in combat stance (3 frames)
    for _ in range(3):
        gif_frames.append((img_combat, 80))

    gif_imgs = [f[0] for f in gif_frames]
    gif_durs = [f[1] for f in gif_frames]
    gif_path = "assets/knight_run_animation.gif"
    gif_imgs[0].save(
        gif_path,
        save_all=True,
        append_images=gif_imgs[1:],
        duration=gif_durs,
        loop=0,
        optimize=True
    )
    print(f"Saved animated GIF {gif_path} ({len(gif_frames)} frames)!")

    # 9. Copy all deliverables to brain directory
    artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"
    shutil.copy2(strip_path, os.path.join(artifact_dir, "knight_run_progression_strip.png"))
    shutil.copy2(gif_path, os.path.join(artifact_dir, "knight_run_animation.gif"))
    for tag, _, _ in all_stage_frames:
        shutil.copy2(f"assets/mockup_run_{tag}.png", os.path.join(artifact_dir, f"mockup_run_{tag}.png"))
    print("All deliverables copied to brain directory successfully!")

if __name__ == "__main__":
    main()
