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

def in_poly(px_, py_, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > py_) != (y1 > py_):
            if px_ < x0 + (py_ - y0) * (x1 - x0) / (y1 - y0):
                inside = not inside
    return inside

def round_corners(px):
    """Drop pixels sticking out on two sides, so the silhouette reads as cast."""
    out = [row[:] for row in px]
    for y in range(N):
        for x in range(N):
            if not px[y][x][3]:
                continue
            empty = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if not (0 <= x + dx < N and 0 <= y + dy < N and px[y + dy][x + dx][3]))
            if empty >= 2:
                out[y][x] = (0, 0, 0, 0)
    return out

def outline_shape(px, col):
    out = [row[:] for row in px]
    for y in range(N):
        for x in range(N):
            if px[y][x][3]:
                continue
            if any(0 <= x + dx < N and 0 <= y + dy < N and px[y + dy][x + dx][3]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = col
    return out

# Classic ingot lozenge, tilted low-left to high-right, with mottled green
# casting and bright highlight streaks along the top face.
INGOT_ART = [
    "................",
    "................",
    ".........xxx....",
    "......xxxxxxxx..",
    "....xxxxxxxxxxx.",
    "...xxxxxxxxxxxx.",
    "..xxxxxxxxxxxxx.",
    ".xxxxxxxxxxxxx..",
    ".xxxxxxxxxxxx...",
    ".xxxxxxxxxxx....",
    "..xxxxxxxxx.....",
    "...xxxxxx.......",
    "....xxx.........",
    "................",
    "................",
    "................",
]

# pale and white glints, running with the long axis of the bar
INGOT_PALE = [(3, 6), (4, 6), (5, 9), (6, 9), (9, 4), (10, 4), (11, 4),
              (3, 8), (7, 8), (12, 5)]
INGOT_WHITE = [(4, 7), (5, 7), (6, 6), (7, 6), (9, 5), (10, 5), (11, 5)]

URA_PALE = (186, 226, 128, 255)
URA_WHITE = (243, 255, 236, 255)

def make_ingot(path, seed=6):
    solid = lambda x, y: (0 <= x < N and 0 <= y < N and INGOT_ART[y][x] == "x")
    nz = noise(seed + 5, passes=1)
    grain = noise(seed + 91, passes=0)          # chunkier patches on top
    px = [[(0, 0, 0, 0) for _ in range(N)] for _ in range(N)]

    for y in range(N):
        for x in range(N):
            if not solid(x, y):
                continue
            # lit from the upper left, roughened so the casting looks mottled
            grad = 1.0 - ((x / 15.0) * 0.42 + (y / 15.0) * 0.58)
            v = grad * 0.55 + nz[y][x] * 0.28 + grain[y][x] * 0.17
            if v < 0.20:
                c = mix(URA_O, URA_D, 0.55)
            elif v < 0.32:
                c = URA_D
            elif v < 0.44:
                c = mix(URA_D, URA_M, 0.6)
            elif v < 0.55:
                c = URA_M
            elif v < 0.65:
                c = mix(URA_M, URA_L, 0.6)
            elif v < 0.76:
                c = URA_L
            elif v < 0.86:
                c = mix(URA_L, URA_PALE, 0.5)
            else:
                c = URA_PALE
            if not solid(x, y + 1) or not solid(x + 1, y):
                c = mix(c, URA_D, 0.55)          # shaded underside
            px[y][x] = q(c)

    for (gx, gy) in INGOT_PALE:
        if solid(gx, gy):
            px[gy][gx] = q(URA_PALE)
    for (gx, gy) in INGOT_WHITE:
        if solid(gx, gy):
            px[gy][gx] = URA_WHITE

    for y in range(N):                            # dark rim
        for x in range(N):
            if solid(x, y) or px[y][x][3]:
                continue
            if any(solid(x + dx, y + dy)
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[y][x] = URA_O
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
# Modelled on Factorio's centrifuge: three cream enrichment drums with green
# uranium showing through, dark caps, gold arms, on a hazard-striped plinth.
MET_O = (26, 27, 30, 255)
MET_D = (56, 58, 63, 255)
MET_M = (94, 98, 105, 255)
MET_L = (136, 141, 150, 255)
MET_H = (178, 184, 194, 255)

AMB_D = (128, 68, 10, 255)
AMB_M = (206, 122, 22, 255)
AMB_L = (255, 166, 46, 255)
AMB_H = (255, 216, 136, 255)

GOLD_D = (122, 88, 16, 255)
GOLD_M = (196, 152, 32, 255)
GOLD_L = (238, 202, 74, 255)
GOLD_H = (255, 238, 160, 255)

CREAM_H = (236, 234, 222, 255)
CREAM_L = (208, 206, 193, 255)
CREAM_M = (170, 169, 158, 255)
CREAM_D = (120, 120, 112, 255)
CREAM_O = (78, 79, 74, 255)

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

def bolts(px, coords=((2, 2), (13, 2), (2, 13), (13, 13))):
    for (bx, by) in coords:
        px[by][bx] = MET_H
        if by + 1 < N:
            px[by + 1][bx] = MET_O

def cylinder_shade(x, lit, mid, dark, edge):
    """Left-to-right falloff that makes a flat face read as a round drum."""
    t = abs(x + 0.5 - 8.0) / 8.0
    if t < 0.28:
        return mix(lit, mid, t / 0.28)
    if t < 0.72:
        return mix(mid, dark, (t - 0.28) / 0.44)
    return mix(dark, edge, (t - 0.72) / 0.28)

# green uranium showing through the drum casing
DRUM_SPOTS = [(3, 5), (6, 4), (10, 5), (12, 7), (4, 9), (8, 8),
              (11, 11), (5, 12), (9, 13), (2, 8), (13, 10), (7, 11)]

def _drum(seed, glow):
    """glow: 0 = inert, 1 = fully lit. Body texture for one enrichment drum."""
    r = Rng(seed)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            c = cylinder_shade(x, CREAM_H, CREAM_L, CREAM_M, CREAM_D)
            row.append(q(sh(c, int((r.f() - 0.5) * 8))))
        px.append(row)
    for y in (0, 1, 14, 15):                              # steel rings
        for x in range(N):
            base = MET_L if y in (0, 14) else MET_D
            px[y][x] = q(mix(base, MET_O, abs(x + 0.5 - 8.0) / 16.0))
    for (sx, sy) in DRUM_SPOTS:                           # uranium showing through
        dim = mix(URA_D, URA_M, 0.5)
        bright = mix(URA_B, URA_S, 0.35)
        c = mix(dim, bright, glow)
        shade = 1.0 - abs(sx + 0.5 - 8.0) / 22.0          # keep the round falloff
        c = (cl(c[0] * shade), cl(c[1] * shade), cl(c[2] * shade), 255)
        px[sy][sx] = q(c)
        if sx + 1 < N:
            px[sy][sx + 1] = q(mix(c, CREAM_M, 0.45))
        if sy + 1 < 14:
            px[sy + 1][sx] = q(mix(c, CREAM_M, 0.55))
    return px

def make_drum(path, seed=61):
    write_png(path, _drum(seed, 0.15))

def make_drum_still(path, seed=61):
    """Peak-glow single frame: the renderer binds textures directly, and only
    atlas sprites animate, so the moving drums need a still lit variant."""
    write_png(path, _drum(seed, 1.0))

def make_drum_top_still(path, seed=63):
    write_png(path, _drum_top(seed, 1.0))


def make_drum_cap(path, seed=62):
    """Dark collar around the top of a drum."""
    px = []
    r = Rng(seed)
    for y in range(N):
        row = []
        for x in range(N):
            c = cylinder_shade(x, MET_L, MET_M, MET_D, MET_O)
            row.append(q(sh(c, int((r.f() - 0.5) * 8))))
        px.append(row)
    for x in range(N):
        px[0][x] = q(mix(MET_H, MET_M, abs(x + 0.5 - 8.0) / 12.0))
        px[3][x] = q(mix(GOLD_M, GOLD_D, abs(x + 0.5 - 8.0) / 10.0))
        px[N - 1][x] = MET_O
    for x in range(1, N, 4):                              # collar bolts
        px[6][x] = MET_H
        px[7][x] = MET_O
    write_png(path, px)

def _drum_top(seed, glow):
    """Looking down on a drum: a rimmed port with the charge inside."""
    px = plate(seed, MET_D, 8)
    for y in range(N):
        for x in range(N):
            d = math.hypot(x + 0.5 - 8.0, y + 0.5 - 8.0)
            if d > 7.4:
                continue
            if d > 6.4:
                px[y][x] = MET_L
            elif d > 5.6:
                px[y][x] = MET_O
            elif d > 3.2:
                px[y][x] = q(mix(MET_M, MET_D, (d - 3.2) / 2.4))
            elif d > 2.4:
                px[y][x] = MET_O
            else:
                hot = mix(URA_S, URA_B, d / 2.4)
                cold = mix(URA_D, URA_O, d / 2.4)
                px[y][x] = q(mix(cold, hot, glow))
    for (bx, by) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        px[by][bx] = MET_H
    return px

def make_drum_top(path, seed=63):
    write_png(path, _drum_top(seed, 0.12))


def make_deck(path, seed=64):
    """Plinth top: tread plate the drums stand on."""
    px = plate(seed, MET_D, 10)
    for y in range(2, N, 4):
        for x in range(N):
            px[y][x] = q(sh(MET_M, -6))
            if x % 2 == 0 and y + 1 < N:
                px[y + 1][x] = MET_O
    frame_edges(px, MET_M, MET_O)
    write_png(path, px)

def make_base(path, seed=45):
    """Plinth skirt: amber/black hazard stripes."""
    r = Rng(seed)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            c = AMB_M if ((x + y) // 3) % 2 == 0 else MET_O
            row.append(q(sh(c, int((r.f() - 0.5) * 12))))
        px.append(row)
    for i in range(N):
        px[0][i] = MET_L
        px[1][i] = MET_D
        px[N - 1][i] = MET_O
        px[N - 2][i] = MET_D
    write_png(path, px)

def make_bottom(path, seed=42):
    px = plate(seed, MET_D, 10)
    frame_edges(px, MET_M, MET_O)
    bolts(px)
    write_png(path, px)

def make_arm(path, seed=65):
    """Gold hydraulic arm, shaded round across its width."""
    r = Rng(seed)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            c = cylinder_shade(x, GOLD_H, GOLD_L, GOLD_M, GOLD_D)
            row.append(q(sh(c, int((r.f() - 0.5) * 8))))
        px.append(row)
    for y in (2, 7, 12):                                  # segment collars
        for x in range(N):
            px[y][x] = q(mix(MET_D, MET_O, abs(x + 0.5 - 8.0) / 12.0))
    write_png(path, px)

def make_pipe(path, seed=66):
    px = []
    r = Rng(seed)
    for y in range(N):
        row = []
        for x in range(N):
            c = cylinder_shade(x, MET_L, MET_M, MET_D, MET_O)
            row.append(q(sh(c, int((r.f() - 0.5) * 6))))
        px.append(row)
    for y in range(0, N, 3):                              # corrugations
        for x in range(N):
            px[y][x] = q(sh(px[y][x], -22))
    write_png(path, px)


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
make_drum(f"{B}/centrifuge_drum.png")
make_drum_cap(f"{B}/centrifuge_cap.png")
make_drum_top(f"{B}/centrifuge_drum_top.png")
make_drum_still(f"{B}/centrifuge_drum_on_still.png")
make_drum_top_still(f"{B}/centrifuge_drum_top_on_still.png")
make_deck(f"{B}/centrifuge_deck.png")
make_base(f"{B}/centrifuge_base.png")
make_bottom(f"{B}/centrifuge_bottom.png")
make_arm(f"{B}/centrifuge_arm.png")
make_pipe(f"{B}/centrifuge_pipe.png")


make_gui(f"{RES}/textures/gui/centrifuge.png")

_cap = []
_real = write_png
write_png = lambda p, px: _cap.append(px)
make_raw_uranium("mem")
write_png = _real
write_png(f"{RES}/icon.png", upscale(_cap[0], 8))
