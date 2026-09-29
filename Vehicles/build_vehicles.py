"""Low-Poly Trucks fuer den Goldgraeber-Simulator.

Ausfuehren:  blender -b -P build_vehicles.py   (oder: python3 build_vehicles.py mit pip-Paket bpy)
Nutzt die Bauteile aus ../Buildings/build_buildings.py.

Jedes Fahrzeug = Karosserie-Mesh + Raeder als eigene Kind-Objekte (Ursprung = Radmitte,
Drehachse = lokale X-Achse). Front zeigt in Blender nach -Y (Unity +Z).
Sattelzug: Empty "Hitch" am Sattelzugmaschinen-Heck; der Auflieger hat seinen Ursprung
am Koenigszapfen (Bodenhoehe), also Auflieger-Position = Hitch-Position mit y/z wie im Skript.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "Buildings"))
import bpy  # noqa: E402

import build_buildings as bb  # noqa: E402
from build_buildings import Build, box, cyl, xf, text, GLASS, IRON, METAL, RED, WHITE, WOOD_D  # noqa: E402

bb.OUT = HERE

TIRE = "2A2A2A"
DARK = "1E1E1E"
CHROME = "C8CCD0"
HEAD = "FFF6C0"
AMBER = "F28C28"
YELLOW = "F2C12E"
ORANGE = "E07B24"


def wheel_parts(r, w, rim, lugs=12):
    g = [(xf(cyl((0, 0, -w / 2), r, r, w, 12, rot=math.pi / 12), rot=(0, 90, 0)), TIRE),
         (xf(cyl((0, 0, -w / 2 - 0.01), r * 0.58, r * 0.58, w + 0.02, 8), rot=(0, 90, 0)), rim),
         (xf(cyl((0, 0, -w / 2 - 0.03), r * 0.2, r * 0.2, w + 0.06, 6), rot=(0, 90, 0)), IRON)]
    for k in range(lugs):
        g.append((xf(box((0, 0, r), (w * 0.9, r * 0.22, 0.06)), rot=(360 * (k + 0.5) / lugs, 0, 0)), TIRE))
    return g


class Vehicle:
    def __init__(self, name):
        self.name = name
        self.b = Build(name)
        self.wheels = []
        self.empties = []

    def add(self, geo, col):
        self.b.add(geo, col)

    def axle(self, tag, y, r, w, track, rim):
        for side, sx in (("L", 1), ("R", -1)):
            self.wheels.append((f"{tag}{side}", sx * track / 2, y, r, w, rim))

    def empty(self, name, loc):
        self.empties.append((name, loc))

    def finish(self):
        body = self.b.finish()
        objs = [body]
        for tag, x, y, r, w, rim in self.wheels:
            wb = Build(f"{self.name}_Wheel_{tag}")
            for geo, c in wheel_parts(r, w, rim):
                wb.add(geo, c)
            ob = wb.finish()
            ob.location = (x, y, r)
            ob.parent = body
            objs.append(ob)
        for name, loc in self.empties:
            e = bpy.data.objects.new(f"{self.name}_{name}", None)
            e.empty_display_size = 0.4
            bpy.context.scene.collection.objects.link(e)
            e.location = loc
            e.parent = body
            objs.append(e)
        return objs


# ------------------------------------------------------------- Bauteile
def cabin(v, y0, y1, w, z0, zg, z1, col, taper=(0.95, 0.82)):
    """Fahrerhaus: Blech bis zg, Glas bis z1, Dach. y0 = Front."""
    yc, d = (y0 + y1) / 2, y1 - y0
    v.add(box((0, yc, (z0 + zg) / 2), (w, d, zg - z0)), col)
    v.add(box((0, yc, (zg + z1) / 2), (w * 0.97, d * 0.98, z1 - zg), taper), GLASS)
    v.add(box((0, yc, z1 + 0.05), (w * 0.97 * taper[0], d * 0.98 * taper[1], 0.1)), col)
    for sx in (-1, 1):  # B-Saeule + Tuerfuge + Griff
        xo = w / 2 * (0.97 + 0.97 * taper[0]) / 2
        v.add(box((sx * xo, yc + d * 0.1, (zg + z1) / 2), (0.08, 0.1, z1 - zg)), col)
        v.add(box((sx * (w / 2 + 0.005), yc + d * 0.12, (z0 + zg) / 2), (0.01, 0.03, zg - z0 - 0.1)), DARK)
        v.add(box((sx * (w / 2 + 0.02), yc, zg - 0.2), (0.03, 0.18, 0.05)), DARK)


def mirrors(v, y, z, xo):
    for sx in (-1, 1):
        v.add(box((sx * (xo - 0.12), y, z + 0.2), (0.24, 0.04, 0.04)), DARK)
        v.add(box((sx * xo, y, z), (0.07, 0.1, 0.42)), DARK)


def lights_front(v, y, z, xo, size=(0.3, 0.16)):
    for sx in (-1, 1):
        v.add(box((sx * xo, y, z), (size[0], 0.05, size[1])), HEAD)


def lights_rear(v, y, z, xo):
    for sx in (-1, 1):
        v.add(box((sx * xo, y, z), (0.25, 0.05, 0.14)), RED)
        v.add(box((sx * (xo - 0.2), y, z), (0.12, 0.05, 0.14)), AMBER)


def beacon(v, x, y, z):
    v.add(cyl((x, y, z), 0.1, 0.1, 0.04, 6), DARK)
    v.add(cyl((x, y, z + 0.04), 0.08, 0.06, 0.14, 6), AMBER)


# =============================================================== PICKUP
def pickup():
    v = Vehicle("Vehicle_Pickup")
    col, W = "B83A32", 1.95
    v.add(box((0, 0, 0.55), (1.5, 5.0, 0.2)), DARK)
    v.add(box((0, -1.85, 0.85), (W, 1.5, 0.6)), col)
    v.add(box((0, -1.8, 1.17), (W * 0.9, 1.3, 0.05)), col)
    cabin(v, -1.1, 0.4, W, 0.55, 1.35, 1.87, col)
    # Ladeflaeche
    v.add(box((0, 1.5, 0.72), (W, 2.2, 0.15)), col)
    for sx in (-1, 1):
        v.add(box((sx * (W / 2 - 0.05), 1.5, 1.05), (0.1, 2.2, 0.55)), col)
        v.add(box((sx * (W / 2 - 0.05), 1.5, 1.34), (0.14, 2.2, 0.04)), DARK)
    v.add(box((0, 0.45, 1.05), (W, 0.1, 0.55)), col)
    v.add(box((0, 2.55, 1.05), (W, 0.1, 0.55)), col)
    v.add(box((0, 2.61, 1.2), (0.4, 0.02, 0.06)), DARK)
    # Kotfluegel
    for y in (-1.6, 1.5):
        for sx in (-1, 1):
            v.add(box((sx * (W / 2 + 0.03), y, 0.84), (0.08, 0.95, 0.1)), DARK)
    # Front / Heck
    v.add(box((0, -2.61, 0.88), (1.1, 0.04, 0.34)), DARK)
    for z in (0.8, 0.95):
        v.add(box((0, -2.64, z), (1.1, 0.03, 0.04)), METAL)
    lights_front(v, -2.61, 0.96, 0.75)
    v.add(box((0, -2.67, 0.6), (W + 0.05, 0.16, 0.18)), METAL)
    v.add(box((0, -2.76, 0.6), (0.5, 0.02, 0.12)), WHITE)
    v.add(box((0, 2.67, 0.6), (W + 0.05, 0.16, 0.18)), METAL)
    v.add(box((0, 2.76, 0.6), (0.5, 0.02, 0.12)), WHITE)
    for sx in (-1, 1):
        v.add(box((sx * 0.88, 2.61, 1.1), (0.14, 0.04, 0.3)), RED)
    mirrors(v, -1.0, 1.45, 1.12)
    # Dach-Lichtleiste + Warnwimpel (Minen-Pickup)
    v.add(box((0, -0.75, 1.96), (1.2, 0.15, 0.08)), DARK)
    beacon(v, -0.45, -0.75, 2.0)
    beacon(v, 0.45, -0.75, 2.0)
    v.add(cyl((0.85, 2.45, 1.3), 0.02, 0.015, 2.4, 6), DARK)
    v.add(box((0.85 - 0.22, 2.45, 3.5), (0.44, 0.01, 0.28)), AMBER)
    # Ladung: Kanister, Werkzeugkiste, Schaufel
    for i, c in enumerate(("C8302C", "4E7A3A")):
        v.add(box((-0.55 + i * 0.3, 0.8, 1.05), (0.24, 0.45, 0.5)), c)
    v.add(box((0, 0.65, 1.2), (1.6, 0.35, 0.3)), METAL)
    v.add(box((0.4, 1.9, 0.83), (0.04, 1.2, 0.04)), bb.WOOD_L)
    v.add(box((0.4, 2.45, 0.83), (0.22, 0.26, 0.03)), METAL)
    v.axle("F", -1.6, 0.4, 0.3, 1.64, "C8C8C8")
    v.axle("R", 1.5, 0.4, 0.3, 1.64, "C8C8C8")
    return v.finish()


# ========================================================== TANKLASTER
def fuel_tanker():
    v = Vehicle("Vehicle_FuelTanker")
    col, W = WHITE, 2.5
    v.add(box((0, 0.3, 0.85), (1.0, 7.8, 0.3)), DARK)
    cabin(v, -4.3, -2.4, W, 0.7, 2.2, 2.9, col, (0.96, 0.85))
    v.add(box((0, -2.75, 3.25), (W * 0.9, 0.9, 0.5), (1.0, 0.4)), col)
    v.add(box((0, -3.35, 1.55), (W + 0.02, 1.92, 0.18)), RED)
    v.add(box((0, -4.31, 1.35), (1.6, 0.04, 0.7)), DARK)
    for k in range(4):
        v.add(box((0, -4.34, 1.1 + k * 0.17), (1.5, 0.03, 0.05)), METAL)
    lights_front(v, -4.31, 1.0, 1.0, (0.35, 0.2))
    v.add(box((0, -4.4, 0.8), (W + 0.05, 0.22, 0.3)), METAL)
    for sx in (-1, 1):
        v.add(box((sx * 1.2, -3.4, 0.62), (0.2, 0.5, 0.06)), METAL)
    mirrors(v, -4.1, 2.35, 1.5)
    beacon(v, -0.5, -3.3, 3.0)
    beacon(v, 0.5, -3.3, 3.0)
    v.add(cyl((1.05, -2.25, 1.0), 0.08, 0.08, 2.5, 8), CHROME)
    # Tank
    TY, TZ, R = 1.1, 2.1, 1.0
    v.add(xf(cyl((0, 0, -3.0), R, R, 6.0, 12, rot=math.pi / 12), loc=(0, TY, TZ), rot=(90, 0, 0)), CHROME)
    for dy in (-3.0, 3.0):
        v.add(xf(cyl((0, 0, -0.1), R * 0.85, R * 0.85, 0.2, 12, rot=math.pi / 12),
                 loc=(0, TY + dy + (0.1 if dy > 0 else -0.1), TZ), rot=(90, 0, 0)), CHROME)
    for dy in (-2.1, 0.0, 2.1):
        v.add(xf(cyl((0, 0, -0.05), R + 0.02, R + 0.02, 0.1, 12, rot=math.pi / 12),
                 loc=(0, TY + dy, TZ), rot=(90, 0, 0)), METAL)
    for sx in (-1, 1):
        v.add(box((sx * 0.975, TY, 1.9), (0.03, 5.9, 0.08)), RED)
        v.add(text("FUEL", 0.45, (sx * 0.985, TY - 1.05, 2.2), 0.02, facing=90 * sx), RED)
        v.add(text("FUEL", 0.45, (sx * 0.985, TY + 1.05, 2.2), 0.02, facing=90 * sx), RED)
    v.add(box((0, TY + 3.22, TZ), (0.5, 0.02, 0.36)), AMBER)
    v.add(text("1203", 0.14, (0, TY + 3.24, TZ), 0.01, facing=180), DARK)
    v.add(box((0, TY, TZ + R), (0.5, 5.6, 0.05)), METAL)
    for dy in (-1.8, 0.0, 1.8):
        v.add(cyl((0, TY + dy, TZ + R - 0.02), 0.28, 0.24, 0.14, 8), METAL)
    for sx in (-1, 1):
        for k in range(6):
            v.add(box((sx * 0.3, TY - 2.5 + k, TZ + R + 0.3), (0.04, 0.04, 0.6)), YELLOW)
        v.add(box((sx * 0.3, TY, TZ + R + 0.6), (0.04, 5.1, 0.04)), YELLOW)
    # Heck: Leiter, Schlauchkasten, Lichter, Stossstange
    for sx in (-0.2, 0.2):
        v.add(box((sx, TY + 3.25, 2.2), (0.05, 0.05, 2.2)), METAL)
    for k in range(6):
        v.add(box((0, TY + 3.25, 1.3 + k * 0.33), (0.4, 0.04, 0.04)), METAL)
    v.add(box((0, 4.35, 1.15), (2.0, 0.5, 0.5)), METAL)
    lights_rear(v, 4.62, 1.0, 1.0)
    v.add(box((0, 4.65, 0.7), (W, 0.12, 0.15)), DARK)
    # Seitenkaesten, Kotfluegel
    for sx in (-1, 1):
        v.add(box((sx * 1.0, -0.9, 1.15), (0.5, 1.6, 0.6)), METAL)
        v.add(box((sx * 1.26, -0.9, 1.15), (0.02, 1.4, 0.04)), DARK)
        v.add(box((sx * 0.95, 2.6, 1.28), (0.66, 2.6, 0.08)), DARK)
        v.add(box((sx * 0.95, 3.95, 0.72), (0.6, 0.03, 0.55)), DARK)
    v.axle("F", -3.0, 0.55, 0.4, 2.0, "C8C8C8")
    v.axle("R1", 1.95, 0.55, 0.6, 1.9, "C8C8C8")
    v.axle("R2", 3.25, 0.55, 0.6, 1.9, "C8C8C8")
    return v.finish()


# ===================================================== SATTELZUGMASCHINE
def semi_tractor():
    v = Vehicle("Vehicle_SemiTractor")
    col, W = "2F5E8C", 2.5
    v.add(box((0, -0.2, 0.85), (1.0, 7.0, 0.3)), DARK)
    v.add(box((0, -2.85, 1.55), (W * 0.8, 2.0, 1.1), (0.9, 0.95)), col)
    for sx in (-1, 1):
        v.add(box((sx * 1.0, -2.75, 1.22), (0.52, 1.6, 0.1)), col)
        v.add(box((sx * 1.0, -2.2, 0.95), (0.52, 0.1, 0.5)), col)
        v.add(box((sx * 1.0, -3.5, 1.32), (0.36, 0.1, 0.16)), HEAD)
    v.add(box((0, -3.87, 1.5), (1.1, 0.04, 0.9)), CHROME)
    for k in range(5):
        v.add(box((0, -3.9, 1.14 + k * 0.18), (1.0, 0.03, 0.05)), DARK)
    v.add(box((0, -3.97, 0.85), (W, 0.22, 0.35)), CHROME)
    v.add(box((0, -3.88, 2.06), (0.25, 0.08, 0.1)), CHROME)
    cabin(v, -1.85, -0.35, W, 1.0, 2.2, 2.9, col, (0.97, 0.85))
    v.add(box((0, 0.15, 2.1), (W, 1.0, 2.2)), col)
    v.add(box((0, -0.7, 3.25), (W * 0.95, 1.9, 0.5), (1.0, 0.5)), col)
    for y, d in ((-1.1, 1.52), (0.15, 1.02)):
        v.add(box((0, y, 1.45), (W + 0.02, d, 0.15)), WHITE)
    v.add(box((0, -1.83, 2.95), (W * 0.9, 0.2, 0.08)), DARK)  # Sonnenblende
    mirrors(v, -1.7, 2.35, 1.5)
    for sx in (-1, 1):
        v.add(cyl((sx * 1.05, 0.75, 1.0), 0.09, 0.09, 2.9, 8), CHROME)
        v.add(xf(cyl((0, 0, -0.55), 0.34, 0.34, 1.1, 10), loc=(sx * 0.95, -1.1, 0.95), rot=(90, 0, 0)), CHROME)
        v.add(box((sx * 1.2, -0.2, 0.7), (0.2, 0.5, 0.06)), METAL)
        v.add(box((sx * 0.95, 1.8, 1.25), (0.66, 2.3, 0.08)), DARK)
        v.add(box((sx * 0.95, 3.0, 0.72), (0.6, 0.03, 0.55)), DARK)
    beacon(v, 0, -1.0, 3.5)
    v.add(box((0, 1.8, 1.06), (1.3, 1.1, 0.12)), DARK)  # Sattelplatte
    v.add(box((0, 2.2, 1.13), (0.2, 0.4, 0.02)), IRON)
    lights_rear(v, 3.15, 0.95, 0.9)
    v.axle("F", -2.6, 0.55, 0.4, 2.0, CHROME)
    v.axle("R1", 1.15, 0.55, 0.6, 1.9, CHROME)
    v.axle("R2", 2.45, 0.55, 0.6, 1.9, CHROME)
    v.empty("Hitch", (0, 1.8, 1.12))
    return v.finish()


# =========================================================== TIEFLADER
def lowboy_trailer():
    """Ursprung = Koenigszapfen auf Bodenhoehe."""
    v = Vehicle("Trailer_LowLoader")
    col, W = "C8302C", 2.6
    v.add(box((0, 0, 1.12), (0.12, 0.12, 0.1)), IRON)  # Koenigszapfen
    v.add(box((0, 0.6, 1.35), (W, 2.2, 0.3)), col)  # Schwanenhals oben
    v.add(xf(box((0, 0, 0), (W, 1.2, 0.3)), loc=(0, 2.1, 1.0), rot=(-38, 0, 0)), col)
    v.add(box((0, 6.9, 0.68), (W, 9.4, 0.26)), col)  # Tiefbett
    v.add(box((0, 6.9, 0.82), (W - 0.2, 9.2, 0.04)), WOOD_D)
    for k in range(12):
        v.add(box((0, 2.4 + k * 0.78, 0.845), (W - 0.2, 0.03, 0.01)), DARK)
    for sx in (-1, 1):
        v.add(box((sx * (W / 2 + 0.02), 6.9, 0.68), (0.04, 9.4, 0.12)), YELLOW)
        for k in range(6):
            v.add(box((sx * (W / 2 + 0.03), 2.8 + k * 1.6, 0.6), (0.03, 0.12, 0.12)), IRON)
    v.add(box((0, 12.4, 1.1), (W, 2.6, 0.3)), col)  # Heckteil ueber Achsen
    v.add(xf(box((0, 0, 0), (W, 0.8, 0.26)), loc=(0, 11.4, 0.9), rot=(30, 0, 0)), col)
    # Rampen hochgeklappt
    for sx in (-0.8, 0.8):
        v.add(xf(box((0, 0, 0), (0.7, 0.12, 1.8)), loc=(sx, 13.7, 2.1), rot=(-8, 0, 0)), DARK)
        for k in range(5):
            v.add(xf(box((0, 0, 0), (0.7, 0.03, 0.04)), loc=(sx, 13.62, 1.4 + k * 0.33), rot=(-8, 0, 0)), METAL)
    # Warnstreifen + Banner + Lichter
    for k in range(10):
        v.add(box((-W / 2 + 0.13 + k * 0.26, 13.72, 1.1), (0.26, 0.02, 0.3)), YELLOW if k % 2 == 0 else DARK)
    v.add(box((0, 13.74, 3.25), (2.4, 0.02, 0.36)), YELLOW)
    v.add(text("OVERSIZE LOAD", 0.2, (0, 13.76, 3.25), 0.01, facing=180), DARK)
    lights_rear(v, 13.72, 0.8, 1.0)
    # Stuetzbeine
    for sx in (-1, 1):
        v.add(box((sx * 0.8, 0.9, 0.62), (0.12, 0.12, 1.1)), DARK)
        v.add(box((sx * 0.8, 0.9, 0.04), (0.3, 0.3, 0.08)), DARK)
        v.add(box((sx * 0.95, 12.5, 0.95), (0.66, 2.8, 0.06)), DARK)
    v.axle("A1", 11.55, 0.45, 0.55, 1.95, col)
    v.axle("A2", 12.5, 0.45, 0.55, 1.95, col)
    v.axle("A3", 13.45, 0.45, 0.55, 1.95, col)
    return v.finish()


# ======================================================= SERVICE-TRUCK
def service_truck():
    v = Vehicle("Vehicle_ServiceTruck")
    col, W = WHITE, 2.3
    v.add(box((0, 0, 0.8), (1.0, 7.0, 0.25)), DARK)
    v.add(box((0, -2.9, 1.3), (W * 0.85, 1.3, 0.8), (0.95, 0.95)), col)
    for sx in (-1, 1):
        v.add(box((sx * 0.95, -2.85, 1.02), (0.4, 1.1, 0.08)), col)
    v.add(box((0, -3.56, 1.3), (1.2, 0.04, 0.55)), DARK)
    lights_front(v, -3.56, 1.3, 0.78, (0.22, 0.2))
    v.add(box((0, -3.62, 0.85), (W, 0.2, 0.28)), METAL)
    cabin(v, -2.25, -0.75, W, 0.85, 1.85, 2.5, col)
    for y, d in ((-1.5, 1.52), (-2.9, 1.32)):
        v.add(box((0, y, 1.45 if y > -2 else 1.3), (W * (1.0 if y > -2 else 0.86) + 0.02, d, 0.14)), ORANGE)
    v.add(box((0, -1.5, 2.62), (1.3, 0.2, 0.08)), DARK)
    beacon(v, -0.4, -1.5, 2.66)
    beacon(v, 0.4, -1.5, 2.66)
    mirrors(v, -2.15, 1.95, 1.35)
    # Pritsche mit Werkzeugkaesten
    v.add(box((0, 1.5, 1.05), (W, 4.4, 0.2)), "6A6A6A")
    for sx in (-1, 1):
        v.add(box((sx * (W / 2 - 0.3), 1.6, 1.65), (0.6, 4.0, 1.0)), col)
        v.add(box((sx * (W / 2 + 0.005), 1.6, 1.55), (0.01, 4.0, 0.14)), ORANGE)
        for k in range(3):
            y = 0.25 + k * 1.33
            v.add(box((sx * (W / 2 + 0.006), y + 0.66, 1.65), (0.01, 0.02, 0.9)), DARK)
            v.add(box((sx * (W / 2 + 0.02), y + 0.45, 1.85), (0.03, 0.15, 0.05)), DARK)
        v.add(text("SERVICE", 0.26, (sx * (W / 2 + 0.012), 1.6, 1.95), 0.01, facing=90 * sx), ORANGE)
        v.add(box((sx * 0.95, 1.6, 0.98), (0.6, 1.4, 0.06)), DARK)
    v.add(box((0, -0.55, 2.2), (W, 0.08, 0.08)), DARK)  # Kopfschutzgitter
    for sx in (-1, 1):
        v.add(box((sx * (W / 2 - 0.05), -0.55, 1.7), (0.08, 0.08, 1.1)), DARK)
    # Schweissgeraet, Flaschen, Ersatzrad
    v.add(box((0, 0.2, 1.45), (0.7, 0.6, 0.6)), RED)
    v.add(box((0, -0.11, 1.55), (0.4, 0.02, 0.2)), DARK)
    for i, c in enumerate(("3C7A3E", "9AA2A8")):
        v.add(cyl((-0.15 + i * 0.3, 1.2, 1.15), 0.12, 0.12, 1.1, 8), c)
        v.add(cyl((-0.15 + i * 0.3, 1.2, 2.25), 0.06, 0.04, 0.1, 6), DARK)
    v.add(xf(cyl((0, 0, -0.14), 0.45, 0.45, 0.28, 12), loc=(0, 2.3, 1.3), rot=(90, 0, 0)), TIRE)
    # Kran
    v.add(cyl((0, 3.3, 1.15), 0.32, 0.26, 0.7, 8), YELLOW)
    v.add(box((0, 3.3, 1.95), (0.36, 0.36, 0.3)), YELLOW)
    v.add(xf(box((0, -1.7, 0), (0.26, 3.4, 0.26)), loc=(0, 3.3, 2.1), rot=(-8, 0, 0)), YELLOW)
    v.add(xf(box((0, -1.0, 0), (0.2, 2.0, 0.2)), loc=(0, 3.3, 2.1), rot=(-8, 0, 0)), DARK)
    v.add(box((0, -0.1, 2.2), (0.02, 0.02, 0.5)), DARK)
    v.add(box((0, -0.1, 1.9), (0.12, 0.08, 0.14)), YELLOW)
    lights_rear(v, 3.72, 1.0, 0.95)
    v.add(box((0, 3.75, 0.72), (W, 0.12, 0.15)), DARK)
    v.axle("F", -2.3, 0.5, 0.36, 1.85, "E8E8E8")
    v.axle("R", 1.8, 0.5, 0.55, 1.8, "E8E8E8")
    return v.finish()


# ==================================================================== MAIN
def export_hierarchy(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(HERE, objs[0].name + ".fbx"), use_selection=True,
        object_types={"MESH", "EMPTY"}, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", bake_space_transform=True,
    )
    print(objs[0].name, sum(len(o.data.polygons) for o in objs if o.type == "MESH"), "faces")


def main():
    sets = [pickup(), service_truck(), fuel_tanker(), semi_tractor(), lowboy_trailer()]
    for objs in sets:
        export_hierarchy(objs)
    cam, target = bb.setup_preview()
    pos = [(-13, 0), (-7.5, 0), (-1.5, 0), (5, 0)]
    for objs, (x, y) in zip(sets, pos):
        objs[0].location = (x, y, 0)
    hitch = sets[3][0].location + [o for o in sets[3] if o.name.endswith("Hitch")][0].location
    sets[4][0].location = (hitch.x, hitch.y, 0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "vehicles.blend"))
    shots = [("preview_all", (16, -20, 9), (-2, 2, 1.2), 28),
             ("preview_Pickup", (-8.5, -7.5, 3.2), (-13, 0, 1.0), 35),
             ("preview_ServiceTruck", (-2.5, -9.5, 4), (-7.5, 0.5, 1.4), 35),
             ("preview_FuelTanker", (4, -11, 4.5), (-1.5, 0.3, 1.8), 33),
             ("preview_SemiTrailer", (17, -8, 7), (5, 7, 1.2), 28),
             ("preview_TrailerRear", (12, 26, 5), (5, 14, 1.2), 32)]
    bb.render_shots(shots, cam, target)
    print("DONE")


if __name__ == "__main__":
    main()
