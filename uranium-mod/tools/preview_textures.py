import struct, zlib, os
RES="/home/user/-keystrokes-overlay/uranium-mod/src/main/resources/assets/uraniummod"
SP="/tmp/claude-0/-home-user--keystrokes-overlay/94f777ea-8854-572f-8986-0729a0b66d98/scratchpad"

def read_png(p):
    d=open(p,'rb').read(); i=8; idat=b''; w=h=0
    while i<len(d):
        ln=struct.unpack('>I',d[i:i+4])[0]; tag=d[i+4:i+8]; data=d[i+8:i+8+ln]
        if tag==b'IHDR': w,h=struct.unpack('>II',data[:8])
        if tag==b'IDAT': idat+=data
        i+=12+ln
    raw=zlib.decompress(idat); px=[]; stride=w*4; prev=bytearray(stride); o=0
    for y in range(h):
        f=raw[o]; o+=1; line=bytearray(raw[o:o+stride]); o+=stride
        for x in range(stride):
            a=line[x-4] if x>=4 else 0; b=prev[x]; c=prev[x-4] if x>=4 else 0
            if f==1: line[x]=(line[x]+a)&255
            elif f==2: line[x]=(line[x]+b)&255
            elif f==3: line[x]=(line[x]+(a+b)//2)&255
            elif f==4:
                pp=a+b-c; pa=abs(pp-a); pb=abs(pp-b); pc=abs(pp-c)
                pr=a if (pa<=pb and pa<=pc) else (b if pb<=pc else c)
                line[x]=(line[x]+pr)&255
        prev=line
        px.append([tuple(line[x*4:x*4+4]) for x in range(w)])
    return px

def write_png(path,px):
    h=len(px); w=len(px[0])
    raw=b"".join(b"\x00"+bytes(c for p in row for c in p) for row in px)
    def ch(t,d): return struct.pack(">I",len(d))+t+d+struct.pack(">I",zlib.crc32(t+d)&0xffffffff)
    open(path,'wb').write(b"\x89PNG\r\n\x1a\n"+ch(b'IHDR',struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+ch(b'IDAT',zlib.compress(raw,9))+ch(b'IEND',b''))

names=[("textures/block/uranium_ore.png","ore"),("textures/block/deepslate_uranium_ore.png","deepslate"),
       ("textures/block/raw_uranium_block.png","raw_block"),("textures/block/uranium_block.png","metal_block"),
       ("textures/item/raw_uranium.png","raw_item"),("textures/item/uranium_ingot.png","ingot")]
S=12; PAD=6; CH=(60,60,66,255); CH2=(48,48,54,255)
tiles=[read_png(f"{RES}/{n}") for n,_ in names]
W=len(tiles)*(16*S+PAD)+PAD; H=16*S+2*PAD
canvas=[[(30,30,34,255)]*W for _ in range(H)]
for ti,t in enumerate(tiles):
    ox=PAD+ti*(16*S+PAD)
    for y in range(16*S):
        for x in range(16*S):
            p=t[y//S][x//S]
            if p[3]==0:
                p = CH if ((x//8+y//8)%2==0) else CH2
            canvas[PAD+y][ox+x]=p[:3]+(255,)
write_png(f"{SP}/preview.png",canvas)
print("preview written", W, "x", H)
