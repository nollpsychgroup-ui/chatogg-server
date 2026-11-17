"""Virtual cameras from data/set_layout.json (provisional until camera/shot-list.md).
Super 35 gate (24.89 mm wide), 2.39:1, spherical (no anamorphic artefacts), deep stop."""
import bpy
from mathutils import Vector

from .common import link, load

SENSOR_W = 24.89


def build(layout=None):
    lay = layout or load("set_layout.json")
    cams = {}
    for name, c in lay["cameras"].items():
        if name.startswith("_"):
            continue
        cd = bpy.data.cameras.new(name)
        cd.lens = c["lens"]
        cd.sensor_fit = "HORIZONTAL"
        cd.sensor_width = SENSOR_W
        cd.clip_start = 0.05
        cd.clip_end = 60.0
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = 4.0
        ob = bpy.data.objects.new(name, cd)
        ob.location = c["loc"]
        d = Vector(c["look_at"]) - Vector(c["loc"])
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cd.dof.focus_distance = c.get("focus", min(d.length, 6.0))
        ob["use"] = c.get("use", "")
        link(ob, "CAMERAS")
        cams[name] = ob
    return cams
