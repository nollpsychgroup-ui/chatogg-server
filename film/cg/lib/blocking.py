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


def _walk_cycle(info, root, facing, hz=0.9, swing_deg=22.0, bob=0.018):
    """Previs walk: each leg (thigh, shin, shoe) swings as one piece about its hip, opposite legs in
    antiphase, with a two-per-cycle body bob on the walk root. Frame-driven (no keys)."""
    obs = _coll_objects(info["collection"])
    lat_x = abs(facing[1]) >= abs(facing[0])   # walking along Y -> swing about X
    idx = 0 if lat_x else 1
    sgn = (1 if facing[1] > 0 else -1) if lat_x else (-1 if facing[0] > 0 else 1)
    w = f"frame*6.283185*{hz}/24"
    for side, ph in (("-1", 0.0), ("1", math.pi)):
        legs = [o for o in obs if o.name.split(".")[0] in (f"NOOR_THIGH_{side}", f"NOOR_SHIN_{side}", f"NOOR_SHOE_{side}")]
        thigh = next((o for o in legs if o.name.startswith("NOOR_THIGH_")), None)
        if thigh is None:
            continue
        vs = sorted((thigh.matrix_world @ v.co for v in thigh.data.vertices), key=lambda v: -v.z)
        hip = sum(vs[:max(1, len(vs) // 10)], Vector()) / max(1, len(vs) // 10)
        piv = bpy.data.objects.new(f"NOOR_HIP_{side}_{root.name}", None)
        link(piv, info["collection"])
        piv.location = hip
        bpy.context.view_layer.update()
        piv.parent = root
        piv.matrix_parent_inverse = root.matrix_world.inverted()
        bpy.context.view_layer.update()
        for o in legs:
            mw = o.matrix_world.copy()
            o.parent = piv
            o.matrix_parent_inverse = piv.matrix_world.inverted()
            o.matrix_world = mw
        d = piv.driver_add("rotation_euler", idx).driver
        d.type = "SCRIPTED"
        d.expression = f"{sgn * math.radians(swing_deg):.4f}*sin({w}+{ph:.4f})"
    d = root.driver_add("delta_location", 2).driver
    d.type = "SCRIPTED"
    d.expression = f"{bob}*abs(sin({w}))"


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
            _walk_cycle(info, root, seg["facing"])
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
    if "v2" not in str(J.get("clock", "")):   # tracks still on the original clock: map them (DP trims)
        from .common import clock_map
        m = clock_map()
        J["tracks"] = {k: [[round(m(t), 3)] + list(rest) for t, *rest in tr] for k, tr in J["tracks"].items()}
    for name, track in J["tracks"].items():
        roots = [o for o in bpy.data.objects if o.name.startswith(f"{name}_HEADRIG")]
        for r in roots:
            heads.apply_track(r, track, J["library"], fps=J.get("fps", 24))
            _head_pitch(r, track, J["library"], J.get("fps", 24))
    return J


def apply_look_ats(D, BL, J, ease=4, step=2):
    """Story looks (Director: the plants and guilt live in them): from the key of each listed expression
    until that character's next key (or the end of the shot), aim gaze_x/gaze_y at the real target.
    Computed from the evaluated scene every `step` frames (heads breathe, pitch and walk), with an
    `ease`-frame blend from and back to the expression track's own gaze at each edge."""
    from bpy_extras import anim_utils
    sc = bpy.context.scene
    fps = J.get("fps", 24)
    shots = D["shots"]
    keep = sc.frame_current
    n = 0
    for la in BL.get("look_at", []):
        track = J["tracks"][la["who"]]
        for i, (t, name, *_) in enumerate(track):
            if name != la["expr"]:
                continue
            nxt = track[i + 1][0] if i + 1 < len(track) else t + 5
            sh = next((x for x in shots if x["in"] <= t < x["out"]), None)
            t1 = min(nxt, sh["out"]) if sh else nxt
            f0, f1 = round(t * fps), round(t1 * fps)
            for root in [o for o in bpy.data.objects if o.name.startswith(f"{la['who']}_HEADRIG")]:
                ad = root.animation_data
                cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
                fcs = {c: next(fc for fc in cb.fcurves if fc.data_path == f'["{c}"]') for c in ("gaze_x", "gaze_y")}
                edge = {c: (fc.evaluate(f0 - ease), fc.evaluate(f1 + ease)) for c, fc in fcs.items()}
                vals = {}
                for f in list(range(f0, f1, step)) + [f1]:
                    sc.frame_set(f)
                    tg = [o for o in bpy.data.objects if o.name.startswith(la["target"]) and not o.hide_render]
                    if not tg:
                        continue
                    d = root.matrix_world.inverted() @ tg[0].matrix_world.translation
                    yaw = math.degrees(math.atan2(d.x, d.y))
                    down = math.degrees(math.atan2(-d.z, math.hypot(d.x, d.y)))
                    # beyond the eyes' 28 deg the head turns too (up to 40 deg), eyes take the rest
                    head = max(-40.0, min(40.0, yaw - max(-28.0, min(28.0, yaw)) * 0.6)) if abs(yaw) > 28 else 0.0
                    vals[f] = (max(-1, min(1, (yaw - head) / 28.0)), max(-1, min(1, down / 20.0)), head)
                if not vals:
                    continue
                if any(v[2] for v in vals.values()):   # head turn: world-Z delta (delta composes in parent space)
                    base = root.delta_rotation_euler[2]
                    root.delta_rotation_euler[2] = base
                    root.keyframe_insert("delta_rotation_euler", index=2, frame=f0 - ease * 2)
                    for f, v in vals.items():
                        root.delta_rotation_euler[2] = base - math.radians(v[2])
                        root.keyframe_insert("delta_rotation_euler", index=2, frame=f)
                    root.delta_rotation_euler[2] = base
                    root.keyframe_insert("delta_rotation_euler", index=2, frame=f1 + ease * 2)
                for c, fc in fcs.items():
                    for j in reversed(range(len(fc.keyframe_points))):   # by index: refs go stale on removal
                        if f0 - ease <= fc.keyframe_points[j].co.x <= f1 + ease:
                            fc.keyframe_points.remove(fc.keyframe_points[j])
                    fc.keyframe_points.insert(f0 - ease, edge[c][0])
                    fc.keyframe_points.insert(f1 + ease, edge[c][1])
                    for f, v in vals.items():
                        fc.keyframe_points.insert(f, v[0] if c == "gaze_x" else v[1])
                n += 1
    sc.frame_set(keep)
    return n


def _head_pitch(root, track, library, fps, ease=10):
    """Pose hint head_pitch_deg (Designer): tip the head down (chin toward the paper) about the rig's
    lateral axis. Keyed on delta_rotation_euler so the rig's own placement is untouched; each change
    eases over `ease` frames ending on the key (the lift to Noor at speech_end is the acting beat)."""
    from mathutils import Quaternion
    # delta rotation composes in parent space, so pitch about the WORLD lateral axis (up x forward)
    bpy.context.view_layer.update()
    fwd = root.matrix_world.to_3x3() @ Vector((0, 1, 0))
    fwd.z = 0
    fwd.normalize()
    axis = Vector((0, 0, 1)).cross(fwd)

    def put(deg, frame):
        root.delta_rotation_euler = Quaternion(axis, math.radians(deg)).to_euler()
        root.keyframe_insert("delta_rotation_euler", frame=frame)

    prev = 0.0
    keyed = False
    for t, name, *_ in track:
        p = float(library.get(name, {}).get("head_pitch_deg", 0.0))
        if p == prev:
            continue
        f = round(t * fps)
        put(prev, max(0, f - ease))
        put(p, f)
        prev, keyed = p, True
    return keyed


BREATH = {"NOOR": (4.2, 0.0), "WALTER": (5.2, 1.3), "BEA": (4.7, 2.9), "KAI": (3.8, 4.1)}   # period s, phase rad
LOWER = ("THIGH", "SHIN", "SHOE", "PELVIS", "_ROOT", "FLOOR")


def add_idles(amp=0.004):
    """Every figure breathes, always (Director: only the sleeping car is still): the upper body and head
    rise and settle a few mm on each character's own period. Drivers on delta_location, so they add to
    the placed poses, walks and the platform slide without touching their keys. Frame-driven and
    deterministic (asleep frames stay identical frame to frame only where nobody is in shot)."""
    n = 0
    for c in bpy.data.collections:
        if not c.name.startswith("CHAR_"):
            continue
        who = c.name.split("_")[1]
        per, ph = BREATH.get(who, (4.5, 0.0))
        for ob in c.objects:
            if any(k in ob.name for k in LOWER) or (ob.parent is not None and ob.parent.name in c.objects):
                continue
            d = ob.driver_add("delta_location", 2).driver
            d.type = "SCRIPTED"
            d.expression = f"{amp}*0.5*(1-cos(frame*6.283185/{per * 24:.1f}+{ph}))"
            n += 1
    return n


def build_bea_reach(D, BL):
    """Shot 15: Bea's hand shoots out toward Kai ('don't'), far too far away. Her nearer arm is swapped
    for an almost straight arm aimed at him for the beat (a pop, like Walter's clamp)."""
    br = BL.get("bea_reach")
    if not br:
        return
    t0, t1 = br["t"]
    C = "CHAR_BEA"
    obs = list(bpy.data.collections[C].objects)
    tgt = Vector(D["set"]["marks"][br["toward"]])
    wc = lambda o: o.matrix_world @ (sum((Vector(c) for c in o.bound_box), Vector()) / 8)
    hand = min([o for o in obs if o.name.startswith("BEA_HAND_")], key=lambda o: (wc(o) - tgt).length)
    side = hand.name.split(".")[0].rsplit("_", 1)[1]
    arm = [o for o in obs if o.name.split(".")[0] in (f"BEA_UARM_{side}", f"BEA_FARM_{side}", f"BEA_HAND_{side}")]
    uarm = next(o for o in arm if o.name.startswith("BEA_UARM_"))
    vs = sorted((uarm.matrix_world @ v.co for v in uarm.data.vertices), key=lambda v: -v.z)
    sh = sum(vs[:max(1, len(vs) // 10)], Vector()) / max(1, len(vs) // 10)
    d = (tgt - sh); d.z = 0.0; d.normalize()
    fwd = Vector(D["set"]["marks"]["BEA"]); fwd = Vector((-1.0 if fwd.x > 0 else 1.0, 0, 0))   # into the aisle
    # "don't": fast and urgent, forward toward Kai at chest-to-shoulder height, out in the aisle so it
    # reads past her body from B (Director), not raised like a hail
    d = (d * 0.75 + fwd * 0.45 + Vector((0, 0, 0.02))).normalized()
    hp = sh + d * br["reach_m"]
    elb = sh.lerp(hp, 0.5) + Vector((0, 0, -0.02))
    side_v = d.cross(Vector((0, 0, 1))).normalized()
    new = [limb("BEA_REACH_UARM", sh, elb, 0.05, uarm.active_material, C, r2=0.042),
           limb("BEA_REACH_FARM", elb, hp, 0.04, uarm.active_material, C, r2=0.032),
           # open palm toward him: a flat paddle facing along the reach, fingers spread
           ellipsoid("BEA_REACH_HAND", hp + d * 0.03, (0.012, 0.05, 0.055), hand.active_material, C,
                     rot=d.to_track_quat("X", "Z").to_matrix())]
    for k in (-2, -1, 0, 1, 2):
        a = hp + d * 0.04 + side_v * (0.022 * k) + Vector((0, 0, 0.045 - 0.006 * abs(k)))
        new.append(limb(f"BEA_REACH_FINGER_{k + 2}", a, a + d * 0.01 + side_v * 0.012 * k + Vector((0, 0, 0.045)),
                        0.008, hand.active_material, C, segs=8))
    for o in new:
        o.pass_index = 2
    for o in new[2:]:
        o.pass_index = 1
    key_visibility(new, [(t0, t1)])
    key_visibility(arm, [(0, t0), (t1, 10_000)])
    # the body leans out of the seat after the arm: upper body and head slide ~7 cm along the reach
    lean = d.copy(); lean.z = 0; lean = lean.normalized() * 0.07
    f0, f1 = t2f(t0), t2f(t1)
    for ob in bpy.data.collections[C].objects:
        if any(k in ob.name for k in LOWER) or ob in new or (ob.parent is not None and ob.parent.name in bpy.data.collections[C].objects):
            continue
        for f, v in ((f0, Vector()), (f0 + 3, lean), (f1 - 4, lean), (f1 + 6, Vector())):
            ob.delta_location[0], ob.delta_location[1] = v.x, v.y
            ob.keyframe_insert("delta_location", index=0, frame=f)
            ob.keyframe_insert("delta_location", index=1, frame=f)
    # the reach itself rides with the lean
    for o in new:
        o.delta_location[0], o.delta_location[1] = lean.x, lean.y


def build(D=None, B=None):
    D = D or dp()
    B = B or load("build.json")
    BL = load("blocking.json")
    for n in ("WALTER", "BEA", "KAI"):
        figures.figure(n, D, B)
    figures.animate_kai(D)
    v = build_noor(D, B, BL)
    build_walter(D, BL)
    build_bea_reach(D, BL)
    J = apply_faces()
    add_idles()
    apply_look_ats(D, BL, J)
    return v
