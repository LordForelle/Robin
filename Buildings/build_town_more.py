"""Stadt-Paket 2: Gemischtwarenladen, Kirche, Blockhuette, Wohnhaus, Planwagen und Kleinprops.

Ausfuehren:  blender -b -P build_town_more.py   (oder: python3 build_town_more.py mit pip-Paket bpy)
Gleiche Konventionen wie build_buildings.py: Front nach -Y, Ursprung = Bodenmitte.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import build_buildings as bb  # noqa: E402
from build_buildings import (  # noqa: E402
    Build, box, cyl, pyramid, tri_x, tri_y, xf, text,
    WOOD, WOOD_D, WOOD_DD, WOOD_L, TRIM, STONE, STONE_L, GLASS, IRON, METAL, GOLD, RED, WHITE, GREEN,
)

SIGNS = {
    "store": "GENERAL STORE",
    "open": "OPEN",
}

CANVAS = "E8DDC4"
BRONZE = "B08D3A"
BARK = "6B4428"
LOGCUT = "C9A06A"


def beam(p0, p1, w, h=None):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    m = d.to_track_quat("Z", "Y").to_matrix()
    v, f = box((0, 0, 0), (w, h or w, d.length))
    mid = (p0 + p1) / 2
    return [tuple(m @ Vector(q) + mid) for q in v], f


def arc_segments_y(b, cy, z0, r, length, t, col, n=10):
    """Halbrund-Plane entlang Y aus n Segmenten."""
    chord = 2 * r * math.sin(math.pi / (2 * n)) + 0.02
    for i in range(n):
        a = math.pi * (i + 0.5) / n
        geo = xf(box((0, 0, 0), (chord, length, t)), rot=(0, -(math.degrees(a) + 90), 0))
        b.add(xf(geo, loc=(r * math.cos(a), cy, z0 + r * math.sin(a))), col)


def spoked_wheel(b, x, y, r, w=0.08):
    b.add(xf(cyl((0, 0, -w / 2), r, r, w, 14), loc=(x, y, r), rot=(0, 90, 0)), WOOD_DD)
    b.add(xf(cyl((0, 0, -w / 2 - 0.01), r * 0.84, r * 0.84, w + 0.02, 14), loc=(x, y, r), rot=(0, 90, 0)), "3A2A1A")
    b.add(xf(cyl((0, 0, -w), r * 0.18, r * 0.18, w * 2, 8), loc=(x, y, r), rot=(0, 90, 0)), IRON)
    for k in range(6):
        a = math.pi * k / 6
        b.add(xf(box((0, 0, 0), (w * 0.6, 0.05, r * 1.7)), loc=(x, y, r), rot=(math.degrees(a), 0, 0)), WOOD_L)


def log_wall(b, x0, x1, y, z0, z1, r, along="x"):
    z = z0 + r
    while z < z1:
        if along == "x":
            b.add(xf(cyl((0, 0, -(x1 - x0) / 2 - 0.15), r, r, (x1 - x0) + 0.3, 7), loc=((x0 + x1) / 2, y, z),
                     rot=(0, 90, 0)), BARK)
            for xe in (x0 - 0.15, x1 + 0.15):
                b.add(xf(cyl((0, 0, -0.01), r * 0.85, r * 0.85, 0.02, 7), loc=(xe, y, z), rot=(0, 90, 0)), LOGCUT)
        else:
            b.add(xf(cyl((0, 0, -(x1 - x0) / 2 - 0.15), r, r, (x1 - x0) + 0.3, 7), loc=(y, (x0 + x1) / 2, z),
                     rot=(90, 0, 0)), BARK)
        z += r * 1.85


# ======================================================= GEMISCHTWAREN
def general_store():
    b = Build("Building_GeneralStore")
    W, D, H = 8.0, 8.0, 4.4
    F = D / 2
    WALLC = "6F8FA6"
    b.add(box((0, 0, 0.15), (W + 0.3, D + 0.3, 0.3)), STONE)
    b.add(box((0, 0, 0.3 + H / 2), (W, D, H)), WALLC)
    z = 0.6
    while z < 0.3 + H:
        b.add(box((0, -F - 0.015, z), (W, 0.03, 0.04)), "5C7A8F")
        for sx in (-1, 1):
            b.add(box((sx * (W / 2 + 0.015), 0, z), (0.03, D, 0.04)), "5C7A8F")
        z += 0.35
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, 0.3 + H / 2), (0.22, 0.22, H)), TRIM)
    ZT = 0.3 + H
    b.add(tri_x(0, 0.3, ZT, W, D - 0.6, 1.4), WALLC)
    b.gable_roof_x(0, 0.3, ZT, W, D - 0.6, 1.4, over=0.3, col="7A3A2E")
    # Scheinfassade mit Rundbogen-Stufen
    b.add(box((0, -F - 0.1, ZT + 1.1), (W + 0.4, 0.2, 2.2)), WALLC)
    b.add(box((0, -F - 0.1, ZT + 2.45), (4.5, 0.2, 0.5)), WALLC)
    b.add(box((0, -F - 0.12, ZT + 2.2), (W + 0.6, 0.3, 0.1)), TRIM)
    b.add(box((0, -F - 0.12, ZT + 2.75), (4.7, 0.3, 0.1)), TRIM)
    b.add(box((0, -F - 0.22, ZT + 1.1), (7.0, 0.06, 1.3)), TRIM)
    b.add(box((0, -F - 0.26, ZT + 1.1), (6.7, 0.05, 1.1)), "2F4A3A")
    b.add(text(SIGNS["store"], 0.62, (0, -F - 0.3, ZT + 1.1), 0.05), GOLD)
    # Veranda
    b.add(box((0, -F - 1.2, 0.25), (W + 0.4, 2.4, 0.2)), WOOD_D)
    for x in (-3.9, -1.3, 1.3, 3.9):
        b.add(box((x, -F - 2.3, 1.95), (0.18, 0.18, 3.2)), TRIM)
    b.add(xf(box((0, -F - 1.25, 3.7), (W + 0.6, 2.7, 0.12)), rot=(-8, 0, 0), pivot=(0, -F, 3.8)), "8E969B")
    b.add(box((0, -F - 2.55, 0.1), (2.4, 0.35, 0.2)), WOOD_D)
    # Tuer + Schaufenster
    b.door(0, 0.35, 1.3, 2.5, F, col=WOOD_DD, frame=TRIM)
    b.add(box((0, -F - 0.1, 2.0), (0.8, 0.04, 0.8)), GLASS)
    for sx in (-1, 1):
        b.window(sx * 2.6, 1.8, 2.2, 2.0, F, frame=TRIM, cross=False)
        for k in range(3):
            b.add(box((sx * 2.6 - 0.8 + k * 0.8, -F - 0.25, 0.95 + 0.02), (0.5, 0.25, 0.1)), WOOD_L)
        # Waren im Fenster
        for k in range(4):
            b.add(cyl((sx * 2.6 - 0.75 + k * 0.5, -F - 0.25, 1.0), 0.09, 0.09, 0.25, 6),
                  ("B83A32", "3C7A3E", "D9822B", "2F5E8C")[k])
    b.add(box((1.0, -F - 0.12, 2.3), (0.6, 0.04, 0.3)), "B83A32")
    b.add(text(SIGNS["open"], 0.14, (1.0, -F - 0.15, 2.3), 0.02), WHITE)
    for sx in (-1, 1):
        for u in (-2.0, 1.5):
            b.window(u, 2.0, 1.1, 1.3, W / 2, side=90 * sx, frame=TRIM)
    # Waren auf der Veranda
    b.barrel(-3.4, -F - 0.5, 0.35)
    b.barrel(-2.8, -F - 0.6, 0.35, 0.25, 0.7)
    b.crate(3.3, -F - 0.6, 0.35, 0.6, 5)
    b.crate(3.3, -F - 0.6, 0.95, 0.45, -8)
    b.add(box((2.1, -F - 0.9, 0.6), (0.9, 0.5, 0.3), (1.1, 1.1)), WOOD_L)  # Apfelkiste
    for k in range(8):
        b.add(box((1.78 + (k % 4) * 0.2, -F - 1.0 + (k // 4) * 0.2, 0.8), (0.12, 0.12, 0.1)), ("B83A32", "C8302C")[k % 2])
    b.add(xf(box((0, 0, 0), (0.04, 0.04, 1.3)), loc=(-1.1, -F - 0.15, 1.0), rot=(8, 0, 0)), WOOD_L)  # Besen
    b.add(xf(box((0, 0, -0.65), (0.25, 0.08, 0.3), (1.3, 1.0)), loc=(-1.1, -F - 0.15, 1.0), rot=(8, 0, 0)), "C9A24A")
    for i in range(3):
        b.add(box((-2.2 + i * 0.4, -F - 0.4, 0.5), (0.35, 0.3, 0.3), (0.85, 0.85)), "CDB88A")
    b.lantern(-0.95, -F - 0.25, 2.7)
    b.lantern(0.95, -F - 0.25, 2.7)
    return b.finish()


# ================================================================ KIRCHE
def church():
    b = Build("Building_Church")
    W, D, H = 7.0, 12.0, 5.0
    F = D / 2
    WALLC = "F2EEE4"
    ROOF = "5B4A3E"
    b.add(box((0, 0, 0.2), (W + 0.3, D + 0.3, 0.4)), STONE)
    b.add(box((0, 0, 0.4 + H / 2), (W, D, H)), WALLC)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, 0.4 + H / 2), (0.25, 0.25, H)), "D8D0C0")
    ZT = 0.4 + H
    b.add(tri_y(0, 0, ZT, W, D, 3.2), WALLC)
    b.gable_roof_y(0, 0, ZT, W, D, 3.2, over=0.35, col=ROOF)
    # Spitzbogenfenster seitlich
    for sx in (-1, 1):
        for u in (-3.5, -1.2, 1.2, 3.5):
            g = [(box((u, -W / 2 - 0.03, 2.6), (1.0, 0.06, 2.2)), "D8D0C0"),
                 (box((u, -W / 2 - 0.06, 2.6), (0.8, 0.04, 2.0)), "5A7FA8"),
                 (tri_y(u, -W / 2 - 0.045, 3.7, 1.0, 0.09, 0.6), "D8D0C0"),
                 (tri_y(u, -W / 2 - 0.07, 3.6, 0.8, 0.05, 0.5), "5A7FA8"),
                 (box((u, -W / 2 - 0.09, 2.7), (0.05, 0.03, 2.2)), "D8D0C0"),
                 (box((u, -W / 2 - 0.12, 1.45), (1.1, 0.2, 0.08)), "D8D0C0")]
            for geo, c in g:
                b.add(xf(geo, rot=(0, 0, 90 * sx)), c)
    # Glockenturm vorne
    TY = -F - 1.1
    b.add(box((0, TY, 0.4 + 3.5), (2.6, 2.4, 7.0)), WALLC)
    b.add(box((0, TY, 7.5), (2.9, 2.7, 0.2)), "D8D0C0")
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * 1.2, TY + sy * 1.1, 8.6), (0.25, 0.25, 2.0)), WALLC)
    b.add(box((0, TY, 9.7), (2.9, 2.7, 0.2)), "D8D0C0")
    b.add(cyl((0, TY, 7.6), 0.05, 0.05, 1.5, 6), IRON)
    b.add(cyl((0, TY, 8.2), 0.55, 0.3, 0.8, 10), BRONZE)
    b.add(cyl((0, TY, 8.1), 0.6, 0.55, 0.12, 10), BRONZE)
    b.add(pyramid((0, TY, 9.8), 2.0, 4.2), ROOF)
    b.add(box((0, TY, 14.5), (0.1, 0.1, 1.2)), GOLD)
    b.add(box((0, TY, 14.7), (0.6, 0.1, 0.1)), GOLD)
    # Eingang, Rundfenster, Stufen
    b.door(0, 0.4, 1.4, 2.6, -TY + 1.2, col="5A3A22", frame="D8D0C0", double=True)
    b.add(tri_y(0, TY - 1.24, 3.1, 1.6, 0.06, 0.6), "D8D0C0")
    b.add(xf(cyl((0, 0, 0), 0.6, 0.6, 0.08, 12), loc=(0, TY - 1.2, 5.3), rot=(90, 0, 0)), "D8D0C0")
    b.add(xf(cyl((0, 0, 0), 0.48, 0.48, 0.08, 12), loc=(0, TY - 1.25, 5.3), rot=(90, 0, 0)), "5A7FA8")
    for k in range(4):
        b.add(xf(box((0, 0, 0), (0.05, 0.04, 0.96)), loc=(0, TY - 1.33, 5.3), rot=(0, 45 * k, 0)), "D8D0C0")
    for i in range(3):
        b.add(box((0, TY - 1.5 - i * 0.3, 0.35 - i * 0.12), (2.4 + i * 0.3, 0.6 + i * 0.3, 0.12)), STONE_L)
    for sx in (-1, 1):
        b.bush(sx * 2.2, TY - 1.0, 0.45)
        b.lamp_post(sx * 2.4, TY - 2.4, 2.8)
    return b.finish()


# ============================================================= BLOCKHUETTE
def log_cabin():
    b = Build("Building_LogCabin")
    W, D, H = 6.0, 5.0, 2.8
    r = 0.14
    b.add(box((0, 0, 0.15), (W + 0.4, D + 0.4, 0.3)), STONE)
    b.add(box((0, 0, 0.3 + H / 2), (W - 0.2, D - 0.2, H)), "7A5230")
    for sy in (-1, 1):
        log_wall(b, -W / 2, W / 2, sy * D / 2, 0.3, 0.3 + H, r, "x")
    for sx in (-1, 1):
        log_wall(b, -D / 2, D / 2, sx * W / 2, 0.3 + r * 0.9, 0.3 + H, r, "y")
    ZT = 0.3 + H
    b.add(tri_x(0, 0, ZT, W, D, 1.6), "7A5230")
    for sx in (-1, 1):
        z = ZT + 0.15
        while z < ZT + 1.5:
            half = D / 2 * (1 - (z - ZT) / 1.6)
            b.add(xf(cyl((0, 0, -half), r, r, 2 * half, 7), loc=(sx * W / 2, 0, z), rot=(90, 0, 0)), BARK)
            z += r * 1.85
    b.gable_roof_x(0, 0, ZT, W, D, 1.6, over=0.5, col="5E4A3A")
    # Kamin
    b.add(box((W / 2 + 0.35, 0.8, 2.6), (0.7, 1.0, 5.2)), STONE_L)
    for k in range(8):
        b.add(box((W / 2 + 0.71, 0.8, 0.3 + k * 0.6), (0.02, 1.0, 0.04)), STONE)
    b.add(box((W / 2 + 0.35, 0.8, 5.25), (0.8, 1.1, 0.1)), STONE)
    # Tuer, Fenster, Veranda
    F = D / 2 + r
    b.door(-1.0, 0.3, 1.0, 2.1, F, col=WOOD_D, frame=WOOD_DD)
    b.window(1.4, 1.7, 1.1, 1.0, F, frame=WOOD_DD, shutters="3E5F4A")
    b.window(-0.8, 1.7, 1.0, 1.0, W / 2 + r, side=-90, frame=WOOD_DD)
    b.add(box((0, -D / 2 - 1.0, 0.25), (W, 1.8, 0.15)), WOOD_D)
    for x in (-W / 2 + 0.1, 0.0, W / 2 - 0.1):
        b.add(cyl((x, -D / 2 - 1.8, 0.3), 0.1, 0.1, 2.4, 7), BARK)
    b.add(xf(box((0, -D / 2 - 0.95, 2.75), (W + 0.4, 2.1, 0.1)), rot=(-12, 0, 0), pivot=(0, -D / 2, 2.9)), "5E4A3A")
    # Schaukelstuhl
    RX, RY = 1.8, -D / 2 - 0.9
    for sx in (-1, 1):
        b.add(xf(box((0, 0, 0), (0.04, 0.7, 0.06)), loc=(RX + sx * 0.22, RY, 0.38), rot=(0, 0, 0)), WOOD_DD)
        b.add(box((RX + sx * 0.22, RY, 0.58), (0.04, 0.04, 0.35)), WOOD_DD)
    b.add(box((RX, RY, 0.75), (0.5, 0.5, 0.05)), WOOD_D)
    b.add(xf(box((0, 0, 0.35), (0.5, 0.05, 0.7)), loc=(RX, RY + 0.25, 0.75), rot=(-12, 0, 0)), WOOD_D)
    b.barrel(-2.6, -D / 2 - 0.5, 0.33, 0.25, 0.7)
    b.lantern(-1.8, -F - 0.2, 2.4)
    for k in range(3):  # Brennholz an der Seite
        b.add(xf(cyl((0, 0, -0.8), 0.1, 0.1, 1.6, 7), loc=(-W / 2 - 0.35, 0.3, 0.12 + k * 0.19), rot=(90, 0, 0)), BARK)
    return b.finish()


# ============================================================== WOHNHAUS
def house():
    b = Build("Building_House")
    W, D, H = 7.0, 6.0, 3.2
    F = D / 2
    WALLC = "D9C27A"
    b.add(box((0, 0, 0.2), (W + 0.3, D + 0.3, 0.4)), STONE)
    b.add(box((0, 0, 0.4 + H / 2), (W, D, H)), WALLC)
    z = 0.7
    while z < 0.4 + H:
        b.add(box((0, -F - 0.015, z), (W, 0.03, 0.04)), "C2AB66")
        z += 0.3
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, 0.4 + H / 2), (0.2, 0.2, H)), WHITE)
    ZT = 0.4 + H
    b.add(tri_x(0, 0, ZT, W, D, 2.2), WALLC)
    b.gable_roof_x(0, 0, ZT, W, D, 2.2, over=0.4, col="3E5F4A")
    # Gaube
    b.add(box((0, -1.6, ZT + 0.9), (1.6, 1.6, 1.3)), WALLC)
    b.add(tri_y(0, -1.6, ZT + 1.55, 1.6, 1.6, 0.7), WALLC)
    b.gable_roof_y(0, -1.6, ZT + 1.55, 1.6, 1.6, 0.7, over=0.15, t=0.1, col="3E5F4A")
    b.window(0, ZT + 0.95, 0.8, 0.8, 2.4, frame=WHITE)
    b.add(box((-2.2, 0.8, ZT + 1.6), (0.5, 0.5, 1.6)), "8E4634")
    # Tuer, Fenster, Veranda
    b.door(0, 0.4, 1.0, 2.2, F, col="8C2F23", frame=WHITE)
    for sx in (-1, 1):
        b.window(sx * 2.1, 2.0, 1.1, 1.3, F, frame=WHITE, shutters="3E5F4A")
        b.add(box((sx * 2.1, -F - 0.2, 1.2), (1.2, 0.25, 0.2)), WOOD_D)
        for k in range(6):
            b.add(box((sx * 2.1 - 0.5 + k * 0.2, -F - 0.2, 1.35), (0.12, 0.15, 0.12)), ("D9425B", "F2C12E", "E86FA0")[k % 3])
        for u in (-1.3, 1.3):
            b.window(u, 2.0, 1.0, 1.2, W / 2, side=90 * sx, frame=WHITE)
    b.add(box((0, -F - 0.9, 0.35), (3.0, 1.8, 0.12)), WOOD_D)
    for sx in (-1, 1):
        b.add(box((sx * 1.4, -F - 1.7, 1.6), (0.12, 0.12, 2.5)), WHITE)
    b.add(tri_y(0, -F - 0.9, 2.85, 3.2, 1.9, 0.8), WALLC)
    b.gable_roof_y(0, -F - 0.9, 2.85, 3.2, 1.9, 0.8, over=0.15, t=0.1, col="3E5F4A")
    b.add(box((0, -F - 1.95, 0.2), (1.2, 0.4, 0.15)), STONE_L)
    # Lattenzaun vorne
    for sx in (-1, 1):
        for k in range(12):
            x = sx * (1.2 + k * 0.2)
            b.add(box((x, -F - 2.6, 0.45), (0.1, 0.03, 0.9)), WHITE)
            b.add(pyramid((x, -F - 2.6, 0.9), 0.06, 0.08, 4, 0), WHITE)
        b.add(box((sx * 2.3, -F - 2.62, 0.6), (2.3, 0.03, 0.08)), WHITE)
        b.add(box((sx * 2.3, -F - 2.62, 0.3), (2.3, 0.03, 0.08)), WHITE)
    b.add(cyl((2.9, -F - 1.2, 0), 0.25, 0.3, 0.4, 8), "B5654B")
    b.bush(2.9, -F - 1.2, 0.3, z=0.35)
    b.add(box((-3.0, -F - 2.2, 0.55), (0.1, 0.1, 1.1)), WOOD_DD)  # Briefkasten
    b.add(box((-3.0, -F - 2.2, 1.2), (0.26, 0.45, 0.22)), "2F5E8C")
    return b.finish()


# ============================================================= PLANWAGEN
def covered_wagon():
    b = Build("Prop_CoveredWagon")
    b.add(box((0, 0, 1.0), (1.5, 3.6, 0.12)), WOOD_D)
    for sx in (-1, 1):
        b.add(box((sx * 0.72, 0, 1.3), (0.06, 3.6, 0.5)), WOOD)
        b.add(box((sx * 0.745, 0, 1.52), (0.02, 3.6, 0.05)), WOOD_DD)
    for sy in (-1, 1):
        b.add(box((0, sy * 1.77, 1.3), (1.5, 0.06, 0.5)), WOOD)
    arc_segments_y(b, 0, 1.55, 0.95, 3.2, 0.04, CANVAS)
    for y in (-1.5, -0.5, 0.5, 1.5):
        arc_segments_y(b, y, 1.55, 0.98, 0.06, 0.04, "CDBF9F")
    b.add(xf(box((0, 0, 0), (1.3, 0.02, 1.2)), loc=(0, 1.62, 1.95)), "3A2A1A")
    for y in (-1.2, 1.3):
        b.add(box((0, y, 0.72), (1.7, 0.12, 0.12)), WOOD_DD)
    spoked_wheel(b, 0.85, -1.2, 0.55)
    spoked_wheel(b, -0.85, -1.2, 0.55)
    spoked_wheel(b, 0.85, 1.3, 0.72)
    spoked_wheel(b, -0.85, 1.3, 0.72)
    b.add(beam((0, -1.8, 0.72), (0, -4.2, 0.55), 0.1), WOOD_D)  # Deichsel
    b.add(box((0, -3.4, 0.62), (1.2, 0.08, 0.08)), WOOD_D)
    b.add(box((0, -1.9, 1.35), (1.3, 0.3, 0.1)), WOOD_D)  # Kutschbock
    b.barrel(0.95, 0.2, 0.9, 0.18, 0.45)
    b.add(xf(box((0, 0, 0), (0.04, 0.04, 1.2)), loc=(-0.95, 0.6, 1.4), rot=(0, 10, 0)), WOOD_L)
    b.add(xf(box((0, 0, -0.6), (0.2, 0.03, 0.26)), loc=(-0.95, 0.6, 1.4), rot=(0, 10, 0)), METAL)
    return b.finish()


# ============================================================ KLEINPROPS
def prop_barrel():
    b = Build("Prop_Barrel")
    b.barrel(0, 0, 0, 0.32, 0.9)
    b.add(cyl((0, 0, 0.88), 0.28, 0.28, 0.02, 8), WOOD_L)
    return b.finish()


def prop_crate():
    b = Build("Prop_Crate")
    b.crate(0, 0, 0, 0.8)
    return b.finish()


def prop_crate_stack():
    b = Build("Prop_CrateStack")
    b.crate(-0.45, 0, 0, 0.8, 4)
    b.crate(0.45, 0.05, 0, 0.8, -6)
    b.crate(0.0, 0.0, 0.8, 0.7, 12)
    b.barrel(1.2, 0.5, 0, 0.3, 0.85)
    return b.finish()


def prop_hitching_post():
    b = Build("Prop_HitchingPost")
    for x in (-1.1, 1.1):
        b.add(box((x, 0, 0.55), (0.16, 0.16, 1.1)), WOOD_DD)
    b.add(box((0, 0, 1.05), (2.6, 0.12, 0.12)), WOOD_D)
    b.add(box((0, 0.5, 0.25), (1.6, 0.6, 0.5)), WOOD_D)  # Trog
    b.add(box((0, 0.5, 0.5), (1.45, 0.45, 0.06)), "3F7FA6")
    return b.finish()


def prop_flagpole():
    b = Build("Prop_FlagPole")
    b.add(box((0, 0, 0.2), (0.8, 0.8, 0.4)), STONE_L)
    b.add(cyl((0, 0, 0.4), 0.07, 0.05, 7.6, 8), METAL)
    b.add(cyl((0, 0, 8.0), 0.1, 0.1, 0.12, 8), GOLD)
    b.add(box((0.8, 0, 7.4), (1.6, 0.03, 0.9)), "2F5E8C")
    b.add(box((0.8, -0.005, 7.4), (1.6, 0.03, 0.25)), GOLD)
    return b.finish()


def main():
    buildings = [general_store(), church(), log_cabin(), house()]
    props = [covered_wagon(), prop_barrel(), prop_crate(), prop_crate_stack(), prop_hitching_post(), prop_flagpole()]
    for ob in buildings + props:
        bb.export_mesh(ob)
    cam, target = bb.setup_preview()
    for ob, x in zip(buildings, (-18, -6, 5, 15)):
        ob.location.x = x
    for ob, (x, y) in zip(props, ((-12, -16), (-8.5, -15), (-7.5, -15), (-5.5, -15), (-2.5, -15), (1, -15))):
        ob.location = (x, y, 0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(bb.OUT, "town_more.blend"))
    shots = [("more_all", (0, -48, 18), (-2, -4, 3), 28),
             ("more_GeneralStore", (-10, -20, 7), (-18, -3, 3.2), 32),
             ("more_Church", (2, -26, 8), (-6, -3, 5), 30),
             ("more_Cabin_House", (16, -22, 7), (10, -3, 2.2), 30),
             ("more_Props", (-3, -24, 4), (-6, -15, 1.0), 32)]
    bb.render_shots(shots, cam, target)
    print("DONE")


if __name__ == "__main__":
    main()
