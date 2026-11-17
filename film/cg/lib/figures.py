"""Blocking figures: seated, painted mannequins in costume colour, built from primitives.
They are placeholders for the Character Designer's sheets (design/), sized and posed so the
light reads correctly on faces and costumes in previs. Only Noor's lanyard is red.
"""
import math

import bpy
from mathutils import Vector

from . import lookdev as ld
from .common import link, load
from .mesh import box, ellipsoid, limb

CAST = {
    "NOOR":   dict(top="noor_suit", arms="noor_suit", legs="noor_suit", skin="skin_a", hair="hair_dark", build=0.95, pose="phone_ear"),
    "WALTER": dict(top="walter_coat", arms="walter_coat", legs="trousers", skin="skin_b", hair="hair_grey", build=1.05, pose="paper"),
    "BEA":    dict(top="bea_scrubs", arms="bea_cardigan", legs="bea_scrubs", skin="skin_c", hair="hair_dark", build=1.0, pose="lap", head_back=True),
    "KAI":    dict(top="kai_hoodie", arms="kai_hoodie", legs="trousers", skin="skin_d", hair="hair_dark", build=1.0, pose="phone_hands", hood=True),
}


def _mat(key, **kw):
    return ld.paint_material(f"char_{key}", key, stroke_scale=kw.pop("stroke_scale", 22.0), stretch=kw.pop("stretch", 1.5), **kw)


def _skin(key):
    return ld.paint_material(f"char_{key}", key, stroke_scale=26.0, stretch=1.0, variation=0.10, roughness=0.55, hue_jitter=0.03, bump=0.01)


def seated(name, lay, pose=None):
    spec = dict(CAST[name])
    if pose:
        spec["pose"] = pose
    ch = lay["characters"][name]
    W = lay["car"]["width"]
    pw = lay["seats"]["pair_width"]
    f = ch["facing"]
    side = ch["side"]
    y0 = side * (W / 2 - 0.04 - (0.75 if ch["seat"] == "aisle" else 0.25) * pw)
    x0 = ch["x"]
    coll = f"CHAR_{name}"
    b = spec["build"]

    def P(fwd, lat, z):
        return Vector((x0 + f * fwd, y0 + lat, z))

    top, arms, legs = _mat(spec["top"]), _mat(spec["arms"]), _mat(spec["legs"])
    skin, hair = _skin(spec["skin"]), _mat(spec["hair"], stroke_scale=40.0, stretch=3.0)
    obs = []
    lean = math.radians(8)
    hip = P(-0.10, 0, 0.58)
    sh = P(-0.16, 0, 1.06 * b ** 0.3)
    # torso
    t = ellipsoid(f"{name}_TORSO", (hip + sh) / 2 + Vector((0, 0, 0.03)), (0.12 * b, 0.185 * b, 0.30), top, coll)
    t.rotation_euler = (0, -f * lean, 0)
    obs.append(t)
    obs.append(ellipsoid(f"{name}_PELVIS", hip, (0.15, 0.18 * b, 0.10), legs, coll))
    # legs
    for s in (-1, 1):
        knee, foot = P(0.32, s * 0.11, 0.60), P(0.38, s * 0.12, 0.09)
        obs.append(limb(f"{name}_THIGH_{s}", P(-0.06, s * 0.10, 0.58), knee, 0.075 * b, legs, coll, r2=0.06))
        obs.append(limb(f"{name}_SHIN_{s}", knee, foot, 0.055, legs, coll, r2=0.045))
        obs.append(ellipsoid(f"{name}_SHOE_{s}", P(0.44, s * 0.12, 0.04), (0.13, 0.05, 0.04), _mat("phone"), coll))
    # head and neck
    head_c = P(-0.13 - (0.05 if spec.get("head_back") else 0), 0, 1.31 * b ** 0.3)
    obs.append(limb(f"{name}_NECK", sh + Vector((0, 0, 0.0)), head_c - Vector((0, 0, 0.08)), 0.045, skin, coll))
    hd = ellipsoid(f"{name}_HEAD", head_c, (0.095, 0.085, 0.115), skin, coll)
    if spec.get("head_back"):
        hd.rotation_euler = (0, -f * math.radians(22), 0)
    obs.append(hd)
    hr = ellipsoid(f"{name}_HAIR", head_c + Vector((-f * 0.02, 0, 0.035)), (0.10, 0.09, 0.10), hair, coll)
    obs.append(hr)
    if spec.get("hood"):
        obs.append(ellipsoid(f"{name}_HOOD", sh + Vector((-f * 0.10, 0, 0.06)), (0.08, 0.17, 0.09), top, coll))
    # arms by pose
    pose = spec["pose"]
    hands = {
        "phone_ear":   [((-0.04, -0.25, 0.86), (0.12, -0.10, 0.70)), ((-0.02, 0.22, 1.00), (-0.10, 0.11, 1.27))],
        "phone_lap":   [((-0.02, -0.24, 0.82), (0.20, -0.06, 0.80)), ((-0.02, 0.24, 0.82), (0.20, 0.06, 0.80))],
        "paper":       [((0.02, -0.25, 0.86), (0.26, -0.17, 0.92)), ((0.02, 0.25, 0.86), (0.26, 0.17, 0.92))],
        "lap":         [((-0.04, -0.24, 0.80), (0.16, -0.08, 0.66)), ((-0.04, 0.24, 0.80), (0.16, 0.08, 0.66))],
        "phone_hands": [((-0.02, -0.24, 0.82), (0.20, -0.05, 0.84)), ((-0.02, 0.24, 0.82), (0.20, 0.05, 0.84))],
    }[pose]
    for s, (elb, hand) in zip((-1, 1), hands):
        shp = P(-0.16, s * 0.19 * b, 1.04)
        e, h = P(*elb), P(*hand)
        obs.append(limb(f"{name}_UARM_{s}", shp, e, 0.05 * b, arms, coll, r2=0.042))
        obs.append(limb(f"{name}_FARM_{s}", e, h, 0.04, arms, coll, r2=0.032))
        obs.append(ellipsoid(f"{name}_HAND_{s}", h, (0.045, 0.035, 0.05), skin, coll))

    # props
    if name == "NOOR":
        red = ld.paint_material("lanyard_red", "lanyard", stroke_scale=40.0, variation=0.08)
        for s in (-1, 1):
            obs.append(limb(f"NOOR_LANYARD_{s}", P(-0.12, s * 0.07, 1.14), P(-0.03, s * 0.012, 0.90), 0.009, red, coll))
        obs.append(box("NOOR_BADGE", P(-0.025, 0, 0.85), (0.012, 0.075, 0.10), _mat("badge", stroke_scale=60.0), coll))
        obs.append(_phone("noor", P(*hands[1][1]) + Vector((f * 0.02, 0.0, 0.0)), head_c, coll))
    elif name == "WALTER":
        paper = box("WALTER_PAPER", P(0.29, 0, 0.98), (0.02, 0.36, 0.30), _mat("newspaper", stroke_scale=50.0, stretch=8.0, variation=0.25), coll)
        paper.rotation_euler = (0, -f * math.radians(20), 0)
    elif name == "BEA":
        obs.append(box("BEA_BAG", P(0.17, 0, 0.66), (0.20, 0.32, 0.16), _mat("bea_cardigan"), coll, bevel=0.03))
    elif name == "KAI":
        obs.append(_phone("kai", P(0.24, 0, 0.88), head_c, coll))
    return obs


def _phone(key, at, look_at, coll):
    """Phone with an emissive screen (material screen_<key>) and a small soft light toward the face."""
    rig = bpy.data.objects.new(f"PHONE_{key.upper()}_RIG", None)
    rig.location = at
    link(rig, coll)
    d = (Vector(look_at) - Vector(at)).normalized()
    rig.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    body = box(f"PHONE_{key.upper()}_BODY", (0, 0, -0.005), (0.075, 0.155, 0.009), _mat("phone", variation=0.0), coll)
    body.parent = rig
    scr = ld.emission_material(f"screen_{key}", (0.70, 0.82, 1.0), 3.0)  # cold blue-white
    sc = box(f"PHONE_{key.upper()}_SCREEN", (0, 0, 0.0), (0.066, 0.142, 0.002), scr, coll)
    sc.parent = rig
    sc.visible_diffuse = False
    sc.visible_shadow = False
    ldata = bpy.data.lights.new(f"PHONE_{key.upper()}_LIGHT", "AREA")
    ldata.size, ldata.size_y = 0.07, 0.14
    ldata.shape = "RECTANGLE"
    ldata.color = (0.70, 0.82, 1.0)
    ldata.energy = 3.0
    lo = bpy.data.objects.new(f"PHONE_{key.upper()}_LIGHT", ldata)
    lo.parent = rig
    lo.location = (0, 0, 0.01)
    lo.rotation_euler = (math.pi, 0, 0)  # area lights emit along local -Z; flip to face +Z (the face)
    link(lo, coll)
    return rig


def build(layout=None, poses=None):
    lay = layout or load("set_layout.json")
    poses = poses or {}
    for n in CAST:
        seated(n, lay, poses.get(n))


def set_visible(name, visible):
    coll = bpy.data.collections.get(f"CHAR_{name}")
    if coll:
        coll.hide_render = not visible
        coll.hide_viewport = not visible
