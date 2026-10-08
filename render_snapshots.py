import os
import shutil
import pygame
import json

os.environ["SDL_VIDEODRIVER"] = "dummy"

pygame.init()
pygame.display.init()
pygame.font.init()

with open("assets/ascii/characters/knight_high_density.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Use 8px font
font_size = 8
font = pygame.font.SysFont("consolas", font_size)
char_w = int(round(font_size * 0.60))
char_h = font_size

w = 84
h = 116
total_w = w * char_w
total_h = h * char_h

frames_to_render = {
    "knight_rest_stance_8px": data["standing_sentinel"],
    "knight_combat_stance_8px": data["combat_stance"],
    "knight_trans_lift_8px": data["trans_lift"],
    "knight_trans_sweep_8px": data["trans_sweep"],
    "knight_trans_ready_8px": data["trans_ready"],
}

artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"

for name, matrix in frames_to_render.items():
    surf = pygame.Surface((total_w, total_h))
    surf.fill((10, 10, 14))
    
    # 1. Backgrounds
    for y, r in enumerate(matrix["rows"]):
        for x, bg in enumerate(r["bg"]):
            rect = pygame.Rect(x * char_w, y * char_h, char_w, char_h)
            surf.fill(tuple(bg), rect)
            
    # 2. Glyphs
    for y, r in enumerate(matrix["rows"]):
        for x, (ch, fg) in enumerate(zip(r["text"], r["fg"])):
            if ch != " ":
                txt_surf = font.render(ch, True, tuple(fg))
                surf.blit(txt_surf, (x * char_w, y * char_h))
                
    asset_path = os.path.join("assets", f"{name}.png")
    pygame.image.save(surf, asset_path)
    print(f"Saved {asset_path}")
    
    art_path = os.path.join(artifact_dir, f"{name}.png")
    shutil.copyfile(asset_path, art_path)
    print(f"Copied to artifact {art_path}")

print("All snapshots rendered and copied successfully!")
