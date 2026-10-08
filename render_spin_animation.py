import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import shutil
import math
from PIL import Image

import viewer

def main():
    v = viewer.AsciiViewer()
    v.stance = "combat"
    v.current_view_idx = 0
    v.font_idx = 4  # 8px crisp font for rich detail
    
    frames = []
    
    # 1. Combat Stance idle (4 frames)
    for i in range(4):
        v.is_attacking = False
        v.anim_time = i * 0.08
        v.render_matrix_surface()
        raw = pygame.image.tobytes(v.cached_surface, "RGB")
        img = Image.frombytes("RGB", v.cached_surface.get_size(), raw)
        frames.append((img, 80)) # 80ms per frame
        
    # 2. Trigger Spin Attack: Step with back leg -> Back turned sweeping cleave -> Step with other leg (26 frames)
    v.is_attacking = True
    v.attack_type = "spin"
    v.attack_progress = 0.0
    v.attack_slash_trail = []
    
    total_attack_steps = 26
    for i in range(total_attack_steps):
        v.attack_progress = i / float(total_attack_steps - 1)
        v.anim_time = 0.32 + i * 0.04
        v.render_matrix_surface()
        raw = pygame.image.tobytes(v.cached_surface, "RGB")
        img = Image.frombytes("RGB", v.cached_surface.get_size(), raw)
        
        # Timing: step has deliberate weight, cleave is fast & explosive, return steps to plant
        ap = v.attack_progress
        if ap < 0.28:
            duration = 65  # Step with back leg
        elif ap < 0.65:
            duration = 45  # Explosive reverse 360 cleave
        else:
            duration = 60  # Step with other leg to return
        frames.append((img, duration))
        
    # 3. Settling back to combat ready (4 frames)
    v.is_attacking = False
    v.attack_slash_trail = []
    for i in range(4):
        v.anim_time = 1.4 + i * 0.08
        v.render_matrix_surface()
        raw = pygame.image.tobytes(v.cached_surface, "RGB")
        img = Image.frombytes("RGB", v.cached_surface.get_size(), raw)
        frames.append((img, 90))
        
    # Save animated GIF
    imgs = [f[0] for f in frames]
    durations = [f[1] for f in frames]
    
    gif_path = os.path.join("assets", "knight_spin_attack_animation.gif")
    imgs[0].save(
        gif_path,
        save_all=True,
        append_images=imgs[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Saved spin attack animation GIF ({len(frames)} frames) to {gif_path}")
    
    # Copy to artifacts directory
    artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"
    if os.path.isdir(artifact_dir):
        shutil.copy2(gif_path, os.path.join(artifact_dir, "knight_spin_attack_animation.gif"))
        print("Copied spin animation GIF to brain directory!")

if __name__ == "__main__":
    main()
