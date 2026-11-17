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
from .mesh import box, ellipsoid, limb
from . import noor

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


def figure(name, D, B, pose=None, at=None, standing=False, facing=None, eyes_closed=False, sculpted=True, face=None):
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
    C = f"CHAR_{name}"
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
    if name == "NOOR" and sculpted:
        obs.append(_tag(limb(f"{name}_NECK", sh + Vector((0, 0, 0.05)), head_c - Vector((0, 0, 0.06)) - f * 0.01, 0.056, noor.skin_mat(), C, segs=12, smooth=True), 1))
        obs += noor.build(head_c, f, lat, C, params=face)
    else:
        obs.append(_tag(limb(f"{name}_NECK", sh, head_c - Vector((0, 0, 0.08)), 0.045, skin, C), 1))
        obs.append(_tag(ellipsoid(f"{name}_HEAD", head_c, (0.095, 0.082, 0.115), skin, C, rot=tilt @ rot), 1))
        obs.append(_tag(ellipsoid(f"{name}_NOSE", head_c + f * 0.092 - Vector((0, 0, 0.012)), (0.02, 0.014, 0.028), skin, C, rot=rot), 1))
        obs.append(_tag(ellipsoid(f"{name}_HAIR", head_c - f * 0.025 + Vector((0, 0, 0.035)), (0.10, 0.09, 0.10), hair, C, rot=rot), 2))
        sclera = ld.gloss("sclera", (0.896, 0.871, 0.807), roughness=0.04, coat=1.0)   # #F3F0E8 (design-notes F2)
        lid = ld.paint(f"lid_{name}", (0.155, 0.0685, 0.0395), tier="face")                 # #6E4A38
        lidline = ld.paint("lid_line", (0.006, 0.005, 0.005), tier="face", variation=0.0)
        for s in (-1, 1):
            ec = head_c + f * 0.074 + lat * s * 0.033 + Vector((0, 0, 0.012))
            obs.append(_tag(ellipsoid(f"{name}_EYE_{s}", ec, (0.012, 0.012, 0.012), sclera, C, segs=16, smooth=True), 1))
            obs.append(_tag(ellipsoid(f"{name}_IRIS_{s}", ec + f * 0.0085, (0.0035, 0.0062, 0.0062), cornea, C, segs=12, rot=rot, smooth=True), 1))
            if eyes_closed:
                obs.append(_tag(ellipsoid(f"{name}_LID_{s}", ec + f * 0.001, (0.0135, 0.0135, 0.0135), lid, C, segs=16, smooth=True), 1))
                obs.append(_tag(limb(f"{name}_LIDLINE_{s}", ec + f * 0.0132 - lat * 0.010 - Vector((0, 0, 0.001)),
                                     ec + f * 0.0132 + lat * 0.010 - Vector((0, 0, 0.001)), 0.0016, lidline, C), 1))
    if spec.get("hood"):
        obs.append(_tag(ellipsoid(f"{name}_HOOD", sh - f * 0.10 + Vector((0, 0, 0.06)), (0.08, 0.17, 0.09), m["top"], C, rot=rot), 2))
    # arms by pose: (elbow, hand) in (fwd, lat, z-unscaled)
    pose = pose or DEFAULT_POSE[name]
    hands = {
        "phone_ear":   [((-0.04, -0.25, 0.86), (0.12, -0.10, 0.70)), ((-0.04, 0.22, 1.00), (-0.11, 0.11, 1.27))],
        "phone_lap":   [((-0.02, -0.24, 0.82), (0.20, -0.06, 0.78)), ((-0.02, 0.24, 0.82), (0.20, 0.06, 0.78))],
        "paper":       [((0.02, -0.25, 0.86), (0.26, -0.17, 0.92)), ((0.02, 0.25, 0.86), (0.26, 0.17, 0.92))],
        "lap":         [((-0.04, -0.24, 0.80), (0.16, -0.08, 0.66)), ((-0.04, 0.24, 0.80), (0.16, 0.08, 0.66))],
        "phone_hands": [((-0.02, -0.24, 0.82), (0.20, -0.05, 0.84)), ((-0.02, 0.24, 0.82), (0.20, 0.05, 0.84))],
        "standing":    [((-0.02, -0.24, 0.82), (0.02, -0.22, 0.58)), ((-0.04, 0.22, 1.00), (-0.11, 0.11, 1.27))],
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
        for s in (-1, 1):
            obs.append(_tag(limb(f"NOOR_STRAP_{s}", P(-0.10, s * 0.065, 1.10), P(-0.012, s * 0.012, 0.90), 0.008, red, C, segs=8, smooth=True), 2))
        obs.append(_tag(box("NOOR_BADGE", P(-0.008, 0, 0.85), (0.075, 0.075, 0.10), ld.gloss("badge_plastic", "noor/badge", roughness=0.25), C), 2))
        bpy.data.objects["NOOR_BADGE"].rotation_euler = (0, 0, yaw)
        rh = P(*hands[1][1])
        target = head_c if pose != "phone_lap" else head_c
        at_ = rh + f * 0.02 if pose != "phone_lap" else (P(*hands[0][1]) + P(*hands[1][1])) / 2 + Vector((0, 0, 0.03))
        _phone("noor", at_, target, C, red_button=False)
    elif name == "WALTER":
        paper = box("WALTER_PAPER", P(0.29, 0, 0.98), (0.02, 0.36, 0.30), ld.paint("newsprint", "props/newsprint", tier="costume", stretch=8.0, variation=0.25), C)
        paper.rotation_euler = (0, -math.radians(20), yaw)
        _tag(paper, 2)
    elif name == "BEA":
        obs.append(_tag(box("BEA_TOTE", P(0.17, 0, 0.66), (0.20, 0.32, 0.16), ld.paint("tote", "bea/tote", tier="costume"), C, bevel=0.03), 2))
        bpy.data.objects["BEA_TOTE"].rotation_euler = (0, 0, yaw)
    elif name == "KAI":
        _phone("kai", P(0.24, 0, 0.88), head_c, C, red_button=True)
    return obs


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
