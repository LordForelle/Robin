"""Erzeugt Low-Poly Arbeiter + Werkzeuge fuer den Goldgraeber-Simulator.

Ausfuehren:  blender -b -P build_workers.py   (oder: python3 build_workers.py mit pip-Paket bpy)
Ausgabe:     FBX-Dateien, workers.blend, preview.png im selben Ordner.
"""
import math
import os

import bpy

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- Szene leeren
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


# ------------------------------------------------------------------ Materialien
_mats = {}


def mat(name, rgb):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*[c ** 2.2 for c in rgb], 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    m.diffuse_color = (*[c ** 2.2 for c in rgb], 1.0)
    _mats[name] = m
    return m


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ------------------------------------------------------------ Geometrie-Helfer
def box_geo(c, s, top=(1.0, 1.0)):
    """Quader um Mittelpunkt c mit Groesse s; Oberseite um top skaliert (Taper)."""
    cx, cy, cz = c
    hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
    tx, ty = hx * top[0], hy * top[1]
    v = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
         (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
         (cx - tx, cy - ty, cz + hz), (cx + tx, cy - ty, cz + hz),
         (cx + tx, cy + ty, cz + hz), (cx - tx, cy + ty, cz + hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


def xbox_geo(x0, x1, cy, cz, sy, sz, end=1.0):
    """Quader entlang X (fuer Arme in T-Pose), Ende um end skaliert."""
    v = [(x0, cy - sy / 2, cz - sz / 2), (x0, cy + sy / 2, cz - sz / 2),
         (x0, cy + sy / 2, cz + sz / 2), (x0, cy - sy / 2, cz + sz / 2)]
    v += [(x1, cy + (y - cy) * end, cz + (z - cz) * end) for (_, y, z) in v]
    if x1 > x0:
        f = [(0, 1, 2, 3)[::-1], (4, 5, 6, 7), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    else:
        f = [(0, 1, 2, 3), (7, 6, 5, 4), (1, 5, 4, 0), (2, 6, 5, 1), (3, 7, 6, 2), (0, 4, 7, 3)]
    return v, f


def cyl_geo(c, r0, r1, h, n=8, cap_top=True, rot=0.0):
    """Zylinder/Kegelstumpf entlang Z, Boden bei c[2]."""
    cx, cy, cz = c
    v, f = [], []
    for i in range(n):
        a = 2 * math.pi * i / n + rot
        v.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cz))
    for i in range(n):
        a = 2 * math.pi * i / n + rot
        v.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a), cz + h))
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    f.append(tuple(reversed(range(n))))
    if cap_top:
        f.append(tuple(range(n, 2 * n)))
    return v, f


def ycyl_geo(c, r, length, n=8):
    """Zylinder entlang Y (z.B. Rad)."""
    v, f = cyl_geo((0, 0, -length / 2), r, r, length, n)
    v = [(c[0] + x, c[1] + z, c[2] + y) for (x, y, z) in v]
    return v, [tuple(reversed(face)) for face in f]


def xcyl_geo(c, r, length, n=8):
    v, f = cyl_geo((0, 0, -length / 2), r, r, length, n)
    v = [(c[0] + z, c[1] + x, c[2] + y) for (x, y, z) in v]
    return v, f


def part(name, geo, material, bone=None, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(geo[0], [], geo[1])
    me.validate()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    (coll or scene.collection).objects.link(ob)
    if bone:
        vg = ob.vertex_groups.new(name=bone)
        vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    return ob


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    # doppelte Vertices innerhalb der Teile zusammenfuehren, Normalen nach aussen
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


# ------------------------------------------------------------------- Skelett
BONES = [
    # name, head, tail, parent
    ("Hips", (0, 0, 0.92), (0, 0, 1.02), None),
    ("Spine", (0, 0, 1.02), (0, 0, 1.20), "Hips"),
    ("Chest", (0, 0, 1.20), (0, 0, 1.42), "Spine"),
    ("Neck", (0, 0, 1.42), (0, 0, 1.50), "Chest"),
    ("Head", (0, 0, 1.50), (0, 0, 1.82), "Neck"),
]
for s, sx in (("L", 1), ("R", -1)):
    BONES += [
        (f"Shoulder.{s}", (0.05 * sx, 0, 1.38), (0.20 * sx, 0, 1.38), "Chest"),
        (f"UpperArm.{s}", (0.20 * sx, 0, 1.38), (0.48 * sx, 0, 1.38), f"Shoulder.{s}"),
        (f"LowerArm.{s}", (0.48 * sx, 0, 1.38), (0.74 * sx, 0, 1.38), f"UpperArm.{s}"),
        (f"Hand.{s}", (0.74 * sx, 0, 1.38), (0.88 * sx, 0, 1.38), f"LowerArm.{s}"),
        (f"UpperLeg.{s}", (0.10 * sx, 0, 0.92), (0.10 * sx, 0, 0.50), "Hips"),
        (f"LowerLeg.{s}", (0.10 * sx, 0, 0.50), (0.10 * sx, 0, 0.10), f"UpperLeg.{s}"),
        (f"Foot.{s}", (0.10 * sx, 0, 0.10), (0.10 * sx, -0.14, 0.03), f"LowerLeg.{s}"),
    ]


def make_armature(name, coll):
    arm = bpy.data.armatures.new(name + "_Rig")
    rig = bpy.data.objects.new(name, arm)
    coll.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for bn, h, t, p in BONES:
        eb = arm.edit_bones.new(bn)
        eb.head, eb.tail = h, t
        if p:
            eb.parent = arm.edit_bones[p]
            eb.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.display_type = "STICK"
    return rig


# ------------------------------------------------------------------- Arbeiter
def build_worker(name, cfg, coll):
    C = {k: mat(f"{k}_{v}", hexc(v)) for k, v in cfg["colors"].items()}
    P = []

    def add(geo, m, bone):
        P.append(part(f"{name}_{bone}_{len(P)}", geo, C[m], bone, coll))

    for s, sx in (("L", 1), ("R", -1)):
        x = 0.10 * sx
        # Stiefel
        add(box_geo((x, -0.03, 0.06), (0.14, 0.28, 0.12), (0.95, 0.9)), "boots", f"Foot.{s}")
        add(box_geo((x, -0.155, 0.015), (0.145, 0.03, 0.03)), "sole", f"Foot.{s}")
        # Beine
        add(box_geo((x, 0, 0.16), (0.14, 0.15, 0.10)), "boots", f"LowerLeg.{s}")
        add(box_geo((x, 0, 0.35), (0.13, 0.14, 0.30), (1.1, 1.08)), "pants", f"LowerLeg.{s}")
        add(box_geo((x, 0, 0.71), (0.155, 0.17, 0.42), (1.12, 1.08)), "pants", f"UpperLeg.{s}")
        # Arme (T-Pose)
        add(xbox_geo(0.19 * sx, 0.49 * sx, 0, 1.38, 0.13, 0.13, 0.9), "shirt", f"UpperArm.{s}")
        lower = "shirt" if cfg.get("long_sleeves") else "skin"
        add(xbox_geo(0.49 * sx, 0.74 * sx, 0, 1.38, 0.105, 0.105, 0.9), lower, f"LowerArm.{s}")
        if cfg.get("long_sleeves"):
            add(xbox_geo(0.70 * sx, 0.745 * sx, 0, 1.38, 0.115, 0.115), "shirt", f"LowerArm.{s}")
        add(xbox_geo(0.74 * sx, 0.87 * sx, 0, 1.38, 0.10, 0.08, 0.95), "gloves", f"Hand.{s}")
        add(xbox_geo(0.75 * sx, 0.80 * sx, -0.06, 1.39, 0.04, 0.04), "gloves", f"Hand.{s}")  # Daumen
        # Schultern (Hemd)
        add(box_geo((0.17 * sx, 0, 1.38), (0.10, 0.16, 0.12)), "shirt", f"Shoulder.{s}")

    # Huefte + Guertel
    add(box_geo((0, 0, 0.95), (0.36, 0.20, 0.14)), "pants", "Hips")
    add(box_geo((0, 0, 1.02), (0.37, 0.21, 0.04)), "belt", "Hips")
    add(box_geo((0, -0.107, 1.02), (0.06, 0.01, 0.035)), "buckle", "Hips")

    # Torso
    add(box_geo((0, 0, 1.13), (0.35, 0.20, 0.22), (1.06, 1.05)), "shirt", "Spine")
    add(box_geo((0, 0, 1.32), (0.39, 0.22, 0.20), (1.08, 1.0)), "shirt", "Chest")

    if cfg.get("vest"):
        # Warnweste: Schale ueber dem Torso, vorne offen (Hemdstreifen sichtbar)
        for sx in (1, -1):
            add(box_geo((0.105 * sx, 0, 1.13), (0.17, 0.215, 0.23), (1.08, 1.05)), "vest", "Spine")
            add(box_geo((0.115 * sx, 0, 1.33), (0.18, 0.235, 0.19), (1.08, 1.0)), "vest", "Chest")
            add(box_geo((0.105 * sx, 0, 1.10), (0.172, 0.222, 0.03)), "stripe", "Spine")
            add(box_geo((0.118 * sx, 0, 1.27), (0.185, 0.24, 0.03)), "stripe", "Chest")
    if cfg.get("overalls"):
        add(box_geo((0, -0.005, 1.15), (0.33, 0.205, 0.26)), "pants", "Spine")
        add(box_geo((0, -0.103, 1.24), (0.20, 0.01, 0.14)), "pants", "Chest")
        for sx in (1, -1):
            add(box_geo((0.085 * sx, 0, 1.38), (0.04, 0.23, 0.04)), "pants", "Chest")
            add(box_geo((0.085 * sx, -0.12, 1.30), (0.035, 0.01, 0.035)), "buckle", "Chest")

    # Kragen + Hals
    add(box_geo((0, 0, 1.43), (0.24, 0.16, 0.04)), "shirt", "Chest")
    add(cyl_geo((0, 0, 1.44), 0.06, 0.06, 0.08, 6), "skin", "Neck")

    # Kopf
    add(box_geo((0, 0, 1.635), (0.23, 0.23, 0.27), (1.0, 0.95)), "skin", "Head")
    for sx in (1, -1):
        add(box_geo((0.05 * sx, -0.117, 1.65), (0.035, 0.01, 0.04)), "eyes", "Head")
        add(box_geo((0.05 * sx, -0.117, 1.69), (0.06, 0.01, 0.015)), "hair", "Head")  # Augenbrauen
        add(box_geo((0.118 * sx, 0.0, 1.63), (0.02, 0.05, 0.06)), "skin", "Head")  # Ohren
    add(box_geo((0, -0.128, 1.61), (0.04, 0.04, 0.06), (0.8, 0.8)), "skin", "Head")  # Nase
    if cfg.get("beard"):
        add(box_geo((0, -0.02, 1.535), (0.24, 0.21, 0.09), (1.0, 1.0)), "hair", "Head")
        add(box_geo((0, -0.12, 1.575), (0.12, 0.02, 0.025)), "hair", "Head")  # Schnurrbart
        for sx in (1, -1):
            add(box_geo((0.112 * sx, -0.02, 1.58), (0.02, 0.18, 0.08)), "hair", "Head")
    elif cfg.get("mustache"):
        add(box_geo((0, -0.12, 1.575), (0.12, 0.02, 0.03)), "hair", "Head")
    else:
        add(box_geo((0, -0.117, 1.565), (0.07, 0.01, 0.012)), "eyes", "Head")  # Mund
    # Haare hinten/seitlich
    add(box_geo((0, 0.03, 1.72), (0.245, 0.19, 0.10)), "hair", "Head")

    # Kopfbedeckung
    hat = cfg.get("hat", "hardhat")
    if hat == "hardhat":
        add(cyl_geo((0, 0.0, 1.735), 0.155, 0.135, 0.02, 8, rot=math.pi / 8), "hat", "Head")
        add(cyl_geo((0, 0.0, 1.755), 0.135, 0.09, 0.09, 8, rot=math.pi / 8), "hat", "Head")
        add(box_geo((0, 0.0, 1.85), (0.035, 0.22, 0.03)), "hat", "Head")  # Mittelrippe
        add(box_geo((0, -0.14, 1.745), (0.2, 0.08, 0.02)), "hat", "Head")  # Schirm vorne
        add(box_geo((0, -0.132, 1.79), (0.07, 0.01, 0.04)), "lamp", "Head")  # Stirnlampe
    elif hat == "cowboy":
        add(cyl_geo((0, 0, 1.745), 0.23, 0.22, 0.02, 8, rot=math.pi / 8), "hat", "Head")
        add(cyl_geo((0, 0, 1.765), 0.13, 0.11, 0.12, 8, rot=math.pi / 8), "hat", "Head")
        add(cyl_geo((0, 0, 1.765), 0.132, 0.13, 0.025, 8, rot=math.pi / 8), "hatband", "Head")
    elif hat == "beanie":
        add(cyl_geo((0, 0, 1.72), 0.128, 0.128, 0.05, 8, rot=math.pi / 8), "hatband", "Head")
        add(cyl_geo((0, 0, 1.77), 0.122, 0.07, 0.10, 8, rot=math.pi / 8), "hat", "Head")

    body = join(P, name + "_Mesh")
    rig = make_armature(name, coll)
    body.parent = rig
    mod = body.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    return rig, body


# ------------------------------------------------------------------ Werkzeuge
def build_tool(name, parts, coll):
    objs = [part(f"{name}_{i}", g, mat(f"tool_{c}", hexc(c)), None, coll) for i, (g, c) in enumerate(parts)]
    return join(objs, name)


WOOD, METAL, DARK = "B07A45", "9AA2A8", "4A4A4A"

TOOLS = {
    # Ursprung = Griffpunkt der Hand
    "Tool_Shovel": [
        (box_geo((0, 0, 0.30), (0.04, 0.04, 1.00)), WOOD),
        (box_geo((0, 0, 0.82), (0.14, 0.035, 0.035)), DARK),
        (box_geo((0, 0, -0.22), (0.05, 0.05, 0.08)), DARK),
        (box_geo((0, 0, -0.38), (0.24, 0.025, 0.26), (1.0, 1.0)), METAL),
        (box_geo((0, 0, -0.54), (0.24, 0.025, 0.06), (1.0, 1.0)), METAL),
    ],
    "Tool_Pickaxe": [
        (box_geo((0, 0, 0.25), (0.045, 0.045, 0.85)), WOOD),
        (box_geo((0, 0, 0.66), (0.10, 0.06, 0.08)), DARK),
        (xbox_geo(0.05, 0.36, 0, 0.66, 0.05, 0.06, 0.25), METAL),
        (xbox_geo(-0.05, -0.30, 0, 0.66, 0.05, 0.07, 0.5), METAL),
    ],
    "Tool_GoldPan": [
        (cyl_geo((0, 0, 0), 0.10, 0.20, 0.07, 10, cap_top=False), DARK),
        (cyl_geo((0, 0, 0.069), 0.20, 0.215, 0.012, 10, cap_top=False), DARK),
        (cyl_geo((0, 0, 0.005), 0.07, 0.07, 0.01, 8), "E8B923"),  # Goldflitter
    ],
    "Tool_Sledgehammer": [
        (box_geo((0, 0, 0.25), (0.045, 0.045, 0.85)), WOOD),
        (xbox_geo(-0.12, 0.12, 0, 0.72, 0.10, 0.10), DARK),
    ],
    "Prop_Bucket": [
        (cyl_geo((0, 0, 0), 0.12, 0.15, 0.30, 8, cap_top=False), "D9822B"),
        (xbox_geo(-0.15, 0.15, 0, 0.36, 0.015, 0.015), DARK),
        (box_geo((0.145, 0, 0.33), (0.015, 0.015, 0.07)), DARK),
        (box_geo((-0.145, 0, 0.33), (0.015, 0.015, 0.07)), DARK),
    ],
    "Prop_Wheelbarrow": [
        (box_geo((0, -0.05, 0.42), (0.55, 0.75, 0.25), (1.25, 1.3)), "3C7A3E"),
        (box_geo((0, -0.05, 0.56), (0.66, 0.94, 0.03)), "6B4A2E"),  # Erdladung
        (box_geo((0, -0.05, 0.60), (0.40, 0.60, 0.06), (0.6, 0.6)), "6B4A2E"),
        (box_geo((0.34, -0.05, 0.57), (0.04, 0.98, 0.05)), "3C7A3E"),  # Rand
        (box_geo((-0.34, -0.05, 0.57), (0.04, 0.98, 0.05)), "3C7A3E"),
        (box_geo((0, 0.47, 0.57), (0.72, 0.04, 0.05)), "3C7A3E"),
        (box_geo((0, -0.57, 0.57), (0.72, 0.04, 0.05)), "3C7A3E"),
        (ycyl_geo((0, -0.55, 0.18), 0.18, 0.08, 10), DARK),
        (xbox_geo(-0.04, 0.04, -0.55, 0.18, 0.06, 0.06), METAL),
        (box_geo((0.22, 0.20, 0.35), (0.04, 1.30, 0.04)), METAL),
        (box_geo((-0.22, 0.20, 0.35), (0.04, 1.30, 0.04)), METAL),
        (box_geo((0.22, 0.12, 0.15), (0.04, 0.04, 0.30)), METAL),
        (box_geo((-0.22, 0.12, 0.15), (0.04, 0.04, 0.30)), METAL),
        (box_geo((0.22, 0.85, 0.35), (0.05, 0.14, 0.05)), DARK),
        (box_geo((-0.22, 0.85, 0.35), (0.05, 0.14, 0.05)), DARK),
    ],
    "Prop_GoldNugget": [
        (box_geo((0, 0, 0.025), (0.07, 0.05, 0.05), (0.6, 0.7)), "E8B923"),
        (box_geo((0.03, 0.01, 0.02), (0.04, 0.04, 0.04), (0.5, 0.6)), "E8B923"),
    ],
}

# ------------------------------------------------------------------ Varianten
WORKERS = {
    "Worker_Miner": dict(hat="hardhat", vest=True, colors=dict(
        skin="E8B894", hair="5A3A22", eyes="1E1E1E", shirt="3F6FB5", pants="3A4F7A",
        boots="6B4526", sole="2E2E2E", gloves="C9A36A", belt="4A3020", buckle="C8C8C8",
        vest="F28C28", stripe="E6E6E6", hat="F2C12E", lamp="FFF6C0")),
    "Worker_Foreman": dict(hat="hardhat", vest=True, mustache=True, long_sleeves=True, colors=dict(
        skin="C68E62", hair="2B2B2B", eyes="1E1E1E", shirt="E4E4E4", pants="4A4A4A",
        boots="3A2A1E", sole="1E1E1E", gloves="8A8A8A", belt="2E2E2E", buckle="D4AF37",
        vest="D8E83A", stripe="E6E6E6", hat="F5F5F5", lamp="FFF6C0")),
    "Worker_Prospector": dict(hat="cowboy", overalls=True, beard=True, long_sleeves=True, colors=dict(
        skin="EAC09C", hair="8A8A8A", eyes="1E1E1E", shirt="B83A32", pants="4D6A96",
        boots="5C3A1E", sole="2E2E2E", gloves="A0703F", belt="3E2A1A", buckle="D4AF37",
        hat="7A5230", hatband="3E2A1A")),
    "Worker_Digger": dict(hat="beanie", vest=True, beard=True, colors=dict(
        skin="7A4E32", hair="1E1A18", eyes="111111", shirt="5E6B45", pants="5B4A3A",
        boots="4A3322", sole="1E1E1E", gloves="D18A2E", belt="2E2E2E", buckle="B0B0B0",
        vest="F28C28", stripe="E6E6E6", hat="2F4F6F", hatband="24394F")),
}


def export_fbx(objs, path, armature=True):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True,
        object_types={"ARMATURE", "MESH"} if armature else {"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
        add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X",
        bake_anim=False, use_armature_deform_only=True,
        bake_space_transform=not armature,
    )


placed = []
for i, (wname, cfg) in enumerate(WORKERS.items()):
    coll = bpy.data.collections.new(wname)
    scene.collection.children.link(coll)
    rig, body = build_worker(wname, cfg, coll)
    export_fbx([rig, body], os.path.join(OUT, wname + ".fbx"))
    rig.location.x = (i - 1.5) * 1.95
    placed.append(rig)

tcoll = bpy.data.collections.new("Tools")
scene.collection.children.link(tcoll)
tool_pos = {
    "Tool_Shovel": (-2.2, -1.4, 0.54), "Tool_Pickaxe": (-1.3, -1.4, 0.08),
    "Tool_GoldPan": (-0.3, -1.4, 0.0), "Tool_Sledgehammer": (0.5, -1.4, 0.08),
    "Prop_Bucket": (1.2, -1.4, 0.0), "Prop_Wheelbarrow": (2.3, -1.6, 0.0),
    "Prop_GoldNugget": (0.0, -1.3, 0.1),
}
for tname, parts in TOOLS.items():
    t = build_tool(tname, parts, tcoll)
    export_fbx([t], os.path.join(OUT, tname + ".fbx"), armature=False)
    t.location = tool_pos[tname]
bpy.data.objects["Prop_GoldNugget"].location = (-0.14, -1.35, 0.0)

# ------------------------------------------------------------------ Vorschau
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.36, 0.24, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

ground_m = mat("ground", hexc("BCA07C"))
g = part("Ground", box_geo((0, 0, -0.01), (30, 30, 0.02)), ground_m)

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.5
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
scene.collection.objects.link(sun)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.lens = 50
cam.location = (3.4, -10.6, 3.9)
scene.collection.objects.link(cam)
target = bpy.data.objects.new("Target", None)
target.location = (0.1, -0.6, 0.8)
scene.collection.objects.link(target)
con = cam.constraints.new("TRACK_TO")
con.target = target
scene.camera = cam

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = int(os.environ.get("SAMPLES", "48"))
scene.cycles.use_denoising = False
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.filepath = os.path.join(OUT, "preview.png")
scene.view_settings.view_transform = "Standard"

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "workers.blend"))
if os.environ.get("RENDER", "1") == "1":
    bpy.ops.render.render(write_still=True)
print("DONE")
