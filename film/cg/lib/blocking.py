"""Previs blocking (Milestone 4, pass 1), driven by data/blocking.json + the Designer's expression tracks.

Noor is built as pose variants (seated lap / phone at ear / phone in lap, standing at the doors, beside
Walter, at Kai's seat, at her seat, on the platform, and walking) and switched by keyed visibility.
Walk variants slide from mark to mark: blocking, not animation. Walter holds the margin note up and
clamps Noor's wrist; the lanyard is thrown at 7.6. Faces: design/expressions/shot_expressions.json via
heads.apply_track on every head rig. Everything is keyed on the cues.json clock (frame = round(t*24)).
"""
import json
import math
import os

import bpy
from mathutils import Vector

from . import figures, lookdev as ld
from .common import FILM_DIR, coll, dp, link, load, t2f
from .mesh import box, limb, text


def key_visibility(obs, intervals, fps=24):
    """Visible only inside the given [t0, t1) intervals (constant keys)."""
    keys = {0: True}
    for t0, t1 in sorted(intervals):
        keys[t2f(t0, fps)] = False
        keys[t2f(t1, fps)] = True
    for ob in obs:
        for f in sorted(keys):
            ob.hide_render = keys[f]
            ob.hide_viewport = keys[f]
            ob.keyframe_insert("hide_render", frame=f)
            ob.keyframe_insert("hide_viewport", frame=f)


def _coll_objects(name):
    return list(bpy.data.collections[name].all_objects)


def _intersect(intervals, t_max=None, t_min=None):
    out = []
    for a, b in intervals:
        if t_max is not None:
            b = min(b, t_max)
        if t_min is not None:
            a = max(a, t_min)
        if b > a:
            out.append((a, b))
    return out


def build_noor(D, B, BL):
    variants = {}   # key -> {"collection", "intervals", "root"}
    for i, seg in enumerate(BL["NOOR"]):
        t0, t1 = seg["t"]
        if seg["kind"] == "seat":
            key = f"seat_{seg['pose']}"
            if key not in variants:
                info = figures.figure("NOOR", D, B, pose=seg["pose"], collection=f"CHAR_NOOR_{key}")
                variants[key] = dict(info, intervals=[])
            variants[key]["intervals"].append((t0, t1))
        elif seg["kind"] == "stand":
            key = f"stand_{i:02d}"
            at = list(seg["at"]) + [0.0]
            info = figures.figure("NOOR", D, B, pose=seg.get("pose", "standing"), at=at, standing=True,
                                  facing=seg["facing"], collection=f"CHAR_NOOR_{key}")
            variants[key] = dict(info, intervals=[(t0, t1)])
            if seg.get("platform"):
                rig = bpy.data.objects["PLATFORM_RIG"]
                for ob in _coll_objects(info["collection"]):
                    if ob.parent is None:
                        ob.parent = rig
                        ob.matrix_parent_inverse = rig.matrix_world.inverted()
        elif seg["kind"] == "walk":
            key = f"walk_{i:02d}"
            fr = list(seg["from"]) + [0.0]
            info = figures.figure("NOOR", D, B, pose="standing_down", at=fr, standing=True,
                                  facing=seg["facing"], collection=f"CHAR_NOOR_{key}")
            root = bpy.data.objects.new(f"NOOR_{key}_ROOT", None)
            root.location = (fr[0], fr[1], 0)
            link(root, info["collection"])
            bpy.context.view_layer.update()
            for ob in _coll_objects(info["collection"]):
                if ob.parent is None and ob is not root:
                    ob.parent = root
                    ob.matrix_parent_inverse = root.matrix_world.inverted()
            for t, xy in ((t0, seg["from"]), (t1, seg["to"])):
                root.location = (xy[0], xy[1], 0)
                root.keyframe_insert("location", frame=t2f(t))
            for fc in root.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
            variants[key] = dict(info, intervals=[(t0, t1)])
    throw = BL["lanyard_throw_t"]
    for key, v in variants.items():
        obs = _coll_objects(v["collection"])
        strap = [o for o in obs if o.name.startswith(("NOOR_STRAP", "NOOR_BADGE"))]
        key_visibility([o for o in obs if o not in strap], v["intervals"])
        key_visibility(strap, _intersect(v["intervals"], t_max=throw))
    # the lanyard on the floor from 7.6 (LANYARD_FLOOR mark)
    m = D["set"]["marks"]["LANYARD_FLOOR"]
    red = bpy.data.materials["the_red_strap"]
    pts = [(-0.15, 0.15), (0.05, 0.25), (0.18, 0.12), (0.15, -0.08), (-0.05, -0.12)]
    floor = []
    for i in range(len(pts) - 1):
        a = (m[0] + pts[i][0], m[1] + pts[i][1], 0.0125)
        b = (m[0] + pts[i + 1][0], m[1] + pts[i + 1][1], 0.0125)
        o = limb(f"STRAP_FLOOR_{i}", a, b, 0.0125, red, "PROPS_LOOSE")
        o.pass_index = 1
        floor.append(o)
    bd = box("BADGE_FLOOR", (m[0] - 0.12, m[1] + 0.02, 0.006), (0.075, 0.10, 0.006), bpy.data.materials["badge_plastic"], "PROPS_LOOSE")
    bd.rotation_euler = (0, 0, math.radians(30))
    bd.pass_index = 1
    floor.append(bd)
    key_visibility(floor, [(throw, 10_000)])
    return variants


def build_walter(D, BL):
    marks = D["set"]["marks"]
    paper = bpy.data.objects["WALTER_PAPER"]
    up0, up1 = BL["walter_paper"]["up"]
    rest_loc, rest_rot = tuple(paper.location), tuple(paper.rotation_euler)
    nl = Vector(marks["NEWSPAPER"])
    # face the paper toward the aisle / the insert cameras
    for f, loc, rot in ((0, rest_loc, rest_rot), (t2f(up0), rest_loc, rest_rot), (t2f(up0) + 12, tuple(nl), (0, 0, math.radians(15))),
                        (t2f(up1), tuple(nl), (0, 0, math.radians(15))), (t2f(up1) + 12, rest_loc, rest_rot)):
        paper.location, paper.rotation_euler = loc, rot
        paper.keyframe_insert("location", frame=f)
        paper.keyframe_insert("rotation_euler", frame=f)
    ink = ld.paint("pen_ink", "props/pen_ink", tier="face", variation=0.0)
    for i, (t, body) in enumerate(BL["walter_paper"]["notes"]):
        tx = text(f"MARGIN_NOTE_{i}", body, (0.012, 0.06 - i * 0.09, 0.05 - i * 0.07), 0.028, ink,
                  rot=(math.pi / 2, 0, math.pi / 2), collection="PROPS_LOOSE")
        tx.parent = paper
        tx.pass_index = 2
        key_visibility([tx], [(t, up1 + 0.5)])
    # the wrist clamp: the fastest motion in the film (2 frames), held to the release
    c0, c1 = BL["walter_clamp"]
    head = bpy.data.objects["WALTER_HEADRIG"].matrix_world.translation
    wrist = Vector(marks["WRIST"])
    sh = Vector((head.x, head.y - 0.19, head.z - 0.27))
    elb = sh.lerp(wrist, 0.5) + Vector((0, 0, -0.08))
    arm_m = bpy.data.materials["c_walter_coat"]
    skin = bpy.data.materials.get("c_walter_skin_face") or bpy.data.materials["c_walter_skin"]
    clamp = [limb("WALTER_CLAMP_UARM", sh, elb, 0.05, arm_m, "CHAR_WALTER", r2=0.042),
             limb("WALTER_CLAMP_FARM", elb, wrist, 0.042, arm_m, "CHAR_WALTER", r2=0.034)]
    hand = limb("WALTER_CLAMP_HAND", wrist - Vector((0.03, 0, 0)), wrist + Vector((0.03, 0, 0)), 0.04, skin, "CHAR_WALTER")
    clamp.append(hand)
    for o in clamp:
        o.pass_index = 2
    key_visibility(clamp, [(c0, c1)])
    orig = [bpy.data.objects[n] for n in ("WALTER_UARM_-1", "WALTER_FARM_-1", "WALTER_HAND_-1") if n in bpy.data.objects]
    key_visibility(orig, [(0, c0), (c1, 10_000)])


def apply_faces():
    import heads  # design/rig on sys.path via figures
    J = json.load(open(os.path.join(FILM_DIR, "design", "expressions", "shot_expressions.json")))
    for name, track in J["tracks"].items():
        roots = [o for o in bpy.data.objects if o.name.startswith(f"{name}_HEADRIG")]
        for r in roots:
            heads.apply_track(r, track, J["library"], fps=J.get("fps", 24))


def build(D=None, B=None):
    D = D or dp()
    B = B or load("build.json")
    BL = load("blocking.json")
    for n in ("WALTER", "BEA", "KAI"):
        figures.figure(n, D, B)
    figures.animate_kai(D)
    v = build_noor(D, B, BL)
    build_walter(D, BL)
    apply_faces()
    return v
