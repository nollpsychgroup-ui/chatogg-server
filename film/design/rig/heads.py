"""Previs face rigs for THE QUIET CAR (Character Designer).

Builds a stylised, painted-ready head for NOOR, KAI, BEA or WALTER, with the controls from
design/expressions/face-rig.md as custom properties on one root empty. Drivers connect those
properties to the parts (lid pivots, eye pivots, shape keys), so animators key only the root.

Use from the TA's build (bpy, Blender 5.3):

    from heads import build_head, place, set_expression
    root = build_head("BEA", collection="CHAR_BEA", mats={"skin": ..., "hair": ...})   # mats optional
    place(root, head_centre, forward)            # forward = the character's facing vector
    set_expression(root, {"lid_up": 0.0, "tension": 0.7, "brow_in": -0.15}, frame=120)

Local frame of the root: +Y forward (out of the face), +Z up, +X = character's RIGHT.
So `_L` controls act on -X (the character's left), `_R` on +X.
The root sits at the centre of the head (mid-height, mid-depth), matching the TA's head_c.

Nothing here paints light: materials are flat albedo (or the TA's PaintSurface ones passed in).
The corneas are real glossy caps, so the panel row shows up as catchlights by itself.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PALETTE = os.path.join(os.path.dirname(HERE), "palette.json")

# Head ellipsoid half-sizes in metres (x half-width, y half-depth, z half-height), jaw taper, extras.
SPEC = {
    "NOOR":   dict(key="noor",   r=(0.074, 0.094, 0.114), jaw=0.72, chin_fwd=0.006, eye_r=0.0135, brow_th=0.0042, mouth_w=0.024, lip_th=1.0),
    "KAI":    dict(key="kai",    r=(0.077, 0.095, 0.115), jaw=0.78, chin_fwd=0.006, eye_r=0.0135, brow_th=0.0048, mouth_w=0.025, lip_th=0.9),
    "BEA":    dict(key="bea",    r=(0.079, 0.093, 0.112), jaw=0.80, chin_fwd=0.004, eye_r=0.0135, brow_th=0.0042, mouth_w=0.026, lip_th=1.15,
                  sclera="#F3F0E8", lid_ink="#0E0907", lid_albedo="#6E4A38", ink_band=0.30),
    "WALTER": dict(key="walter", r=(0.071, 0.095, 0.120), jaw=0.72, chin_fwd=0.007, eye_r=0.0130, brow_th=0.0060, mouth_w=0.024, lip_th=0.75),
}

CONTROLS = {  # name: (default, min, max)  -- see face-rig.md
    "lid_up_L": (0.8, 0, 1.1), "lid_up_R": (0.8, 0, 1.1), "lid_low_L": (0, 0, 1), "lid_low_R": (0, 0, 1), "tension": (0, 0, 1),
    "brow_in_L": (0, -1, 1), "brow_in_R": (0, -1, 1), "brow_out_L": (0, -1, 1), "brow_out_R": (0, -1, 1),
    "smile_L": (0, -1, 1), "smile_R": (0, -1, 1), "press": (0, 0, 1), "jaw": (0, 0, 1), "chin": (0, 0, 1),
    "naso": (0, 0, 1), "gaze_x": (0, -1, 1), "gaze_y": (0, -1, 1), "tear": (0, 0, 1),
}
NEUTRAL = {
    "NOOR": dict(lid_up=0.82, naso=0.2), "KAI": dict(lid_up=0.7, naso=0.1),
    "BEA": dict(lid_up=0.7, naso=0.35, lid_low=0.1), "WALTER": dict(lid_up=0.62, naso=0.6),
}
EYE_X, EYE_Z = 0.032, 0.012  # eye centres: +-x, z above head centre
BROW_Z = 0.034


# ------------------------------------------------------------------ palette and materials

def _palette():
    with open(PALETTE) as f:
        return json.load(f)["colours"]


def _lin(hexv):
    h = hexv.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def _mat(name, rgb, rough=0.85, transmission=0.0, coat=0.0, ior=1.45):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = tuple(rgb) + (1,)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["IOR"].default_value = ior
    if transmission == 0 and rough > 0.5:
        b.inputs["Specular IOR Level"].default_value = 0.12  # matte gouache: almost no sheen
    m.diffuse_color = tuple(rgb) + (1,)
    return m


def default_materials(name):
    """Flat albedo materials from palette.json. The TA can pass PaintSurface materials instead."""
    P = _palette()
    s = SPEC[name]
    k = s["key"]

    def c(key):
        return tuple(P[key]["linear"])
    return {
        "skin": _mat(f"hd_{k}_skin", c(f"{k}/skin")),
        "lid": _mat(f"hd_{k}_lid", _lin(s["lid_albedo"]) if "lid_albedo" in s else c(f"{k}/skin")),
        "lid_ink": _mat(f"hd_{k}_lidink", _lin(s.get("lid_ink", "#24180F")), rough=0.6),
        "hair": _mat(f"hd_{k}_hair", c(f"{k}/hair")),
        "brow": _mat(f"hd_{k}_brow", _lin({"noor": "#231B18", "kai": "#1E1A18", "bea": "#231915", "walter": "#B9B3AA"}[k])),
        "lips": _mat(f"hd_{k}_lips", c(f"{k}/lips")),
        "sclera": _mat(f"hd_{k}_sclera", _lin(s.get("sclera", "#E9E6DE")), rough=0.35),
        "iris": _mat(f"hd_{k}_iris", c(f"{k}/iris"), rough=0.4),
        "pupil": _mat("hd_pupil", _lin("#0C0908"), rough=0.4),
        "cornea": _mat("hd_cornea", (1, 1, 1), rough=0.02, transmission=1.0, ior=1.376),
        "mouth": _mat("hd_mouth", _lin("#2E1E1A")),
        "teeth": _mat("hd_teeth", _lin("#D9D2C6"), rough=0.5),
        "tear": _mat("hd_tear", (1, 1, 1), rough=0.02, transmission=1.0, ior=1.33),
    }


# ------------------------------------------------------------------ geometry helpers

def _link(ob, collection):
    if isinstance(collection, str):
        col = bpy.data.collections.get(collection)
        if col is None:
            col = bpy.data.collections.new(collection)
            bpy.context.scene.collection.children.link(col)
    elif collection is None:
        col = bpy.context.scene.collection
    else:
        col = collection
    col.objects.link(ob)


def _mesh_obj(name, bm, mats, collection, parent, smooth=True, pass_index=1):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.parent = parent
    ob.pass_index = pass_index
    _link(ob, collection)
    return ob


def _empty(name, parent, loc, collection):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.01
    e.parent = parent
    e.location = loc
    _link(e, collection)
    return e


def _sphere(r, segs=24, rings=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    return bm


class Skull:
    """Analytic head surface: an ellipsoid whose half-width tapers toward the jaw."""

    def __init__(self, s):
        self.rx, self.ry, self.rz = s["r"]
        self.jaw = s["jaw"]
        self.chin_fwd = s["chin_fwd"]

    def taper(self, zn):  # zn = z / rz in [-1, 1]
        if zn >= -0.15:
            return 1.0
        t = min(1.0, (-0.15 - zn) / 0.85)
        return 1.0 - (1.0 - self.jaw) * t * t

    def shape(self, v):
        """Map a unit-sphere point to the head surface."""
        zn = v.z
        x = v.x * self.rx * self.taper(zn)
        y = v.y * self.ry
        if zn < -0.5 and v.y > 0:
            y += self.chin_fwd * (-0.5 - zn) * 2 * v.y
        if -0.45 < zn < 0.1 and v.y > 0.2:  # cheekbones
            x *= 1.0 + 0.05 * math.cos((zn + 0.175) / 0.275 * math.pi / 2)
        return Vector((x, y, v.z * self.rz))

    def front_y(self, x, z):
        zn = max(-0.999, min(0.999, z / self.rz))
        w = self.rx * self.taper(zn)
        q = 1 - (x / w) ** 2 - zn ** 2
        return self.ry * math.sqrt(max(q, 0.0))


def _strip(skull, pts_xz, width_fn, lift=0.0015, normal_push=0.0):
    """A thin ribbon lying on the face surface along pts_xz; returns (bm, columns of vert pairs)."""
    bm = bmesh.new()
    cols = []
    for i, (x, z) in enumerate(pts_xz):
        w = width_fn(i)
        top = Vector((x, skull.front_y(x, z + w / 2) + lift, z + w / 2))
        bot = Vector((x, skull.front_y(x, z - w / 2) + lift, z - w / 2))
        cols.append((bm.verts.new(top), bm.verts.new(bot)))
    for a, b in zip(cols, cols[1:]):
        bm.faces.new((a[1], b[1], b[0], a[0]))
    return bm, cols


# ------------------------------------------------------------------ drivers

def _drive(owner, path, index, root, expr, props):
    fc = owner.driver_add(path, index) if index is not None else owner.driver_add(path)
    d = fc.driver
    d.type = "SCRIPTED"
    for p in props:
        v = d.variables.new()
        v.name = p
        v.type = "SINGLE_PROP"
        v.targets[0].id = root
        v.targets[0].data_path = f'["{p}"]'
    d.expression = expr
    return fc


def _shape_keys(ob, keys):
    """keys: {name: (offsets dict vert_index -> Vector, slider_min)}"""
    ob.shape_key_add(name="Basis")
    out = {}
    for name, (offs, smin) in keys.items():
        sk = ob.shape_key_add(name=name, from_mix=False)
        sk.slider_min = smin
        for i, d in offs.items():
            sk.data[i].co = sk.data[i].co + d
        out[name] = sk
    return out


# ------------------------------------------------------------------ build

def build_head(name, collection=None, mats=None, pass_face=1, pass_hair=2):
    """Build the head for NOOR/KAI/BEA/WALTER. Returns the root empty (place it with place())."""
    name = name.upper()
    s = SPEC[name]
    M = default_materials(name)
    if mats:
        M.update({k: v for k, v in mats.items() if v is not None})
    skull = Skull(s)
    root = bpy.data.objects.new(f"{name}_HEADRIG", None)
    root.empty_display_type = "SPHERE"
    root.empty_display_size = 0.12
    _link(root, collection)
    for k, (dv, lo, hi) in CONTROLS.items():
        root[k] = float(dv)
        ui = root.id_properties_ui(k)
        ui.update(min=lo, max=hi, soft_min=lo, soft_max=hi)
    set_expression(root, NEUTRAL[name])

    # skull
    bm = _sphere(1.0, 32, 22)
    for v in bm.verts:
        v.co = skull.shape(v.co)
    _mesh_obj(f"{name}_HD_SKULL", bm, [M["skin"]], collection, root, pass_index=pass_face)

    # neck stub (the TA's neck limb meets it)
    # nose: a soft wedge
    bm = _sphere(1.0, 16, 10)
    for v in bm.verts:
        c = v.co
        v.co = Vector((c.x * 0.0115 * (0.75 + 0.35 * (1 - c.z) / 2), c.y * 0.010 + (0.004 if c.y > 0 else 0) * (0.5 - 0.5 * c.z), c.z * 0.019))
    nz = -0.020
    bm_obj = _mesh_obj(f"{name}_HD_NOSE", bm, [M["skin"]], collection, root, pass_index=pass_face)
    bm_obj.location = (0, skull.front_y(0, nz) - 0.002, nz)

    # ears
    for sx in (-1, 1):
        bm = _sphere(1.0, 12, 8)
        for v in bm.verts:
            v.co = Vector((v.co.x * 0.008, v.co.y * 0.016, v.co.z * (0.032 if name != "WALTER" else 0.037)))
        e = _mesh_obj(f"{name}_HD_EAR_{'R' if sx > 0 else 'L'}", bm, [M["skin"]], collection, root, pass_index=pass_face)
        e.location = (sx * skull.rx * 0.97, -0.006, -0.004)

    # eyes
    for side, sx in (("L", -1), ("R", 1)):
        _eye(name, side, sx, s, skull, M, root, collection, pass_face)

    # brows
    for side, sx in (("L", -1), ("R", 1)):
        _brow(name, side, sx, s, skull, M, root, collection, pass_face)

    _mouth(name, s, skull, M, root, collection, pass_face)
    _hair(name, s, skull, M, root, collection, pass_hair)

    # tear: a wet line on the character's right cheek (camera side in the confession)
    bm = _sphere(1.0, 10, 8)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.0012, v.co.y * 0.001, v.co.z * 0.012))
    tx, tz = EYE_X + 0.006, EYE_Z - 0.026
    tear = _mesh_obj(f"{name}_HD_TEAR", bm, [M["tear"]], collection, root, pass_index=pass_face)
    tear.location = (tx, skull.front_y(tx, tz) + 0.0008, tz)
    for i in range(3):
        _drive(tear, "scale", i, root, "max(0.001, tear)", ["tear"])
    return root


def _eye(name, side, sx, s, skull, M, root, collection, pf):
    r = s["eye_r"]
    ex, ez = sx * EYE_X, EYE_Z
    ey = skull.front_y(ex, ez) - r + 0.003  # protrudes ~3 mm: shallow sockets, eyes catch top light
    piv = _empty(f"{name}_HD_EYE_{side}", root, (ex, ey, ez), collection)
    # eyeball (sclera) + iris + pupil + cornea cap, all on the gaze pivot
    bm = _sphere(r, 24, 16)
    _mesh_obj(f"{name}_HD_SCLERA_{side}", bm, [M["sclera"]], collection, piv, pass_index=pf)
    bm = _sphere(1.0, 20, 12)
    for v in bm.verts:
        v.co = Vector((v.co.x * r * 0.47, v.co.y * r * 0.12 + r * 0.93, v.co.z * r * 0.47))
    _mesh_obj(f"{name}_HD_IRIS_{side}", bm, [M["iris"]], collection, piv, pass_index=pf)
    bm = _sphere(1.0, 16, 10)
    for v in bm.verts:
        v.co = Vector((v.co.x * r * 0.21, v.co.y * r * 0.06 + r * 1.035, v.co.z * r * 0.21))
    _mesh_obj(f"{name}_HD_PUPIL_{side}", bm, [M["pupil"]], collection, piv, pass_index=pf)
    bm = _sphere(r * 1.03, 28, 18)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < r * 0.55], context="VERTS")
    for v in bm.verts:  # corneal bulge
        v.co.y += (v.co.y - r * 0.55) * 0.35
    cor = _mesh_obj(f"{name}_HD_CORNEA_{side}", bm, [M["cornea"]], collection, piv, pass_index=pf)
    cor.visible_shadow = False
    _drive(piv, "rotation_euler", 2, root, "radians(-28*gaze_x)", ["gaze_x"])
    _drive(piv, "rotation_euler", 0, root, "radians(-20*gaze_y)", ["gaze_y"])

    # lids: shells slightly larger than the eyeball, rotating about the eye's lateral axis
    for which in ("UP", "LOW"):
        lp = _empty(f"{name}_HD_LID{which}_{side}", root, (ex, ey, ez), collection)
        rl = r * (1.24 if which == "UP" else 1.17)  # upper lid must clear the corneal bulge (~1.2 r)
        bm = _sphere(rl, 28, 18)
        keep_top = which == "UP"
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if (v.co.z < -1e-6 if keep_top else v.co.z > 1e-6) or v.co.y < -rl * 0.2],
                         context="VERTS")
        band = s.get("ink_band", 0.22) * rl
        mats = [M["lid"] if which == "UP" else M["skin"], M["lid_ink"]]
        me_bm = bm
        for f in me_bm.faces:
            zmin = min(abs(v.co.z) for v in f.verts)
            f.material_index = 1 if (which == "UP" and zmin < band and f.calc_center_median().y > 0) else 0
        lid = _mesh_obj(f"{name}_HD_LID{which}_{side}_MESH", me_bm, mats, collection, lp, pass_index=pf)
        if which == "UP":
            # lid_up 0 -> edge 15 deg below centre (closed), 0.8 -> just over the iris top, 1.1 -> wide
            _drive(lp, "rotation_euler", 0, root, f"radians(-15 + 55*lid_up_{side} - 4*tension*(lid_up_{side} < 0.12))",
                   [f"lid_up_{side}", "tension"])
        else:
            _drive(lp, "rotation_euler", 0, root, f"radians(-25 + 24*lid_low_{side})", [f"lid_low_{side}"])
        if which == "UP":
            # awake squeeze: lid shell pulls in a touch while closed
            for i in range(3):
                _drive(lid, "scale", i, root, f"1 - 0.03*tension*(lid_up_{side} < 0.12)", ["tension", f"lid_up_{side}"])


def _brow(name, side, sx, s, skull, M, root, collection, pf):
    n = 7
    xi, xo = 0.011, 0.047
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = sx * (xi + (xo - xi) * t)
        z = BROW_Z + 0.004 * math.sin(math.pi * t * 0.9) - 0.003 * t
        pts.append((x, z))
    th = s["brow_th"]
    bm, cols = _strip(skull, pts, lambda i: th * (1.15 - 0.6 * i / (n - 1)), lift=0.0012)
    ob_bm = bm
    idx = {}
    ob = _mesh_obj(f"{name}_HD_BROW_{side}", ob_bm, [M["brow"]], collection, root, pass_index=pf)
    # vertex order: column i -> verts 2i (top), 2i+1 (bottom)

    def offs(fn):
        d = {}
        for i in range(n):
            t = i / (n - 1)
            v = fn(t)
            d[2 * i] = v
            d[2 * i + 1] = v
        return d
    keys = _shape_keys(ob, {
        "inner_up": (offs(lambda t: Vector((0, 0, 0.0075 * (1 - t) ** 1.5))), 0),
        "inner_down": (offs(lambda t: Vector((-sx * 0.0025 * (1 - t), 0.0008 * (1 - t), -0.0055 * (1 - t) ** 1.5))), 0),
        "outer_up": (offs(lambda t: Vector((0, 0, 0.006 * t ** 1.5))), 0),
        "outer_down": (offs(lambda t: Vector((0, 0, -0.005 * t ** 1.5))), 0),
    })
    _drive(keys["inner_up"], "value", None, root, f"max(0, brow_in_{side})", [f"brow_in_{side}"])
    _drive(keys["inner_down"], "value", None, root, f"max(0, -brow_in_{side})", [f"brow_in_{side}"])
    _drive(keys["outer_up"], "value", None, root, f"max(0, brow_out_{side})", [f"brow_out_{side}"])
    _drive(keys["outer_down"], "value", None, root, f"max(0, -brow_out_{side})", [f"brow_out_{side}"])


def _mouth(name, s, skull, M, root, collection, pf):
    mz = -0.058
    mw = s["mouth_w"]
    th = s["lip_th"]
    n = 11
    xs = [-mw + 2 * mw * i / (n - 1) for i in range(n)]

    def lip(upper):
        pts = [(x, mz + (0.0032 if upper else -0.0036) * th * max(0.0, 1 - (x / mw) ** 2) ** 0.5) for x in xs]
        w = lambda i: max(0.0008, (0.0062 if upper else 0.0072) * th * max(0.0, 1 - (xs[i] / mw) ** 2) ** 0.6)
        return _strip(skull, pts, w, lift=0.0012)

    obs = {}
    for part, upper in (("UPPERLIP", True), ("LOWERLIP", False)):
        bm, cols = lip(upper)
        ob = _mesh_obj(f"{name}_HD_{part}", bm, [M["lips"]], collection, root, pass_index=pf)
        obs[part] = ob

        def offs(fn):
            d = {}
            for i, x in enumerate(xs):
                a = fn(x / mw, i, upper)
                for k in (0, 1):
                    if a is not None:
                        d[2 * i + k] = a[k] if isinstance(a, tuple) else a
            return d

        def corner(sgn):
            def f(u, i, up):
                w = max(0.0, u * sgn) ** 2.2
                return Vector((sgn * 0.0018 * w, -0.001 * w, 0.0085 * w))
            return f
        sk = _shape_keys(ob, {
            "smile_L": (offs(corner(-1)), -1),  # character's left = -X
            "smile_R": (offs(corner(1)), -1),
            # column verts: 0 = top edge, 1 = bottom edge. Press thins both lips toward the mouth line.
            "press": (offs(lambda u, i, up: (Vector((0, -0.0004, -0.0024)) * (1 - u * u), Vector((0, -0.0004, 0))) if up
                           else (Vector((0, -0.0004, 0)), Vector((0, -0.0004, 0.0028)) * (1 - u * u))), 0),
            "jaw": (offs(lambda u, i, up: (Vector((0, -0.001, 0.0 if up else -0.013)) * (1 - 0.7 * u * u),
                                           Vector((0, -0.001, 0.0006 if up else -0.013)) * (1 - 0.7 * u * u))), 0),
            "chin": (offs(lambda u, i, up: None if up else Vector((0, 0.0012, 0.0016)) * (1 - u * u)), 0),
        })
        _drive(sk["smile_L"], "value", None, root, "smile_L", ["smile_L"])
        _drive(sk["smile_R"], "value", None, root, "smile_R", ["smile_R"])
        _drive(sk["press"], "value", None, root, "press", ["press"])
        _drive(sk["jaw"], "value", None, root, "jaw", ["jaw"])
        _drive(sk["chin"], "value", None, root, "chin", ["chin"])
    # mouth interior and teeth (seen only when the jaw opens)
    bm = _sphere(1.0, 16, 10)
    for v in bm.verts:
        v.co = Vector((v.co.x * mw * 0.9, v.co.y * 0.008, v.co.z * 0.009))
    inner = _mesh_obj(f"{name}_HD_MOUTH", bm, [M["mouth"]], collection, root, pass_index=pf)
    inner.location = (0, skull.front_y(0, mz) - 0.012, mz - 0.004)
    _drive(inner, "location", 1, root, f"{skull.front_y(0, mz) - 0.012:.5f} + 0.0062*min(1, jaw*5)", ["jaw"])
    bm = _sphere(1.0, 16, 8)
    for v in bm.verts:
        v.co = Vector((v.co.x * mw * 0.7, v.co.y * 0.006, v.co.z * 0.0025))
    teeth = _mesh_obj(f"{name}_HD_TEETH", bm, [M["teeth"]], collection, root, pass_index=pf)
    teeth.location = (0, skull.front_y(0, mz) - 0.010, mz - 0.0005)
    _drive(teeth, "location", 1, root, f"{skull.front_y(0, mz) - 0.010:.5f} + 0.0056*min(1, jaw*5)", ["jaw"])


def _hair(name, s, skull, M, root, collection, ph):
    def cap(keep, grow=1.06, nm="HAIR"):
        bm = _sphere(1.0, 32, 22)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(v.co)], context="VERTS")
        for v in bm.verts:
            p = skull.shape(v.co)
            v.co = p * grow
        return _mesh_obj(f"{name}_HD_{nm}", bm, [M["hair"]], collection, root, pass_index=ph)

    if name == "NOOR":
        # swept back from a hairline at the top of the forehead; low bun at the nape
        cap(lambda c: c.z > 0.42 - 0.75 * max(0.0, -c.y) + 0.06 * c.x or (c.y < -0.25 and c.z > -0.55), 1.05)
        bm = _sphere(0.032, 16, 12)
        bun = _mesh_obj(f"{name}_HD_BUN", bm, [M["hair"]], collection, root, pass_index=ph)
        bun.location = (0, -skull.ry * 0.95, -0.055)
    elif name == "KAI":
        cap(lambda c: c.z > 0.30 - 0.9 * max(0.0, -c.y) or (c.y < -0.2 and c.z > -0.45), 1.09)
        for i, (x, y, z, r) in enumerate([(-0.03, 0.06, 0.085, 0.022), (0.025, 0.07, 0.08, 0.02), (0.0, 0.03, 0.105, 0.028),
                                          (0.045, 0.0, 0.095, 0.022), (-0.05, -0.01, 0.09, 0.022)]):
            bm = _sphere(r, 12, 8)
            lk = _mesh_obj(f"{name}_HD_LOCK{i}", bm, [M["hair"]], collection, root, pass_index=ph)
            lk.location = (x, y, z)
            lk.scale = (1.0, 0.8, 0.55)
    elif name == "BEA":
        cap(lambda c: c.z > 0.38 - 0.9 * max(0.0, -c.y) or (c.y < -0.3 and c.z > -0.4), 1.04)
    elif name == "WALTER":
        cap(lambda c: (abs(c.x) > 0.6 and -0.3 < c.z < 0.45 and c.y < 0.05) or (c.y < -0.35 and -0.4 < c.z < 0.55), 1.02, "HAIR_SIDES")


# ------------------------------------------------------------------ placing and keying

def place(root, centre, forward):
    """Put the rig's root at the head centre, facing `forward` (any horizontal vector)."""
    f = Vector(forward)
    f.z = 0
    f.normalize()
    root.location = Vector(centre)
    root.rotation_euler = (0, 0, math.atan2(f.y, f.x) - math.pi / 2)


def set_expression(root, params, frame=None, from_neutral=False):
    """Set controls (un-suffixed names set both sides) and optionally key them at `frame`.
    from_neutral=True first resets every control to the character's neutral (as on the sheets)."""
    vals = {}
    if from_neutral:
        base = {k: dv for k, (dv, lo, hi) in CONTROLS.items()}
        nm = root.name.replace("_HEADRIG", "")
        for k, v in NEUTRAL.get(nm, {}).items():
            for kk in (k, f"{k}_L", f"{k}_R"):
                if kk in base:
                    base[kk] = v
        p2 = dict(params)
        for k in list(p2):
            if f"{k}_L" in CONTROLS:
                p2.setdefault(f"{k}_L", p2[k])
                p2.setdefault(f"{k}_R", p2[k])
        base.update({k: v for k, v in p2.items() if k in CONTROLS})
        params = base
    for k, v in params.items():
        if k in CONTROLS:
            vals[k] = v
        elif f"{k}_L" in CONTROLS:
            vals.setdefault(f"{k}_L", v)
            vals.setdefault(f"{k}_R", v)
    for k, v in vals.items():
        root[k] = float(v)
        if frame is not None:
            root.keyframe_insert(f'["{k}"]', frame=frame)
    return vals
