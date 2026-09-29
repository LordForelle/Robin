"""Erzeugt Low-Poly Gebaeude fuer den Goldgraeber-Simulator.

Ausfuehren:  blender -b -P build_buildings.py   (oder: python3 build_buildings.py mit pip-Paket bpy)
Ausgabe:     FBX pro Gebaeude, buildings.blend, preview_*.png im selben Ordner.
Front zeigt in Blender nach -Y (in Unity nach +Z). Ursprung = Bodenmitte.
Schilder-Texte: siehe SIGNS unten.
"""
import math
import os

import bpy
from mathutils import Euler, Vector

OUT = os.path.dirname(os.path.abspath(__file__))

SIGNS = {
    "saloon": "SALOON",
    "hiring": "HIRING",
    "townhall": "TOWN HALL",
    "gas": "GAS",
    "gas_price": "3.49",
    "shop": "SHOP",
    "ice": "ICE",
    "bank": "BANK",
    "gold": "GOLD",
    "gold_sub": "BUY & SELL",
}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ------------------------------------------------------------------ Farben
WOOD = "A0693A"
WOOD_D = "7A4A26"
WOOD_DD = "553420"
WOOD_L = "C49A6C"
TRIM = "EFE6D2"
STONE = "8C857A"
STONE_L = "B3AB9C"
GLASS = "2E8A8F"
DOOR_DARK = "2A1C12"
IRON = "3A3A3A"
METAL = "9AA2A8"
GOLD = "E8B923"
LAMP = "FFE08A"
RED = "C8302C"
WHITE = "EDEDED"
GREEN = "4E7A3A"

_mats = {}


def mat(hexcol):
    if hexcol in _mats:
        return _mats[hexcol]
    rgb = [int(hexcol[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c ** 2.2 for c in rgb]
    m = bpy.data.materials.new("bld_" + hexcol)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    if hexcol in (GOLD, METAL):
        bsdf.inputs["Metallic"].default_value = 0.6
        bsdf.inputs["Roughness"].default_value = 0.4
    if hexcol == LAMP:
        bsdf.inputs["Emission Color"].default_value = (*lin, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 1.5
    m.diffuse_color = (*lin, 1.0)
    _mats[hexcol] = m
    return m


# ------------------------------------------------------------ Geometrie
def box(c, s, top=(1.0, 1.0)):
    cx, cy, cz = c
    hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
    tx, ty = hx * top[0], hy * top[1]
    v = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
         (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
         (cx - tx, cy - ty, cz + hz), (cx + tx, cy - ty, cz + hz),
         (cx + tx, cy + ty, cz + hz), (cx - tx, cy + ty, cz + hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


def cyl(c, r0, r1, h, n=8, rot=0.0, cap=True):
    """Zylinder/Kegelstumpf entlang Z, Boden bei c[2]."""
    cx, cy, cz = c
    v = [(cx + r0 * math.cos(2 * math.pi * i / n + rot), cy + r0 * math.sin(2 * math.pi * i / n + rot), cz)
         for i in range(n)]
    v += [(cx + r1 * math.cos(2 * math.pi * i / n + rot), cy + r1 * math.sin(2 * math.pi * i / n + rot), cz + h)
          for i in range(n)]
    f = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    f.append(tuple(reversed(range(n))))
    if cap:
        f.append(tuple(range(n, 2 * n)))
    return v, f


def pyramid(c, r, h, n=4, rot=math.pi / 4):
    cx, cy, cz = c
    v = [(cx + r * math.cos(2 * math.pi * i / n + rot), cy + r * math.sin(2 * math.pi * i / n + rot), cz)
         for i in range(n)] + [(cx, cy, cz + h)]
    f = [(i, (i + 1) % n, n) for i in range(n)] + [tuple(reversed(range(n)))]
    return v, f


def tri_x(cx, cy, z0, w, d, h):
    """Dreiecksprisma, First entlang X (Giebel links/rechts)."""
    v = []
    for x in (cx - w / 2, cx + w / 2):
        v += [(x, cy - d / 2, z0), (x, cy + d / 2, z0), (x, cy, z0 + h)]
    f = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return v, f


def tri_y(cx, cy, z0, w, d, h):
    """Dreiecksprisma, First entlang Y (Giebel vorne/hinten)."""
    v = []
    for y in (cy - d / 2, cy + d / 2):
        v += [(cx - w / 2, y, z0), (cx + w / 2, y, z0), (cx, y, z0 + h)]
    f = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    return v, f


def xf(geo, loc=(0, 0, 0), rot=(0, 0, 0), pivot=(0, 0, 0)):
    """Geometrie um pivot drehen (Euler XYZ, Grad) und verschieben."""
    m = Euler([math.radians(a) for a in rot]).to_matrix()
    p = Vector(pivot)
    v = [tuple(m @ (Vector(q) - p) + p + Vector(loc)) for q in geo[0]]
    return v, geo[1]


def text(s, size, c, depth=0.04, facing=0):
    """Text als Mesh, Vorderseite zeigt nach -Y (facing dreht um Z)."""
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = s
    cu.size = size
    cu.extrude = depth / 2
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.resolution_u = 2
    ob = bpy.data.objects.new("txt", cu)
    scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh()
    v = [tuple(q.co) for q in me.vertices]
    f = [tuple(p.vertices) for p in me.polygons]
    ob.evaluated_get(dg).to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return xf((v, f), loc=c, rot=(90, 0, facing))


def signed_volume(me):
    """Positiv, wenn die Normalen eines geschlossenen Teils nach aussen zeigen."""
    vol = 0.0
    for p in me.polygons:
        vs = [me.vertices[i].co for i in p.vertices]
        for k in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[k].cross(vs[k + 1]))
    return vol


class Build:
    def __init__(self, name):
        self.name = name
        self.parts = []

    def add(self, geo, col):
        self.parts.append((geo, col))

    # --- Bauteile -------------------------------------------------------
    def window(self, x, z, w, h, wall, side=0, frame=TRIM, glass=GLASS, cross=True, sill=True, shutters=None):
        """Fenster auf Wand; wall = Abstand Wand zur Mitte, side = Drehung um Z (0 = vorne)."""
        g = []
        y = -wall
        g.append((box((x, y - 0.03, z), (w + 0.16, 0.08, h + 0.16)), frame))
        g.append((box((x, y - 0.05, z), (w, 0.06, h)), glass))
        if cross:
            g.append((box((x, y - 0.08, z), (0.06, 0.04, h)), frame))
            g.append((box((x, y - 0.08, z), (w, 0.04, 0.06)), frame))
        if sill:
            g.append((box((x, y - 0.1, z - h / 2 - 0.1), (w + 0.3, 0.2, 0.08)), frame))
        if shutters:
            for sx in (-1, 1):
                g.append((box((x + sx * (w / 2 + 0.25), y - 0.04, z), (0.34, 0.06, h + 0.1)), shutters))
        for geo, col in g:
            self.add(xf(geo, rot=(0, 0, side)), col)

    def bars(self, x, z, w, h, wall, n=5):
        for i in range(n):
            bx = x - w / 2 + w * (i + 0.5) / n
            self.add(box((bx, -wall - 0.12, z), (0.04, 0.04, h + 0.1)), IRON)
        self.add(box((x, -wall - 0.12, z), (w + 0.1, 0.04, 0.04)), IRON)

    def door(self, x, z0, w, h, wall, col=DOOR_DARK, frame=TRIM, double=False, knob=GOLD):
        y = -wall
        self.add(box((x, y - 0.03, z0 + h / 2 + 0.05), (w + 0.24, 0.08, h + 0.1)), frame)
        self.add(box((x, y - 0.06, z0 + h / 2), (w, 0.06, h)), col)
        # Fuellungen
        halves = (-w / 4, w / 4) if double else (0,)
        pw = w / 2 - 0.2 if double else w - 0.3
        for hx in halves:
            self.add(box((x + hx, y - 0.1, z0 + h * 0.72), (pw, 0.03, h * 0.35)), col)
            self.add(box((x + hx, y - 0.1, z0 + h * 0.28), (pw, 0.03, h * 0.35)), col)
        if double:
            self.add(box((x, y - 0.1, z0 + h / 2), (0.04, 0.03, h)), frame)
            for kx in (-0.1, 0.1):
                self.add(box((x + kx, y - 0.13, z0 + h * 0.48), (0.05, 0.05, 0.12)), knob)
        else:
            self.add(box((x + w / 2 - 0.15, y - 0.13, z0 + h * 0.48), (0.06, 0.05, 0.06)), knob)

    def barrel(self, x, y, z=0.0, r=0.3, h=0.8):
        self.add(cyl((x, y, z), r * 0.9, r, h / 2, 8), WOOD_D)
        self.add(cyl((x, y, z + h / 2), r, r * 0.9, h / 2, 8), WOOD_D)
        for bz in (0.12, h - 0.16):
            self.add(cyl((x, y, z + bz), r * 0.96 + 0.02, r * 0.96 + 0.02, 0.05, 8), IRON)
        self.add(cyl((x, y, z + h / 2 - 0.03), r + 0.02, r + 0.02, 0.06, 8), IRON)

    def crate(self, x, y, z=0.0, s=0.6, rot=0):
        g = [(box((0, 0, s / 2), (s, s, s)), WOOD_L)]
        for sy in (-1, 1):
            g.append((box((0, sy * (s / 2 + 0.01), s / 2), (s, 0.03, 0.08)), WOOD_D))
            g.append((box((0, sy * (s / 2 + 0.01), s / 2), (0.08, 0.03, s)), WOOD_D))
        for geo, col in g:
            self.add(xf(geo, loc=(x, y, z), rot=(0, 0, rot)), col)

    def lantern(self, x, y, z, arm=0.25):
        self.add(box((x, y + arm / 2, z + 0.25), (0.04, arm, 0.04)), IRON)
        self.add(box((x, y, z), (0.18, 0.18, 0.26)), LAMP)
        self.add(pyramid((x, y, z + 0.13), 0.16, 0.14), IRON)
        self.add(box((x, y, z - 0.15), (0.2, 0.2, 0.04)), IRON)

    def lamp_post(self, x, y, h=3.2):
        self.add(cyl((x, y, 0), 0.14, 0.12, 0.3, 6), IRON)
        self.add(cyl((x, y, 0.3), 0.06, 0.05, h - 0.3, 6), IRON)
        self.add(box((x, y, h + 0.2), (0.3, 0.3, 0.4), (1.2, 1.2)), LAMP)
        self.add(pyramid((x, y, h + 0.4), 0.3, 0.25), IRON)

    def bench(self, x, y, z=0.0, w=1.6, rot=0):
        g = [(box((0, 0, 0.45), (w, 0.45, 0.07)), WOOD_D),
             (box((0, 0.2, 0.75), (w, 0.06, 0.3)), WOOD_D)]
        for sx in (-1, 1):
            g.append((box((sx * (w / 2 - 0.1), 0, 0.22), (0.08, 0.4, 0.44)), WOOD_DD))
        for geo, col in g:
            self.add(xf(geo, loc=(x, y, z), rot=(0, 0, rot)), col)

    def bush(self, x, y, s=0.6, col=GREEN, z=0.0):
        self.add(cyl((x, y, z), s * 0.7, s, s * 0.6, 6), col)
        self.add(cyl((x, y, z + s * 0.6), s, s * 0.4, s * 0.6, 6, rot=0.5), col)

    def gable_roof_x(self, cx, cy, z, w, d, h, over=0.4, t=0.15, col="7A3A2E"):
        """Satteldach, First entlang X."""
        half = d / 2 + over
        ang = math.degrees(math.atan2(h, d / 2))
        length = half / math.cos(math.radians(ang)) + 0.1
        for sy in (-1, 1):
            geo = box((0, 0, 0), (w + 2 * over, length, t))
            geo = xf(geo, rot=(-sy * ang, 0, 0))
            off = Vector((0, sy * (length / 2 - 0.05), 0))
            off.rotate(Euler((math.radians(-sy * ang), 0, 0)))
            self.add(xf(geo, loc=(cx, cy + off.y, z + h + off.z + t / 2)), col)
        self.add(box((cx, cy, z + h + 0.1), (w + 2 * over, 0.2, 0.15)), WOOD_DD)

    def gable_roof_y(self, cx, cy, z, w, d, h, over=0.4, t=0.15, col="7A3A2E"):
        """Satteldach, First entlang Y (Giebel vorne)."""
        tmp = Build("tmp")
        tmp.gable_roof_x(0, 0, z, d, w, h, over, t, col)
        for geo, c in tmp.parts:
            self.add(xf(geo, loc=(cx, cy, 0), rot=(0, 0, 90)), c)

    def finish(self):
        objs = []
        for i, (geo, col) in enumerate(self.parts):
            me = bpy.data.meshes.new(f"{self.name}_{i}")
            me.from_pydata(geo[0], [], geo[1])
            me.validate()
            if signed_volume(me) < 0:
                me.flip_normals()
            me.materials.append(mat(col))
            ob = bpy.data.objects.new(me.name, me)
            scene.collection.objects.link(ob)
            objs.append(ob)
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
        ob.name = ob.data.name = self.name
        for p in ob.data.polygons:
            p.use_smooth = False
        return ob


# =================================================================== SALOON
def saloon():
    b = Build("Building_Saloon")
    W, D, H = 8.0, 7.0, 6.0
    F = D / 2  # Frontwand bei y = -F
    b.add(box((0, 0, 0.15), (W + 0.3, D + 0.3, 0.3)), STONE)
    b.add(box((0, 0, 0.3 + H / 2), (W, D, H)), WOOD)
    # Bretterlinien Front + Seiten
    z = 0.6
    while z < 0.3 + H:
        b.add(box((0, -F - 0.015, z), (W, 0.03, 0.05)), WOOD_D)
        for sx in (-1, 1):
            b.add(box((sx * (W / 2 + 0.015), 0, z), (0.03, D, 0.05)), WOOD_D)
        z += 0.4
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, 0.3 + H / 2), (0.22, 0.22, H)), WOOD_DD)
    # Flachdach + Scheinfassade
    b.add(box((0, 0.2, 0.3 + H + 0.1), (W + 0.3, D + 0.4, 0.2)), "5E4A3A")
    b.add(box((0, -F - 0.1, 7.2), (W + 0.4, 0.2, 1.8)), WOOD)
    b.add(box((0, -F - 0.1, 8.3), (W * 0.55, 0.2, 0.4)), WOOD)
    b.add(box((0, -F - 0.1, 8.65), (W * 0.25, 0.2, 0.3)), WOOD)
    for zc, wc in ((8.1, W + 0.6), (8.5, W * 0.55 + 0.2), (8.8, W * 0.25 + 0.2)):
        b.add(box((0, -F - 0.12, zc), (wc, 0.34, 0.1)), TRIM)
    # Schild
    b.add(box((0, -F - 0.24, 7.15), (5.6, 0.06, 1.3)), WOOD_DD)
    b.add(box((0, -F - 0.28, 7.15), (5.3, 0.06, 1.05)), TRIM)
    b.add(text(SIGNS["saloon"], 0.95, (0, -F - 0.33, 7.15), 0.05), "8C2F23")
    # Veranda + Balkon
    PY = -F - 1.3
    b.add(box((0, PY, 0.25), (W + 0.4, 2.6, 0.2)), WOOD_D)
    for i in range(12):
        b.add(box((-W / 2 - 0.2 + (i + 0.5) * (W + 0.4) / 12, PY, 0.355), (0.03, 2.6, 0.01)), WOOD_DD)
    b.add(box((0, -F - 2.75, 0.1), (2.4, 0.35, 0.2)), WOOD_D)
    posts = (-3.95, -1.3, 1.3, 3.95)
    for x in posts:
        b.add(box((x, -F - 2.45, 1.85), (0.2, 0.2, 3.0)), WOOD_DD)
        b.add(xf(box((0, 0, 0), (0.1, 0.5, 0.1)), loc=(x, -F - 2.25, 3.05), rot=(45, 0, 0)), WOOD_DD)
    b.add(box((0, PY, 3.45), (W + 0.4, 2.7, 0.2)), WOOD_DD)
    yb = -F - 2.55
    b.add(box((0, yb, 4.45), (W + 0.4, 0.1, 0.1)), TRIM)
    b.add(box((0, yb, 3.65), (W + 0.4, 0.1, 0.08)), TRIM)
    for i in range(21):
        b.add(box((-4.0 + i * 0.4, yb, 4.05), (0.06, 0.06, 0.8)), TRIM)
    for sx in (-1, 1):
        b.add(box((sx * 4.15, PY - 0.05, 4.45), (0.1, 2.6, 0.1)), TRIM)
        for j in range(6):
            b.add(box((sx * 4.15, -F - 0.1 - j * 0.45, 4.05), (0.06, 0.06, 0.8)), TRIM)
    # Eingang mit Schwingtueren
    b.add(box((0, -F - 0.02, 1.6), (1.7, 0.06, 2.5)), DOOR_DARK)
    b.add(box((0, -F - 0.04, 2.95), (2.0, 0.1, 0.2)), WOOD_DD)
    for sx in (-1, 1):
        b.add(box((sx * 0.93, -F - 0.04, 1.6), (0.16, 0.1, 2.6)), WOOD_DD)
        b.add(box((sx * 0.41, -F - 0.12, 1.55), (0.74, 0.05, 1.0)), WOOD_L)
        for zz in (1.15, 1.55, 1.95):
            b.add(box((sx * 0.41, -F - 0.155, zz), (0.74, 0.03, 0.07)), WOOD_D)
        b.lantern(sx * 1.35, -F - 0.25, 2.55)
    # Fenster
    for sx in (-1, 1):
        b.window(sx * 2.65, 1.75, 1.5, 1.6, F, shutters="3E5F4A")
        b.window(sx * 2.65, 4.8, 1.2, 1.4, F)
        for u in (-1.8, 1.4):
            b.window(u, 1.9, 1.0, 1.3, W / 2, side=90 * sx)
            b.window(u, 4.8, 1.0, 1.3, W / 2, side=90 * sx)
    b.door(0, 3.55, 1.1, 2.1, F, col=WOOD_DD)
    # Aushang "HIRING"
    b.add(box((1.45, -F - 0.05, 1.8), (0.62, 0.06, 0.8)), WOOD_DD)
    b.add(box((1.45, -F - 0.09, 1.8), (0.52, 0.03, 0.66)), "F4EEDC")
    b.add(text(SIGNS["hiring"], 0.13, (1.45, -F - 0.11, 1.98), 0.02), "B83A32")
    for i in range(3):
        b.add(box((1.45, -F - 0.11, 1.75 - i * 0.12), (0.36, 0.01, 0.03)), IRON)
    # Deko: Faesser, Bank, Anbindebalken, Kisten
    b.barrel(3.5, -F - 0.5, 0.35)
    b.barrel(2.9, -F - 0.45, 0.35, r=0.26, h=0.7)
    b.bench(-2.6, -F - 0.4, 0.35)
    for sx in (-1, 1):
        y = -F - 3.8
        for x in (sx * 1.9, sx * 3.7):
            b.add(box((x, y, 0.5), (0.14, 0.14, 1.0)), WOOD_DD)
        b.add(box((sx * 2.8, y, 0.9), (2.0, 0.1, 0.1)), WOOD_D)
    b.crate(-3.7, -F - 0.5, 0.35, 0.55, 10)
    b.crate(3.9, 1.0, 0.0, 0.7, 5)
    b.crate(3.9, 1.8, 0.0, 0.6, -8)
    b.barrel(-4.5, 2.0)
    return b.finish()


# ================================================================ RATHAUS
def townhall():
    b = Build("Building_TownHall")
    W, D, H = 12.0, 9.0, 7.0
    F = D / 2
    WALL = "E8DCC0"
    ROOF = "5B6770"
    COL = "F4F0E6"
    b.add(box((0, 0, 0.3), (W + 0.3, D + 0.3, 0.6)), STONE)
    b.add(box((0, 0, 0.6 + H / 2), (W, D, H)), WALL)
    b.add(box((0, 0, 3.95), (W + 0.12, D + 0.12, 0.2)), COL)  # Gurtgesims
    b.add(box((0, 0, 0.6 + H + 0.1), (W + 0.4, D + 0.4, 0.3)), COL)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, 0.6 + H / 2), (0.35, 0.35, H)), COL)
    # Hauptdach mit Giebeln
    ZR = 0.6 + H + 0.25
    b.add(tri_x(0, 0, ZR, W + 0.3, D + 0.3, 2.8), WALL)
    b.gable_roof_x(0, 0, ZR, W + 0.3, D + 0.3, 2.8, over=0.35, col=ROOF)
    # Portikus: Treppe, Saeulen, Gebaelk, Dreiecksgiebel
    PY = -F - 1.6
    for i in range(1, 4):
        b.add(box((0, -F - 1.4 - i * 0.3, 0.6 - i * 0.15 - 0.075), (7.6 + i * 0.4, 2.8 + i * 0.6, 0.15)), STONE_L)
    b.add(box((0, -F - 1.4, 0.3), (7.6, 2.8, 0.6)), STONE_L)
    for x in (-3.0, -1.0, 1.0, 3.0):
        b.add(box((x, PY - 0.6, 0.72), (0.8, 0.8, 0.25)), COL)
        b.add(cyl((x, PY - 0.6, 0.85), 0.3, 0.26, 5.3, 8, rot=math.pi / 8), COL)
        b.add(box((x, PY - 0.6, 6.25), (0.8, 0.8, 0.25)), COL)
    b.add(box((0, -F - 1.15, 6.7), (8.2, 2.7, 0.7)), COL)
    b.add(box((0, -F - 2.5, 6.45), (8.2, 0.06, 0.12)), "C9BFA8")
    b.add(tri_y(0, -F - 1.15, 7.05, 8.4, 2.7, 1.6), COL)
    b.add(xf(tri_y(0, -F - 2.52, 7.2, 6.4, 0.05, 1.1), rot=(0, 0, 0)), "D8CDB4")
    b.gable_roof_y(0, -F - 1.15, 7.05, 8.4, 2.7, 1.6, over=0.2, col=ROOF)
    # Schrift auf Gebaelk
    b.add(text(SIGNS["townhall"], 0.42, (0, -F - 2.55, 6.7), 0.04), "7A5A1A")
    # Uhrturm
    TZ = 0.6 + H + 0.25
    b.add(box((0, 0.3, TZ + 2.4), (2.6, 2.6, 4.8)), WALL)
    b.add(box((0, 0.3, TZ + 4.9), (3.0, 3.0, 0.25)), COL)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * 1.3, 0.3 + sy * 1.3, TZ + 2.4), (0.25, 0.25, 4.8)), COL)
    b.add(pyramid((0, 0.3, TZ + 5.0), 2.2, 2.2), ROOF)
    b.add(cyl((0, 0.3, TZ + 6.6), 0.05, 0.04, 2.4, 6), IRON)
    b.add(box((0.65, 0.3, TZ + 8.6), (1.2, 0.03, 0.7)), "2F5E8C")
    b.add(box((0.65, 0.28, TZ + 8.6), (1.2, 0.03, 0.18)), GOLD)
    # Uhren vorne + seitlich
    for side in (0, 90, -90):
        g = []
        cy_face = 0.3 - 1.3
        g.append((xf(cyl((0, 0, 0), 0.85, 0.85, 0.1, 12), loc=(0, cy_face - 0.02, TZ + 3.2), rot=(90, 0, 0)), IRON))
        g.append((xf(cyl((0, 0, 0), 0.75, 0.75, 0.1, 12), loc=(0, cy_face - 0.06, TZ + 3.2), rot=(90, 0, 0)), COL))
        for k in range(12):
            a = 2 * math.pi * k / 12
            g.append((box((0.62 * math.sin(a), cy_face - 0.17, TZ + 3.2 + 0.62 * math.cos(a)), (0.06, 0.03, 0.12)), IRON))
        g.append((box((0, cy_face - 0.2, TZ + 3.2 + 0.25), (0.06, 0.03, 0.5)), IRON))
        g.append((box((0.18, cy_face - 0.2, TZ + 3.2), (0.36, 0.03, 0.06)), IRON))
        for geo, c in g:
            b.add(xf(geo, rot=(0, 0, side), pivot=(0, 0.3, 0)), c)
    # Tuer + Fenster
    b.door(0, 0.6, 2.0, 3.0, F, col="5A3A22", frame=COL, double=True)
    b.add(box((0, -F - 0.05, 4.0), (2.0, 0.06, 0.5)), GLASS)
    for x in (-4.6, -2.6, 2.6, 4.6):
        b.window(x, 2.3, 1.1, 2.0, F, frame=COL, shutters="3E5F4A")
        b.window(x, 5.6, 1.1, 1.7, F, frame=COL)
    b.window(0, 5.6, 1.3, 1.7, F, frame=COL)
    for sx in (-1, 1):
        for u in (-2.4, 0.0, 2.4):
            b.window(u, 2.3, 1.1, 2.0, W / 2, side=90 * sx, frame=COL)
            b.window(u, 5.6, 1.1, 1.7, W / 2, side=90 * sx, frame=COL)
    # Umfeld
    for sx in (-1, 1):
        b.lamp_post(sx * 4.3, -F - 3.4)
        b.bush(sx * 5.2, -F - 0.7, 0.45, z=0.45)
        b.bush(sx * 6.0, -F - 0.7, 0.35, "5E8C44", z=0.45)
        b.add(box((sx * 5.6, -F - 0.7, 0.25), (1.8, 1.0, 0.5)), STONE_L)
        b.bench(sx * 6.2, -F - 3.0, 0, 1.6, 0)
    return b.finish()


# ============================================================ TANKSTELLE
def gas_station():
    b = Build("Building_GasStation")
    CONC = "A8A8A0"
    b.add(box((0, -2.5, 0.05), (15, 12, 0.1)), CONC)
    for i in range(6):
        b.add(box((-7.5 + i * 3, -2.5, 0.101), (0.05, 12, 0.005)), "8E8E88")
    # Shop
    SY = 2.2
    b.add(box((0, SY + 1.5, 0.1 + 1.8), (9, 3.0, 3.6)), WHITE)
    b.add(box((0, SY + 1.5, 3.85), (9.3, 3.3, 0.5)), RED)
    b.add(box((0, SY + 1.5, 4.15), (9.4, 3.4, 0.12)), WHITE)
    b.add(box((0, SY - 0.02, 0.35), (9.0, 0.06, 0.5)), "5E5E5E")
    for x in (-3.3, -1.9, 2.3, 3.6):
        b.add(box((x, SY - 0.03, 1.75), (1.25, 0.06, 2.3)), GLASS)
        b.add(box((x + 0.66, SY - 0.05, 1.75), (0.08, 0.08, 2.4)), METAL)
    b.add(box((-2.6, SY - 0.05, 2.95), (2.9, 0.08, 0.1)), METAL)
    b.add(box((2.95, SY - 0.05, 2.95), (2.9, 0.08, 0.1)), METAL)
    b.add(box((0.2, SY - 0.03, 1.4), (1.5, 0.06, 2.6)), METAL)
    b.add(box((0.2, SY - 0.06, 1.45), (1.3, 0.06, 2.4)), GLASS)
    b.add(box((0.2, SY - 0.1, 1.4), (0.5, 0.04, 0.06)), IRON)
    b.add(text(SIGNS["shop"], 0.36, (0, SY - 0.02, 3.85), 0.04), WHITE)
    # Dach
    CY = -4.0
    for x in (-3.8, 3.8):
        for y in (CY - 1.8, CY + 1.8):
            b.add(box((x, y, 2.6), (0.35, 0.35, 5.0)), WHITE)
            b.add(box((x, y, 0.35), (0.5, 0.5, 0.5)), RED)
    b.add(box((0, CY, 5.35), (11, 7, 0.7)), WHITE)
    b.add(box((0, CY, 5.25), (11.1, 7.1, 0.25)), RED)
    for x in (-3, 0, 3):
        for y in (CY - 1.6, CY + 1.6):
            b.add(box((x, y, 4.98), (1.2, 0.5, 0.05)), LAMP)
    b.add(text(SIGNS["gas"], 0.55, (-3.4, CY - 3.57, 5.45), 0.04), RED)
    b.add(text(SIGNS["gas"], 0.55, (3.4, CY - 3.57, 5.45), 0.04), RED)
    # Zapfsaeulen-Inseln
    for x in (-2.0, 2.0):
        b.add(box((x, CY, 0.2), (1.3, 3.8, 0.2)), "C8C8C0")
        for y in (CY - 1.95, CY + 1.95):
            b.add(box((x, y, 0.2), (1.3, 0.12, 0.21)), GOLD)
        for py, rot in ((CY - 0.8, 0), (CY + 0.8, 180)):
            g = []
            g.append((box((0, 0, 1.15), (0.9, 0.6, 1.7)), RED))
            g.append((box((0, 0, 2.1), (0.95, 0.65, 0.2)), WHITE))
            g.append((box((0, -0.31, 1.6), (0.6, 0.02, 0.35)), IRON))
            g.append((box((-0.1, -0.325, 1.62), (0.25, 0.01, 0.08)), "7CFC6A"))
            g.append((box((0, -0.31, 1.15), (0.6, 0.02, 0.3)), WHITE))
            for k in range(3):
                g.append((box((-0.2 + k * 0.2, -0.325, 1.15), (0.14, 0.01, 0.1)), (GOLD, GREEN, IRON)[k]))
            for sx in (-1, 1):
                g.append((box((sx * 0.5, 0, 1.3), (0.1, 0.25, 0.35)), IRON))
                g.append((box((sx * 0.56, 0.02, 1.0), (0.05, 0.05, 0.6)), IRON))
            for geo, c in g:
                b.add(xf(geo, loc=(x, py, 0.2), rot=(0, 0, rot)), c)
        b.add(box((x, CY, 1.0), (0.15, 0.15, 1.6)), METAL)  # Mittelpoller
    # Preisschild-Mast
    PX, PY = 6.3, -7.6
    for sx in (-0.7, 0.7):
        b.add(box((PX + sx, PY, 2.6), (0.25, 0.25, 5.2)), METAL)
    b.add(box((PX, PY, 5.6), (2.5, 0.4, 1.5)), WHITE)
    b.add(box((PX, PY, 5.6), (2.3, 0.44, 1.3)), RED)
    b.add(text(SIGNS["gas"], 0.7, (PX, PY - 0.25, 5.6), 0.04), WHITE)
    b.add(box((PX, PY, 4.1), (2.2, 0.3, 1.2)), IRON)
    b.add(text(SIGNS["gas_price"], 0.55, (PX, PY - 0.17, 4.1), 0.03), GOLD)
    # Deko
    for i in range(4):
        b.add(cyl((-6.6, 1.0, 0.1 + i * 0.26), 0.36, 0.36, 0.24, 10), "2A2A2A")
    b.add(cyl((-6.6, 1.0, 1.14), 0.18, 0.18, 0.01, 8), "444444")
    for i, (x, y) in enumerate(((-6.8, 2.5), (-6.1, 2.8), (-6.5, 3.4))):
        b.barrel(x, y, 0.1, 0.3, 0.9)
    b.add(box((5.4, SY - 0.5, 0.75), (1.4, 0.8, 1.3)), WHITE)
    b.add(box((5.4, SY - 0.91, 0.9), (1.2, 0.02, 0.5)), "4D8FCC")
    b.add(text(SIGNS["ice"], 0.3, (5.4, SY - 0.93, 0.9), 0.02), WHITE)
    b.add(box((6.8, SY - 0.4, 0.7), (0.5, 0.4, 1.2)), GOLD)  # Luftpumpe
    b.add(box((6.8, SY - 0.61, 0.95), (0.3, 0.02, 0.3)), IRON)
    b.add(cyl((-4.4, SY - 0.5, 0.1), 0.25, 0.25, 0.8, 8), GREEN)  # Muelleimer
    b.add(cyl((-4.4, SY - 0.5, 0.9), 0.28, 0.2, 0.12, 8), IRON)
    return b.finish()


# =================================================================== BANK
def bank():
    b = Build("Building_Bank")
    W, D, H = 9.0, 8.0, 7.2
    F = D / 2
    BRICK = "A5553F"
    SAND = "D8C7A0"
    b.add(box((0, 0, 0.35), (W + 0.3, D + 0.3, 0.7)), SAND)
    b.add(box((0, 0, 0.7 + H / 2), (W, D, H)), BRICK)
    # Ziegelfugen-Andeutung Front
    z = 1.0
    while z < 0.7 + H:
        b.add(box((0, -F - 0.012, z), (W, 0.025, 0.03)), "8E4634")
        z += 0.35
    b.add(box((0, 0, 4.1), (W + 0.15, D + 0.15, 0.25)), SAND)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((sx * W / 2, sy * D / 2, 0.7 + H / 2), (0.45, 0.45, H)), SAND)
    # Gesims mit Zahnfries + Attika
    ZT = 0.7 + H
    b.add(box((0, 0, ZT + 0.15), (W + 0.6, D + 0.6, 0.3)), SAND)
    for i in range(22):
        b.add(box((-W / 2 + 0.2 + i * (W - 0.4) / 21, -F - 0.08, ZT - 0.1), (0.15, 0.16, 0.2)), SAND)
    b.add(box((0, 0, ZT + 0.6), (W, D, 0.6)), BRICK)
    b.add(box((0, 0, ZT + 0.95), (W + 0.3, D + 0.3, 0.12)), SAND)
    b.add(box((0, 0.3, ZT + 0.35), (W - 0.4, D - 0.4, 0.3)), "5A5A5A")
    b.add(box((0, -F - 0.1, ZT + 1.35), (2.4, 0.2, 0.7)), SAND)
    b.add(xf(cyl((0, 0, 0), 0.5, 0.5, 0.12, 12), loc=(0, -F - 0.2, ZT + 1.35), rot=(90, 0, 0)), GOLD)
    b.add(text("$", 0.6, (0, -F - 0.33, ZT + 1.35), 0.04), "7A5A1A")
    # Eingang: Stufen, Pilaster, Tuer, Schild
    for i in range(3):
        b.add(box((0, -F - 0.4 - i * 0.35, 0.58 - i * 0.2), (3.6 + i * 0.4, 0.8 + i * 0.7, 0.2)), SAND)
    for sx in (-1, 1):
        b.add(box((sx * 1.55, -F - 0.25, 2.1), (0.5, 0.5, 2.9)), SAND)
        b.add(cyl((sx * 1.55, -F - 0.3, 0.7), 0.2, 0.2, 2.9, 8), "E8DCC0")
    b.door(0, 0.7, 1.9, 2.7, F, col="2F4A3A", frame=SAND, double=True)
    b.add(box((0, -F - 0.3, 3.72), (4.0, 0.72, 0.34)), SAND)
    b.add(box((0, -F - 0.08, 4.8), (4.4, 0.1, 1.0)), "1F2E27")
    b.add(box((0, -F - 0.06, 4.8), (4.6, 0.06, 1.2)), GOLD)
    b.add(text(SIGNS["bank"], 0.8, (0, -F - 0.16, 4.8), 0.05), GOLD)
    # Fenster mit Gittern
    for sx in (-1, 1):
        b.window(sx * 3.2, 2.2, 1.3, 2.0, F, frame=SAND)
        b.bars(sx * 3.2, 2.2, 1.3, 2.0, F)
        b.add(box((sx * 3.2, -F - 0.05, 3.45), (1.8, 0.12, 0.3), (0.8, 1.0)), SAND)
        b.window(sx * 3.2, 6.1, 1.2, 1.6, F, frame=SAND)
        for u in (-2.2, 0.0, 2.2):
            b.window(u, 2.2, 1.1, 1.8, W / 2, side=90 * sx, frame=SAND)
            b.window(u, 6.0, 1.1, 1.5, W / 2, side=90 * sx, frame=SAND)
            tmp = Build("t")
            tmp.bars(u, 2.2, 1.1, 1.8, W / 2)
            for geo, c in tmp.parts:
                b.add(xf(geo, rot=(0, 0, 90 * sx)), c)
    # Umfeld
    for sx in (-1, 1):
        b.lantern(sx * 2.35, -F - 0.3, 3.0)
        b.lamp_post(sx * 4.2, -F - 2.2)
        b.add(box((sx * 3.2, -F - 0.5, 0.35), (1.6, 0.6, 0.5)), SAND)
        b.bush(sx * 3.2, -F - 0.5, 0.3, z=0.55)
    return b.finish()


# ============================================================== GOLDLADEN
def gold_shop():
    b = Build("Building_GoldShop")
    W, D, H = 6.5, 6.5, 3.8
    F = D / 2
    WALLC = "6E4424"
    b.add(box((0, 0, 0.15), (W + 0.3, D + 0.3, 0.3)), STONE)
    b.add(box((0, 0, 0.3 + H / 2), (W, D, H)), WALLC)
    # Stulpschalung vertikal
    for i in range(17):
        x = -W / 2 + 0.2 + i * (W - 0.4) / 16
        b.add(box((x, -F - 0.02, 0.3 + H / 2), (0.07, 0.04, H)), WOOD_DD)
    for sx in (-1, 1):
        for j in range(17):
            y = -D / 2 + 0.2 + j * (D - 0.4) / 16
            b.add(box((sx * (W / 2 + 0.02), y, 0.3 + H / 2), (0.04, 0.07, H)), WOOD_DD)
    # Giebel vorne
    ZR = 0.3 + H
    b.add(tri_y(0, 0, ZR, W, D, 2.2), WALLC)
    b.gable_roof_y(0, 0, ZR, W, D, 2.2, over=0.4, col="8E969B")
    b.add(xf(cyl((0, 0, 0), 0.3, 0.3, 0.06, 8), loc=(0, -F - 0.05, ZR + 1.45), rot=(90, 0, 0)), WOOD_L)
    # Grosses Schild am Giebel
    SZ = ZR + 0.4
    b.add(box((0, -F - 0.08, SZ), (3.9, 0.12, 1.05)), WOOD_DD)
    b.add(box((0, -F - 0.15, SZ), (3.7, 0.04, 0.88)), "1E1E1E")
    b.add(text(SIGNS["gold"], 0.52, (-0.35, -F - 0.18, SZ + 0.1), 0.05), GOLD)
    b.add(text(SIGNS["gold_sub"], 0.17, (-0.35, -F - 0.18, SZ - 0.28), 0.03), TRIM)
    b.add(box((1.3, -F - 0.2, SZ), (0.5, 0.1, 0.4), (0.6, 0.7)), GOLD)
    b.add(box((1.44, -F - 0.23, SZ - 0.12), (0.28, 0.08, 0.22), (0.6, 0.7)), GOLD)
    # Veranda mit gestreifter Markise
    b.add(box((0, -F - 0.9, 0.2), (W + 0.3, 1.8, 0.2)), WOOD_D)
    for x in (-W / 2 - 0.05, W / 2 + 0.05):
        b.add(box((x, -F - 1.7, 1.75), (0.16, 0.16, 2.9)), WOOD_DD)
    b.add(box((0, -F - 1.7, 3.2), (W + 0.3, 0.16, 0.16)), WOOD_DD)
    n = 9
    for i in range(n):
        x = -W / 2 - 0.15 + (i + 0.5) * (W + 0.3) / n
        col = GOLD if i % 2 == 0 else "8C2F23"
        b.add(xf(box((x, 0, 0), ((W + 0.3) / n, 1.9, 0.06)), loc=(0, -F - 0.9, 3.55), rot=(18, 0, 0)), col)
        b.add(box((x, -F - 1.83, 3.18), ((W + 0.3) / n, 0.04, 0.3)), col)
    # Tuer + Schaufenster
    b.door(-1.9, 0.3, 1.1, 2.3, F, col=WOOD_L, frame=WOOD_DD)
    b.add(box((-1.9, -F - 0.1, 2.05), (0.7, 0.04, 0.6)), GLASS)
    b.window(1.0, 1.8, 2.8, 1.8, F, frame=WOOD_L, cross=False)
    for x in (0.1, 1.9):
        b.add(box((x, -F - 0.09, 1.8), (0.06, 0.05, 1.8)), WOOD_L)
    b.window(1.0, 1.2, 2.8, 0.01, F, frame=WOOD_L, cross=False, sill=False)
    # Goldbarren im Fenster (Ablage)
    b.add(box((1.0, -F - 0.25, 0.95), (2.8, 0.35, 0.08)), WOOD_L)
    for i, (x, z) in enumerate(((0.3, 1.02), (0.62, 1.02), (0.94, 1.02), (0.46, 1.12), (0.78, 1.12), (0.62, 1.22))):
        b.add(box((x, -F - 0.25, z), (0.28, 0.14, 0.1), (0.8, 0.7)), GOLD)
    for x in (1.5, 1.75, 2.0, 1.65):
        b.add(box((x, -F - 0.25, 1.03), (0.12, 0.1, 0.1), (0.6, 0.7)), GOLD)
    # Tisch mit Goldwaage
    TX, TY = -0.3, -F - 1.1
    b.add(box((TX, TY, 1.05), (1.3, 0.6, 0.07)), WOOD_L)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(box((TX + sx * 0.55, TY + sy * 0.22, 0.65), (0.07, 0.07, 0.8)), WOOD_DD)
    b.add(box((TX, TY, 1.12), (0.25, 0.2, 0.06)), GOLD)
    b.add(box((TX, TY, 1.4), (0.05, 0.05, 0.55)), GOLD)
    b.add(box((TX, TY, 1.66), (0.7, 0.04, 0.04)), GOLD)
    for sx in (-1, 1):
        b.add(box((TX + sx * 0.33, TY, 1.5), (0.015, 0.015, 0.3)), IRON)
        b.add(cyl((TX + sx * 0.33, TY, 1.33), 0.08, 0.12, 0.04, 8), GOLD)
    b.add(box((TX + 0.33, TY, 1.39), (0.08, 0.06, 0.06), (0.6, 0.6)), GOLD)
    # Haengeschild seitlich
    b.add(box((W / 2 + 0.45, -F + 0.6, 3.3), (0.9, 0.06, 0.06)), IRON)
    b.add(box((W / 2 + 0.55, -F + 0.6, 2.9), (0.7, 0.06, 0.6)), WOOD_DD)
    b.add(box((W / 2 + 0.55, -F + 0.56, 2.9), (0.3, 0.04, 0.25), (0.6, 0.7)), GOLD)
    b.add(box((W / 2 + 0.55, -F + 0.64, 2.9), (0.3, 0.04, 0.25), (0.6, 0.7)), GOLD)
    # Deko
    b.crate(-3.5, -F - 1.2, 0.3, 0.55, 12)
    b.crate(-3.1, 0.6, 0.0, 0.7, -6)
    b.barrel(-3.3, 1.6)
    b.lantern(-2.75, -F - 0.25, 2.55)
    b.lantern(2.75, -F - 0.25, 2.55)
    # Pfanne + Schaufel an Wand
    b.add(xf(cyl((0, 0, 0), 0.18, 0.3, 0.07, 10), loc=(-W / 2 - 0.1, 0.4, 2.2), rot=(0, -90, 0)), IRON)
    b.add(xf(box((0, 0, 0), (0.04, 0.04, 1.3)), loc=(-W / 2 - 0.08, -0.6, 1.4), rot=(12, 0, 0)), WOOD_L)
    b.add(xf(box((0, 0, 0), (0.03, 0.26, 0.3)), loc=(-W / 2 - 0.08, -0.47, 0.6), rot=(12, 0, 0)), METAL)
    return b.finish()


# ================================================================== Export
BUILDERS = [saloon, townhall, gas_station, bank, gold_shop]
objs = []
for fn in BUILDERS:
    ob = fn()
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, ob.name + ".fbx"), use_selection=True,
        object_types={"MESH"}, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", bake_space_transform=True,
    )
    print(ob.name, len(ob.data.polygons), "faces")
    objs.append(ob)

# ================================================================= Vorschau
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.62, 0.72, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.8

ground = Build("Ground")
ground.add(box((0, 0, -0.05), (200, 200, 0.1)), "BCA07C")
ground.finish()

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.5
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
scene.collection.objects.link(sun)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scene.collection.objects.link(cam)
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
con = cam.constraints.new("TRACK_TO")
con.target = target
scene.camera = cam

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = int(os.environ.get("SAMPLES", "40"))
scene.cycles.use_denoising = False
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.view_settings.view_transform = "Standard"

xs = [-34, -17, 0, 16, 30]
for ob, x in zip(objs, xs):
    ob.location.x = x

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "buildings.blend"))

if os.environ.get("RENDER", "1") == "1":
    shots = [("preview_all", (-2, -52, 20), (-2, 0, 3), 24)]
    for ob, x in zip(objs, xs):
        short = ob.name.replace("Building_", "")
        shots.append((f"preview_{short}", (x + 9, -21, 7.5), (x, -2, 3.2), 32))
    only = os.environ.get("ONLY")
    for name, cl, tl, lens in shots:
        if only and only not in name:
            continue
        cam.location = cl
        target.location = tl
        cam.data.lens = lens
        scene.render.filepath = os.path.join(OUT, name + ".png")
        bpy.ops.render.render(write_still=True)
print("DONE")
