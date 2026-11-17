"""Virtual cameras from camera/cues.json: S35 cropped to 2.39:1, spherical, one camera object
per DP position (A, A2, B..G) plus SHOT_CAM, which is set per shot (loc, aim, lens; A->A2 push
interpolated over the shot). Cameras are keyed on ones (DP rule)."""
import bpy
from mathutils import Vector

from .common import dp, link

SUBJECT_Z = {}


def _cam(name, sensor, lens, loc, aim):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = sensor["width_mm"]
    cd.sensor_height = sensor["height_mm"]
    cd.clip_start = 0.05
    cd.clip_end = 80.0
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = 4.0
    ob = bpy.data.objects.new(name, cd)
    link(ob, "CAMERAS")
    aim_at(ob, loc, aim)
    return ob


def aim_at(ob, loc, aim):
    ob.location = loc
    d = Vector(aim) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    ob.data.dof.focus_distance = max(0.5, d.length)


def build(D=None):
    D = D or dp()
    sensor = D["camera"]["sensor"]
    out = {}
    for k, p in D["camera"]["positions"].items():
        if "loc" not in p:
            continue
        aim = p.get("aim", D["set"]["marks"]["NOOR"])
        out[k] = _cam(f"CAM_{k}", sensor, p["lens"], p["loc"], aim)
    out["SHOT"] = _cam("SHOT_CAM", sensor, 32, (0, -3.5, 1.65), (0, 13, 1.65))
    return out


def set_shot(shot_no, t, D=None, aim_override=None):
    """Point SHOT_CAM at shot `shot_no` as it is at time t (seconds)."""
    D = D or dp()
    s = next(x for x in D["shots"] if x["shot"] == shot_no)
    ob = bpy.data.objects["SHOT_CAM"]
    ob.data.lens = s["lens_mm"]
    if s["camera_loc"] is None:   # inserts (pos I): placement per shot, set by the caller
        bpy.context.scene.camera = ob
        return s
    loc = Vector(s["camera_loc"])
    path = s.get("path")
    if path:  # moving shots: linear from path.from to path.to over the shot (DP's cues.json)
        u = max(0.0, min(1.0, (t - s["in"]) / (s["out"] - s["in"])))
        loc = Vector(path["from"]).lerp(Vector(path["to"]), u)
    aim = aim_override or s["aim"]
    aim_at(ob, loc, aim)
    bpy.context.scene.camera = ob
    return s
