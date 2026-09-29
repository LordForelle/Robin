"""Bergbau-, Camp- und Natur-Props fuer den Goldgraeber-Simulator.

Ausfuehren:  blender -b -P build_props.py   (oder: python3 build_props.py mit pip-Paket bpy)
Nutzt die Bauteile aus ../Buildings/build_buildings.py. Front nach -Y, Ursprung = Bodenmitte.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "Buildings"))
import bpy  # noqa: E402  (bpy vor bmesh laden)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import build_buildings as bb  # noqa: E402
from build_buildings import (  # noqa: E402
    Build, box, cyl, pyramid, tri_x, tri_y, xf, text,
    WOOD, WOOD_D, WOOD_DD, WOOD_L, STONE, STONE_L, GLASS, IRON, METAL, GOLD, RED, WHITE, GREEN,
)

bb.OUT = HERE

SIGNS = {
    "diesel": "DIESEL",
    "danger": "DANGER",
    "keep_out": "KEEP OUT",
    "claim": "GOLD CLAIM",
    "office": "OFFICE",
}

DARK = "1E1E1E"
TIRE = "2A2A2A"
YELLOW = "F2C12E"
BLUE = "2F5E8C"
WATER = "3F7FA6"
CANVAS = "D9C9A3"
CANVAS_D = "BFAE86"
DIRT = "6B4A2E"
GRAVEL = "8C857A"
ROCK = "7E7A72"
ROCK_D = "656159"
FLAME = "FF8A1E"
FLAME_L = "FFD23F"
BARK = "5A3A22"
WOODCUT = "D9B77E"


def emissive(hexcol, strength=4.0):
    m = bb.mat(hexcol)
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission Color"].default_value = bsdf.inputs["Base Color"].default_value
    bsdf.inputs["Emission Strength"].default_value = strength


emissive(FLAME)
emissive(FLAME_L)


# ------------------------------------------------------------- Helfer
def beam(p0, p1, w, h=None):
    """Quader von p0 nach p1 (Streben, Seile, Beine)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    m = d.to_track_quat("Z", "Y").to_matrix()
    v, f = box((0, 0, 0), (w, h or w, d.length))
    mid = (p0 + p1) / 2
    return [tuple(m @ Vector(q) + mid) for q in v], f


def rock_geo(c, size, seed, sub=1, jitter=0.22, sink=0.3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    rng = random.Random(seed)
    v = []
    for q in bm.verts:
        k = 1 + rng.uniform(-jitter, jitter)
        v.append((c[0] + q.co.x * size[0] * k, c[1] + q.co.y * size[1] * k,
                  c[2] + (q.co.z * k + sink) * size[2]))
    f = [tuple(x.index for x in face.verts) for face in bm.faces]
    bm.free()
    return v, f


def pile_geo(c, r, h, seed, jitter=0.12):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    rng = random.Random(seed)
    v = []
    for q in bm.verts:
        k = 1 + rng.uniform(-jitter, jitter)
        z = max(q.co.z, -0.02)
        v.append((c[0] + q.co.x * r * k, c[1] + q.co.y * r * k, c[2] + z * h * k))
    f = [tuple(x.index for x in face.verts) for face in bm.faces]
    bm.free()
    return v, f


def log(b, p0, p1, r, n=8):
    """Stamm von p0 nach p1 mit hellen Schnittflaechen."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    m = d.to_track_quat("Z", "Y").to_matrix()
    for geo, col in ((cyl((0, 0, 0), r, r, d.length, n), BARK),
                     (cyl((0, 0, -0.01), r * 0.85, r * 0.85, d.length + 0.02, n), WOODCUT)):
        b.add(([tuple(m @ Vector(q) + p0) for q in geo[0]], geo[1]), col)


def skid(b, w, d, h=0.15):
    b.add(box((0, 0, h / 2), (w, d, h)), DARK)
    for sx in (-1, 1):
        b.add(box((sx * (w / 2 - 0.05), 0, h + 0.04), (0.1, d, 0.08)), DARK)


def wheel_static(b, x, y, r, w):
    b.add(xf(cyl((0, 0, -w / 2), r, r, w, 10), loc=(x, y, r), rot=(0, 90, 0)), TIRE)
    b.add(xf(cyl((0, 0, -w / 2 - 0.01), r * 0.55, r * 0.55, w + 0.02, 8), loc=(x, y, r), rot=(0, 90, 0)), METAL)


# ============================================================== BERGBAU
def sluice_box():
    b = Build("Mining_SluiceBox")
    L, Wt = 4.0, 0.7
    ang = 7
    piv = (0, 0, 1.0)

    def t(geo):
        return xf(geo, rot=(ang, 0, 0), pivot=piv)

    b.add(t(box((0, 0, 1.0), (Wt, L, 0.05))), "3C6E47")  # Matte
    for sx in (-1, 1):
        b.add(t(box((sx * (Wt / 2 + 0.03), 0, 1.15), (0.06, L, 0.35))), "7A8288")
    for k in range(12):
        b.add(t(box((0, -L / 2 + 0.3 + k * 0.3, 1.06), (Wt, 0.04, 0.07))), METAL)
    b.add(t(box((0, -0.1, 1.08), (Wt, L - 0.3, 0.02))), WATER)
    # Aufgabekasten oben (+Y) mit Spruehrohr
    b.add(t(box((0, L / 2 + 0.35, 1.35), (1.0, 0.7, 0.7))), "7A8288")
    b.add(t(box((0, L / 2 + 0.35, 1.71), (0.9, 0.6, 0.02))), DIRT)
    b.add(t(xf(cyl((0, 0, -0.6), 0.05, 0.05, 1.2, 8), loc=(0, L / 2 + 0.05, 1.8), rot=(0, 90, 0))), BLUE)
    b.add(t(beam((0.6, L / 2 + 0.05, 1.8), (1.2, L / 2 + 1.5, 0.05), 0.09)), DARK)  # Schlauch
    # Beine
    for sy, hz in ((-1, 0.72), (1, 1.25)):
        for sx in (-1, 1):
            y = sy * (L / 2 - 0.3)
            z = 1.0 - math.tan(math.radians(ang)) * -y
            b.add(box((sx * (Wt / 2 + 0.1), y, z / 2), (0.08, 0.08, z)), IRON)
        b.add(box((0, y, 0.3), (Wt + 0.28, 0.06, 0.06)), IRON)
    # Auslauf-Wasser
    b.add(box((0, -L / 2 - 0.6, 0.01), (1.2, 1.0, 0.02)), WATER)
    b.add(box((0.8, 0.8, 0.15), (0.5, 0.35, 0.3), (0.9, 0.9)), "D9822B")  # Eimer-Kiste
    return b.finish()


def generator():
    b = Build("Mining_Generator")
    skid(b, 1.2, 2.6)
    b.add(box((0, 0, 0.83), (1.05, 2.4, 1.2)), YELLOW)
    b.add(box((0, 0, 1.45), (1.1, 2.45, 0.06)), YELLOW)
    b.add(box((0, -1.21, 0.85), (0.8, 0.02, 0.8)), DARK)
    for k in range(6):
        b.add(box((0, -1.23, 0.55 + k * 0.12), (0.76, 0.02, 0.03)), "4A4A4A")
    b.add(box((0, 1.21, 0.8), (0.8, 0.02, 0.8)), DARK)
    for sx in (-1, 1):
        for y in (-0.5, 0.45):
            b.add(box((sx * 0.527, y, 0.83), (0.01, 0.02, 1.0)), "B8961E")
        b.add(box((sx * 0.535, -0.05, 0.9), (0.02, 0.12, 0.05)), DARK)
    b.add(box((0.535, 0.75, 0.95), (0.02, 0.5, 0.5)), DARK)  # Schalttafel
    for k in range(3):
        b.add(xf(cyl((0, 0, 0), 0.06, 0.06, 0.02, 8), loc=(0.55, 0.6 + k * 0.15, 1.05), rot=(0, 90, 0)), WHITE)
    b.add(box((0.55, 0.75, 0.8), (0.02, 0.3, 0.06)), RED)
    b.add(cyl((-0.25, 0.8, 1.48), 0.07, 0.07, 0.5, 8), IRON)
    b.add(cyl((-0.25, 0.8, 1.98), 0.09, 0.09, 0.06, 8), IRON)
    b.add(cyl((0.3, -0.7, 1.48), 0.07, 0.07, 0.05, 8), DARK)
    b.add(box((0, 0, 1.55), (0.3, 0.08, 0.15)), IRON)  # Kranoese
    b.add(xf(cyl((0, 0, 0), 0.25, 0.25, 0.12, 10), loc=(0.62, 0.2, 0.3), rot=(0, 90, 0)), DARK)  # Kabelrolle
    b.add(xf(cyl((0, 0, 0), 0.12, 0.12, 0.13, 8), loc=(0.62, 0.2, 0.3), rot=(0, 90, 0)), "4A4A4A")
    return b.finish()


def water_pump():
    b = Build("Mining_WaterPump")
    skid(b, 0.8, 1.4)
    b.add(box((0, 0.3, 0.5), (0.6, 0.6, 0.55)), RED)
    b.add(box((0, 0.3, 0.8), (0.4, 0.4, 0.1)), DARK)
    b.add(cyl((0.2, 0.55, 0.78), 0.05, 0.05, 0.25, 6), IRON)
    b.add(xf(cyl((0, 0, -0.2), 0.25, 0.25, 0.4, 10), loc=(0, -0.35, 0.45), rot=(90, 0, 0)), BLUE)
    b.add(xf(cyl((0, 0, 0), 0.1, 0.1, 0.6, 8), loc=(0, -0.55, 0.4), rot=(90, 0, 0)), DARK)
    b.add(beam((0, -1.15, 0.4), (0, -2.3, 0.08), 0.18), DARK)
    b.add(cyl((0, -0.35, 0.7), 0.07, 0.07, 0.5, 8), METAL)
    b.add(xf(cyl((0, 0, -0.08), 0.14, 0.14, 0.02, 8), loc=(0, -0.35, 1.05), rot=(0, 0, 0)), RED)
    b.add(beam((0, -0.35, 1.2), (0.9, 0.9, 0.08), 0.12), BLUE)
    return b.finish()


def water_tank():
    b = Build("Mining_WaterTank")
    b.add(box((0, 0, 0.08), (1.2, 1.0, 0.16)), WOOD_D)
    for x in (-0.45, 0, 0.45):
        b.add(box((x, 0, 0.18), (0.15, 1.0, 0.04)), WOOD_L)
    b.add(box((0, 0, 0.75), (1.12, 0.92, 1.1)), "E8E8E0")
    for sx in (-1, 1):
        for k in range(4):
            b.add(box((sx * 0.57, -0.4 + k * 0.27, 0.75), (0.03, 0.03, 1.15)), METAL)
            b.add(box((-0.4 + k * 0.27, sx * 0.47, 0.75), (0.03, 0.03, 1.15)), METAL)
        for z in (0.3, 0.75, 1.2):
            b.add(box((sx * 0.57, 0, z), (0.03, 0.97, 0.03)), METAL)
            b.add(box((0, sx * 0.47, z), (1.17, 0.03, 0.03)), METAL)
    b.add(box((0, 0, 1.31), (0.3, 0.3, 0.02)), METAL)
    b.add(cyl((0, 0, 1.32), 0.12, 0.12, 0.06, 8), "4A4A4A")
    b.add(box((0, -0.52, 0.32), (0.15, 0.14, 0.12)), DARK)
    b.add(box((0, -0.6, 0.32), (0.18, 0.04, 0.04)), RED)
    b.add(box((0, 0.2, 0.5), (1.13, 0.2, 0.3)), WATER)  # Fuellstand angedeutet
    return b.finish()


def conveyor():
    b = Build("Mining_Conveyor")
    L, H = 6.0, 1.2
    for sx in (-1, 1):
        b.add(box((sx * 0.45, 0, H), (0.08, L, 0.2)), RED)
        for k in range(10):
            b.add(xf(cyl((0, 0, -0.03), 0.05, 0.05, 0.06, 6), loc=(sx * 0.47, -L / 2 + 0.3 + k * 0.6, H + 0.05),
                     rot=(0, 90, 0)), IRON)
    b.add(box((0, 0, H + 0.1), (0.8, L - 0.2, 0.04)), DARK)
    b.add(box((0, 0, H - 0.08), (0.8, L - 0.2, 0.04)), DARK)
    for y in (-L / 2 + 0.1, L / 2 - 0.1):
        b.add(xf(cyl((0, 0, -0.45), 0.13, 0.13, 0.9, 10), loc=(0, y, H + 0.01), rot=(0, 90, 0)), IRON)
    for y in (-L / 2 + 0.5, 0, L / 2 - 0.5):
        for sx in (-1, 1):
            b.add(box((sx * 0.45, y, (H - 0.1) / 2), (0.08, 0.08, H - 0.1)), IRON)
        b.add(beam((-0.45, y, 0.2), (0.45, y, H - 0.2), 0.05), IRON)
    b.add(box((0.6, L / 2 - 0.4, H + 0.05), (0.35, 0.4, 0.3)), BLUE)  # Motor
    b.add(xf(cyl((0, 0, 0), 0.12, 0.12, 0.3, 8), loc=(0.6, L / 2 - 0.6, H + 0.05), rot=(90, 0, 0)), BLUE)
    for k in range(5):  # Material auf dem Band
        b.add(rock_geo((-0.15 + (k % 3) * 0.15, -2.0 + k * 0.9, H + 0.13), (0.12, 0.12, 0.06), 90 + k, 0, 0.3, 0.2), DIRT)
    return b.finish()


def dirt_pile():
    b = Build("Mining_DirtPile")
    b.add(pile_geo((0, 0, 0), 2.2, 1.4, 1), DIRT)
    for k in range(6):
        a = k * 1.1
        b.add(rock_geo((1.9 * math.cos(a), 1.9 * math.sin(a), 0), (0.2, 0.18, 0.15), 10 + k, 0), ROCK_D)
    return b.finish()


def gravel_pile():
    b = Build("Mining_GravelPile")
    b.add(pile_geo((0, 0, 0), 2.0, 1.6, 2, 0.08), GRAVEL)
    for k in range(10):
        a = k * 0.7
        rr = 1.3 + (k % 3) * 0.25
        b.add(rock_geo((rr * math.cos(a), rr * math.sin(a), (2.0 - rr) * 0.6), (0.14, 0.12, 0.1), 30 + k, 0), STONE_L)
    return b.finish()


def ore_pile():
    b = Build("Mining_OrePile")
    b.add(pile_geo((0, 0, 0), 1.3, 0.8, 3, 0.18), "4A3A30")
    rng = random.Random(7)
    for k in range(14):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.2, 1.1)
        z = 0.8 * math.sqrt(max(0.0, 1 - (rr / 1.3) ** 2)) - 0.03
        b.add(rock_geo((rr * math.cos(a), rr * math.sin(a), z), (0.06, 0.05, 0.04), 50 + k, 0, 0.3, 0.0), GOLD)
    return b.finish()


def fuel_skid():
    b = Build("Mining_FuelTank")
    b.add(box((0, 0, 0.1), (3.2, 1.6, 0.2)), DARK)
    for sx in (-1, 1):
        b.add(box((sx * 1.58, 0, 0.3), (0.04, 1.6, 0.2)), DARK)
        b.add(box((sx * 1.0, 0, 0.35), (0.25, 1.3, 0.3)), DARK)
    b.add(xf(cyl((0, 0, -1.4), 0.65, 0.65, 2.8, 12, rot=math.pi / 12), loc=(0, 0, 1.1), rot=(0, 90, 0)), "C8302C")
    for sx in (-1, 1):
        b.add(xf(cyl((0, 0, -0.05), 0.55, 0.55, 0.1, 12, rot=math.pi / 12), loc=(sx * 1.43, 0, 1.1), rot=(0, 90, 0)), "C8302C")
    b.add(text(SIGNS["diesel"], 0.3, (0, -0.64, 1.1), 0.02), WHITE)
    b.add(box((0, 0, 1.78), (0.3, 0.3, 0.1)), DARK)
    b.add(cyl((0.6, 0, 1.7), 0.05, 0.05, 0.35, 6), IRON)
    b.add(box((1.25, -0.6, 0.75), (0.45, 0.3, 0.9)), WHITE)  # Zapfsaeule
    b.add(box((1.25, -0.76, 0.95), (0.3, 0.02, 0.2)), DARK)
    b.add(box((1.5, -0.62, 0.8), (0.08, 0.14, 0.25)), DARK)
    b.add(beam((1.52, -0.7, 0.7), (1.7, -0.9, 0.25), 0.04), DARK)
    b.add(box((-1.2, -0.72, 0.9), (0.4, 0.02, 0.35)), "F28C28")
    return b.finish()


def light_tower():
    b = Build("Mining_LightTower")
    b.add(box((0, 0, 0.6), (1.3, 2.2, 0.9)), YELLOW)
    b.add(box((0, 0, 1.07), (1.35, 2.25, 0.05)), YELLOW)
    b.add(box((0, -1.11, 0.6), (0.8, 0.02, 0.5)), DARK)
    for sx in (-1, 1):
        wheel_static(b, sx * 0.8, 0.2, 0.3, 0.2)
        b.add(box((sx * 0.8, 0.2, 0.65), (0.25, 0.7, 0.05)), DARK)
        b.add(beam((sx * 0.6, -0.9, 0.3), (sx * 1.4, -1.3, 0.1), 0.08), DARK)
        b.add(box((sx * 1.4, -1.3, 0.05), (0.2, 0.2, 0.1)), DARK)
    b.add(beam((0, -1.1, 0.35), (0, -2.2, 0.35), 0.1), DARK)
    b.add(box((0, -2.25, 0.3), (0.15, 0.15, 0.1)), IRON)
    b.add(box((0, 0.9, 0.15), (0.08, 0.08, 0.3)), DARK)
    b.add(box((0, 0.7, 3.5), (0.18, 0.18, 5.0)), METAL)
    b.add(box((0, 0.7, 5.9), (0.12, 0.12, 0.8)), METAL)
    b.add(box((0, 0.7, 6.3), (1.6, 0.12, 0.1)), DARK)
    for x in (-0.6, -0.2, 0.2, 0.6):
        b.add(box((x, 0.6, 6.5), (0.34, 0.2, 0.3)), DARK)
        b.add(box((x, 0.49, 6.5), (0.28, 0.02, 0.24)), bb.LAMP)
    return b.finish()


def panning_station():
    b = Build("Mining_PanningStation")
    b.add(box((0, 0, 0.72), (2.0, 0.8, 0.1)), WOOD_D)
    for sx in (-1, 1):
        b.add(box((sx * 0.93, 0, 0.45), (0.08, 0.7, 0.05)), WOOD_D)
        for sy in (-1, 1):
            b.add(box((sx * 0.9, sy * 0.33, 0.35), (0.08, 0.08, 0.7)), WOOD_DD)
    b.add(box((0, 0, 0.95), (1.8, 0.62, 0.36)), WOOD)
    b.add(box((0, 0, 1.1), (1.7, 0.52, 0.04)), WATER)
    for x in (-0.4, 0.45):
        b.add(cyl((x, -0.05, 1.08), 0.14, 0.24, 0.07, 10), IRON)
        b.add(cyl((x, -0.05, 1.085), 0.05, 0.05, 0.01, 8), GOLD)
    b.add(beam((-1.3, 0.6, 1.8), (-0.85, 0.1, 1.2), 0.07), BLUE)  # Wasserzulauf
    b.add(box((-1.35, 0.65, 0.9), (0.08, 0.08, 1.8)), WOOD_DD)
    b.add(box((1.25, -0.3, 0.2), (0.35, 0.35, 0.4), (0.9, 0.9)), "D9822B")
    b.add(cyl((1.25, 0.35, 0), 0.18, 0.2, 0.35, 8), DARK)
    return b.finish()


# ================================================================= MINE
def mine_entrance():
    b = Build("Mining_MineEntrance")
    b.add(rock_geo((0, 2.6, 0), (5.5, 3.2, 3.6), 11, 2, 0.12, 0.05), ROCK)
    for sx in (-1, 1):
        b.add(rock_geo((sx * 3.8, 0.8, 0), (1.6, 1.5, 1.4), 12 + sx, 1), ROCK_D)
    b.add(box((0, 0.6, 1.5), (2.8, 2.4, 3.0)), "141210")  # Stollen
    for sx in (-1, 1):
        log(b, (sx * 1.45, -0.55, 0), (sx * 1.45, -0.55, 3.2), 0.18)
        log(b, (sx * 1.45, 0.4, 0), (sx * 1.45, 0.4, 3.2), 0.16)
    log(b, (-1.9, -0.55, 3.25), (1.9, -0.55, 3.25), 0.2)
    log(b, (-1.7, 0.4, 3.2), (1.7, 0.4, 3.2), 0.17)
    for k in range(6):
        b.add(box((-1.1 + k * 0.44, -0.1, 3.45), (0.2, 1.3, 0.12)), WOOD_D)
    b.add(box((0, -0.8, 3.75), (2.0, 0.08, 0.5)), WOOD_L)
    b.add(text("MINE", 0.36, (0, -0.85, 3.75), 0.03), "3A2A1A")
    b.add(box((1.25, -0.8, 2.4), (0.25, 0.25, 0.3)), bb.LAMP)
    b.add(pyramid((1.25, -0.8, 2.55), 0.2, 0.15), IRON)
    b.add(box((-2.3, -0.9, 0.5), (0.6, 0.02, 0.4)), "F2C12E")  # Warnschild
    b.add(box((-2.3, -0.9, 0.25), (0.06, 0.06, 0.5)), WOOD_DD)
    # Gleis aus dem Stollen
    rail_segment(b, 0, -1.6, 4.4, sleepers=8)
    return b.finish()


def rail_segment(b, x, y, L, sleepers=None, gauge=0.6):
    n = sleepers or int(L / 0.5)
    for k in range(n):
        b.add(box((x, y - L / 2 + (k + 0.5) * L / n, 0.05), (1.0, 0.18, 0.1)), WOOD_D)
    for sx in (-1, 1):
        b.add(box((x + sx * gauge / 2, y, 0.14), (0.05, L, 0.08)), METAL)
        b.add(box((x + sx * gauge / 2, y, 0.11), (0.1, L, 0.02)), IRON)


def rail_straight():
    b = Build("Mining_RailStraight")
    rail_segment(b, 0, 0, 4.0)
    return b.finish()


def rail_bumper():
    b = Build("Mining_RailBumper")
    rail_segment(b, 0, 0, 2.0)
    for sx in (-0.3, 0.3):
        b.add(box((sx, 0.8, 0.45), (0.12, 0.12, 0.7)), WOOD_DD)
        b.add(beam((sx, 0.85, 0.75), (sx, 0.35, 0.1), 0.1), WOOD_DD)
    b.add(box((0, 0.72, 0.62), (1.0, 0.18, 0.22)), RED)
    b.add(box((0, 0.62, 0.62), (0.8, 0.02, 0.1)), WHITE)
    return b.finish()


def minecart():
    b = Build("Mining_Minecart")
    b.add(box((0, 0, 0.3), (0.7, 1.0, 0.14)), DARK)
    b.add(box((0, 0, 0.75), (0.85, 1.2, 0.7), (1.15, 1.12)), "8A5A3A")
    for z in (0.45, 1.05):
        b.add(box((0, 0, z), (0.87 if z < 1 else 0.98, 1.22 if z < 1 else 1.35, 0.06)), IRON)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * 0.46, sy * 0.55, 0.75), (0.04, 0.06, 0.6)), IRON)
    b.add(pile_geo((0, 0, 1.08), 0.5, 0.25, 8, 0.2), "4A3A30")
    for k in range(5):
        a = k * 1.3
        b.add(rock_geo((0.25 * math.cos(a), 0.3 * math.sin(a), 1.2), (0.05, 0.04, 0.04), 60 + k, 0, 0.3, 0.0), GOLD)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(xf(cyl((0, 0, -0.05), 0.17, 0.17, 0.1, 10), loc=(sx * 0.3, sy * 0.35, 0.19), rot=(0, 90, 0)), IRON)
    for sy in (-1, 1):
        b.add(box((0, sy * 0.7, 0.3), (0.12, 0.2, 0.08)), DARK)
    return b.finish()


def tnt_crate():
    b = Build("Mining_TNTCrate")
    b.crate(0, 0, 0, 0.6)
    b.add(box((0, -0.31, 0.3), (0.42, 0.02, 0.2)), RED)
    b.add(text("TNT", 0.15, (0, -0.325, 0.3), 0.02), WHITE)
    for k in range(4):
        b.add(xf(cyl((0, 0, -0.18), 0.04, 0.04, 0.36, 6), loc=(-0.12 + k * 0.08, -0.05, 0.64), rot=(90, 0, 0)), RED)
    b.add(beam((0.12, 0.13, 0.66), (0.35, 0.35, 0.8), 0.015), "E8DDC4")
    return b.finish()


def gold_bars():
    b = Build("Mining_GoldBars")
    rows = [(4, 0.0), (3, 0.09), (2, 0.18), (1, 0.27)]
    for n, z in rows:
        for i in range(n):
            x = (i - (n - 1) / 2) * 0.13
            for j in range(2):
                b.add(box((x, j * 0.26 - 0.13, z + 0.045), (0.12, 0.25, 0.09), (0.75, 0.9)), GOLD)
    return b.finish()


def safe():
    b = Build("Mining_Safe")
    b.add(box((0, 0, 0.1), (0.95, 0.85, 0.2)), DARK)
    b.add(box((0, 0, 0.72), (0.9, 0.8, 1.1)), "2F4A3A")
    b.add(box((0, -0.41, 0.72), (0.74, 0.03, 0.94)), "3E5F4A")
    b.add(box((0, -0.43, 0.72), (0.66, 0.02, 0.86)), GOLD)
    b.add(box((0, -0.44, 0.72), (0.62, 0.02, 0.82)), "3E5F4A")
    b.add(xf(cyl((0, 0, 0), 0.1, 0.1, 0.04, 12), loc=(0, -0.46, 0.85), rot=(90, 0, 0)), METAL)
    b.add(box((0, -0.5, 0.85), (0.02, 0.01, 0.07)), DARK)
    b.add(box((0.18, -0.48, 0.6), (0.2, 0.04, 0.04)), METAL)
    b.add(box((0.28, -0.44, 0.52), (0.08, 0.04, 0.2)), METAL)
    for sx in (-1, 1):
        b.add(box((sx * 0.3, -0.44, 1.02), (0.05, 0.03, 0.08)), GOLD)
    return b.finish()


def feed_hopper():
    b = Build("Mining_FeedHopper")
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * 1.1, sy * 1.1, 1.1), (0.15, 0.15, 2.2)), DARK)
        b.add(beam((sx * 1.1, -1.1, 0.3), (sx * 1.1, 1.1, 1.9), 0.08), DARK)
    b.add(box((0, 0, 2.7), (2.6, 2.6, 1.2), (1.0, 1.0)), "C8302C")
    b.add(box((0, 0, 1.66), (0.9, 0.9, 0.92), (2.89, 2.89)), "C8302C")
    b.add(box((0, 0, 1.2), (0.9, 0.9, 0.3)), DARK)
    for k in range(9):
        b.add(box((-1.2 + k * 0.3, 0, 3.35), (0.08, 2.7, 0.1)), IRON)
    b.add(box((0, 0, 3.32), (2.7, 0.1, 0.08)), IRON)
    b.add(box((0, -1.9, 0.9), (0.9, 2.4, 0.08)), DARK)  # Auslauf
    b.add(xf(box((0, 0, 0), (0.8, 1.2, 0.35)), loc=(0, -1.0, 1.05), rot=(12, 0, 0)), "C8302C")
    for k in range(4):
        b.add(rock_geo((-0.8 + k * 0.5, 0.2 * (k % 2), 3.45), (0.2, 0.18, 0.14), 80 + k, 0), DIRT)
    return b.finish()


def platform_scale():
    b = Build("Mining_Scale")
    b.add(box((0, 0, 0.06), (1.2, 1.2, 0.12)), METAL)
    b.add(box((0, 0, 0.125), (1.1, 1.1, 0.01)), IRON)
    b.add(box((0, 0.62, 0.6), (0.08, 0.08, 1.2)), DARK)
    b.add(box((0, 0.62, 1.3), (0.4, 0.12, 0.3)), YELLOW)
    b.add(box((0, 0.55, 1.3), (0.3, 0.02, 0.12)), "1E3A1E")
    b.add(box((-0.05, 0.54, 1.3), (0.16, 0.01, 0.06)), "7CFC6A")
    b.add(box((0.1, 0.0, 0.25), (0.28, 0.2, 0.22), (0.7, 0.7)), GOLD)
    return b.finish()


# ================================================================ CAMP
def container(name, col, office=False):
    b = Build(name)
    L, W, H = 6.06, 2.44, 2.6
    b.add(box((0, 0, H / 2), (L, W, H)), col)
    rib = {"E8E8E8": "CFCFCF", "B83A32": "96302A"}.get(col, "4A4A4A")
    for k in range(20):
        x = -L / 2 + 0.2 + k * (L - 0.4) / 19
        for sy in (-1, 1):
            b.add(box((x, sy * (W / 2 + 0.02), H / 2), (0.1, 0.04, H - 0.3)), rib)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (0.1, H - 0.1):
                b.add(box((sx * (L / 2 - 0.08), sy * (W / 2 - 0.08), z), (0.2, 0.2, 0.2)), DARK)
    for sy in (-1, 1):
        b.add(box((0, sy * (W / 2 - 0.02), H - 0.08), (L, 0.08, 0.16)), rib)
        b.add(box((0, sy * (W / 2 - 0.02), 0.08), (L, 0.08, 0.16)), rib)
    if office:
        b.add(box((-1.2, -W / 2 - 0.05, 1.05), (0.95, 0.1, 2.1)), "4A4A4A")
        b.add(box((-1.2, -W / 2 - 0.11, 1.5), (0.5, 0.02, 0.45)), GLASS)
        b.add(box((-0.85, -W / 2 - 0.13, 1.0), (0.1, 0.04, 0.04)), METAL)
        for x in (0.6, 2.0):
            b.add(box((x, -W / 2 - 0.05, 1.5), (1.1, 0.1, 0.9)), WHITE)
            b.add(box((x, -W / 2 - 0.1, 1.5), (0.95, 0.04, 0.75)), GLASS)
            for k in range(5):
                b.add(box((x - 0.4 + k * 0.2, -W / 2 - 0.14, 1.5), (0.03, 0.03, 0.8)), IRON)
        b.add(box((2.2, -W / 2 - 0.25, 2.25), (0.7, 0.4, 0.5)), "D8D8D8")  # Klimageraet
        b.add(box((2.2, -W / 2 - 0.46, 2.25), (0.5, 0.02, 0.35)), "4A4A4A")
        for k in range(3):  # Treppe
            b.add(box((-1.2, -W / 2 - 0.45 - k * 0.28, 0.6 - k * 0.2), (1.1, 0.28, 0.05)), METAL)
        for sx in (-1, 1):
            b.add(beam((-1.2 + sx * 0.55, -W / 2 - 0.3, 0.65), (-1.2 + sx * 0.55, -W / 2 - 1.1, 0.05), 0.05), METAL)
            b.add(box((-1.2 + sx * 0.6, -W / 2 - 0.7, 1.2), (0.04, 0.04, 1.0)), METAL)
        b.add(box((-1.2, -W / 2 - 0.12, 2.35), (1.2, 0.04, 0.3)), BLUE)
        b.add(text(SIGNS["office"], 0.18, (-1.2, -W / 2 - 0.15, 2.35), 0.02), WHITE)
    else:
        b.add(box((L / 2 + 0.03, 0, H / 2), (0.06, W - 0.2, H - 0.3)), col)
        b.add(box((L / 2 + 0.065, 0, H / 2), (0.01, 0.03, H - 0.35)), DARK)
        for y in (-0.8, -0.35, 0.35, 0.8):
            b.add(box((L / 2 + 0.09, y, H / 2), (0.04, 0.05, H - 0.4)), METAL)
            b.add(box((L / 2 + 0.12, y, 1.1), (0.06, 0.1, 0.12)), DARK)
    return b.finish()


def wall_tent():
    b = Build("Camp_Tent")
    W, D, H = 3.0, 4.0, 1.3
    b.add(box((0, 0, H / 2), (W, D, H)), CANVAS)
    b.add(tri_y(0, 0, H, W, D, 1.1), CANVAS)
    b.gable_roof_y(0, 0, H, W, D, 1.1, over=0.15, t=0.04, col=CANVAS_D)
    b.add(box((0, -D / 2 - 0.01, 0.95), (0.9, 0.02, 1.9)), "3A3226")
    for sx in (-1, 1):
        b.add(cyl((sx * 0.5, -D / 2 - 0.08, 0), 0.08, 0.08, 1.9, 6), CANVAS_D)
    for sx in (-1, 1):
        for y in (-1.4, 0.0, 1.4):
            b.add(beam((sx * (W / 2 + 0.2), y, H + 0.05), (sx * (W / 2 + 1.1), y, 0.0), 0.015), "8A7A5A")
            b.add(box((sx * (W / 2 + 1.12), y, 0.08), (0.04, 0.04, 0.16)), WOOD_DD)
    for y in (-D / 2 - 0.05, D / 2 + 0.05):
        b.add(box((0, y, (H + 1.1) / 2 + 0.05), (0.07, 0.07, H + 1.2)), WOOD_D)
    b.add(cyl((0.8, 1.2, H + 0.35), 0.08, 0.08, 1.1, 8), IRON)
    b.add(cyl((0.8, 1.2, H + 1.45), 0.13, 0.13, 0.08, 8), IRON)
    return b.finish()


def toilet():
    b = Build("Camp_Toilet")
    b.add(box((0, 0, 0.05), (1.2, 1.2, 0.1)), DARK)
    b.add(box((0, 0, 1.15), (1.1, 1.1, 2.1)), BLUE)
    b.add(box((0, 0, 2.25), (1.15, 1.15, 0.1)), WHITE)
    b.add(pyramid((0, 0, 2.3), 0.8, 0.15), WHITE)
    b.add(box((0, -0.56, 1.1), (0.8, 0.04, 1.9)), "3A6E9E")
    for k in range(4):
        b.add(box((0, -0.59, 1.7 + k * 0.06), (0.4, 0.02, 0.025)), DARK)
    b.add(box((0.3, -0.6, 1.1), (0.05, 0.04, 0.2)), DARK)
    b.add(box((0.3, -0.6, 1.25), (0.08, 0.02, 0.06)), "4E7A3A")
    b.add(cyl((0.35, 0.3, 2.3), 0.05, 0.05, 0.3, 6), WHITE)
    return b.finish()


def campfire():
    b = Build("Camp_Campfire")
    for k in range(9):
        a = 2 * math.pi * k / 9
        b.add(rock_geo((0.6 * math.cos(a), 0.6 * math.sin(a), 0), (0.16, 0.13, 0.12), 70 + k, 0), ROCK)
    b.add(cyl((0, 0, 0), 0.45, 0.45, 0.02, 8), "2A2420")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        log(b, (0.45 * math.cos(a), 0.45 * math.sin(a), 0.05), (0.05 * math.cos(a), 0.05 * math.sin(a), 0.35), 0.06, 6)
    b.add(pyramid((0, 0, 0.05), 0.28, 0.7, 5, 0.3), FLAME)
    b.add(pyramid((0.08, 0.05, 0.05), 0.16, 0.5, 5, 0.9), FLAME_L)
    b.add(pyramid((-0.1, -0.06, 0.05), 0.14, 0.4, 5, 0.1), FLAME_L)
    # Sitz-Staemme
    log(b, (-1.6, -0.6, 0.18), (-1.4, 0.8, 0.18), 0.18)
    log(b, (1.3, -1.2, 0.18), (0.4, -1.7, 0.18), 0.18)
    return b.finish()


def woodpile():
    b = Build("Camp_Woodpile")
    r = 0.13
    for row, n in enumerate((5, 4, 3, 2)):
        for i in range(n):
            x = (i - (n - 1) / 2) * 2 * r
            z = r + row * r * 1.75
            log(b, (x, -0.5, z), (x, 0.5, z), r, 7)
    for sx in (-1, 1):
        b.add(box((sx * 0.78, 0, 0.5), (0.08, 0.08, 1.0)), WOOD_DD)
    log(b, (0.5, -0.9, 0.35), (0.6, -1.0, 0.0), 0.15, 8)  # Hackklotz
    b.add(cyl((0.9, -1.0, 0), 0.22, 0.22, 0.45, 8), BARK)
    b.add(cyl((0.9, -1.0, 0.44), 0.19, 0.19, 0.02, 8), WOODCUT)
    b.add(xf(box((0, 0, 0), (0.03, 0.03, 0.6)), loc=(0.95, -1.0, 0.7), rot=(0, 35, 0)), WOOD_L)
    b.add(box((0.8, -1.0, 0.52), (0.14, 0.03, 0.1)), METAL)
    return b.finish()


def workbench():
    b = Build("Camp_Workbench")
    b.add(box((0, 0, 0.9), (2.0, 0.8, 0.08)), WOOD_D)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * 0.92, sy * 0.33, 0.45), (0.08, 0.08, 0.9)), WOOD_DD)
        b.add(box((sx * 0.92, 0, 0.2), (0.06, 0.7, 0.05)), WOOD_DD)
    b.add(box((0, 0, 0.25), (1.9, 0.7, 0.04)), WOOD_D)
    b.add(box((0, 0.36, 1.45), (2.0, 0.06, 1.0)), WOOD_L)  # Werkzeugwand
    for sx in (-1, 1):
        b.add(box((sx * 0.96, 0.36, 1.2), (0.08, 0.08, 1.55)), WOOD_DD)
    b.add(box((-0.6, 0.32, 1.5), (0.04, 0.02, 0.5)), WOOD)  # Hammer
    b.add(box((-0.6, 0.31, 1.75), (0.16, 0.04, 0.06)), IRON)
    b.add(box((-0.3, 0.32, 1.45), (0.05, 0.02, 0.4)), METAL)  # Schluessel
    b.add(box((0.0, 0.32, 1.45), (0.25, 0.02, 0.06)), RED)  # Saege
    b.add(box((0.0, 0.32, 1.35), (0.4, 0.01, 0.12)), METAL)
    b.add(box((0.5, 0.32, 1.6), (0.03, 0.02, 0.55)), WOOD)  # Schaufel
    b.add(box((0.5, 0.32, 1.25), (0.18, 0.02, 0.2)), METAL)
    b.add(box((0.8, 0, 1.02), (0.2, 0.16, 0.16)), BLUE)  # Schraubstock
    b.add(box((0.8, -0.1, 1.05), (0.24, 0.05, 0.08)), BLUE)
    b.add(box((-0.3, -0.05, 1.0), (0.5, 0.25, 0.12)), RED)  # Werkzeugkiste
    b.add(box((0.3, 0.05, 0.98), (0.3, 0.2, 0.08)), GOLD)
    b.lantern(-0.8, -0.1, 1.08, arm=0.05)
    return b.finish()


def sign_danger():
    b = Build("Camp_SignDanger")
    for sx in (-0.55, 0.55):
        b.add(box((sx, 0, 0.9), (0.08, 0.08, 1.8)), WOOD_DD)
    b.add(box((0, -0.05, 1.35), (1.4, 0.04, 0.8)), WHITE)
    b.add(box((0, -0.075, 1.6), (1.36, 0.02, 0.28)), RED)
    b.add(text(SIGNS["danger"], 0.2, (0, -0.09, 1.6), 0.02), WHITE)
    b.add(text(SIGNS["keep_out"], 0.16, (0, -0.08, 1.2), 0.02), DARK)
    return b.finish()


def claim_gate():
    b = Build("Camp_ClaimGate")
    for sx in (-1, 1):
        log(b, (sx * 3.2, 0, 0), (sx * 3.2, 0, 4.4), 0.2)
        b.add(rock_geo((sx * 3.2, 0, 0), (0.45, 0.4, 0.25), 90 + sx, 1), ROCK)
        log(b, (sx * 3.2, 0.4, 0), (sx * 3.2, 1.6, 1.3), 0.08, 6)  # Strebe
    log(b, (-3.8, 0, 4.2), (3.8, 0, 4.2), 0.2)
    b.add(box((0, -0.15, 3.3), (3.4, 0.1, 0.8)), WOOD_L)
    b.add(box((0, -0.2, 3.3), (3.2, 0.02, 0.62)), WOOD_D)
    b.add(text(SIGNS["claim"], 0.45, (0, -0.23, 3.3), 0.04), GOLD)
    for sx in (-1, 1):
        b.add(box((sx * 1.4, -0.15, 3.9), (0.03, 0.03, 0.6)), IRON)
    # Torfluegel (Rahmen offen)
    for sx in (-1, 1):
        x0 = sx * 3.0
        for z in (0.4, 1.2):
            b.add(beam((x0, -0.1, z), (x0 - sx * 0.5, -2.6, z), 0.1), WOOD_D)
        b.add(box((x0 - sx * 0.5, -2.6, 0.75), (0.1, 0.1, 1.2)), WOOD_D)
        b.add(beam((x0, -0.1, 0.4), (x0 - sx * 0.5, -2.6, 1.2), 0.08), WOOD_D)
    b.add(pyramid((-3.2, 0, 4.4), 0.15, 0.2, 6), IRON)
    b.add(pyramid((3.2, 0, 4.4), 0.15, 0.2, 6), IRON)
    b.lantern(2.95, -0.25, 3.3)
    return b.finish()


def sack_pallet():
    b = Build("Camp_SackPallet")
    b.add(box((0, 0, 0.07), (1.2, 1.0, 0.04)), WOOD_L)
    for x in (-0.5, 0, 0.5):
        b.add(box((x, 0, 0.03), (0.12, 1.0, 0.06)), WOOD_D)
    for k in range(7):
        b.add(box((-0.55 + k * 0.18, 0, 0.12), (0.12, 1.0, 0.02)), WOOD_L)
    pos = [(-0.3, -0.25, 0.23), (0.3, -0.25, 0.23), (-0.3, 0.25, 0.23), (0.3, 0.25, 0.23),
           (0.0, -0.25, 0.47), (0.0, 0.25, 0.47)]
    for i, (x, y, z) in enumerate(pos):
        b.add(xf(box((0, 0, 0), (0.55, 0.45, 0.22), (0.85, 0.85)), loc=(x, y, z), rot=(0, 0, (i * 13) % 10 - 5)),
              "CDB88A" if i % 2 else "BFA676")
    return b.finish()


# ================================================================ NATUR
def rocks():
    out = []
    specs = [("Nature_Rock_Small", (0.35, 0.3, 0.25), 1),
             ("Nature_Rock_Medium", (0.8, 0.65, 0.5), 2),
             ("Nature_Rock_Large", (1.6, 1.2, 1.1), 3)]
    for name, s, seed in specs:
        b = Build(name)
        b.add(rock_geo((0, 0, 0), s, seed, 1), ROCK)
        if seed > 1:
            b.add(rock_geo((s[0] * 0.8, -s[1] * 0.5, 0), (s[0] * 0.35, s[1] * 0.35, s[2] * 0.35), seed + 10, 0), ROCK_D)
        out.append(b.finish())
    b = Build("Nature_RockCluster")
    for k, (x, y, sc) in enumerate(((0, 0, 1.0), (1.3, 0.4, 0.6), (-1.1, 0.6, 0.7), (0.4, -1.0, 0.45), (-0.5, -0.9, 0.3))):
        b.add(rock_geo((x, y, 0), (0.9 * sc, 0.8 * sc, 0.7 * sc), 20 + k, 1), ROCK if k % 2 == 0 else ROCK_D)
    b.add(rock_geo((0.2, 0.3, 0.55), (0.3, 0.25, 0.08), 99, 1, 0.1, 0.0), "5E8C44")  # Moos
    out.append(b.finish())
    return out


def stump():
    b = Build("Nature_Stump")
    b.add(cyl((0, 0, 0), 0.42, 0.36, 0.55, 8), BARK)
    b.add(cyl((0, 0, 0.54), 0.33, 0.33, 0.03, 8), WOODCUT)
    b.add(cyl((0, 0, 0.56), 0.12, 0.12, 0.01, 8), "C49A6C")
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        b.add(beam((0.3 * math.cos(a), 0.3 * math.sin(a), 0.2), (0.75 * math.cos(a), 0.75 * math.sin(a), 0.0), 0.12), BARK)
    b.add(xf(box((0, 0, 0), (0.03, 0.03, 0.7)), loc=(0.1, 0.05, 0.85), rot=(15, 0, 0)), WOOD_L)  # Axt
    b.add(xf(box((0, 0, 0.3), (0.18, 0.04, 0.12)), loc=(0.1, 0.05, 0.85), rot=(15, 0, 0)), METAL)
    return b.finish()


def fallen_log():
    b = Build("Nature_FallenLog")
    log(b, (-2.5, 0, 0.3), (2.5, 0.3, 0.28), 0.3, 9)
    for x, a in ((-1.2, 40), (0.6, -30), (1.8, 60)):
        b.add(xf(beam((0, 0, 0), (0, 0.6, 0.35), 0.08), loc=(x, 0.1, 0.35), rot=(0, 0, a)), BARK)
    b.add(rock_geo((0.3, -0.2, 0.52), (0.35, 0.18, 0.07), 5, 1, 0.1, 0.0), "5E8C44")
    for k in range(3):
        b.add(cyl((-0.8 + k * 0.25, -0.35, 0), 0.03, 0.03, 0.12, 6), "EFE6D2")
        b.add(cyl((-0.8 + k * 0.25, -0.35, 0.12), 0.08, 0.02, 0.06, 6), "B83A32")  # Pilze
    return b.finish()


def bridge():
    b = Build("Nature_Bridge")
    L, W = 8.0, 3.2
    for sx in (-1, 1):
        b.add(box((sx * (W / 2 - 0.2), 0, 0.5), (0.3, L + 0.6, 0.35)), WOOD_DD)
    n = 26
    for k in range(n):
        y = -L / 2 + (k + 0.5) * L / n
        b.add(box((0, y, 0.72), (W, L / n - 0.04, 0.08)), WOOD_D if k % 3 else WOOD)
    for sx in (-1, 1):
        for k in range(5):
            y = -L / 2 + k * L / 4
            b.add(box((sx * W / 2, y, 1.15), (0.14, 0.14, 1.0)), WOOD_DD)
            b.add(box((sx * W / 2, y, 0.3), (0.2, 0.2, 0.9)), WOOD_DD)
        b.add(box((sx * W / 2, 0, 1.6), (0.1, L, 0.1)), WOOD_L)
        b.add(box((sx * W / 2, 0, 1.1), (0.06, L, 0.08)), WOOD_L)
        for k in range(4):
            y0 = -L / 2 + k * L / 4
            b.add(beam((sx * W / 2, y0 + 0.1, 0.8), (sx * W / 2, y0 + L / 4 - 0.1, 1.55), 0.06), WOOD_D)
    for sy in (-1, 1):
        b.add(rock_geo((0, sy * (L / 2 + 0.2), 0), (W / 2 + 0.3, 0.6, 0.35), 40 + sy, 1), ROCK)
    return b.finish()


# ==================================================================== MAIN
def main():
    groups = {
        "mining": [sluice_box(), generator(), water_pump(), water_tank(), conveyor(), fuel_skid(),
                   light_tower(), panning_station(), dirt_pile(), gravel_pile(), ore_pile()],
        "camp": [container("Camp_ContainerOffice", "E8E8E8", True), container("Camp_ContainerStorage", "B83A32"),
                 wall_tent(), toilet(), campfire(), woodpile(), workbench(), sign_danger(), claim_gate(), sack_pallet()],
        "nature": rocks() + [stump(), fallen_log(), bridge()],
        "mine": [mine_entrance(), rail_straight(), rail_bumper(), minecart(), tnt_crate(), gold_bars(), safe(),
                 feed_hopper(), platform_scale()],
    }
    for objs in groups.values():
        for ob in objs:
            bb.export_mesh(ob)
    cam, target = bb.setup_preview()
    layout = {
        "mining": (-8, [(-4, 0), (0, 0), (2.5, 0), (4.5, 0), (8, 0.5), (-4, 6), (0.5, 6), (4, 6), (-9, 12), (-3.5, 12), (1, 12)]),
        "camp": (-40, [(-6, 0), (1, 0), (7, 0), (11, -1), (-6, 7), (-2, 7), (1.5, 7), (4.5, 7), (0, 14), (7, 7)]),
        "nature": (30, [(-4, 0), (-2.5, 0), (0.5, 0), (5, 0), (-4, 5), (0, 5), (4, 7)]),
        "mine": (60, [(0, 4), (-5, -4), (-5, -7.5), (-5, -1.2), (-2.5, -4), (-1.5, -5), (-0.2, -4.2), (5, -2), (2.2, -4.8)]),
    }
    for key, objs in groups.items():
        ox, pts = layout[key]
        for ob, (x, y) in zip(objs, pts):
            ob.location = (ox + x, y, 0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "props.blend"))
    shots = [("preview_Mining", (-2, -15, 9), (-8, 5, 0.8), 30),
             ("preview_Camp", (-34, -16, 9), (-39, 6, 1.0), 30),
             ("preview_Nature", (36, -12, 7), (30, 3.5, 0.5), 32),
             ("preview_Mine", (66, -14, 6), (59.5, 0, 1.2), 30)]
    bb.render_shots(shots, cam, target)
    print("DONE")


if __name__ == "__main__":
    main()
