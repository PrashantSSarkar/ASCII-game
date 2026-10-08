import json
import copy
import math
import os
import shutil
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
from PIL import Image

def main():
    json_path = "assets/ascii/characters/knight_high_density.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    m_combat = data["combat_stance"]
    m_rest = data["standing_sentinel"]
    w = m_combat["width"]
    h = m_combat["height"]

    # 1. Build a 100% PERFECT SEAMLESS background plate
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
                if len(ground_donors) > 0:
                    donor = ground_donors[(x * 13 + y * 7) % len(ground_donors)]
                    row.append(copy.deepcopy(donor))
                else:
                    row.append({"text": "=", "fg": [110, 105, 95], "bg": [18, 16, 14], "anatomy": "ground_flagstone"})
            else:
                if len(wall_donors) > 0:
                    donor = wall_donors[(x * 11 + y * 17) % len(wall_donors)]
                    row.append(copy.deepcopy(donor))
                else:
                    row.append({"text": "%", "fg": [120, 105, 85], "bg": [19, 16, 13], "anatomy": "background"})
        bg_plate.append(row)

    # Helper: draw Bresenham line
    def draw_line(matrix, x0, y0, x1, y1, ch, fg, bg, zone, width=1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            for ox in range(-width // 2, width // 2 + 1):
                for oy in range(-width // 2, width // 2 + 1):
                    px = x + ox
                    py = y + oy
                    if 0 <= px < matrix["width"] and 0 <= py < matrix["height"]:
                        r = matrix["rows"][py]
                        txt = list(r["text"])
                        txt[px] = ch
                        r["text"] = "".join(txt)
                        r["fg"][px] = fg[:]
                        r["bg"][px] = bg[:]
                        r["anatomy"][px] = zone
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

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

    # Clean combat stance with no sword
    m_combat_clean = copy.deepcopy(m_combat)
    for y in range(h):
        r = m_combat_clean["rows"][y]
        txt = list(r["text"])
        for x in range(w):
            if r["anatomy"][x] == "weapon_sword":
                plate = bg_plate[y][x]
                txt[x] = plate["text"]
                r["fg"][x] = plate["fg"][:]
                r["bg"][x] = plate["bg"][:]
                r["anatomy"][x] = plate["anatomy"]
        r["text"] = "".join(txt)

    # Master Sword Drawing function (same as heavy attack)
    def render_greatsword(matrix, hx, hy, tx, ty, add_wave=False):
        dx = tx - hx
        dy = ty - hy
        length = math.hypot(dx, dy)
        ux = dx / max(1e-4, length)
        uy = dy / max(1e-4, length)

        angle_deg = math.degrees(math.atan2(dy, dx))
        if -22.5 <= angle_deg <= 22.5 or angle_deg >= 157.5 or angle_deg <= -157.5:
            blade_ch = "="
        elif 22.5 < angle_deg < 67.5 or -157.5 < angle_deg < -112.5:
            blade_ch = "\\"
        elif 67.5 <= angle_deg <= 112.5 or -112.5 <= angle_deg <= -67.5:
            blade_ch = "|"
        else:
            blade_ch = "/"

        # Pommel
        px = int(round(hx - ux * 4.5))
        py = int(round(hy - uy * 4.5))
        draw_line(matrix, px, py, px, py, "O", [215, 225, 235], [35, 42, 52], "weapon_sword", width=1)

        # Grip
        draw_line(matrix, px, py, hx, hy, "#", [115, 120, 128], [24, 26, 30], "weapon_sword", width=1)

        # Gauntlets
        draw_line(matrix, int(hx - 1), int(hy), int(hx + 1), int(hy + 1), "@", [190, 195, 200], [30, 32, 36], "arms_gauntlets", width=1)

        # Crossguard
        perp_x = -uy
        perp_y = ux
        gx1 = int(round(hx - perp_x * 4.0))
        gy1 = int(round(hy - perp_y * 4.0))
        gx2 = int(round(hx + perp_x * 4.0))
        gy2 = int(round(hy + perp_y * 4.0))
        draw_line(matrix, gx1, gy1, gx2, gy2, "+", [235, 242, 252], [42, 50, 60], "weapon_sword", width=1)

        # Blade Core
        draw_line(matrix, hx, hy, tx, ty, blade_ch, [255, 255, 255], [65, 80, 100], "weapon_sword", width=1)
        # Fuller channel
        fx0 = int(round(hx + perp_x))
        fy0 = int(round(hy + perp_y))
        fx1 = int(round(tx + perp_x))
        fy1 = int(round(ty + perp_y))
        draw_line(matrix, fx0, fy0, fx1, fy1, blade_ch, [170, 192, 218], [36, 46, 60], "weapon_sword", width=1)

        # Tip apex
        tip_ch = "^" if dy < -20 else (">" if dx > 20 else ("v" if dy > 20 else "*"))
        if 0 <= tx < w and 0 <= ty < h:
            r_tip = matrix["rows"][ty]
            t_txt = list(r_tip["text"])
            t_txt[tx] = tip_ch
            r_tip["text"] = "".join(t_txt)
            r_tip["fg"][tx] = [255, 255, 255]
            r_tip["bg"][tx] = [80, 100, 125]
            r_tip["anatomy"][tx] = "weapon_sword"

        # Crescent Slash Arc
        if add_wave:
            arc_pts = [
                (int(tx - 16), int(ty - 14), "*", [255, 255, 255], [100, 130, 170]),
                (int(tx - 8), int(ty - 9), "/", [230, 245, 255], [80, 110, 150]),
                (int(tx - 2), int(ty - 4), "/", [245, 250, 255], [90, 120, 160]),
                (int(tx + 2), int(ty), ">", [255, 255, 255], [110, 140, 180]),
                (int(tx + 1), int(ty + 5), ")", [230, 245, 255], [85, 115, 155]),
                (int(tx - 4), int(ty + 10), ")", [200, 230, 255], [70, 95, 135]),
                (int(tx - 12), int(ty + 15), "/", [170, 210, 250], [50, 75, 110]),
                (int(tx - 22), int(ty + 19), "-", [140, 185, 235], [35, 60, 90]),
                (int(tx - 34), int(ty + 22), "~", [110, 155, 210], [25, 45, 75]),
            ]
            for ax, ay, ach, afg, abg in arc_pts:
                if 0 <= ax < w and 0 <= ay < h:
                    r_arc = matrix["rows"][ay]
                    atxt = list(r_arc["text"])
                    atxt[ax] = ach
                    r_arc["text"] = "".join(atxt)
                    r_arc["fg"][ax] = afg
                    r_arc["bg"][ax] = abg
                    r_arc["anatomy"][ax] = "weapon_sword"

    # -------------------------------------------------------------
    # 1. KEYFRAME: spin_step
    # Knight takes a step with his back leg across, initiating pivot
    # -------------------------------------------------------------
    m_spin_step = empty_matrix()
    for y in range(h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat not in ("background", "ground_flagstone"):
                dx, dy = 0, 0
                if anat in ("head_helm", "pauldrons", "torso_cuirass"):
                    dx = 3
                    dy = 1
                elif anat == "arms_gauntlets":
                    dx = 2
                    dy = 0
                elif anat == "cape_mantle":
                    cape_pct = max(0.0, (y - 20) / 85.0)
                    dx = int(round(3 + 8 * cape_pct))
                    dy = 1
                elif anat == "waist_fauld":
                    dx = 4
                    dy = 1
                elif anat in ("legs_greaves", "feet_sabatons"):
                    # Back leg (x < 38) takes an aggressive step forward across!
                    if x < 40:
                        dx = 14  # Back leg steps forward across!
                        dy = -1
                    else:
                        dx = 1   # Front leg pivots
                        dy = 1
                
                tx = x + dx
                ty = y + dy
                if 0 <= tx < w and 0 <= ty < h:
                    r_dst = m_spin_step["rows"][ty]
                    txt = list(r_dst["text"])
                    txt[tx] = r_src["text"][x]
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][tx] = r_src["fg"][x][:]
                    r_dst["bg"][tx] = r_src["bg"][x][:]
                    r_dst["anatomy"][tx] = anat

    # Arms & Sword during spin_step: held mid-low, gathering angular momentum
    draw_line(m_spin_step, 36, 48, 42, 54, "@", [160, 170, 180], [28, 30, 34], "arms_gauntlets", width=1)
    render_greatsword(m_spin_step, 42, 54, 16, 72, add_wave=False)


    # -------------------------------------------------------------
    # 2. KEYFRAME: spin_back_cut
    # Full back turned towards the viewer!
    # Cape draped over back and billowing to the right,
    # rear armor and legs visible in powerful athletic plant,
    # broad sweeping horizontal cleave reaching out to 106!
    # -------------------------------------------------------------
    m_spin_back_cut = empty_matrix()

    # Step A: Transfer lower body (waist_fauld, legs, feet)
    for y in range(h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat in ("waist_fauld", "legs_greaves", "feet_sabatons"):
                # Stepped back leg is now planted forward at center
                # Other leg coiled behind on left
                if x < 40:
                    dx = 14  # Stepped leg planted forward!
                    dy = 1
                else:
                    dx = -4  # Other leg coiled behind
                    dy = 0
                
                tx = x + dx
                ty = y + dy
                if 0 <= tx < w and 0 <= ty < h:
                    r_dst = m_spin_back_cut["rows"][ty]
                    txt = list(r_dst["text"])
                    txt[tx] = r_src["text"][x]
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][tx] = [int(c * 0.92) for c in r_src["fg"][x]]
                    r_dst["bg"][tx] = [int(c * 0.92) for c in r_src["bg"][x]]
                    r_dst["anatomy"][tx] = anat

    # Step B: Render Helmet from the REAR at TRUE coordinates
    cx_head = 45
    for y in range(12, 28):
        radius = 3 + int(3.5 * (y - 12) / 15.0)
        for x in range(cx_head - radius, cx_head + radius + 1):
            if 0 <= x < w and 0 <= y < h:
                r_dst = m_spin_back_cut["rows"][y]
                txt = list(r_dst["text"])
                dist = abs(x - cx_head)
                if dist == 0:
                    txt[x] = "|" if y % 2 == 0 else "!"
                    fg = [215, 220, 230]
                    bg = [48, 52, 62]
                elif dist == 1:
                    txt[x] = "8" if y % 2 == 0 else "0"
                    fg = [185, 190, 205]
                    bg = [38, 42, 52]
                elif dist < radius:
                    txt[x] = "[" if x < cx_head else "]"
                    fg = [150, 155, 170]
                    bg = [30, 34, 44]
                else:
                    txt[x] = "(" if x < cx_head else ")"
                    fg = [115, 120, 135]
                    bg = [22, 26, 34]
                r_dst["text"] = "".join(txt)
                r_dst["fg"][x] = fg
                r_dst["bg"][x] = bg
                r_dst["anatomy"][x] = "head_helm"

    # Red Crest plume streaming from top: y in [8, 18], x in [43, 60]
    for y in range(8, 19):
        crest_len = 2 + int(10.0 * (1.0 - (y - 8) / 11.0))
        for ox in range(crest_len):
            cx = cx_head + ox
            if 0 <= cx < w:
                r_dst = m_spin_back_cut["rows"][y]
                txt = list(r_dst["text"])
                txt[cx] = "*" if ox == 0 else ("^" if ox < crest_len - 1 else "~")
                intensity = max(0.4, 1.0 - ox / float(crest_len))
                fg = [int(220 * intensity + 20), int(75 * intensity), int(70 * intensity)]
                bg = [int(65 * intensity + 15), int(18 * intensity), int(16 * intensity)]
                r_dst["text"] = "".join(txt)
                r_dst["fg"][cx] = fg
                r_dst["bg"][cx] = bg
                r_dst["anatomy"][cx] = "head_helm"

    # Nape maille aventail: y in [24, 30], x in [39, 53]
    for y in range(24, 31):
        w_nape = 4 + (y - 24)
        for ox in range(-w_nape, w_nape + 1):
            cx = cx_head + ox
            if 0 <= cx < w:
                r_dst = m_spin_back_cut["rows"][y]
                txt = list(r_dst["text"])
                txt[cx] = "#" if (cx + y) % 2 == 0 else "%"
                fg = [125, 130, 140]
                bg = [30, 34, 42]
                r_dst["text"] = "".join(txt)
                r_dst["fg"][cx] = fg
                r_dst["bg"][cx] = bg
                r_dst["anatomy"][cx] = "pauldrons"

    # Rear Pauldrons with organic shoulder curves
    for y in range(24, 43):
        y_prog = (y - 24) / 18.0
        p_left_start = int(32 - 7.0 * math.sin(y_prog * math.pi))
        p_left_end = 39
        for px in range(p_left_start, p_left_end + 1):
            r_dst = m_spin_back_cut["rows"][y]
            txt = list(r_dst["text"])
            txt[px] = "(" if px == p_left_start else ("=" if y % 3 == 0 else "\\")
            fg = [155, 160, 170]
            bg = [36, 40, 48]
            r_dst["text"] = "".join(txt)
            r_dst["fg"][px] = fg
            r_dst["bg"][px] = bg
            r_dst["anatomy"][px] = "pauldrons"

        p_right_start = 50
        p_right_end = int(58 + 8.0 * math.sin(y_prog * math.pi))
        for px in range(p_right_start, p_right_end + 1):
            r_dst = m_spin_back_cut["rows"][y]
            txt = list(r_dst["text"])
            txt[px] = ")" if px == p_right_end else ("=" if y % 3 == 0 else "/")
            fg = [160, 165, 175]
            bg = [38, 42, 50]
            r_dst["text"] = "".join(txt)
            r_dst["fg"][px] = fg
            r_dst["bg"][px] = bg
            r_dst["anatomy"][px] = "pauldrons"

    # Cuirass Backplate (Dorsal harness): y in [28, 54], x in [38, 52]
    for y in range(28, 55):
        for bx in range(38, 53):
            r_dst = m_spin_back_cut["rows"][y]
            txt = list(r_dst["text"])
            dist = abs(bx - cx_head)
            if dist == 0:
                txt[bx] = "|" if y % 2 == 0 else "!"
                fg = [190, 195, 210]
                bg = [42, 46, 56]
            elif dist <= 2:
                txt[bx] = "8" if y % 4 == 0 else ("H" if y % 4 == 2 else "=")
                fg = [160, 165, 175]
                bg = [34, 38, 46]
            else:
                txt[bx] = "[" if bx < cx_head else "]"
                fg = [130, 135, 145]
                bg = [26, 30, 38]
            r_dst["text"] = "".join(txt)
            r_dst["fg"][bx] = fg
            r_dst["bg"][bx] = bg
            r_dst["anatomy"][bx] = "torso_cuirass"

    # CAPE DRAPED OVER BACK AND BILLOWING TO THE RIGHT!
    # Cape leaves the left leg visible (cx >= 38 below y=60) so the knight's armor and planted legs are clearly seen!
    for y in range(24, 102):
        y_rel = (y - 24) / 78.0
        if y < 58:
            c_left = max(34, 40 - int(6.0 * math.sin(y_rel * math.pi)))
        else:
            c_left = max(42, 48 - int(6.0 * math.sin(y_rel * math.pi)))
        
        c_right = min(96, 54 + int(42.0 * math.sin(y_rel * math.pi * 0.85)))
        
        if y < 20 or y >= 106:
            continue

        for cx in range(c_left, c_right + 1):
            if 28 <= y <= 38 and (cx_head - 2) <= cx <= (cx_head + 2):
                continue

            r_dst = m_spin_back_cut["rows"][y]
            txt = list(r_dst["text"])
            
            wave = math.sin(cx * 0.38 + y * 0.28)
            if wave > 0.6:
                ch = "%"
            elif wave > 0.2:
                ch = "#"
            elif wave > -0.2:
                ch = "&"
            elif wave > -0.6:
                ch = "S"
            else:
                ch = "="
                
            fold_shading = 0.5 + 0.5 * math.sin(cx * 0.35 + y * 0.25)
            rim_light = max(0.0, (cx - 44) / 48.0)
            
            fg = [
                min(255, int(115 * fold_shading + 85 * rim_light + 25)),
                min(255, int(32 * fold_shading + 30 * rim_light + 10)),
                min(255, int(28 * fold_shading + 25 * rim_light + 10))
            ]
            bg = [
                min(255, int(45 * fold_shading + 40 * rim_light + 12)),
                min(255, int(14 * fold_shading + 12 * rim_light + 4)),
                min(255, int(12 * fold_shading + 10 * rim_light + 4))
            ]
            
            txt[cx] = ch
            r_dst["text"] = "".join(txt)
            r_dst["fg"][cx] = fg
            r_dst["bg"][cx] = bg
            r_dst["anatomy"][cx] = "cape_mantle"

    # Arms driving the blade across
    draw_line(m_spin_back_cut, 36, 44, 46, 48, "@", [160, 170, 180], [28, 30, 34], "arms_gauntlets", width=1)
    draw_line(m_spin_back_cut, 44, 44, 48, 48, "@", [180, 190, 200], [30, 32, 36], "arms_gauntlets", width=1)

    # SWORD: Sweeping Greatsword horizontal cleave extending out to tip (106, 44) with crescent wave!
    render_greatsword(m_spin_back_cut, 48, 48, 106, 44, add_wave=True)


    # -------------------------------------------------------------
    # 3. KEYFRAME: spin_unwind_step
    # Knight steps with the other leg to return to attack stance,
    # rotating back to face front, sword finishing upward follow-through
    # -------------------------------------------------------------
    m_spin_unwind_step = empty_matrix()
    for y in range(h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat not in ("background", "ground_flagstone"):
                dx, dy = 0, 0
                if anat in ("head_helm", "pauldrons", "torso_cuirass"):
                    dx = 4
                    dy = 1
                elif anat == "arms_gauntlets":
                    dx = 5
                    dy = 0
                elif anat == "cape_mantle":
                    cape_pct = max(0.0, (y - 20) / 85.0)
                    dx = int(round(5 + 10 * cape_pct))
                    dy = 1
                elif anat == "waist_fauld":
                    dx = 4
                    dy = 1
                elif anat in ("legs_greaves", "feet_sabatons"):
                    # The other leg (right leg, x >= 40) steps around forward!
                    if x >= 40:
                        dx = 10   # Stepping around forward into combat stance plant!
                        dy = 0
                    else:
                        dx = 2   # Pivot base
                        dy = 1
                
                tx = x + dx
                ty = y + dy
                if 0 <= tx < w and 0 <= ty < h:
                    r_dst = m_spin_unwind_step["rows"][ty]
                    txt = list(r_dst["text"])
                    txt[tx] = r_src["text"][x]
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][tx] = r_src["fg"][x][:]
                    r_dst["bg"][tx] = r_src["bg"][x][:]
                    r_dst["anatomy"][tx] = anat

    # Arms and sword follow-through in spin_unwind_step:
    draw_line(m_spin_unwind_step, 40, 46, 48, 48, "@", [160, 170, 180], [28, 30, 34], "arms_gauntlets", width=1)
    render_greatsword(m_spin_unwind_step, 48, 48, 86, 18, add_wave=False)

    # Store into json data
    data["spin_step"] = m_spin_step
    data["spin_back_cut"] = m_spin_back_cut
    data["spin_unwind_step"] = m_spin_unwind_step

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Updated knight_high_density.json with spin attack keyframes!")

    # Update knight_data.js
    js_path = "assets/ascii/characters/knight_data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("/* High-Density Micro-ASCII Knight Character Dataset (110x116) */\n")
        f.write("const HIGH_DENSITY_DATA = ")
        json.dump(data, f)
        f.write(";\n")
        f.write("if (typeof module !== 'undefined' && module.exports) {\n")
        f.write("    module.exports = HIGH_DENSITY_DATA;\n")
        f.write("}\n")
    print("Updated knight_data.js with spin attack keyframes!")

    # Render test snapshot of the keyframes
    pygame.init()
    font = pygame.font.SysFont("consolas", 8)
    cw, ch = font.size("M")

    for k in ["spin_step", "spin_back_cut", "spin_unwind_step"]:
        mat = data[k]
        surf = pygame.Surface((w * cw, h * ch))
        surf.fill((10, 11, 14))
        for y in range(h):
            row = mat["rows"][y]
            for x in range(w):
                bg = row["bg"][x]
                fg = row["fg"][x]
                c = row["text"][x]
                pygame.draw.rect(surf, bg, (x * cw, y * ch, cw, ch))
                if c != ' ':
                    try:
                        ts = font.render(c, False, fg)
                        surf.blit(ts, (x * cw, y * ch))
                    except:
                        pass
        raw = pygame.image.tobytes(surf, "RGB")
        img = Image.frombytes("RGB", surf.get_size(), raw)
        out_p = os.path.join("assets", f"knight_{k}_8px.png")
        img.save(out_p)
        print(f"Rendered {out_p}")

    # Generate 5-stage spin progression strip
    snap1 = Image.open("assets/knight_combat_stance_8px.png")
    snap2 = Image.open("assets/knight_spin_step_8px.png")
    snap3 = Image.open("assets/knight_spin_back_cut_8px.png")
    snap4 = Image.open("assets/knight_spin_unwind_step_8px.png")
    snap5 = Image.open("assets/knight_combat_stance_8px.png")

    frames = [snap1, snap2, snap3, snap4, snap5]
    sw, sh = snap1.size
    strip = Image.new("RGB", (sw * len(frames), sh), (10, 11, 14))
    for i, frame in enumerate(frames):
        strip.paste(frame, (i * sw, 0))
    strip_out = os.path.join("assets", "knight_spin_progression_strip.png")
    strip.save(strip_out)
    print(f"Saved spin progression strip to {strip_out}")

    # Copy to brain artifacts
    artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"
    if os.path.isdir(artifact_dir):
        for k in ["spin_step", "spin_back_cut", "spin_unwind_step"]:
            shutil.copy2(os.path.join("assets", f"knight_{k}_8px.png"), os.path.join(artifact_dir, f"knight_{k}_8px.png"))
        shutil.copy2(strip_out, os.path.join(artifact_dir, "knight_spin_progression_strip.png"))
        print("Copied spin attack artifacts to brain directory!")

if __name__ == "__main__":
    main()
