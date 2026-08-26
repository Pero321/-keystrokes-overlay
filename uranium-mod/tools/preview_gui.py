"""Composites the centrifuge GUI sheet into a mock of the live screen."""
import os, struct, sys, zlib
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "src", "main", "resources", "assets", "uraniummod")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "docs", "gui.png")

def rd(p):
    d = open(p, 'rb').read(); i = 8; idat = b''; w = h = 0
    while i < len(d):
        ln = struct.unpack(">I", d[i:i+4])[0]; t = d[i+4:i+8]; da = d[i+8:i+8+ln]
        if t == b'IHDR': w, h = struct.unpack(">II", da[:8])
        if t == b'IDAT': idat += da
        i += 12 + ln
    raw = zlib.decompress(idat); st = w*4; prev = bytearray(st); o = 0; out = []
    for _ in range(h):
        f = raw[o]; o += 1; L = bytearray(raw[o:o+st]); o += st
        for x in range(st):
            a = L[x-4] if x >= 4 else 0; b = prev[x]; c = prev[x-4] if x >= 4 else 0
            if f == 1: L[x] = (L[x]+a) & 255
            elif f == 2: L[x] = (L[x]+b) & 255
            elif f == 3: L[x] = (L[x]+(a+b)//2) & 255
            elif f == 4:
                pp = a+b-c; pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                L[x] = (L[x]+pr) & 255
        prev = L; out.append([tuple(L[x*4:x*4+4]) for x in range(w)])
    return out

def wr(p, px):
    h, w = len(px), len(px[0])
    raw = b"".join(b"\x00" + bytes(c for q in r for c in q) for r in px)
    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t+d) & 0xffffffff)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(b"\x89PNG\r\n\x1a\n"
        + ch(b'IHDR', struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))

# Minimal 5x7 digit font, close enough to Minecraft's to judge the layout.
GLYPHS = {
    "0": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["#...#", "#...#", "#...#", "#####", "....#", "....#", "....#"],
    "5": ["#####", "#....", "#....", "####.", "....#", "#...#", ".###."],
    "6": [".###.", "#...#", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "#...#", ".###."],
    "%": ["#...#", "#..#.", "...#.", "..#..", ".#...", ".#..#", "#...#"],
}
ADVANCE = 6

def text_width(t):
    return max(0, len(t) * ADVANCE - 1)

def draw_text(px, t, tx, ty, col):
    for k, chpos in enumerate(t):
        g = GLYPHS.get(chpos)
        if not g:
            continue
        for gy, row in enumerate(g):
            for gx, c in enumerate(row):
                if c == "#":
                    yy, xx = ty + gy, tx + k * ADVANCE + gx
                    if 0 <= yy < len(px) and 0 <= xx < len(px[0]):
                        px[yy][xx] = col

PW, PH = 176, 166
HX, HY, HW, HH = 25, 20, 12, 38          # must match CentrifugeScreen
AX, AY, AW, AH = 86, 38, 16, 11
g = rd(f"{RES}/textures/gui/centrifuge.png")
raw_item = rd(f"{RES}/textures/item/raw_uranium.png")
ingot = rd(f"{RES}/textures/item/uranium_ingot.png")
u238 = rd(f"{RES}/textures/item/uranium_238.png")
u235 = rd(f"{RES}/textures/item/uranium_235.png")

HEAT_TEXT_Y = 61
COLD_COL = (0xC0, 0x8A, 0x3C, 255)
READY_COL = (0xFF, 0xD0, 0x70, 255)
THRESHOLD = 0.60

def shot(heat_frac, prog_frac, items):
    px = [[g[y][x] for x in range(PW)] for y in range(PH)]
    heat = int(HH * heat_frac)
    for i in range(heat):
        sy = HH - heat + i
        for j in range(HW):
            px[HY + HH - heat + i][HX + j] = g[sy][200 + j]
    prog = int(AW * prog_frac)
    for i in range(AH):
        for j in range(prog):
            c = g[i][176 + j]
            if c[3]: px[AY + i][AX + j] = c
    for (spr, sx, sy) in items:
        for y in range(16):
            for x in range(16):
                c = spr[y][x]
                if c[3]: px[sy + y][sx + x] = c
    label = f"{int(round(heat_frac * 100))}%"
    col = READY_COL if heat_frac >= THRESHOLD else COLD_COL
    draw_text(px, label, HX + HW // 2 - text_width(label) // 2, HEAT_TEXT_Y, col)
    return px

# cold with an input waiting; hot and mid-run, with the common isotope piling
# up on top and the rare one that has landed once below it
shots = [shot(0.28, 0.0, [(raw_item, 56, 35)]),
         shot(0.78, 0.62, [(raw_item, 56, 35), (u238, 116, 26), (u235, 116, 48)])]
S, PAD = 3, 14
W = PAD + len(shots) * (PW*S + PAD); H = PAD*2 + PH*S
cv = [[(20, 20, 23, 255) for _ in range(W)] for _ in range(H)]
for k, sp in enumerate(shots):
    ox = PAD + k * (PW*S + PAD)
    for y in range(PH*S):
        for x in range(PW*S):
            cv[PAD+y][ox+x] = sp[y//S][x//S][:3] + (255,)
wr(OUT, cv)
print(f"wrote {OUT} ({W}x{H})")
