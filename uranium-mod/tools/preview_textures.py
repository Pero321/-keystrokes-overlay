"""Renders an upscaled contact sheet of the mod's textures (for eyeballing)."""
import os, struct, sys, zlib
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "src", "main", "resources", "assets", "uraniummod")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "docs", "textures.png")

def read_png(p):
    d = open(p, "rb").read(); i = 8; idat = b""; w = h = 0
    while i < len(d):
        ln = struct.unpack(">I", d[i:i+4])[0]; tag = d[i+4:i+8]; data = d[i+8:i+8+ln]
        if tag == b"IHDR": w, h = struct.unpack(">II", data[:8])
        if tag == b"IDAT": idat += data
        i += 12 + ln
    raw = zlib.decompress(idat); px = []; stride = w*4; prev = bytearray(stride); o = 0
    for _ in range(h):
        f = raw[o]; o += 1; line = bytearray(raw[o:o+stride]); o += stride
        for x in range(stride):
            a = line[x-4] if x >= 4 else 0; b = prev[x]; c = prev[x-4] if x >= 4 else 0
            if f == 1: line[x] = (line[x]+a) & 255
            elif f == 2: line[x] = (line[x]+b) & 255
            elif f == 3: line[x] = (line[x]+(a+b)//2) & 255
            elif f == 4:
                pp = a+b-c; pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x]+pr) & 255
        prev = line
        px.append([tuple(line[x*4:x*4+4]) for x in range(w)])
    return px

def write_png(path, px):
    h, w = len(px), len(px[0])
    raw = b"".join(b"\x00" + bytes(c for p in row for c in p) for row in px)
    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t+d) & 0xffffffff)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
        + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b""))

if __name__ == "__main__":
    NAMES = [
        "textures/block/uranium_ore.png", "textures/block/deepslate_uranium_ore.png",
        "textures/item/raw_uranium.png", "textures/item/uranium_ingot.png",
        "textures/block/raw_uranium_block.png", "textures/block/uranium_block.png",
        "textures/block/centrifuge_rotor_top.png", "textures/block/centrifuge_base.png",
        "textures/block/centrifuge_deck.png", "textures/block/centrifuge_shaft.png",
    ]
    S, PAD, COLS = 11, 8, 5
    tiles = [read_png(os.path.join(RES, n)) for n in NAMES]
    rows = (len(tiles) + COLS - 1) // COLS
    W = PAD + COLS * (16*S + PAD)
    H = PAD + rows * (16*S + PAD)
    canvas = [[(26, 26, 30, 255) for _ in range(W)] for _ in range(H)]
    for i, t in enumerate(tiles):
        ox = PAD + (i % COLS) * (16*S + PAD)
        oy = PAD + (i // COLS) * (16*S + PAD)
        for y in range(16*S):
            for x in range(16*S):
                p = t[y//S][x//S]
                if len(p) == 4 and p[3] == 0:
                    p = (58, 58, 64, 255) if ((x//8 + y//8) % 2 == 0) else (46, 46, 52, 255)
                canvas[oy+y][ox+x] = p[:3] + (255,)
    write_png(OUT, canvas)
    print(f"wrote {OUT} ({W}x{H})")
