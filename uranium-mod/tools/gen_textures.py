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
    """Stone with uranium crystals seated in it.

    Each crystal is lit from its own top-left corner rather than the texture's,
    so the cluster reads as separate faceted lumps instead of one flat blob, and
    the stone around it is shadowed so the crystals sit *in* the rock.
    """
    px = stone_base(seed, base, spread, tint)
    nz = noise(seed + 977, passes=1)

    for y in range(N):
        for x in range(N):
            if is_ore(x, y):
                continue
            touching = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if is_ore(x + dx, y + dy)]
            if touching:
                # deeper shadow where the crystal overhangs the stone
                deep = any(dx == -1 or dy == -1 for dx, dy in touching)
                px[y][x] = sh(px[y][x], -26 if deep else -14)

    for y in range(N):
        for x in range(N):
            if not is_ore(x, y):
                continue
            up = is_ore(x, y - 1)
            down = is_ore(x, y + 1)
            left = is_ore(x - 1, y)
            right = is_ore(x + 1, y)
            if not up and not left:
                c = mix(URA_B, URA_S, 0.45)             # lit corner
            elif not up or not left:
                c = URA_B
            elif not down or not right:
                c = URA_D                               # shaded underside
            else:
                c = URA_M if (x + y) % 3 else URA_L     # faceted interior
            px[y][x] = q(sh(c, int((nz[y][x] - 0.5) * 18)))
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
    """Packed crystal chunks, banded into flat facets so they read as cut stone."""
    r = Rng(seed)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            bd, off, rad = 1e9, None, None
            for (cx, cy, rr) in CHUNKS:
                d = math.hypot(wd(x + 0.5, cx), wd(y + 0.5, cy)) / rr
                if d < bd:
                    bd, off, rad = d, (x + 0.5 - cx, y + 0.5 - cy), rr
            if bd >= 1.0:
                c = URA_O                                   # seam
            elif bd > 0.84:
                c = mix(URA_D, URA_O, 0.4)                  # rim
            else:
                lit = (-off[0] - off[1]) / (rad * 1.5)
                if lit > 0.55:
                    c = mix(URA_B, URA_S, 0.35)
                elif lit > 0.22:
                    c = URA_B
                elif lit > -0.10:
                    c = URA_L
                elif lit > -0.42:
                    c = URA_M
                else:
                    c = URA_D
            row.append(q(sh(c, int((r.f() - 0.5) * 8))))
        px.append(row)
    write_png(path, px)

def make_metal_block(path, seed=4):
    """Refined metal: brushed streaks with a bevelled edge and corner studs, so
    the block has a silhouette instead of reading as flat noise."""
    r = Rng(seed)
    rows = [Rng(seed * 7919 + y * 104729).f() for y in range(N)]
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            v = rows[y] + (r.f() - 0.5) * 0.20
            c = (URA_D if v < 0.26 else URA_M if v < 0.60 else
                 URA_L if v < 0.86 else URA_B)
            row.append(q(c))
        px.append(row)
    for i in range(N):
        px[0][i] = q(mix(px[0][i], URA_S, 0.45))
        px[i][0] = q(mix(px[i][0], URA_B, 0.40))
        px[N - 1][i] = q(mix(px[N - 1][i], URA_O, 0.45))
        px[i][N - 1] = q(mix(px[i][N - 1], URA_O, 0.35))
    for (bx, by) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        px[by][bx] = q(mix(URA_S, URA_B, 0.4))
        if by + 1 < N:
            px[by + 1][bx] = q(URA_D)
    write_png(path, px)

# ---------------------------------------------------------------- centrifuge
# A heavy armoured rotor tower. Dark steel with gold trim and green glow
# panels reads far better at block scale than a pale casing, and the glow is
# what makes the machine look alive.
STEEL_O = (24, 27, 33, 255)
STEEL_D = (40, 45, 55, 255)
STEEL_M = (68, 76, 90, 255)
STEEL_L = (104, 114, 132, 255)
STEEL_H = (150, 162, 182, 255)

GOLD_D = (122, 88, 16, 255)
GOLD_M = (196, 152, 32, 255)
GOLD_L = (238, 202, 74, 255)

GLOW_D = (26, 84, 44, 255)
GLOW_M = (58, 178, 88, 255)
GLOW_L = (118, 245, 148, 255)
GLOW_H = (206, 255, 214, 255)

# amber palette, shared by the plinth hazard stripes and the console GUI
AMB_D = (128, 68, 10, 255)
AMB_M = (206, 122, 22, 255)
AMB_L = (255, 166, 46, 255)
AMB_H = (255, 216, 136, 255)

TAU = math.pi * 2.0

# The drum is ~39 block-pixels around but only 8 tall, so a square texture
# would have to stretch 2.4x to wrap it. The tower map is 64x16 instead, and
# carries no left-right shading: the entity shader lights curved surfaces from
# the vertex normals, and anything baked in would rotate with the drum.
TOWER_W, TOWER_H = 128, 24
PANEL = 8                       # eight panels around the circumference
WIN_TOP, WIN_BOT = 7, 16        # window rows, inclusive
WIN_L, WIN_R = 3, 6             # window columns within a panel, inclusive

# v-bands of the tower map, shared by the renderer
BAND_LOWER = (0, 4)             # lower collar
BAND_BODY = (4, 20)             # spinning body
BAND_UPPER = (20, 24)           # upper collar

def _tower_pixel(x, y):
    """One texel of the unwrapped tower, before grain."""
    p = x % PANEL
    if y <= 3 or y >= 20:                                   # collars
        if y in (0, 20):
            return STEEL_L
        if y in (3, TOWER_H - 1):
            return STEEL_O
        return STEEL_H if p == 4 else STEEL_D               # bolt heads
    if y in (4, 19):                                        # gold trim rails
        return GOLD_L if p == 0 else GOLD_M
    if p <= 1:                                              # vertical strut
        return STEEL_D
    if WIN_TOP <= y <= WIN_BOT and WIN_L <= p <= WIN_R:
        edge = y in (WIN_TOP, WIN_BOT) or p in (WIN_L, WIN_R)
        # deliberately dim: the lit look comes from the emissive overlay, so an
        # idle machine has to read as genuinely off
        return STEEL_O if edge else mix(GLOW_D, STEEL_O, 0.45)
    return STEEL_M

def make_tower(path, seed=71):
    r = Rng(seed)
    px = [[q(sh(_tower_pixel(x, y), int((r.f() - 0.5) * 8)))
           for x in range(TOWER_W)] for y in range(TOWER_H)]
    write_png(path, px)

def make_tower_glow(path, seed=72):
    """Emissive overlay: only the window interiors, everything else clear."""
    r = Rng(seed)
    px = []
    for y in range(TOWER_H):
        row = []
        for x in range(TOWER_W):
            p = x % PANEL
            if WIN_TOP <= y <= WIN_BOT and WIN_L <= p <= WIN_R \
                    and not (y in (WIN_TOP, WIN_BOT) or p in (WIN_L, WIN_R)):
                mid = max(0.0, 1.0 - abs(y - (WIN_TOP + WIN_BOT) / 2.0) / 6.0)
                row.append(q(sh(mix(GLOW_L, GLOW_H, mid * 0.5),
                                int((r.f() - 0.5) * 10))))
            else:
                row.append((0, 0, 0, 0))
        px.append(row)
    write_png(path, px)

ROTOR_N = 32

def _rotor_top(seed, glow):
    """Top of the housing, seen from above: a rimmed rotor port."""
    r = Rng(seed)
    px = [[q(sh(STEEL_D, int((r.f() - 0.5) * 8)))
           for _ in range(ROTOR_N)] for _ in range(ROTOR_N)]
    k = ROTOR_N / 16.0
    for y in range(ROTOR_N):
        for x in range(ROTOR_N):
            d = math.hypot(x + 0.5 - ROTOR_N / 2.0, y + 0.5 - ROTOR_N / 2.0) / k
            if d > 7.6:
                continue
            if d > 6.6:
                px[y][x] = STEEL_L
            elif d > 6.0:
                px[y][x] = STEEL_O
            elif d > 4.6:
                px[y][x] = GOLD_M if ((x + y) // 2) % 2 == 0 else STEEL_M
            elif d > 3.6:
                px[y][x] = STEEL_O
            else:
                hot = mix(GLOW_H, GLOW_L, d / 3.6)
                cold = mix(GLOW_D, STEEL_O, d / 3.6)
                px[y][x] = q(mix(cold, hot, glow))
    for (bx, by) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        px[by][bx] = STEEL_H
    return px

def make_rotor_top(path, seed=73):
    write_png(path, _rotor_top(seed, 0.10))

def make_rotor_top_glow(path, seed=73):
    """Emissive: just the port, clear elsewhere."""
    base = _rotor_top(seed, 1.0)
    k = ROTOR_N / 16.0
    px = []
    for y in range(ROTOR_N):
        row = []
        for x in range(ROTOR_N):
            d = math.hypot(x + 0.5 - ROTOR_N / 2.0, y + 0.5 - ROTOR_N / 2.0) / k
            row.append(base[y][x] if d <= 3.6 else (0, 0, 0, 0))
        px.append(row)
    write_png(path, px)

def make_shaft(path, seed=74):
    """Gold drive shaft. Wraps a thin rod, so no baked shading here either."""
    r = Rng(seed)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            c = GOLD_M
            if y % 5 == 0:
                c = GOLD_D
            elif y % 5 == 1:
                c = GOLD_L
            row.append(q(sh(c, int((r.f() - 0.5) * 10))))
        px.append(row)
    write_png(path, px)

# The skirt is 6 block-pixels tall, so the renderer samples rows 5..11 of this
# texture. Those rows carry the whole design; the rest is never seen.
SKIRT_V0, SKIRT_V1 = 5, 11

# The skirt is only 3 block-pixels tall, so the renderer samples rows 6..9.
SKIRT_V0, SKIRT_V1 = 6, 9

def make_base(path, seed=45):
    """Foundation rim. Deliberately plain: the drum nearly fills the footprint,
    so this is a shadow line under it, not a decorated slab."""
    r = Rng(seed)
    px = [[q(sh(STEEL_O, int((r.f() - 0.5) * 6))) for _ in range(N)] for _ in range(N)]
    for x in range(N):
        px[SKIRT_V0][x] = q(mix(STEEL_M, STEEL_D, 0.4))     # lit top edge
        px[SKIRT_V0 + 1][x] = q(STEEL_D)
        px[SKIRT_V1 - 1][x] = q(mix(STEEL_O, (0, 0, 0, 255), 0.35))
    write_png(path, px)

def make_foot(path, seed=46):
    """Corner anchor block: heavier steel with a bolt on each face."""
    r = Rng(seed)
    px = [[q(sh(STEEL_M, int((r.f() - 0.5) * 10))) for _ in range(N)] for _ in range(N)]
    for i in range(N):
        px[0][i] = STEEL_H
        px[i][0] = STEEL_L
        px[N - 1][i] = STEEL_O
        px[i][N - 1] = STEEL_D
    for (bx, by) in ((5, 5), (10, 5), (5, 10), (10, 10)):
        px[by][bx] = STEEL_H
        px[by + 1][bx] = STEEL_O
    for x in range(4, 12):                              # amber accent
        px[13][x] = q(AMB_M)
    write_png(path, px)

def make_deck(path, seed=64):
    """Foundation top. Only a narrow ring of it is ever visible around the drum."""
    r = Rng(seed)
    px = [[q(sh(STEEL_D, int((r.f() - 0.5) * 8))) for _ in range(N)] for _ in range(N)]
    for i in range(N):
        px[0][i] = q(STEEL_M)
        px[i][0] = q(STEEL_M)
        px[N - 1][i] = q(STEEL_O)
        px[i][N - 1] = q(STEEL_O)
    write_png(path, px)

def make_bottom(path, seed=42):
    r = Rng(seed)
    px = [[q(sh(STEEL_D, int((r.f() - 0.5) * 10))) for _ in range(N)] for _ in range(N)]
    for i in range(N):
        px[0][i] = STEEL_M
        px[i][0] = STEEL_M
        px[N - 1][i] = STEEL_O
        px[i][N - 1] = STEEL_O
    for (bx, by) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        px[by][bx] = STEEL_H
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
make_tower(f"{B}/centrifuge_tower.png")
make_tower_glow(f"{B}/centrifuge_tower_glow.png")
make_rotor_top(f"{B}/centrifuge_rotor_top.png")
make_rotor_top_glow(f"{B}/centrifuge_rotor_top_glow.png")
make_shaft(f"{B}/centrifuge_shaft.png")
make_base(f"{B}/centrifuge_base.png")
make_deck(f"{B}/centrifuge_deck.png")
make_bottom(f"{B}/centrifuge_bottom.png")

make_gui(f"{RES}/textures/gui/centrifuge.png")

_cap = []
_real = write_png
write_png = lambda p, px: _cap.append(px)
make_raw_uranium("mem")
write_png = _real
write_png(f"{RES}/icon.png", upscale(_cap[0], 8))
