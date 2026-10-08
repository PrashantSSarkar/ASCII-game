"""
⚔️ Comprehensive Detail Fix:
1. Polish gothic steel sword crossguard during transition (NO yellow/gold).
2. Clean all dark blue sky remnants in the arm/shoulder region in combat stance.
3. Procedural razor-sharp greatsword blade in combat stance (defined cutting edges, fuller, specular glints, pointed tip).
4. Remove ghost silhouette of old rest-stance cape on the left flank in combat stance with warm ambient background plate.
"""

import json
import math
import copy

def run_fix():
    with open("assets/ascii/characters/knight_high_density.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    m_rest = data["standing_sentinel"]
    m_combat = data["combat_stance"]
    w = 84
    h = 116

    # =========================================================================
    # STEP 1: Build 100% Pristine Uniform Warm Background Plate
    # =========================================================================
    clean_wall_pool = []
    for y in range(0, 50):
        r = m_rest["rows"][y]
        for x in range(w):
            if r["anatomy"][x] == "background":
                fg = r["fg"][x]
                bg = r["bg"][x]
                # True torchlit stone wall
                if bg[0] >= 14 and bg[0] >= bg[2] and sum(bg) >= 30 and sum(fg) >= 200:
                    clean_wall_pool.append({
                        "text": r["text"][x],
                        "fg": fg[:],
                        "bg": bg[:],
                        "anatomy": "background"
                    })

    clean_ground_pool = []
    for y in range(108, 116):
        r = m_rest["rows"][y]
        for x in range(w):
            if r["anatomy"][x] in ("ground_flagstone", "background"):
                fg = r["fg"][x]
                bg = r["bg"][x]
                if sum(bg) >= 20:
                    clean_ground_pool.append({
                        "text": r["text"][x],
                        "fg": fg[:],
                        "bg": bg[:],
                        "anatomy": "ground_flagstone"
                    })

    bg_plate = []
    for y in range(h):
        row = []
        r_rest = m_rest["rows"][y]
        for x in range(w):
            if y >= 108:
                if r_rest["anatomy"][x] in ("ground_flagstone", "background") and sum(r_rest["bg"][x]) >= 20:
                    row.append({
                        "text": r_rest["text"][x],
                        "fg": r_rest["fg"][x][:],
                        "bg": r_rest["bg"][x][:],
                        "anatomy": "ground_flagstone"
                    })
                else:
                    donor = clean_ground_pool[(x * 7 + y * 13) % len(clean_ground_pool)]
                    row.append(copy.deepcopy(donor))
            else:
                anat = r_rest["anatomy"][x]
                fg = r_rest["fg"][x]
                bg = r_rest["bg"][x]
                if anat == "background" and bg[0] >= 14 and bg[0] >= bg[2] and sum(bg) >= 30 and sum(fg) >= 200:
                    row.append({
                        "text": r_rest["text"][x],
                        "fg": r_rest["fg"][x][:],
                        "bg": r_rest["bg"][x][:],
                        "anatomy": "background"
                    })
                else:
                    donor = clean_wall_pool[(x * 11 + y * 17) % len(clean_wall_pool)]
                    row.append(copy.deepcopy(donor))
        bg_plate.append(row)

    print(f"Generated clean bg_plate ({len(bg_plate)} rows, pool {len(clean_wall_pool)})")

    # =========================================================================
    # STEP 2: Clean Combat Stance Silhouette, Arm Region, and Old Cape Outline
    # =========================================================================
    # Determine the left boundary where knight armor/cape starts for each row
    def get_knight_left_bound(y):
        if y < 24:
            return 26
        elif y <= 26:
            return 22
        elif y <= 29:
            return 22
        elif y <= 34:
            return 20
        elif y <= 38:
            return 17
        elif y <= 44:
            return 16
        elif y <= 53:
            return 19
        elif y <= 60:
            return 17
        elif y <= 80:
            return 16
        elif y <= 104:
            return 15
        else:
            return 10

    # 2a. Reset ALL old weapon_sword cells and blurry smear in combat stance
    for y in range(h):
        r_com = m_combat["rows"][y]
        txt = list(r_com["text"])
        expected_sword_x = 82.0 - (y - 10) * 1.25 if 10 <= y <= 65 else -100
        for x in range(w):
            is_old_sword = (r_com["anatomy"][x] == "weapon_sword")
            is_near_old_sword = (abs(x - expected_sword_x) <= 7 and (x < 28 or y < 35 or is_old_sword))
            if is_old_sword or is_near_old_sword:
                plate = bg_plate[y][x]
                txt[x] = plate["text"]
                r_com["fg"][x] = plate["fg"][:]
                r_com["bg"][x] = plate["bg"][:]
                r_com["anatomy"][x] = plate["anatomy"]
        r_com["text"] = "".join(txt)

    # 2b. Clean background, remove blue sky in arm region and dark cape outline on left flank
    for y in range(h):
        r_com = m_combat["rows"][y]
        txt = list(r_com["text"])
        left_bound = get_knight_left_bound(y)

        for x in range(w):
            anat = r_com["anatomy"][x]
            fg = r_com["fg"][x]
            bg = r_com["bg"][x]
            is_red = (fg[0] > 45 and fg[0] > fg[1] * 1.30 and fg[0] > fg[2] * 1.30)
            is_blue = (bg[2] > bg[0] and bg[2] >= 14) or (fg[2] > fg[0] + 10 and sum(fg) < 420)

            should_be_bg = False

            # Everything to the left of the knight's silhouette
            if x < left_bound:
                should_be_bg = True

            # In the arm/shoulder region (y in [24..62], x in [16..32]), remove blue sky
            elif 24 <= y <= 62 and x <= 32:
                if is_blue and not is_red:
                    should_be_bg = True

            # Leg gap in combat stance
            elif 26 <= x <= 40 and not is_red and 80 <= y <= 104:
                lum = sum(fg) / 3.0
                if lum < 115 or is_blue:
                    should_be_bg = True

            # Existing background or ground flagstone
            elif anat in ("background", "ground_flagstone"):
                should_be_bg = True

            if should_be_bg:
                plate = bg_plate[y][x]
                txt[x] = plate["text"]
                r_com["fg"][x] = plate["fg"][:]
                r_com["bg"][x] = plate["bg"][:]
                r_com["anatomy"][x] = plate["anatomy"]
            else:
                # For remaining armor, ensure warm specular tone (no cold blue cast)
                if not is_red and anat != "cape_mantle":
                    if fg[2] > fg[0]:
                        fg[0] = fg[2]
                        fg[1] = max(fg[1], fg[2] - 5)
                    if bg[2] > bg[0]:
                        bg[0] = bg[2]
                        bg[1] = max(bg[1], bg[2] - 3)

        r_com["text"] = "".join(txt)

    # =========================================================================
    # STEP 3: Procedural Razor-Sharp Greatsword Blade in combat_stance
    # =========================================================================
    sword_grid = {}

    # 3a. Needle-sharp Apex Tip at (82, 10)
    sword_grid[(82, 10)] = ("^", [255, 255, 255], [70, 85, 105], "weapon_sword")
    sword_grid[(81, 11)] = ("/", [255, 255, 255], [65, 80, 100], "weapon_sword")
    sword_grid[(80, 11)] = ("/", [190, 210, 235], [42, 52, 66], "weapon_sword")

    # 3b. Blade Body from y = 12 down to y = 56
    for y in range(12, 57):
        xc = 82.0 - (y - 10) * 1.25
        x_edge = int(round(xc))
        x_fuller = x_edge - 1

        # Specular glint every 7 rows along cutting edge
        is_glint = (y % 7 == 2)
        edge_ch = "*" if is_glint else "/"
        edge_fg = [255, 255, 255]
        edge_bg = [95, 115, 140] if is_glint else [65, 80, 100]

        sword_grid[(x_edge, y)] = (edge_ch, edge_fg, edge_bg, "weapon_sword")
        sword_grid[(x_fuller, y)] = ("/", [170, 192, 218], [36, 46, 60], "weapon_sword")

        # Ricasso widening near hilt
        if y >= 48:
            x_spine = x_fuller - 1
            sword_grid[(x_spine, y)] = ("/", [140, 160, 185], [30, 38, 50], "weapon_sword")

    # 3c. Gothic Steel Cruciform Quillons / Crossguard at (22, 58)
    quillon_pts = [
        (20, 56, "*", [210, 225, 240], [35, 42, 50]),
        (21, 57, "=", [228, 236, 246], [40, 48, 58]),
        (22, 58, "+", [242, 248, 255], [45, 54, 65]),
        (23, 59, "=", [228, 236, 246], [40, 48, 58]),
        (24, 60, "*", [210, 225, 240], [35, 42, 50]),
    ]
    for qx, qy, qch, qfg, qbg in quillon_pts:
        sword_grid[(qx, qy)] = (qch, qfg, qbg, "weapon_sword")

    # 3d. Dark Wrapped Grip & Steel Pommel
    sword_grid[(21, 59)] = ("#", [115, 120, 128], [24, 26, 30], "weapon_sword")
    sword_grid[(20, 60)] = ("#", [115, 120, 128], [24, 26, 30], "weapon_sword")
    sword_grid[(19, 61)] = ("O", [215, 225, 235], [35, 42, 52], "weapon_sword")

    # 3e. Articulated Steel Gauntlets gripping hilt (Neutral warm steel)
    sword_grid[(21, 58)] = ("@", [195, 195, 195], [32, 32, 32], "arms_gauntlets")
    sword_grid[(22, 59)] = ("@", [195, 195, 195], [32, 32, 32], "arms_gauntlets")

    # Apply sword_grid into m_combat
    for (sx, sy), (sch, sfg, sbg, sanat) in sword_grid.items():
        if 0 <= sx < w and 0 <= sy < h:
            r = m_combat["rows"][sy]
            txt = list(r["text"])
            txt[sx] = sch
            r["text"] = "".join(txt)
            r["fg"][sx] = sfg[:]
            r["bg"][sx] = sbg[:]
            r["anatomy"][sx] = sanat

    print("Procedural crisp razor-sharp greatsword blade rendered in combat_stance!")

    # =========================================================================
    # STEP 4: Build Pristine Transition Frames
    # =========================================================================
    def clean_sword_free(matrix, stance_type):
        m = copy.deepcopy(matrix)
        if stance_type == "rest":
            for y in range(h):
                r = m["rows"][y]
                txt = list(r["text"])
                for x in range(w):
                    if r["anatomy"][x] == "weapon_sword":
                        donor_x = 37 if (37 < w and r["anatomy"][37] != "weapon_sword") else 47
                        txt[x] = r["text"][donor_x]
                        r["fg"][x] = r["fg"][donor_x][:]
                        r["bg"][x] = r["bg"][donor_x][:]
                        r["anatomy"][x] = r["anatomy"][donor_x]
                r["text"] = "".join(txt)
        else:
            for y in range(h):
                r = m["rows"][y]
                txt = list(r["text"])
                for x in range(w):
                    if r["anatomy"][x] == "weapon_sword":
                        plate = bg_plate[y][x]
                        txt[x] = plate["text"]
                        r["fg"][x] = plate["fg"][:]
                        r["bg"][x] = plate["bg"][:]
                        r["anatomy"][x] = plate["anatomy"]
                r["text"] = "".join(txt)
        return m

    m_rest_clean = clean_sword_free(m_rest, "rest")
    m_combat_clean = clean_sword_free(m_combat, "combat")

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

    def build_trans_frame(alpha, hilt, tip):
        out = {
            "width": w,
            "height": h,
            "rows": []
        }
        for y in range(h):
            r_out_txt = []
            r_out_fg = []
            r_out_bg = []
            r_out_anat = []

            r_rest_c = m_rest_clean["rows"][y]
            r_com_c = m_combat_clean["rows"][y]

            for x in range(w):
                anat_0 = r_rest_c["anatomy"][x]
                anat_1 = r_com_c["anatomy"][x]

                is_bg_0 = anat_0 in ("background", "ground_flagstone")
                is_bg_1 = anat_1 in ("background", "ground_flagstone")

                if is_bg_0 and is_bg_1:
                    plate_cell = bg_plate[y][x]
                    r_out_txt.append(plate_cell["text"])
                    r_out_fg.append(plate_cell["fg"][:])
                    r_out_bg.append(plate_cell["bg"][:])
                    r_out_anat.append(plate_cell["anatomy"])
                else:
                    if alpha < 0.5:
                        use_source = 0 if not is_bg_0 else 1
                    else:
                        use_source = 1 if not is_bg_1 else 0

                    if use_source == 0:
                        ch = r_rest_c["text"][x]
                        fg = r_rest_c["fg"][x][:]
                        bg = r_rest_c["bg"][x][:]
                        anat = anat_0
                    else:
                        ch = r_com_c["text"][x]
                        fg = r_com_c["fg"][x][:]
                        bg = r_com_c["bg"][x][:]
                        anat = anat_1

                    if not is_bg_0 and not is_bg_1:
                        fg0 = r_rest_c["fg"][x]
                        fg1 = r_com_c["fg"][x]
                        bg0 = r_rest_c["bg"][x]
                        bg1 = r_com_c["bg"][x]
                        fg = [
                            int(fg0[0] * (1 - alpha) + fg1[0] * alpha),
                            int(fg0[1] * (1 - alpha) + fg1[1] * alpha),
                            int(fg0[2] * (1 - alpha) + fg1[2] * alpha)
                        ]
                        bg = [
                            int(bg0[0] * (1 - alpha) + bg1[0] * alpha),
                            int(bg0[1] * (1 - alpha) + bg1[1] * alpha),
                            int(bg0[2] * (1 - alpha) + bg1[2] * alpha)
                        ]
                        ch = r_com_c["text"][x] if alpha > 0.5 else r_rest_c["text"][x]

                    r_out_txt.append(ch)
                    r_out_fg.append(fg)
                    r_out_bg.append(bg)
                    r_out_anat.append(anat)

            out["rows"].append({
                "text": "".join(r_out_txt),
                "fg": r_out_fg,
                "bg": r_out_bg,
                "anatomy": r_out_anat
            })

        hx, hy = hilt
        tx, ty = tip
        dx = tx - hx
        dy = ty - hy
        length = math.sqrt(dx**2 + dy**2)
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

        # 1. Pommel (Steel wheel - NO YELLOW)
        px = int(round(hx - ux * 4))
        py = int(round(hy - uy * 4))
        draw_line(out, px, py, px, py, "O", [215, 225, 235], [35, 42, 52], "weapon_sword", width=1)

        # 2. Grip (Dark wrapped steel/leather)
        draw_line(out, px, py, hx, hy, "#", [115, 120, 128], [24, 26, 30], "weapon_sword", width=1)

        # 3. Steel Gauntlets gripping the hilt (drawn FIRST so crossguard is on top, and in STEEL - NO YELLOW)
        draw_line(out, int(hx - 1), int(hy), int(hx + 1), int(hy + 1), "@", [185, 195, 205], [28, 32, 38], "arms_gauntlets", width=1)

        # 4. Polished Gothic Steel Crossguard (cruciform quillons perpendicular to blade - NO YELLOW)
        perp_x = -uy
        perp_y = ux
        gx1 = int(round(hx - perp_x * 3.5))
        gy1 = int(round(hy - perp_y * 3.5))
        gx2 = int(round(hx + perp_x * 3.5))
        gy2 = int(round(hy + perp_y * 3.5))
        # Draw quillons in gleaming steel matching stationary stance
        draw_line(out, gx1, gy1, gx2, gy2, "+", [232, 240, 250], [42, 50, 60], "weapon_sword", width=1)

        # 5. Razor-Sharp Blade Core & Cutting Edge
        draw_line(out, hx, hy, tx, ty, blade_ch, [255, 255, 255], [65, 80, 100], "weapon_sword", width=1)
        # Fuller bevel
        draw_line(out, int(round(hx + perp_x)), int(round(hy + perp_y)), int(round(tx + perp_x)), int(round(ty + perp_y)), blade_ch, [180, 200, 225], [38, 48, 62], "weapon_sword", width=1)

        return out

    # Generate the 3 transition stages
    frame_1 = build_trans_frame(0.25, (40, 48), (46, 82))
    frame_2 = build_trans_frame(0.50, (33, 53), (58, 52))
    frame_3 = build_trans_frame(0.75, (27, 56), (68, 26))

    data["standing_sentinel"] = m_rest
    data["combat_stance"] = m_combat
    data["trans_lift"] = frame_1
    data["trans_sweep"] = frame_2
    data["trans_ready"] = frame_3

    with open("assets/ascii/characters/knight_high_density.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    print("Updated knight_high_density.json with all precision fixes!")

    with open("assets/ascii/characters/knight_data.js", "w", encoding="utf-8") as f:
        f.write("window.KNIGHT_DATA = " + json.dumps(data) + ";\n")
    print("Updated knight_data.js with all precision fixes!")

if __name__ == "__main__":
    run_fix()
