#!/usr/bin/env python3
"""Compose docs/preview.png: every pillow and every Zzz particle on one sheet."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_textures import (ROOT, Canvas, PALETTES, PARTICLE_LAYOUT, NAVY,
                               WHITE, ICE, LILAC, pillow_canvas, zzz_canvas)

BG = (30, 33, 41, 255)
GRID = (44, 48, 59, 255)


def paste(dst, src, ox, oy):
    for y in range(src.h):
        for x in range(src.w):
            c = src.px[y][x]
            if c[3] == 255:
                dst.set(ox + x, oy + y, c)
            elif c[3]:
                a = c[3]
                b = dst.get(ox + x, oy + y)
                dst.set(ox + x, oy + y, tuple(
                    (c[i] * a + b[i] * (255 - a)) // 255 for i in range(3)) + (255,))


def main():
    cell, gap = 128, 16
    cols = 6
    w = gap + cols * (cell + gap)
    h = gap + cell + gap + cell + gap
    sheet = Canvas(w, h)
    sheet.rect(0, 0, w - 1, h - 1, BG)

    # row 1: the six pillows
    for i, tier in enumerate(PALETTES):
        x = gap + i * (cell + gap)
        sheet.rect(x - 2, gap - 2, x + cell + 1, gap + cell + 1, GRID)
        sheet.rect(x, gap, x + cell - 1, gap + cell - 1, BG)
        pil = pillow_canvas(PALETTES[tier])
        paste(sheet, pil.scaled(cell // pil.w), x, gap)

    # row 2: the Zzz particles
    y = gap + cell + gap
    particles = [
        ("hit", WHITE), ("crit", ICE), ("enchanted", LILAC), ("sweep", WHITE),
    ]
    for i, (_, core) in enumerate(particles):
        x = gap + i * (cell + gap)
        sheet.rect(x - 2, y - 2, x + cell + 1, y + cell + 1, GRID)
        sheet.rect(x, y, x + cell - 1, y + cell - 1, BG)
        paste(sheet, zzz_canvas(32, core, NAVY, PARTICLE_LAYOUT).scaled(4), x, y)

    sheet.save(os.path.join(ROOT, "docs", "preview.png"))


if __name__ == "__main__":
    main()
