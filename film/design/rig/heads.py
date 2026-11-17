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
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PALETTE = os.path.join(os.path.dirname(HERE), "palette.json")

# Head ellipsoid half-sizes in metres (x half-width, y half-depth, z half-height), jaw taper, extras.
SPEC = {
    "NOOR":   dict(key="noor",   r=(0.074, 0.094, 0.114), jaw=0.70, chin_fwd=0.006, eye_r=0.0135, brow_th=0.0042, mouth_w=0.024, lip_th=1.0),
    "KAI":    dict(key="kai",    r=(0.077, 0.095, 0.115), jaw=0.82, chin_fwd=0.006, eye_r=0.0135, brow_th=0.0048, mouth_w=0.025, lip_th=0.9),
    "BEA":    dict(key="bea",    r=(0.079, 0.093, 0.112), jaw=0.80, chin_fwd=0.004, eye_r=0.0135, brow_th=0.0042, mouth_w=0.026, lip_th=1.15,
                  sclera="#F3F0E8", lid_ink="#0E0907", lid_albedo="#7C5642", ink_band=0.42),
    "WALTER": dict(key="walter", r=(0.076, 0.095, 0.114), jaw=0.74, chin_fwd=0.007, eye_r=0.0142, dome=1.15, brow_th=0.0085, mouth_w=0.024, lip_th=0.75,
                  lid_ink="#3A2C25", lid_albedo="#C9A68D", ink_band=0.30, brow_lift=0.0028),  # heavy lids, bushy brows (shot 38)
}

CONTROLS = {  # name: (default, min, max)  -- see face-rig.md
    "lid_up_L": (0.8, 0, 1.1), "lid_up_R": (0.8, 0, 1.1), "lid_low_L": (0, 0, 1), "lid_low_R": (0, 0, 1), "tension": (0, 0, 1),
    "brow_in_L": (0, -1, 1), "brow_in_R": (0, -1, 1), "brow_out_L": (0, -1, 1), "brow_out_R": (0, -1, 1),
    "smile_L": (0, -1, 1), "smile_R": (0, -1, 1), "press": (0, 0, 1), "jaw": (0, 0, 1), "chin": (0, 0, 1),
    "naso": (0, 0, 1), "gaze_x": (0, -1, 1), "gaze_y": (0, -1, 1), "tear": (0, 0, 1),
}
NEUTRAL = {
    "NOOR": dict(lid_up=0.82, naso=0.2), "KAI": dict(lid_up=0.7, naso=0.1),
    "BEA": dict(lid_up=0.7, naso=0.35, lid_low=0.1), "WALTER": dict(lid_up=0.66, naso=0.6, lid_low=0.15),
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
        "brow": _mat(f"hd_{k}_brow", _lin({"noor": "#231B18", "kai": "#1E1A18", "bea": "#231915", "walter": "#9E978D"}[k])),
        "hair_thin": _mat(f"hd_{k}_hairthin", _lin({"walter": "#D6BFAC"}.get(k, "#1E1A19"))),
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


def _sphere(r, segs=24, rings=16, pole_y=False):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    if pole_y:  # poles on the Y axis, so caps cut across Y get clean round rims
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    return bm


# Anatomy as smooth displacement fields on top of the base ellipsoid (metres, head-local).
# Each entry: (x, z, sigma, push) with the centre on the face (y found on the base surface), mirrored in x
# when x != 0. "push" moves the surface out (+) or in (-) along its normal.
ANATOMY = [
    (0.030, 0.030, 0.018, 0.0035),    # brow ridge
    (0.000, 0.030, 0.012, 0.0020),    # glabella
    (0.032, 0.008, 0.011, -0.0035),   # eye socket (shallow by design: top light)
    (0.048, -0.012, 0.016, 0.0040),   # cheekbone
    (0.000, -0.055, 0.020, 0.0040),   # muzzle round the mouth
    (0.000, -0.098, 0.013, 0.0040),   # chin
    (0.066, 0.050, 0.020, -0.0030),   # temples
    (0.060, -0.072, 0.016, 0.0060),   # jaw angle
    (0.032, -0.010, 0.007, 0.0012),   # under-eye fullness
]
CHARACTER_ANATOMY = {
    "NOOR":   [(0.050, -0.010, 0.014, 0.0020), (0.046, -0.045, 0.014, -0.0015),   # defined cheekbones, slight hollow
               (0.060, -0.074, 0.016, -0.0045), (0.000, -0.100, 0.012, -0.0010)],  # softer, tapered jaw and chin
    "KAI":    [(0.045, -0.045, 0.016, 0.0020), (0.000, -0.098, 0.012, -0.0015)],   # young: full cheeks, softer chin
    "BEA":    [(0.045, -0.040, 0.018, 0.0035), (0.032, -0.012, 0.008, 0.0022)],    # full cheeks; tired under-eyes
    "WALTER": [(0.030, 0.030, 0.016, 0.0010), (0.032, 0.008, 0.010, 0.0018),  # brow, but keep sockets shallow (top light)
               (0.046, -0.040, 0.016, -0.0012),     # cheeks: age in lines, not holes
               (0.050, -0.088, 0.014, 0.0014), (0.032, -0.012, 0.008, 0.0014),      # soft jowls; under-eye bags
               (0.000, 0.070, 0.030, 0.0015),                                       # high forehead
               (0.031, -0.036, 0.010, 0.0016)]                                      # cheek fold above the nasolabial
              + [(0.017 + 0.0035 * i, -0.030 - 0.0085 * i, 0.0035, -0.0016) for i in range(5)]   # nasolabial crease
              + [(x, z, 0.0028, -0.0006) for z in (0.056, 0.069, 0.082) for x in (0.0, 0.018, 0.036)],  # forehead lines
}


class Skull:
    """Head surface: a jaw-tapered ellipsoid plus smooth anatomical displacement fields."""

    def __init__(self, s, name=None):
        self.rx, self.ry, self.rz = s["r"]
        self.jaw = s["jaw"]
        self.chin_fwd = s["chin_fwd"]
        self.dome = s.get("dome", 0.75)
        self.fields = []
        for (x, z, sig, push) in ANATOMY + CHARACTER_ANATOMY.get(name, []):
            for sx in ((1, -1) if x else (1,)):
                cx = sx * x
                c = Vector((cx, self._base_front_y(cx, z), z))
                self.fields.append((c, sig, push))

    def taper(self, zn):  # zn = z / rz in [-1, 1]
        if zn >= -0.15:
            return 1.0
        t = min(1.0, (-0.15 - zn) / 0.85)
        return 1.0 - (1.0 - self.jaw) * t * t

    def _base(self, v):
        # superellipsoid: squarer than an egg (boxier cranium, flatter face plane, firmer jaw)
        zz = v.z
        pw = 2.0 + self.dome * max(0.0, min(1.0, (zz + 0.2) / 0.6)) + 0.3 * max(0.0, min(1.0, (-zz - 0.3) / 0.4))
        sc = (abs(v.x) ** pw + abs(v.y) ** pw + abs(v.z) ** pw) ** (-1.0 / pw)
        v = v * sc
        zn = v.z
        x = v.x * self.rx * self.taper(zn)
        y = v.y * self.ry
        if zn < -0.5 and v.y > 0:
            y += self.chin_fwd * (-0.5 - zn) * 2 * v.y
        z = v.z * self.rz
        # jaw underside and the back of the jaw: flatten the bottom of the egg toward the neck
        if z < -0.07 and y < 0.05:
            k = min(1.0, (0.05 - y) / 0.06)
            z = z + (-0.07 - z) * 0.6 * k
        if y < 0 and z > -0.05:  # fuller cranium behind
            y *= 1.06
        return Vector((x, y, z))

    def _base_front_y(self, x, z):
        zn = max(-0.999, min(0.999, z / self.rz))
        w = self.rx * self.taper(zn)
        q = 1 - (x / w) ** 2 - zn ** 2
        return self.ry * math.sqrt(max(q, 0.0))

    def shape(self, v):
        """Map a unit-sphere point to the head surface."""
        p = self._base(v)
        n = Vector((p.x / self.rx ** 2, p.y / self.ry ** 2, p.z / self.rz ** 2)).normalized()
        d = 0.0
        for c, sig, push in self.fields:
            q = (p - c).length_squared
            if q < 9 * sig * sig:
                d += push * math.exp(-q / (2 * sig * sig))
        return p + n * d

    def front_y(self, x, z):
        """y of the (displaced) face surface at (x, z), found by iterating on the sphere."""
        c = Vector((x / self.rx, 0.0, max(-0.99, min(0.99, z / self.rz))))
        for _ in range(30):
            c.x = max(-0.99, min(0.99, c.x))
            c.z = max(-0.99, min(0.99, c.z))
            c.y = math.sqrt(max(1e-6, 1 - c.x * c.x - c.z * c.z))
            p = self.shape(c)
            ex, ez = x - p.x, z - p.z
            if abs(ex) < 1e-6 and abs(ez) < 1e-6:
                break
            c.x += ex / (self.rx * self.taper(c.z)) * 0.9
            c.z += ez / self.rz * 0.9
        return self.shape(c).y


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
    skull = Skull(s, name)
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
    bm = _sphere(1.0, 64, 44)
    for v in bm.verts:
        v.co = skull.shape(v.co)
    _mesh_obj(f"{name}_HD_SKULL", bm, [M["skin"]], collection, root, pass_index=pass_face)

    # neck stub (the TA's neck limb meets it)
    # nose: a soft wedge
    # nose: a wedge, narrow at the bridge, widening to the nostrils, flat underneath (not a ball)
    bm = _sphere(1.0, 20, 14)
    for v in bm.verts:
        c = v.co
        t = (1 - c.z) / 2                      # 0 at the bridge, 1 at the base
        wx = 0.0055 + 0.0085 * t ** 1.4        # half-width
        proj = 0.003 + 0.010 * t ** 0.8        # forward projection grows toward the tip
        z = c.z * 0.021
        if c.z < -0.75:                        # flatten the underside
            z = -0.75 * 0.021 - (c.z + 0.75) * 0.004
        v.co = Vector((c.x * wx, c.y * (proj if c.y > 0 else 0.006), z))
    nz = -0.020
    bm_obj = _mesh_obj(f"{name}_HD_NOSE", bm, [M["skin"]], collection, root, pass_index=pass_face)
    bm_obj.location = (0, skull.front_y(0, nz) - 0.002, nz)

    # ears
    for sx in (-1, 1):
        bm = _sphere(1.0, 12, 8)
        for v in bm.verts:
            v.co = Vector((v.co.x * 0.007, v.co.y * 0.014, v.co.z * (0.028 if name != "WALTER" else 0.036)))
        e = _mesh_obj(f"{name}_HD_EAR_{'R' if sx > 0 else 'L'}", bm, [M["skin"]], collection, root, pass_index=pass_face)
        e.location = (sx * skull.rx * (1.04 if name == "WALTER" else 0.95), -0.008, -0.006)

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
    # iris and pupil lie ON the eyeball (under the cornea), as caps of a slightly larger sphere
    for part, cut, grow, mat in (("IRIS", 0.866, 1.004, M["iris"]), ("PUPIL", 0.976, 1.008, M["pupil"])):
        bm = _sphere(r * grow, 64, 48, pole_y=True)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < cut * r * grow], context="VERTS")
        _mesh_obj(f"{name}_HD_{part}_{side}", bm, [mat], collection, piv, pass_index=pf)
    # cornea: a smooth spherical cap meeting the eyeball at the iris rim. Its radius is stylised
    # FLATTER than a real cornea (0.9 r vs ~0.65 r), which makes each panel's reflection bigger,
    # so the row of panels stays countable on the 75 mm close-up.
    rc = s.get("cornea_rc", 0.9) * r
    rim_y = r * math.sqrt(1 - 0.5 ** 2)                    # iris rim on the eyeball (iris radius 0.5 r)
    yc = rim_y - math.sqrt(max(rc * rc - (0.5 * r) ** 2, 0.0)) + 0.012 * r
    bm = _sphere(rc, 96, 64, pole_y=True)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y + yc < rim_y - 0.03 * r], context="VERTS")
    for v in bm.verts:
        v.co.y += yc
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
    bm, cols = _strip(skull, pts, lambda i: th * (1.15 - 0.6 * i / (n - 1)), lift=s.get("brow_lift", 0.0012))
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
    """Hair as a smooth shell over the skull. Below the hairline the shell sinks under the skin,
    so the hairline is a clean painted edge, not a cut mesh."""

    def ss(e0, e1, x):
        t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
        return t * t * (3 - 2 * t)

    def shell(field, grow, nm="HAIR", band=0.07, base=0.93):
        bm = _sphere(1.0, 64, 44)
        for v in bm.verts:
            c = v.co.copy()
            k = ss(-band, band, field(c))
            g = base + (grow(c) - base) * k
            v.co = skull.shape(c) * g
        return _mesh_obj(f"{name}_HD_{nm}", bm, [M["hair"]], collection, root, pass_index=ph)

    def hairline(front, side, back, part=0.0):
        def hz(c):
            a = abs(math.atan2(c.x, c.y)) / math.pi        # 0 front, 0.5 sides, 1 back
            z = front + (side - front) * ss(0.0, 0.5, a) + (back - side) * ss(0.5, 1.0, a)
            return z - part * c.x * (1 - ss(0.0, 0.3, a))
        return lambda c: c.z - hz(c)

    if name == "NOOR":
        # side-parted, swept back over the tops of the ears into a low bun at the nape
        shell(hairline(0.42, 0.02, -0.62, part=0.08), lambda c: 1.05 + 0.04 * max(0.0, c.z) * (1 - 0.5 * max(0.0, c.y)))
        bm = _sphere(0.034, 18, 12)
        bun = _mesh_obj(f"{name}_HD_BUN", bm, [M["hair"]], collection, root, pass_index=ph)
        bun.location = (0, -skull.ry * 0.98, -0.058)
        bun.scale = (1.15, 0.85, 0.9)
    elif name == "KAI":
        shell(hairline(0.26, 0.05, -0.5), lambda c: 1.09 + 0.05 * max(0.0, c.z))
        for i, (x, y, z, r) in enumerate([(-0.03, 0.06, 0.085, 0.022), (0.025, 0.07, 0.08, 0.02), (0.0, 0.03, 0.105, 0.028),
                                          (0.045, 0.0, 0.095, 0.022), (-0.05, -0.01, 0.09, 0.022)]):
            bm = _sphere(r, 12, 8)
            lk = _mesh_obj(f"{name}_HD_LOCK{i}", bm, [M["hair"]], collection, root, pass_index=ph)
            lk.location = (x, y, z)
            lk.scale = (1.0, 0.8, 0.55)
    elif name == "BEA":
        shell(hairline(0.38, -0.02, -0.45), lambda c: 1.045)
    elif name == "WALTER":
        # thinning white hair, combed back: a fuller band round the sides and back, and a thin top
        # (lighter, scalp showing through) from a receding hairline. Not bald.
        # a soft band wrapping continuously round the back, sitting a little behind and above the ears
        # (ears in front), with an irregular painted edge broken into strands at the temples: hair, not hardware
        side = hairline(1.5, 0.12, -0.50)
        top_lim = hairline(0.46, 0.46, 0.50)

        def rough(c):
            a = math.atan2(c.x, c.y)
            front = 1.0 + 1.2 * max(0.0, 1 - abs(abs(a) / math.pi - 0.40) / 0.12)   # broken strands at the temples
            return front * (0.05 * math.sin(11 * a + 3 * c.z) + 0.035 * math.sin(29 * c.z - 4 * a))

        shell(lambda c: min(side(c) + rough(c), -top_lim(c) + rough(c), (abs(math.atan2(c.x, c.y)) / math.pi - 0.40) * 1.6 + rough(c)),
              lambda c: 1.045 + 0.025 * max(0.0, -c.y), "HAIR_SIDES", band=0.06)
        Mt = dict(M)
        Mt["hair"] = M.get("hair_thin", M["hair"])
        shell_top = hairline(0.74, 0.46, 0.20)
        bm = _sphere(1.0, 64, 44)
        for v in bm.verts:
            c = v.co.copy()
            k = ss(-0.06, 0.06, shell_top(c))
            v.co = skull.shape(c) * (0.94 + (1.012 - 0.94) * k)
        _mesh_obj(f"{name}_HD_HAIR_TOP", bm, [Mt["hair"]], collection, root, pass_index=ph)


def build_neck(root, name, collection=None, mats=None, scarf=None):
    """Optional neck that meets the jaw underside, parented to the head root (replaces a limb neck).
    Older necks are thicker and shorter in frame. For WALTER a grey wool scarf wraps the base."""
    name = name.upper()
    M = default_materials(name)
    if mats:
        M.update({k: v for k, v in mats.items() if v is not None})
    rx, ry = {"NOOR": (0.046, 0.044), "KAI": (0.052, 0.050), "BEA": (0.056, 0.052), "WALTER": (0.058, 0.054)}[name]
    bm = bmesh.new()
    rings, segs = 8, 24
    ring = []
    for i in range(rings + 1):
        t = i / rings
        z = -0.055 - 0.13 * t
        yc = -0.012 - 0.010 * t
        k = 1.0 + 0.18 * t * t          # flares into the shoulders
        rr = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            x, y = math.cos(a) * rx * k, math.sin(a) * ry * k
            if name in ("WALTER", "KAI") and abs(a - math.pi / 2) < 0.35 and 0.25 < t < 0.55:
                y += 0.004                # Adam's apple
            rr.append(bm.verts.new((x, y + yc, z)))
        ring.append(rr)
    for i in range(rings):
        for j in range(segs):
            a, b = ring[i][j], ring[i][(j + 1) % segs]
            c, d = ring[i + 1][(j + 1) % segs], ring[i + 1][j]
            bm.faces.new((a, b, c, d))
    neck = _mesh_obj(f"{name}_HD_NECK", bm, [M["skin"]], collection, root, pass_index=1)
    obs = [neck]
    if scarf if scarf is not None else name == "WALTER":
        sc_mat = M.get("scarf") or _mat("hd_walter_scarf", tuple(_palette()["walter/scarf"]["linear"]))
        parts = []
        # wrap: a soft torus round the neck base, then a knot at the front and two ends hanging down
        bm = bmesh.new()
        R, rr, seg, ring_n = rx * 1.18, 0.015, 36, 12
        grid = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            row = []
            for j in range(ring_n):
                b = 2 * math.pi * j / ring_n
                rad = R + rr * math.cos(b) * (1.0 + 0.25 * math.sin(3 * a))   # lumpy wool
                row.append(bm.verts.new((math.cos(a) * rad, math.sin(a) * rad * ry / rx, rr * math.sin(b) * 1.15)))
            grid.append(row)
        for i in range(seg):
            for j in range(ring_n):
                bm.faces.new((grid[i][j], grid[(i + 1) % seg][j], grid[(i + 1) % seg][(j + 1) % ring_n], grid[i][(j + 1) % ring_n]))
        w = _mesh_obj(f"{name}_HD_SCARF", bm, [sc_mat], collection, root, pass_index=2)
        w.location = (0, -0.014, -0.118)
        parts.append(w)
        bm = _sphere(1.0, 16, 12)
        for v in bm.verts:
            v.co = Vector((v.co.x * 0.020, v.co.y * 0.012, v.co.z * 0.017))
        k = _mesh_obj(f"{name}_HD_SCARF_KNOT", bm, [sc_mat], collection, root, pass_index=2)
        k.location = (0.008, ry * 1.18 + 0.006, -0.135)
        parts.append(k)
        for i, (dx, rot) in enumerate(((-0.006, 0.12), (0.020, -0.18))):
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((0.040, 0.012, 0.15)), verts=bm.verts)
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.004, segments=2, affect="EDGES")
            e = _mesh_obj(f"{name}_HD_SCARF_END{i}", bm, [sc_mat], collection, root, pass_index=2)
            e.location = (dx, ry * 1.18 + 0.010, -0.215)
            e.rotation_euler = (0.12, rot, rot * 0.5)
            parts.append(e)
        obs += parts
    return obs


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


def apply_track(root, keys, library, fps=24, ease_frames=7, fast=("walter/clamp",)):
    """Key a per-shot expression track (expressions/shot_expressions.json) onto a head rig.
    keys: [[time_s, name, shot], ...]. Each change holds the previous expression until
    `ease_frames` before the new key, then eases in (Bezier). Names in `fast` ease in 2 frames."""
    prev = None
    for t, name, _shot in keys:
        f = round(t * fps)
        if prev is not None:
            ease = 2 if name in fast else ease_frames
            set_expression(root, library[prev], frame=max(0, f - ease), from_neutral=True)
        set_expression(root, library[name], frame=f, from_neutral=True)
        prev = name
