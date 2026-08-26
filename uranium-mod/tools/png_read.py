"""Minimal PNG reader that handles the colour types Minecraft actually ships:
truecolour+alpha, truecolour, indexed (with tRNS) and greyscale+alpha."""
import struct, zlib

def read_png(path):
    d = open(path, 'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n', path
    i, idat, plte, trns = 8, b'', None, None
    while i < len(d):
        ln = struct.unpack(">I", d[i:i+4])[0]
        typ, data = d[i+4:i+8], d[i+8:i+8+ln]
        if typ == b'IHDR':
            w, h, depth, ctype = struct.unpack(">IIBB", data[:10])
        elif typ == b'PLTE': plte = data
        elif typ == b'tRNS': trns = data
        elif typ == b'IDAT': idat += data
        i += 12 + ln
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    # sub-byte depths only occur for indexed/greyscale, where several pixels
    # share a byte -- vanilla ships many textures as 4-bit indexed, which by
    # itself says their palettes fit in 16 colours
    stride = (w * channels * depth + 7) // 8
    raw = zlib.decompress(idat)
    prev, out, pos = bytearray(stride), [], 0
    for _ in range(h):
        f = raw[pos]; pos += 1
        line = bytearray(raw[pos:pos+stride]); pos += stride
        for x in range(stride):
            a = line[x-channels] if x >= channels else 0
            b = prev[x]
            c = prev[x-channels] if x >= channels else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        prev = line
        if depth < 8:
            unpacked = bytearray()
            per = 8 // depth
            mask = (1 << depth) - 1
            for byte in line:
                for k in range(per - 1, -1, -1):
                    unpacked.append((byte >> (k * depth)) & mask)
            line = unpacked[:w * channels]
        row = []
        for x in range(w):
            if ctype == 6:   px = tuple(line[x*4:x*4+4])
            elif ctype == 2: px = tuple(line[x*3:x*3+3]) + (255,)
            elif ctype == 4: px = (line[x*2],)*3 + (line[x*2+1],)
            elif ctype == 0: px = (line[x],)*3 + (255,)
            else:
                idx = line[x]
                px = tuple(plte[idx*3:idx*3+3]) + (
                    (trns[idx] if trns and idx < len(trns) else 255),)
            row.append(px)
        out.append(row)
    return w, h, out
