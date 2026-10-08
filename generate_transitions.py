"""
⚔️ Clean Inpainting and Transition Generator
Removes ghost sword traces and generates pristine intermediate keyframes.
"""

import json
import math
import copy

def load_data():
    with open("assets/ascii/characters/knight_high_density.json", "r", encoding="utf-8") as f:
        return json.load(f)

def clean_matrix_without_sword(matrix, stance_type):
    """
    Returns a copy of the matrix with the sword completely infilled by surrounding context.
    """
    m = copy.deepcopy(matrix)
    w = m["width"]
    h = m["height"]
    
    if stance_type == "rest":
        # In rest stance, sword is vertical at x in [39..45], y in [45..105]
        for y in range(h):
            r = m["rows"][y]
            txt = list(r["text"])
            for x in range(w):
                if r["anatomy"][x] == "weapon_sword":
                    # Infill from left neighbor (x=38) or right neighbor (x=46)
                    # Prefer neighbor that is not background if available
                    cand_x = 37 if 37 >= 0 else 0
                    if cand_x < w and r["anatomy"][cand_x] != "weapon_sword":
                        donor_x = cand_x
                    else:
                        donor_x = 47 if 47 < w else cand_x
                        
                    txt[x] = r["text"][donor_x]
                    r["fg"][x] = r["fg"][donor_x][:]
                    r["bg"][x] = r["bg"][donor_x][:]
                    r["anatomy"][x] = r["anatomy"][donor_x]
            r["text"] = "".join(txt)
            
    elif stance_type == "combat":
        # In combat stance, sword is diagonal from (19, 60) to (74, 15)
        for y in range(h):
            r = m["rows"][y]
            txt = list(r["text"])
            for x in range(w):
                if r["anatomy"][x] == "weapon_sword":
                    # Infill from vertical neighbors (y-2 or y+2)
                    donor_y = y - 2 if y - 2 >= 0 and m["rows"][y - 2]["anatomy"][x] != "weapon_sword" else (y + 2 if y + 2 < h else y)
                    donor_row = m["rows"][donor_y]
                    donor_anat = donor_row["anatomy"][x]
                    
                    txt[x] = donor_row["text"][x]
                    r["fg"][x] = donor_row["fg"][x][:]
                    r["bg"][x] = donor_row["bg"][x][:]
                    r["anatomy"][x] = donor_anat
            r["text"] = "".join(txt)
            
    return m

def create_blank_matrix(w=84, h=116):
    rows = []
    for y in range(h):
        is_ground = (y >= 108)
        text_row = []
        fg_row = []
        bg_row = []
        anat_row = []
        for x in range(w):
            if is_ground:
                ch = "." if (x + y) % 4 == 0 else " "
                text_row.append(ch)
                fg_row.append([71, 85, 105])
                bg_row.append([24, 27, 34])
                anat_row.append("ground_flagstone")
            else:
                text_row.append(" ")
                fg_row.append([40, 45, 55])
                bg_row.append([10, 11, 14])
                anat_row.append("background")
        rows.append({
            "text": "".join(text_row),
            "fg": fg_row,
            "bg": bg_row,
            "anatomy": anat_row
        })
    return {"width": w, "height": h, "rows": rows}

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
                    r["fg"][px] = fg
                    r["bg"][px] = bg
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

def build_transition_frame(m_rest_clean, m_combat_clean, alpha, sword_hilt, sword_tip, stage_name):
    w = 84
    h = 116
    out = create_blank_matrix(w, h)
    
    # 1. Morph body & background between sword-free rest and combat bases
    for y in range(h):
        r_rest = m_rest_clean["rows"][y]
        r_com = m_combat_clean["rows"][y]
        r_out = out["rows"][y]
        
        txt_out = list(r_out["text"])
        
        for x in range(w):
            anat_0 = r_rest["anatomy"][x]
            anat_1 = r_com["anatomy"][x]
            
            # Dominant body segment based on alpha
            if alpha < 0.5:
                source_anat = anat_0 if anat_0 != "background" else anat_1
                use_source = 0 if anat_0 != "background" else 1
            else:
                source_anat = anat_1 if anat_1 != "background" else anat_0
                use_source = 1 if anat_1 != "background" else 0
                
            if use_source == 0:
                ch = r_rest["text"][x]
                fg = r_rest["fg"][x]
                bg = r_rest["bg"][x]
            else:
                ch = r_com["text"][x]
                fg = r_com["fg"][x]
                bg = r_com["bg"][x]
                
            # If both are foreground body elements, blend colors
            if anat_0 != "background" and anat_1 != "background":
                fg0 = r_rest["fg"][x]
                fg1 = r_com["fg"][x]
                bg0 = r_rest["bg"][x]
                bg1 = r_com["bg"][x]
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
                ch = r_com["text"][x] if alpha > 0.5 else r_rest["text"][x]
                
            txt_out[x] = ch
            r_out["fg"][x] = fg
            r_out["bg"][x] = bg
            r_out["anatomy"][x] = source_anat
            
        r_out["text"] = "".join(txt_out)
        
    # 2. Render dynamic greatsword
    hx, hy = sword_hilt
    tx, ty = sword_tip
    
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
        
    # Pommel (behind hilt)
    px = int(round(hx - ux * 4))
    py = int(round(hy - uy * 4))
    draw_line(out, px, py, px, py, "O", [212, 175, 55], [40, 30, 10], "weapon_sword", width=1)
    
    # Grip (from pommel to guard)
    draw_line(out, px, py, hx, hy, "#", [130, 85, 50], [35, 25, 18], "weapon_sword", width=1)
    
    # Crossguard (perpendicular to blade)
    perp_x = -uy
    perp_y = ux
    gx1 = int(round(hx - perp_x * 4))
    gy1 = int(round(hy - perp_y * 4))
    gx2 = int(round(hx + perp_x * 4))
    gy2 = int(round(hy + perp_y * 4))
    draw_line(out, gx1, gy1, gx2, gy2, "+", [235, 240, 248], [45, 52, 60], "weapon_sword", width=1)
    
    # Blade Core & Cutting Edges (from guard to tip)
    draw_line(out, hx, hy, tx, ty, blade_ch, [250, 252, 255], [60, 70, 85], "weapon_sword", width=1)
    # Give blade double thickness
    draw_line(out, int(round(hx + perp_x)), int(round(hy + perp_y)), int(round(tx + perp_x)), int(round(ty + perp_y)), blade_ch, [215, 228, 240], [45, 55, 68], "weapon_sword", width=1)
    
    # Hands / Gauntlets at hilt
    draw_line(out, int(hx - 1), int(hy), int(hx + 1), int(hy + 1), "@", [215, 160, 65], [55, 40, 18], "arms_gauntlets", width=1)

    return out

def generate_clean_transitions():
    data = load_data()
    m_rest = data["standing_sentinel"]
    m_combat = data["combat_stance"]
    
    m_rest_clean = clean_matrix_without_sword(m_rest, "rest")
    m_combat_clean = clean_matrix_without_sword(m_combat, "combat")
    
    # Phase 1: Lift Initiation (alpha = 0.25)
    hilt_1 = (40, 48)
    tip_1 = (46, 82)
    frame_1 = build_transition_frame(m_rest_clean, m_combat_clean, 0.25, hilt_1, tip_1, "trans_lift")
    
    # Phase 2: Mid-Torso Sweep (alpha = 0.50)
    hilt_2 = (33, 53)
    tip_2 = (58, 52)
    frame_2 = build_transition_frame(m_rest_clean, m_combat_clean, 0.50, hilt_2, tip_2, "trans_sweep")
    
    # Phase 3: High Guard Hoist (alpha = 0.75)
    hilt_3 = (27, 56)
    tip_3 = (68, 26)
    frame_3 = build_transition_frame(m_rest_clean, m_combat_clean, 0.75, hilt_3, tip_3, "trans_ready")
    
    data["trans_lift"] = frame_1
    data["trans_sweep"] = frame_2
    data["trans_ready"] = frame_3
    
    with open("assets/ascii/characters/knight_high_density.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    print("Saved clean transition frames to knight_high_density.json!")
    
    with open("assets/ascii/characters/knight_data.js", "w", encoding="utf-8") as f:
        f.write("window.KNIGHT_DATA = " + json.dumps(data) + ";\n")
    print("Saved clean transition frames to knight_data.js!")

if __name__ == "__main__":
    generate_clean_transitions()
