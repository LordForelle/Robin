"""Begehbarer Saloon mit Inneneinrichtung.

Ausfuehren:  blender -b -P build_saloon_interior.py   (oder: python3 build_saloon_interior.py mit pip-Paket bpy)

Export: Building_SaloonInterior.fbx mit Hierarchie
  Building_SaloonInterior          Erdgeschoss: Waende, Boden, Bar, Tische, Treppe, Veranda
    SaloonInterior_Upper           Obergeschoss: Decke/Boden OG, Waende OG, Balkon, Fassade
    SaloonInterior_Roof            Dach
Upper + Roof in Unity ausblenden = Schnittansicht von oben.
Aussenmasse wie Building_Saloon (8 x 7 m), Front nach -Y (Unity +Z).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import build_buildings as bb  # noqa: E402
from build_buildings import (  # noqa: E402
    Build, box, cyl, pyramid, xf, text,
    WOOD, WOOD_D, WOOD_DD, WOOD_L, TRIM, STONE, GLASS, DOOR_DARK, IRON, METAL, GOLD, WHITE,
)

SIGNS = {"saloon": "SALOON", "hiring": "HIRING", "board": "WORKERS WANTED"}

W, D = 8.0, 7.0
T = 0.2  # Wandstaerke
FZ = 0.35  # Oberkante Fussboden EG
Z1 = 3.45  # Unterkante Decke EG
Z2 = 3.6  # Oberkante Boden OG
ZT = 6.3  # Oberkante Waende
WALLPAPER = "7A2E2A"
PANEL = "5A3A22"
FELT = "2F6B3A"
BRASS = "C9A13B"
HOLE = (2.75, 3.8, -1.0, 2.6)  # Treppenloch x0, x1, y0, y1

SIDES = {"front": (0, D / 2), "back": (180, D / 2), "right": (90, W / 2), "left": (-90, W / 2)}


# ------------------------------------------------------------------ Waende
def wall(b, side, z0, z1, openings, siding=True):
    """Wand mit Oeffnungen. openings: (u0, u1, zo0, zo1) im lokalen Wandsystem."""
    rot, off = SIDES[side]
    half = (W if side in ("front", "back") else D) / 2
    u_pts = {-half, half}
    for u0, u1, _, _ in openings:
        u_pts |= {max(-half, u0), min(half, u1)}
    u_pts = sorted(u_pts)
    parts = []
    for a, c in zip(u_pts, u_pts[1:]):
        cover = sorted((zo0, zo1) for u0, u1, zo0, zo1 in openings if u0 <= a + 1e-6 and u1 >= c - 1e-6)
        z = z0
        for zo0, zo1 in cover:
            if zo0 > z:
                parts.append((a, c, z, zo0))
            z = max(z, zo1)
        if z < z1:
            parts.append((a, c, z, z1))
    for a, c, za, zb in parts:
        um, uw, zm, zh = (a + c) / 2, c - a, (za + zb) / 2, zb - za
        g = [(box((um, -off + T / 2 + 0.01, zm), (uw, T - 0.02, zh)), WOOD), ]
        # Innenseite: Tapete oben, Holzpaneel unten (nur EG)
        if z0 < 1.0:
            lo, hi = za, min(zb, FZ + 1.1)
            if hi > lo:
                g.append((box((um, -off + T + 0.005, (lo + hi) / 2), (uw, 0.01, hi - lo)), PANEL))
            lo = max(za, FZ + 1.1)
            if zb > lo:
                g.append((box((um, -off + T + 0.005, (lo + zb) / 2), (uw, 0.01, zb - lo)), WALLPAPER))
        else:
            g.append((box((um, -off + T + 0.005, zm), (uw, 0.01, zh)), "8A6A4A"))
        if siding:
            z = 0.6
            while z < ZT:
                if za < z < zb:
                    g.append((box((um, -off - 0.015, z), (uw, 0.03, 0.05)), WOOD_D))
                z += 0.4
        for geo, col in g:
            b.add(xf(geo, rot=(0, 0, rot)), col)


def win_open(u, zc, w, h):
    return (u - w / 2, u + w / 2, zc - h / 2, zc + h / 2)


def inner_sill(b, side, u, zc, w, h):
    rot, off = SIDES[side]
    b.add(xf(box((u, -off + T + 0.08, zc - h / 2 - 0.04), (w + 0.2, 0.16, 0.06)), rot=(0, 0, rot)), WOOD_DD)
    b.add(xf(box((u, -off + T / 2, zc), (w, 0.04, h)), rot=(0, 0, rot)), GLASS)
    b.add(xf(box((u, -off + T / 2 + 0.03, zc), (0.05, 0.03, h)), rot=(0, 0, rot)), WOOD_DD)
    b.add(xf(box((u, -off + T / 2 + 0.03, zc), (w, 0.03, 0.05)), rot=(0, 0, rot)), WOOD_DD)


# ------------------------------------------------------------------ Moebel
def chair(b, x, y, face):
    g = [(box((0, 0, FZ + 0.45), (0.42, 0.42, 0.05)), WOOD_D)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.append((box((sx * 0.17, sy * 0.17, FZ + 0.22), (0.04, 0.04, 0.45)), WOOD_DD))
        g.append((box((sx * 0.17, 0.19, FZ + 0.72), (0.04, 0.04, 0.55)), WOOD_DD))
    for zz in (FZ + 0.75, FZ + 0.95):
        g.append((box((0, 0.19, zz), (0.38, 0.03, 0.07)), WOOD_D))
    for geo, c in g:
        b.add(xf(geo, loc=(x, y, 0), rot=(0, 0, face)), c)


def round_table(b, x, y, r=0.5, top=WOOD_L):
    b.add(cyl((x, y, FZ), 0.3, 0.3, 0.04, 8), WOOD_DD)
    b.add(cyl((x, y, FZ + 0.04), 0.06, 0.06, 0.7, 6), WOOD_DD)
    b.add(cyl((x, y, FZ + 0.74), r, r, 0.05, 12), top)
    for k, a in enumerate((0, 90, 180, 270)):
        chair(b, x + (r + 0.35) * math.sin(math.radians(a)), y - (r + 0.35) * math.cos(math.radians(a)), a + 180)


def bottle(b, x, y, z, col):
    b.add(cyl((x, y, z), 0.035, 0.035, 0.2, 6), col)
    b.add(cyl((x, y, z + 0.2), 0.035, 0.014, 0.04, 6), col)
    b.add(cyl((x, y, z + 0.24), 0.014, 0.014, 0.06, 6), col)


def glass_cup(b, x, y, z):
    b.add(cyl((x, y, z), 0.03, 0.035, 0.08, 6), "CFE3EA")
    b.add(cyl((x, y, z + 0.01), 0.028, 0.028, 0.04, 6), "C98A2E")


def stool(b, x, y):
    b.add(cyl((x, y, FZ), 0.18, 0.12, 0.05, 6), IRON)
    b.add(cyl((x, y, FZ + 0.05), 0.04, 0.04, 0.65, 6), IRON)
    b.add(cyl((x, y, FZ + 0.7), 0.19, 0.19, 0.07, 8), "7A2E2A")


def picture(b, side, u, zc, w, h, col):
    rot, off = SIDES[side]
    for geo, c in ((box((u, -off + T + 0.03, zc), (w, 0.04, h)), BRASS),
                   (box((u, -off + T + 0.05, zc), (w - 0.1, 0.02, h - 0.1)), col)):
        b.add(xf(geo, rot=(0, 0, rot)), c)


def sconce(b, side, u, zc):
    rot, off = SIDES[side]
    g = [(box((u, -off + T + 0.1, zc - 0.05), (0.04, 0.2, 0.04)), BRASS),
         (box((u, -off + T + 0.22, zc + 0.05), (0.12, 0.12, 0.18)), bb.LAMP),
         (pyramid((u, -off + T + 0.22, zc + 0.14), 0.1, 0.1), BRASS)]
    for geo, c in g:
        b.add(xf(geo, rot=(0, 0, rot)), c)


# ================================================================ ERDGESCHOSS
def ground_floor():
    b = Build("Building_SaloonInterior")
    F = D / 2
    b.add(box((0, 0, 0.15), (W + 0.3, D + 0.3, 0.3)), STONE)
    b.add(box((0, 0, 0.325), (W - 2 * T, D - 2 * T, 0.05)), WOOD_D)
    for k in range(20):
        b.add(box((-W / 2 + T + (k + 0.5) * (W - 2 * T) / 20, 0, FZ + 0.001), (0.02, D - 2 * T, 0.002)), WOOD_DD)
    # Waende EG
    front_open = [(-0.85, 0.85, FZ, FZ + 2.5), win_open(-2.65, 1.75, 1.5, 1.6), win_open(2.65, 1.75, 1.5, 1.6)]
    side_open = [win_open(-1.8, 1.9, 1.0, 1.3), win_open(1.4, 1.9, 1.0, 1.3)]
    wall(b, "front", 0.3, Z2, front_open)
    wall(b, "back", 0.3, Z2, [(-2.35, -1.45, FZ, FZ + 2.2)])
    wall(b, "right", 0.3, Z2, side_open)
    wall(b, "left", 0.3, Z2, side_open)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, (0.3 + Z2) / 2), (0.22, 0.22, Z2 - 0.3)), WOOD_DD)
    # Fenster + Tuerrahmen (aussen), Fensterbaenke innen
    for sx in (-1, 1):
        b.window(sx * 2.65, 1.75, 1.5, 1.6, F, shutters="3E5F4A")
        inner_sill(b, "front", sx * 2.65, 1.75, 1.5, 1.6)
        for u in (-1.8, 1.4):
            b.window(u, 1.9, 1.0, 1.3, W / 2, side=90 * sx)
            inner_sill(b, "right" if sx > 0 else "left", u, 1.9, 1.0, 1.3)
    b.add(box((0, -F - 0.04, 2.95), (2.0, 0.1, 0.2)), WOOD_DD)
    for sx in (-1, 1):
        b.add(box((sx * 0.93, -F - 0.04, 1.6), (0.16, 0.1, 2.6)), WOOD_DD)
        b.add(box((sx * 0.41, -F + 0.1, 1.55), (0.74, 0.05, 1.0)), WOOD_L)  # Schwingtueren
        for zz in (1.15, 1.55, 1.95):
            b.add(box((sx * 0.41, -F + 0.065, zz), (0.74, 0.03, 0.07)), WOOD_D)
        b.lantern(sx * 1.35, -F - 0.25, 2.55)
    # Hintertuer (Rueckwand, u = -1.9 -> x = +1.9)
    b.add(box((1.9, F - T + 0.02, FZ + 1.1), (0.9, 0.06, 2.2)), WOOD_DD)
    b.add(box((1.9, F - T - 0.02, FZ + 1.05), (0.7, 0.03, 0.9)), PANEL)
    b.add(box((1.6, F - T - 0.04, FZ + 1.0), (0.06, 0.05, 0.06)), GOLD)

    # --- Bar links
    BX = -2.5
    b.add(box((BX, 0.7, FZ + 0.55), (0.6, 4.4, 1.1)), PANEL)
    b.add(box((BX, 0.7, FZ + 1.13), (0.8, 4.6, 0.06)), WOOD_L)
    for k in range(7):
        b.add(box((BX + 0.31, -1.25 + k * 0.65, FZ + 0.55), (0.02, 0.5, 0.8)), WOOD_DD)
    b.add(xf(cyl((0, 0, -2.2), 0.03, 0.03, 4.4, 6), loc=(BX + 0.45, 0.7, FZ + 0.15), rot=(90, 0, 0)), BRASS)
    for k in range(5):
        stool(b, BX + 0.85, -1.0 + k * 0.85)
    for x, y in ((BX, -0.8), (BX, 0.2), (BX + 0.1, 1.5)):
        glass_cup(b, x, y, FZ + 1.16)
    bottle(b, BX - 0.1, 0.6, FZ + 1.16, "3C6E2A")
    b.add(box((BX - 0.2, 2.2, FZ + 1.26), (0.3, 0.2, 0.2)), WOOD)  # Kasse
    b.add(box((BX - 0.2, 2.2, FZ + 1.4), (0.26, 0.18, 0.08)), BRASS)
    # Rueckbuffet an der linken Wand
    RX = -W / 2 + T + 0.25
    b.add(box((RX, 0.7, FZ + 0.45), (0.5, 4.2, 0.9)), WOOD_DD)
    b.add(box((RX, 0.7, FZ + 0.92), (0.55, 4.3, 0.05)), WOOD_L)
    b.add(box((-W / 2 + T + 0.02, 0.7, FZ + 1.9), (0.04, 2.2, 1.2)), BRASS)
    b.add(box((-W / 2 + T + 0.05, 0.7, FZ + 1.9), (0.02, 2.0, 1.0)), "B9CCD6")  # Spiegel
    cols = ("3C6E2A", "7A3A1A", "C98A2E", "2F4A3A", "8C2F23")
    for s, zz in enumerate((FZ + 1.3, FZ + 2.6)):
        for side_y in (-1.0, 2.4):
            b.add(box((-W / 2 + T + 0.15, side_y, zz), (0.3, 1.2, 0.04)), WOOD_D)
            for k in range(6):
                bottle(b, -W / 2 + T + 0.15, side_y - 0.5 + k * 0.2, zz + 0.02, cols[(k + s) % 5])
    for k in range(8):
        bottle(b, RX, -0.9 + k * 0.4, FZ + 0.95, cols[k % 5])
    b.add(xf(cyl((0, 0, -0.35), 0.3, 0.3, 0.7, 10), loc=(RX, 2.8, FZ + 1.3), rot=(90, 0, 0)), WOOD)
    b.add(xf(cyl((0, 0, -0.36), 0.31, 0.31, 0.05, 10), loc=(RX, 2.8, FZ + 1.3), rot=(90, 0, 0)), IRON)
    b.add(box((RX, 2.43, FZ + 1.2), (0.05, 0.08, 0.1)), BRASS)
    # --- Tische
    round_table(b, -0.6, -1.7)
    round_table(b, 1.0, -0.1)
    for (x, y) in ((-0.6, -1.7), (1.0, -0.1)):
        bottle(b, x + 0.1, y, FZ + 0.79, "7A3A1A")
        glass_cup(b, x - 0.2, y + 0.1, FZ + 0.79)
        glass_cup(b, x + 0.15, y - 0.25, FZ + 0.79)
    # Pokertisch
    PX, PY = -0.3, 1.9
    b.add(cyl((PX, PY, FZ), 0.35, 0.35, 0.04, 8), WOOD_DD)
    b.add(cyl((PX, PY, FZ + 0.04), 0.08, 0.08, 0.7, 8), WOOD_DD)
    b.add(cyl((PX, PY, FZ + 0.74), 0.72, 0.72, 0.06, 12), WOOD_D)
    b.add(cyl((PX, PY, FZ + 0.8), 0.62, 0.62, 0.005, 12), FELT)
    for k, a in enumerate((0, 90, 180, 270)):
        ra = math.radians(a)
        chair(b, PX + 1.05 * math.sin(ra), PY - 1.05 * math.cos(ra), a + 180)
        cx, cy = PX + 0.42 * math.sin(ra), PY - 0.42 * math.cos(ra)
        for j in range(3):
            b.add(cyl((cx + 0.08 * j - 0.08, cy, FZ + 0.805), 0.03, 0.03, 0.02 * (j + 2), 8),
                  ("C8302C", "2F5E8C", WHITE)[j])
        b.add(xf(box((0, 0, 0), (0.1, 0.14, 0.004)), loc=(cx * 0.7 + PX * 0.3, cy * 0.7 + PY * 0.3, FZ + 0.81),
                 rot=(0, 0, a + 15)), WHITE)
    for k in range(5):
        b.add(xf(box((0, 0, 0), (0.1, 0.14, 0.004)), loc=(PX - 0.2 + k * 0.1, PY, FZ + 0.81)), WHITE)
    b.add(cyl((PX, PY, Z1 - 0.04), 0.12, 0.12, 0.04, 8), IRON)  # Haengelampe
    b.add(cyl((PX, PY, 2.6), 0.02, 0.02, 0.85, 6), IRON)
    b.add(cyl((PX, PY, 2.45), 0.3, 0.1, 0.18, 8), "3E5F4A")
    b.add(cyl((PX, PY, 2.4), 0.1, 0.1, 0.05, 8), bb.LAMP)
    # --- Klavier an der Rueckwand
    KX, KY = 0.2, D / 2 - T - 0.35
    b.add(box((KX, KY, FZ + 0.65), (1.5, 0.6, 1.3)), "3A2418")
    b.add(box((KX, KY - 0.4, FZ + 0.76), (1.45, 0.3, 0.06)), "3A2418")
    b.add(box((KX, KY - 0.4, FZ + 0.8), (1.3, 0.22, 0.03)), "F4F0E6")
    for k in range(18):
        if k % 7 not in (2, 6):
            b.add(box((KX - 0.6 + k * 0.07, KY - 0.35, FZ + 0.825), (0.03, 0.12, 0.02)), "111111")
    b.add(box((KX, KY - 0.31, FZ + 1.1), (1.2, 0.02, 0.3)), "4A2E1E")
    for sx in (-1, 1):
        b.add(box((KX + sx * 0.7, KY - 0.4, FZ + 0.38), (0.08, 0.08, 0.76)), "3A2418")
        b.add(cyl((KX + sx * 0.55, KY, FZ + 1.3), 0.05, 0.05, 0.12, 6), BRASS)
        b.add(cyl((KX + sx * 0.55, KY, FZ + 1.42), 0.02, 0.02, 0.1, 6), "F4F0E6")
        b.add(pyramid((KX + sx * 0.55, KY, FZ + 1.52), 0.02, 0.05, 4), bb.LAMP)
    b.add(box((KX, KY - 0.95, FZ + 0.48), (0.7, 0.35, 0.06)), "7A2E2A")
    for sx in (-1, 1):
        b.add(box((KX + sx * 0.3, KY - 0.95, FZ + 0.22), (0.05, 0.3, 0.45)), "3A2418")
    # --- Anwerbe-Tisch vorne rechts
    HX, HY = 2.1, -2.6
    b.add(box((HX, HY, FZ + 0.75), (1.3, 0.7, 0.05)), WOOD)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((HX + sx * 0.58, HY + sy * 0.28, FZ + 0.37), (0.05, 0.05, 0.74)), WOOD_DD)
    b.add(box((HX - 0.2, HY, FZ + 0.785), (0.3, 0.4, 0.01)), "F4EEDC")
    b.add(box((HX + 0.2, HY + 0.1, FZ + 0.79), (0.22, 0.3, 0.02)), "EDE0BF")
    b.add(xf(box((0, 0, 0), (0.01, 0.01, 0.2)), loc=(HX + 0.02, HY - 0.05, FZ + 0.86), rot=(25, 0, 30)), WHITE)
    b.add(cyl((HX + 0.02, HY - 0.05, FZ + 0.775), 0.03, 0.03, 0.05, 6), "1E1E1E")
    b.lantern(HX + 0.45, HY + 0.1, FZ + 0.95, arm=0.05)
    chair(b, HX, HY + 0.65, 180)
    chair(b, HX - 0.3, HY - 0.65, 0)
    chair(b, HX + 0.4, HY - 0.7, 10)
    # Anwerbe-Brett an der Vorderwand innen
    b.add(box((1.38, -F + T + 0.03, FZ + 1.85), (0.9, 0.06, 1.0)), WOOD_DD)
    b.add(box((1.38, -F + T + 0.065, FZ + 2.25), (0.84, 0.01, 0.16)), "8C2F23")
    b.add(text(SIGNS["board"], 0.065, (1.38, -F + T + 0.075, FZ + 2.25), 0.01, facing=180), WHITE)
    for k in range(2):
        px = 1.17 + k * 0.42
        b.add(box((px, -F + T + 0.07, FZ + 1.75), (0.3, 0.01, 0.42)), "F4EEDC")
        b.add(box((px, -F + T + 0.078, FZ + 1.85), (0.14, 0.005, 0.14)), "8A7A5A")
        b.add(box((px, -F + T + 0.078, FZ + 1.63), (0.22, 0.005, 0.03)), "3A2A1A")
    # --- Treppe an der rechten Wand
    n = 12
    rise = (Z2 - FZ) / n
    run = (HOLE[3] - HOLE[2]) / n
    SX = (HOLE[0] + HOLE[1]) / 2
    for k in range(n):
        zt = FZ + (k + 1) * rise
        y = HOLE[2] + (k + 0.5) * run
        b.add(box((SX, y, (FZ + zt) / 2), (HOLE[1] - HOLE[0], run, zt - FZ)), WOOD_D)
        b.add(box((SX, y - run / 2 + 0.02, zt - 0.01), (HOLE[1] - HOLE[0] + 0.02, 0.05, 0.03)), WOOD_L)
    for k in range(0, n + 1, 2):
        y = HOLE[2] + k * run
        zt = FZ + k * rise
        b.add(box((HOLE[0] + 0.05, y, zt + 0.5), (0.05, 0.05, 1.0)), WOOD_DD)
    hand0 = (HOLE[0] + 0.05, HOLE[2], FZ + 1.0)
    hand1 = (HOLE[0] + 0.05, HOLE[3], Z2 + 1.0)
    L = math.dist(hand0, hand1)
    ang = math.degrees(math.atan2(hand1[2] - hand0[2], hand1[1] - hand0[1]))
    b.add(xf(box((0, 0, 0), (0.07, L, 0.07)), loc=((hand0[0] + hand1[0]) / 2, (hand0[1] + hand1[1]) / 2,
                                                    (hand0[2] + hand1[2]) / 2), rot=(ang, 0, 0)), WOOD_L)
    b.add(box((HOLE[0] + 0.05, HOLE[2] - 0.05, FZ + 0.6), (0.12, 0.12, 1.2)), WOOD_DD)
    # --- Kronleuchter, Deko
    CX, CY = 0.4, -0.9
    b.add(cyl((CX, CY, 2.7), 0.02, 0.02, Z1 - 2.7, 6), IRON)
    for k in range(8):
        a = 2 * math.pi * k / 8
        x, y = CX + 0.5 * math.cos(a), CY + 0.5 * math.sin(a)
        b.add(xf(box((0, 0, 0), (0.05, 0.4, 0.04)), loc=(CX + 0.5 * math.cos(a + math.pi / 8),
                                                         CY + 0.5 * math.sin(a + math.pi / 8), 2.7),
                 rot=(0, 0, math.degrees(a + math.pi / 8))), BRASS)
        b.add(cyl((x, y, 2.72), 0.02, 0.02, 0.1, 6), "F4F0E6")
        b.add(pyramid((x, y, 2.82), 0.025, 0.07, 4), bb.LAMP)
    for side, u, zc, w, h, c in (("back", 1.1, 2.2, 1.0, 0.7, "4E7A3A"), ("back", -0.2, 2.3, 0.7, 0.5, "B07A45"),
                                 ("right", 0.0, 2.6, 0.8, 0.6, "2F5E8C"), ("left", 2.9, 2.4, 0.5, 0.7, "C98A2E")):
        picture(b, side, u, zc, w, h, c)
    # Hoerner ueber dem Spiegel
    b.add(box((-W / 2 + T + 0.08, 0.7, 3.05), (0.12, 0.3, 0.2)), "E8DDC4")
    for sy in (-1, 1):
        b.add(xf(box((0, 0, 0), (0.06, 0.5, 0.06), (0.5, 0.5)), loc=(-W / 2 + T + 0.15, 0.7 + sy * 0.35, 3.12),
                 rot=(sy * -25, 0, 0)), "E8DDC4")
    for side, u in (("back", 2.8), ("back", -2.9), ("front", -1.4)):
        sconce(b, side, u, 2.5)
    b.add(box((0, -1.8, FZ + 0.003), (1.2, 2.6, 0.006)), "8C2F23")  # Laeufer
    for x, y in ((-1.7, -2.8), (1.6, 1.3)):
        b.add(cyl((x, y, FZ), 0.14, 0.1, 0.18, 8), BRASS)  # Spucknapf
        b.add(cyl((x, y, FZ + 0.18), 0.12, 0.14, 0.04, 8), BRASS)
    b.barrel(-3.5, -2.8, FZ, 0.3, 0.85)
    b.barrel(-2.9, -3.0, FZ, 0.26, 0.7)
    b.add(box((-1.2, D / 2 - T - 0.3, FZ + 0.4), (0.9, 0.5, 0.8)), WOOD_D)  # Kiste Rueckwand
    b.crate(-1.2, D / 2 - T - 0.3, FZ + 0.8, 0.45, 8)

    # --- Aussen: Veranda, Balkonboden, Pfosten, Deko
    PY = -F - 1.3
    b.add(box((0, PY, 0.25), (W + 0.4, 2.6, 0.2)), WOOD_D)
    for i in range(12):
        b.add(box((-W / 2 - 0.2 + (i + 0.5) * (W + 0.4) / 12, PY, 0.355), (0.03, 2.6, 0.01)), WOOD_DD)
    b.add(box((0, -F - 2.75, 0.1), (2.4, 0.35, 0.2)), WOOD_D)
    for x in (-3.95, -1.3, 1.3, 3.95):
        b.add(box((x, -F - 2.45, 1.85), (0.2, 0.2, 3.0)), WOOD_DD)
        b.add(xf(box((0, 0, 0), (0.1, 0.5, 0.1)), loc=(x, -F - 2.25, 3.05), rot=(45, 0, 0)), WOOD_DD)
    b.add(box((0, PY, 3.45), (W + 0.4, 2.7, 0.2)), WOOD_DD)
    b.add(box((1.45, -F - 0.05, 1.8), (0.62, 0.06, 0.8)), WOOD_DD)
    b.add(box((1.45, -F - 0.09, 1.8), (0.52, 0.03, 0.66)), "F4EEDC")
    b.add(text(SIGNS["hiring"], 0.13, (1.45, -F - 0.11, 1.98), 0.02), "B83A32")
    b.barrel(3.5, -F - 0.5, 0.35)
    b.barrel(2.9, -F - 0.45, 0.35, r=0.26, h=0.7)
    b.bench(-2.6, -F - 0.4, 0.35)
    for sx in (-1, 1):
        y = -F - 3.8
        for x in (sx * 1.9, sx * 3.7):
            b.add(box((x, y, 0.5), (0.14, 0.14, 1.0)), WOOD_DD)
        b.add(box((sx * 2.8, y, 0.9), (2.0, 0.1, 0.1)), WOOD_D)
    return b.finish()


# ================================================================ OBERGESCHOSS
def upper_floor():
    b = Build("SaloonInterior_Upper")
    F = D / 2
    ix0, ix1, iy0, iy1 = -W / 2 + T, W / 2 - T, -D / 2 + T, D / 2 - T
    hx0, hx1, hy0, hy1 = HOLE
    zc = (Z1 + Z2) / 2
    for (x0, x1, y0, y1) in ((ix0, hx0, iy0, iy1), (hx0, ix1, iy0, hy0), (hx0, ix1, hy1, iy1)):
        b.add(box(((x0 + x1) / 2, (y0 + y1) / 2, zc), (x1 - x0, y1 - y0, Z2 - Z1)), WOOD_D)
    for k in range(6):  # Deckenbalken
        y = iy0 + 0.4 + k * 1.2
        if not (hy0 < y < hy1):
            b.add(box((0, y, Z1 - 0.08), (W - 2 * T, 0.14, 0.16)), WOOD_DD)
        else:
            b.add(box(((ix0 + hx0) / 2, y, Z1 - 0.08), (hx0 - ix0, 0.14, 0.16)), WOOD_DD)
    # Gelaender am Treppenloch
    b.add(box((hx0 - 0.03, (hy0 + hy1) / 2, Z2 + 0.95), (0.07, hy1 - hy0, 0.07)), WOOD_L)
    b.add(box(((hx0 + hx1) / 2, hy0 - 0.03, Z2 + 0.95), (hx1 - hx0, 0.07, 0.07)), WOOD_L)
    for k in range(9):
        b.add(box((hx0 - 0.03, hy0 + k * (hy1 - hy0) / 8, Z2 + 0.47), (0.04, 0.04, 0.95)), WOOD_L)
    for k in range(3):
        b.add(box((hx0 + k * 0.5, hy0 - 0.03, Z2 + 0.47), (0.04, 0.04, 0.95)), WOOD_L)
    # Waende OG
    front_open = [(-0.55, 0.55, Z2, Z2 + 2.1), win_open(-2.65, 4.8, 1.2, 1.4), win_open(2.65, 4.8, 1.2, 1.4)]
    side_open = [win_open(-1.8, 4.8, 1.0, 1.3), win_open(1.4, 4.8, 1.0, 1.3)]
    wall(b, "front", Z2, ZT, front_open)
    wall(b, "back", Z2, ZT, [])
    wall(b, "right", Z2, ZT, side_open)
    wall(b, "left", Z2, ZT, side_open)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, (Z2 + ZT) / 2), (0.22, 0.22, ZT - Z2)), WOOD_DD)
    for sx in (-1, 1):
        b.window(sx * 2.65, 4.8, 1.2, 1.4, F)
        inner_sill(b, "front", sx * 2.65, 4.8, 1.2, 1.4)
        for u in (-1.8, 1.4):
            b.window(u, 4.8, 1.0, 1.3, W / 2, side=90 * sx)
            inner_sill(b, "right" if sx > 0 else "left", u, 4.8, 1.0, 1.3)
    b.door(0, Z2 - 0.05, 1.1, 2.1, F, col=WOOD_DD)
    # Zwischenwand mit Zimmertueren
    PY = 0.9
    for x0, x1 in ((ix0, -2.9), (-2.1, -0.4), (0.4, hx0 - 0.1)):
        b.add(box(((x0 + x1) / 2, PY, (Z2 + ZT) / 2), (x1 - x0, 0.12, ZT - Z2)), "8A6A4A")
    for x in (-2.5, 0.0):
        b.add(box((x, PY, Z2 + 2.3), (0.8, 0.12, ZT - Z2 - 2.2 + 0.05)), "8A6A4A")
        b.add(box((x, PY - 0.07, Z2 + 1.05), (0.8, 0.04, 2.1)), WOOD_DD)
        b.add(box((x + 0.28, PY - 0.1, Z2 + 1.0), (0.05, 0.04, 0.05)), GOLD)
        b.add(box((x, PY - 0.1, Z2 + 1.8), (0.16, 0.01, 0.1)), BRASS)
    for sx in (-1, 1):
        sconce(b, "front", sx * 1.4, Z2 + 1.9)
    # Balkongelaender
    yb = -F - 2.55
    b.add(box((0, yb, 4.45), (W + 0.4, 0.1, 0.1)), TRIM)
    b.add(box((0, yb, 3.65), (W + 0.4, 0.1, 0.08)), TRIM)
    for i in range(21):
        b.add(box((-4.0 + i * 0.4, yb, 4.05), (0.06, 0.06, 0.8)), TRIM)
    for sx in (-1, 1):
        b.add(box((sx * 4.15, -F - 1.35, 4.45), (0.1, 2.6, 0.1)), TRIM)
        for j in range(6):
            b.add(box((sx * 4.15, -F - 0.1 - j * 0.45, 4.05), (0.06, 0.06, 0.8)), TRIM)
    # Scheinfassade + Schild
    b.add(box((0, -F - 0.1, 7.2), (W + 0.4, 0.2, 1.8)), WOOD)
    b.add(box((0, -F - 0.1, 8.3), (W * 0.55, 0.2, 0.4)), WOOD)
    b.add(box((0, -F - 0.1, 8.65), (W * 0.25, 0.2, 0.3)), WOOD)
    for zc2, wc in ((8.1, W + 0.6), (8.5, W * 0.55 + 0.2), (8.8, W * 0.25 + 0.2)):
        b.add(box((0, -F - 0.12, zc2), (wc, 0.34, 0.1)), TRIM)
    b.add(box((0, -F - 0.24, 7.15), (5.6, 0.06, 1.3)), WOOD_DD)
    b.add(box((0, -F - 0.28, 7.15), (5.3, 0.06, 1.05)), TRIM)
    b.add(text(SIGNS["saloon"], 0.95, (0, -F - 0.33, 7.15), 0.05), "8C2F23")
    return b.finish()


def roof():
    b = Build("SaloonInterior_Roof")
    b.add(box((0, 0.2, ZT + 0.1), (W + 0.3, D + 0.4, 0.2)), "5E4A3A")
    b.add(box((0, 0, ZT - 0.05), (W - 2 * T, D - 2 * T, 0.1)), WOOD_D)
    return b.finish()


# ==================================================================== MAIN
def main():
    base = ground_floor()
    up = upper_floor()
    rf = roof()
    for o in (up, rf):
        o.parent = base
    objs = [base, up, rf]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(bb.OUT, base.name + ".fbx"), use_selection=True,
        object_types={"MESH"}, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", bake_space_transform=True,
    )
    print(base.name, sum(len(o.data.polygons) for o in objs), "faces")
    cam, target = bb.setup_preview()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(bb.OUT, "saloon_interior.blend"))
    bb.render_shots([("interior_Exterior", (9, -21, 7.5), (0, -2, 3.2), 32)], cam, target)
    up.hide_render = rf.hide_render = True
    bb.render_shots([("interior_Cutaway", (7, -13, 12), (0, 0.2, 0.5), 30),
                     ("interior_View", (1.8, -3.0, 1.75), (-1.6, 2.2, 1.0), 20),
                     ("interior_Bar", (1.8, 2.6, 1.8), (-2.9, -0.6, 1.1), 22),
                     ("interior_Hiring", (-1.2, 1.0, 1.9), (1.9, -2.9, 1.2), 24)], cam, target)
    print("DONE")


if __name__ == "__main__":
    main()
