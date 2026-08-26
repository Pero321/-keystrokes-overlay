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

def wd_signed(a, b, n=N):
    """Shortest signed offset from b to a on a wrapping axis, so shapes that
    cross a tile edge stay round instead of being cut in half."""
    d = (a - b + n * 1.5) % n - n * 0.5
    return d

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

# dark rock the raw nuggets are bedded in
MAT_O = (33, 34, 37, 255)
MAT_D = (60, 63, 65, 255)
MAT_M = (92, 96, 97, 255)

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
    """Raw ore as vanilla draws it: big rounded nuggets bedded in dark rock.

    The previous version shaded by distance-from-centre alone, which made every
    chunk a flat disc. These are lit from a real surface normal, so each nugget
    is round, catches a specular near the light and drops a contact shadow onto
    the matrix under it."""
    r = Rng(seed)
    mx = noise(seed + 17, passes=1)         # matrix mottling
    lx, ly, lz = -0.55, -0.62, 0.56         # light direction, upper left, toward viewer

    # nugget centres and radii, tuned to tile: anything crossing an edge is
    # sampled with wrap-around distance so the block repeats seamlessly
    lumps = [(4.0, 3.6, 3.0), (11.6, 2.8, 2.6), (8.2, 9.0, 3.1),
             (14.4, 8.8, 2.3), (2.6, 11.8, 2.6), (12.2, 14.2, 2.5)]

    def nearest(x, y):
        best = None
        for (cx, cy, rr) in lumps:
            dx, dy = wd_signed(x, cx), wd_signed(y, cy)
            d = math.hypot(dx, dy)
            if best is None or d - rr < best[0] - best[3]:
                best = (d, dx, dy, rr)
        return best

    px = []
    for y in range(N):
        row = []
        for x in range(N):
            d, dx, dy, rr = nearest(x + 0.5, y + 0.5)
            if d <= rr:
                # unit normal of a hemisphere of radius rr
                nx, ny = dx / rr, dy / rr
                nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
                lam = nx * lx + ny * ly + nz * lz
                edge = d / rr
                if edge > 0.90:
                    c = URA_O                                   # crisp dark rim
                elif lam > 0.86:
                    c = URA_S
                elif lam > 0.72:
                    c = mix(URA_B, URA_S, 0.45)
                elif lam > 0.55:
                    c = URA_B
                elif lam > 0.36:
                    c = URA_L
                elif lam > 0.16:
                    c = URA_M
                elif lam > 0.02:
                    c = mix(URA_M, URA_D, 0.6)
                else:
                    c = URA_D
                c = sh(c, int((r.f() - 0.5) * 6))
            else:
                # rock matrix. It has to stay clearly lighter than the nugget
                # rims or the gaps read as holes rather than as stone.
                near = min(1.0, (d - rr) / 1.4)
                base = mix(MAT_D, MAT_M, mx[y][x])
                c = mix(mix(MAT_D, MAT_O, 0.45), base, near)
                if dx > 0 and dy > 0 and d - rr < 1.1:
                    c = mix(c, MAT_O, 0.40)                     # contact shadow
            row.append(q(c))
        px.append(row)
    write_png(path, px)
def make_metal_block(path, seed=4):
    """Refined metal as a machined plate.

    Two earlier attempts failed the same way: heavy per-pixel noise. At 16x16 a
    texture has no room for noise *and* structure -- the noise wins and the
    block reads as static. This keeps the grain very low amplitude and spends
    the contrast budget on structure instead: a bevelled outer frame, an inset
    panel with its own bevel, four rivets and one diagonal sheen band."""
    r = Rng(seed)

    # base plate: quiet vertical brushing, deliberately low contrast
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            col = Rng(seed * 7919 + x * 104729).f()
            v = 0.5 + (col - 0.5) * 0.35 + (r.f() - 0.5) * 0.12
            row.append(mix(URA_M, URA_L, v))
        px.append(row)

    def bevel(x0, y0, x1, y1, hi, lo, strength=1.0):
        """Light the top and left edges of a rectangle, shade bottom and right."""
        for x in range(x0, x1):
            px[y0][x] = mix(px[y0][x], hi, strength)
            px[y1 - 1][x] = mix(px[y1 - 1][x], lo, strength)
        for y in range(y0, y1):
            px[y][x0] = mix(px[y][x0], hi, strength * 0.8)
            px[y][x1 - 1] = mix(px[y][x1 - 1], lo, strength * 0.8)

    # outer frame: two rings, so the block has a raised lip
    bevel(0, 0, N, N, URA_S, URA_O, 1.0)
    bevel(1, 1, N - 1, N - 1, URA_B, mix(URA_O, URA_D, 0.5), 0.75)

    # inset panel: darker fill, then bevelled the other way round so it reads
    # as recessed rather than as a second raised plate
    for y in range(4, 12):
        for x in range(4, 12):
            px[y][x] = mix(px[y][x], URA_D, 0.45)
    bevel(3, 3, 13, 13, mix(URA_O, URA_D, 0.6), URA_L, 0.85)

    # A faint sheen down the panel diagonal. Kept weak on purpose: at full
    # strength the stair-stepping of a 45-degree line on a 16px grid reads as a
    # zigzag decoration rather than as light.
    for i in (-1, 0, 1):
        for t in range(4, 12):
            x, y = t + i, t
            if 4 <= x < 12 and 4 <= y < 12:
                px[y][x] = mix(px[y][x], URA_L, 0.12 if i else 0.22)

    # rivets in the frame corners, each a lit dome with a dropped shadow
    for (bx, by) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        px[by][bx] = URA_S
        if by + 1 < N:
            px[by + 1][bx] = mix(URA_O, URA_D, 0.4)

    write_png(path, [[q(c) for c in row] for row in px])
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
    # two stacked outputs: the guaranteed product on top, the rare byproduct
    # below it, tinted green so the two do not read as interchangeable
    machine_slot(px, 116, 26)
    machine_slot(px, 116, 48, accent=URA_L)
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

# ---------------------------------------------------------------- isotopes,
# tools and shielding
#
# Sprites here are built from geometry rather than hand-drawn pixel maps. At
# 16x16 a mis-typed character in an ASCII map is invisible in the source and
# obvious in the game, and there is no way to check one without rendering it.
# Strokes and polygons can at least be reasoned about.

WOOD_D = (72, 50, 28, 255)
WOOD_M = (110, 78, 44, 255)
WOOD_L = (146, 106, 62, 255)

# dull, spent metal for depleted uranium: the same hue, drained of chroma
DEP_O = (26, 32, 26, 255)
DEP_D = (52, 62, 52, 255)
DEP_M = (84, 98, 82, 255)
DEP_L = (120, 136, 116, 255)
DEP_B = (156, 172, 150, 255)

def blank(n=N):
    return [["." for _ in range(n)] for _ in range(n)]

def mask_rows(rows):
    """A literal character mask, checked for size and for left-right symmetry.

    Symmetry is the only cheap invariant a 16x16 sprite has: every armour piece
    here is meant to be mirror-symmetric, so an off-by-one in a row shows up as
    an assertion instead of as a lopsided lump in the inventory."""
    assert len(rows) == N, f"{len(rows)} rows, want {N}"
    for i, row in enumerate(rows):
        assert len(row) == N, f"row {i} is {len(row)} wide, want {N}"
        assert row == row[::-1], f"row {i} is not symmetric: {row!r}"
    return [list(row) for row in rows]

def stroke(m, pts, w, ch):
    """Draw a thick polyline of character ch through pts."""
    half = w / 2.0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        seg = math.hypot(dx, dy) or 1.0
        for y in range(N):
            for x in range(N):
                px_, py_ = x + 0.5, y + 0.5
                t = ((px_ - x0) * dx + (py_ - y0) * dy) / (seg * seg)
                t = min(1.0, max(0.0, t))
                if math.hypot(px_ - (x0 + dx * t), py_ - (y0 + dy * t)) <= half:
                    m[y][x] = ch

def disc(m, cx, cy, r, ch):
    for y in range(N):
        for x in range(N):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                m[y][x] = ch

def ellipse(m, cx, cy, rx, ry, ch):
    for y in range(N):
        for x in range(N):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                m[y][x] = ch

def poly(m, pts, ch):
    for y in range(N):
        for x in range(N):
            if in_poly(x + 0.5, y + 0.5, pts):
                m[y][x] = ch

def shade_mask(m, ramps, seed=1, outline=URA_O):
    """Light a character mask from the upper left and rim it with an outline.

    ramps maps each character to a list of colours, darkest first. The shade
    index comes from a lighting term, so a shape is lit by where it sits in its
    own silhouette rather than by where it sits in the sprite."""
    r = Rng(seed)
    px = [[(0, 0, 0, 0) for _ in range(N)] for _ in range(N)]
    filled = lambda x, y: (0 <= x < N and 0 <= y < N and m[y][x] != ".")

    for y in range(N):
        for x in range(N):
            ch = m[y][x]
            if ch == ".":
                continue
            ramp = ramps[ch]
            # distance to the unlit side of this shape, normalised
            open_up = sum(1 for d in range(1, 4) if not filled(x - d, y - d))
            open_dn = sum(1 for d in range(1, 4) if not filled(x + d, y + d))
            lam = 0.5 + (open_up - open_dn) * 0.16 + (r.f() - 0.5) * 0.12
            idx = int(min(len(ramp) - 1, max(0, round(lam * (len(ramp) - 1)))))
            c = ramp[idx]
            if not filled(x, y + 1) or not filled(x + 1, y):
                c = mix(c, ramp[0], 0.5)
            px[y][x] = q(c)

    for y in range(N):                                  # outline
        for x in range(N):
            if filled(x, y) or px[y][x][3]:
                continue
            if any(filled(x + dx, y + dy)
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[y][x] = outline
    return px

URA_RAMP = [URA_O, URA_D, URA_M, URA_L, URA_B, URA_S]
DEP_RAMP = [DEP_O, DEP_D, DEP_M, DEP_L, DEP_B]
WOOD_RAMP = [WOOD_D, WOOD_M, WOOD_L]

# ---- isotopes -----------------------------------------------------------

def make_pellet(path, ramp, seed, glow=None):
    """A short cylindrical pellet seen slightly from above.

    Built as a rectangle capped with two ellipses rather than with discs: a
    disc wide enough to cap the body also bulges past its sides, which is what
    turned the first attempt into a lumpy blob instead of a cylinder."""
    RX, TOP, BOT = 3.6, 4.4, 11.6
    m = blank()
    poly(m, [(8.0 - RX, TOP), (8.0 + RX, TOP), (8.0 + RX, BOT), (8.0 - RX, BOT)], "x")
    ellipse(m, 8.0, TOP, RX, 1.9, "x")
    ellipse(m, 8.0, BOT, RX, 1.9, "x")
    px = shade_mask(m, {"x": ramp}, seed, outline=ramp[0])

    # relight the body as a cylinder: brightness depends only on how far across
    # the barrel a pixel is, so the shading runs in vertical bands
    for y in range(N):
        for x in range(N):
            if not px[y][x][3] or not (TOP - 2.4 < y + 0.5 < BOT + 2.4):
                continue
            u = (x + 0.5 - 8.0) / RX
            if abs(u) > 1.0:
                continue
            lam = 0.72 - u * 0.62 - u * u * 0.30
            idx = int(min(len(ramp) - 1, max(0, round(lam * (len(ramp) - 1)))))
            px[y][x] = q(ramp[idx])

    # top face: an ellipse lit flat, a shade brighter than the barrel so the
    # pellet reads as standing up
    for y in range(N):
        for x in range(N):
            dx, dy = (x + 0.5 - 8.0) / RX, (y + 0.5 - TOP) / 1.9
            if dx * dx + dy * dy <= 1.0 and px[y][x][3]:
                edge = math.hypot(dx, dy)
                px[y][x] = q(mix(ramp[-1], ramp[-2], edge))

    # crisp the silhouette back up after the relight
    for y in range(N):
        for x in range(N):
            if not px[y][x][3]:
                continue
            if any(not (0 <= x + dx < N and 0 <= y + dy < N and px[y + dy][x + dx][3])
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[y][x] = q(mix(px[y][x], ramp[0], 0.55))

    if glow:
        for (gx, gy) in glow:
            px[gy][gx] = URA_WHITE
    write_png(path, px)
def make_fuel_cell(path, seed=31):
    """A sealed rod: steel casing with a viewing window onto the charge."""
    m = blank()
    poly(m, [(5.0, 1.5), (11.0, 1.5), (11.0, 14.5), (5.0, 14.5)], "s")
    poly(m, [(4.0, 2.5), (12.0, 2.5), (12.0, 4.5), (4.0, 4.5)], "s")   # top collar
    poly(m, [(4.0, 11.5), (12.0, 11.5), (12.0, 13.5), (4.0, 13.5)], "s")
    poly(m, [(6.0, 5.5), (10.0, 5.5), (10.0, 10.5), (6.0, 10.5)], "x") # window
    px = shade_mask(m, {"s": [MET_O, MET_D, MET_M, MET_L, MET_H],
                        "x": URA_RAMP}, seed, outline=MET_O)
    # the charge glows: brighten the window core past anything the casing does
    for y in range(6, 10):
        for x in range(7, 9):
            px[y][x] = q(mix(URA_B, URA_WHITE, 0.35 if y in (7, 8) else 0.0))
    write_png(path, px)

# ---- tools --------------------------------------------------------------

HANDLE = [(11.0, 5.0), (2.8, 13.2)]

def tool_base():
    m = blank()
    stroke(m, HANDLE, 2.2, "h")
    return m

def make_pickaxe(path, seed=41):
    m = tool_base()
    # head: an arc across the top, thickening toward the middle where it meets
    # the handle, with the two points swept back
    stroke(m, [(2.0, 4.0), (5.0, 1.6), (8.5, 1.2), (12.0, 1.8), (14.2, 3.8)], 2.0, "x")
    stroke(m, [(8.5, 2.0), (10.6, 5.2)], 2.2, "x")
    write_png(path, shade_mask(m, {"x": URA_RAMP, "h": WOOD_RAMP}, seed))

def make_axe(path, seed=42):
    """Broad bearded blade, narrow at the eye. The first version was a small
    blob on the end of a stick, which read as a hammer."""
    m = tool_base()
    poly(m, [(9.6, 1.4), (11.8, 2.0), (12.4, 6.2), (10.4, 7.6)], "x")   # eye
    poly(m, [(9.6, 1.4), (10.4, 7.6), (6.0, 7.0), (4.4, 4.6), (5.6, 2.0)], "x")
    write_png(path, shade_mask(m, {"x": URA_RAMP, "h": WOOD_RAMP}, seed))
def make_shovel(path, seed=43):
    m = blank()
    stroke(m, [(10.2, 6.2), (2.8, 13.2)], 2.2, "h")
    poly(m, [(8.6, 1.4), (13.4, 1.4), (13.8, 5.4), (11.0, 7.6), (8.2, 5.4)], "x")
    write_png(path, shade_mask(m, {"x": URA_RAMP, "h": WOOD_RAMP}, seed))

def make_hoe(path, seed=44):
    m = tool_base()
    stroke(m, [(4.5, 2.2), (12.0, 2.2)], 2.0, "x")
    stroke(m, [(4.8, 2.2), (4.8, 5.4)], 2.0, "x")
    write_png(path, shade_mask(m, {"x": URA_RAMP, "h": WOOD_RAMP}, seed))

def make_sword(path, seed=45):
    """Wide blade, a crossguard that actually crosses, and a pommel. The first
    version had a 2px blade and a guard buried inside it, so it read as a stick
    with a green tip."""
    m = blank()
    stroke(m, [(2.2, 14.0), (4.6, 11.6)], 2.6, "h")             # grip
    disc(m, 2.0, 14.2, 1.4, "g")                                # pommel
    stroke(m, [(2.6, 11.0), (7.2, 15.0)], 2.0, "g")             # crossguard
    stroke(m, [(5.4, 11.0), (12.6, 3.8)], 3.4, "x")             # blade
    poly(m, [(12.0, 3.2), (14.6, 1.2), (13.8, 4.4)], "x")       # point
    write_png(path, shade_mask(m, {
        "x": URA_RAMP,
        "h": WOOD_RAMP,
        "g": [MET_O, MET_D, MET_M, MET_L, MET_H],
    }, seed))
# ---- shielding ----------------------------------------------------------
# Lead-grey plate with amber hazard flashes, so it never reads as another
# uranium item -- the point of the suit is that it is *not* radioactive.

SHL_O = (28, 30, 34, 255)
SHL_D = (58, 62, 68, 255)
SHL_M = (92, 98, 106, 255)
SHL_L = (132, 139, 148, 255)
SHL_B = (172, 180, 190, 255)
SHL_RAMP = [SHL_O, SHL_D, SHL_M, SHL_L, SHL_B]

def make_shielded_helmet(path, seed=51):
    m = blank()
    disc(m, 8.0, 8.0, 5.6, "s")
    poly(m, [(2.0, 8.0), (14.0, 8.0), (14.0, 13.0), (2.0, 13.0)], "s")
    poly(m, [(5.0, 6.0), (11.0, 6.0), (11.0, 9.5), (5.0, 9.5)], "v")   # visor
    px = shade_mask(m, {"s": SHL_RAMP, "v": [AMB_D, AMB_M, AMB_L]}, seed,
                    outline=SHL_O)
    write_png(path, px)

def make_shielded_chestplate(path, seed=52):
    """Torso, shoulder pads, neck notch, hazard band across the chest."""
    return write_png(path, shade_mask(mask_rows([
        "................",
        "................",
        "..sss......sss..",
        "..sssss..sssss..",
        "..ssssssssssss..",
        "..ssssssssssss..",
        "...ssssssssss...",
        "...aaaaaaaaaa...",
        "...aaaaaaaaaa...",
        "...ssssssssss...",
        "...ssssssssss...",
        "....ssssssss....",
        "....ssssssss....",
        "....ssssssss....",
        "................",
        "................",
    ]), {"s": SHL_RAMP, "a": [AMB_D, AMB_M, AMB_L]}, seed, outline=SHL_O))
def make_shielded_leggings(path, seed=53):
    m = blank()
    poly(m, [(3.0, 2.0), (13.0, 2.0), (13.0, 6.0), (3.0, 6.0)], "s")   # belt
    poly(m, [(3.0, 6.0), (7.0, 6.0), (7.0, 14.0), (3.0, 14.0)], "s")
    poly(m, [(9.0, 6.0), (13.0, 6.0), (13.0, 14.0), (9.0, 14.0)], "s")
    poly(m, [(6.5, 2.5), (9.5, 2.5), (9.5, 4.5), (6.5, 4.5)], "a")     # buckle
    write_png(path, shade_mask(m, {"s": SHL_RAMP, "a": [AMB_D, AMB_M, AMB_L]},
                               seed, outline=SHL_O))

def make_shielded_boots(path, seed=54):
    m = blank()
    poly(m, [(2.5, 5.0), (6.5, 5.0), (6.5, 11.0), (2.5, 11.0)], "s")
    poly(m, [(9.5, 5.0), (13.5, 5.0), (13.5, 11.0), (9.5, 11.0)], "s")
    poly(m, [(2.0, 11.0), (7.0, 11.0), (7.0, 13.5), (2.0, 13.5)], "a") # sole
    poly(m, [(9.0, 11.0), (14.0, 11.0), (14.0, 13.5), (9.0, 13.5)], "a")
    write_png(path, shade_mask(m, {"s": SHL_RAMP, "a": [AMB_D, AMB_M, AMB_L]},
                               seed, outline=SHL_O))

def make_armor_layer(path, layer, seed=55):
    """The texture drawn on the player model. Layer 1 covers helmet, chestplate
    and boots; layer 2 is the leggings. Both are 64x32 in the vanilla layout, so
    this fills the whole sheet with plate and lets the model's UVs cut it up."""
    r = Rng(seed)
    w, h = 64, 32
    px = [[(0, 0, 0, 0) for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            v = 0.45 + (Rng(seed * 131 + x * 7919 + (y // 3) * 104729).f() - 0.5) * 0.5
            v += (r.f() - 0.5) * 0.14
            c = SHL_RAMP[int(min(len(SHL_RAMP) - 1, max(0, round(v * (len(SHL_RAMP) - 1)))))]
            # panel seams every four pixels, so the plate has visible sections
            if x % 8 == 0 or y % 8 == 0:
                c = mix(c, SHL_O, 0.55)
            px[y][x] = q(c)
    # amber hazard band across the chest of layer 1, and the belt on layer 2
    band = range(20, 24) if layer == 1 else range(2, 5)
    for y in band:
        for x in range(w):
            if 0 <= y < h:
                px[y][x] = q(mix(AMB_D, AMB_M, ((x // 2) % 2) * 0.8))
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

I = f"{RES}/textures/item"
# U-238 is the spent bulk isotope, so it is drawn in a drained palette; U-235
# is the one worth waiting for and gets the full green plus a specular glint.
make_pellet(f"{I}/uranium_238.png", DEP_RAMP, 21)
make_pellet(f"{I}/uranium_235.png", URA_RAMP, 22, glow=[(6, 6), (7, 5), (9, 9)])
make_fuel_cell(f"{I}/uranium_fuel_cell.png")
make_pickaxe(f"{I}/uranium_pickaxe.png")
make_axe(f"{I}/uranium_axe.png")
make_shovel(f"{I}/uranium_shovel.png")
make_hoe(f"{I}/uranium_hoe.png")
make_sword(f"{I}/uranium_sword.png")
make_shielded_helmet(f"{I}/shielded_helmet.png")
make_shielded_chestplate(f"{I}/shielded_chestplate.png")
make_shielded_leggings(f"{I}/shielded_leggings.png")
make_shielded_boots(f"{I}/shielded_boots.png")

E = f"{RES}/textures/entity/equipment"
os.makedirs(f"{E}/humanoid", exist_ok=True)
os.makedirs(f"{E}/humanoid_leggings", exist_ok=True)
make_armor_layer(f"{E}/humanoid/shielded.png", 1)
make_armor_layer(f"{E}/humanoid_leggings/shielded.png", 2)

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
