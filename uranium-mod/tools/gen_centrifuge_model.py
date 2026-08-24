"""Builds the centrifuge block model: three drums on a plinth, Factorio-style.

    python3 tools/gen_centrifuge_model.py

Writes models/block/centrifuge.json and centrifuge_on.json. The two differ only
in whether the drum body uses the animated glowing texture.
"""
import json, os

NS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                  "src", "main", "resources", "assets", "uraniummod")

# drum footprints: two at the front (-z), one behind, as in the reference
DRUMS = [(1, 1), (9, 1), (5, 8)]     # from-x, from-z of each 6x6 drum
DRUM_W = 6
BODY_Y0, BODY_Y1 = 3, 12
CAP_Y0, CAP_Y1 = 12, 14

# gold arms: (from, to, rotation axis, angle). Each leans out over its drum.
ARMS = [
    ([2.6, 11.0, 2.6], [4.1, 16.0, 4.1], "z", 45),
    ([11.9, 11.0, 2.6], [13.4, 16.0, 4.1], "z", -45),
    ([7.25, 11.0, 10.4], [8.75, 16.0, 11.9], "x", -45),
]

def face(tex, uv=None, cull=None):
    f = {"texture": tex}
    if uv is not None:
        f["uv"] = uv
    if cull:
        f["cullface"] = cull
    return f

def build(on):
    drum_tex = "uraniummod:block/centrifuge_drum_on" if on else \
               "uraniummod:block/centrifuge_drum"
    textures = {
        "particle": "uraniummod:block/centrifuge_base",
        "bottom": "uraniummod:block/centrifuge_bottom",
        "base":   "uraniummod:block/centrifuge_base",
        "deck":   "uraniummod:block/centrifuge_deck",
        "drum":   drum_tex,
        "cap":    "uraniummod:block/centrifuge_cap",
        "drumtop": "uraniummod:block/centrifuge_drum_top_on" if on else
                   "uraniummod:block/centrifuge_drum_top",
        "arm":    "uraniummod:block/centrifuge_arm",
        "pipe":   "uraniummod:block/centrifuge_pipe",
    }

    elements = []

    # plinth. A 3px-tall face needs a 3px slice or the diagonal hazard
    # stripes squash into flat lines.
    plinth = {"from": [0, 0, 0], "to": [16, 3, 16], "faces": {
        "down": face("#bottom", [0, 0, 16, 16], "down"),
        "up":   face("#deck", [0, 0, 16, 16]),
    }}
    for d, cull in (("north", "north"), ("south", "south"),
                    ("east", "east"), ("west", "west")):
        plinth["faces"][d] = face("#base", [0, 6, 16, 9], cull)
    elements.append(plinth)

    for (dx, dz) in DRUMS:
        elements.append({
            "from": [dx, BODY_Y0, dz],
            "to":   [dx + DRUM_W, BODY_Y1, dz + DRUM_W],
            "faces": {d: face("#drum", [0, 0, 16, 16])
                      for d in ("north", "south", "east", "west")},
        })
        elements.append({
            "from": [dx - 0.5, CAP_Y0, dz - 0.5],
            "to":   [dx + DRUM_W + 0.5, CAP_Y1, dz + DRUM_W + 0.5],
            "faces": {
                **{d: face("#cap", [0, 0, 16, 16])
                   for d in ("north", "south", "east", "west")},
                "up": face("#drumtop", [0, 0, 16, 16]),
            },
        })

    for (a, b, axis, angle) in ARMS:
        origin = [(a[0] + b[0]) / 2.0, a[1], (a[2] + b[2]) / 2.0]
        elements.append({
            "from": a, "to": b,
            "rotation": {"origin": origin, "axis": axis,
                         "angle": angle, "rescale": True},
            "faces": {d: face("#arm", [0, 0, 16, 16])
                      for d in ("north", "south", "east", "west", "up")},
        })

    # feed pipe across the front of the plinth
    elements.append({
        "from": [5, 3, 0.5], "to": [11, 5, 2.5],
        "faces": {
            **{d: face("#pipe", [0, 0, 16, 16])
               for d in ("north", "south", "east", "west")},
            "up": face("#pipe", [0, 0, 16, 16]),
        },
    })

    return {"parent": "block/block", "textures": textures, "elements": elements}

for on, name in ((False, "centrifuge"), (True, "centrifuge_on")):
    path = os.path.join(NS, "models", "block", f"{name}.json")
    with open(path, "w") as f:
        json.dump(build(on), f, indent=2)
        f.write("\n")
    print("wrote", os.path.relpath(path, NS))
