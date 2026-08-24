"""Walks blockstates -> models -> textures and checks every reference resolves.

Catches the failure mode you can't see without launching the game: a model
pointing at a texture that isn't there, an unresolved #placeholder, or an
animation strip whose height isn't a whole number of frames.
"""
import json, os, re, struct, sys, zipfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                    "src", "main", "resources")
NS = "uraniummod"
VANILLA = os.environ.get(
    "MC_CLIENT_JAR", "/root/.gradle/caches/fabric-loom/1.21.4/minecraft-client.jar")
BUILTIN = {"builtin/generated", "builtin/entity", "minecraft:builtin/generated",
           "minecraft:builtin/entity"}

errors = []
seen_textures = set()
checked = {"blockstates": 0, "models": 0, "textures": 0, "anim": 0,
           "java_textures": 0}

vanilla = set()
if os.path.exists(VANILLA):
    with zipfile.ZipFile(VANILLA) as z:
        vanilla = set(z.namelist())
else:
    print(f"note: {VANILLA} not found, vanilla refs will be assumed valid")

def rel_path(ident, kind, ext):
    ns, _, path = ident.rpartition(":")
    ns = ns or "minecraft"
    return ns, f"assets/{ns}/{kind}/{path}.{ext}"

def read_model(ident):
    ns, rel = rel_path(ident, "models", "json")
    if ns == NS:
        full = os.path.join(ROOT, rel)
        if not os.path.exists(full):
            return None
        checked["models"] += 1
        return json.load(open(full))
    if not vanilla:
        return {}
    if rel not in vanilla:
        return None
    with zipfile.ZipFile(VANILLA) as z:
        return json.loads(z.read(rel))

def resolve(ident):
    """Merge a model's parent chain. Returns (textures, elements, chain)."""
    chain, textures, elements = [], {}, None
    seen, cur = set(), ident
    while cur and cur not in BUILTIN:
        if cur in seen:
            errors.append(f"{ident}: parent cycle at {cur}")
            break
        seen.add(cur)
        data = read_model(cur)
        if data is None:
            errors.append(f"{ident}: missing model in chain: {cur}")
            break
        chain.append((cur, data))
        cur = data.get("parent")
    # parents first so children override; elements come from the nearest
    # model in the chain that declares them, exactly as Minecraft does
    for name, data in reversed(chain):
        textures.update(data.get("textures", {}))
    for name, data in chain:
        if "elements" in data:
            elements = (name, data["elements"])
            break
    return textures, elements, chain

def deref(textures, value, ident, where):
    """Follow #placeholders to a concrete texture id."""
    seen = set()
    while value.startswith("#"):
        key = value[1:]
        if key in seen:
            errors.append(f"{ident}: texture reference cycle on #{key}")
            return None
        seen.add(key)
        if key not in textures:
            errors.append(f"{ident}: {where} uses undefined #{key}")
            return None
        value = textures[key]
    return value

def check_texture_file(ident, value, where):
    ns, rel = rel_path(value, "textures", "png")
    if ns == NS:
        if not os.path.exists(os.path.join(ROOT, rel)):
            errors.append(f"{ident}: {where} -> missing texture {value}")
            return
    elif vanilla and rel not in vanilla:
        errors.append(f"{ident}: {where} -> missing vanilla texture {value}")
        return
    checked["textures"] += 1
    seen_textures.add(value)

def check_model(ident):
    textures, elements, chain = resolve(ident)
    if not chain:
        return
    if elements:
        owner, els = elements
        for i, el in enumerate(els):
            for face, spec in el.get("faces", {}).items():
                t = spec.get("texture", "")
                r = deref(textures, t, ident, f"element {i} face '{face}'")
                if r:
                    check_texture_file(ident, r, f"element {i} face '{face}'")
    else:
        # no geometry (e.g. builtin/generated): just check the declared layers
        for key, val in textures.items():
            r = deref(textures, val, ident, f"texture '{key}'")
            if r:
                check_texture_file(ident, r, f"texture '{key}'")

for name in sorted(os.listdir(os.path.join(ROOT, "assets", NS, "blockstates"))):
    data = json.load(open(os.path.join(ROOT, "assets", NS, "blockstates", name)))
    checked["blockstates"] += 1
    for variant in data.get("variants", {}).values():
        for v in (variant if isinstance(variant, list) else [variant]):
            check_model(v["model"])

for name in sorted(os.listdir(os.path.join(ROOT, "assets", NS, "items"))):
    data = json.load(open(os.path.join(ROOT, "assets", NS, "items", name)))
    m = data.get("model", {}).get("model")
    if not m:
        errors.append(f"items/{name}: no model declared")
    else:
        check_model(m)

tex_dir = os.path.join(ROOT, "assets", NS, "textures")
for dirpath, _, files in os.walk(tex_dir):
    for f in files:
        full = os.path.join(dirpath, f)
        if f.endswith(".png"):
            if open(full, "rb").read(8) != b"\x89PNG\r\n\x1a\n":
                errors.append(f"{f}: not a valid png")
        elif f.endswith(".mcmeta"):
            png = full[:-len(".mcmeta")]
            if not os.path.exists(png):
                errors.append(f"{f}: no matching png")
                continue
            json.load(open(full))
            w, h = struct.unpack(">II", open(png, "rb").read(24)[16:24])
            if h % w:
                errors.append(f"{os.path.basename(png)}: {w}x{h} is not a whole "
                              f"number of {w}x{w} frames")
            else:
                checked["anim"] += 1

# Textures bound directly from Java (the block entity renderer) are invisible to
# the model walk above, so a typo there would only show up as a missing-texture
# checkerboard in game. Check those literals too.
JAVA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                         "src", "main", "java")
lit_re = re.compile(r'"(textures/[A-Za-z0-9_/]+\.png)"')
for dirpath, _, files in os.walk(JAVA_ROOT):
    for f in files:
        if not f.endswith(".java"):
            continue
        src = open(os.path.join(dirpath, f)).read()
        for rel in lit_re.findall(src):
            full = os.path.join(ROOT, "assets", NS, rel)
            if os.path.exists(full):
                checked["java_textures"] += 1
            else:
                errors.append(f"{f}: references missing texture {NS}:{rel}")

# Report textures nothing points at any more. Not an error -- icon.png and the
# like are referenced from fabric.mod.json -- but dead art quietly bloats the jar.
referenced = set()
for dirpath, _, files in os.walk(os.path.join(ROOT, "assets", NS, "textures")):
    for f in files:
        if f.endswith(".png"):
            referenced.add(os.path.join(dirpath, f))
used = set()
for ident in sorted(seen_textures):
    ns, rel = rel_path(ident, "textures", "png")
    if ns == NS:
        used.add(os.path.normpath(os.path.join(ROOT, rel)))
for dirpath, _, files in os.walk(JAVA_ROOT):
    for f in files:
        if f.endswith(".java"):
            for rel in lit_re.findall(open(os.path.join(dirpath, f)).read()):
                used.add(os.path.normpath(os.path.join(ROOT, "assets", NS, rel)))
unused = sorted(os.path.relpath(p2, ROOT) for p2 in
                {os.path.normpath(x) for x in referenced} - used)

print("checked: " + ", ".join(f"{v} {k}" for k, v in checked.items()))
if unused:
    print("\nunreferenced textures (not an error):")
    for u in unused:
        print("  -", u)
if errors:
    print("\nPROBLEMS:")
    for e in dict.fromkeys(errors):
        print("  -", e)
    sys.exit(1)
print("all asset references resolve")
