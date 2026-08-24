"""Lays out the frames of the centrifuge's animated textures side by side."""
import os, struct, sys, zlib
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "src", "main", "resources", "assets", "uraniummod")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "docs", "animation.png")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preview_textures import read_png, write_png

STRIPS = ["textures/block/centrifuge_drum_on.png",
          "textures/block/centrifuge_drum_top_on.png"]
S, PAD = 9, 7
rows = []
for name in STRIPS:
    strip = read_png(os.path.join(RES, name))
    n = len(strip) // 16
    rows.append([[strip[f * 16 + y] for y in range(16)] for f in range(n)])
COLS = max(len(r) for r in rows)
W = PAD + COLS * (16 * S + PAD)
H = PAD + len(rows) * (16 * S + PAD)
cv = [[(24, 24, 28, 255) for _ in range(W)] for _ in range(H)]
for ri, row in enumerate(rows):
    oy = PAD + ri * (16 * S + PAD)
    for ci, t in enumerate(row):
        ox = PAD + ci * (16 * S + PAD)
        for y in range(16 * S):
            for x in range(16 * S):
                cv[oy + y][ox + x] = t[y // S][x // S][:3] + (255,)
write_png(OUT, cv)
print(f"wrote {OUT} ({W}x{H})")
