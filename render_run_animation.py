import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import shutil
import math
from PIL import Image

def main():
    import json
    with open("assets/ascii/characters/knight_high_density.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    pygame.init()
    font = pygame.font.SysFont("consolas", 8)
    cw, ch = font.size("M")
    w = data["combat_stance"]["width"]
    h = data["combat_stance"]["height"]

    def render_matrix_to_img(mat):
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
        return Image.frombytes("RGB", surf.get_size(), raw)

    frames = []

    # 1. Base Combat Stance (Active Attack Stance) — 4 frames (80ms each)
    img_combat = render_matrix_to_img(data["combat_stance"])
    for _ in range(4):
        frames.append((img_combat, 80))

    # 2. Transition from Attack Stance to Running — 2 frames (70ms each)
    img_start = render_matrix_to_img(data["run_trans_start"])
    frames.append((img_start, 70))
    frames.append((img_start, 60))

    # 3. Running Loop: 3 full stride cycles (each cycle = Stride 1 -> 2 -> 3 -> 4)
    # 70ms per stride phase for athletic sprint cadence
    img_s1 = render_matrix_to_img(data["run_stride_1"])
    img_s2 = render_matrix_to_img(data["run_stride_2"])
    img_s3 = render_matrix_to_img(data["run_stride_3"])
    img_s4 = render_matrix_to_img(data["run_stride_4"])

    for cycle in range(3):
        frames.append((img_s1, 65))
        frames.append((img_s2, 65))
        frames.append((img_s3, 65))
        frames.append((img_s4, 65))

    # 4. Braking Skid / Stop — 3 frames (80ms, 90ms, 80ms)
    img_skid = render_matrix_to_img(data["run_skid_stop"])
    frames.append((img_skid, 80))
    frames.append((img_skid, 90))
    frames.append((img_skid, 80))

    # 5. Recovery Return to Active Stance — 2 frames (75ms each)
    img_recover = render_matrix_to_img(data["run_recover_stance"])
    frames.append((img_recover, 75))
    frames.append((img_recover, 75))

    # 6. Settled back in Combat Stance — 4 frames (80ms each)
    for _ in range(4):
        frames.append((img_combat, 80))

    # Save animated GIF
    imgs = [f[0] for f in frames]
    durations = [f[1] for f in frames]

    gif_path = os.path.join("assets", "knight_run_animation.gif")
    imgs[0].save(
        gif_path,
        save_all=True,
        append_images=imgs[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Saved running animation GIF ({len(frames)} frames) to {gif_path}")

    # Copy to artifacts directory
    artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"
    if os.path.isdir(artifact_dir):
        shutil.copy2(gif_path, os.path.join(artifact_dir, "knight_run_animation.gif"))
        print("Copied running animation GIF to brain directory!")

if __name__ == "__main__":
    main()
