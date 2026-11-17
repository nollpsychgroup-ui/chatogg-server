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
from .mesh import box, ellipsoid, limb, plane, text


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


def _reach(info, target_name, t, D=None):
    """Replace the arm nearest `target_name` (evaluated at time t) with one reaching to it.
    PHONE_*_ENDCALL: the hand hovers 3 cm above the button with the thumb pointing down at it."""
    sc = bpy.context.scene
    keep = sc.frame_current
    sc.frame_set(t2f(t) + 1)
    tgt = bpy.data.objects[target_name].matrix_world.translation.copy()
    sc.frame_set(keep)
    obs = _coll_objects(info["collection"])
    wc = lambda o: o.matrix_world @ (sum((Vector(c) for c in o.bound_box), Vector()) / 8)
    hands = [o for o in obs if o.name.startswith("NOOR_HAND_")]
    hand = min(hands, key=lambda o: (wc(o) - tgt).length)
    side = hand.name.split(".")[0].rsplit("_", 1)[1]
    arm = [o for o in obs if o.name.split(".")[0] in (f"NOOR_UARM_{side}", f"NOOR_FARM_{side}", f"NOOR_HAND_{side}")]
    uarm = next(o for o in arm if o.name.startswith("NOOR_UARM_"))
    vs = sorted((uarm.matrix_world @ v.co for v in uarm.data.vertices), key=lambda v: -v.z)
    sh = sum(vs[:max(1, len(vs) // 10)], Vector()) / max(1, len(vs) // 10)
    m_arm, m_skin = uarm.active_material, hand.active_material
    C = info["collection"]
    for o in arm:
        bpy.data.objects.remove(o, do_unlink=True)
    endcall = "ENDCALL" in target_name
    if endcall:   # hand on the far side of the phone from the shot's camera, thumb reaching over the button
        shot = next((x for x in (D or dp())["shots"] if x["in"] <= t + 0.5 < x["out"]), None)
        cam = Vector(shot["camera_loc"]) if shot and shot.get("camera_loc") else tgt + Vector((0, -1, 0.3))
        away = (tgt - cam); away.z = 0; away.normalize()
        hp = tgt + away * 0.075 + Vector((0, 0, 0.06))
    else:
        hp = tgt + Vector((-0.05, 0, 0))
    elb = sh.lerp(hp, 0.5) + Vector((0, 0, -0.10))
    for o in (limb(f"NOOR_REACH_UARM_{side}", sh, elb, 0.05, m_arm, C, r2=0.042),
              limb(f"NOOR_REACH_FARM_{side}", elb, hp, 0.04, m_arm, C, r2=0.032)):
        o.pass_index = 2
    ellipsoid(f"NOOR_REACH_HAND_{side}", hp, (0.04, 0.03, 0.03) if endcall else (0.045, 0.035, 0.04), m_skin, C).pass_index = 1
    if endcall:   # the thumb, hovering ~1.5 cm over the red button
        limb(f"NOOR_REACH_THUMB_{side}", hp + (tgt - hp) * 0.25, tgt + Vector((0, 0, 0.016)), 0.010, m_skin, C, r2=0.008).pass_index = 1


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
            if seg.get("reach_to"):
                _reach(info, seg["reach_to"], t0, D)
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


def _tex_mat(name, path, axes, size, alpha=False):
    """Matte image material. axes/size: object-space projection (e.g. ("y", "z") over 0.36 x 0.30 m,
    centred); None: the object's Generated coordinates. alpha: ink on transparent."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Roughness"].default_value = 0.9
    im = nt.nodes.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(path, check_existing=True)
    im.extension = "CLIP"
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if axes:
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        for k, (ax, sz) in enumerate(zip(axes, size)):
            mad = nt.nodes.new("ShaderNodeMath"); mad.operation = "MULTIPLY_ADD"
            nt.links.new(sep.outputs[ax.upper()], mad.inputs[0])
            mad.inputs[1].default_value, mad.inputs[2].default_value = 1.0 / sz, 0.5
            nt.links.new(mad.outputs[0], comb.inputs[k])
        nt.links.new(comb.outputs[0], im.inputs[0])
    else:
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(sep.outputs["Y"], comb.inputs[0])
        nt.links.new(sep.outputs["Z"], comb.inputs[1])
        nt.links.new(comb.outputs[0], im.inputs[0])
    nt.links.new(im.outputs["Color"], bs.inputs["Base Color"])
    if alpha:
        nt.links.new(im.outputs["Alpha"], bs.inputs["Alpha"])
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    return mat


def build_walter(D, BL):
    marks = D["set"]["marks"]
    paper = bpy.data.objects["WALTER_PAPER"]
    up0, up1 = BL["walter_paper"]["up"]
    rest_loc, rest_rot = tuple(paper.location), tuple(paper.rotation_euler)
    nl = Vector(marks["NEWSPAPER"])
    # the written face (+X) turned to the insert camera (shots 22/23), so the margin notes read
    ins = next(s for s in D["shots"] if s.get("aim_subject") == "NEWSPAPER" and s.get("camera_loc"))
    cam = Vector(ins["camera_loc"])
    yaw = math.atan2(cam.y - nl.y, cam.x - nl.x)
    tilt = -math.atan2(cam.z - nl.z, (cam.xy - nl.xy).length)
    up_rot = (0, tilt, yaw)
    for f, loc, rot in ((0, rest_loc, rest_rot), (t2f(up0), rest_loc, rest_rot), (t2f(up0) + 12, tuple(nl), up_rot),
                        (t2f(up1), tuple(nl), up_rot), (t2f(up1) + 12, rest_loc, rest_rot)):
        paper.location, paper.rotation_euler = loc, rot
        paper.keyframe_insert("location", frame=f)
        paper.keyframe_insert("rotation_euler", frame=f)
    # newsprint page + the two handwritten notes (props/props.md section 2), textures from lib/props_tex.py
    from . import props_tex
    tex = props_tex.build_textures()
    paper.data.materials.clear()
    paper.data.materials.append(_tex_mat("newsprint_page", tex["page"][0], ("y", "z"), (0.36, 0.30)))
    for i, (key, (y0, z0)) in enumerate((("note_walter", (-0.165, 0.085)), ("note_bea", (-0.165, 0.005)))):
        path, w, h = tex[key]
        note = plane(f"MARGIN_NOTE_{i}", (0, 0, 0), (w, h), _tex_mat(key, path, None, None, alpha=True), normal="X",
                     collection="PROPS_LOOSE")
        note.parent = paper
        note.location = (0.0115, y0 + w / 2, z0 - h / 2 + 0.03)
        note.rotation_euler = (0, 0, 0)
        note.pass_index = 2
        t, _ = BL["walter_paper"]["notes"][i]
        key_visibility([note], [(t, up1 + 0.5)])
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
