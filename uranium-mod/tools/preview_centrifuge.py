"""Previews the centrifuge as it renders in world: the baked plinth plus the
rotor tower CentrifugeBlockEntityRenderer generates at runtime.

    python3 tools/preview_centrifuge.py out.png [--spin 0.6] [--heat 1.0]

The cylinder maths mirrors the Java renderer's. It verifies geometry, texture
mapping and placement -- not the Java rendering code, which only the game runs.
"""
import argparse, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_model import model_quads, rasterize

# must match CentrifugeBlockEntityRenderer
SIDES = 32
CX = CZ = 8.0
FOOT_MIN, FOOT_MAX = -16.0, 32.0
COLLAR_R, BODY_R, GLOW_R = 21.0, 19.0, 19.4
HOUSING_R, SHAFT_R = 13.0, 3.0
Y_PLINTH = 5.0
Y_BODY0, Y_BODY1 = 9.0, 22.0
Y_UPPER, Y_HOUSING, Y_SHAFT = 26.0, 29.0, 32.0
V_LOWER = (0.0, 4.0 / 24.0 * 16)
V_BODY = (4.0 / 24.0 * 16, 20.0 / 24.0 * 16)
V_UPPER = (20.0 / 24.0 * 16, 16.0)

NS = "uraniummod:block/"
TOWER = NS + "centrifuge_tower"
TOWER_GLOW = NS + "centrifuge_tower_glow"
ROTOR_TOP = NS + "centrifuge_rotor_top"
ROTOR_TOP_GLOW = NS + "centrifuge_rotor_top_glow"
SHAFT = NS + "centrifuge_shaft"
BASE = NS + "centrifuge_base"
DECK = NS + "centrifuge_deck"

def side_shade(nx):
    """Approximates Minecraft's directional shading on a curved surface."""
    return 0.8 - 0.2 * abs(nx)

def cylinder(cx, cz, radius, y0, y1, v0, v1, tex, spin=0.0):
    quads = []
    for i in range(SIDES):
        a0 = math.tau * i / SIDES + spin
        a1 = math.tau * (i + 1) / SIDES + spin
        x0, z0 = cx + math.cos(a0) * radius, cz + math.sin(a0) * radius
        x1, z1 = cx + math.cos(a1) * radius, cz + math.sin(a1) * radius
        u0 = 16.0 * i / SIDES
        u1 = 16.0 * (i + 1) / SIDES
        nx = math.cos((a0 + a1) / 2)
        quads.append(([(x0, y1, z0), (x1, y1, z1), (x1, y0, z1), (x0, y0, z0)],
                      [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], tex, side_shade(nx)))
    return quads

def disc(cx, cz, radius, y, tex, shade=1.0):
    quads = []
    for i in range(SIDES):
        a0 = math.tau * i / SIDES
        a1 = math.tau * (i + 1) / SIDES
        x0, z0 = cx + math.cos(a0) * radius, cz + math.sin(a0) * radius
        x1, z1 = cx + math.cos(a1) * radius, cz + math.sin(a1) * radius
        u0, v0 = 8 + math.cos(a0) * 8, 8 + math.sin(a0) * 8
        u1, v1 = 8 + math.cos(a1) * 8, 8 + math.sin(a1) * 8
        quads.append(([(cx, y, cz), (x0, y, z0), (x1, y, z1), (cx, y, cz)],
                      [(8, 8), (u0, v0), (u1, v1), (8, 8)], tex, shade))
    return quads

def box(x0, y0, z0, x1, y1, z1, tex):
    faces = [
        ([(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)], 1.0),
        ([(x0,y0,z1),(x1,y0,z1),(x1,y0,z0),(x0,y0,z0)], 0.5),
        ([(x1,y1,z0),(x0,y1,z0),(x0,y0,z0),(x1,y0,z0)], 0.8),
        ([(x0,y1,z1),(x1,y1,z1),(x1,y0,z1),(x0,y0,z1)], 0.8),
        ([(x1,y1,z1),(x1,y1,z0),(x1,y0,z0),(x1,y0,z1)], 0.6),
        ([(x0,y1,z0),(x0,y1,z1),(x0,y0,z1),(x0,y0,z0)], 0.6),
    ]
    uv = [(0,0),(16,0),(16,16),(0,16)]
    return [(c, uv, tex, sh) for c, sh in faces]

def build(heat, spin):
    q = []
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            x0, z0 = dx * 16.0, dz * 16.0
            q += box(x0, 0.0, z0, x0 + 16.0, Y_PLINTH, z0 + 16.0, BASE)
    q += cylinder(CX, CZ, COLLAR_R, Y_PLINTH, Y_BODY0, *V_LOWER, TOWER)
    q += cylinder(CX, CZ, COLLAR_R, Y_BODY1, Y_UPPER, *V_UPPER, TOWER)
    q += disc(CX, CZ, COLLAR_R, Y_UPPER, DECK)
    q += cylinder(CX, CZ, HOUSING_R, Y_UPPER, Y_HOUSING, *V_UPPER, TOWER)
    q += disc(CX, CZ, HOUSING_R, Y_HOUSING, ROTOR_TOP)
    q += cylinder(CX, CZ, BODY_R, Y_BODY0, Y_BODY1, *V_BODY, TOWER, spin)

    shaft_spin = spin * 2.5
    q += cylinder(CX, CZ, SHAFT_R, Y_HOUSING, Y_SHAFT, 0.0, 16.0, SHAFT, shaft_spin)
    for i in range(3):
        a = shaft_spin + math.radians(i * 120.0)
        q += cylinder(CX + math.cos(a) * 8.0, CZ + math.sin(a) * 8.0,
                      2.0, Y_HOUSING, Y_HOUSING + 2.4, 0.0, 16.0, SHAFT)

    if heat > 0.02:
        q += cylinder(CX, CZ, GLOW_R, Y_BODY0, Y_BODY1, *V_BODY, TOWER_GLOW, spin)
        q += disc(CX, CZ, HOUSING_R, Y_HOUSING + 0.05, ROTOR_TOP_GLOW)
    return q

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--spin", type=float, default=0.0)
    ap.add_argument("--heat", type=float, default=0.0)
    ap.add_argument("--size", type=int, default=340)
    ap.add_argument("--zoom", type=float, default=2.4)
    ap.add_argument("--yaw", type=float, default=-35.0)
    ap.add_argument("--pitch", type=float, default=24.0)
    a = ap.parse_args()
    rasterize(build(a.heat, a.spin), a.out, a.size, a.yaw, a.pitch, zoom=a.zoom)
