"""Generates every texture for the Uranium Ore mod. Pure stdlib PNG writer, no deps.

    python3 tools/gen_textures.py

The uranium palette is deliberately a saturated Factorio-style green; change the
URA_* constants below to retune the whole set at once.
"""
import math, os, struct, zlib

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "src", "main", "resources", "assets", "uraniummod")
N = 16

# ---------------------------------------------------------------- png writer
def write_png(path, px):
    h, w = len(px), len(px[0])
    for y, row in enumerate(px):
        assert len(row) == w, f"{path}: row {y} has {len(row)} px, expected {w}"
        for x, p in enumerate(row):
            assert len(p) == 4, f"{path}: pixel ({x},{y}) is {p}, expected RGBA"
    raw = b"".join(b"\x00" + bytes(c for p in row for c in p) for row in px)
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    blob = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(blob)
    print("wrote", os.path.relpath(path, RES))

# ---------------------------------------------------------------- helpers
class Rng:
    def __init__(s, seed):
        # scramble: sequential seeds otherwise give near-identical first draws
        h = (seed * 2654435761) & 0xffffffff
        h ^= h >> 15; h = (h * 2246822519) & 0xffffffff
        h ^= h >> 13; h = (h * 3266489917) & 0xffffffff
        s.s = h ^ (h >> 16)
    def next(s): s.s = (s.s * 1664525 + 1013904223) & 0xffffffff; return s.s
    def f(s): return s.next() / 0xffffffff

def blur(g, passes):
    n = len(g)
    for _ in range(passes):
        o = [[0.0] * n for _ in range(n)]
        for y in range(n):
            for x in range(n):
                o[y][x] = sum(g[(y + dy) % n][(x + dx) % n]
                              for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0
        g = o
    return g

def noise(seed, passes=2, n=N):
    r = Rng(seed)
    g = blur([[r.f() for _ in range(n)] for _ in range(n)], passes)
    lo = min(map(min, g)); hi = max(map(max, g)); sp = (hi - lo) or 1.0
    return [[(v - lo) / sp for v in row] for row in g]

cl = lambda v: 0 if v < 0 else (255 if v > 255 else int(v))
def sh(c, a): return (cl(c[0] + a), cl(c[1] + a), cl(c[2] + a), 255)
def mix(a, b, t):
    t = min(1.0, max(0.0, t))
    return (cl(a[0] + (b[0] - a[0]) * t), cl(a[1] + (b[1] - a[1]) * t),
            cl(a[2] + (b[2] - a[2]) * t), 255)
def q(c, s=6): return (cl(round(c[0] / s) * s), cl(round(c[1] / s) * s),
                       cl(round(c[2] / s) * s), 255)
def wd(a, b, n=N):
    d = abs(a - b); return min(d, n - d)

# ---------------------------------------------------------------- palettes
# uranium: saturated green crystal
URA_O = (16, 44, 16, 255)      # outline / deepest shadow
URA_D = (34, 88, 32, 255)      # dark facet
URA_M = (56, 146, 50, 255)     # mid facet
URA_L = (94, 202, 80, 255)     # lit facet
URA_B = (140, 236, 120, 255)   # bright rim
URA_S = (205, 255, 190, 255)   # specular

# machine casing
MET_O = (34, 36, 40, 255)
MET_D = (66, 70, 78, 255)
MET_M = (104, 110, 120, 255)
MET_L = (146, 153, 164, 255)
MET_H = (186, 193, 204, 255)

PAL = {"o": URA_O, "d": URA_D, "m": URA_M, "l": URA_L, "b": URA_B, "s": URA_S}

# ---------------------------------------------------------------- ore blocks
ORE_MASK = [
    "................",
    "....ooo.........",
    "...ooooo....oo..",
    "...oooo....oooo.",
    "....oo.....oooo.",
    "...........ooo..",
    ".....oo.........",
    "....oooo........",
    "...oooooo.......",
    "....oooo....oo..",
    ".....oo....oooo.",
    "..........ooooo.",
    "...........ooo..",
    "..oo............",
    ".oooo...........",
    "..ooo...........",
]
is_ore = lambda x, y: ORE_MASK[y % N][x % N] == "o"

def stone_base(seed, base, spread, tint=(0, 0, 0)):
    blotch = noise(seed, passes=2)
    grain = Rng(seed + 31337)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            v = (blotch[y][x] - 0.5) * 2.0 * spread + (grain.f() - 0.5) * 14
            row.append(q((cl(base + v + tint[0]), cl(base + v + tint[1]),
                          cl(base + v + tint[2]), 255)))
        px.append(row)
    return px

def make_ore(path, seed, base, spread, tint=(0, 0, 0)):
    px = stone_base(seed, base, spread, tint)
    nz = noise(seed + 977, passes=1)
    for y in range(N):
        for x in range(N):
            if is_ore(x, y):
                continue
            if any(is_ore(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[y][x] = sh(px[y][x], -18)
    for y in range(N):
        for x in range(N):
            if not is_ore(x, y):
                continue
            above = y > 0 and is_ore(x, y - 1)
            below = y < N - 1 and is_ore(x, y + 1)
            left = x > 0 and is_ore(x - 1, y)
            c = URA_B if (not above or not left) else (URA_D if not below else URA_M)
            px[y][x] = q(sh(c, int((nz[y][x] - 0.5) * 22)))
    write_png(path, px)

# ---------------------------------------------------------------- raw uranium
# A faceted hexagonal crystal, drawn by hand so it reads at 16px.
RAW_ART = [
    "................",
    "................",
    ".....ooooo......",
    "....obbbbbo.....",
    "...oblllllbo....",
    "..obllllllbo....",
    "..olllllllllo...",
    ".odmmmmmmmmmdo..",
    ".odmmmmmmmmmdo..",
    ".oddmmmmmmmddo..",
    "..oddmmmmmddo...",
    "...oddddddddo...",
    "....oooooooo....",
    "................",
    "................",
    "................",
]
RAW_SPEC = {(5, 4), (6, 4), (4, 5), (5, 5)}

def make_raw_uranium(path, seed=5):
    r = Rng(seed)
    px = [[(0, 0, 0, 0) for _ in range(N)] for _ in range(N)]
    for y in range(N):
        for x in range(N):
            ch = RAW_ART[y][x]
            if ch == ".":
                continue
            # right-hand facet: the lit face turns over past x=9
            if ch == "l" and x >= 9:
                ch = "m"
            if (x, y) in RAW_SPEC:
                ch = "s"
            c = PAL[ch]
            if ch != "o":
                c = sh(c, int((r.f() - 0.5) * 10))
            px[y][x] = q(c)
    write_png(path, px)

# ---------------------------------------------------------------- ingot
INGOT_MASK = [
    "................", "................", "................", "................",
    "......xxxxxxx...", ".....xxxxxxxxx..", "....xxxxxxxxxx..", "...xxxxxxxxxx...",
    "..xxxxxxxxxx....", "..xxxxxxxxx.....", "..xxxxxxxx......", "...xxxxxx.......",
    "................", "................", "................", "................",
]
inside = lambda m, x, y: 0 <= x < N and 0 <= y < N and m[y][x] == "x"

def make_ingot(path, seed=6):
    r = Rng(seed)
    px = [[(0, 0, 0, 0) for _ in range(N)] for _ in range(N)]
    for y in range(N):
        for x in range(N):
            if not inside(INGOT_MASK, x, y):
                if any(inside(INGOT_MASK, x + dx, y + dy)
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    px[y][x] = URA_O
                continue
            s = x + y                       # runs across the ingot's thickness
            if s <= 12:   c = URA_B
            elif s <= 14: c = URA_L
            elif s <= 17: c = URA_M
            elif s <= 19: c = mix(URA_M, URA_D, 0.6)
            else:         c = URA_D
            if not inside(INGOT_MASK, x, y + 1) or not inside(INGOT_MASK, x + 1, y):
                c = mix(c, URA_O, 0.4)
            if not inside(INGOT_MASK, x, y - 1):
                c = mix(c, URA_S, 0.55)
            px[y][x] = q(sh(c, int((r.f() - 0.5) * 8)))
    write_png(path, px)

# ---------------------------------------------------------------- storage blocks
CHUNKS = [(3.4, 3.2, 3.5), (11.2, 2.8, 3.2), (7.6, 9.4, 3.6),
          (13.6, 10.2, 3.0), (2.4, 12.4, 3.1), (14.6, 15.4, 2.6)]

def make_raw_block(path, seed=3):
    """Packed crystal chunks with dark seams."""
    r = Rng(seed)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            bd, off, rad = 1e9, None, None
            for (cx, cy, rr) in CHUNKS:
                d = math.hypot(wd(x + 0.5, cx), wd(y + 0.5, cy)) / rr
                if d < bd: bd, off, rad = d, (x + 0.5 - cx, y + 0.5 - cy), rr
            if bd >= 1.0:    c = URA_O
            elif bd > 0.80:  c = URA_D
            else:
                lit = (-off[0] - off[1]) / (rad * 1.6)
                c = URA_B if lit > 0.42 else (URA_L if lit > 0.05 else
                                              (URA_M if lit > -0.32 else URA_D))
            row.append(q(sh(c, int((r.f() - 0.5) * 10))))
        px.append(row)
    write_png(path, px)

def make_metal_block(path, seed=4):
    """Refined metal: flat brushed streaks, tiles seamlessly."""
    r = Rng(seed)
    rows = [Rng(seed * 7919 + y * 104729).f() for y in range(N)]
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            v = rows[y] + (r.f() - 0.5) * 0.22
            c = (URA_D if v < 0.26 else URA_M if v < 0.60 else
                 URA_L if v < 0.86 else URA_B)
            row.append(q(c))
        px.append(row)
    write_png(path, px)

# ---------------------------------------------------------------- centrifuge
def bevel(px, lo, hi):
    """Plate edge: lighter top/left, darker bottom/right."""
    for i in range(N):
        px[0][i] = hi; px[i][0] = hi
        px[N - 1][i] = lo; px[i][N - 1] = lo
    px[0][N - 1] = MET_M; px[N - 1][0] = MET_M

def rivets(px, col=MET_H, shadow=MET_D):
    for (rx, ry) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        px[ry][rx] = col
        px[ry + 1][rx] = shadow

def plate(seed):
    r = Rng(seed)
    px = [[q(sh(MET_M, int((r.f() - 0.5) * 14))) for _ in range(N)] for _ in range(N)]
    bevel(px, MET_D, MET_L)
    return px

def make_centrifuge_side(path, seed=41):
    px = plate(seed)
    for y in range(5, 12):                      # vent slots
        for x in (5, 6, 9, 10):
            px[y][x] = MET_D if x in (5, 9) else MET_O
    for x in range(4, 12):
        px[4][x] = MET_L
        px[12][x] = MET_D
    rivets(px)
    write_png(path, px)

def make_centrifuge_bottom(path, seed=42):
    px = plate(seed)
    rivets(px)
    write_png(path, px)

def make_centrifuge_top(path, seed=43):
    px = plate(seed)
    cx = cy = 7.5
    for y in range(N):
        for x in range(N):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d < 2.0:   px[y][x] = q(mix(URA_M, URA_L, 0.4))   # rotor core
            elif d < 3.0: px[y][x] = MET_O
            elif d < 4.2: px[y][x] = q(sh(MET_D, 6))
            elif d < 5.0: px[y][x] = MET_L
    rivets(px)
    write_png(path, px)

def make_centrifuge_front(path, on, seed=44):
    px = plate(seed)
    for y in range(4, 12):                      # recessed window
        for x in range(4, 12):
            px[y][x] = MET_O
    glow_a = URA_B if on else URA_D
    glow_b = URA_S if on else mix(URA_D, URA_O, 0.5)
    r = Rng(seed + (1 if on else 0))
    for y in range(5, 11):
        for x in range(5, 11):
            d = math.hypot(x - 7.5, y - 7.5)
            t = max(0.0, 1.0 - d / 3.4)
            c = mix(glow_a, glow_b, t)
            px[y][x] = q(sh(c, int((r.f() - 0.5) * (18 if on else 8))))
    for x in range(4, 12):                      # window frame
        px[3][x] = MET_L; px[12][x] = MET_D
    for y in range(4, 12):
        px[y][3] = MET_L; px[y][12] = MET_D
    rivets(px)
    write_png(path, px)

# ---------------------------------------------------------------- gui sheet
GW, GH = 256, 256
PANEL_W, PANEL_H = 176, 166
C_BG   = (198, 198, 198, 255)
C_HI   = (255, 255, 255, 255)
C_LO   = (85, 85, 85, 255)
C_SLOT = (139, 139, 139, 255)
C_SLOT_HI = (255, 255, 255, 255)
C_SLOT_LO = (55, 55, 55, 255)

HEAT_X, HEAT_Y, HEAT_W, HEAT_H = 26, 19, 14, 52
ARROW_X, ARROW_Y, ARROW_W, ARROW_H = 79, 34, 24, 17
THRESHOLD = 0.60                      # matches OPERATING_HEAT / MAX_HEAT in Java

def gui_slot(px, sx, sy):
    """Draw a standard 16x16 inventory slot with its 1px recessed border."""
    for y in range(sy, sy + 16):
        for x in range(sx, sx + 16):
            px[y][x] = C_SLOT
    for x in range(sx - 1, sx + 17):
        px[sy - 1][x] = C_SLOT_LO
        px[sy + 16][x] = C_SLOT_HI
    for y in range(sy - 1, sy + 17):
        px[y][sx - 1] = C_SLOT_LO
        px[y][sx + 16] = C_SLOT_HI
    px[sy - 1][sx + 16] = C_BG
    px[sy + 16][sx - 1] = C_BG

def heat_ramp(t):
    """0 = cold green, 1 = white-hot. Reads as 'warming up'."""
    if t < 0.5:  return mix(URA_D, URA_B, t / 0.5)
    if t < 0.8:  return mix(URA_B, (245, 226, 96, 255), (t - 0.5) / 0.3)
    return mix((245, 226, 96, 255), (255, 246, 214, 255), (t - 0.8) / 0.2)

def make_gui(path):
    px = [[(0, 0, 0, 0) for _ in range(GW)] for _ in range(GH)]
    for y in range(PANEL_H):
        for x in range(PANEL_W):
            px[y][x] = C_BG
    for x in range(PANEL_W):
        px[0][x] = C_HI; px[PANEL_H - 1][x] = C_LO
    for y in range(PANEL_H):
        px[y][0] = C_HI; px[y][PANEL_W - 1] = C_LO

    gui_slot(px, 56, 35)                                   # input
    gui_slot(px, 116, 35)                                  # output
    for row in range(3):                                   # player inventory
        for col in range(9):
            gui_slot(px, 8 + col * 18, 84 + row * 18)
    for col in range(9):                                   # hotbar
        gui_slot(px, 8 + col * 18, 142)

    # recessed heat gauge well
    for y in range(HEAT_Y, HEAT_Y + HEAT_H):
        for x in range(HEAT_X, HEAT_X + HEAT_W):
            px[y][x] = (58, 58, 58, 255)
    for x in range(HEAT_X - 1, HEAT_X + HEAT_W + 1):
        px[HEAT_Y - 1][x] = C_SLOT_LO
        px[HEAT_Y + HEAT_H][x] = C_SLOT_HI
    for y in range(HEAT_Y - 1, HEAT_Y + HEAT_H + 1):
        px[y][HEAT_X - 1] = C_SLOT_LO
        px[y][HEAT_X + HEAT_W] = C_SLOT_HI

    # threshold notch, so the player can see the heat they're waiting for
    ty = HEAT_Y + HEAT_H - int(HEAT_H * THRESHOLD)
    for x in range(HEAT_X + HEAT_W + 1, HEAT_X + HEAT_W + 4):
        px[ty][x] = (60, 60, 60, 255)
    px[ty - 1][HEAT_X + HEAT_W + 1] = (140, 140, 140, 255)
    px[ty + 1][HEAT_X + HEAT_W + 1] = (140, 140, 140, 255)

    # empty progress arrow, drawn dim into the panel
    def arrow(ox, oy, fill, outline):
        for i in range(ARROW_H):
            half = abs(i - 8)
            if i < 3 or i > 13:
                continue
            if 5 <= i <= 11:
                span = range(0, 16)
            else:
                span = range(0, 16)
            for j in span:
                px[oy + i][ox + j] = fill
        for i in range(ARROW_H):                     # head
            half = abs(i - 8)
            w = 8 - half
            if w <= 0:
                continue
            for j in range(16, 16 + w):
                if j < ARROW_W:
                    px[oy + i][ox + j] = fill
    arrow(ARROW_X, ARROW_Y, (172, 172, 172, 255), None)

    # ---- overlay sprites, sampled by the screen at draw time ----
    # filled progress arrow at (176, 0)
    for i in range(ARROW_H):
        for j in range(ARROW_W):
            px[i][176 + j] = (0, 0, 0, 0)
    def filled(ox, oy, col):
        for i in range(3, 14):
            for j in range(0, 16):
                px[oy + i][ox + j] = col
        for i in range(ARROW_H):
            w = 8 - abs(i - 8)
            for j in range(16, 16 + max(0, w)):
                if j < ARROW_W:
                    px[oy + i][ox + j] = col
    filled(176, 0, (126, 226, 106, 255))

    # heat fill at (200, 0), 14 x 52, bottom of the sprite = cold
    for i in range(HEAT_H):
        t = (HEAT_H - 1 - i) / (HEAT_H - 1)
        c = heat_ramp(t)
        for j in range(HEAT_W):
            edge = 0.75 if (j == 0 or j == HEAT_W - 1) else 1.0
            px[i][200 + j] = (cl(c[0] * edge), cl(c[1] * edge), cl(c[2] * edge), 255)
    write_png(path, px)

# ---------------------------------------------------------------- run
def upscale(px, f):
    return [[px[y // f][x // f] for x in range(len(px[0]) * f)]
            for y in range(len(px) * f)]

make_ore(f"{RES}/textures/block/uranium_ore.png", 20240001, 128, 20)
make_ore(f"{RES}/textures/block/deepslate_uranium_ore.png", 20240002, 84, 15, tint=(-2, -2, 5))
make_raw_block(f"{RES}/textures/block/raw_uranium_block.png")
make_metal_block(f"{RES}/textures/block/uranium_block.png")
make_raw_uranium(f"{RES}/textures/item/raw_uranium.png")
make_ingot(f"{RES}/textures/item/uranium_ingot.png")

make_centrifuge_side(f"{RES}/textures/block/centrifuge_side.png")
make_centrifuge_top(f"{RES}/textures/block/centrifuge_top.png")
make_centrifuge_bottom(f"{RES}/textures/block/centrifuge_bottom.png")
make_centrifuge_front(f"{RES}/textures/block/centrifuge_front.png", on=False)
make_centrifuge_front(f"{RES}/textures/block/centrifuge_front_on.png", on=True)
make_gui(f"{RES}/textures/gui/centrifuge.png")

_cap = []
_real = write_png
write_png = lambda p, px: _cap.append(px)
make_raw_uranium("mem")
write_png = _real
write_png(f"{RES}/icon.png", upscale(_cap[0], 8))
