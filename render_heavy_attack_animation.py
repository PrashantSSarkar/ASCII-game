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
    v.font_idx = 4  # 8px crisp font for rich micro-ASCII fidelity
    
    frames = []
    
    # 1. Combat Stance idle (4 frames)
    for i in range(4):
        v.is_attacking = False
        v.anim_time = i * 0.08
        v.render_matrix_surface()
        raw = pygame.image.tobytes(v.cached_surface, "RGB")
        img = Image.frombytes("RGB", v.cached_surface.get_size(), raw)
        frames.append((img, 80))
        
    # 2. Trigger Heavy Attack (6 distinct martial phases over 36 animation frames)
    v.is_attacking = True
    v.attack_type = "heavy"
    v.attack_progress = 0.0
    v.attack_slash_trail = []
    
    total_attack_steps = 36
    for i in range(total_attack_steps):
        v.attack_progress = i / float(total_attack_steps - 1)
        v.anim_time = 0.32 + i * 0.035
        v.render_matrix_surface()
        raw = pygame.image.tobytes(v.cached_surface, "RGB")
        img = Image.frombytes("RGB", v.cached_surface.get_size(), raw)
        
        ap = v.attack_progress
        if ap < 0.23:
            duration = 60   # Phase 1: Windup & Chamber (Good speed)
        elif ap < 0.41:
            duration = 65   # Phase 2: Planted Stride (Good speed)
        elif ap < 0.53:
            duration = 24   # Phase 3: Back-Turned Cut (Fast explosive strike!)
        elif ap < 0.65:
            duration = 30   # Phase 4: Follow-Through / Impact Hold (Fast!)
        elif ap < 0.83:
            duration = 65   # Phase 5: Torso Unwind (Good speed)
        else:
            duration = 65   # Phase 6: Left Leg Step & Return (Good speed)
            
        frames.append((img, duration))
        
    # 3. Settling back to combat ready (4 frames)
    v.is_attacking = False
    v.attack_slash_trail = []
    for i in range(4):
        v.anim_time = 1.6 + i * 0.08
        v.render_matrix_surface()
        raw = pygame.image.tobytes(v.cached_surface, "RGB")
        img = Image.frombytes("RGB", v.cached_surface.get_size(), raw)
        frames.append((img, 90))
        
    # Save animated GIF
    imgs = [f[0] for f in frames]
    durations = [f[1] for f in frames]
    
    gif_path = os.path.join("assets", "knight_heavy_attack_animation.gif")
    imgs[0].save(
        gif_path,
        save_all=True,
        append_images=imgs[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Saved heavy attack animation GIF ({len(frames)} frames) to {gif_path}")
    
    # Copy to artifacts directory
    artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"
    if os.path.isdir(artifact_dir):
        shutil.copy2(gif_path, os.path.join(artifact_dir, "knight_heavy_attack_animation.gif"))
        print("Copied heavy attack animation GIF to brain directory!")

if __name__ == "__main__":
    main()
