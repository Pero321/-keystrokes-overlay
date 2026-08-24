"""Generates the 16x16 textures for the Uranium Ore mod. Pure stdlib PNG writer."""
import math, os, struct, zlib

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "src", "main", "resources", "assets", "uraniummod")
N = 16

# ---------------------------------------------------------------- png writer
def write_png(path, px):
    h = len(px); w = len(px[0])
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
    def __init__(self, seed): self.s = seed & 0xffffffff
    def next(self):
        self.s = (self.s * 1664525 + 1013904223) & 0xffffffff
        return self.s
    def f(self): return self.next() / 0xffffffff

def blur(grid, passes):
    n = len(grid)
    for _ in range(passes):
        out = [[0.0] * n for _ in range(n)]
        for y in range(n):
            for x in range(n):
                t = sum(grid[(y + dy) % n][(x + dx) % n]
                        for dy in (-1, 0, 1) for dx in (-1, 0, 1))
                out[y][x] = t / 9.0
        grid = out
    return grid

def noise(seed, passes=2, n=N):
    r = Rng(seed)
    g = blur([[r.f() for _ in range(n)] for _ in range(n)], passes)
    lo = min(min(row) for row in g); hi = max(max(row) for row in g)
    span = (hi - lo) or 1.0
    return [[(v - lo) / span for v in row] for row in g]

def clamp(v): return 0 if v < 0 else (255 if v > 255 else int(v))
def shade(c, amt): return (clamp(c[0] + amt), clamp(c[1] + amt), clamp(c[2] + amt), 255)
def mix(a, b, t):
    t = min(1.0, max(0.0, t))
    return (clamp(a[0] + (b[0] - a[0]) * t), clamp(a[1] + (b[1] - a[1]) * t),
            clamp(a[2] + (b[2] - a[2]) * t), 255)
def quant(c, step=7):
    """Snap to a coarse palette so the result reads as pixel art, not a gradient."""
    return (clamp(round(c[0] / step) * step), clamp(round(c[1] / step) * step),
            clamp(round(c[2] / step) * step), 255)
def wrapd(a, b, n=N):
    d = abs(a - b)
    return min(d, n - d)

# ---------------------------------------------------------------- palettes
ORE_LIGHT   = (219, 247, 98)
ORE_MID     = (168, 204, 46)
ORE_DARK    = (104, 133, 25)

RAW_LIGHT   = (205, 235, 100)
RAW_MID     = (154, 187, 55)
RAW_DARK    = (95, 122, 30)
RAW_SEAM    = (41, 53, 13)

ING_LIGHT   = (226, 250, 120)
ING_MID     = (172, 210, 60)
ING_DARK    = (116, 148, 33)
ING_OUTLINE = (56, 72, 17)

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
    """Blotches for the large shapes plus per-pixel grain, like vanilla stone."""
    blotch = noise(seed, passes=2)
    grain = Rng(seed + 31337)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            v = (blotch[y][x] - 0.5) * 2.0 * spread + (grain.f() - 0.5) * 14
            row.append(quant((clamp(base + v + tint[0]), clamp(base + v + tint[1]),
                              clamp(base + v + tint[2]), 255)))
        px.append(row)
    return px

def make_ore(path, seed, base, spread, tint=(0, 0, 0)):
    px = stone_base(seed, base, spread, tint)
    nz = noise(seed + 977, passes=1)

    for y in range(N):                       # darken stone touching a blob
        for x in range(N):
            if is_ore(x, y):
                continue
            if any(is_ore(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[y][x] = shade(px[y][x], -18)

    for y in range(N):
        for x in range(N):
            if not is_ore(x, y):
                continue
            above = y > 0 and is_ore(x, y - 1)
            below = y < N - 1 and is_ore(x, y + 1)
            left = x > 0 and is_ore(x - 1, y)
            if not above or not left:
                c = ORE_LIGHT
            elif not below:
                c = ORE_DARK
            else:
                c = ORE_MID
            px[y][x] = quant(shade(c, int((nz[y][x] - 0.5) * 24)))
    write_png(path, px)

# ---------------------------------------------------------------- storage blocks
# Rounded chunks with dark seams between them, in the spirit of raw iron blocks.
CHUNKS = [(3.4, 3.2, 3.5), (11.2, 2.8, 3.2), (7.6, 9.4, 3.6),
          (13.6, 10.2, 3.0), (2.4, 12.4, 3.1), (14.6, 15.4, 2.6)]

def make_raw_block(path, seed):
    grain = Rng(seed)
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            best, bestd, bestc = None, 1e9, None
            for (cx, cy, r) in CHUNKS:
                dx, dy = wrapd(x + 0.5, cx), wrapd(y + 0.5, cy)
                d = math.hypot(dx, dy) / r
                if d < bestd:
                    bestd, best, bestc = d, (cx, cy, r), (x + 0.5 - cx, y + 0.5 - cy)
            if bestd >= 1.0:
                c = RAW_SEAM                              # gap between chunks
            elif bestd > 0.82:
                c = RAW_DARK                              # chunk rim
            else:
                # light falls from the upper-left of each chunk
                lit = (-bestc[0] - bestc[1]) / (best[2] * 2.0)
                c = mix(RAW_DARK, RAW_LIGHT, 0.45 + lit * 0.9)
                c = mix(c, RAW_MID, 0.3)
            row.append(quant(shade(c, int((grain.f() - 0.5) * 14))))
        px.append(row)
    write_png(path, px)

def make_metal_block(path, seed):
    """Refined metal: a few flat tones in small patches, no smooth gradient."""
    nz = noise(seed, passes=1)
    grain = Rng(seed + 555)
    tones = [ING_DARK, mix(ING_DARK, ING_MID, 0.55), ING_MID,
             mix(ING_MID, ING_LIGHT, 0.5), ING_LIGHT]
    px = []
    for y in range(N):
        row = []
        for x in range(N):
            v = nz[y][x] + (grain.f() - 0.5) * 0.18
            idx = min(len(tones) - 1, max(0, int(v * len(tones))))
            row.append(quant(tones[idx]))
        px.append(row)
    write_png(path, px)

# ---------------------------------------------------------------- items
RAW_MASK = [
    "................",
    "................",
    ".....xxx........",
    "....xxxxx.......",
    "...xxxxxxx......",
    "...xxxxxxxx.....",
    "..xxxxxxxxx.....",
    "..xxxxxxxxxx....",
    "..xxxxxxxxxx....",
    "...xxxxxxxxx....",
    "...xxxxxxxx.....",
    "....xxxxxx......",
    ".....xxxx.......",
    "................",
    "................",
    "................",
]

# facet seams inside the raw chunk, so it reads as a rock and not a blob
RAW_FACETS = [(6, 4), (7, 5), (8, 6), (5, 8), (6, 9), (7, 10), (4, 7), (9, 7), (10, 8)]

INGOT_MASK = [
    "................",
    "................",
    "................",
    "................",
    "......xxxxxxx...",
    ".....xxxxxxxxx..",
    "....xxxxxxxxxx..",
    "...xxxxxxxxxx...",
    "..xxxxxxxxxx....",
    "..xxxxxxxxx.....",
    "..xxxxxxxx......",
    "...xxxxxx.......",
    "................",
    "................",
    "................",
    "................",
]

def make_item(path, mask, light, mid, dark, outline, seed, facets=()):
    inside = lambda x, y: 0 <= x < N and 0 <= y < N and mask[y][x] == "x"
    grain = Rng(seed)
    px = [[(0, 0, 0, 0) for _ in range(N)] for _ in range(N)]
    for y in range(N):
        for x in range(N):
            if not inside(x, y):
                if any(inside(x + dx, y + dy)
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    px[y][x] = (outline[0], outline[1], outline[2], 255)
                continue
            if not inside(x, y - 1) or not inside(x - 1, y):
                c = light
            elif not inside(x, y + 1) or not inside(x + 1, y):
                c = dark
            else:
                t = (x + y) / (2.0 * (N - 1))
                c = mix(mix(light, dark, (t - 0.15) / 0.6), mid, 0.35)
            if (x, y) in facets:
                c = mix(c, dark, 0.55)
            px[y][x] = quant(shade(c, int((grain.f() - 0.5) * 12)))
    write_png(path, px)

def upscale(px, f):
    return [[px[y // f][x // f] for x in range(len(px[0]) * f)]
            for y in range(len(px) * f)]

# ---------------------------------------------------------------- run
make_ore(f"{RES}/textures/block/uranium_ore.png", 20240001, 128, 20)
make_ore(f"{RES}/textures/block/deepslate_uranium_ore.png", 20240002, 84, 15, tint=(-2, -2, 5))
make_raw_block(f"{RES}/textures/block/raw_uranium_block.png", 20240003)
make_metal_block(f"{RES}/textures/block/uranium_block.png", 20240004)
make_item(f"{RES}/textures/item/raw_uranium.png", RAW_MASK,
          RAW_LIGHT, RAW_MID, RAW_DARK, RAW_SEAM, 20240005, facets=RAW_FACETS)
make_item(f"{RES}/textures/item/uranium_ingot.png", INGOT_MASK,
          ING_LIGHT, ING_MID, ING_DARK, ING_OUTLINE, 20240006)

_cap = []
_real = write_png
write_png = lambda p, px: _cap.append(px)
make_ore("mem", 20240001, 128, 20)
write_png = _real
write_png(f"{RES}/icon.png", upscale(_cap[0], 8))
