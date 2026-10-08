import json
import copy
import math
import os
import shutil

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
from PIL import Image, ImageDraw

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

    # Helper: draw Bresenham line with optional occlude_zones
    def draw_line(matrix, x0, y0, x1, y1, ch, fg, bg, zone, width=1, occlude_zones=None):
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
                        if occlude_zones and r["anatomy"][px] in occlude_zones:
                            continue
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

    # Clean combat matrix with sword removed
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

    # Master Sword Drawing function with occlusion support
    def render_greatsword(matrix, hx, hy, tx, ty, add_wave=False, blade_glow=False, occlude_zones=None):
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
        draw_line(matrix, px, py, px, py, "O", [215, 225, 235], [35, 42, 52], "weapon_sword", width=1, occlude_zones=occlude_zones)

        # Grip
        draw_line(matrix, px, py, hx, hy, "#", [115, 120, 128], [24, 26, 30], "weapon_sword", width=1, occlude_zones=occlude_zones)

        # Gauntlets
        draw_line(matrix, int(hx - 1), int(hy), int(hx + 1), int(hy + 1), "@", [190, 195, 200], [30, 32, 36], "arms_gauntlets", width=1, occlude_zones=occlude_zones)

        # Crossguard
        perp_x = -uy
        perp_y = ux
        gx1 = int(round(hx - perp_x * 4.0))
        gy1 = int(round(hy - perp_y * 4.0))
        gx2 = int(round(hx + perp_x * 4.0))
        gy2 = int(round(hy + perp_y * 4.0))
        draw_line(matrix, gx1, gy1, gx2, gy2, "+", [235, 242, 252], [42, 50, 60], "weapon_sword", width=1, occlude_zones=occlude_zones)

        # Blade Core
        core_fg = [255, 255, 255] if not blade_glow else [255, 245, 220]
        core_bg = [65, 80, 100] if not blade_glow else [85, 75, 40]
        draw_line(matrix, hx, hy, tx, ty, blade_ch, core_fg, core_bg, "weapon_sword", width=1, occlude_zones=occlude_zones)

        # Fuller channel
        fx0 = int(round(hx + perp_x))
        fy0 = int(round(hy + perp_y))
        fx1 = int(round(tx + perp_x))
        fy1 = int(round(ty + perp_y))
        draw_line(matrix, fx0, fy0, fx1, fy1, blade_ch, [170, 192, 218], [36, 46, 60], "weapon_sword", width=1, occlude_zones=occlude_zones)

        # Tip apex
        tip_ch = "^" if dy < -20 else (">" if dx > 20 else ("v" if dy > 20 else "*"))
        if 0 <= tx < w and 0 <= ty < h:
            r_tip = matrix["rows"][ty]
            if not (occlude_zones and r_tip["anatomy"][tx] in occlude_zones):
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
                    if occlude_zones and r_arc["anatomy"][ax] in occlude_zones:
                        continue
                    atxt = list(r_arc["text"])
                    atxt[ax] = ach
                    r_arc["text"] = "".join(atxt)
                    r_arc["fg"][ax] = afg
                    r_arc["bg"][ax] = abg
                    r_arc["anatomy"][ax] = "weapon_sword"
    # Action: The knight begins the heavy attack by taking a step with his
    #         RIGHT leg forward. His torso rotates 45 deg away from viewer,
    #         and he chambers the two-handed greatsword high & back over
    #         his left shoulder to gather maximum mechanical leverage.
    # =========================================================================
    m_step1_windup = empty_matrix()
    for y in range(h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat not in ("background", "ground_flagstone"):
                dx, dy = 0, 0
                if anat in ("head_helm", "pauldrons", "torso_cuirass"):
                    dx = -2
                    dy = 1
                elif anat == "arms_gauntlets":
                    dx = -4
                    dy = -2
                elif anat == "cape_mantle":
                    cape_pct = max(0.0, (y - 18) / 85.0)
                    dx = int(round(-4 - 8 * cape_pct))
                    dy = 1
                elif anat == "waist_fauld":
                    dx = -1
                    dy = 1
                elif anat in ("legs_greaves", "feet_sabatons"):
                    if x < 42:
                        dx = 0
                        dy = 0
                    else:
                        dx = -6  # Right leg stepping forward-across
                        dy = 1
                
                tx = x + dx
                ty = y + dy
                if 0 <= tx < w and 0 <= ty < h:
                    r_dst = m_step1_windup["rows"][ty]
                    txt = list(r_dst["text"])
                    txt[tx] = r_src["text"][x]
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][tx] = r_src["fg"][x][:]
                    r_dst["bg"][tx] = r_src["bg"][x][:]
                    r_dst["anatomy"][tx] = anat

    draw_line(m_step1_windup, 34, 42, 38, 38, "@", [170, 180, 190], [28, 32, 36], "arms_gauntlets", width=1)
    render_greatsword(m_step1_windup, 38, 38, 16, 12, add_wave=False)


    # =========================================================================
    # MOCKUP FRAME 2: heavy_step1_planted_front (Between Windup and Strike)
    # Action: The right foot has stepped forward across; the LEGS HAVE SWITCHED
    #         PLACES (right leg forward in lunge, left leg back in anchor).
    #         However, the TORSO HAS NOT TURNED YET, so front breastplate,
    #         visor, and arms face the viewer, and the CAPE IS NOT FACING THE
    #         VIEWER (it hangs on his back behind the torso).
    #         The two-handed greatsword is driving forward across the chest.
    # =========================================================================
    m_step1_planted_front = empty_matrix()

    # 1. Front-facing Upper Body from m_combat_clean (cape hangs behind):
    for y in range(h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat in ("head_helm", "pauldrons", "torso_cuirass", "cape_mantle"):
                r_dst = m_step1_planted_front["rows"][y]
                txt = list(r_dst["text"])
                txt[x] = r_src["text"][x]
                r_dst["text"] = "".join(txt)
                r_dst["fg"][x] = r_src["fg"][x][:]
                r_dst["bg"][x] = r_src["bg"][x][:]
                r_dst["anatomy"][x] = anat

    # 2. Lower Body: THE 2 LEGS SWITCH POSITION WITH VERTICAL AXIS FLIP ON REAR LEG!
    MIRROR_CHARS = {'/': '\\', '\\': '/', '(': ')', ')': '(', '[': ']', ']': '[', '{': '}', '}': '{', '<': '>', '>': '<'}
    for y in range(54, h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat in ("legs_greaves", "feet_sabatons"):
                if x < 42:
                    nx = x + 44  # Left leg moves to forward lunge on the right
                    ny = y
                    if 0 <= nx < w and 0 <= ny < h:
                        r_dst = m_step1_planted_front["rows"][ny]
                        txt = list(r_dst["text"])
                        txt[nx] = r_src["text"][x]
                        r_dst["text"] = "".join(txt)
                        r_dst["fg"][nx] = r_src["fg"][x][:]
                        r_dst["bg"][nx] = r_src["bg"][x][:]
                        r_dst["anatomy"][nx] = anat
                else:
                    # Vertical axis flip on rear anchor leg on the left (Frame 3)
                    nx = 87 - x
                    ny = y
                    if 0 <= nx < w and 0 <= ny < h:
                        r_dst = m_step1_planted_front["rows"][ny]
                        txt = list(r_dst["text"])
                        ch = r_src["text"][x]
                        txt[nx] = MIRROR_CHARS.get(ch, ch)
                        r_dst["text"] = "".join(txt)
                        r_dst["fg"][nx] = r_src["fg"][x][:]
                        r_dst["bg"][nx] = r_src["bg"][x][:]
                        r_dst["anatomy"][nx] = anat
            elif anat == "waist_fauld":
                if x < 42:
                    nx = x + 20
                else:
                    nx = x - 14
                if 0 <= nx < w:
                    r_dst = m_step1_planted_front["rows"][y]
                    txt = list(r_dst["text"])
                    txt[nx] = r_src["text"][x]
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][nx] = r_src["fg"][x][:]
                    r_dst["bg"][nx] = r_src["bg"][x][:]
                    r_dst["anatomy"][nx] = anat

    # Arms & Greatsword driving forward across the chest:
    draw_line(m_step1_planted_front, 40, 44, 46, 42, "@", [185, 195, 205], [32, 36, 42], "arms_gauntlets", width=1)
    render_greatsword(m_step1_planted_front, 46, 42, 88, 32, add_wave=False, blade_glow=True)


    # =========================================================================
    # MOCKUP FRAME 3: heavy_step1_strike
    # Action: The right foot is firmly planted forward in a deep combat stride.
    #         The knight's BACK IS COMPLETELY TURNED TO THE VIEWER!
    #         He delivers a crushing forward strike, greatsword fully extended
    #         straight forward past his body out to x=106!
    # =========================================================================
    m_step1_strike = empty_matrix()

    # 1. Lower Body: THE 2 LEGS SWITCH POSITION!
    # In combat_stance, left leg is at x < 42, right leg is at x >= 42.
    # As the knight steps with his right foot and turns his back to the viewer:
    # - The left leg (which was on the left at x in [10, 38]) moves to the right forward lunge (x -> x + 44 => [54, 82])
    # - The right leg (which was on the right at x in [47, 78]) moves to the left rear anchor (x -> x - 38 => [9, 40])
    MIRROR_CHARS = {'/': '\\', '\\': '/', '(': ')', ')': '(', '[': ']', ']': '[', '{': '}', '}': '{', '<': '>', '>': '<'}

    for y in range(54, h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat in ("legs_greaves", "feet_sabatons"):
                if x < 42:
                    nx = x + 44  # Left leg moves to forward lunge on the right
                    ny = y
                    if 0 <= nx < w and 0 <= ny < h:
                        r_dst = m_step1_strike["rows"][ny]
                        txt = list(r_dst["text"])
                        txt[nx] = r_src["text"][x]
                        r_dst["text"] = "".join(txt)
                        r_dst["fg"][nx] = r_src["fg"][x][:]
                        r_dst["bg"][nx] = r_src["bg"][x][:]
                        r_dst["anatomy"][nx] = anat
                else:
                    # Horizontally flipped rear anchor leg on the left (Frames 4 & 5)
                    nx = 87 - x
                    ny = y
                    if 0 <= nx < w and 0 <= ny < h:
                        r_dst = m_step1_strike["rows"][ny]
                        txt = list(r_dst["text"])
                        ch = r_src["text"][x]
                        txt[nx] = MIRROR_CHARS.get(ch, ch)
                        r_dst["text"] = "".join(txt)
                        r_dst["fg"][nx] = r_src["fg"][x][:]
                        r_dst["bg"][nx] = r_src["bg"][x][:]
                        r_dst["anatomy"][nx] = anat
            elif anat == "waist_fauld":
                # Fauld and maille skirt bridge across the hips connecting the swapped legs
                if x < 42:
                    nx = x + 20
                else:
                    nx = x - 14
                ny = y
                if 0 <= nx < w and 0 <= ny < h:
                    r_dst = m_step1_strike["rows"][ny]
                    txt = list(r_dst["text"])
                    txt[nx] = r_src["text"][x]
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][nx] = r_src["fg"][x][:]
                    r_dst["bg"][nx] = r_src["bg"][x][:]
                    r_dst["anatomy"][nx] = anat

    # 2. DORSAL HELMET WITH 100% COMBAT STANCE COLOR SHADING & SHAPE (NO RED PLUME)
    # Shape is exact sallet skull dome (x in [34, 48], y in [12, 27]) centered at cx=41.
    # Colors and micro-textures sampled directly from combat_stance["rows"][y].
    cx_head = 41
    for y in range(12, 28):
        r_comb = m_combat_clean["rows"][y]
        helm_xs = [x for x in range(w) if r_comb["anatomy"][x] == "head_helm"]
        if not helm_xs:
            continue
        min_hx, max_hx = min(helm_xs), max(helm_xs)
        
        r_dst = m_step1_strike["rows"][y]
        txt = list(r_dst["text"])
        for x in range(34, 49):
            dist = abs(x - cx_head)
            sample_x = min_hx + dist if (min_hx + dist) <= max_hx else max_hx
            
            # Exact color shading from combat stance
            fg = r_comb["fg"][sample_x][:]
            bg = r_comb["bg"][sample_x][:]
            
            # Micro-texture for dorsal Gothic sallet / close-helm
            if dist == 0:
                ch = "|" if y % 2 == 0 else "#"
            elif dist == 1:
                ch = "|" if y % 3 != 0 else "/"
            elif dist <= 3:
                ch = "/" if x < cx_head else "\\"
            elif dist <= 5:
                ch = "-" if y % 2 == 0 else ":"
            elif dist == 6:
                ch = "\\" if x < cx_head else "/"
            else:
                ch = "(" if x < cx_head else ")"
                
            txt[x] = ch
            r_dst["fg"][x] = fg
            r_dst["bg"][x] = bg
            r_dst["anatomy"][x] = "head_helm"
        r_dst["text"] = "".join(txt)

    # 3. DORSAL PAULDRONS & BACKPLATE WITH 100% COMBAT STANCE COLOR SHADING
    # Samples actual Gothic plate colors and micro-textures from combat_stance["rows"][y].
    for y in range(24, 55):
        r_comb = m_combat_clean["rows"][y]
        p_xs = [x for x in range(w) if r_comb["anatomy"][x] in ("pauldrons", "torso_cuirass")]
        if not p_xs:
            continue
        sample_fg = r_comb["fg"][p_xs[len(p_xs)//2]][:]
        sample_bg = r_comb["bg"][p_xs[len(p_xs)//2]][:]
        
        r_dst = m_step1_strike["rows"][y]
        txt = list(r_dst["text"])
        
        # Left shoulder pauldron: x in [26, 37]
        for px in range(26, 38):
            dist_p = abs(px - 32)
            txt[px] = "(" if px == 26 else ("/" if dist_p < 4 else "=")
            r_dst["fg"][px] = sample_fg[:]
            r_dst["bg"][px] = sample_bg[:]
            r_dst["anatomy"][px] = "pauldrons"
            
        # Right shoulder pauldron: x in [48, 62]
        for px in range(48, 63):
            dist_p = abs(px - 55)
            txt[px] = ")" if px == 62 else ("\\" if dist_p < 4 else "=")
            r_dst["fg"][px] = sample_fg[:]
            r_dst["bg"][px] = sample_bg[:]
            r_dst["anatomy"][px] = "pauldrons"
            
        # Cuirass backplate: x in [37, 49]
        if y >= 26:
            for bx in range(37, 49):
                dist_b = abs(bx - cx_head)
                if dist_b == 0:
                    txt[bx] = "|" if y % 2 == 0 else "!"
                elif dist_b <= 2:
                    txt[bx] = "=" if y % 3 == 0 else "/"
                else:
                    txt[bx] = ":" if y % 2 == 0 else "-"
                r_dst["fg"][bx] = sample_fg[:]
                r_dst["bg"][bx] = sample_bg[:]
                r_dst["anatomy"][bx] = "torso_cuirass"
                
        r_dst["text"] = "".join(txt)

    # Cape draped across back, trailing naturally to the left with the lunge
    # Kept strictly within dorsal/back silhouette (x in [24, 58]) so the forward right arm and sword are completely clear!
    for y in range(24, 98):
        y_rel = (y - 24) / 74.0
        # Left edge trails to the left behind the forward lunge
        c_left = int(32 - 9.0 * math.sin(y_rel * math.pi * 0.75))
        # Right edge stays cleanly at the torso flank (leaving x >= 59 completely unobstructed)
        c_right = int(58 - 2.5 * math.sin(y_rel * math.pi * 0.9))
        
        # Bottom tattered hem taper
        if y > 91:
            c_left += int((y - 91) * 1.8)
            c_right -= int((y - 91) * 1.5)

        if c_left > c_right:
            continue

        for cx in range(c_left, c_right + 1):
            if 28 <= y <= 38 and (cx_head - 1) <= cx <= (cx_head + 1):
                continue

            r_dst = m_step1_strike["rows"][y]
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
            r_col = int(145 * fold_shading + 65)
            g_col = int(22 * fold_shading + 10)
            b_col = int(26 * fold_shading + 12)
            
            txt[cx] = ch
            r_dst["text"] = "".join(txt)
            r_dst["fg"][cx] = [r_col, g_col, b_col]
            r_dst["bg"][cx] = [int(r_col * 0.28), int(g_col * 0.28), int(b_col * 0.28)]
            r_dst["anatomy"][cx] = "cape_mantle"

    # Right arm driving forward into the strike from the right shoulder:
    draw_line(m_step1_strike, 56, 38, 64, 42, "@", [175, 185, 195], [32, 35, 42], "arms_gauntlets", width=1, occlude_zones=("cape_mantle",))
    draw_line(m_step1_strike, 64, 42, 66, 44, "@", [190, 200, 210], [35, 38, 46], "arms_gauntlets", width=1, occlude_zones=("cape_mantle",))

    # Extended Forward Greatsword Strike:
    # Hilt at (66, 44), blade driving straight forward across the screen to maximum reach x=109!
    # Any part occluded by the dorsal cape or body is strictly clipped so the sword NEVER sticks through the cape.
    render_greatsword(m_step1_strike, 66, 44, 109, 44, add_wave=True, blade_glow=True, occlude_zones=("cape_mantle", "torso_cuirass", "head_helm"))


    # =========================================================================
    # MOCKUP FRAME 3: heavy_step1_followthrough
    # Action: The heavy strike has fully connected. Both arms are fully extended
    #         forward-downward, the weight of the massive blade pulling forward.
    #         Back is still turned to the viewer, right leg deeply planted forward.
    #         Cape stays on back, sword extends forward-downward to x=109.
    # =========================================================================
    m_step1_followthrough = copy.deepcopy(m_step1_strike)
    for y in range(h):
        r = m_step1_followthrough["rows"][y]
        txt = list(r["text"])
        for x in range(w):
            if r["anatomy"][x] == "weapon_sword":
                plate = bg_plate[y][x]
                txt[x] = plate["text"]
                r["fg"][x] = plate["fg"][:]
                r["bg"][x] = plate["bg"][:]
                r["anatomy"][x] = plate["anatomy"]
        r["text"] = "".join(txt)

    # Follow-through arms extended forward-downward:
    draw_line(m_step1_followthrough, 58, 42, 66, 46, "@", [170, 180, 190], [30, 34, 40], "arms_gauntlets", width=1, occlude_zones=("cape_mantle",))
    draw_line(m_step1_followthrough, 66, 46, 68, 48, "@", [185, 195, 205], [34, 38, 44], "arms_gauntlets", width=1, occlude_zones=("cape_mantle",))

    # Follow-through blade extending forward-downward to maximum reach x=109:
    render_greatsword(m_step1_followthrough, 68, 48, 109, 53, add_wave=False, blade_glow=False, occlude_zones=("cape_mantle", "torso_cuirass", "head_helm"))


    # =========================================================================
    # MOCKUP FRAME 5: heavy_step2_unwind_front (Second-to-Last Recovery Frame)
    # Action: Following the follow-through, the knight's TORSO UNWINDS BACK
    #         FACING THE VIEWER (breastplate, visor, and front armor visible;
    #         cape hangs behind on his back, NOT facing the viewer).
    #         The legs are still in the SWITCHED STEP (right leg forward,
    #         left leg back). The greatsword is decelerating upward into a
    #         high center defensive guard before the left leg steps back.
    # =========================================================================
    m_step2_unwind_front = empty_matrix()

    # 1. Front-facing Upper Body from m_combat_clean (cape hangs behind):
    for y in range(h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat in ("head_helm", "pauldrons", "torso_cuirass", "cape_mantle"):
                r_dst = m_step2_unwind_front["rows"][y]
                txt = list(r_dst["text"])
                txt[x] = r_src["text"][x]
                r_dst["text"] = "".join(txt)
                r_dst["fg"][x] = r_src["fg"][x][:]
                r_dst["bg"][x] = r_src["bg"][x][:]
                r_dst["anatomy"][x] = anat

    # 2. Lower Body: LEGS STILL IN SWITCHED STEP WITH VERTICAL AXIS FLIP ON REAR LEG
    for y in range(54, h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat in ("legs_greaves", "feet_sabatons"):
                if x < 42:
                    nx = x + 44  # Left leg in forward lunge on the right
                    ny = y
                    if 0 <= nx < w and 0 <= ny < h:
                        r_dst = m_step2_unwind_front["rows"][ny]
                        txt = list(r_dst["text"])
                        txt[nx] = r_src["text"][x]
                        r_dst["text"] = "".join(txt)
                        r_dst["fg"][nx] = r_src["fg"][x][:]
                        r_dst["bg"][nx] = r_src["bg"][x][:]
                        r_dst["anatomy"][nx] = anat
                else:
                    # Vertical axis flip on rear anchor leg on the left (Frame 6)
                    nx = 87 - x
                    ny = y
                    if 0 <= nx < w and 0 <= ny < h:
                        r_dst = m_step2_unwind_front["rows"][ny]
                        txt = list(r_dst["text"])
                        ch = r_src["text"][x]
                        txt[nx] = MIRROR_CHARS.get(ch, ch)
                        r_dst["text"] = "".join(txt)
                        r_dst["fg"][nx] = r_src["fg"][x][:]
                        r_dst["bg"][nx] = r_src["bg"][x][:]
                        r_dst["anatomy"][nx] = anat
            elif anat == "waist_fauld":
                if x < 42:
                    nx = x + 20
                else:
                    nx = x - 14
                if 0 <= nx < w:
                    r_dst = m_step2_unwind_front["rows"][y]
                    txt = list(r_dst["text"])
                    txt[nx] = r_src["text"][x]
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][nx] = r_src["fg"][x][:]
                    r_dst["bg"][nx] = r_src["bg"][x][:]
                    r_dst["anatomy"][nx] = anat

    # Arms & Greatsword rising to high defensive center guard:
    draw_line(m_step2_unwind_front, 42, 46, 48, 44, "@", [180, 190, 200], [30, 34, 40], "arms_gauntlets", width=1)
    render_greatsword(m_step2_unwind_front, 48, 44, 86, 20, add_wave=False, blade_glow=False)


    # =========================================================================
    # MOCKUP FRAME 6: heavy_step2_return (Final Recovery Step to Neutral)
    # Action: The knight steps with his LEFT foot forward around to return to
    #         combat stance. His body settles squarely back into base stance.
    # =========================================================================
    m_step2_return = empty_matrix()
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
                    dx = 4
                    dy = 0
                elif anat == "cape_mantle":
                    cape_pct = max(0.0, (y - 20) / 85.0)
                    dx = int(round(3 + 8 * cape_pct))
                    dy = 1
                elif anat == "waist_fauld":
                    dx = 3
                    dy = 1
                elif anat in ("legs_greaves", "feet_sabatons"):
                    if x < 42:
                        dx = 8   # Left leg stepping forward around to re-align stance
                        dy = 0
                    else:
                        dx = 2   # Right foot planted
                        dy = 1
                
                tx = x + dx
                ty = y + dy
                if 0 <= tx < w and 0 <= ty < h:
                    r_dst = m_step2_return["rows"][ty]
                    txt = list(r_dst["text"])
                    txt[tx] = r_src["text"][x]
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][tx] = r_src["fg"][x][:]
                    r_dst["bg"][tx] = r_src["bg"][x][:]
                    r_dst["anatomy"][tx] = anat

    draw_line(m_step2_return, 40, 46, 48, 48, "@", [160, 170, 180], [28, 30, 34], "arms_gauntlets", width=1)
    render_greatsword(m_step2_return, 48, 48, 86, 20, add_wave=False)


    # =========================================================================
    # Store into json & js datasets
    # =========================================================================
    data["heavy_step1_windup"] = m_step1_windup
    data["heavy_step1_planted_front"] = m_step1_planted_front
    data["heavy_step1_strike"] = m_step1_strike
    data["heavy_step1_followthrough"] = m_step1_followthrough
    data["heavy_step2_unwind_front"] = m_step2_unwind_front
    data["heavy_step2_return"] = m_step2_return

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Updated knight_high_density.json with heavy attack keyframe mockups!")

    js_path = "assets/ascii/characters/knight_data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("/* High-Density Micro-ASCII Knight Character Dataset (110x116) */\n")
        f.write("const HIGH_DENSITY_DATA = ")
        json.dump(data, f)
        f.write(";\n")
        f.write("if (typeof module !== 'undefined' && module.exports) {\n")
        f.write("    module.exports = HIGH_DENSITY_DATA;\n")
        f.write("}\n")
    print("Updated knight_data.js with heavy attack keyframe mockups!")

    # =========================================================================
    # Render PNG Snapshots of each frame (Consolas 8px font)
    # =========================================================================
    pygame.init()
    font = pygame.font.SysFont("consolas", 8)
    cw, ch = font.size("M")

    frame_keys = [
        ("combat_stance", "0_combat_stance_guard", "Base: Combat Stance"),
        ("heavy_step1_windup", "1_heavy_step1_windup", "Step 1: Right Leg Chamber"),
        ("heavy_step1_planted_front", "2_heavy_step1_planted_front", "Step 1: Planted Stride (Torso Front)"),
        ("heavy_step1_strike", "3_heavy_step1_strike", "Step 1 Strike: Back-Turned Cut"),
        ("heavy_step1_followthrough", "4_heavy_step1_followthrough", "Step 1 Follow-Through: Impact Hold"),
        ("heavy_step2_unwind_front", "5_heavy_step2_unwind_front", "Step 2: Torso Unwind (Second to Last)"),
        ("heavy_step2_return", "6_heavy_step2_return", "Step 2 Return: Left Leg Step & Return"),
    ]

    rendered_images = []
    for k, fname, _ in frame_keys:
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
        out_p = os.path.join("assets", f"mockup_{fname}.png")
        img.save(out_p)
        rendered_images.append((fname, img))
        print(f"Rendered {out_p}")

    # =========================================================================
    # Generate Side-by-Side Progression Strip
    # =========================================================================
    sw, sh = rendered_images[0][1].size
    pad = 12
    header_h = 36
    total_w = len(rendered_images) * sw + (len(rendered_images) + 1) * pad
    total_h = sh + pad * 2 + header_h

    strip = Image.new("RGB", (total_w, total_h), (14, 16, 22))
    draw = ImageDraw.Draw(strip)

    titles = [t for _, _, t in frame_keys]

    for i, ((fname, img), title) in enumerate(zip(rendered_images, titles)):
        x_pos = pad + i * (sw + pad)
        y_pos = pad + header_h
        strip.paste(img, (x_pos, y_pos))
        draw.rectangle([x_pos, pad, x_pos + sw, pad + header_h - 4], fill=(24, 28, 38), outline=(60, 70, 90))
        draw.text((x_pos + 8, pad + 10), title, fill=(240, 245, 255))

    strip_path = os.path.join("assets", "knight_heavy_attack_mockup_strip.png")
    strip.save(strip_path)
    print(f"Saved heavy attack mockup strip to {strip_path}")

    # =========================================================================
    # Copy to Brain Artifacts Directory
    # =========================================================================
    artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"
    if os.path.isdir(artifact_dir):
        for fname, _ in rendered_images:
            shutil.copy2(os.path.join("assets", f"mockup_{fname}.png"), os.path.join(artifact_dir, f"mockup_{fname}.png"))
        shutil.copy2(strip_path, os.path.join(artifact_dir, "knight_heavy_attack_mockup_strip.png"))
        print("Copied all heavy attack mockup artifacts to brain directory!")

if __name__ == "__main__":
    main()
