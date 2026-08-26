"""Writes the centrifuge's baked model and blockstate.

Only the plinth is baked: the rotor tower is drawn by
CentrifugeBlockEntityRenderer, which can make it an actual cylinder and turn it.
The same plinth model is reused for the item, so the block still shows something
sensible in the inventory.
"""
import json, os

NS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                  "src", "main", "resources", "assets", "uraniummod")

def build():
    """The in-world model is empty: CentrifugeBlockEntityRenderer draws the whole
    3x3x2 machine as triangles. Only the particle texture is declared."""
    return {"textures": {"particle": "uraniummod:block/centrifuge_base"}}

def build_item():
    """Inventory icon. The in-world machine is drawn by the renderer, so the item
    needs geometry of its own: a stepped drum that reads at 16px in a hotbar.

    The tower map is 128 wide (sixteen panels around the drum). Sampling all of
    it onto a 12px face squashes it into stripes, so the icon takes a two-panel
    slice: u 0..2 of the 0..16 uv space is texture columns 0..16.
    """
    tex = {
        "particle": "uraniummod:block/centrifuge_base",
        "base": "uraniummod:block/centrifuge_base",
        "deck": "uraniummod:block/centrifuge_deck",
        "tower": "uraniummod:block/centrifuge_tower",
        "rotor": "uraniummod:block/centrifuge_rotor_top",
    }
    PANELS = 2.0                       # texture columns 0..16 of 128

    def stack(x0, y0, z0, x1, y1, z1, v0, v1, top=None):
        uv = [0, v0, PANELS, v1]
        faces = {d: {"texture": "#tower", "uv": uv}
                 for d in ("north", "south", "east", "west")}
        if top:
            faces["up"] = {"texture": top, "uv": [0, 0, 16, 16]}
        return {"from": [x0, y0, z0], "to": [x1, y1, z1], "faces": faces}

    # v-bands of the 128x24 map, expressed in the 0..16 uv space
    LOWER0, LOWER1 = 0.0, 4.0 / 24.0 * 16
    BODY0, BODY1 = 4.0 / 24.0 * 16, 20.0 / 24.0 * 16
    UPPER0, UPPER1 = 20.0 / 24.0 * 16, 16.0

    return {
        "parent": "block/block",
        "textures": tex,
        "elements": [
            {"from": [1, 0, 1], "to": [15, 2, 15], "faces": {
                **{d: {"texture": "#base", "uv": [0, 6, 16, 9]}
                   for d in ("north", "south", "east", "west")},
                "down": {"texture": "#base", "uv": [0, 0, 16, 16]},
            }},
            stack(1, 2, 1, 15, 5, 15, LOWER0, LOWER1),
            stack(2, 5, 2, 14, 13, 14, BODY0, BODY1),
            stack(1, 13, 1, 15, 16, 15, UPPER0, UPPER1, top="#rotor"),
        ],
    }


for name, model in (("centrifuge_static", build()), ("centrifuge", build_item())):
    path = os.path.join(NS, "models", "block", f"{name}.json")
    with open(path, "w") as f:
        json.dump(model, f, indent=2)
        f.write("\n")
    print("wrote", os.path.relpath(path, NS))

# every state renders the same empty shell; the renderer draws the machine
rot = {"north": 0, "east": 90, "south": 180, "west": 270}
variants = {}
for facing, y in rot.items():
    for lit in ("false", "true"):
        v = {"model": "uraniummod:block/centrifuge_static"}
        if y:
            v["y"] = y
        variants[f"facing={facing},lit={lit}"] = v
bs = os.path.join(NS, "blockstates", "centrifuge.json")
with open(bs, "w") as f:
    json.dump({"variants": variants}, f, indent=2)
    f.write("\n")
print("wrote", os.path.relpath(bs, NS))
