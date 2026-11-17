"""Mesh helpers (bmesh, real-world sizes, no object scale) and section-split building."""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from .common import coll, link


def _obj(name, bm, mat, collection, loc=(0, 0, 0), smooth=False):
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
    link(ob, collection)
    return ob


def box(name, center, size, mat, collection="SET", bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=2, affect="EDGES")
    return _obj(name, bm, mat, collection, loc=center)


def plane(name, center, size, mat, collection="SET", normal="Z"):
    """Axis-aligned rectangle facing `normal`. size = (u, v):
    Z/-Z: (x, y); X/-X: (y, z); Y/-Y: (x, z)."""
    u, v = size[0] / 2, size[1] / 2
    ax = normal[-1]
    sgn = -1 if normal.startswith("-") else 1
    if ax == "Z":
        pts = [(-u, -v, 0), (u, -v, 0), (u, v, 0), (-u, v, 0)]
    elif ax == "X":
        pts = [(0, -u, -v), (0, u, -v), (0, u, v), (0, -u, v)]
    else:
        pts = [(-u, 0, -v), (-u, 0, v), (u, 0, v), (u, 0, -v)]
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    f = bm.faces.new(vs)
    bm.normal_update()
    want = Vector({"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[ax]) * sgn
    if f.normal.dot(want) < 0:
        bmesh.ops.reverse_faces(bm, faces=[f])
    return _obj(name, bm, mat, collection, loc=center)


def limb(name, a, b, r, mat, collection="CHARACTERS", r2=None, segs=16, smooth=True):
    a, b = Vector(a), Vector(b)
    d = b - a
    ln = max(d.length, 1e-4)
    bm = bmesh.new()
    r2 = r2 if r2 else r
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r2, depth=ln)
    for rr, z in ((r, -ln / 2), (r2, ln / 2)):
        res = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=8, radius=rr)
        bmesh.ops.translate(bm, vec=Vector((0, 0, z)), verts=res["verts"])
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.transform(bm, matrix=q.to_matrix().to_4x4(), verts=bm.verts)
    return _obj(name, bm, mat, collection, loc=(a + b) / 2, smooth=smooth)


def ellipsoid(name, center, radii, mat, collection="CHARACTERS", segs=20, rot=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2 + 2, radius=1.0)
    bmesh.ops.scale(bm, vec=Vector(radii), verts=bm.verts)
    if rot is not None:
        bmesh.ops.transform(bm, matrix=rot.to_4x4(), verts=bm.verts)
    return _obj(name, bm, mat, collection, loc=center, smooth=smooth)


def text(name, body, loc, size, mat, rot=(math.pi / 2, 0, 0), collection="SET", align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = rot
    cu.materials.append(mat)
    link(ob, collection)
    return ob


# ----------------------------------------------------------------------------- sections

class Sections:
    """Splits along-the-car geometry at the panel joins and records which panel's section each
    piece belongs to, so each panel's direct light can be linked to its own section
    (virtual baffles: the DP's hard edge for cue 7)."""

    def __init__(self, bounds):
        self.bounds = bounds          # {"P1": (lo, hi), ...}
        self.members = {p: [] for p in bounds}

    def which(self, y):
        for p, (lo, hi) in self.bounds.items():
            if lo - 1e-6 <= y <= hi + 1e-6:
                return p
        return None

    def assign(self, ob, panels):
        for p in panels:
            self.members[p].append(ob)

    def ybox(self, name, x, y0, y1, z, sx, sz, mat, collection="SET", bevel=0.0):
        """Box spanning y0..y1, cut at section joins."""
        cuts = sorted({y0, y1} | {b for lo_hi in self.bounds.values() for b in lo_hi if y0 < b < y1})
        obs = []
        for i in range(len(cuts) - 1):
            a, b = cuts[i], cuts[i + 1]
            ob = box(f"{name}_{i:02d}", (x, (a + b) / 2, z), (sx, b - a, sz), mat, collection, bevel)
            self.assign(ob, [self.which((a + b) / 2)])
            obs.append(ob)
        return obs

    def yplane(self, name, x, y0, y1, z, su, normal, mat, collection="SET"):
        """Horizontal (Z/-Z, su = x size) or side-wall (X/-X, su = z size) plane along y0..y1, cut at joins."""
        cuts = sorted({y0, y1} | {b for lo_hi in self.bounds.values() for b in lo_hi if y0 < b < y1})
        obs = []
        for i in range(len(cuts) - 1):
            a, b = cuts[i], cuts[i + 1]
            if normal in ("Z", "-Z"):
                ob = plane(f"{name}_{i:02d}", (x, (a + b) / 2, z), (su, b - a), mat, collection, normal)
            else:
                ob = plane(f"{name}_{i:02d}", (x, (a + b) / 2, z), (b - a, su), mat, collection, normal)
            self.assign(ob, [self.which((a + b) / 2)])
            obs.append(ob)
        return obs

    def finalize(self):
        """Create LL_<panel> receiver collections (not linked to the scene)."""
        out = {}
        for p, obs in self.members.items():
            c = bpy.data.collections.get(f"LL_{p}") or bpy.data.collections.new(f"LL_{p}")
            for ob in obs:
                if ob.name not in c.objects:
                    c.objects.link(ob)
            out[p] = c
        return out
