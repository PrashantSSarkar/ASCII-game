"""
⚔️ Dedicated High-Density ASCII Character & Scene Viewer
Built with pygame-ce for the ASCII Medieval RPG Engine

Stance System & Smooth Movement Transition:
  [Z] Toggle Stance: REST STANCE <-> COMBAT STANCE
    - Dynamic Physical Movement Transition:
      * Knight lifts two-handed greatsword off the flagstones
      * Sweeps blade diagonally across torso with kinetic motion arc
      * Steps feet outward from narrow sentinel to wide athletic battle stance
      * Billowing crimson cape catches wind from the swing momentum
      * Fully reversible and interruptible in real time
    - REST STANCE: Grounded greatsword, calm breathing sway & gentle cape ripple
    - COMBAT STANCE: Attack-ready guard with raised two-handed greatsword,
                    athletic side-to-side battle bounce & accelerated cape flutter

Controls:
  [Z] Toggle REST / COMBAT Stance (Smooth Animated Transition)
  [SPACE] Toggle Animation (PLAY / PAUSE)
  [ [ ] / [ ] ] Decrease / Increase Animation Speed
  [1] Hero Knight (Rest vs Combat Stance with Live Transition)
  [2] The Weary Vigil (Camp / Rest, 96x80)
  [3] Battlefield Overlook (Panoramic Scene, 160x80)
  [4] Draft 1 Sentinel (Terminal Scale, 48x38)
  [A] Toggle Anatomical Hit-Zone Overlay
  [C] Cycle Palette: TrueColor -> Grim Steel -> Amber CRT -> Green Phosphor
  [B] Toggle Background Shading
  [G] Toggle Grid Lines
  [+] / [-] or Mouse Wheel: Adjust Font Size / Pixel Density
  Left-Click Drag: Pan Canvas
  [R] Reset View
  [S] Save Frame Screenshot
  [ESC] / [Q] Quit
"""

import sys
import os
import json
import math
import pygame

# Set working directory to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join("assets", "ascii", "characters", "knight_high_density.json")
if not os.path.exists(DATA_PATH):
    print(f"Error: Could not find {DATA_PATH}. Run process_standing.py first.")
    sys.exit(1)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    HIGH_DENSITY_DATA = json.load(f)

# Also load Draft 1 Sentinel for View 4
from preview_knight import SENTINEL_ROWS, PALETTE as DRAFT1_PALETTE

def build_draft1_matrix():
    rows = []
    width = len(SENTINEL_ROWS[0][0])
    for art_row, col_row in SENTINEL_ROWS:
        fg_row = []
        bg_row = []
        chars = []
        for ch, code in zip(art_row, col_row):
            info = DRAFT1_PALETTE.get(code)
            chars.append(ch)
            if info:
                hex_c = info[0].lstrip('#')
                r = int(hex_c[0:2], 16)
                g = int(hex_c[2:4], 16)
                b = int(hex_c[4:6], 16)
                fg_row.append([r, g, b])
                bg_row.append([int(r * 0.15), int(g * 0.15), int(b * 0.15)])
            else:
                fg_row.append([120, 120, 120])
                bg_row.append([10, 10, 15])
        rows.append({
            "text": "".join(chars),
            "fg": fg_row,
            "bg": bg_row
        })
    return {
        "id": "draft1_sentinel_hero",
        "name": "Draft 1 Sentinel (Terminal Scale)",
        "width": width,
        "height": len(rows),
        "rows": rows
    }

DRAFT1_MATRIX = build_draft1_matrix()

# Anatomical overlay palette
ANATOMY_PALETTE = {
    "head_helm":        ((241, 196, 15),  "Head: Close Helm & Visor [1.75x Crit Hitbox]"),
    "pauldrons":        ((189, 195, 199), "Shoulders: Tiered Pauldrons [0.85x Deflect]"),
    "torso_cuirass":    ((0, 206, 201),   "Torso: Gothic Cuirass & Ridge [0.70x Armor]"),
    "cape_mantle":      ((231, 76, 60),   "Cape: Tattered Crimson Mantle [Sine Wave Physics]"),
    "arms_gauntlets":   ((230, 126, 34),  "Arms: Vambraces & Gauntlets [1.00x Hitbox]"),
    "weapon_sword":     ((255, 255, 255), "Weapon: Two-Handed Greatsword [38 Dmg / 55 Poise]"),
    "waist_fauld":      ((155, 89, 182),  "Waist: Fauld & Maille Skirt [1.10x Hitbox]"),
    "legs_greaves":     ((46, 204, 113),  "Legs: Cuisses & Greaves [1.25x Stagger Hitbox]"),
    "feet_sabatons":    ((52, 73, 94),    "Feet: Pointed Sabatons & Spurs [Ground Plant]"),
    "ground_flagstone": ((80, 85, 95),    "Ground: Weathered Flagstone Pavers"),
    "background":       ((20, 22, 28),    "Environment Background")
}

class AsciiViewer:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        pygame.font.init()
        
        self.win_width = 1140
        self.win_height = 920
        self.screen = pygame.display.set_mode((self.win_width, self.win_height), pygame.RESIZABLE)
        pygame.display.set_caption("⚔️ ASCII Knight — Animated Stances & Transitions Viewer")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Stance System & Dynamic Transition State
        self.stance = "rest"             # Current stabilized stance: 'rest' or 'combat'
        self.target_stance = "rest"      # Destination stance
        self.is_transitioning = False    # True while actively moving between stances
        self.transition_progress = 0.0   # 0.0 = rest, 1.0 = combat
        self.transition_duration = 0.22  # Snappy responsive stance transition duration
        self.sword_trail = []            # Motion trail points (x, y, age)
        
        # Other views (Vigil, Scene, Draft 1)
        self.current_view_idx = 0
        
        # Supported font sizes
        self.font_sizes = [4, 5, 6, 7, 8, 9, 10, 12, 14, 18]
        self.font_idx = 3  # Default 7px
        self.font_cache = {}
        
        # Palette Modes
        self.palettes = ["TrueColor", "Grim Steel", "Amber CRT", "Emerald Phosphor"]
        self.palette_idx = 0
        
        # Toggles
        self.show_bg = True
        self.show_grid = False
        self.show_anatomy = False
        
        # Animation State
        self.is_animated = True
        self.anim_time = 0.0
        self.anim_speed = 1.0
        
        # Camera / Panning
        self.pan_x = 90
        self.pan_y = 50
        self.is_panning = False
        self.pan_start = (0, 0)
        self.pan_orig = (0, 0)
        
        # UI Font
        self.ui_font = pygame.font.SysFont("consolas", 14, bold=True)
        self.small_ui_font = pygame.font.SysFont("consolas", 12)
        
        # Surface caching
        self.cached_surface = None
        self.dirty_surface = True
        
        # Hover info
        self.hover_cell = None

    def get_font(self, size):
        if size not in self.font_cache:
            font = pygame.font.SysFont("consolas", size)
            char_w, char_h = font.size("M")
            char_w = max(1, char_w)
            char_h = max(1, char_h)
            self.font_cache[size] = (font, char_w, char_h)
        return self.font_cache[size]

    def current_data(self):
        if self.current_view_idx == 0:
            if self.is_transitioning:
                p = self.transition_progress
                if p < 0.18:
                    return HIGH_DENSITY_DATA["standing_sentinel"]
                elif p < 0.44:
                    return HIGH_DENSITY_DATA["trans_lift"]
                elif p < 0.72:
                    return HIGH_DENSITY_DATA["trans_sweep"]
                elif p < 0.90:
                    return HIGH_DENSITY_DATA["trans_ready"]
                else:
                    return HIGH_DENSITY_DATA["combat_stance"]
            else:
                if self.stance == "combat":
                    return HIGH_DENSITY_DATA["combat_stance"]
                else:
                    return HIGH_DENSITY_DATA["standing_sentinel"]
        elif self.current_view_idx == 1:
            return HIGH_DENSITY_DATA["character_focus"]
        elif self.current_view_idx == 2:
            return HIGH_DENSITY_DATA["scene"]
        else:
            return DRAFT1_MATRIX

    def render_matrix_surface(self):
        data = self.current_data()
        font_size = self.font_sizes[self.font_idx]
        font, char_w, char_h = self.get_font(font_size)
        
        cols = data["width"]
        rows = data["height"]
        
        # Extra padding on sides so billowing cape & wide stance don't clip
        pad_x = char_w * 6
        pad_y = char_h * 3
        
        surf_w = cols * char_w + pad_x * 2
        surf_h = rows * char_h + pad_y * 2
        surf = pygame.Surface((surf_w, surf_h))
        surf.fill((12, 12, 16))
        
        has_anatomy = "anatomy" in data["rows"][0]
        is_hero_view = (self.current_view_idx == 0)
        is_combat = is_hero_view and (self.stance == "combat") and not self.is_transitioning
        t = self.anim_time if self.is_animated else 0.0
        
        # Transition progress parameters
        p = self.transition_progress if self.is_transitioning else (1.0 if is_combat else 0.0)
        
        # Render background rects
        if self.show_bg:
            for y, row_data in enumerate(data["rows"]):
                row_anat = row_data["anatomy"] if has_anatomy else None
                for x, bg_col in enumerate(row_data["bg"]):
                    dx = 0
                    dy = 0
                    zone = row_anat[x] if row_anat else "background"
                    
                    if is_hero_view:
                        if self.is_transitioning:
                            # TRANSITION MOTION KINEMATICS
                            # 1. Torso & Arms follow momentum of the greatsword swing
                            swing_momentum = math.sin(math.pi * p)
                            if zone in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets"):
                                dx = int(round(1.5 * swing_momentum * char_w))
                                # Downward knee dip during heavy blade lift
                                dy = int(round(1.8 * math.sin(math.pi * min(1.0, p * 1.8)) * char_h))
                            elif zone == "cape_mantle":
                                # Sudden wind billow as the heavy sword sweeps
                                cape_weight = max(0.0, (y - 18) / 90.0)
                                dx = int(round(4.0 * cape_weight * swing_momentum * char_w))
                                dy = int(round(1.0 * cape_weight * swing_momentum * char_h))
                        elif self.is_animated:
                            if is_combat:
                                # COMBAT STANCE: Side-to-Side Battle Bob & Weight Shift
                                sway_weight = max(0.0, (108 - y) / 95.0)
                                if zone == "cape_mantle":
                                    cape_weight = max(0.0, (y - 18) / 90.0)
                                    dx_cells = 3.0 * cape_weight * math.sin(0.16 * y + 4.2 * t) + 1.2 * cape_weight * math.cos(0.09 * y + 2.5 * t)
                                    dy_cells = 0.7 * cape_weight * math.sin(0.14 * y + 3.5 * t)
                                    dx = int(round(dx_cells * char_w))
                                    dy = int(round(dy_cells * char_h))
                                elif zone == "weapon_sword":
                                    dx = int(round(1.8 * math.sin(2.8 * t - 0.35) * char_w))
                                    dy = int(round(0.8 * abs(math.cos(2.8 * t)) * char_h))
                                elif zone in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets", "waist_fauld", "legs_greaves"):
                                    dx = int(round(1.6 * sway_weight * math.sin(2.8 * t) * char_w))
                                    dy = int(round(0.8 * sway_weight * abs(math.cos(2.8 * t)) * char_h))
                            else:
                                # REST STANCE: Inverted Pendulum Breathing Sway & Cape Ripple
                                if zone == "cape_mantle":
                                    cape_weight = max(0.0, (y - 16) / 92.0)
                                    dx_cells = 2.4 * cape_weight * math.sin(0.14 * y + 3.2 * t) + 0.8 * cape_weight * math.cos(0.08 * y + 1.8 * t)
                                    dy_cells = 0.5 * cape_weight * math.sin(0.10 * y + 2.5 * t)
                                    dx = int(round(dx_cells * char_w))
                                    dy = int(round(dy_cells * char_h))
                                elif zone in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets", "waist_fauld"):
                                    sway_weight = max(0.0, (100 - y) / 95.0)
                                    dx = int(round(1.3 * sway_weight * math.sin(1.2 * t) * char_w))
                                    dy = int(round(0.5 * math.sin(1.2 * t) * char_h))
                                elif zone == "weapon_sword":
                                    sword_weight = max(0.0, (110 - y) / 68.0)
                                    dx = int(round(1.3 * sword_weight * math.sin(1.2 * t) * char_w))
                                    dy = int(round(0.5 * sword_weight * math.sin(1.2 * t) * char_h))

                    draw_x = pad_x + x * char_w + dx
                    draw_y = pad_y + y * char_h + dy
                    
                    if self.show_anatomy and has_anatomy:
                        col, _ = ANATOMY_PALETTE.get(zone, ((20, 20, 25), ""))
                        r, g, b = int(col[0] * 0.25), int(col[1] * 0.25), int(col[2] * 0.25)
                    else:
                        r, g, b = self.apply_palette(bg_col)
                    rect = pygame.Rect(draw_x, draw_y, char_w, char_h)
                    surf.fill((r, g, b), rect)
                    
        # Grid lines
        if self.show_grid and char_w > 4:
            grid_col = (25, 25, 35)
            for x in range(cols + 1):
                pygame.draw.line(surf, grid_col, (pad_x + x * char_w, pad_y), (pad_x + x * char_w, pad_y + rows * char_h))
            for y in range(rows + 1):
                pygame.draw.line(surf, grid_col, (pad_x, pad_y + y * char_h), (pad_x + cols * char_w, pad_y + y * char_h))

        # Glyphs
        blits = []
        for y, row_data in enumerate(data["rows"]):
            text_str = row_data["text"]
            row_anat = row_data["anatomy"] if has_anatomy else None
            
            for x, (ch, fg_col) in enumerate(zip(text_str, row_data["fg"])):
                if ch == ' ':
                    continue
                
                dx = 0
                dy = 0
                zone = row_anat[x] if row_anat else "background"
                
                if is_hero_view:
                    if self.is_transitioning:
                        swing_momentum = math.sin(math.pi * p)
                        if zone in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets"):
                            dx = int(round(1.5 * swing_momentum * char_w))
                            dy = int(round(1.8 * math.sin(math.pi * min(1.0, p * 1.8)) * char_h))
                        elif zone == "cape_mantle":
                            cape_weight = max(0.0, (y - 18) / 90.0)
                            dx = int(round(4.0 * cape_weight * swing_momentum * char_w))
                            dy = int(round(1.0 * cape_weight * swing_momentum * char_h))
                    elif self.is_animated:
                        if is_combat:
                            sway_weight = max(0.0, (108 - y) / 95.0)
                            if zone == "cape_mantle":
                                cape_weight = max(0.0, (y - 18) / 90.0)
                                dx_cells = 3.0 * cape_weight * math.sin(0.16 * y + 4.2 * t) + 1.2 * cape_weight * math.cos(0.09 * y + 2.5 * t)
                                dy_cells = 0.7 * cape_weight * math.sin(0.14 * y + 3.5 * t)
                                dx = int(round(dx_cells * char_w))
                                dy = int(round(dy_cells * char_h))
                            elif zone == "weapon_sword":
                                dx = int(round(1.8 * math.sin(2.8 * t - 0.35) * char_w))
                                dy = int(round(0.8 * abs(math.cos(2.8 * t)) * char_h))
                            elif zone in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets", "waist_fauld", "legs_greaves"):
                                dx = int(round(1.6 * sway_weight * math.sin(2.8 * t) * char_w))
                                dy = int(round(0.8 * sway_weight * abs(math.cos(2.8 * t)) * char_h))
                        else:
                            if zone == "cape_mantle":
                                cape_weight = max(0.0, (y - 16) / 92.0)
                                dx_cells = 2.4 * cape_weight * math.sin(0.14 * y + 3.2 * t) + 0.8 * cape_weight * math.cos(0.08 * y + 1.8 * t)
                                dy_cells = 0.5 * cape_weight * math.sin(0.10 * y + 2.5 * t)
                                dx = int(round(dx_cells * char_w))
                                dy = int(round(dy_cells * char_h))
                            elif zone in ("head_helm", "pauldrons", "torso_cuirass", "arms_gauntlets", "waist_fauld"):
                                sway_weight = max(0.0, (100 - y) / 95.0)
                                dx = int(round(1.3 * sway_weight * math.sin(1.2 * t) * char_w))
                                dy = int(round(0.5 * math.sin(1.2 * t) * char_h))
                            elif zone == "weapon_sword":
                                sword_weight = max(0.0, (110 - y) / 68.0)
                                dx = int(round(1.3 * sword_weight * math.sin(1.2 * t) * char_w))
                                dy = int(round(0.5 * sword_weight * math.sin(1.2 * t) * char_h))

                draw_x = pad_x + x * char_w + dx
                draw_y = pad_y + y * char_h + dy

                if self.show_anatomy and has_anatomy:
                    col, _ = ANATOMY_PALETTE.get(zone, ((160, 160, 160), ""))
                    r, g, b = col
                else:
                    r, g, b = self.apply_palette(fg_col)
                    # Dynamic specular lighting on blade / cape during motion
                    if is_hero_view and self.is_animated and zone == "cape_mantle":
                        freq = 4.2 if (is_combat or self.is_transitioning) else 3.2
                        shimmer = int(18 * math.sin(0.14 * y + freq * t))
                        r = min(255, max(0, r + shimmer))
                    elif is_hero_view and self.is_transitioning and zone == "weapon_sword":
                        # Glint gleam on blade during sweep
                        r = min(255, r + 25)
                        g = min(255, g + 25)
                        b = min(255, b + 25)
                    
                try:
                    glyph_surf = font.render(ch, False, (r, g, b))
                    blits.append((glyph_surf, (draw_x, draw_y)))
                except Exception:
                    pass
                    
        # Render dynamic blade motion trail during transition
        if is_hero_view and self.is_transitioning and 0.15 <= p <= 0.88:
            # Current blade tip estimate
            tip_x = int(round(42 + 31 * p))
            tip_y = int(round(102 - 86 * p + 14 * math.sin(math.pi * p)))
            self.sword_trail.append((tip_x, tip_y, 0))
            if len(self.sword_trail) > 5:
                self.sword_trail.pop(0)
                
            for trail_idx, (tx, ty, _) in enumerate(self.sword_trail):
                trail_px = pad_x + tx * char_w
                trail_py = pad_y + ty * char_h
                alpha_factor = (trail_idx + 1) / len(self.sword_trail)
                tr_color = (int(160 * alpha_factor), int(200 * alpha_factor), int(255 * alpha_factor))
                trail_ch = "/" if p > 0.4 else "|"
                try:
                    trail_surf = font.render(trail_ch, False, tr_color)
                    blits.append((trail_surf, (trail_px, trail_py)))
                except Exception:
                    pass
        elif not self.is_transitioning and len(self.sword_trail) > 0:
            self.sword_trail.clear()
            
        surf.blits(blits)
        self.cached_surface = surf
        self.dirty_surface = False

    def apply_palette(self, rgb):
        r, g, b = rgb
        mode = self.palettes[self.palette_idx]
        if mode == "TrueColor":
            return r, g, b
        elif mode == "Grim Steel":
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            return int(lum * 0.85), int(lum * 0.95), min(255, int(lum * 1.15))
        elif mode == "Amber CRT":
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            return min(255, int(lum * 1.3)), int(lum * 0.75), int(lum * 0.15)
        elif mode == "Emerald Phosphor":
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            return int(lum * 0.2), min(255, int(lum * 1.3)), int(lum * 0.3)
        return r, g, b

    def toggle_stance(self):
        # Triggers smooth animated movement between rest and combat stance
        self.current_view_idx = 0
        if self.target_stance == "rest":
            self.target_stance = "combat"
        else:
            self.target_stance = "rest"
        self.is_transitioning = True
        self.dirty_surface = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.win_width = event.w
                self.win_height = event.h
                self.screen = pygame.display.set_mode((self.win_width, self.win_height), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key == pygame.K_z:
                    self.toggle_stance()
                elif event.key == pygame.K_SPACE:
                    self.is_animated = not self.is_animated
                    self.dirty_surface = True
                elif event.key == pygame.K_LEFTBRACKET:
                    self.anim_speed = max(0.2, self.anim_speed - 0.2)
                elif event.key == pygame.K_RIGHTBRACKET:
                    self.anim_speed = min(3.0, self.anim_speed + 0.2)
                elif event.key == pygame.K_1:
                    self.current_view_idx = 0
                    self.dirty_surface = True
                elif event.key == pygame.K_2:
                    self.current_view_idx = 1
                    self.dirty_surface = True
                elif event.key == pygame.K_3:
                    self.current_view_idx = 2
                    self.dirty_surface = True
                elif event.key == pygame.K_4:
                    self.current_view_idx = 3
                    self.dirty_surface = True
                elif event.key == pygame.K_a:
                    self.show_anatomy = not self.show_anatomy
                    self.dirty_surface = True
                elif event.key == pygame.K_c:
                    self.palette_idx = (self.palette_idx + 1) % len(self.palettes)
                    self.dirty_surface = True
                elif event.key == pygame.K_b:
                    self.show_bg = not self.show_bg
                    self.dirty_surface = True
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                    self.dirty_surface = True
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    if self.font_idx < len(self.font_sizes) - 1:
                        self.font_idx += 1
                        self.dirty_surface = True
                elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                    if self.font_idx > 0:
                        self.font_idx -= 1
                        self.dirty_surface = True
                elif event.key == pygame.K_r:
                    self.pan_x = 90
                    self.pan_y = 50
                elif event.key == pygame.K_s:
                    if self.cached_surface:
                        out_path = os.path.join("assets", f"snapshot_{self.stance}_{self.font_sizes[self.font_idx]}px.png")
                        pygame.image.save(self.cached_surface, out_path)
                        print(f"Saved snapshot to {out_path}")
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0 and self.font_idx < len(self.font_sizes) - 1:
                    self.font_idx += 1
                    self.dirty_surface = True
                elif event.y < 0 and self.font_idx > 0:
                    self.font_idx -= 1
                    self.dirty_surface = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.is_panning = True
                    self.pan_start = event.pos
                    self.pan_orig = (self.pan_x, self.pan_y)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_panning = False
            elif event.type == pygame.MOUSEMOTION:
                if self.is_panning:
                    dx = event.pos[0] - self.pan_start[0]
                    dy = event.pos[1] - self.pan_start[1]
                    self.pan_x = self.pan_orig[0] + dx
                    self.pan_y = self.pan_orig[1] + dy
                self.update_hover(event.pos)

    def update_hover(self, mouse_pos):
        font_size = self.font_sizes[self.font_idx]
        _, char_w, char_h = self.get_font(font_size)
        data = self.current_data()
        
        pad_x = char_w * 6
        pad_y = char_h * 3
        
        rel_x = mouse_pos[0] - self.pan_x - pad_x
        rel_y = mouse_pos[1] - self.pan_y - pad_y
        
        if 0 <= rel_x < data["width"] * char_w and 0 <= rel_y < data["height"] * char_h:
            cell_x = int(rel_x // char_w)
            cell_y = int(rel_y // char_h)
            if cell_y < len(data["rows"]) and cell_x < len(data["rows"][cell_y]["text"]):
                ch = data["rows"][cell_y]["text"][cell_x]
                fg = data["rows"][cell_y]["fg"][cell_x]
                bg = data["rows"][cell_y]["bg"][cell_x]
                zone_desc = ""
                if "anatomy" in data["rows"][cell_y]:
                    zone = data["rows"][cell_y]["anatomy"][cell_x]
                    _, zone_desc = ANATOMY_PALETTE.get(zone, ((0,0,0), zone))
                self.hover_cell = (cell_x, cell_y, ch, fg, bg, zone_desc)
                return
        self.hover_cell = None

    def draw_ui(self):
        # Top Header Bar
        header_rect = pygame.Rect(0, 0, self.win_width, 44)
        pygame.draw.rect(self.screen, (18, 20, 26), header_rect)
        pygame.draw.line(self.screen, (38, 42, 54), (0, 44), (self.win_width, 44))
        
        f_size = self.font_sizes[self.font_idx]
        _, cw, ch = self.get_font(f_size)
        
        # Stance & Transition Badges
        if self.current_view_idx == 0:
            if self.is_transitioning:
                if self.target_stance == "combat":
                    pct = int(self.transition_progress * 100)
                    stance_badge = f"[DRAWING WEAPON: {pct}%]"
                    badge_col = (241, 196, 15)
                else:
                    pct = int((1.0 - self.transition_progress) * 100)
                    stance_badge = f"[GROUNDING WEAPON: {pct}%]"
                    badge_col = (116, 185, 255)
            elif self.stance == "combat":
                stance_badge = "[STANCE: COMBAT READY (ATTACK)]"
                badge_col = (255, 75, 75)
            else:
                stance_badge = "[STANCE: REST SENTINEL]"
                badge_col = (46, 204, 113)
            view_title = f"The Knight {stance_badge} — [Z] Toggle"
        else:
            view_titles = ["", "The Weary Vigil (Camp)", "Battlefield Overlook (Scene)", "Draft 1 Sentinel (Terminal)"]
            view_title = view_titles[self.current_view_idx]
            badge_col = (240, 240, 245)
        
        title_surf = self.ui_font.render(f"⚔️ {view_title}", True, badge_col)
        self.screen.blit(title_surf, (16, 13))
        
        anatomy_status = "ON" if self.show_anatomy else "OFF"
        fps = int(self.clock.get_fps())
        meta_txt = f"{fps} FPS | Font: {f_size}px ({cw}x{ch}) | [Z] Stance Transition | [A] Anat: {anatomy_status}"
        meta_surf = self.small_ui_font.render(meta_txt, True, (160, 175, 195))
        self.screen.blit(meta_surf, (self.win_width - meta_surf.get_width() - 16, 15))
        
        # Bottom Status Bar / Inspector
        bar_y = self.win_height - 34
        bar_rect = pygame.Rect(0, bar_y, self.win_width, 34)
        pygame.draw.rect(self.screen, (16, 18, 24), bar_rect)
        pygame.draw.line(self.screen, (35, 38, 50), (0, bar_y), (self.win_width, bar_y))
        
        if self.hover_cell:
            cx, cy, ch, fg, bg, zone_desc = self.hover_cell
            swatch_rect = pygame.Rect(16, bar_y + 9, 16, 16)
            pygame.draw.rect(self.screen, (fg[0], fg[1], fg[2]), swatch_rect)
            pygame.draw.rect(self.screen, (200, 200, 200), swatch_rect, 1)
            
            anatomy_tag = f" | {zone_desc}" if zone_desc else ""
            info_txt = f"Cell: ({cx}, {cy}) | Glyph: '{ch}' | FG: ({fg[0]},{fg[1]},{fg[2]}){anatomy_tag}"
            info_surf = self.small_ui_font.render(info_txt, True, (220, 230, 245))
            self.screen.blit(info_surf, (40, bar_y + 9))
        else:
            hint_txt = "Press [Z] for Smooth Transition Animation | [SPACE] Play/Pause | [1/2/3/4] Views | [A] Anatomy | Drag to Pan | Scroll Zoom"
            hint_surf = self.small_ui_font.render(hint_txt, True, (120, 130, 145))
            self.screen.blit(hint_surf, (16, bar_y + 9))

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            self.handle_events()
            
            # Step transition state machine
            if self.is_transitioning:
                speed = (1.0 / self.transition_duration) * self.anim_speed
                if self.target_stance == "combat":
                    self.transition_progress += dt * speed
                    if self.transition_progress >= 1.0:
                        self.transition_progress = 1.0
                        self.is_transitioning = False
                        self.stance = "combat"
                else:
                    self.transition_progress -= dt * speed
                    if self.transition_progress <= 0.0:
                        self.transition_progress = 0.0
                        self.is_transitioning = False
                        self.stance = "rest"
                self.dirty_surface = True
                
            if self.is_animated:
                self.anim_time += dt * self.anim_speed
                self.dirty_surface = True
                
            if self.dirty_surface:
                self.render_matrix_surface()
                
            self.screen.fill((10, 10, 14))
            
            if self.cached_surface:
                self.screen.blit(self.cached_surface, (self.pan_x, self.pan_y))
                
            self.draw_ui()
            pygame.display.flip()
            
        pygame.quit()

if __name__ == "__main__":
    viewer = AsciiViewer()
    viewer.run()
