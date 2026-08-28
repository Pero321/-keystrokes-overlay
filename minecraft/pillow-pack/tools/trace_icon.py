#!/usr/bin/env python3
"""One-off: turn art/pillow_icon.svg into the mask the texture generator uses.

The icon is a flat silhouette with the pillow's fold punched out as a hole.
We want both parts separately: the *body* (silhouette with its holes filled
back in) and the *crease* (just those holes), so the generator can shade the
body and draw the fold as a seam instead of leaving a see-through gap.

The result is baked into art/pillow_mask.png as a plain RGBA image
(alpha = body, red = crease) so that generate_textures.py needs no
dependencies at all. Only re-run this if the source icon changes:

    pip install pillow cairosvg
    python3 tools/trace_icon.py
"""

import os

import cairosvg
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG = os.path.join(ROOT, "art", "pillow_icon.svg")
OUT = os.path.join(ROOT, "art", "pillow_mask.png")

TRACE = 512   # rasterise big, so the flood fill is unambiguous
STORE = 256   # then keep a comfortable multiple of the texture sizes


def main():
    png = os.path.join(ROOT, "art", "_trace_tmp.png")
    cairosvg.svg2png(url=SVG, write_to=png, output_width=TRACE,
                     output_height=TRACE, background_color=None)
    ink = Image.open(png).convert("RGBA").split()[3].point(
        lambda v: 0 if v > 128 else 255)          # 0 = ink, 255 = not ink
    os.remove(png)

    # Flood the background in from a corner; whatever stays 255 is enclosed.
    ImageDraw.floodfill(ink, (0, 0), 128)
    outside = ink.point(lambda v: 255 if v == 128 else 0)
    crease = ink.point(lambda v: 255 if v == 255 else 0)
    body = outside.point(lambda v: 0 if v else 255)

    body = body.resize((STORE, STORE), Image.LANCZOS).point(lambda v: 255 if v > 128 else 0)
    crease = crease.resize((STORE, STORE), Image.LANCZOS).point(lambda v: 255 if v > 128 else 0)

    black = Image.new("L", (STORE, STORE), 0)
    Image.merge("RGBA", (crease, black, black, body)).save(OUT)

    px = body.load()
    filled = sum(1 for y in range(STORE) for x in range(STORE) if px[x, y])
    print("wrote %s  body=%d px  crease=%d px"
          % (os.path.relpath(OUT, ROOT), filled,
             sum(crease.point(lambda v: 1 if v else 0).getdata())))


if __name__ == "__main__":
    main()
