"""Blocking figures: painted mannequins at the Character Designer's sizes, posed on the DP's marks.
Placeholders for design/sheets; they exist so light reads correctly on faces and costumes in
previs. Glossy corneas show the real panel row as catchlights. Only the strap and Kai's end-call
button are THE_RED.
"""
import math

import bpy
from mathutils import Matrix, Vector

from . import lookdev as ld
from .common import coll, dp, link, load, t2f
from .mesh import box, ellipsoid, limb, text
from . import noor
from .common import FILM_DIR
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(FILM_DIR, "design", "rig"))
import heads as _heads  # Character Designer's face rig (design/rig/heads.py)

CAST = {
    "NOOR":   dict(top="noor/suit", arms="noor/suit", legs="noor/skirt", shoes="noor/shoes", skin="noor/skin", hair="noor/hair", iris="noor/iris"),
    "WALTER": dict(top="walter/coat", arms="walter/coat", legs="walter/trousers", shoes="walter/shoes", skin="walter/skin", hair="walter/hair", iris="walter/iris"),
    "BEA":    dict(top="bea/scrubs", arms="bea/cardigan", legs="bea/scrubs", shoes="bea/clogs", skin="bea/skin", hair="bea/hair", iris="bea/iris", cardigan=True),
    "KAI":    dict(top="kai/hoodie", arms="kai/hoodie", legs="kai/jeans", shoes="kai/sneakers", skin="kai/skin", hair="kai/hair", iris="kai/iris", hood=True),
}
DEFAULT_POSE = {"NOOR": "lap", "WALTER": "paper", "BEA": "lap", "KAI": "phone_hands"}


def _tag(ob, idx):
    ob.pass_index = idx
    return ob


def figure(name, D, B, pose=None, at=None, standing=False, facing=None, eyes_closed=False, sculpted=True, face=None, collection=None):
    spec = CAST[name]
    fig = B["figures"][name]
    mark = Vector(at if at else D["set"]["marks"][name])
    fa = facing or fig["facing"]
    f = Vector((fa[0], fa[1], 0)).normalized()
    lat = Vector((0, 0, 1)).cross(f)
    eye = fig["eye"] if not standing else fig["height"] * 0.935
    hip_z = 0.56 if not standing else fig["height"] * 0.52
    # upper body scaled so the eye lands on the Designer's seated eye height
    k = (eye + 0.02 - hip_z) / (1.31 - 0.58)
    sw = fig["shoulder"] / 0.44
    O = Vector((mark.x, mark.y, 0)) + f * 0.10
    C = collection or f"CHAR_{name}"
    coll(C, coll("CHARACTERS"))

    def P(fw, la, z):
        zz = hip_z + (z - 0.58) * k if z >= 0.58 else z
        return O + f * fw + lat * la + Vector((0, 0, zz))

    def Pz(fw, la, zabs):
        return O + f * fw + lat * la + Vector((0, 0, zabs))

    m = {r: ld.paint(f"c_{spec[r].replace('/', '_')}", spec[r], tier="costume") for r in ("top", "arms", "legs", "shoes")}
    skin = ld.paint(f"c_{spec['skin'].replace('/', '_')}", spec["skin"], tier="face")
    hair = ld.paint(f"c_{spec['hair'].replace('/', '_')}", spec["hair"], tier="costume", stretch=6.0)
    cornea = ld.gloss(f"cornea_{name}", spec["iris"], roughness=0.03, coat=1.0)
    obs = []
    yaw = math.atan2(f.y, f.x)
    rot = Matrix.Rotation(yaw, 3, "Z")
    lean = Matrix.Rotation(math.radians(8), 3, lat)
    hip = P(-0.10, 0, 0.58)
    sh = P(-0.16, 0, 1.06)
    if name == "NOOR" and sculpted:
        obs += noor.torso(hip, sh, f, lat, C, sw)
    else:
        obs.append(_tag(ellipsoid(f"{name}_TORSO", (hip + sh) / 2 + Vector((0, 0, 0.02)), (0.12, 0.185 * sw, 0.29 * k), m["top"], C,
                                  rot=lean @ rot), 2))
    obs.append(_tag(ellipsoid(f"{name}_PELVIS", hip, (0.15, 0.18 * sw, 0.10), m["legs"], C, rot=rot), 2))
    if spec.get("cardigan"):
        for s in (-1, 1):
            obs.append(_tag(ellipsoid(f"{name}_CARDIGAN_{s}", (hip + sh) / 2 + lat * s * 0.10 * sw + Vector((0, 0, 0.02)),
                                      (0.125, 0.09 * sw, 0.29 * k), m["arms"], C, rot=lean @ rot), 2))
    # legs
    for s in (-1, 1):
        if standing:
            knee, foot = Pz(0.0, s * 0.10, 0.48), Pz(0.02, s * 0.11, 0.08)
            top = Pz(-0.02, s * 0.10, hip_z)
        else:
            knee, foot, top = Pz(0.32, s * 0.11, 0.58), Pz(0.38, s * 0.12, 0.09), Pz(-0.06, s * 0.10, 0.57)
        obs.append(_tag(limb(f"{name}_THIGH_{s}", top, knee, 0.075, m["legs"], C, r2=0.06), 2))
        obs.append(_tag(limb(f"{name}_SHIN_{s}", knee, foot, 0.055, m["legs"], C, r2=0.045), 2))
        obs.append(_tag(ellipsoid(f"{name}_SHOE_{s}", foot + f * 0.06 - Vector((0, 0, 0.05)), (0.13, 0.05, 0.04), m["shoes"], C, rot=rot), 2))
    # head, neck, hair, eyes (glossy corneas -> panel catchlights)
    head_c = P(-0.13, 0, 1.31)
    tilt = Matrix.Rotation(math.radians(-6), 3, lat)
    # head: the Character Designer's rig (design/rig/heads.py) with the TA's painted materials
    neck_top = head_c - Vector((0, 0, 0.065)) - f * 0.01
    obs.append(_tag(limb(f"{name}_NECK", sh + Vector((0, 0, 0.05)), neck_top, 0.038, skin if name != "NOOR" else noor.skin_mat(),
                         C, segs=12, smooth=True), 1))
    key = name.lower()
    face_skin = noor.skin_mat() if name == "NOOR" else ld.paint(f"c_{key}_skin_face", f"{key}/skin", tier="face",
                                                               shadow=f"{key}/skin_shadow", axis="x", stretch=3.0,
                                                               variation=0.025, shadow_mix=0.08, tilt=0.07)
    mats = {"skin": face_skin,
            "hair": ld.paint(f"c_{key}_hair_rig", f"{key}/hair", tier="costume", stroke_scale=90.0, stretch=6.0, axis="z", variation=0.35),
            "lips": ld.paint(f"c_{key}_lips", f"{key}/lips", tier="face", variation=0.04)}
    root = _heads.build_head(name, collection=C, mats=mats)
    _heads.place(root, head_c, f)
    expr = dict(face or {})
    if eyes_closed:
        expr.update({"lid_up": 0.0, "tension": 0.35})
    if expr:
        _heads.set_expression(root, expr, from_neutral=True)
    for ob in [root] + list(root.children_recursive):
        if ob.type == "MESH" and ob.pass_index == 0:
            ob.pass_index = 1
    if spec.get("hood"):
        obs.append(_tag(ellipsoid(f"{name}_HOOD", sh - f * 0.10 + Vector((0, 0, 0.06)), (0.08, 0.17, 0.09), m["top"], C, rot=rot), 2))
    # arms by pose: (elbow, hand) in (fwd, lat, z-unscaled)
    pose = pose or DEFAULT_POSE[name]
    hands = {
        "phone_ear":   [((-0.04, -0.25, 0.86), (0.12, -0.10, 0.70)), ((-0.04, 0.22, 1.00), (-0.11, 0.11, 1.27))],
        "phone_lap":   [((-0.02, -0.24, 0.82), (0.22, -0.13, 0.76)), ((-0.02, 0.24, 0.82), (0.22, 0.13, 0.76))],
        "paper":       [((0.02, -0.25, 0.86), (0.26, -0.17, 0.92)), ((0.02, 0.25, 0.86), (0.26, 0.17, 0.92))],
        "lap":         [((-0.04, -0.24, 0.80), (0.16, -0.08, 0.66)), ((-0.04, 0.24, 0.80), (0.16, 0.08, 0.66))],
        "phone_hands": [((-0.02, -0.24, 0.82), (0.20, -0.05, 0.84)), ((-0.02, 0.24, 0.82), (0.20, 0.05, 0.84))],
        "standing":    [((-0.02, -0.24, 0.82), (0.02, -0.22, 0.58)), ((-0.04, 0.22, 1.00), (-0.11, 0.11, 1.27))],
        "standing_down": [((-0.02, -0.24, 0.82), (0.02, -0.22, 0.58)), ((-0.02, 0.24, 0.82), (0.02, 0.22, 0.58))],
        "standing_reach": [((-0.02, -0.24, 0.82), (0.02, -0.22, 0.58)), ((0.16, 0.22, 1.02), (0.40, 0.12, 1.02))],
    }[pose]
    for s, (elb, hand) in zip((-1, 1), hands):
        shp = P(-0.16, s * 0.19 * sw, 1.04)
        e, h = P(*elb), P(*hand)
        obs.append(_tag(limb(f"{name}_UARM_{s}", shp, e, 0.05, m["arms"], C, r2=0.042), 2))
        obs.append(_tag(limb(f"{name}_FARM_{s}", e, h, 0.04, m["arms"], C, r2=0.032), 2))
        obs.append(_tag(ellipsoid(f"{name}_HAND_{s}", h, (0.045, 0.035, 0.05), skin, C, rot=rot), 1))
    # props
    if name == "NOOR":
        red = ld.paint("the_red_strap", "THE_RED", tier="costume", variation=0.06)
        from .mesh import ribbon
        for s in (-1, 1):
            # 25 mm flat strap (8b): round the back of the neck, over the collar, down the blazer front to the badge
            pts = [P(-0.19, s * 0.035, 1.16), P(-0.13, s * 0.062, 1.17), P(-0.07, s * 0.066, 1.12),
                   P(0.004, s * 0.052, 1.04), P(0.016, s * 0.030, 0.96), P(0.018, s * 0.010, 0.905)]
            obs.append(_tag(ribbon(f"NOOR_STRAP_{s}", pts, 0.025, 0.004, f, red, C), 1))
        badge = _tag(box("NOOR_BADGE", P(0.022, 0, 0.85), (0.075, 0.008, 0.10), ld.gloss("badge_plastic", "noor/badge", roughness=0.25), C), 1)
        badge.rotation_euler = (0, 0, yaw)
        obs.append(badge)
        rh = P(*hands[1][1])
        if pose == "phone_lap":   # face-up on the DP's mark, screen turned to the MARK insert camera (shot 51)
            at_ = Vector(D["set"]["marks"]["NOOR_PHONE_LAP"])
            ins = next((s for s in D["shots"] if s.get("aim_subject") == "NOOR_PHONE_LAP" and s.get("camera_loc")), None)
            target = Vector(ins["camera_loc"]) if ins else at_ + Vector((0, 0, 1))
        else:
            at_, target = rh + f * 0.02, head_c
        phone = _phone("noor", at_, target, C, red_button=False)
    elif name == "WALTER":
        paper = box("WALTER_PAPER", P(0.29, 0, 0.98), (0.02, 0.36, 0.30), ld.paint("newsprint", "props/newsprint", tier="costume", stretch=8.0, variation=0.25), C)
        paper.rotation_euler = (0, -math.radians(20), yaw)
        _tag(paper, 2)
    elif name == "BEA":
        tote = _tag(box("BEA_TOTE", P(0.17, 0, 0.66), (0.20, 0.32, 0.16), ld.paint("tote", "bea/tote", tier="costume"), C, bevel=0.03), 2)
        tote.rotation_euler = (0, 0, yaw)
        obs.append(tote)
    elif name == "KAI":
        _phone("kai", P(0.24, 0, 0.88), head_c, C, red_button=True)
    return {"collection": C, "root": root, "head_c": head_c, "f": f}


def _phone(key, at, look_at, C, red_button=False):
    """Phone with an emissive screen (screen_<key>) and a small soft light toward the face.
    Kai's screen carries the red end-call button (THE_RED, the film's second red)."""
    rig = bpy.data.objects.new(f"PHONE_{key.upper()}_RIG", None)
    rig.location = at
    link(rig, C)
    d = (Vector(look_at) - Vector(at)).normalized()
    rig.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    body = box(f"PHONE_{key.upper()}_BODY", (0, 0, -0.005), (0.075, 0.155, 0.009),
               ld.paint(f"phone_case_{key}", "props/noor_phone_case" if key == "noor" else "kai/phone_case", tier="costume", variation=0.0), C)
    scr = ld.emission(f"screen_{key}", "props/screen_glow", 6.0)
    sc = box(f"PHONE_{key.upper()}_SCREEN", (0, 0.005, 0.0), (0.066, 0.13, 0.002), scr, C)
    parts = [body, sc]
    caller = {"noor": "MARK", "kai": "MUM"}.get(key)
    if caller:   # caller ID, dark on the lit screen (inserts 19/30/32/51)
        ink = bpy.data.materials.get("phone_ink") or ld.paint("phone_ink", "props/pen_ink", tier="face", variation=0.0)
        cid = text(f"PHONE_{key.upper()}_CALLER", caller, (0, 0.035, 0.0016), 0.017, ink, rot=(0, 0, 0), collection=C)
        cid.data.extrude = 0.0003
        parts.append(cid)
    if red_button:
        rb = box(f"PHONE_{key.upper()}_ENDCALL", (0, -0.058, 0.0012), (0.022, 0.022, 0.002), ld.emission(f"endcall_{key}", "THE_RED", 6.0), C)
        parts.append(rb)
    for p in parts:
        p.parent = rig
        p.pass_index = 2
    for p in parts[1:]:
        p.visible_diffuse = False
        p.visible_shadow = False
    ldata = bpy.data.lights.new(f"PHONE_{key.upper()}_LIGHT", "AREA")
    ldata.size, ldata.size_y = 0.07, 0.14
    ldata.color = ld.pal("props/screen_glow")
    lo = bpy.data.objects.new(f"PHONE_{key.upper()}_LIGHT", ldata)
    lo.parent = rig
    lo.location = (0, 0, 0.012)
    lo.rotation_euler = (math.pi, 0, 0)
    link(lo, C)
    return rig


def build(D=None, B=None, poses=None, standing=None, closed=()):
    D = D or dp()
    B = B or load("build.json")
    poses = poses or {}
    standing = standing or {}
    for n in CAST:
        if n in standing:
            figure(n, D, B, pose=standing[n].get("pose", "standing"), at=standing[n]["at"], standing=True,
                   facing=standing[n].get("facing"))
        else:
            figure(n, D, B, poses.get(n), eyes_closed=(n in closed))
    animate_kai(D)


def animate_kai(D):
    """Cue 4: Kai is removed in the dark (no animation). His phone is left face-up on the seat."""
    f = t2f(next(c["t"] for c in D["cues"] if c["id"] == "4"), D["fps"]) + 1
    ph = bpy.data.objects["PHONE_KAI_RIG"]
    phone_parts = {ph.name} | {c.name for c in ph.children}
    for ob in bpy.data.collections["CHAR_KAI"].objects:
        if ob.name in phone_parts:
            continue
        for fr, hide in ((0, False), (f, True)):
            ob.hide_render = hide
            ob.keyframe_insert("hide_render", frame=fr)
    seat = Vector(D["set"]["marks"]["KAI_PHONE"])
    for fr, loc, rot in ((0, tuple(ph.location), tuple(ph.rotation_euler)), (f, (seat.x - 0.1, seat.y, seat.z + 0.03), (0, 0, math.radians(20)))):
        ph.location, ph.rotation_euler = loc, rot
        ph.keyframe_insert("location", frame=fr)
        ph.keyframe_insert("rotation_euler", frame=fr)
    for fc in ph.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def set_visible(name, visible):
    c = bpy.data.collections.get(f"CHAR_{name}")
    if c:
        c.hide_render = not visible
