"""Render the Milestone 3 style frames (1280 x 536 PNG) into film/cg/stills/.

    python film/cg/render_styleframes.py [--only sf03] [--samples 64] [--raw] [--res 1280]

Every frame is a real frame of the cue-driven scene: camera from the DP's shot list, lighting
from camera/cues.json at time t. --raw writes the physical render without the painterly comp.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import build_scene  # noqa: E402
from lib import cameras, common  # noqa: E402
from lib.mesh import box, limb  # noqa: E402

STILLS = os.path.join(common.CG_DIR, "stills")


def lanyard_thrown():
    """From 7.6: the strap and badge are on the aisle floor in front of Noor (red on grey)."""
    for n in ("NOOR_STRAP_-1", "NOOR_STRAP_1", "NOOR_BADGE"):
        o = bpy.data.objects.get(n)
        if o:
            o.hide_render = True
    red = bpy.data.materials["the_red_strap"]
    pts = [(0.05, 11.95, 0.012), (0.2, 11.8, 0.012), (0.18, 11.62, 0.012), (0.0, 11.58, 0.012), (-0.08, 11.75, 0.012)]
    for i in range(len(pts) - 1):
        limb(f"STRAP_FLOOR_{i}", pts[i], pts[i + 1], 0.009, red, "PROPS_LOOSE").pass_index = 2
    b = box("BADGE_FLOOR", (-0.12, 11.88, 0.006), (0.075, 0.10, 0.006), bpy.data.materials["badge_plastic"], "PROPS_LOOSE")
    b.rotation_euler = (0, 0, math.radians(30))


SETUPS = {"lanyard_thrown": lanyard_thrown}


def render(name, beat, samples, paint, res):
    scene = build_scene.build(res=res, samples=samples, paint=paint, poses=beat.get("poses"), standing=beat.get("standing"), closed=tuple(beat.get("eyes_closed", [])))
    for fn in beat.get("setup", []):
        SETUPS[fn]()
    t = beat["t"]
    cameras.set_shot(beat["shot"], t, aim_override=beat.get("aim"))
    scene.frame_set(common.t2f(t))
    scene.view_settings.exposure += beat.get("exposure", 0.0)
    os.makedirs(STILLS, exist_ok=True)
    scene.render.filepath = os.path.join(STILLS, name + ("" if paint else "_raw") + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath, "frame", scene.frame_current)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64
    w = int(argv[argv.index("--res") + 1]) if "--res" in argv else 1280
    paint = "--raw" not in argv
    for name, beat in common.load("styleframes.json")["frames"].items():
        if only and not name.startswith(only):
            continue
        render(name, beat, samples, paint, (w, round(w / 2.39)))
