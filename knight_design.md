# ⚔️ Character Design Workbench: The Knight (Stances & Fluid Transitions)

> **Character Identifier**: `the_knight_standing_sentinel` / `the_knight_combat_ready`  
> **Archetype**: Gothic Vanguard Sentinel  
> **Visual Anchors**: Worn Dark Gothic Steel Plate, Tattered Crimson Mantle, Close Helm with Visor Slit, Two-Handed Greatsword  
> **Primary Matrices**: `84 columns × 116 rows` (9,744 micro-cells at 6px–8px monospace density)  
> **Movement Transition Engine**: Continuous 60 FPS physical draw & sheathe kinematics between **Rest Sentinel** and **Combat Ready** via the **[Z]** key  
> **Engine Asset Spec**: [knight.json](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/ascii/characters/knight.json)  
> **High-Density Data**: [knight_high_density.json](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/ascii/characters/knight_high_density.json)

---

## 1. Stance System & Physical Movement Transition Architecture

The knight does not instantly teleport or crossfade between stances. Instead, pressing **`Z`** initiates a physical character motion sequence where the knight draws or sheathes his two-handed greatsword:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            FLUID STANCE MOVEMENT PIPELINE                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
  REST SENTINEL             LIFT INITIATION          MID-TORSO SWEEP             HIGH HOIST              COMBAT READY
  (Planted Blade)          (Weight Shift & Dip)      (Horizontal Arc)       (Wide Stance Settle)         (Attack Guard)
     p = 0.00                    p = 0.25                p = 0.50                 p = 0.75                  p = 1.00
      [═══]                       [═══]                   [═══]                    [═══]                     [═══]
       │ │                         │ │                     │ │                      │ │                       │ │
       │ │                         │ │                     │ │                      │ │                       \ \
       │ │                         │ │                     │ │                      / /                        \ \
      ( v )                       ( v )                    \ \                     (   )                      (   )
 (Grounded Tip)              (Tip clears stone)     (Slash motion trail)      (Feet planting)             (Battle bob)

  ◀─────────────────────────────────────────────────────────────────────────────────────────▶
                        INTERRUPTIBLE & FULLY REVERSIBLE STATE MACHINE (Key: Z)
```

### The 5 Movement Phases ($p \in [0.0, 1.0]$):
1. **$p = 0.00$ — Rest Sentinel (`standing_sentinel`)**: Upright sentinel posture with two-handed blade planted vertically into flagstones between sabatons.
2. **$p = 0.25$ — Lift Initiation (`trans_lift`)**: Knight flexes into his knees ($\Delta y = +1.8$ cells) and pulls hilt upward. Blade tip clears the stone pavers and tilts $78^\circ$ outward.
3. **$p = 0.50$ — Mid-Torso Sweep (`trans_sweep`)**: The greatsword sweeps horizontally across chest/waist level. Knight steps feet outward mid-stride; crimson mantle whips outward from centrifugal force; kinetic cyan-silver motion streak trails behind blade tip.
4. **$p = 0.75$ — High Hoist (`trans_ready`)**: Blade elevates to $45^\circ$, hands locking into two-handed attack grip, right foot firmly planting into wide athletic battle base.
5. **$p = 1.00$ — Combat Ready (`combat_stance`)**: Attack-ready diagonal guard achieved, settling into continuous 60 FPS side-to-side battle bounce ($\omega = 2.8$ rad/s).

*Reversing (Combat $\to$ Rest)* executes the exact motion in reverse: lowering the blade from high guard, sweeping down across torso, stepping feet inward, and firmly planting the tip back into stone.

---

## 2. Anatomical Breakdown & Hit-Zone Architecture

### 2.1 The 9 Anatomical Sub-Blocks & Combat Hit-Zones

| Segment ID | Body Region | Rest Role | Movement Transition Role | Combat Role | Hit-Zone Multiplier | Stagger / Deflect Risk |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| `head_helm` | Close Helm & Visor | Upright vigil | Eyes track sword swing | Tucked chin into gorget | **1.75× Crit** | 45% Stagger Risk |
| `pauldrons` | Fluted Pauldrons | Symmetrical drape | Torso twist momentum | Angled lead shoulder | **0.85× Deflect** | 35% Deflection |
| `torso_cuirass` | Gothic Keel Breastplate | Upright center core | Athletic hip & chest rotation | Bladed 3/4 torso angle | **0.70× Heavy Armor** | 80% Poise Resistance |
| `cape_mantle` | Tattered Crimson Mantle | Gentle drape down flanks | Centrifugal wind flare | Billowing back over right flank | **Cloth Physics** | Pure cosmetic layer |
| `arms_gauntlets` | Gauntlets & Arm Harness | Clasped on pommel | Pulls & sweeps hilt | Two-handed raised attack grip | **1.00× Normal** | 20% Disarm Risk |
| `weapon_sword` | Greatsword | Grounded tip ($y=102$) | Continuous arc from $90^\circ \to -40^\circ$ | Raised diagonal attack guard | **38 Dmg / 55 Poise** | Reach: 2.4 units |
| `waist_fauld` | Fauld Lames & Maille | Relaxed neutral | Athletic crouch compression | Athletic hip torsion | **1.10× Normal** | 70 Armor |
| `legs_greaves` | Cuisses & Greaves | Straight standing | Knees bend & step outward | Deep bent knees in ready stance | **1.25× Vulnerable** | 30% Knockdown Risk |
| `feet_sabatons` | Pointed Sabatons | Narrow stone plant ($w=22$) | Foot slides from 22 to 52 width | Wide athletic battle base ($w=52$) | **Ground Anchor** | Zero slip anchor |

---

## 3. Procedural Harmonic Animation Kinematics

### 3.1 Snappy Transition Movement Kinematics ($T = 0.22\text{s}$)
- **Uniform Ambient Background**: Standardized 100% across all stances and transitions using the `standing_sentinel` warm torchlight plate (zero color jumping or blue-sky flicker).
- **Continuous Weapon Geometry**: Cleaned silhouette with the raised greatsword tip fully tagged up to $(82, 10)$, eliminating stray detached blade fragments in the background.
- **Knee Compression Dip**:
  $$\Delta y_{\text{knee\_dip}}(p) = \text{round}\left(1.8 \cdot \sin(\pi \cdot \min(1.0, 1.8 \cdot p))\right)$$
- **Upper Body Momentum**:
  $$\Delta x_{\text{momentum}}(p) = \text{round}\left(1.5 \cdot \sin(\pi \cdot p)\right)$$
- **Cape Centrifugal Wind Flare**:
  $$\Delta x_{\text{cape\_burst}}(y, p) = \text{round}\left(w_{\text{cape}} \cdot 4.0 \cdot \sin(\pi \cdot p)\right)$$
- **Dynamic Sword Tip Trajectory Arc**:
  $$X_{\text{tip}}(p) = 42 + 31 \cdot p$$
  $$Y_{\text{tip}}(p) = 102 - 86 \cdot p + 14 \cdot \sin(\pi \cdot p)$$
- **Kinetic Blade Streak**:
  During $0.15 \le p \le 0.88$, glowing whoosh streak glyphs (`/`, `|`, `-`, `.`) trail the moving blade tip with alpha-decaying silver/cyan glow `[180, 220, 255]`.

### 3.2 Stabilized Idle Animations
- **Rest Stance (Sentinel)**: Inverted pendulum breathing sway ($\omega = 1.2$ rad/s), blade anchored into stone at $y=102$, dual-frequency cape ripple.
- **Combat Stance (Ready)**: Spring-loaded athletic side-to-side weight transfer ($\omega = 2.8$ rad/s), vertical knee bounce, weapon inertia lag, and accelerated gale-force cape flutter ($\omega = 4.2$ rad/s).

---

## 4. Viewing Interfaces & Controls

### 4.1 Native Desktop Window ([viewer.py](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/viewer.py) — Pygame-CE)
```powershell
python viewer.py
```

| Key / Input | Action |
| :--- | :--- |
| **`[Z]`** | **Toggle Stance with Smooth Animated Physical Movement** |
| **`[SPACE]`** | Toggle Animation (Pause / Play 60 FPS loop) |
| **`[` / `]`** | Decrease / Increase animation speed (0.2x $\to$ 3.0x) |
| **`[1]`** | Hero Knight (Rest, Combat & Transitions) |
| **`[2]`** | The Weary Vigil (Camp / Rest Pose — 96×80) |
| **`[3]`** | Battlefield Overlook Scene (Wide Panoramic — 160×80) |
| **`[4]`** | Draft 1 Sentinel (Terminal Scale — 48×38) |
| **`[A]`** | Toggle Anatomical Hit-Zone Color Overlay |
| **`[C]`** | Cycle Palette (TrueColor $\to$ Grim Steel $\to$ Amber CRT $\to$ Phosphor) |
| **`[B]`** | Toggle Background Cell Shading |
| **`[G]`** | Toggle Micro-Cell Grid Lines |
| **`[+]` / `[-]` / Wheel** | Monospace Font Density Zoom (4px $\to$ 18px) |
| **Left-Click Drag** | Pan canvas |
| **`[R]`** | Reset Camera Pan & Zoom |
| **`[S]`** | Export high-res PNG snapshot to `assets/` |

### 4.2 Interactive Web Viewer ([viewer.html](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/viewer.html))
Open in any browser:
- Header **`[🛡️ / ⚔️ Z] Stance Toggle`** with real-time percentage indicators (`Drawing Greatsword (45%)` / `Sheathing to Ground (60%)`).
- Direct stance selector buttons (`Rest Sentinel` vs `Combat Ready`).
- Hotkeys: **`Z`** (stance transition), **`Space`** (play/pause), **`A`** (anatomy), **`B`** (background), **`R`** (reset pan).
- Live interactive cell & hit-zone tooltip inspector.

---

## 5. Rendered Snapshots & Asset References

- **Combat Stance (Attack Ready)**: [snapshot_combat_stance_8px.png](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/snapshot_combat_stance_8px.png)
- **Transition Phase 3 (High Hoist)**: [snapshot_trans_ready_8px.png](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/snapshot_trans_ready_8px.png)
- **Transition Phase 2 (Mid-Torso Sweep)**: [snapshot_trans_sweep_8px.png](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/snapshot_trans_sweep_8px.png)
- **Transition Phase 1 (Lift Initiation)**: [snapshot_trans_lift_8px.png](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/snapshot_trans_lift_8px.png)
- **Rest Stance (Standing Sentinel)**: [snapshot_rest_stance_8px.png](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/snapshot_rest_stance_8px.png)
- **Character Asset Schema**: [knight.json](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/ascii/characters/knight.json)
- **High-Density Matrix Dataset**: [knight_high_density.json](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/ascii/characters/knight_high_density.json)
- **Web Matrix Source**: [knight_data.js](file:///c:/Users/Asus/Desktop/Creative%20Work%20and%20ideas/Ascii%20game/ASCII-game/assets/ascii/characters/knight_data.js)
