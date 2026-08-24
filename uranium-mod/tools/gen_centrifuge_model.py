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
    plinth = {"from": [0, 0, 0], "to": [16, 1.5, 16], "faces": {
        "down": {"texture": "#bottom", "uv": [0, 0, 16, 16], "cullface": "down"},
        "up": {"texture": "#deck", "uv": [0, 0, 16, 16]},
    }}
    for d in ("north", "south", "east", "west"):
        # a 1.5px-tall face needs a thin slice, or the hazard stripes flatten out
        plinth["faces"][d] = {"texture": "#base", "uv": [0, 7, 16, 8.5], "cullface": d}
    return {
        "parent": "block/block",
        "textures": {
            "particle": "uraniummod:block/centrifuge_base",
            "bottom": "uraniummod:block/centrifuge_bottom",
            "base": "uraniummod:block/centrifuge_base",
            "deck": "uraniummod:block/centrifuge_deck",
        },
        "elements": [plinth],
    }

model = build()
for name in ("centrifuge_static", "centrifuge"):
    path = os.path.join(NS, "models", "block", f"{name}.json")
    with open(path, "w") as f:
        json.dump(model, f, indent=2)
        f.write("\n")
    print("wrote", os.path.relpath(path, NS))

# every state uses the same plinth; the renderer handles lit vs idle
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
