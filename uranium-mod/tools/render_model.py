"""Software renderer for Minecraft block models.

Parses a model's parent chain, resolves its textures, and rasterises the
elements to a PNG so a model can be checked without launching the game.

    python3 tools/render_model.py uraniummod:block/centrifuge out.png

Supports element rotation, per-face UVs and Minecraft's own directional face
shading. Animated textures are rendered from a chosen frame (--frame).
"""
import argparse, json, math, os, struct, sys, zipfile, zlib

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                    "src", "main", "resources")
NS = "uraniummod"
VANILLA = os.environ.get(
    "MC_CLIENT_JAR", "/root/.gradle/caches/fabric-loom/1.21.4/minecraft-client.jar")

# ------------------------------------------------------------------ png io
def read_png(path):
    d = open(path, "rb").read()
    i, idat, w, h = 8, b"", 0, 0
    while i < len(d):
        ln = struct.unpack(">I", d[i:i+4])[0]; tag = d[i+4:i+8]; data = d[i+8:i+8+ln]
        if tag == b"IHDR": w, h = struct.unpack(">II", data[:8])
        if tag == b"IDAT": idat += data
        i += 12 + ln
    raw = zlib.decompress(idat); st = w*4; prev = bytearray(st); o = 0; out = []
    for _ in range(h):
        f = raw[o]; o += 1; L = bytearray(raw[o:o+st]); o += st
        for x in range(st):
            a = L[x-4] if x >= 4 else 0; b = prev[x]; c = prev[x-4] if x >= 4 else 0
            if f == 1: L[x] = (L[x]+a) & 255
            elif f == 2: L[x] = (L[x]+b) & 255
            elif f == 3: L[x] = (L[x]+(a+b)//2) & 255
            elif f == 4:
                pp = a+b-c; pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                L[x] = (L[x]+pr) & 255
        prev = L
        out.append([tuple(L[x*4:x*4+4]) for x in range(w)])
    return out

def write_png(path, px):
    h, w = len(px), len(px[0])
    raw = b"".join(b"\x00" + bytes(c for p in row for c in p) for row in px)
    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t+d) & 0xffffffff)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
        + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b""))

# ------------------------------------------------------------------ assets
def rel_path(ident, kind, ext):
    ns, _, path = ident.rpartition(":")
    return (ns or "minecraft"), f"assets/{ns or 'minecraft'}/{kind}/{path}.{ext}"

def load_json_asset(ident, kind):
    ns, rel = rel_path(ident, kind, "json")
    if ns == NS:
        p = os.path.join(ROOT, rel)
        return json.load(open(p)) if os.path.exists(p) else None
    if not os.path.exists(VANILLA):
        return {}
    with zipfile.ZipFile(VANILLA) as z:
        return json.loads(z.read(rel)) if rel in z.namelist() else None

def resolve_model(ident):
    chain, cur, seen = [], ident, set()
    while cur and not cur.endswith(("builtin/generated", "builtin/entity")):
        if cur in seen: break
        seen.add(cur)
        data = load_json_asset(cur, "models")
        if data is None:
            raise SystemExit(f"missing model: {cur}")
        chain.append(data)
        cur = data.get("parent")
    textures, elements = {}, None
    for data in reversed(chain):
        textures.update(data.get("textures", {}))
    for data in chain:
        if "elements" in data:
            elements = data["elements"]; break
    return textures, (elements or [])

_tex_cache = {}
def load_texture(ident, frame=0):
    key = (ident, frame)
    if key in _tex_cache:
        return _tex_cache[key]
    ns, rel = rel_path(ident, "textures", "png")
    if ns == NS:
        img = read_png(os.path.join(ROOT, rel))
    else:
        with zipfile.ZipFile(VANILLA) as z:
            tmp = "/tmp/_rm_tex.png"
            open(tmp, "wb").write(z.read(rel))
            img = read_png(tmp)
    w = len(img[0])
    if len(img) > w:                      # animation strip: take one frame
        n = len(img) // w
        f = frame % n
        img = img[f*w:(f+1)*w]
    _tex_cache[key] = img
    return img

def deref(textures, val):
    seen = set()
    while val.startswith("#"):
        k = val[1:]
        if k in seen or k not in textures:
            return None
        seen.add(k)
        val = textures[k]
    return val

# ------------------------------------------------------------------ geometry
FACE_SHADE = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8,
              "east": 0.6, "west": 0.6}

def box_face(x0, y0, z0, x1, y1, z1, face):
    """Returns 4 corners in order matching uv (u0,v0)-(u1,v1) top-left first."""
    if face == "north":   # -z, seen from outside
        return [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)]
    if face == "south":   # +z
        return [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)]
    if face == "west":    # -x
        return [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)]
    if face == "east":    # +x
        return [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)]
    if face == "up":      # +y
        return [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
    if face == "down":    # -y
        return [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)]
    raise ValueError(face)

def rotate_point(p, rot):
    if not rot:
        return p
    ox, oy, oz = rot["origin"]
    ang = math.radians(rot.get("angle", 0))
    axis = rot["axis"]
    x, y, z = p[0]-ox, p[1]-oy, p[2]-oz
    c, s = math.cos(ang), math.sin(ang)
    if axis == "x":   y, z = y*c - z*s, y*s + z*c
    elif axis == "y": x, z = x*c + z*s, -x*s + z*c
    else:             x, y = x*c - y*s, x*s + y*c
    if rot.get("rescale"):
        k = 1.0 / math.cos(ang) if abs(math.cos(ang)) > 1e-6 else 1.0
        if axis == "x":   y, z = y*k, z*k
        elif axis == "y": x, z = x*k, z*k
        else:             x, y = x*k, y*k
    return (x+ox, y+oy, z+oz)

# ------------------------------------------------------------------ render
def model_quads(model_id, frame=0):
    """Flatten a model's elements into (corners, uvs, texture_id, shade) quads."""
    textures, elements = resolve_model(model_id)
    quads = []
    for el in elements:
        x0, y0, z0 = el["from"]; x1, y1, z1 = el["to"]
        rot = el.get("rotation")
        for face, spec in el.get("faces", {}).items():
            tex_id = deref(textures, spec.get("texture", ""))
            if not tex_id:
                continue
            corners = [rotate_point(p, rot) for p in box_face(x0, y0, z0, x1, y1, z1, face)]
            u0, v0, u1, v1 = spec.get("uv", [0, 0, 16, 16])
            uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            quads.append((corners, uvs, tex_id, FACE_SHADE[face]))
    return quads

def rasterize(quads, out, size=512, yaw=-35.0, pitch=28.0, frame=0, bg=(0, 0, 0, 0), zoom=1.0):
    ss = 3                                     # supersample factor
    W = size * ss
    buf = [[bg for _ in range(W)] for _ in range(W)]
    zbuf = [[-1e9] * W for _ in range(W)]   # larger z is nearer

    cy, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    scale = W / (26.0 * zoom)

    def project(p):
        x, y, z = p[0]-8.0, p[1]-8.0, p[2]-8.0
        x, z = x*cy + z*sy_, -x*sy_ + z*cy
        y, z = y*cp - z*sp, y*sp + z*cp
        return (W/2 + x*scale, W/2 - y*scale, z)

    for corners, uvs, tex_id, shade in quads:
        tex = load_texture(tex_id, frame)
        th, tw = len(tex), len(tex[0])
        pts = [project(c) for c in corners]
        for tri in ((0, 1, 2), (0, 2, 3)):
            (ax, ay, az), (bx, by, bz), (cx_, cy_, cz) = (pts[i] for i in tri)
            (au, av), (bu, bv), (cu, cv) = (uvs[i] for i in tri)
            minx = max(0, int(min(ax, bx, cx_))); maxx = min(W-1, int(max(ax, bx, cx_)) + 1)
            miny = max(0, int(min(ay, by, cy_))); maxy = min(W-1, int(max(ay, by, cy_)) + 1)
            den = (by-cy_)*(ax-cx_) + (cx_-bx)*(ay-cy_)
            if abs(den) < 1e-9:
                continue
            for py in range(miny, maxy+1):
                for px_ in range(minx, maxx+1):
                    w0 = ((by-cy_)*(px_+0.5-cx_) + (cx_-bx)*(py+0.5-cy_)) / den
                    w1 = ((cy_-ay)*(px_+0.5-cx_) + (ax-cx_)*(py+0.5-cy_)) / den
                    w2 = 1.0 - w0 - w1
                    if w0 < -1e-6 or w1 < -1e-6 or w2 < -1e-6:
                        continue
                    depth = w0*az + w1*bz + w2*cz
                    if depth <= zbuf[py][px_]:
                        continue
                    u = w0*au + w1*bu + w2*cu
                    v = w0*av + w1*bv + w2*cv
                    tx = min(tw-1, max(0, int(u/16.0*tw)))
                    ty = min(th-1, max(0, int(v/16.0*th)))
                    col = tex[ty][tx]
                    if col[3] == 0:
                        continue
                    zbuf[py][px_] = depth
                    buf[py][px_] = (min(255, int(col[0]*shade)),
                                    min(255, int(col[1]*shade)),
                                    min(255, int(col[2]*shade)), 255)

    # box-filter the supersampled buffer down
    outpx = []
    for y in range(size):
        row = []
        for x in range(size):
            r = g = b = a = 0
            for dy in range(ss):
                for dx in range(ss):
                    p = buf[y*ss+dy][x*ss+dx]
                    r += p[0]*p[3]; g += p[1]*p[3]; b += p[2]*p[3]; a += p[3]
            if a == 0:
                row.append(bg)
            else:
                row.append((r//a, g//a, b//a, a//(ss*ss)))
        outpx.append(row)
    write_png(out, outpx)
    print(f"rendered -> {out} ({size}x{size}, {len(quads)} faces)")

def render(model_id, out, size=512, yaw=-35.0, pitch=28.0, frame=0, bg=(0, 0, 0, 0)):
    rasterize(model_quads(model_id, frame), out, size, yaw, pitch, frame, bg)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("out")
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--yaw", type=float, default=-35.0)
    ap.add_argument("--pitch", type=float, default=28.0)
    ap.add_argument("--frame", type=int, default=0)
    a = ap.parse_args()
    render(a.model, a.out, a.size, a.yaw, a.pitch, a.frame)
