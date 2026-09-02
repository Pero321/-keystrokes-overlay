#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Готує map-data.js — контури країн Європи для тренажера.

Джерело даних: Natural Earth 1:50m Admin 0 (public domain) у вигляді TopoJSON
з пакета world-atlas:

    curl -o countries-50m.json \
        https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json

Запуск:

    python3 tools/gen-map.py countries-50m.json map-data.js

Що робить скрипт понад просте перетворення TopoJSON -> SVG:
  * повертає Крим Україні (Natural Earth відносить його до Росії);
  * розгортає довготу через 180-й меридіан, інакше кільце материкової
    Росії після обрізання дає фальшиву смугу через усю карту;
  * проєкція Ламберта (рівновелика азимутальна) з центром на Європі;
  * обрізає все до кадру «Ісландія - Урал, Крит - Нордкап»;
  * спрощує контури (Дуглас-Пекер) до розміру, що має сенс для карти
    завширшки ~1000 px, і рахує точку для підпису кожної країни.
"""

import json
import math
import os
import sys

def load(path):
    return json.load(open(path))

def decode_arcs(topo):
    sx, sy = topo['transform']['scale']
    tx, ty = topo['transform']['translate']
    out = []
    for arc in topo['arcs']:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx; y += dy
            pts.append((x*sx+tx, y*sy+ty))
        out.append(pts)
    return out

def ring(arcs, idxs):
    pts = []
    for i in idxs:
        if i >= 0:
            seg = arcs[i]
        else:
            seg = arcs[~i][::-1]
        if pts: seg = seg[1:]
        pts.extend(seg)
    return pts

def polys(arcs, geom):
    t = geom['type']
    if t == 'Polygon':
        return [[ring(arcs, r) for r in geom['arcs']]]
    if t == 'MultiPolygon':
        return [[ring(arcs, r) for r in p] for p in geom['arcs']]
    return []

def pip(pt, poly):
    x, y = pt; inside = False
    n = len(poly)
    for i in range(n):
        x1,y1 = poly[i]; x2,y2 = poly[(i+1)%n]
        if (y1>y) != (y2>y):
            xi = (x2-x1)*(y-y1)/(y2-y1)+x1
            if x < xi: inside = not inside
    return inside


SRC = sys.argv[1] if len(sys.argv) > 1 else 'countries-50m.json'
DST = sys.argv[2] if len(sys.argv) > 2 else 'map-data.js'

T = load(SRC)
ARCS = decode_arcs(T)
GEOMS = {x['properties']['name']: x for x in T['objects']['countries']['geometries']}

# quiz country -> (ukrainian name, region key, natural-earth source names)
QUIZ = [
 ("IS","Ісландія","north",["Iceland"]),
 ("NO","Норвегія","north",["Norway"]),
 ("SE","Швеція","north",["Sweden"]),
 ("FI","Фінляндія","north",["Finland","Åland"]),
 ("DK","Данія","north",["Denmark"]),
 ("EE","Естонія","north",["Estonia"]),
 ("LV","Латвія","north",["Latvia"]),
 ("LT","Литва","north",["Lithuania"]),
 ("GB","Велика Британія","north",["United Kingdom"]),
 ("IE","Ірландія","north",["Ireland"]),

 ("FR","Франція","west",["France"]),
 ("DE","Німеччина","west",["Germany"]),
 ("NL","Нідерланди","west",["Netherlands"]),
 ("BE","Бельгія","west",["Belgium"]),
 ("LU","Люксембург","west",["Luxembourg"]),
 ("CH","Швейцарія","west",["Switzerland"]),
 ("AT","Австрія","west",["Austria"]),
 ("MC","Монако","west",["Monaco"]),
 ("LI","Ліхтенштейн","west",["Liechtenstein"]),

 ("PL","Польща","central",["Poland"]),
 ("CZ","Чехія","central",["Czechia"]),
 ("SK","Словаччина","central",["Slovakia"]),
 ("HU","Угорщина","central",["Hungary"]),
 ("RO","Румунія","central",["Romania"]),
 ("BG","Болгарія","central",["Bulgaria"]),

 ("UA","Україна","east",["Ukraine"]),
 ("BY","Білорусь","east",["Belarus"]),
 ("MD","Молдова","east",["Moldova"]),
 ("RU","Росія","east",["Russia"]),

 ("PT","Португалія","south",["Portugal"]),
 ("ES","Іспанія","south",["Spain"]),
 ("AD","Андорра","south",["Andorra"]),
 ("IT","Італія","south",["Italy"]),
 ("SM","Сан-Марино","south",["San Marino"]),
 ("VA","Ватикан","south",["Vatican"]),
 ("MT","Мальта","south",["Malta"]),
 ("SI","Словенія","south",["Slovenia"]),
 ("HR","Хорватія","south",["Croatia"]),
 ("BA","Боснія і Герцеговина","south",["Bosnia and Herz."]),
 ("RS","Сербія","south",["Serbia"]),
 ("ME","Чорногорія","south",["Montenegro"]),
 ("XK","Косово","south",["Kosovo"]),
 ("MK","Північна Македонія","south",["Macedonia"]),
 ("AL","Албанія","south",["Albania"]),
 ("GR","Греція","south",["Greece"]),
 ("CY","Кіпр","south",["Cyprus","N. Cyprus"]),
 ("TR","Туреччина","south",["Turkey"]),
]

BACKDROP = ["Morocco","Algeria","Tunisia","Libya","Egypt","Syria","Lebanon","Israel","Palestine",
            "Iraq","Iran","Jordan","Saudi Arabia","Georgia","Armenia","Azerbaijan","Kazakhstan",
            "Turkmenistan","Uzbekistan","Greenland","Faeroe Is.","Isle of Man","Jersey","Guernsey",
            "W. Sahara","Mauritania","Mali","Niger","Chad","Sudan"]

# ---- Crimea belongs to Ukraine (Natural Earth files it under Russia) ----
def take_crimea():
    ru = polys(ARCS, GEOMS['Russia'])
    keep, crimea = [], []
    for p in ru:
        (crimea if pip((34.2, 45.2), p[0]) else keep).append(p)
    return keep, crimea

RU_POLYS, CRIMEA = take_crimea()

# ---- coarse lon/lat window, then projection, then exact clip in map space ----
LON0, LON1, LAT0, LAT1 = -40.0, 70.0, 25.0, 75.0
# Кадр карти (те, що видно): від Ісландії до Уралу, від Криту до Нордкапу.
FRAME = dict(lon0=-25.5, lon1=50.0, lat0=34.2, lat1=71.6)

def clip_poly(pts, inside, isect):
    out = pts
    for edge in range(4):
        src, out = out, []
        if not src: break
        prev = src[-1]
        for cur in src:
            ci, pi = inside(cur, edge), inside(prev, edge)
            if ci:
                if not pi: out.append(isect(prev, cur, edge))
                out.append(cur)
            elif pi:
                out.append(isect(prev, cur, edge))
            prev = cur
    return out

def rect_clipper(x0, x1, y0, y1):
    def inside(p, e):
        return (p[0] >= x0, p[0] <= x1, p[1] >= y0, p[1] <= y1)[e]
    def isect(a, b, e):
        if e < 2:
            xv = x0 if e == 0 else x1
            t = (xv - a[0]) / (b[0] - a[0])
            return (xv, a[1] + t * (b[1] - a[1]))
        yv = y0 if e == 2 else y1
        t = (yv - a[1]) / (b[1] - a[1])
        return (a[0] + t * (b[0] - a[0]), yv)
    return lambda pts: clip_poly(pts, inside, isect)

geo_clip = rect_clipper(LON0, LON1, LAT0, LAT1)

# Lambert azimuthal equal-area centred on Europe (the ETRS89-LAEA look)
R = 1000.0
LAM0, PHI0 = math.radians(12.0), math.radians(52.0)

def project(lon, lat):
    lam, phi = math.radians(lon), math.radians(lat)
    c = 1 + math.sin(PHI0) * math.sin(phi) + math.cos(PHI0) * math.cos(phi) * math.cos(lam - LAM0)
    if c <= 1e-9: return None
    k = R * math.sqrt(2.0 / c)
    x = k * math.cos(phi) * math.sin(lam - LAM0)
    y = -k * (math.cos(PHI0) * math.sin(phi) - math.sin(PHI0) * math.cos(phi) * math.cos(lam - LAM0))
    return (x, y)

def unwrap(ring):
    """Розгортає довготу через 180-й меридіан: 179 -> 181, а не -179.

    Кільце материкової Росії замикається на Чукотці, тож без цього
    прямокутне обрізання дає фальшиву смугу через усю карту."""
    out = [ring[0]]
    for lon, lat in ring[1:]:
        prev = out[-1][0]
        while lon - prev > 180: lon -= 360
        while lon - prev < -180: lon += 360
        out.append((lon, lat))
    # Починаємо з найсхіднішої точки: ребро замикання опиняється за вікном
    # обрізання одним шматком і не породжує зайвих країв.
    k = max(range(len(out)), key=lambda i: out[i][0])
    return out[k:] + out[:k]

# Заатлантичні володіння — не на карті Європи.
FAR_ISLANDS = [
    (-32.0, -24.4, 36.0, 40.0),   # Азорські о-ви
    (-18.5, -15.0, 30.0, 33.5),   # Мадейра
    (-19.0, -12.5, 27.0, 30.0),   # Канарські о-ви
]

def far_island(ring):
    lons = [p[0] for p in ring]; lats = [p[1] for p in ring]
    for x0, x1, y0, y1 in FAR_ISLANDS:
        if x0 <= min(lons) and max(lons) <= x1 and y0 <= min(lats) and max(lats) <= y1:
            return True
    return False

def prep(polygons):
    """lon/lat polygons -> projected rings (outer + holes)."""
    res = []
    for rings in polygons:
        if far_island(rings[0]):
            continue
        rings = [unwrap(r) for r in rings]
        pr = []
        for r in rings:
            c = geo_clip(r)
            if len(c) < 3: continue
            p = [project(*pt) for pt in c]
            if any(v is None for v in p): continue
            pr.append(p)
        if pr: res.append(pr)
    return res

def source_polys(names):
    out = []
    for n in names:
        if n == 'Russia':
            out += RU_POLYS
        else:
            out += polys(ARCS, GEOMS[n])
        if n == 'Ukraine':
            out += CRIMEA
    return out

PROJ = {}
for code, uk, region, names in QUIZ:
    PROJ[code] = prep(source_polys(names))
BACK = []
for n in BACKDROP:
    BACK += prep(polys(ARCS, GEOMS[n]))

# ---- view box: bbox of the projected map frame ----
xs, ys = [], []
def sample_frame():
    st = 0.25
    lo0, lo1, la0, la1 = FRAME['lon0'], FRAME['lon1'], FRAME['lat0'], FRAME['lat1']
    n = int((lo1-lo0)/st)+1
    m = int((la1-la0)/st)+1
    for i in range(n):
        lo = lo0 + i*st
        for la in (la0, la1): yield (lo, la)
    for j in range(m):
        la = la0 + j*st
        for lo in (lo0, lo1): yield (lo, la)
for lo, la in sample_frame():
    p = project(lo, la)
    if p: xs.append(p[0]); ys.append(p[1])
MINX, MAXX, MINY, MAXY = min(xs), max(xs), min(ys), max(ys)
W, H = MAXX-MINX, MAXY-MINY
view_clip = rect_clipper(MINX, MAXX, MINY, MAXY)

def area(r):
    a = 0.0
    for i in range(len(r)):
        x1,y1 = r[i]; x2,y2 = r[(i+1) % len(r)]
        a += x1*y2 - x2*y1
    return abs(a)/2

def centroid(r):
    a = cx = cy = 0.0
    for i in range(len(r)):
        x1,y1 = r[i]; x2,y2 = r[(i+1) % len(r)]
        f = x1*y2 - x2*y1
        a += f; cx += (x1+x2)*f; cy += (y1+y2)*f
    if abs(a) < 1e-9:
        return (sum(p[0] for p in r)/len(r), sum(p[1] for p in r)/len(r))
    a *= 0.5
    return (cx/(6*a), cy/(6*a))

def fmt(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith('.0') else s

MIN_AREA = 1.2   # drop specks, but never the whole country

def simplify(pts, tol):
    """Douglas-Peucker on a closed ring; keeps enough shape for a 1000px-wide map."""
    if len(pts) < 8: return pts
    keep = [False]*len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts)-1)]
    t2 = tol*tol
    while stack:
        i, j = stack.pop()
        if j <= i+1: continue
        ax, ay = pts[i]; bx, by = pts[j]
        dx, dy = bx-ax, by-ay
        den = dx*dx + dy*dy
        best, bi = -1.0, -1
        for k in range(i+1, j):
            px, py = pts[k]
            if den == 0:
                d2 = (px-ax)**2 + (py-ay)**2
            else:
                t = ((px-ax)*dx + (py-ay)*dy) / den
                t = 0.0 if t < 0 else (1.0 if t > 1 else t)
                d2 = (px-ax-t*dx)**2 + (py-ay-t*dy)**2
            if d2 > best: best, bi = d2, k
        if best > t2:
            keep[bi] = True
            stack.append((i, bi)); stack.append((bi, j))
    out = [p for p, k in zip(pts, keep) if k]
    return out if len(out) >= 3 else pts

def thin(ring):
    a = area(ring)
    tol = 0.35 if a > 400 else (0.18 if a > 40 else 0.0)
    return simplify(ring, tol) if tol else ring

def to_path(polygons, keep_all=False):
    d, kept = [], []
    for rings in polygons:
        outer = view_clip(rings[0])
        if len(outer) < 3: continue
        if not keep_all and area(outer) < MIN_AREA: continue
        kept.append(outer)
        parts = [outer] + [view_clip(h) for h in rings[1:]]
        for r in parts:
            r = thin(r)
            if len(r) < 3: continue
            d.append("M" + "L".join(f"{fmt(x-MINX)},{fmt(y-MINY)}" for x, y in r) + "Z")
    return "".join(d), kept

out_countries = []
for code, uk, region, names in QUIZ:
    d, kept = to_path(PROJ[code])
    if not kept:                              # microstate wiped out by MIN_AREA
        d, kept = to_path(PROJ[code], keep_all=True)
    big = max(kept, key=area)
    cx, cy = centroid(big)
    biggest = area(big)
    out_countries.append({
        "id": code, "name": uk, "region": region, "d": d,
        "c": [round(cx-MINX, 1), round(cy-MINY, 1)],
        "a": round(biggest),
        "tiny": 1 if biggest < 90 else 0,
    })

back_d = []
for rings in BACK:
    outer = view_clip(rings[0])
    if len(outer) < 3 or area(outer) < MIN_AREA: continue
    for r in [outer] + [view_clip(h) for h in rings[1:]]:
        r = thin(r)
        if len(r) < 3: continue
        back_d.append("M" + "L".join(f"{fmt(x-MINX)},{fmt(y-MINY)}" for x, y in r) + "Z")

data = {"width": round(W, 1), "height": round(H, 1),
        "backdrop": "".join(back_d), "countries": out_countries}

with open(DST, 'w', encoding='utf-8') as f:
    f.write('// Згенеровано з Natural Earth 50m (public domain) — див. tools/gen-map.py.\n')
    f.write('// Не редагувати вручну.\n')
    f.write('window.EUROPE_MAP = ')
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    f.write(';\n')

print('countries:', len(out_countries))
print('viewBox:  ', round(W, 1), 'x', round(H, 1))
print('written:  ', DST, os.path.getsize(DST), 'bytes')
