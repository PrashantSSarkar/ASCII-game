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

        # Gauntlet (one-handed grip)
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
        tip_ch = ">" if dx > 0 else "<"
        if 0 <= tx < w and 0 <= ty < h:
            r_tip = matrix["rows"][ty]
            if not (occlude_zones and r_tip["anatomy"][tx] in occlude_zones):
                t_txt = list(r_tip["text"])
                t_txt[tx] = tip_ch
                r_tip["text"] = "".join(t_txt)
                r_tip["fg"][tx] = [255, 255, 255]
                r_tip["bg"][tx] = [80, 100, 125]
                r_tip["anatomy"][tx] = "weapon_sword"

    # =========================================================================
    # Master Function: Render Horizontally Flapping Running Cape
    # =========================================================================
    def render_running_cape(matrix, wave_phase=0.0, intensity=1.0, attach_x=42, attach_y=28):
        """
        Renders the realistic tattered crimson mantle streaming horizontally
        behind the running knight to the left, matching the concept art reference.
        """
        # Cape streams horizontally leftward from shoulders: x from attach_x down to x ~ 6..10
        # Vertical thickness: y spans ~ 14 to 22 cells, undulating with high-speed flutter
        for cx in range(8, attach_x + 1):
            # Normalized length along the cape stream: 0.0 at far trailing left edge, 1.0 at shoulders
            u = (cx - 8) / float(max(1, attach_x - 8))
            
            # Centerline vertical undulation of the flapping cape
            flutter = math.sin((1.0 - u) * math.pi * 3.5 + wave_phase) * (4.5 * (1.0 - u * 0.4) * intensity)
            cy_center = attach_y + flutter + (1.0 - u) * 8.0  # slight droop toward the tail
            
            # Vertical thickness of the mantle: thicker near back (18 cells), tapering to frayed tail (8 cells)
            half_thick = 3.5 + 6.5 * math.pow(u, 0.7)
            
            # Ragged tail fraying
            if cx < 18:
                half_thick *= (cx - 7) / 11.0
                
            y_min = int(round(cy_center - half_thick))
            y_max = int(round(cy_center + half_thick))
            
            if y_min > y_max:
                continue
                
            for cy in range(y_min, y_max + 1):
                if not (0 <= cy < h and 0 <= cx < w):
                    continue
                    
                v = (cy - y_min) / float(max(1, y_max - y_min)) # 0.0 top edge to 1.0 bottom edge
                
                # Longitudinal fold ripples along the wind stream
                fold_phase = (1.0 - u) * math.pi * 4.0 + v * math.pi * 3.0 + wave_phase * 1.2
                elev = 0.75 * math.sin(fold_phase) + 0.25 * math.cos(u * math.pi * 6.0 + v * math.pi * 2.0)
                
                # Characters: authentic combat stance micro-weave
                if cy == y_min:
                    ch = "/" if flutter > 0 else "-"
                elif cy == y_max:
                    ch = "\\" if flutter > 0 else "-"
                elif elev > 0.82 and (cx + cy) % 3 == 0:
                    ch = "s"  # Highlighted fold ridge
                elif elev < -0.68:
                    ch = "|" if cx % 2 == 0 else "/"  # Crease shadow
                elif elev < -0.45 and cy % 2 == 0:
                    ch = "-"
                else:
                    ch = "%"  # Fine velvet cloth fiber
                    
                # Color shading matching combat_stance crimson
                lighting = 0.5 + 0.5 * elev
                r_col = int(98 + 84 * lighting)
                r_col = max(95, min(205, r_col))
                g_col = int(r_col * 0.20 + 2.0 * math.sin(cx * 0.5))
                b_col = int(r_col * 0.18 + 1.5 * math.cos(cy * 0.5))
                bg_col = [int(r_col * 0.17), int(g_col * 0.17), int(b_col * 0.17)]
                
                r_dst = matrix["rows"][cy]
                # Only overwrite background or existing cape (do not overwrite cuirass or head)
                if r_dst["anatomy"][cx] in ("background", "cape_mantle"):
                    txt = list(r_dst["text"])
                    txt[cx] = ch
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][cx] = [r_col, g_col, b_col]
                    r_dst["bg"][cx] = bg_col
                    r_dst["anatomy"][cx] = "cape_mantle"
                    
            # Add loose fluttering shreds trailing at the far left
            if cx in (8, 10, 12) and (cy_center + cx) % 3 == 0:
                shred_x = cx - 2
                shred_y = int(round(cy_center + math.sin(cx * 1.5) * 3.0))
                if 0 <= shred_y < h and 0 <= shred_x < w:
                    r_dst = matrix["rows"][shred_y]
                    if r_dst["anatomy"][shred_x] == "background":
                        txt = list(r_dst["text"])
                        txt[shred_x] = "%"
                        r_dst["text"] = "".join(txt)
                        r_dst["fg"][shred_x] = [105, 21, 19]
                        r_dst["bg"][shred_x] = [18, 4, 3]
                        r_dst["anatomy"][shred_x] = "cape_mantle"

    # =========================================================================
    # Master Function: Build Running Knight Frame
    # =========================================================================
    def build_running_frame(
        torso_dx, torso_dy,
        leg_l_phase,  # 'forward', 'passing_high', 'back_extended', 'under_hip'
        leg_r_phase,
        arm_l_dx, arm_l_dy,
        sword_angle_deg,
        cape_phase,
        skid_dust=False
    ):
        """
        Synthesizes a complete running keyframe with authentic Gothic steel plate armor,
        athletic forward-leaning kinematics, one-handed sword carry, and flapping cape.
        """
        mat = empty_matrix()
        
        # 1. Torso, Head, Pauldrons (facing right with forward athletic sprint lean)
        for y in range(h):
            r_src = m_combat_clean["rows"][y]
            for x in range(w):
                anat = r_src["anatomy"][x]
                if anat in ("head_helm", "pauldrons", "torso_cuirass", "waist_fauld"):
                    # Forward lean increases with height: head leans further forward than waist
                    lean_x = torso_dx + int(round(max(0.0, (54 - y) / 28.0) * 3.0))
                    lean_y = torso_dy
                    tx = x + lean_x
                    ty = y + lean_y
                    if 0 <= tx < w and 0 <= ty < h:
                        r_dst = mat["rows"][ty]
                        txt = list(r_dst["text"])
                        txt[tx] = r_src["text"][x]
                        r_dst["text"] = "".join(txt)
                        r_dst["fg"][tx] = r_src["fg"][x][:]
                        r_dst["bg"][tx] = r_src["bg"][x][:]
                        r_dst["anatomy"][tx] = anat

        # 2. Render Horizontally Flapping Cape behind shoulders/back
        cape_attach_x = 42 + torso_dx
        cape_attach_y = 28 + torso_dy
        render_running_cape(mat, wave_phase=cape_phase, intensity=1.0, attach_x=cape_attach_x, attach_y=cape_attach_y)

        # 3. Left Arm (Lead Pumping Gauntlet)
        # Left arm pumps forward or backward based on running cycle
        lax = 48 + torso_dx + arm_l_dx
        lay = 42 + torso_dy + arm_l_dy
        draw_line(mat, 44 + torso_dx, 36 + torso_dy, lax, lay, "@", [180, 190, 200], [30, 34, 40], "arms_gauntlets", width=1)
        # Fist gauntlet
        draw_line(mat, lax, lay, lax + 2, lay, "O", [210, 220, 230], [35, 40, 48], "arms_gauntlets", width=1)

        # 4. Right Arm & Greatsword in One Hand (Low Forward Flank Carry)
        # Right gauntlet at waist flank
        rhx = 46 + torso_dx
        rhy = 48 + torso_dy
        draw_line(mat, 42 + torso_dx, 38 + torso_dy, rhx, rhy, "@", [175, 185, 195], [30, 32, 38], "arms_gauntlets", width=1)
        
        # Greatsword blade extends low along flank (length ~ 34 cells)
        sword_rad = math.radians(sword_angle_deg)
        stx = int(round(rhx + math.cos(sword_rad) * 34.0))
        sty = int(round(rhy + math.sin(sword_rad) * 34.0))
        render_greatsword(mat, rhx, rhy, stx, sty, add_wave=False, blade_glow=False)

        # 5. Leg Kinematics (Right & Left Legs across Stride Phases)
        # We sample authentic greaves & sabatons from m_combat_clean
        def render_leg(is_right, phase):
            donor_min_x = 42 if is_right else 10
            donor_max_x = 80 if is_right else 42
            
            for y in range(54, h):
                r_src = m_combat_clean["rows"][y]
                for x in range(donor_min_x, donor_max_x):
                    anat = r_src["anatomy"][x]
                    if anat in ("legs_greaves", "feet_sabatons"):
                        # Base leg offset from stance
                        if is_right:
                            rx = x - 58
                        else:
                            rx = x - 26
                        ry = y - 54
                        
                        # Apply stride transformation based on phase
                        if phase == "forward_contact":
                            # Leg extended forward striking ground
                            dx = rx + 16 + torso_dx
                            dy = ry + torso_dy
                        elif phase == "passing_high":
                            # Knee driven high in the air under torso, foot tucked up (airborne)
                            progress_y = ry / 54.0
                            dx = rx + int(round(progress_y * -8.0)) + torso_dx
                            dy = int(round(ry * 0.76)) - 10 + torso_dy  # lifted 10 cells off stone!
                        elif phase == "back_extended":
                            # Leg trailing back in push-off extension
                            progress_y = ry / 54.0
                            dx = rx - 18 - int(round(progress_y * 10.0)) + torso_dx
                            dy = ry - 2 + torso_dy
                        elif phase == "under_hip":
                            # Leg bearing full weight directly under hip
                            dx = rx + 2 + torso_dx
                            dy = ry + torso_dy
                        elif phase == "skid_brake":
                            # Both feet dug in forward with knees bent in braking crouch
                            dx = rx + (12 if is_right else 4) + torso_dx
                            dy = ry + 2 + torso_dy
                        else:
                            dx = rx + torso_dx
                            dy = ry + torso_dy
                            
                        dst_x = 42 + dx
                        dst_y = 54 + dy
                        if 0 <= dst_x < w and 0 <= dst_y < h:
                            # Sabatons should not penetrate floor (y >= 110)
                            if anat == "feet_sabatons" and dst_y > 109:
                                dst_y = 109
                            r_dst = mat["rows"][dst_y]
                            txt = list(r_dst["text"])
                            txt[dst_x] = r_src["text"][x]
                            r_dst["text"] = "".join(txt)
                            r_dst["fg"][dst_x] = r_src["fg"][x][:]
                            r_dst["bg"][dst_x] = r_src["bg"][x][:]
                            r_dst["anatomy"][dst_x] = anat

        render_leg(is_right=False, phase=leg_l_phase)
        render_leg(is_right=True, phase=leg_r_phase)

        # 6. Braking dust / stone sparks if skidding
        if skid_dust:
            for d_x, d_y, d_ch, d_fg in [
                (36, 107, ".", [190, 180, 160]),
                (38, 106, "*", [220, 205, 175]),
                (42, 107, "~", [170, 160, 140]),
                (58, 107, ".", [190, 180, 160]),
                (62, 106, "*", [225, 210, 180]),
                (66, 107, "-", [180, 170, 150])
            ]:
                if 0 <= d_x < w and 0 <= d_y < h:
                    r_d = mat["rows"][d_y]
                    t = list(r_d["text"])
                    t[d_x] = d_ch
                    r_d["text"] = "".join(t)
                    r_d["fg"][d_x] = d_fg
                    r_d["anatomy"][d_x] = "ground_flagstone"

        return mat

    # =========================================================================
    # BUILD KEYFRAMES
    # =========================================================================
    print("Building running animation keyframes...")

    # Frame 1: Transition Start from Attack Stance
    # Knight leans forward, shifts greatsword into one hand at right flank, right leg steps into drive
    m_run_start = build_running_frame(
        torso_dx=2, torso_dy=1,
        leg_l_phase="under_hip", leg_r_phase="forward_contact",
        arm_l_dx=-2, arm_l_dy=0,
        sword_angle_deg=18.0,
        cape_phase=0.5,
        skid_dust=False
    )

    # Frame 2: Core Stride 1 (Right Foot Lead Contact)
    # Right leg extended forward in contact, left leg trailing in push-off extension, cape streaming left
    m_run_stride_1 = build_running_frame(
        torso_dx=4, torso_dy=2,
        leg_l_phase="back_extended", leg_r_phase="forward_contact",
        arm_l_dx=-6, arm_l_dy=2,  # Left arm pumps back
        sword_angle_deg=32.0,      # Greatsword low forward flank carry
        cape_phase=1.8,
        skid_dust=False
    )

    # Frame 3: Core Stride 2 (Right Passing / Left Knee Drive)
    # Right leg pushing under hip, left knee driving forward through the air (airborne), torso rebounds
    m_run_stride_2 = build_running_frame(
        torso_dx=4, torso_dy=0,
        leg_l_phase="passing_high", leg_r_phase="under_hip",
        arm_l_dx=2, arm_l_dy=-2,  # Left arm pumping forward
        sword_angle_deg=28.0,
        cape_phase=3.2,
        skid_dust=False
    )

    # Frame 4: Core Stride 3 (Left Foot Lead Contact)
    # Left leg striking forward, right leg trailing back in extension, torso compression
    m_run_stride_3 = build_running_frame(
        torso_dx=4, torso_dy=2,
        leg_l_phase="forward_contact", leg_r_phase="back_extended",
        arm_l_dx=6, arm_l_dy=-4,  # Left arm fully forward
        sword_angle_deg=34.0,
        cape_phase=4.6,
        skid_dust=False
    )

    # Frame 5: Core Stride 4 (Left Passing / Right Knee Drive)
    # Left leg pushing under hip, right knee driving through the air (airborne), cape wave crest
    m_run_stride_4 = build_running_frame(
        torso_dx=4, torso_dy=0,
        leg_l_phase="under_hip", leg_r_phase="passing_high",
        arm_l_dx=-2, arm_l_dy=0,
        sword_angle_deg=30.0,
        cape_phase=6.0,
        skid_dust=False
    )

    # Frame 6: Braking Skid / Stop
    # Knight plants both feet into wide braking crouch, leans back against momentum, sparks & dust
    m_run_skid = build_running_frame(
        torso_dx=0, torso_dy=3,
        leg_l_phase="skid_brake", leg_r_phase="skid_brake",
        arm_l_dx=-4, arm_l_dy=4,
        sword_angle_deg=10.0,      # Sword elevates as deceleration begins
        cape_phase=1.2,
        skid_dust=True
    )

    # Frame 7: Recovery Return to Attack Stance
    # Knight straightens up, re-gripping greatsword with two hands into high guard
    m_run_recover = empty_matrix()
    for y in range(h):
        r_src = m_combat_clean["rows"][y]
        for x in range(w):
            anat = r_src["anatomy"][x]
            if anat not in ("background", "ground_flagstone"):
                tx = x + 1
                ty = y + 1
                if 0 <= tx < w and 0 <= ty < h:
                    r_dst = m_run_recover["rows"][ty]
                    txt = list(r_dst["text"])
                    txt[tx] = r_src["text"][x]
                    r_dst["text"] = "".join(txt)
                    r_dst["fg"][tx] = r_src["fg"][x][:]
                    r_dst["bg"][tx] = r_src["bg"][x][:]
                    r_dst["anatomy"][tx] = anat

    # Re-grip greatsword in two hands returning to attack guard
    render_greatsword(m_run_recover, 48, 48, 86, 20, add_wave=False, blade_glow=False)

    # =========================================================================
    # Store into json & js datasets
    # =========================================================================
    data["run_trans_start"] = m_run_start
    data["run_stride_1"] = m_run_stride_1
    data["run_stride_2"] = m_run_stride_2
    data["run_stride_3"] = m_run_stride_3
    data["run_stride_4"] = m_run_stride_4
    data["run_skid_stop"] = m_run_skid
    data["run_recover_stance"] = m_run_recover

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Updated knight_high_density.json with running keyframes!")

    js_path = "assets/ascii/characters/knight_data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("/* High-Density Micro-ASCII Knight Character Dataset (110x116) */\n")
        f.write("const HIGH_DENSITY_DATA = ")
        json.dump(data, f)
        f.write(";\n")
        if "module" in "":
            pass
        f.write("if (typeof module !== 'undefined' && module.exports) {\n")
        f.write("    module.exports = HIGH_DENSITY_DATA;\n")
        f.write("}\n")
    print("Updated knight_data.js with running keyframes!")

    # =========================================================================
    # Render PNG Snapshots of each frame (Consolas 8px font)
    # =========================================================================
    pygame.init()
    font = pygame.font.SysFont("consolas", 8)
    cw, ch = font.size("M")

    frame_keys = [
        ("combat_stance", "0_active_combat_stance", "Base: Active Attack Stance"),
        ("run_trans_start", "1_run_trans_start", "Phase 1: Sprint Initiation Lean"),
        ("run_stride_1", "2_run_stride_1", "Phase 2: Stride 1 (Right Contact)"),
        ("run_stride_2", "3_run_stride_2", "Phase 3: Stride 2 (Left Knee Drive)"),
        ("run_stride_3", "4_run_stride_3", "Phase 4: Stride 3 (Left Contact)"),
        ("run_stride_4", "5_run_stride_4", "Phase 5: Stride 4 (Right Knee Drive)"),
        ("run_skid_stop", "6_run_skid_stop", "Phase 6: Braking Skid & Halt"),
        ("run_recover_stance", "7_run_recover_stance", "Phase 7: Return to Active Stance"),
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
        out_p = os.path.join("assets", f"mockup_run_{fname}.png")
        img.save(out_p)
        rendered_images.append((fname, img))
        print(f"Rendered {out_p}")

    # =========================================================================
    # Generate Side-by-Side Running Progression Strip
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

    strip_path = os.path.join("assets", "knight_run_progression_strip.png")
    strip.save(strip_path)
    print(f"Saved running mockup strip to {strip_path}")

    # =========================================================================
    # Copy to Brain Artifacts Directory
    # =========================================================================
    artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"
    if os.path.isdir(artifact_dir):
        for fname, _ in rendered_images:
            shutil.copy2(os.path.join("assets", f"mockup_run_{fname}.png"), os.path.join(artifact_dir, f"mockup_run_{fname}.png"))
        shutil.copy2(strip_path, os.path.join(artifact_dir, "knight_run_progression_strip.png"))
        print("Copied all running mockup artifacts to brain directory!")

if __name__ == "__main__":
    main()
