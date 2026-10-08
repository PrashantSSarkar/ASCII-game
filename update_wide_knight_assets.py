import json
import copy
import math
import os
import shutil
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
from PIL import Image

def main():
    with open("assets/ascii/characters/knight_high_density.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    m_rest = data["standing_sentinel"]
    m_combat = data["combat_stance"]

    old_w = 84
    new_w = 110
    h = 116

    # Extract clean donor background pools
    clean_wall_pool = []
    for y in range(0, 50):
        r = m_rest["rows"][y]
        for x in range(old_w):
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
        for x in range(old_w):
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

    # Build clean background plate of size (new_w, h)
    bg_plate = []
    for y in range(h):
        row = []
        r_rest = m_rest["rows"][y]
        for x in range(new_w):
            if x < old_w:
                anat = r_rest["anatomy"][x]
                fg = r_rest["fg"][x]
                bg = r_rest["bg"][x]
                if y >= 108:
                    if anat in ("ground_flagstone", "background") and sum(bg) >= 20:
                        row.append({
                            "text": r_rest["text"][x],
                            "fg": fg[:],
                            "bg": bg[:],
                            "anatomy": "ground_flagstone"
                        })
                    else:
                        donor = clean_ground_pool[(x * 7 + y * 13) % len(clean_ground_pool)]
                        row.append(copy.deepcopy(donor))
                else:
                    if anat == "background" and bg[0] >= 14 and bg[0] >= bg[2] and sum(bg) >= 30 and sum(fg) >= 200:
                        row.append({
                            "text": r_rest["text"][x],
                            "fg": fg[:],
                            "bg": bg[:],
                            "anatomy": "background"
                        })
                    else:
                        donor = clean_wall_pool[(x * 11 + y * 17) % len(clean_wall_pool)]
                        row.append(copy.deepcopy(donor))
            else:
                if y >= 108:
                    donor = clean_ground_pool[(x * 7 + y * 13) % len(clean_ground_pool)]
                    row.append(copy.deepcopy(donor))
                else:
                    donor = clean_wall_pool[(x * 11 + y * 17) % len(clean_wall_pool)]
                    row.append(copy.deepcopy(donor))
        bg_plate.append(row)

    def pad_matrix(src):
        out = {
            "width": new_w,
            "height": h,
            "rows": []
        }
        for y in range(h):
            r_src = src["rows"][y]
            txt = list(r_src["text"])
            fg = [c[:] for c in r_src["fg"]]
            bg = [c[:] for c in r_src["bg"]]
            anat = list(r_src["anatomy"])
            for x in range(old_w, new_w):
                plate = bg_plate[y][x]
                txt.append(plate["text"])
                fg.append(plate["fg"][:])
                bg.append(plate["bg"][:])
                anat.append(plate["anatomy"])
            out["rows"].append({
                "text": "".join(txt),
                "fg": fg,
                "bg": bg,
                "anatomy": anat
            })
        return out

    padded_rest = pad_matrix(m_rest)
    padded_combat = pad_matrix(m_combat)
    padded_trans_lift = pad_matrix(data["trans_lift"])
    padded_trans_sweep = pad_matrix(data["trans_sweep"])
    padded_trans_ready = pad_matrix(data["trans_ready"])

    # Clean sword-free combat body on width new_w
    m_combat_clean = copy.deepcopy(padded_combat)
    for y in range(h):
        r = m_combat_clean["rows"][y]
        txt = list(r["text"])
        for x in range(new_w):
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

    def build_attack_frame(stage):
        out = {
            "width": new_w,
            "height": h,
            "rows": []
        }
        for y in range(h):
            r_txt = [bg_plate[y][x]["text"] for x in range(new_w)]
            r_fg = [bg_plate[y][x]["fg"][:] for x in range(new_w)]
            r_bg = [bg_plate[y][x]["bg"][:] for x in range(new_w)]
            r_anat = [bg_plate[y][x]["anatomy"] for x in range(new_w)]
            out["rows"].append({
                "text": "".join(r_txt),
                "fg": r_fg,
                "bg": r_bg,
                "anatomy": r_anat
            })

        for y in range(h):
            r_src = m_combat_clean["rows"][y]
            for x in range(new_w):
                anat = r_src["anatomy"][x]
                if anat not in ("background", "ground_flagstone"):
                    dx = 0
                    dy = 0
                    
                    if stage == "windup":
                        if anat in ("head_helm", "pauldrons", "torso_cuirass"):
                            dx = -3
                            dy = 1
                        elif anat == "arms_gauntlets":
                            dx = -4
                            dy = -1
                        elif anat == "cape_mantle":
                            cape_pct = max(0.0, (y - 18) / 85.0)
                            dx = int(round(-3 - 3 * cape_pct))
                            dy = 1
                        elif anat == "waist_fauld":
                            dx = -2
                            dy = 1
                        elif anat in ("legs_greaves", "feet_sabatons"):
                            leg_fac = max(0.0, min(1.0, (x - 24) / 40.0))
                            dx = int(round(-1 - 2 * leg_fac))
                            dy = 0
                            
                    elif stage == "slash":
                        # ATHLETIC FORWARD LUNGE: Front leg drives forward, whole body shifts right
                        if anat in ("head_helm", "pauldrons", "torso_cuirass"):
                            dx = 10
                            dy = 2
                        elif anat == "arms_gauntlets":
                            dx = 13
                            dy = 2
                        elif anat == "cape_mantle":
                            cape_pct = max(0.0, (y - 18) / 85.0)
                            dx = int(round(10 + 6 * cape_pct))
                            dy = 2
                        elif anat == "waist_fauld":
                            dx = 8
                            dy = 2
                        elif anat in ("legs_greaves", "feet_sabatons"):
                            leg_fac = max(0.0, min(1.0, (x - 24) / 42.0))
                            dx = int(round(4 + 8 * leg_fac))
                            dy = int(round(1 + 1 * leg_fac))
                            
                    elif stage == "recovery":
                        if anat in ("head_helm", "pauldrons", "torso_cuirass"):
                            dx = 6
                            dy = 1
                        elif anat == "arms_gauntlets":
                            dx = 8
                            dy = 0
                        elif anat == "cape_mantle":
                            cape_pct = max(0.0, (y - 18) / 85.0)
                            dx = int(round(6 + 4 * cape_pct))
                            dy = 1
                        elif anat == "waist_fauld":
                            dx = 5
                            dy = 1
                        elif anat in ("legs_greaves", "feet_sabatons"):
                            leg_fac = max(0.0, min(1.0, (x - 24) / 42.0))
                            dx = int(round(3 + 4 * leg_fac))
                            dy = 1

                    dst_x = x + dx
                    dst_y = y + dy
                    if 0 <= dst_x < new_w and 0 <= dst_y < h:
                        r_out = out["rows"][dst_y]
                        txt_list = list(r_out["text"])
                        txt_list[dst_x] = r_src["text"][x]
                        r_out["text"] = "".join(txt_list)
                        r_out["fg"][dst_x] = r_src["fg"][x][:]
                        r_out["bg"][dst_x] = r_src["bg"][x][:]
                        r_out["anatomy"][dst_x] = anat

        # Draw Greatsword and connected Gauntlets
        if stage == "windup":
            hx, hy = (24, 48)
            tx, ty = (46, 4)
            add_slash_wave = False
            draw_line(out, 32, 44, 24, 48, "@", [160, 170, 180], [28, 30, 34], "arms_gauntlets", width=1)
            draw_line(out, 40, 46, 26, 48, "@", [150, 160, 170], [26, 28, 32], "arms_gauntlets", width=1)
            
        elif stage == "slash":
            # FULL EXTENSION: Hilt at (58, 54), Tip far to right at (106, 44)
            hx, hy = (58, 54)
            tx, ty = (106, 44)
            add_slash_wave = True
            draw_line(out, 46, 48, 58, 54, "@", [160, 170, 180], [26, 28, 32], "arms_gauntlets", width=1)
            draw_line(out, 54, 48, 59, 54, "@", [180, 190, 200], [30, 32, 36], "arms_gauntlets", width=1)
            
        elif stage == "recovery":
            hx, hy = (50, 50)
            tx, ty = (86, 16)
            add_slash_wave = False
            draw_line(out, 42, 46, 50, 50, "@", [160, 170, 180], [28, 30, 34], "arms_gauntlets", width=1)
            draw_line(out, 50, 46, 51, 50, "@", [180, 190, 200], [30, 32, 36], "arms_gauntlets", width=1)

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
        draw_line(out, px, py, px, py, "O", [215, 225, 235], [35, 42, 52], "weapon_sword", width=1)

        # Grip
        draw_line(out, px, py, hx, hy, "#", [115, 120, 128], [24, 26, 30], "weapon_sword", width=1)

        # Gauntlets
        draw_line(out, int(hx - 1), int(hy), int(hx + 1), int(hy + 1), "@", [190, 195, 200], [30, 32, 36], "arms_gauntlets", width=1)

        # Crossguard
        perp_x = -uy
        perp_y = ux
        gx1 = int(round(hx - perp_x * 4.0))
        gy1 = int(round(hy - perp_y * 4.0))
        gx2 = int(round(hx + perp_x * 4.0))
        gy2 = int(round(hy + perp_y * 4.0))
        draw_line(out, gx1, gy1, gx2, gy2, "+", [235, 242, 252], [42, 50, 60], "weapon_sword", width=1)

        # Blade Core
        draw_line(out, hx, hy, tx, ty, blade_ch, [255, 255, 255], [65, 80, 100], "weapon_sword", width=1)
        # Fuller channel
        fx0 = int(round(hx + perp_x))
        fy0 = int(round(hy + perp_y))
        fx1 = int(round(tx + perp_x))
        fy1 = int(round(ty + perp_y))
        draw_line(out, fx0, fy0, fx1, fy1, blade_ch, [170, 192, 218], [36, 46, 60], "weapon_sword", width=1)

        # Tip apex
        tip_ch = "^" if dy < -20 else (">" if dx > 20 else ("v" if dy > 20 else "*"))
        if 0 <= tx < new_w and 0 <= ty < h:
            r_tip = out["rows"][ty]
            t_txt = list(r_tip["text"])
            t_txt[tx] = tip_ch
            r_tip["text"] = "".join(t_txt)
            r_tip["fg"][tx] = [255, 255, 255]
            r_tip["bg"][tx] = [80, 100, 125]
            r_tip["anatomy"][tx] = "weapon_sword"

        # Crescent Slash Arc
        if add_slash_wave:
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
                if 0 <= ax < new_w and 0 <= ay < h:
                    r_arc = out["rows"][ay]
                    atxt = list(r_arc["text"])
                    atxt[ax] = ach
                    r_arc["text"] = "".join(atxt)
                    r_arc["fg"][ax] = afg
                    r_arc["bg"][ax] = abg
                    r_arc["anatomy"][ax] = "weapon_sword"

        return out

    frame_windup = build_attack_frame("windup")
    frame_slash = build_attack_frame("slash")
    frame_recovery = build_attack_frame("recovery")

    # Update dataset
    data["standing_sentinel"] = padded_rest
    data["combat_stance"] = padded_combat
    data["trans_lift"] = padded_trans_lift
    data["trans_sweep"] = padded_trans_sweep
    data["trans_ready"] = padded_trans_ready
    data["attack_windup"] = frame_windup
    data["attack_slash"] = frame_slash
    data["attack_recovery"] = frame_recovery

    with open("assets/ascii/characters/knight_high_density.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    print("Updated knight_high_density.json with wide frames (110x116)!")

    with open("assets/ascii/characters/knight_data.js", "w", encoding="utf-8") as f:
        f.write("window.KNIGHT_DATA = " + json.dumps(data) + ";\n")
    print("Updated knight_data.js with wide frames (110x116)!")

    # Render snapshot images
    pygame.init()
    font = pygame.font.SysFont("consolas", 8)
    char_w, char_h = font.size("M")
    pad_x = char_w * 4
    pad_y = char_h * 2

    def render_frame_to_image(matrix):
        sw = matrix["width"] * char_w + pad_x * 2
        sh = matrix["height"] * char_h + pad_y * 2
        surf = pygame.Surface((sw, sh))
        surf.fill((10, 11, 14))
        for y in range(matrix["height"]):
            row = matrix["rows"][y]
            for x in range(matrix["width"]):
                r, g, b = row["bg"][x]
                rect = pygame.Rect(pad_x + x * char_w, pad_y + y * char_h, char_w, char_h)
                surf.fill((r, g, b), rect)
        for y in range(matrix["height"]):
            row = matrix["rows"][y]
            for x, (ch, fg) in enumerate(zip(row["text"], row["fg"])):
                if ch == ' ': continue
                try:
                    gs = font.render(ch, False, fg)
                    surf.blit(gs, (pad_x + x * char_w, pad_y + y * char_h))
                except:
                    pass
        raw = pygame.image.tobytes(surf, "RGB")
        return Image.frombytes("RGB", (sw, sh), raw)

    img_rest = render_frame_to_image(padded_rest)
    img_combat = render_frame_to_image(padded_combat)
    img_windup = render_frame_to_image(frame_windup)
    img_slash = render_frame_to_image(frame_slash)
    img_recovery = render_frame_to_image(frame_recovery)

    img_rest.save("assets/knight_rest_stance_8px.png")
    img_combat.save("assets/knight_combat_stance_8px.png")
    img_windup.save("assets/knight_attack_windup_8px.png")
    img_slash.save("assets/knight_attack_slash_8px.png")
    img_recovery.save("assets/knight_attack_recovery_8px.png")

    w_p, h_p = img_rest.size
    strip = Image.new("RGB", (w_p * 5, h_p), (10, 11, 14))
    strip.paste(img_rest, (0, 0))
    strip.paste(img_windup, (w_p, 0))
    strip.paste(img_slash, (w_p * 2, 0))
    strip.paste(img_recovery, (w_p * 3, 0))
    strip.paste(img_combat, (w_p * 4, 0))
    strip.save("assets/knight_attack_progression_strip.png")
    print("Saved knight_attack_progression_strip.png!")

    # Copy to artifacts directory
    artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"
    for fn in [
        "knight_rest_stance_8px.png",
        "knight_combat_stance_8px.png",
        "knight_attack_windup_8px.png",
        "knight_attack_slash_8px.png",
        "knight_attack_recovery_8px.png",
        "knight_attack_progression_strip.png"
    ]:
        src_p = os.path.join("assets", fn)
        dst_p = os.path.join(artifact_dir, fn)
        shutil.copy2(src_p, dst_p)

    print("Copied all updated artifacts to brain directory successfully!")

if __name__ == "__main__":
    main()
