import json

with open("assets/ascii/characters/knight_high_density.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. Verify Transitions for any yellow
yellow_found = []
for trans_key in ("trans_lift", "trans_sweep", "trans_ready"):
    frame = data[trans_key]
    for y, r in enumerate(frame["rows"]):
        for x in range(frame["width"]):
            fg = r["fg"][x]
            bg = r["bg"][x]
            # Yellow: high red & green, low blue
            if (fg[0] > 180 and fg[1] > 140 and fg[2] < 110) or (bg[0] > 60 and bg[1] > 40 and bg[2] < 25):
                yellow_found.append((trans_key, x, y, r["text"][x], fg, bg))

print(f"1. Transition Yellow Check: {len(yellow_found)} yellow cells found.")
if yellow_found:
    print("   Example:", yellow_found[0])
else:
    print("   -> PASS: 100% polished gothic steel, zero yellow/gold!")

# 2. Verify Arm Region Blue in combat_stance
combat = data["combat_stance"]
blue_found = []
for y in range(24, 63):
    r = combat["rows"][y]
    for x in range(33):
        anat = r["anatomy"][x]
        fg = r["fg"][x]
        bg = r["bg"][x]
        # Check if cell has blue tint
        is_blue = (bg[2] > bg[0] and bg[2] >= 14) or (fg[2] > fg[0] + 10 and anat != "weapon_sword")
        if is_blue:
            blue_found.append((x, y, r["text"][x], anat, fg, bg))

print(f"2. Arm Region Blue Check: {len(blue_found)} blue cells found.")
if blue_found:
    print("   Examples:", blue_found[:3])
else:
    print("   -> PASS: Zero blue sky cells in arm region!")

# 3. Verify Blade in combat_stance
sword_cells_by_row = {}
for y in range(10, 62):
    r = combat["rows"][y]
    sword_x = []
    for x in range(combat["width"]):
        if r["anatomy"][x] == "weapon_sword":
            sword_x.append((x, r["text"][x], r["fg"][x]))
    if sword_x:
        sword_cells_by_row[y] = sword_x

print(f"3. Combat Blade Check: Sword present across {len(sword_cells_by_row)} rows (y={min(sword_cells_by_row.keys())} to {max(sword_cells_by_row.keys())})")
widths = [len(v) for v in sword_cells_by_row.values()]
print(f"   Max blade width: {max(widths)}, Min blade width: {min(widths)}, Avg width: {sum(widths)/len(widths):.1f}")
print("   Tip row (y=10):", [(x, ch, fg) for x, ch, fg in sword_cells_by_row[10]])
print("   Mid blade row (y=30):", [(x, ch, fg) for x, ch, fg in sword_cells_by_row[30]])
print("   Guard row (y=58):", [(x, ch, fg) for x, ch, fg in sword_cells_by_row[58]])

# 4. Verify Left Flank Dark Cape Silhouette in combat_stance
dark_flank_cells = []
for y in range(24, 106):
    r = combat["rows"][y]
    for x in range(20):
        anat = r["anatomy"][x]
        bg = r["bg"][x]
        # Old dark shadow had sum(bg) < 22
        if anat == "background" and sum(bg) < 25:
            dark_flank_cells.append((x, y, bg))

print(f"4. Left Flank Dark Cape Shadow Check: {len(dark_flank_cells)} dark cells found.")
if dark_flank_cells:
    print("   Example:", dark_flank_cells[:3])
else:
    print("   -> PASS: Zero dark cape shadow cells! Uniform warm torchlight throughout.")
