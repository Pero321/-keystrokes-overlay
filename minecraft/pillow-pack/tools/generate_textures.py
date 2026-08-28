#!/usr/bin/env python3
"""Generate every PNG used by the "Sleepy Pillows" resource pack.

No third-party dependencies: PNGs are encoded by hand with zlib from the
standard library, so the pack can be rebuilt anywhere Python 3 runs.

    python3 tools/generate_textures.py

Output goes into src/assets/minecraft/textures/ and src/pack.png.
"""

import os
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
ITEM_DIR = os.path.join(SRC, "assets", "minecraft", "textures", "item")
PARTICLE_DIR = os.path.join(SRC, "assets", "minecraft", "textures", "particle")

TRANSPARENT = (0, 0, 0, 0)


# --------------------------------------------------------------------------
# tiny PNG writer
# --------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = [[TRANSPARENT for _ in range(w)] for _ in range(h)]

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = color

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return TRANSPARENT

    def rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, color)

    def scaled(self, factor):
        out = Canvas(self.w * factor, self.h * factor)
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y][x]
                if c[3]:
                    out.rect(x * factor, y * factor,
                             x * factor + factor - 1, y * factor + factor - 1, c)
        return out

    def with_alpha(self, alpha):
        out = Canvas(self.w, self.h)
        for y in range(self.h):
            for x in range(self.w):
                r, g, b, a = self.px[y][x]
                out.px[y][x] = (r, g, b, a * alpha // 255)
        return out

    def shifted(self, dx, dy):
        out = Canvas(self.w, self.h)
        for y in range(self.h):
            for x in range(self.w):
                out.set(x + dx, y + dy, self.px[y][x])
        return out

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        raw = b"".join(
            b"\x00" + bytes(v for px in row for v in px) for row in self.px
        )

        def chunk(tag, data):
            body = tag + data
            return (struct.pack(">I", len(data)) + body
                    + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

        blob = b"\x89PNG\r\n\x1a\n"
        blob += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
        blob += chunk(b"IDAT", zlib.compress(raw, 9))
        blob += chunk(b"IEND", b"")
        with open(path, "wb") as fh:
            fh.write(blob)
        print("  wrote", os.path.relpath(path, ROOT))


def outline(canvas, color):
    """Add a 1px border around every opaque pixel (8-neighbourhood)."""
    edges = []
    for y in range(canvas.h):
        for x in range(canvas.w):
            if canvas.get(x, y)[3]:
                continue
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (dx or dy) and canvas.get(x + dx, y + dy)[3]:
                        edges.append((x, y))
                        break
                else:
                    continue
                break
    for x, y in edges:
        canvas.set(x, y, color)


# --------------------------------------------------------------------------
# the letter Z
# --------------------------------------------------------------------------

def draw_z(canvas, ox, oy, size, color):
    """Draw a pixel-art capital Z whose bounding box is size x size."""
    bar = 2 if size >= 9 else 1
    thick = 2 if size >= 9 else 1
    for i in range(bar):
        canvas.rect(ox, oy + i, ox + size - 1, oy + i, color)
        canvas.rect(ox, oy + size - 1 - i, ox + size - 1, oy + size - 1 - i, color)
    for row in range(bar, size - bar):
        x = size - 1 - row
        for t in range(thick):
            canvas.set(ox + min(x + t, size - 1), oy + row, color)


def zzz_canvas(size, core, edge, layout):
    """Three Zs drifting up and to the right, outlined for readability."""
    c = Canvas(size, size)
    for (ox, oy, glyph) in layout:
        draw_z(c, ox, oy, glyph, core)
    outline(c, edge)
    return c


# 32x32 particle sheet: big Z bottom-left, tiny Z top-right.
PARTICLE_LAYOUT = [(1, 18, 13), (14, 8, 9), (24, 2, 5)]

NAVY = (26, 30, 56, 255)
WHITE = (255, 255, 255, 255)
ICE = (191, 232, 255, 255)
LILAC = (224, 191, 255, 255)


# --------------------------------------------------------------------------
# pillows
# --------------------------------------------------------------------------

# outline, shadow, base, highlight, stitching
PALETTES = {
    "wooden":    ((90, 70, 48, 255),  (154, 122, 82, 255),  (200, 162, 118, 255), (224, 195, 154, 255), (122, 92, 58, 255)),
    "stone":     ((60, 60, 62, 255),  (128, 128, 132, 255), (168, 168, 172, 255), (200, 200, 204, 255), (110, 110, 114, 255)),
    "iron":      ((110, 110, 114, 255), (180, 180, 186, 255), (227, 227, 232, 255), (255, 255, 255, 255), (154, 154, 160, 255)),
    "golden":    ((110, 80, 16, 255),  (201, 154, 34, 255),  (242, 203, 78, 255),  (255, 231, 154, 255), (168, 122, 24, 255)),
    "diamond":   ((30, 110, 104, 255), (63, 181, 172, 255),  (111, 227, 216, 255), (169, 245, 238, 255), (46, 143, 135, 255)),
    "netherite": ((22, 18, 22, 255),   (50, 44, 49, 255),    (74, 67, 72, 255),    (107, 97, 105, 255),  (198, 162, 92, 255)),
}

# Rounded, puffy silhouette: (row, x_start, x_end)
PILLOW_ROWS = [
    (3, 3, 12),
    (4, 2, 13),
    (5, 1, 14),
    (6, 1, 14),
    (7, 1, 14),
    (8, 1, 14),
    (9, 1, 14),
    (10, 1, 14),
    (11, 2, 13),
    (12, 3, 12),
]


def pillow_canvas(palette):
    edge, shadow, base, light, stitch = palette
    c = Canvas(16, 16)

    # flat silhouette, then a diagonal light source from the top-left so the
    # pillow reads as soft and puffy rather than as a flat brick
    for y, x0, x1 in PILLOW_ROWS:
        for x in range(x0, x1 + 1):
            tone = x + y
            c.set(x, y, light if tone <= 13 else (shadow if tone >= 20 else base))

    # pinched corner tufts
    for (tx, ty) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        c.set(tx, ty, shadow)

    # embroidered "z"
    draw_z(c, 5, 5, 5, stitch)

    outline(c, edge)
    return c


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def main():
    print("pillows:")
    for tier, palette in PALETTES.items():
        pillow_canvas(palette).save(os.path.join(ITEM_DIR, "pillow_%s.png" % tier))

    print("particles:")
    variants = {
        "zzz_hit": WHITE,
        "zzz_crit": ICE,
        "zzz_enchanted": LILAC,
    }
    for name, core in variants.items():
        zzz_canvas(32, core, NAVY, PARTICLE_LAYOUT).save(
            os.path.join(PARTICLE_DIR, name + ".png"))

    # sweep attack: 8 frames of a Zzz drifting upwards and fading out
    sweep = zzz_canvas(32, WHITE, NAVY, PARTICLE_LAYOUT)
    alphas = (120, 200, 255, 255, 220, 180, 130, 80)
    for frame, alpha in enumerate(alphas):
        sweep.shifted(0, 3 - frame).with_alpha(alpha).save(
            os.path.join(PARTICLE_DIR, "zzz_sweep_%d.png" % frame))

    # Also overwrite the vanilla texture names, so the pack still looks right
    # even if a future snapshot renames the particle definitions.
    print("vanilla particle overrides:")
    zzz_canvas(32, ICE, NAVY, PARTICLE_LAYOUT).save(
        os.path.join(PARTICLE_DIR, "critical_hit.png"))
    zzz_canvas(32, LILAC, NAVY, PARTICLE_LAYOUT).save(
        os.path.join(PARTICLE_DIR, "enchanted_hit.png"))
    zzz_canvas(32, WHITE, NAVY, PARTICLE_LAYOUT).save(
        os.path.join(PARTICLE_DIR, "damage.png"))
    for frame, alpha in enumerate(alphas):
        sweep.shifted(0, 3 - frame).with_alpha(alpha).save(
            os.path.join(PARTICLE_DIR, "sweep_%d.png" % frame))

    print("pack icon:")
    icon = Canvas(128, 128)
    pillow = pillow_canvas(PALETTES["diamond"]).scaled(8)
    for y in range(128):
        for x in range(128):
            if pillow.px[y][x][3]:
                icon.px[y][x] = pillow.px[y][x]
    badge = zzz_canvas(32, WHITE, NAVY, PARTICLE_LAYOUT).scaled(2)
    for y in range(64):
        for x in range(64):
            c = badge.px[y][x]
            if c[3]:
                icon.set(x + 62, y + 2, c)
    icon.save(os.path.join(SRC, "pack.png"))


if __name__ == "__main__":
    main()
