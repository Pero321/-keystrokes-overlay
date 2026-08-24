"""Previews the centrifuge as it renders in world: the baked static shell plus
the cylinders CentrifugeBlockEntityRenderer generates at runtime.

    python3 tools/preview_centrifuge.py out.png [--spin 0.6] [--lit]

The cylinder maths here mirrors the Java renderer's. It verifies geometry and
placement -- that the drums sit on the plinth at the right radius and height --
not the Java rendering code itself, which only the game can exercise.
"""
import argparse, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_model import model_quads, rasterize

# must match CentrifugeBlockEntityRenderer
SIDES = 12
DRUMS = [(4.0, 4.0), (12.0, 4.0), (8.0, 11.0)]
DRUM_R, DRUM_Y0, DRUM_Y1 = 3.0, 3.0, 12.0
CAP_R, CAP_Y1 = 3.5, 14.0
ARM_R, ARM_LEN = 0.9, 5.0

NS = "uraniummod:block/"

def side_shade(nx, nz):
    """Approximates Minecraft's directional shading for a curved surface."""
    return 0.8 - 0.2 * abs(nx)

def cylinder(cx, cz, radius, y0, y1, tex, spin=0.0):
    quads = []
    for i in range(SIDES):
        a0 = math.tau * i / SIDES + spin
        a1 = math.tau * (i + 1) / SIDES + spin
        x0, z0 = cx + math.cos(a0) * radius, cz + math.sin(a0) * radius
        x1, z1 = cx + math.cos(a1) * radius, cz + math.sin(a1) * radius
        u0 = 16.0 * i / SIDES
        u1 = 16.0 * (i + 1) / SIDES
        nx, nz = math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2)
        corners = [(x0, y1, z0), (x1, y1, z1), (x1, y0, z1), (x0, y0, z0)]
        uvs = [(u0, 0.0), (u1, 0.0), (u1, 16.0), (u0, 16.0)]
        quads.append((corners, uvs, tex, side_shade(nx, nz)))
    return quads

def disc(cx, cz, radius, y, tex):
    quads = []
    for i in range(SIDES):
        a0 = math.tau * i / SIDES
        a1 = math.tau * (i + 1) / SIDES
        x0, z0 = cx + math.cos(a0) * radius, cz + math.sin(a0) * radius
        x1, z1 = cx + math.cos(a1) * radius, cz + math.sin(a1) * radius
        u0, v0 = 8 + math.cos(a0) * 8, 8 + math.sin(a0) * 8
        u1, v1 = 8 + math.cos(a1) * 8, 8 + math.sin(a1) * 8
        corners = [(cx, y, cz), (x0, y, z0), (x1, y, z1), (cx, y, cz)]
        uvs = [(8.0, 8.0), (u0, v0), (u1, v1), (8.0, 8.0)]
        quads.append((corners, uvs, tex, 1.0))
    return quads

def arm(cx, cz, index, phase):
    """Thin gold rod leaning off the collar, rocking with the drums."""
    lean = math.radians(38.0 + math.sin(phase + index * 2.1) * 12.0)
    yaw = math.atan2(cx - 8.0, cz - 8.0)      # lean away from the block centre
    quads = []
    for i in range(SIDES):
        a0 = math.tau * i / SIDES
        a1 = math.tau * (i + 1) / SIDES
        ring = []
        for a in (a0, a1):
            for t in (ARM_LEN, 0.0):
                lx, ly, lz = math.cos(a) * ARM_R, t, math.sin(a) * ARM_R
                # rotate about X by lean, then about Y by yaw
                ly2 = ly * math.cos(lean) - lz * math.sin(lean)
                lz2 = ly * math.sin(lean) + lz * math.cos(lean)
                lx2 = lx * math.cos(yaw) + lz2 * math.sin(yaw)
                lz3 = -lx * math.sin(yaw) + lz2 * math.cos(yaw)
                ring.append((cx + lx2, CAP_Y1 + ly2, cz + lz3))
        corners = [ring[0], ring[2], ring[3], ring[1]]
        u0 = 16.0 * i / SIDES
        u1 = 16.0 * (i + 1) / SIDES
        uvs = [(u0, 0.0), (u1, 0.0), (u1, 16.0), (u0, 16.0)]
        quads.append((corners, uvs, NS + "centrifuge_arm", 0.7))
    return quads

def build(lit, spin, phase):
    quads = list(model_quads("uraniummod:block/centrifuge_static"))
    drum_tex = NS + ("centrifuge_drum_on_still" if lit else "centrifuge_drum")
    top_tex = NS + ("centrifuge_drum_top_on_still" if lit else "centrifuge_drum_top")
    for i, (cx, cz) in enumerate(DRUMS):
        s = spin if i % 2 == 0 else -spin
        quads += cylinder(cx, cz, DRUM_R, DRUM_Y0, DRUM_Y1, drum_tex, s)
        quads += cylinder(cx, cz, CAP_R, DRUM_Y1, CAP_Y1, NS + "centrifuge_cap")
        quads += disc(cx, cz, CAP_R, CAP_Y1, top_tex)
        quads += arm(cx, cz, i, phase)
    return quads

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--spin", type=float, default=0.0)
    ap.add_argument("--phase", type=float, default=0.0)
    ap.add_argument("--lit", action="store_true")
    ap.add_argument("--size", type=int, default=340)
    ap.add_argument("--yaw", type=float, default=-35.0)
    ap.add_argument("--pitch", type=float, default=28.0)
    a = ap.parse_args()
    rasterize(build(a.lit, a.spin, a.phase), a.out, a.size, a.yaw, a.pitch)
