"""Generates every texture for the Uranium Ore mod. Pure stdlib PNG writer, no deps.

    python3 tools/gen_textures.py

The uranium palette is deliberately a saturated Factorio-style green; change the
URA_* constants below to retune the whole set at once.
"""
import json, math, os, struct, zlib

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
# Dark machine casing with amber hazard accents. The glow stays uranium-green:
# that light is the material being refined, not part of the machine's livery.
MET_O = (26, 27, 30, 255)
MET_D = (56, 58, 63, 255)
MET_M = (94, 98, 105, 255)
MET_L = (136, 141, 150, 255)
MET_H = (178, 184, 194, 255)

AMB_D = (128, 68, 10, 255)
AMB_M = (206, 122, 22, 255)
AMB_L = (255, 166, 46, 255)
AMB_H = (255, 216, 136, 255)

TAU = math.pi * 2.0

def plate(seed, base=MET_M, spread=12):
    r = Rng(seed)
    return [[q(sh(base, int((r.f() - 0.5) * spread))) for _ in range(N)] for _ in range(N)]

def frame_edges(px, hi=MET_L, lo=MET_D):
    for i in range(N):
        px[0][i] = hi
        px[i][0] = hi
        px[N - 1][i] = lo
        px[i][N - 1] = lo
    px[0][N - 1] = MET_M
    px[N - 1][0] = MET_M

def bolts(px, coords=((2, 2), (13, 2), (2, 13), (13, 13))):
    for (bx, by) in coords:
        px[by][bx] = MET_H
        if by + 1 < N:
            px[by + 1][bx] = MET_O

def make_centrifuge_bottom(path, seed=42):
    px = plate(seed, MET_D, 10)
    frame_edges(px, MET_M, MET_O)
    bolts(px)
    write_png(path, px)

def make_centrifuge_base(path, seed=45):
    """Plinth skirt: amber/black hazard stripes."""
    r = Rng(seed)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            band = ((x + y) // 3) % 2
            c = AMB_M if band == 0 else MET_O
            row.append(q(sh(c, int((r.f() - 0.5) * 12))))
        px.append(row)
    for i in range(N):                       # capping rails top and bottom
        px[0][i] = MET_L
        px[1][i] = MET_D
        px[N - 1][i] = MET_O
        px[N - 2][i] = MET_D
    write_png(path, px)

def make_centrifuge_post(path, seed=46):
    """Corner column: a bolted strut with a lit edge."""
    px = plate(seed, MET_D, 10)
    for y in range(N):
        px[y][0] = MET_L
        px[y][1] = MET_M
        px[y][N - 1] = MET_O
        px[y][N - 2] = MET_D
    for y in (2, 7, 12):
        px[y][4] = MET_H
        px[y + 1][4] = MET_O
        px[y][11] = MET_H
        px[y + 1][11] = MET_O
    write_png(path, px)

def make_centrifuge_collar(path, seed=47):
    """Housing band under the rotor: vent slits between amber rails."""
    px = plate(seed, MET_M, 12)
    for i in range(N):
        px[0][i] = MET_H
        px[1][i] = AMB_M
        px[N - 1][i] = MET_O
        px[N - 2][i] = MET_D
    for x in range(2, 14, 3):
        for y in range(4, 12):
            px[y][x] = MET_O
            px[y][x + 1] = MET_D
    write_png(path, px)

def _side_base(seed):
    px = plate(seed, MET_M, 12)
    frame_edges(px)
    for y in range(4, 12):                   # recessed service panel
        for x in range(3, 13):
            px[y][x] = q(sh(MET_D, 4))
    for x in range(3, 13):
        px[3][x] = MET_O
        px[12][x] = MET_H
    for y in range(3, 13):
        px[y][2] = MET_O
        px[y][13] = MET_H
    for x in range(4, 12, 2):                # louvre slits
        for y in range(6, 10):
            px[y][x] = MET_O
    bolts(px)
    return px

def make_centrifuge_side(path, seed=41):
    px = _side_base(seed)
    px[5][11] = MET_O                        # status lamp, dark
    write_png(path, px)

def make_centrifuge_side_on(path, frames=4, seed=41):
    """Status lamp blinks while running."""
    out = []
    for f in range(frames):
        px = _side_base(seed)
        lit = f % frames
        glow = [URA_B, URA_L, URA_M, URA_L][lit]
        px[5][11] = glow
        px[4][11] = q(mix(MET_D, glow, 0.45))
        px[6][11] = q(mix(MET_D, glow, 0.45))
        out.extend(px)
    write_png(path, out)

def _front_base(seed):
    px = plate(seed, MET_M, 12)
    frame_edges(px)
    for x in range(2, 14):                   # amber bezel around the window
        px[2][x] = AMB_M
        px[13][x] = AMB_D
    for y in range(2, 14):
        px[y][2] = AMB_M
        px[y][13] = AMB_D
    for y in range(3, 13):
        for x in range(3, 13):
            px[y][x] = MET_O
    bolts(px)
    return px

def make_centrifuge_front(path, seed=44):
    px = _front_base(seed)
    r = Rng(seed + 7)
    for y in range(4, 12):                   # cold glass
        for x in range(4, 12):
            d = math.hypot(x - 7.5, y - 7.5)
            c = mix(URA_D, URA_O, min(1.0, d / 4.0))
            px[y][x] = q(sh(c, int((r.f() - 0.5) * 8)))
    write_png(path, px)

def make_centrifuge_front_on(path, frames=8, seed=44):
    """Window pulses as the charge spins up."""
    out = []
    for f in range(frames):
        px = _front_base(seed)
        r = Rng(seed + 100 + f)
        pulse = 0.55 + 0.45 * math.sin(TAU * f / frames)
        for y in range(4, 12):
            for x in range(4, 12):
                d = math.hypot(x - 7.5, y - 7.5)
                core = max(0.0, 1.0 - d / 4.2)
                t = min(1.0, core * (0.55 + 0.75 * pulse))
                c = mix(URA_D, URA_S, t)
                c = mix(c, URA_B, 0.35)
                px[y][x] = q(sh(c, int((r.f() - 0.5) * 12)))
        out.extend(px)
    write_png(path, out)

def _rotor_frame(theta, on, seed):
    """One frame of the turbine seen from above."""
    r = Rng(seed)
    px = plate(seed, MET_M, 10)
    frame_edges(px)
    bolts(px)
    for y in range(N):
        for x in range(N):
            dx, dy = x + 0.5 - 8.0, y + 0.5 - 8.0
            rad = math.hypot(dx, dy)
            if rad > 7.3:
                continue                                  # casing corners
            if rad > 6.3:
                px[y][x] = AMB_M if ((x + y) // 2) % 2 == 0 else MET_L
                continue
            if rad > 5.9:
                px[y][x] = MET_O
                continue
            if rad <= 1.7:                                # hub
                px[y][x] = MET_H if rad < 0.9 else MET_L
                continue
            ang = (math.atan2(dy, dx) + theta) % (TAU / 3.0)
            span = TAU / 3.0
            if ang < span * 0.34:
                c = MET_H if on else MET_L                # blade face
            elif ang < span * 0.44:
                c = MET_D                                 # blade edge
            else:
                c = mix(URA_M, URA_B, 0.4) if on else MET_O
            px[y][x] = q(sh(c, int((r.f() - 0.5) * 8)))
    return px

def make_centrifuge_top(path, seed=43):
    write_png(path, _rotor_frame(0.0, False, seed))

def make_centrifuge_top_on(path, frames=8, seed=43):
    out = []
    for f in range(frames):
        out.extend(_rotor_frame(TAU / 3.0 * f / frames, True, seed))
    write_png(path, out)

def write_mcmeta(path, frametime, interpolate=False):
    body = {"animation": {"frametime": frametime}}
    if interpolate:
        body["animation"]["interpolate"] = True
    with open(path, "w") as f:
        json.dump(body, f, indent=2)
        f.write("\n")
    print("wrote", os.path.relpath(path, RES))

# ---------------------------------------------------------------- gui sheet
GW, GH = 256, 256
PANEL_W, PANEL_H = 176, 166

# Factorio-ish console palette
P_BG    = (49, 48, 45, 255)
P_SUNK  = (36, 35, 33, 255)
P_RAISE = (66, 64, 60, 255)
P_HI    = (112, 109, 102, 255)
P_LO    = (22, 21, 20, 255)
SLOT_BG = (33, 32, 30, 255)

# The gauge is shortened to leave room for the numeric readout the screen
# draws underneath it. Keep these in step with CentrifugeScreen.
HEAT_X, HEAT_Y, HEAT_W, HEAT_H = 25, 20, 12, 38
ARROW_X, ARROW_Y, ARROW_W, ARROW_H = 86, 38, 16, 11
SHAFT_LEN, SHAFT_TOP, SHAFT_BOT = 10, 3, 8
THRESHOLD = 0.60          # keep in sync with OPERATING_HEAT / MAX_HEAT in Java

def rect(px, x0, y0, x1, y1, c):
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[y][x] = c

def bevel_rect(px, x0, y0, x1, y1, hi, lo):
    for x in range(x0, x1):
        px[y0][x] = hi
        px[y1 - 1][x] = lo
    for y in range(y0, y1):
        px[y][x0] = hi
        px[y][x1 - 1] = lo

def sunken(px, x0, y0, x1, y1, fill=P_SUNK):
    rect(px, x0, y0, x1, y1, fill)
    bevel_rect(px, x0, y0, x1, y1, P_LO, P_HI)

def machine_slot(px, sx, sy, accent=AMB_M):
    """16x16 slot with a dark well and an amber corner accent."""
    rect(px, sx, sy, sx + 16, sy + 16, SLOT_BG)
    for x in range(sx - 1, sx + 17):
        px[sy - 1][x] = P_LO
        px[sy + 16][x] = P_HI
    for y in range(sy - 1, sy + 17):
        px[y][sx - 1] = P_LO
        px[y][sx + 16] = P_HI
    for d in range(3):
        px[sy - 1][sx + d] = accent
        px[sy + d][sx - 1] = accent
        px[sy + 16][sx + 15 - d] = accent
        px[sy + 15 - d][sx + 16] = accent

def inv_slot(px, sx, sy):
    rect(px, sx, sy, sx + 16, sy + 16, SLOT_BG)
    for x in range(sx - 1, sx + 17):
        px[sy - 1][x] = P_LO
        px[sy + 16][x] = P_HI
    for y in range(sy - 1, sy + 17):
        px[y][sx - 1] = P_LO
        px[y][sx + 16] = P_HI

def heat_ramp(t):
    """0 = cold, 1 = white hot, through amber."""
    if t < 0.45:
        return mix(AMB_D, AMB_M, t / 0.45)
    if t < 0.80:
        return mix(AMB_M, AMB_L, (t - 0.45) / 0.35)
    return mix(AMB_L, AMB_H, (t - 0.80) / 0.20)

def make_gui(path):
    px = [[(0, 0, 0, 0) for _ in range(GW)] for _ in range(GH)]
    rect(px, 0, 0, PANEL_W, PANEL_H, P_BG)
    bevel_rect(px, 0, 0, PANEL_W, PANEL_H, P_HI, P_LO)

    # title bar with an amber rule under it
    rect(px, 4, 4, PANEL_W - 4, 15, P_RAISE)
    bevel_rect(px, 4, 4, PANEL_W - 4, 15, P_HI, P_LO)
    rect(px, 5, 15, PANEL_W - 5, 16, AMB_M)

    # recessed machine bay
    sunken(px, 6, 18, PANEL_W - 6, 70)

    machine_slot(px, 56, 35)
    machine_slot(px, 116, 35)
    for row in range(3):
        for col in range(9):
            inv_slot(px, 8 + col * 18, 84 + row * 18)
    for col in range(9):
        inv_slot(px, 8 + col * 18, 142)

    # heat gauge well
    sunken(px, HEAT_X, HEAT_Y, HEAT_X + HEAT_W, HEAT_Y + HEAT_H, (20, 19, 18, 255))
    for i in range(1, 5):                                   # tick marks
        ty = HEAT_Y + HEAT_H - int(HEAT_H * i / 5.0)
        for x in range(HEAT_X + HEAT_W, HEAT_X + HEAT_W + 2):
            px[ty][x] = (96, 93, 87, 255)
    # threshold marker: the temperature the player is waiting for
    ty = HEAT_Y + HEAT_H - int(HEAT_H * THRESHOLD)
    for k in range(4):
        for d in range(k + 1):
            yy = ty - d
            if HEAT_Y <= yy < HEAT_Y + HEAT_H + 2:
                px[yy][HEAT_X + HEAT_W + 1 + k] = AMB_L
            yy = ty + d
            if HEAT_Y <= yy < HEAT_Y + HEAT_H + 2:
                px[yy][HEAT_X + HEAT_W + 1 + k] = AMB_L
    for x in range(HEAT_X, HEAT_X + HEAT_W):                # dashed line at threshold
        if (x - HEAT_X) % 2 == 0:
            px[ty][x] = AMB_D

    # empty progress arrow, etched into the bay
    def draw_arrow(ox, oy, col):
        mid = ARROW_H // 2
        for i in range(SHAFT_TOP, SHAFT_BOT):               # shaft
            for j in range(SHAFT_LEN):
                px[oy + i][ox + j] = col
        for i in range(ARROW_H):                            # head
            w = (ARROW_W - SHAFT_LEN) - abs(i - mid)
            for j in range(SHAFT_LEN, min(ARROW_W, SHAFT_LEN + max(0, w))):
                px[oy + i][ox + j] = col

    draw_arrow(ARROW_X, ARROW_Y, (28, 27, 26, 255))

    # ---- overlay sprites sampled by the screen at draw time ----
    draw_arrow(176, 0, AMB_L)
    for i in range(ARROW_H):                                # brighten the leading edge
        w = (ARROW_W - SHAFT_LEN) - abs(i - ARROW_H // 2)
        j = SHAFT_LEN + max(0, w) - 1
        if SHAFT_LEN <= j < ARROW_W:
            px[i][176 + j] = AMB_H

    for i in range(HEAT_H):
        t = (HEAT_H - 1 - i) / (HEAT_H - 1)
        c = heat_ramp(t)
        for j in range(HEAT_W):
            edge = 0.72 if (j == 0 or j == HEAT_W - 1) else 1.0
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

B = f"{RES}/textures/block"
make_centrifuge_bottom(f"{B}/centrifuge_bottom.png")
make_centrifuge_base(f"{B}/centrifuge_base.png")
make_centrifuge_post(f"{B}/centrifuge_post.png")
make_centrifuge_collar(f"{B}/centrifuge_collar.png")
make_centrifuge_side(f"{B}/centrifuge_side.png")
make_centrifuge_side_on(f"{B}/centrifuge_side_on.png")
make_centrifuge_front(f"{B}/centrifuge_front.png")
make_centrifuge_front_on(f"{B}/centrifuge_front_on.png")
make_centrifuge_top(f"{B}/centrifuge_top.png")
make_centrifuge_top_on(f"{B}/centrifuge_top_on.png")

write_mcmeta(f"{B}/centrifuge_top_on.png.mcmeta", 2)
write_mcmeta(f"{B}/centrifuge_front_on.png.mcmeta", 3, interpolate=True)
write_mcmeta(f"{B}/centrifuge_side_on.png.mcmeta", 5, interpolate=True)

make_gui(f"{RES}/textures/gui/centrifuge.png")

_cap = []
_real = write_png
write_png = lambda p, px: _cap.append(px)
make_raw_uranium("mem")
write_png = _real
write_png(f"{RES}/icon.png", upscale(_cap[0], 8))
