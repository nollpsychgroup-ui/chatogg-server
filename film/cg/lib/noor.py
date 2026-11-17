"""Noor, sculpted to design/sheets/noor.svg (head + torso, painted treatment).

Head built by deforming a sphere in a local frame (x = her lateral, y = forward, z = up):
an egg cranium, narrowed jaw, flat cheek planes, SHALLOW eye sockets and brow (style guide 2.3:
faces designed for top light), nose wedge, lips, ears; real eyes (pale sclera, mid-dark iris,
glossy cornea that reflects the real panels) with an upper lid at her neutral lid_up 0.82 and a
firm lid line; painted brows; hair in a low bun with one loose lock (it appears after the
emergency-handle beat). Torso: the upright rectangle -- squared blazer shoulders, open lapels
over the pale blouse, the red strap and badge dead centre.
Rig controls (expressions/face-rig.md) are exposed as build parameters for now: lid_up, brow_in,
smile, press, gaze; M4 turns them into shape keys.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import lookdev as ld
from .common import link
from .mesh import _obj, ellipsoid, limb, box

NEUTRAL = dict(lid_up=0.82, brow_in=0.0, smile=0.0, press=0.0, gaze_x=0.0, gaze_y=0.0, loose_lock=False)


def _gauss(p, c, r):
    return math.exp(-((p - c).length_squared) / (r * r))


def _head_mesh(name, M, skin, coll):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=56, v_segments=40, radius=1.0)
    bumps = [  # (centre in head space, radius, displacement along normal)
        (Vector((0.031, 0.075, 0.012)), 0.016, -0.0045), (Vector((-0.031, 0.075, 0.012)), 0.016, -0.0045),   # shallow sockets
        (Vector((0.033, 0.080, 0.036)), 0.014, 0.0025), (Vector((-0.033, 0.080, 0.036)), 0.014, 0.0025),      # soft brow
        (Vector((0.047, 0.060, -0.012)), 0.020, 0.0045), (Vector((-0.047, 0.060, -0.012)), 0.020, 0.0045),   # cheekbones
        (Vector((0.0, 0.070, -0.095)), 0.020, 0.005),                                                         # chin
        (Vector((0.0, 0.088, -0.050)), 0.020, 0.003),                                                         # muzzle
    ]
    for v in bm.verts:
        d = v.co.copy()
        x, y, z = d.x * 0.071, d.y * 0.090, d.z * 0.113
        if z < 0:  # jaw narrows toward the chin
            t = min(1.0, -z / 0.11)
            x *= 1.0 - 0.32 * t * t
            if y < 0:
                y *= 1.0 - 0.35 * t
        if z > 0 and y < 0:  # fuller back of skull
            y *= 1.06
        if y > 0.05:  # flatter front planes (forehead, cheeks)
            y = 0.05 + (y - 0.05) * 0.85
        p = Vector((x, y, z))
        n = Vector((x / 0.071 ** 2, y / 0.090 ** 2, z / 0.113 ** 2)).normalized()
        for c, r, dd in bumps:
            p += n * dd * _gauss(p, c, r)
        v.co = p
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return _obj(name, bm, skin, coll, smooth=True)


def _cap(name, M, hair, coll):
    """Hair cap: a slightly larger shell, trimmed to a hairline (forehead, temples, nape)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=28, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.077, v.co.y * 0.097, v.co.z * 0.120)) + Vector((0, -0.004, 0.004))
    # hair pulled back to a low bun: hairline high on the forehead, temples and ears clear
    kill = [v for v in bm.verts if (v.co.y > 0.015 and v.co.z < 0.088 - 0.35 * abs(v.co.x))
            or (v.co.z < 0.02 and v.co.y > -0.045) or v.co.z < -0.07]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.004)
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return _obj(name, bm, hair, coll, smooth=True)


def _lid(name, M, center, r, lid_up, skin, coll):
    """Upper lid: spherical shell over the eye, cut at the lid height. lid_up 1 = wide, 0 = closed."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=r)
    cut_z = r * (-0.3 + 0.9 * lid_up)          # 0.82 -> lid edge just over the iris top
    kill = [v for v in bm.verts if v.co.z < cut_z or v.co.y < -r * 0.2]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    ob = _obj(name, bm, skin, coll, smooth=True)
    return ob, cut_z


def skin_mat():
    return ld.paint("noor_skin", "noor/skin", tier="face", shadow="noor/skin_shadow", axis="z", stretch=1.6,
                    variation=0.04, shadow_mix=0.2, tilt=0.09)


def build(head_c, f, lat, coll, pal_prefix="noor", params=None):
    """Sculpted head at head_c (world), facing f. Returns created objects (pass index 1 = face)."""
    P = dict(NEUTRAL)
    P.update(params or {})
    up = Vector((0, 0, 1))
    R = Matrix((lat, f, up)).transposed()
    M = Matrix.Translation(head_c) @ R.to_4x4()
    W = lambda v: M @ Vector(v)  # head space -> world
    skin = skin_mat()
    hair = ld.paint("noor_hair", "noor/hair", tier="costume", stroke_scale=90.0, stretch=6.0, axis="z", variation=0.4)
    lips = ld.paint("noor_lips", "noor/lips", tier="face")
    line = ld.paint("lid_line", (0.006, 0.005, 0.005), tier="face", variation=0.0)
    sclera = ld.gloss("noor_sclera", (0.80, 0.79, 0.75), roughness=0.3)
    iris = ld.paint("noor_iris", "noor/iris", tier="face", variation=0.05)
    cornea = bpy.data.materials.get("cornea_glass")
    if cornea is None:
        cornea = bpy.data.materials.new("cornea_glass")
        cornea.use_nodes = True
        b = cornea.node_tree.nodes["Principled BSDF"]
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.0
        b.inputs["IOR"].default_value = 1.376
    obs = [_head_mesh("NOOR_HEAD", M, skin, coll)]
    # nose wedge
    obs.append(limb("NOOR_NOSE_BRIDGE", W((0, 0.083, 0.012)), W((0, 0.104, -0.026)), 0.006, skin, coll, r2=0.010, segs=12, smooth=True))
    obs.append(ellipsoid("NOOR_NOSE_TIP", W((0, 0.103, -0.031)), (0.0095, 0.009, 0.0085), skin, coll, segs=14, rot=R.to_3x3(), smooth=True))
    for s in (-1, 1):
        obs.append(ellipsoid(f"NOOR_NOSTRIL_{s}", W((s * 0.009, 0.089, -0.033)), (0.0045, 0.0045, 0.0035), skin, coll, segs=12, rot=R.to_3x3(), smooth=True))
    # mouth: lips + a firm mouth line; corners move with smile/press
    sm, pr = P["smile"], P["press"]
    obs.append(ellipsoid("NOOR_LIP_UP", W((0, 0.084, -0.055)), (0.020 + 0.003 * sm, 0.0055, 0.0045 * (1 - 0.4 * pr)), lips, coll, segs=14, rot=R.to_3x3(), smooth=True))
    obs.append(ellipsoid("NOOR_LIP_LOW", W((0, 0.082, -0.0635)), (0.017 + 0.003 * sm, 0.006, 0.0055 * (1 - 0.4 * pr)), lips, coll, segs=14, rot=R.to_3x3(), smooth=True))
    obs.append(limb("NOOR_MOUTH_LINE", W((-0.020, 0.0875, -0.0595 + 0.004 * sm)), W((0.020, 0.0875, -0.0595 + 0.004 * sm)), 0.0011, line, coll, segs=6, smooth=True))
    # ears
    for s in (-1, 1):
        obs.append(ellipsoid(f"NOOR_EAR_{s}", W((s * 0.070, -0.004, 0.0)), (0.009, 0.016, 0.027), skin, coll, segs=12, rot=R.to_3x3(), smooth=True))
    # eyes: sclera, iris, glossy cornea, upper lid + lid line, brows
    gx, gy = P["gaze_x"] * 0.004, P["gaze_y"] * 0.003
    for s in (-1, 1):
        ec = Vector((s * 0.031, 0.072, 0.012))
        obs.append(ellipsoid(f"NOOR_EYE_{s}", W(ec), (0.0128,) * 3, sclera, coll, segs=20, smooth=True))
        obs.append(ellipsoid(f"NOOR_IRIS_{s}", W(ec + Vector((gx, 0.0105, gy))), (0.0066, 0.0028, 0.0066), iris, coll, segs=18, rot=R.to_3x3(), smooth=True))
        obs.append(ellipsoid(f"NOOR_CORNEA_{s}", W(ec + Vector((gx, 0.0035, gy))), (0.0105, 0.0105, 0.0105), cornea, coll, segs=20, smooth=True))
        lid, cz = _lid(f"NOOR_LID_{s}", M, ec + Vector((0, 0.0012, 0)), 0.0140, P["lid_up"], skin, coll)
        obs.append(lid)
        y_edge = 0.0140 * math.sqrt(max(0.0, 1 - (cz / 0.0140) ** 2))
        obs.append(limb(f"NOOR_LIDLINE_{s}", W(ec + Vector((-0.012, y_edge * 0.75, cz))), W(ec + Vector((0.012, y_edge * 0.75, cz))),
                        0.0011, line, coll, segs=6, smooth=True))
        bi = P["brow_in"] * 0.004
        obs.append(limb(f"NOOR_BROW_{s}", W((s * 0.016, 0.086, 0.034 + bi)), W((s * 0.046, 0.079, 0.035)), 0.0026, hair, coll, r2=0.0016, segs=8, smooth=True))
    # hair: cap, low bun, one loose lock
    obs.append(_cap("NOOR_HAIR", M, hair, coll))
    obs.append(ellipsoid("NOOR_BUN", W((0, -0.098, -0.045)), (0.032, 0.026, 0.028), hair, coll, segs=16, rot=R.to_3x3(), smooth=True))
    if P["loose_lock"]:
        obs.append(limb("NOOR_LOCK", W((0.055, 0.05, 0.07)), W((0.068, 0.062, -0.02)), 0.004, hair, coll, r2=0.002, segs=8, smooth=True))
    for o in obs:
        o.pass_index = 1
    return obs


def torso(hip, sh, f, lat, coll, sw=1.0):
    """The upright rectangle: squared blazer shoulders, lapels open over the blouse."""
    up = Vector((0, 0, 1))
    R = Matrix((lat, f, up)).transposed()
    blazer = ld.paint("noor_blazer", "noor/suit", tier="costume", axis="z", stretch=3.0, shadow="noor/lapel", variation=0.16, tilt=0.22)
    blouse = ld.paint("noor_blouse", "noor/blouse", tier="costume", axis="z")
    lapel = ld.paint("noor_lapel", "noor/lapel", tier="costume", axis="z")
    obs = []
    mid = (hip + sh) / 2
    h = (sh - hip).z
    body = box("NOOR_BLAZER", mid + Vector((0, 0, 0.02)), (0.36 * sw, 0.21, h + 0.06), blazer, coll, bevel=0.03)
    body.rotation_euler = R.to_euler()
    # squared, padded blazer shoulders: a flattened ellipsoid that rounds into the neck
    shoulders = ellipsoid("NOOR_SHOULDERS", sh + Vector((0, 0, 0.02)), (0.225 * sw, 0.105, 0.075), blazer, coll, segs=16, rot=R.to_3x3(), smooth=True)
    obs += [body, shoulders]
    # blouse V and lapels, on the front plane
    front = mid + f * 0.106
    bl = box("NOOR_BLOUSE", front + Vector((0, 0, 0.12)), (0.11, 0.004, 0.20), blouse, coll)
    bl.rotation_euler = R.to_euler()
    obs.append(bl)
    for s in (-1, 1):
        lp = box(f"NOOR_LAPEL_{s}", front + lat * s * 0.07 + f * 0.003 + Vector((0, 0, 0.10)), (0.05, 0.006, 0.26), lapel, coll)
        lp.rotation_euler = (R @ Matrix.Rotation(-s * math.radians(14), 3, "Y")).to_euler()
        obs.append(lp)
    for o in obs:
        o.pass_index = 2
    return obs
