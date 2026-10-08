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
        
    # 2. Trigger Attack: Wind-up, Sweeping Cleave, Recovery (24 frames)
    v.is_attacking = True
    v.attack_progress = 0.0
    v.attack_slash_trail = []
    
    total_attack_steps = 26
    for i in range(total_attack_steps):
        v.attack_progress = i / float(total_attack_steps - 1)
        v.anim_time = 0.32 + i * 0.04
        v.render_matrix_surface()
        raw = pygame.image.tobytes(v.cached_surface, "RGB")
        img = Image.frombytes("RGB", v.cached_surface.get_size(), raw)
        
        # Timing: windup has deliberate weight, cleave is fast & explosive, recovery settles
        ap = v.attack_progress
        if ap < 0.22:
            duration = 65  # Wind-up
        elif ap < 0.60:
            duration = 45  # Explosive cleave
        else:
            duration = 55  # Recovery
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
    
    gif_path = os.path.join("assets", "knight_attack_animation.gif")
    imgs[0].save(
        gif_path,
        save_all=True,
        append_images=imgs[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Saved attack animation GIF ({len(frames)} frames) to {gif_path}")
    
    # Generate 5-stage side-by-side montage strip:
    # 1. Combat Guard -> 2. High Wind-Up -> 3. Sweeping Cleave -> 4. Slash Followthrough -> 5. Return to Guard
    key_indices = [2, 7, 14, 20, 30]
    montage_frames = [imgs[idx] for idx in key_indices]
    
    w, h = montage_frames[0].size
    strip = Image.new("RGB", (w * len(montage_frames), h), (10, 11, 14))
    for idx, frame in enumerate(montage_frames):
        strip.paste(frame, (idx * w, 0))
        
    strip_path = os.path.join("assets", "knight_attack_progression_strip.png")
    strip.save(strip_path)
    print(f"Saved attack progression strip to {strip_path}")
    
    # Copy to artifacts directory
    artifact_dir = r"C:\Users\Asus\.gemini\antigravity-ide\brain\a4e368e9-0da6-4f0c-93ee-51a8be7a445d"
    if os.path.isdir(artifact_dir):
        shutil.copy2(gif_path, os.path.join(artifact_dir, "knight_attack_animation.gif"))
        shutil.copy2(strip_path, os.path.join(artifact_dir, "knight_attack_progression_strip.png"))
        print("Copied attack animation artifacts to brain directory!")

if __name__ == "__main__":
    main()
