"""Stadt-Ergaenzung: Maschinenhaendler, Hotel, Sheriff-Buero und Strassen-Props.

Ausfuehren:  blender -b -P build_town_extras.py   (oder: python3 build_town_extras.py mit pip-Paket bpy)
Nutzt die Bauteile aus build_buildings.py. Gleiche Konventionen: Front nach -Y, Ursprung = Bodenmitte.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import build_buildings as bb  # noqa: E402
from build_buildings import (  # noqa: E402
    Build, box, cyl, pyramid, tri_x, tri_y, xf, text,
    WOOD, WOOD_D, WOOD_DD, WOOD_L, TRIM, STONE, STONE_L, GLASS, DOOR_DARK,
    IRON, METAL, GOLD, RED, WHITE, GREEN,
)

SIGNS = {
    "dealer": "MACHINES",
    "dealer_sub": "SALES & REPAIR",
    "office": "OFFICE",
    "hotel": "HOTEL",
    "rooms": "ROOMS",
    "sheriff": "SHERIFF",
    "wanted": "WANTED",
    "arrows": ("MINE", "TOWN", "RIVER"),
}

YELLOW = "F2C12E"
CONC = "A8A8A0"


def drum(b, x, y, z=0.0, col="2F5E8C", r=0.28, h=0.85):
    b.add(cyl((x, y, z), r, r, h, 10), col)
    for bz in (h * 0.33, h * 0.66):
        b.add(cyl((x, y, z + bz), r + 0.015, r + 0.015, 0.04, 10), col)
    b.add(cyl((x + r * 0.5, y, z + h), 0.05, 0.05, 0.02, 6), IRON)


def tire(b, x, y, z=0.0, r=0.55, w=0.35):
    b.add(cyl((x, y, z), r, r, w, 10), "2A2A2A")
    b.add(cyl((x, y, z + w), r * 0.55, r * 0.55, 0.005, 10), "3E3E3E")


def star(b, x, y, z, r, col=GOLD, t=0.06, n=5):
    """Stern mit n Zacken, Vorderseite nach -Y."""
    for k in range(n):
        a0 = math.pi / 2 + 2 * math.pi * k / n
        pts = [(0, 0), (r * 0.42 * math.cos(a0 - math.pi / n), r * 0.42 * math.sin(a0 - math.pi / n)),
               (r * math.cos(a0), r * math.sin(a0)),
               (r * 0.42 * math.cos(a0 + math.pi / n), r * 0.42 * math.sin(a0 + math.pi / n))]
        v = [(x + px, y - t / 2, z + pz) for px, pz in pts] + [(x + px, y + t / 2, z + pz) for px, pz in pts]
        f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        b.add((v, f), col)


def flower_box(b, x, y, z, w=1.0):
    b.add(box((x, y, z), (w, 0.28, 0.2)), WOOD_D)
    for i in range(int(w / 0.18)):
        fx = x - w / 2 + 0.1 + i * 0.18
        b.add(box((fx, y, z + 0.14), (0.14, 0.18, 0.1)), GREEN)
        b.add(box((fx + 0.03, y - 0.03, z + 0.22), (0.08, 0.08, 0.07)), ("D9425B", "F2C12E", "E86FA0")[i % 3])


# ======================================================== MASCHINENHAENDLER
def machine_dealer():
    b = Build("Building_MachineDealer")
    W, D, H = 14.0, 11.0, 6.0
    F = D / 2
    WALLC = "5F7A8C"
    RIB = "4E6575"
    b.add(box((0, -2.0, 0.05), (W + 10, D + 9, 0.1)), CONC)
    b.add(box((0, 0, 0.1 + H / 2), (W, D, H)), WALLC)
    # Wellblech-Rippen
    n = int(D / 0.35)
    for sx in (-1, 1):
        for j in range(n):
            b.add(box((sx * (W / 2 + 0.02), -D / 2 + 0.2 + j * (D - 0.4) / (n - 1), 0.1 + H / 2), (0.04, 0.08, H)), RIB)
    for i in range(int(W / 0.35)):
        x = -W / 2 + 0.2 + i * (W - 0.4) / (int(W / 0.35) - 1)
        b.add(box((x, F + 0.02, 0.1 + H / 2), (0.08, 0.04, H)), RIB)
    b.add(box((0, -F - 0.02, H - 0.2), (W, 0.06, 0.6)), YELLOW)
    b.add(tri_y(0, 0, 0.1 + H, W, D, 1.8), WALLC)
    b.gable_roof_y(0, 0, 0.1 + H, W, D, 1.8, over=0.35, col="8E969B")
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, 0.1 + H / 2), (0.25, 0.25, H)), YELLOW)
    # Rolltore: links offen, rechts geschlossen
    for x, open_ in ((-3.4, True), (2.6, False)):
        dw, dh = 4.4, 4.6
        b.add(box((x, -F - 0.05, 0.1 + dh / 2 + 0.1), (dw + 0.4, 0.1, dh + 0.2)), YELLOW)
        if open_:
            b.add(box((x, -F - 0.08, 0.1 + dh / 2), (dw, 0.06, dh)), "1E2226")
            b.add(box((x, -F - 0.1, 0.1 + dh - 0.35), (dw, 0.08, 0.7)), "B8BEC2")
            b.add(box((x, -F - 0.12, 0.1 + dh - 0.7), (dw, 0.06, 0.08)), IRON)
            # Hebebuehne innen angedeutet
            b.add(box((x - 1.1, -F + 1.5, 0.6), (0.25, 0.25, 1.0)), RED)
            b.add(box((x + 1.1, -F + 1.5, 0.6), (0.25, 0.25, 1.0)), RED)
        else:
            b.add(box((x, -F - 0.08, 0.1 + dh / 2), (dw, 0.06, dh)), "B8BEC2")
            for k in range(15):
                b.add(box((x, -F - 0.12, 0.25 + k * 0.3), (dw, 0.03, 0.05)), "8E969B")
            b.add(box((x, -F - 0.13, 0.3), (0.5, 0.06, 0.08)), IRON)
    # Schild am Giebel
    SZ = H + 0.75
    b.add(box((0, -F - 0.1, SZ), (7.2, 0.15, 1.5)), IRON)
    b.add(box((0, -F - 0.18, SZ), (7.0, 0.04, 1.3)), YELLOW)
    b.add(text(SIGNS["dealer"], 0.72, (0, -F - 0.21, SZ + 0.18), 0.05), "1E1E1E")
    b.add(text(SIGNS["dealer_sub"], 0.26, (0, -F - 0.21, SZ - 0.42), 0.03), "1E1E1E")
    for sx in (-1, 1):  # Flutlichter
        b.add(box((sx * 4.2, -F - 0.3, H - 0.3), (0.06, 0.5, 0.06)), IRON)
        b.add(box((sx * 4.2, -F - 0.55, H - 0.4), (0.4, 0.15, 0.25)), IRON)
        b.add(box((sx * 4.2, -F - 0.63, H - 0.4), (0.34, 0.02, 0.19)), bb.LAMP)
    # Buero-Anbau rechts
    OX = W / 2 + 2.2
    OW, OD, OH = 4.4, 6.0, 3.4
    OY = -F + OD / 2
    b.add(box((OX, OY, 0.1 + OH / 2), (OW, OD, OH)), "E8DCC0")
    b.add(box((OX, OY, 0.1 + OH + 0.1), (OW + 0.3, OD + 0.3, 0.2)), "5A5A5A")
    b.add(box((OX, OY, OH - 0.1), (OW + 0.05, OD + 0.05, 0.3)), YELLOW)
    b.door(OX - 1.1, 0.1, 1.0, 2.3, F, col="2F5E8C", frame=WHITE)
    b.window(OX + 0.9, 1.5, 1.6, 1.3, F, frame=WHITE)
    b.window(-0.5, 1.7, 1.4, 1.2, OX + OW / 2, side=90, frame=WHITE)
    b.window(1.8, 1.7, 1.4, 1.2, OX + OW / 2, side=90, frame=WHITE)
    b.add(box((OX, -F - 0.06, OH + 0.55), (2.4, 0.1, 0.55)), "1E1E1E")
    b.add(text(SIGNS["office"], 0.3, (OX, -F - 0.13, OH + 0.55), 0.03), YELLOW)
    # Hof: Reifen, Faesser, Werkzeugkiste, Kompressor
    for i in range(3):
        tire(b, -9.2, -3.0, 0.1 + i * 0.36, 0.6)
    tire(b, -9.0, -4.6, 0.1, 0.8, 0.45)
    for (x, y, c) in ((-9.4, 2.0, "2F5E8C"), (-8.8, 2.4, RED), (-9.3, 3.0, "2F5E8C"), (-8.7, 3.2, "4E7A3A")):
        drum(b, x, y, 0.1, c)
    b.add(box((-6.3, -F - 0.5, 0.6), (0.9, 0.5, 1.0)), RED)  # Werkzeugwagen
    for k in range(4):
        b.add(box((-6.3, -F - 0.76, 0.3 + k * 0.22), (0.8, 0.02, 0.03)), IRON)
    b.add(cyl((-6.3 - 0.3, -F - 0.5, 0.1), 0.06, 0.06, 0.12, 6), IRON)
    b.add(xf(cyl((0, 0, 0), 0.3, 0.3, 1.1, 8), loc=(6.2, -F - 0.6, 0.45), rot=(0, 90, 0), pivot=(0, 0, 0)), RED)
    b.add(box((6.75, -F - 0.6, 0.85), (0.35, 0.3, 0.3)), IRON)
    # Wimpelkette ueber dem Verkaufsplatz
    for x in (-11.5, 11.5):
        b.add(cyl((x, -F - 7.5, 0.1), 0.07, 0.06, 4.6, 6), METAL)
    b.add(box((0, -F - 7.5, 4.55), (23.0, 0.02, 0.02)), IRON)
    cols = (RED, YELLOW, "2F5E8C", WHITE)
    for k in range(38):
        x = -11.0 + k * 22.0 / 37
        b.add(tri_y(x, -F - 7.5, 4.54, 0.34, 0.01, -0.42), cols[k % 4])
    b.lamp_post(-10.5, -F - 1.0, 3.6)
    b.lamp_post(10.5, -F - 1.0, 3.6)
    return b.finish()


# ==================================================================== HOTEL
def hotel():
    b = Build("Building_Hotel")
    W, D = 9.0, 8.0
    FL = 3.2
    H = FL * 3
    F = D / 2
    WALLC = "3E6B5A"
    b.add(box((0, 0, 0.15), (W + 0.3, D + 0.3, 0.3)), STONE)
    b.add(box((0, 0, 0.3 + H / 2), (W, D, H)), WALLC)
    z = 0.6
    while z < 0.3 + H:
        b.add(box((0, -F - 0.015, z), (W, 0.03, 0.04)), "335A4B")
        for sx in (-1, 1):
            b.add(box((sx * (W / 2 + 0.015), 0, z), (0.03, D, 0.04)), "335A4B")
        z += 0.35
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, 0.3 + H / 2), (0.25, 0.25, H)), TRIM)
    for k in (1, 2):
        b.add(box((0, 0, 0.3 + k * FL), (W + 0.1, D + 0.1, 0.15)), TRIM)
    # Dach + Scheinfassade mit Schild
    ZT = 0.3 + H
    b.add(box((0, 0.2, ZT + 0.1), (W + 0.3, D + 0.4, 0.2)), "5E4A3A")
    b.add(box((0, -F - 0.1, ZT + 0.8), (W + 0.4, 0.2, 1.6)), WALLC)
    b.add(tri_y(0, -F - 0.1, ZT + 1.6, 4.0, 0.2, 0.8), WALLC)
    b.add(box((0, -F - 0.12, ZT + 1.6), (W + 0.7, 0.3, 0.12)), TRIM)
    b.add(box((0, -F - 0.22, ZT + 0.8), (6.0, 0.06, 1.3)), TRIM)
    b.add(box((0, -F - 0.26, ZT + 0.8), (5.7, 0.05, 1.08)), "7A2E2A")
    b.add(text(SIGNS["hotel"], 0.95, (0, -F - 0.3, ZT + 0.8), 0.05), GOLD)
    b.add(box((2.2, 2.0, ZT + 0.9), (0.8, 0.8, 1.6)), "8E4634")  # Schornstein
    b.add(box((2.2, 2.0, ZT + 1.75), (1.0, 1.0, 0.15)), STONE)
    # Erdgeschoss
    b.door(0, 0.3, 1.8, 2.6, F, col="5A3A22", frame=TRIM, double=True)
    b.add(box((0, -F - 0.05, 3.1), (1.8, 0.06, 0.35)), GLASS)
    for sx in (-1, 1):
        b.window(sx * 3.0, 1.8, 1.5, 1.6, F, frame=TRIM)
        b.lantern(sx * 1.4, -F - 0.25, 2.5)
    # Vordach am Eingang
    b.add(box((0, -F - 1.1, 3.25), (3.2, 2.2, 0.15)), "7A2E2A")
    b.add(box((0, -F - 2.15, 3.15), (3.2, 0.1, 0.3)), TRIM)
    for sx in (-1, 1):
        b.add(box((sx * 1.5, -F - 2.1, 1.75), (0.14, 0.14, 2.9)), TRIM)
    b.add(box((0, -F - 1.1, 0.35), (3.4, 2.4, 0.1)), "7A2E2A")  # Teppich/Podest
    # Obergeschosse mit Blumenkaesten + Fensterlaeden
    for k in (1, 2):
        zc = 0.3 + k * FL + 1.55
        for x in (-3.3, -1.1, 1.1, 3.3):
            b.window(x, zc, 1.0, 1.5, F, frame=TRIM, shutters="7A2E2A", sill=False)
            flower_box(b, x, -F - 0.16, zc - 0.9, 1.1)
    # Seitenfenster
    for sx in (-1, 1):
        for k in range(3):
            for u in (-2.2, 0.0, 2.2):
                b.window(u, 0.3 + k * FL + 1.6, 0.9, 1.4, W / 2, side=90 * sx, frame=TRIM)
    # Haengeschild ROOMS
    b.add(box((W / 2 + 0.55, -F + 0.4, 2.9), (1.1, 0.06, 0.06)), IRON)
    b.add(box((W / 2 + 0.65, -F + 0.4, 2.5), (1.0, 0.06, 0.55)), TRIM)
    b.add(text(SIGNS["rooms"], 0.2, (W / 2 + 0.65, -F + 0.36, 2.5), 0.02), "7A2E2A")
    b.add(text(SIGNS["rooms"], 0.2, (W / 2 + 0.65, -F + 0.44, 2.5), 0.02, facing=180), "7A2E2A")
    # Deko: Pflanzkuebel, Bank, Koffer
    for sx in (-1, 1):
        b.add(cyl((sx * 2.0, -F - 2.4, 0.0), 0.3, 0.38, 0.55, 8), "B5654B")
        b.bush(sx * 2.0, -F - 2.4, 0.33, z=0.5)
    b.bench(-3.2, -F - 0.5, 0.3)
    b.add(box((3.1, -F - 0.6, 0.55), (0.8, 0.45, 0.5)), "7A4A26")
    b.add(box((3.1, -F - 0.6, 0.55), (0.82, 0.47, 0.06)), WOOD_DD)
    b.add(box((3.3, -F - 0.5, 0.95), (0.6, 0.35, 0.3)), "4E6575")
    b.add(box((3.3, -F - 0.5, 1.12), (0.2, 0.06, 0.05)), IRON)
    return b.finish()


# =================================================================== SHERIFF
def sheriff():
    b = Build("Building_Sheriff")
    W, D, H = 7.0, 7.0, 4.2
    F = D / 2
    WALLC = "8A6A4A"
    b.add(box((0, 0, 0.2), (W + 0.3, D + 0.3, 0.4)), STONE)
    b.add(box((0, 0, 0.4 + 0.6), (W, D, 1.2)), STONE_L)  # Steinsockel
    b.add(box((0, 0, 0.4 + H / 2), (W - 0.04, D - 0.04, H)), WALLC)
    z = 1.8
    while z < 0.4 + H:
        b.add(box((0, -F - 0.015, z), (W, 0.03, 0.04)), WOOD_D)
        for sx in (-1, 1):
            b.add(box((sx * (W / 2 + 0.015), 0, z), (0.03, D, 0.04)), WOOD_D)
        z += 0.35
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, 0.4 + H / 2), (0.22, 0.22, H)), WOOD_DD)
    ZT = 0.4 + H
    b.add(box((0, 0.2, ZT + 0.1), (W + 0.3, D + 0.4, 0.2)), "5E4A3A")
    # Scheinfassade mit Stufen, Schild und Stern
    b.add(box((0, -F - 0.1, ZT + 0.8), (W + 0.3, 0.2, 1.6)), WALLC)
    b.add(box((0, -F - 0.1, ZT + 1.8), (3.0, 0.2, 0.4)), WALLC)
    b.add(box((0, -F - 0.12, ZT + 1.6), (W + 0.5, 0.3, 0.1)), TRIM)
    b.add(box((0, -F - 0.12, ZT + 2.0), (3.2, 0.3, 0.1)), TRIM)
    b.add(box((0, -F - 0.22, ZT + 0.75), (5.2, 0.06, 1.0)), WOOD_DD)
    b.add(box((0, -F - 0.26, ZT + 0.75), (5.0, 0.05, 0.84)), TRIM)
    b.add(text(SIGNS["sheriff"], 0.62, (0.35, -F - 0.3, ZT + 0.75), 0.05), "3A2A1A")
    star(b, -2.0, -F - 0.32, ZT + 0.75, 0.36)
    # Vordach (Pultdach) auf Pfosten
    b.add(box((0, -F - 0.9, 0.5), (W + 0.3, 1.8, 0.2)), WOOD_D)
    for x in (-W / 2, -1.2, 1.2, W / 2):
        b.add(box((x, -F - 1.7, 1.95), (0.16, 0.16, 2.9)), WOOD_DD)
    b.add(xf(box((0, -F - 0.95, 3.5), (W + 0.5, 2.1, 0.12)), rot=(-10, 0, 0), pivot=(0, -F, 3.6)), "8E969B")
    # Tuer, Fenster, Gitterfenster
    b.door(0, 0.6, 1.1, 2.3, F, col=WOOD_DD, frame=WOOD_L)
    b.window(-2.2, 2.0, 1.3, 1.3, F, frame=WOOD_L, shutters="3E5F4A")
    for sx in (-1, 1):
        for u in (-1.6, 1.4):
            b.window(u, 2.6, 0.8, 0.7, W / 2, side=90 * sx, frame=STONE_L, cross=False)
            t = Build("t")
            t.bars(u, 2.6, 0.8, 0.7, W / 2, n=4)
            for geo, c in t.parts:
                b.add(xf(geo, rot=(0, 0, 90 * sx)), c)
    # Steckbrief-Brett
    BX = 2.2
    b.add(box((BX, -F - 0.05, 2.1), (1.5, 0.08, 1.1)), WOOD_DD)
    for i, px in enumerate((-0.38, 0.38)):
        b.add(box((BX + px, -F - 0.1, 2.1), (0.62, 0.02, 0.85)), "EDE0BF")
        b.add(text(SIGNS["wanted"], 0.09, (BX + px, -F - 0.115, 2.43), 0.01), "3A2A1A")
        b.add(box((BX + px, -F - 0.115, 2.12), (0.3, 0.01, 0.34)), "8A7A5A")
        b.add(box((BX + px, -F - 0.115, 1.83), (0.4, 0.01, 0.05)), "3A2A1A")
        b.add(box((BX + px, -F - 0.115, 1.74), (0.3, 0.01, 0.03)), "3A2A1A")
    # Deko
    b.bench(-2.2, -F - 0.5, 0.6, 1.4)
    b.barrel(3.1, -F - 0.45, 0.6, 0.26, 0.7)
    for x in (-2.6, 2.6):
        b.add(box((x, -F - 2.6, 0.5), (0.14, 0.14, 1.0)), WOOD_DD)
    b.add(box((0, -F - 2.6, 0.9), (5.3, 0.1, 0.1)), WOOD_D)
    b.lantern(0.95, -F - 0.25, 2.6)
    return b.finish()


# ==================================================================== PROPS
def prop_street_lamp():
    b = Build("Prop_StreetLamp")
    b.lamp_post(0, 0, 3.2)
    return b.finish()


def prop_signpost():
    b = Build("Prop_Signpost")
    b.add(box((0, 0, 1.4), (0.14, 0.14, 2.8)), WOOD_DD)
    b.add(pyramid((0, 0, 2.8), 0.12, 0.12), WOOD_DD)
    b.add(box((0, 0, 0.1), (0.3, 0.3, 0.2)), STONE)
    for k, (label, ang) in enumerate(zip(SIGNS["arrows"], (-20, 150, 60))):
        z = 2.45 - k * 0.42
        flip = 1
        g = [(box((0.66 * flip, -0.09, z), (1.2, 0.05, 0.3)), WOOD_L),
             (xf(tri_x(0, 0, 0, 0.05, 0.3, 0.22), loc=(1.26 * flip, -0.09, z), rot=(0, 90, 0)), WOOD_L),
             (text(label, 0.17, (0.63 * flip, -0.12, z), 0.02), "3A2A1A"),
             (text(label, 0.17, (0.63 * flip, -0.06, z), 0.02, facing=180), "3A2A1A")]
        for geo, c in g:
            b.add(xf(geo, rot=(0, 0, ang)), c)
    return b.finish()


def prop_mailbox():
    b = Build("Prop_Mailbox")
    b.add(box((0, 0, 0.55), (0.1, 0.1, 1.1)), WOOD_DD)
    b.add(box((0, 0, 1.12), (0.3, 0.5, 0.06)), WOOD_DD)
    b.add(box((0, 0, 1.25), (0.26, 0.48, 0.2)), "2F5E8C")
    b.add(xf(cyl((0, 0, -0.24), 0.13, 0.13, 0.48, 8), loc=(0, 0, 1.35), rot=(90, 0, 0)), "2F5E8C")
    b.add(box((0.15, 0.05, 1.45), (0.03, 0.04, 0.3)), RED)
    b.add(box((0.15, 0.13, 1.56), (0.03, 0.14, 0.09)), RED)
    return b.finish()


def prop_water_tower():
    b = Build("Prop_WaterTower")
    R, LZ = 1.6, 4.5
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(xf(box((0, 0, LZ / 2), (0.22, 0.22, LZ + 0.2)), loc=(sx * 1.25, sy * 1.25, 0),
                     rot=(sy * 4, -sx * 4, 0), pivot=(0, 0, LZ)), WOOD_DD)
    for z in (1.4, 3.0):
        for s in (-1, 1):
            b.add(box((0, s * 1.3, z), (2.7, 0.1, 0.12)), WOOD_D)
            b.add(box((s * 1.3, 0, z + 0.12), (0.1, 2.5, 0.12)), WOOD_D)
    for s in (-1, 1):
        b.add(xf(box((0, 0, 0), (0.08, 0.08, 2.6)), loc=(0, s * 1.34, 2.2), rot=(0, 55, 0)), WOOD_D)
        b.add(xf(box((0, 0, 0), (0.08, 0.08, 2.6)), loc=(s * 1.34, 0, 2.2), rot=(55, 0, 0)), WOOD_D)
    b.add(box((0, 0, LZ + 0.1), (3.4, 3.4, 0.2)), WOOD_D)
    b.add(cyl((0, 0, LZ + 0.2), R, R, 2.6, 12), WOOD)
    for i in range(12):
        a = 2 * math.pi * (i + 0.5) / 12
        b.add(xf(box((0, 0, 1.3), (0.04, 0.04, 2.6)), loc=(R * 0.99 * math.cos(a), R * 0.99 * math.sin(a), LZ + 0.2),
                 rot=(0, 0, math.degrees(a))), WOOD_D)
    for z in (0.3, 1.2, 2.2):
        b.add(cyl((0, 0, LZ + 0.2 + z), R + 0.03, R + 0.03, 0.08, 12), IRON)
    b.add(cyl((0, 0, LZ + 2.8), R + 0.2, 0.05, 1.1, 12), "5B6770")
    # Leiter + Auslauf
    for dx in (-0.2, 0.2):
        b.add(box((dx, -1.45, LZ / 2 + 0.5), (0.06, 0.06, LZ + 1.0)), WOOD_L)
    for k in range(14):
        b.add(box((0, -1.45, 0.4 + k * 0.36), (0.4, 0.05, 0.04)), WOOD_L)
    b.add(xf(box((0, 0, 0), (0.1, 1.2, 0.1)), loc=(1.3, -1.3, LZ + 0.1), rot=(20, 0, 45)), IRON)
    return b.finish()


def prop_fence():
    b = Build("Prop_Fence")
    for x in (-1.2, 1.2):
        b.add(box((x, 0, 0.6), (0.14, 0.14, 1.2)), WOOD_DD)
        b.add(pyramid((x, 0, 1.2), 0.1, 0.08), WOOD_DD)
    for z in (0.45, 0.95):
        b.add(box((0, -0.09, z), (2.5, 0.05, 0.14)), WOOD_D)
    b.add(xf(box((0, -0.12, 0.7), (2.6, 0.04, 0.12)), rot=(0, -11, 0), pivot=(0, 0, 0.7)), WOOD_D)
    return b.finish()


def prop_well():
    b = Build("Prop_Well")
    b.add(cyl((0, 0, 0), 0.95, 0.9, 0.8, 10, rot=0.3), STONE_L)
    b.add(cyl((0, 0, 0.8), 0.98, 0.98, 0.1, 10, rot=0.3), STONE)
    b.add(cyl((0, 0, 0.86), 0.7, 0.7, 0.05, 10), "2B4A6B")
    for sx in (-1, 1):
        b.add(box((sx * 0.85, 0, 1.3), (0.14, 0.14, 1.9)), WOOD_DD)
    b.add(tri_x(0, 0, 2.25, 2.1, 1.6, 0.6), WOOD_D)
    b.gable_roof_x(0, 0, 2.25, 2.0, 1.4, 0.6, over=0.25, t=0.08, col="7A3A2E")
    b.add(xf(cyl((0, 0, -0.85), 0.08, 0.08, 1.7, 8), loc=(0, 0, 1.75), rot=(0, 90, 0)), WOOD_L)
    b.add(box((1.0, 0, 1.75), (0.1, 0.05, 0.05)), IRON)
    b.add(box((1.05, 0, 1.6), (0.05, 0.05, 0.3)), IRON)
    b.add(box((0, 0, 1.3), (0.02, 0.02, 0.8)), "C9B08A")
    b.add(cyl((0, 0, 0.72), 0.15, 0.18, 0.25, 8), WOOD_D)
    return b.finish()


def prop_trough():
    b = Build("Prop_Trough")
    b.add(box((0, 0, 0.35), (2.0, 0.7, 0.5)), WOOD_D)
    b.add(box((0, 0, 0.55), (1.85, 0.55, 0.12)), "3F7FA6")
    for x in (-0.8, 0.8):
        b.add(box((x, 0, 0.15), (0.12, 0.8, 0.3)), WOOD_DD)
    return b.finish()


# ==================================================================== MAIN
def main():
    buildings = [machine_dealer(), hotel(), sheriff()]
    props = [prop_street_lamp(), prop_signpost(), prop_mailbox(), prop_water_tower(),
             prop_fence(), prop_well(), prop_trough()]
    for ob in buildings + props:
        bb.export_mesh(ob)
    cam, target = bb.setup_preview()
    xs = [-18, 2, 16]
    for ob, x in zip(buildings, xs):
        ob.location.x = x
    prop_pos = [(-6, -18), (-3.5, -18), (-1.8, -18), (2.5, -17), (6, -18), (9.5, -18), (12.5, -18)]
    for ob, (x, y) in zip(props, prop_pos):
        ob.location = (x, y, 0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(bb.OUT, "town_extras.blend"))
    shots = [("extras_all", (0, -52, 20), (0, -6, 3), 26),
             ("extras_MachineDealer", (-5, -27, 9), (-17, -5, 3.5), 30),
             ("extras_Hotel", (12, -25, 10), (2, -2, 5.5), 28),
             ("extras_Sheriff", (23, -16, 6), (16, -2, 2.8), 32),
             ("extras_Props", (5, -30, 5), (3.5, -18, 2.2), 34)]
    bb.render_shots(shots, cam, target)
    print("DONE")


if __name__ == "__main__":
    main()
