"""Counts actual placed blocks in a generated world by parsing chunk NBT.

Run `./gradlew runServer` first so that `run/world/` exists, then:
    python3 tools/verify_worldgen.py
Point it at another world with WORLD=/path/to/world.
"""
import collections, glob, gzip, math, os, signal, struct, sys, zlib

signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # don't traceback when piped into head

WORLD = os.environ.get("WORLD", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "run", "world"))

# ------------------------------------------------------------------ NBT reader
class R:
    def __init__(self, b): self.b = b; self.i = 0
    def u1(self): v = self.b[self.i]; self.i += 1; return v
    def i1(self): v = struct.unpack_from(">b", self.b, self.i)[0]; self.i += 1; return v
    def i2(self): v = struct.unpack_from(">h", self.b, self.i)[0]; self.i += 2; return v
    def u2(self): v = struct.unpack_from(">H", self.b, self.i)[0]; self.i += 2; return v
    def i4(self): v = struct.unpack_from(">i", self.b, self.i)[0]; self.i += 4; return v
    def i8(self): v = struct.unpack_from(">q", self.b, self.i)[0]; self.i += 8; return v
    def f4(self): v = struct.unpack_from(">f", self.b, self.i)[0]; self.i += 4; return v
    def f8(self): v = struct.unpack_from(">d", self.b, self.i)[0]; self.i += 8; return v
    def s(self):
        n = self.u2(); v = self.b[self.i:self.i + n].decode("utf-8", "replace"); self.i += n; return v

def payload(r, t):
    if t == 1: return r.i1()
    if t == 2: return r.i2()
    if t == 3: return r.i4()
    if t == 4: return r.i8()
    if t == 5: return r.f4()
    if t == 6: return r.f8()
    if t == 7:
        n = r.i4()
        if n <= 0: return b""
        v = r.b[r.i:r.i + n]; r.i += n; return v
    if t == 8: return r.s()
    if t == 0: return None
    if t == 9:
        it = r.u1(); n = r.i4()
        if it == 0 or n <= 0: return []
        return [payload(r, it) for _ in range(n)]
    if t == 10:
        d = {}
        while True:
            ct = r.u1()
            if ct == 0: return d
            name = r.s()                    # must read the key BEFORE the payload
            d[name] = payload(r, ct)
    if t == 11:
        n = r.i4()
        if n <= 0: return []
        v = list(struct.unpack_from(">%di" % n, r.b, r.i)); r.i += 4 * n; return v
    if t == 12:
        n = r.i4()
        if n <= 0: return []
        v = list(struct.unpack_from(">%dq" % n, r.b, r.i)); r.i += 8 * n; return v
    raise ValueError("tag %d" % t)

def parse_nbt(raw):
    r = R(raw); t = r.u1()
    if t == 0: return {}
    r.s()
    return payload(r, t)

# ------------------------------------------------------------------ region reader
def region_chunks(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 8192: return
    for i in range(1024):
        rec = struct.unpack(">I", data[i * 4:i * 4 + 4])[0]
        off, cnt = rec >> 8, rec & 0xff
        if not off or not cnt: continue
        p = off * 4096
        if p + 5 > len(data): continue
        ln = struct.unpack(">I", data[p:p + 4])[0]
        comp = data[p + 4]
        blob = data[p + 5:p + 4 + ln]
        try:
            if comp == 1: yield parse_nbt(gzip.decompress(blob))
            elif comp == 2: yield parse_nbt(zlib.decompress(blob))
            elif comp == 3: yield parse_nbt(blob)
        except Exception:
            continue

# ------------------------------------------------------------------ block counting
def unpack_states(data, palette_len, count=4096):
    """1.16+ packing: entries never span a long."""
    bits = max(4, (palette_len - 1).bit_length())
    per_long = 64 // bits
    mask = (1 << bits) - 1
    out = []
    for lng in data:
        u = lng & 0xFFFFFFFFFFFFFFFF
        for k in range(per_long):
            if len(out) >= count: return out
            out.append((u >> (k * bits)) & mask)
    return out

TRACK = ("uraniummod:uranium_ore", "uraniummod:deepslate_uranium_ore",
         "minecraft:iron_ore", "minecraft:deepslate_iron_ore",
         "minecraft:diamond_ore", "minecraft:deepslate_diamond_ore",
         "minecraft:emerald_ore", "minecraft:deepslate_emerald_ore",
         "minecraft:ancient_debris")

counts = collections.Counter()
ylevels = collections.Counter()
chunks = 0
skipped = 0
for path in sorted(glob.glob(os.path.join(WORLD, "region", "*.mca"))):
    for ch in region_chunks(path):
        # Edge chunks are saved as proto-chunks with the ore step not yet run;
        # counting them would understate the real density.
        if ch.get("Status") != "minecraft:full": 
            skipped += 1
            continue
        secs = ch.get("sections")
        if not secs: continue
        chunks += 1
        for sec in secs:
            bs = sec.get("block_states")
            if not bs: continue
            pal = [e.get("Name") for e in bs.get("palette", [])]
            if not any(n in TRACK for n in pal): continue
            data = bs.get("data")
            ybase = sec.get("Y", 0) * 16
            if data is None:
                if pal and pal[0] in TRACK:
                    counts[pal[0]] += 4096
                continue
            idx = unpack_states(data, len(pal))
            for pos, v in enumerate(idx):
                if v < len(pal) and pal[v] in TRACK:
                    counts[pal[v]] += 1
                    if pal[v].startswith("uraniummod:"):
                        ylevels[ybase + (pos >> 8)] += 1

print(f"fully generated chunks: {chunks}   (skipped {skipped} proto-chunks)\n")
ur = counts["uraniummod:uranium_ore"] + counts["uraniummod:deepslate_uranium_ore"]
print(f"{'block':<40} {'total':>8} {'per chunk':>10}")
print("-" * 60)
for name in TRACK:
    c = counts[name]
    print(f"{name:<40} {c:>8} {c / max(chunks,1):>10.2f}")
print("-" * 60)
print(f"{'URANIUM (both)':<40} {ur:>8} {ur / max(chunks,1):>10.2f}")

if ylevels:
    print("\nuranium by y-level (10-block bands):")
    bands = collections.Counter()
    for y, c in ylevels.items():
        bands[(y // 10) * 10] += c
    peak = max(bands.values())
    for b in sorted(bands, reverse=True):
        bar = "#" * max(1, round(bands[b] / peak * 44))
        print(f"  y {b:>4}..{b+9:<4} {bands[b]:>6}  {bar}")
sys.exit(0 if ur else 1)
