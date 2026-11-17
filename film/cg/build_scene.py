"""Build THE QUIET CAR carriage scene from scratch.

Shared data: camera/cues.json (DP: set, panels, marks, looks, breath, cues, events, cameras, shots)
and design/palette.json (Character Designer). TA build detail: cg/data/build.json.

    python film/cg/build_scene.py [--save film/cg/.cache/quiet_car.blend]     (bpy wheel)
    blender -b --python film/cg/build_scene.py -- [--save ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

from lib import build_set, cameras, common, cue_driver, figures, light_rig, lookdev  # noqa: E402


def build(res=(1280, 536), samples=64, paint=True, poses=None, standing=None, closed=()):
    common.clear_scene()
    scene = bpy.context.scene
    scene.name = "QUIET_CAR"
    lookdev.setup_render(scene, res=res, samples=samples)
    D, B = common.dp(), common.load("build.json")
    common.coll("SET"); common.coll("CHARACTERS"); common.coll("PROPS_LOOSE"); common.coll("EXTERIOR")
    sec = build_set.build(D, B)
    figures.build(D, B, poses, standing, closed)
    ll = sec.finalize()
    light_rig.build(D, B, ll)
    cue_driver.build(D, B)
    cams = cameras.build(D)
    scene.camera = cams["A"]
    lookdev.setup_compositor(scene, enabled=paint)
    return scene


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    build()
    if "--save" in argv:
        out = os.path.abspath(argv[argv.index("--save") + 1])
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out)
        print("saved", out)
