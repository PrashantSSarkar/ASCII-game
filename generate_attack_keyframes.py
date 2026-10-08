import json
import math
import copy

with open("assets/ascii/characters/knight_high_density.json", "r", encoding="utf-8") as f:
    data = json.load(f)

m_rest = data["standing_sentinel"]
m_combat = data["combat_stance"]
w = 84
h = 116

# Extract clean background plate from m_rest
clean_wall_pool = []
for y in range(0, 50):
    r = m_rest["rows"][y]
    for x in range(w):
        if r["anatomy"][x] == "background":
            fg = r["fg"][x]
            bg = r["bg"][x]
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

# Clean sword-free combat body
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

def build_attack_frame(body_dx_upper, body_dy_upper, cape_dx, hilt, tip, add_slash_wave=False):
    out = {
        "width": w,
        "height": h,
        "rows": []
    }
    # Initialize with clean bg_plate
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

    # Stamp deformed combat body
    for y in range(h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat not in ("background", "ground_flagstone"):
                dx = 0
                dy = 0
                if anat in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets"):
                    dx = body_dx_upper
                    dy = body_dy_upper
                elif anat == "cape_mantle":
                    cape_w = max(0.0, (y - 18) / 90.0)
                    dx = int(round(cape_dx * cape_w))
                    dy = int(round(body_dy_upper * 0.7))
                elif anat in ("waist_fauld", "legs_greaves"):
                    leg_w = max(0.0, (108 - y) / 50.0)
                    dx = int(round(body_dx_upper * 0.5 * leg_w))
                    dy = int(round(body_dy_upper * 0.4 * leg_w))

                dst_x = x + dx
                dst_y = y + dy
                if 0 <= dst_x < w and 0 <= dst_y < h:
                    r_out = out["rows"][dst_y]
                    txt_list = list(r_out["text"])
                    txt_list[dst_x] = r_src["text"][x]
                    r_out["text"] = "".join(txt_list)
                    r_out["fg"][dst_x] = r_src["fg"][x][:]
                    r_out["bg"][dst_x] = r_src["bg"][x][:]
                    r_out["anatomy"][dst_x] = anat

    hx, hy = hilt
    tx, ty = tip
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

    # 1. Pommel (steel wheel O)
    px = int(round(hx - ux * 4))
    py = int(round(hy - uy * 4))
    draw_line(out, px, py, px, py, "O", [215, 225, 235], [35, 42, 52], "weapon_sword", width=1)

    # 2. Grip (# dark steel wire)
    draw_line(out, px, py, hx, hy, "#", [115, 120, 128], [24, 26, 30], "weapon_sword", width=1)

    # 3. Gauntlets (@ steel plate)
    draw_line(out, int(hx - 1), int(hy), int(hx + 1), int(hy + 1), "@", [190, 195, 200], [30, 32, 36], "arms_gauntlets", width=1)

    # 4. Quillons / Crossguard (perpendicular to blade)
    perp_x = -uy
    perp_y = ux
    gx1 = int(round(hx - perp_x * 3.5))
    gy1 = int(round(hy - perp_y * 3.5))
    gx2 = int(round(hx + perp_x * 3.5))
    gy2 = int(round(hy + perp_y * 3.5))
    draw_line(out, gx1, gy1, gx2, gy2, "+", [235, 242, 252], [42, 50, 60], "weapon_sword", width=1)

    # 5. Blade Core & Cutting Edge
    draw_line(out, hx, hy, tx, ty, blade_ch, [255, 255, 255], [65, 80, 100], "weapon_sword", width=1)
    # Fuller channel
    fx0 = int(round(hx + perp_x))
    fy0 = int(round(hy + perp_y))
    fx1 = int(round(tx + perp_x))
    fy1 = int(round(ty + perp_y))
    draw_line(out, fx0, fy0, fx1, fy1, blade_ch, [170, 192, 218], [36, 46, 60], "weapon_sword", width=1)

    # Tip apex glyph
    tip_ch = "^" if dy < -20 else (">" if dx > 20 else ("v" if dy > 20 else "*"))
    if 0 <= tx < w and 0 <= ty < h:
        r_tip = out["rows"][ty]
        t_txt = list(r_tip["text"])
        t_txt[tx] = tip_ch
        r_tip["text"] = "".join(t_txt)
        r_tip["fg"][tx] = [255, 255, 255]
        r_tip["bg"][tx] = [80, 100, 125]
        r_tip["anatomy"][tx] = "weapon_sword"

    # 6. Slash Wave Crescent (for peak slash)
    if add_slash_wave:
        arc_pts = [
            (int(tx - 8), int(ty - 14), "*", [255, 255, 255], [100, 130, 170]),
            (int(tx - 4), int(ty - 10), "/", [230, 245, 255], [80, 110, 150]),
            (int(tx), int(ty - 5), "/", [245, 250, 255], [90, 120, 160]),
            (int(tx + 2), int(ty), ">", [255, 255, 255], [110, 140, 180]),
            (int(tx + 1), int(ty + 5), ")", [230, 245, 255], [85, 115, 155]),
            (int(tx - 2), int(ty + 10), ")", [200, 230, 255], [70, 95, 135]),
            (int(tx - 8), int(ty + 14), "/", [170, 210, 250], [50, 75, 110]),
            (int(tx - 16), int(ty + 18), "-", [140, 185, 235], [35, 60, 90]),
            (int(tx - 26), int(ty + 20), "~", [110, 155, 210], [25, 45, 75]),
        ]
        for ax, ay, ach, afg, abg in arc_pts:
            if 0 <= ax < w and 0 <= ay < h:
                r_arc = out["rows"][ay]
                atxt = list(r_arc["text"])
                atxt[ax] = ach
                r_arc["text"] = "".join(atxt)
                r_arc["fg"][ax] = afg
                r_arc["bg"][ax] = abg
                r_arc["anatomy"][ax] = "weapon_sword"

    return out

# 1. attack_windup:
# Knight coils back: body_dx = -2, body_dy = +1, cape pulled back dx = -3
# Greatsword cocked high behind head: hilt at (18, 50), tip at (42, 6)
frame_windup = build_attack_frame(-2, 1, -3, (18, 50), (42, 6), add_slash_wave=False)

# 2. attack_slash:
# Forward cleave: body_dx = +3, body_dy = +2, cape flaring right dx = +8
# Greatsword sweeping horizontally: hilt at (24, 58), tip at (81, 38) with full crescent slash arc
frame_slash = build_attack_frame(3, 2, 8, (24, 58), (81, 38), add_slash_wave=True)

# 3. attack_recovery:
# Follow-through return: body_dx = +1, body_dy = +1, cape dx = +3
# Blade arcing upward on return path: hilt at (20, 58), tip at (66, 24)
frame_recovery = build_attack_frame(1, 1, 3, (20, 58), (66, 24), add_slash_wave=False)

data["attack_windup"] = frame_windup
data["attack_slash"] = frame_slash
data["attack_recovery"] = frame_recovery

with open("assets/ascii/characters/knight_high_density.json", "w", encoding="utf-8") as f:
    json.dump(data, f)
print("Updated attack keyframes in knight_high_density.json!")

with open("assets/ascii/characters/knight_data.js", "w", encoding="utf-8") as f:
    f.write("window.KNIGHT_DATA = " + json.dumps(data) + ";\n")
print("Updated attack keyframes in knight_data.js!")
