"""Small mesh-building helpers (bmesh, real-world sizes, no object scale)."""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from .common import link


def _obj(name, bm, mat, coll, loc=(0, 0, 0), smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if mat is not None:
        me.materials.append(mat)
    link(ob, coll)
    return ob


def box(name, center, size, mat, coll="SET", bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=2, affect="EDGES")
    return _obj(name, bm, mat, coll, loc=center)


def plane(name, center, size, mat, coll="SET", normal="Z"):
    """Axis-aligned rectangle. normal: 'Z', '-Z', 'X', '-X', 'Y', '-Y'."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    sx, sy = size
    bmesh.ops.scale(bm, vec=Vector((sx, sy, 1)), verts=bm.verts)
    rot = {
        "Z": Matrix.Identity(4),
        "-Z": Matrix.Rotation(math.pi, 4, "X"),
        "X": Matrix.Rotation(math.pi / 2, 4, "Y") @ Matrix.Rotation(math.pi / 2, 4, "Z"),
        "-X": Matrix.Rotation(-math.pi / 2, 4, "Y") @ Matrix.Rotation(math.pi / 2, 4, "Z"),
        "Y": Matrix.Rotation(-math.pi / 2, 4, "X"),
        "-Y": Matrix.Rotation(math.pi / 2, 4, "X"),
    }[normal]
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    return _obj(name, bm, mat, coll, loc=center)


def limb(name, a, b, r, mat, coll="CHARACTERS", r2=None, segs=12):
    """Tapered capsule-ish cylinder from a to b (world points), with spherical caps."""
    a, b = Vector(a), Vector(b)
    d = b - a
    ln = d.length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r2 if r2 else r, depth=ln)
    for v, rr, z in ((None, r, -ln / 2), (None, r2 if r2 else r, ln / 2)):
        res = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=8, radius=rr)
        bmesh.ops.translate(bm, vec=Vector((0, 0, z)), verts=res["verts"])
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.transform(bm, matrix=q.to_matrix().to_4x4(), verts=bm.verts)
    return _obj(name, bm, mat, coll, loc=(a + b) / 2, smooth=True)


def ellipsoid(name, center, radii, mat, coll="CHARACTERS", segs=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2 + 2, radius=1.0)
    bmesh.ops.scale(bm, vec=Vector(radii), verts=bm.verts)
    return _obj(name, bm, mat, coll, loc=center, smooth=True)


def text(name, body, loc, size, mat, rot=(math.pi / 2, 0, -math.pi / 2), coll="SET", align="CENTER", extrude=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.extrude = extrude
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = rot
    cu.materials.append(mat)
    link(ob, coll)
    return ob
