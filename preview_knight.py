import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console(width=110, highlight=False)

# ==========================================
# COLOR PALETTE SPECIFICATION
# ==========================================
PALETTE = {
    'r': ("#FF5555", "Light Red Crest (Plume Highlight)"),
    'R': ("#B71C1C", "Deep Red Crest (Plume Shadow)"),
    'S': ("#E2E8F0", "Worn Steel (Polished Rim & Edges)"),
    's': ("#8A9AA7", "Worn Steel (Main Cuirass & Plates)"),
    'd': ("#1E293B", "Steel Crevices & Visor Slits"),
    'm': ("#64748B", "Chainmail Hauberk Links"),
    'c': ("#54331C", "Dark Brown Cape (Main Drape)"),
    'h': ("#7A4E2C", "Dark Brown Cape (Fold Highlight)"),
    'C': ("#331E10", "Dark Brown Cape (Deep Shadow)"),
    'l': ("#5B3A29", "Oiled Leather (Belts & Straps)"),
    'g': ("#F59E0B", "Aged Brass / Gold (Rivets & Buckles)"),
    'b': ("#CBD5E1", "Honed Blade (Fuller & Flat)"),
    'B': ("#FFFFFF", "Blade Razor Edge"),
}

# ==========================================
# SPRITE DATA 1: THE IRON SENTINEL
# ==========================================
SENTINEL_ROWS = [
    ( "                      ,~~~~~~.                  ",
      "                      rrrrrrrr                  " ),
    ( "                    .'  / / / \\                 ",
      "                    rr  r r r r                 " ),
    ( "                  .'  / / / /  |                ",
      "                  Rr  r r r r  r                " ),
    ( "                 /  / / / /   /                 ",
      "                 R  r r r r   r                 " ),
    ( "                |  / / / /   /                  ",
      "                R  r r r r   r                  " ),
    ( "                 \\  \\ \\ \\ \\ /                   ",
      "                 R  R R R R r                   " ),
    ( "               .--'--\\_\\_\\_v--.                 ",
      "               SSSSSSddddddSSSS                 " ),
    ( "              /  .------------.  \\              ",
      "              S  SssssssssssssS  S              " ),
    ( "             /  /  __________  \\  \\             ",
      "             S  S  dddddddddd  S  S             " ),
    ( "            |  |  /  _    _  \\  |  |            ",
      "            S  s  d  S    S  d  s  S            " ),
    ( "            |  | |  [|]  [|]  | |  |            ",
      "            S  s d  dSd  dSd  d s  S            " ),
    ( "            |  | |  ===::===  | |  |            ",
      "            S  s d  dddddddd  d s  S            " ),
    ( "            |  |  \\   ____   /  |  |            ",
      "            S  s  d   dddd   d  s  S            " ),
    ( "             \\  \\  '-......-'  /  /             ",
      "             S  S  sdddddddds  S  S             " ),
    ( "      _..-''  '--'------------'--'  ''-.._      ",
      "      hhhhhh  SSSSSSSSSSSSSSSSSSSS  hhhhhh      " ),
    ( "    .' / \\      (o)          (o)      / \\ '.    ",
      "    c  c c      ggg          ggg      c c  c    " ),
    ( "   /  /   \\    / |            | \\    /   \\  \\   ",
      "   C  c   c   S  S            S  S   c   c  C   " ),
    ( "  /  /  .-'\\  |  |   .----.   |  |  /'-.  \\  \\  ",
      "  C  c SSSss  S  s  SssssssS  s  S  ssSSS c  C  " ),
    ( " |  |  / [=]\\ |  |  /  ||  \\  |  | /[=] \\  |  | ",
      " C  c S  sdsS S  s S s bb s S s  S Ssd  S c  C " ),
    ( " |  | | [===]||  | | : || : | |  ||[===] | |  | ",
      " C  c S sdddsSS  s S d bb d S s  SSsddd S c  C " ),
    ( " |  | | [===]||  | | : || : | |  ||[===] | |  | ",
      " C  c S sdddsSS  s S d bb d S s  SSsddd S c  C " ),
    ( " |  |  \\ [=]/ \\  |  \\  ||  /  |  / \\[=] /  |  | ",
      " C  c   SsdsS  S s  S s bb s S  s  SsdsS  c  C " ),
    ( "  \\  \\  '---'  \\  \\  (  O  ) /  /   '---'  /  /  ",
      "  C  c  SSSSS   S S  (  g  ) S S    SSSSS  c  C  " ),
    ( "   \\  \\  \\ \\    '. \\.-'-#-.-/ .'    / /   /  /   ",
      "   C  c  c c     S SSSSSgSSSSS S    c c   c  C   " ),
    ( "    \\  \\  \\ \\     |===| | |===|    / /   /  /    ",
      "    C  c  c c     llllb B bllll    c c   c  C    " ),
    ( "     \\  \\  \\ \\   /    | | |    \\  / /   /  /     ",
      "     C  c  c c  S    db B bd    S c c   c  C     " ),
    ( "      \\  \\  \\ \\ |  /| | | | |\\  |/ /   /  /      ",
      "      C  c  c c S SsSdb B bdSsS S c c  c  C      " ),
    ( "       \\  \\  \\ '| | | | | | | | |' /  /  /       ",
      "       C  c  c  S s Sdb B bdS s S  c  c  C       " ),
    ( "        \\  \\  ' | | | | | | | | | '  /  /        ",
      "        C  c    S s Sdb B bdS s S    c  C        " ),
    ( "         \\  \\   | \\ | | | | | / |   /  /         ",
      "         C  c   S S Sdb B bdS S S   c  C         " ),
    ( "          \\  \\  |  '.'| | |'.'  |  /  /          ",
      "          C  c  S  Sssb B bssS  S  c  C          " ),
    ( "           \\  \\ |   /|| | ||\\   | /  /           ",
      "           C  c S  Ssdb B bdSs  S c  C           " ),
    ( "            \\  '|  | || | || |  |'  /            ",
      "            C   S  s db B bd s  S   C            " ),
    ( "             \\  |  | || | || |  |  /             ",
      "             C  S  s db B bd s  S  C             " ),
    ( "              '-|  | |\\ | /| |  |-'              ",
      "              hhS  s d\\ B /d s  Shh              " ),
    ( "                |  | | \\|/ | |  |                ",
      "                S  s S  B  S s  S                " ),
    ( "               (___|_|  v  |_|___)               ",
      "               SSSSSSS  B  SSSSSSS               " ),
    ( "             .---------------------.             ",
      "             sssssssssssssssssssssss             " ),
    ( "            '-----------------------'            ",
      "            sssssssssssssssssssssssss            " ),
]

# ==========================================
# SPRITE DATA 2: THE VANGUARD (COMBAT STANCE)
# ==========================================
VANGUARD_ROWS = [
    ( "                       ,~~~~~~.                 ",
      "                       rrrrrrrr                 " ),
    ( "                     .'  / / / \\         /\\     ",
      "                     rr  r r r r         BB     " ),
    ( "                   .'  / / / /  |       /  \\    ",
      "                   Rr  r r r r  r      / b  \\   " ),
    ( "                  /  / / / /   /       / /\\ \\   ",
      "                  R  r r r r   r      / / b\\ \\  " ),
    ( "                 |  / / / /   /        | || |   ",
      "                 R  r r r r   r        | || |   " ),
    ( "                .--'--\\_\\_\\_v--.       | || |   ",
      "                SSSSSSddddddSSSS       | || |   " ),
    ( "               /  .------------.  \\    | || |   ",
      "               S  SssssssssssssS  S    b BB b   " ),
    ( "              /  /  __________  \\  \\   | || |   ",
      "              S  S  dddddddddd  S  S   b BB b   " ),
    ( "             |  |  /  _    _  \\  |  |  | || |   ",
      "             S  s  d  S    S  d  s  S  b BB b   " ),
    ( "             |  | |  [|]  [|]  | |  |  | || |   ",
      "             S  s d  dSd  dSd  d s  S  b BB b   " ),
    ( "             |  | |  ===::===  | |  |  | || |   ",
      "             S  s d  dddddddd  d s  S  b BB b   " ),
    ( "             |  |  \\   ____   /  |  | .---#---. ",
      "             S  s  d   dddd   d  s  S SSSsgsSSS " ),
    ( "     .------. \\  \\  '-......-'  /  /  |___|___| ",
      "     SssssssS S  S  sdddddddds  S  S  SSSSSSSSS " ),
    ( "   .' /====\\ '. '--'------------'--'     | |    ",
      "   S SssssssS S SSSSSSSSSSSSSSSSSSSS     lll    " ),
    ( "  /  /| .. |\\  \\   (o)        /| [=]\\    ( O )  ",
      "  S  sS mm Ss  S   ggg       S SssssS    ( g )  " ),
    ( " |  | | :: | |  | / | \\      | |[===]|  / / \\ \\ ",
      " S  s S mm S s  S S s S      S SdddsS  S S   S S" ),
    ( " |  | | :: | |  | | |  \\     | | \\=/ / / /   \\ \\ ",
      " S  s S mm S s  S S s   S    S S  s / / /     c  " ),
    ( " |  | | :: | |  | | |   \\    |  \\___/ / /     \\ \\ ",
      " S  s S mm S s  S S s    S   S  Ssss / /       c  " ),
    ( " |  | | :: | |  | | |    \\   /|      / /       \\ \\ ",
      " S  s S mm S s  S S s     S S S     / /         C  " ),
    ( "  \\  \\| :: |/  /  | |     \\ | |     / /         \\ \\ ",
      "  S  sS mm Ss  S  S s      SS S    / /           C  " ),
    ( "   \\  '----'  /   | |      \\| |    / /           \\ \\ ",
      "   S   ssss   S   S s       S S   / /             C  " ),
    ( "    \\        /    | |       | |   / /             '-'",
      "     S      S     S s       S S  / /              hh " ),
    ( "     \\  /\\  /     \\ \\       / /  / /                ",
      "      S /\\ S       S s     s S  c c                 " ),
    ( "      \\/  \\/       '.\\_____/.'  / /                 ",
      "       v  v         SSSSSSSSS  c c                  " ),
    ( "        \\/          |===|===|  / /                  ",
      "        v           llllgllll c c                   " ),
    ( "                   /  _   _  \\/ /                   ",
      "                  S  S s S s  Sc                    " ),
    ( "                  |  / \\ / \\  |                     ",
      "                  S S   S   S S                     " ),
    ( "                  | |   |   | |                     ",
      "                  S s   S   s S                     " ),
    ( "                  | |   |   | |                     ",
      "                  S s   S   s S                     " ),
    ( "                 (___) (___)                        ",
      "                 SSSSS SSSSS                        " ),
]

# ==========================================
# SPRITE DATA 3: FIELD SPRITE (COMPACT 16x14)
# ==========================================
FIELD_ROWS = [
    ( "     ,~~~.    ", "     rrrrr    " ),
    ( "   .' / \\ '.  ", "   rr r r rr  " ),
    ( "  / .-----. \\ ", "  S SsssssS S " ),
    ( "  | | [=] | | ", "  S s ddd s S " ),
    ( "  | | === | | ", "  S s ddd s S " ),
    ( " .--'-----'--.", " hhhSSSSSSShhh" ),
    ( "/ / | === | \\ \\", "c c S sds S c c" ),
    ( "| | | ::: | | |", "c c S mmm S c c" ),
    ( "| | | ::: | | |", "c c S mmm S c c" ),
    ( " \\ \\| === |/ / ", "c c S sds S c c" ),
    ( "  \\ |#####| /  ", "  c SllgllS c  " ),
    ( "   \\| === |/   ", "   cS sss Sc   " ),
    ( "    | / \\ |    ", "    S S s S    " ),
    ( "    | | | |    ", "    S s S s    " ),
    ( "   (__) (__)   ", "   SSSS SSSS   " ),
]

def render_sprite(rows, title=""):
    t = Text()
    for art_row, col_row in rows:
        max_l = max(len(art_row), len(col_row))
        art_row = art_row.ljust(max_l)
        col_row = col_row.ljust(max_l)
        for ch, code in zip(art_row, col_row):
            info = PALETTE.get(code)
            if info:
                t.append(ch, style=info[0])
            else:
                t.append(ch)
        t.append("\n")
    return Panel(t, title=f"[bold white]{title}[/bold white]", border_style="dim")

def print_palette_table():
    table = Table(title="Character Material & Color Palette", border_style="blue")
    table.add_column("Code", justify="center", style="bold yellow")
    table.add_column("Material / Segment", style="white")
    table.add_column("Hex Color", style="bold")
    table.add_column("Swatch Preview", justify="center")

    for code, (hex_val, name) in PALETTE.items():
        swatch = f"[{hex_val}]########## ({code})[/{hex_val}]"
        table.add_row(f"'{code}'", name, f"[{hex_val}]{hex_val}[/{hex_val}]", swatch)
    return table

def main():
    console.print()
    console.rule("[bold red]=== ASCII KNIGHT CHARACTER SPECIFICATION & VISUAL WORKBENCH ===[/bold red]")
    console.print()
    
    console.print(print_palette_table())
    console.print()

    console.print(render_sprite(SENTINEL_ROWS, "Variation 1: The Iron Sentinel (Planted Greatsword, High-Density Hero Sprite)"))
    console.print()

    console.print(render_sprite(VANGUARD_ROWS, "Variation 2: The Vanguard (Combat Dueling Stance - Longsword & Heater Shield)"))
    console.print()

    console.print(render_sprite(FIELD_ROWS, "Variation 3: The Field Explorer (Compact 14x16 Grid Sprite)"))
    console.print()
    
    console.rule("[bold green]=== Render completed successfully ===[/bold green]")

if __name__ == "__main__":
    main()
