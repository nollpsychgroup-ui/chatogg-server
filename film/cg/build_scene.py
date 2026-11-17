"""Build THE QUIET CAR carriage scene from scratch: set, look-dev, figures, light rig, cues, cameras.

Usage (either works):
    blender -b --python film/cg/build_scene.py -- [--save out.blend]
    python film/cg/build_scene.py [--save out.blend]        # with the `bpy` wheel (pip install bpy)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

from lib import build_set, cameras, common, cue_driver, figures, light_rig, lookdev  # noqa: E402


def build(res=(960, 402), samples=64, paint=True, poses=None):
    common.clear_scene()
    scene = bpy.context.scene
    scene.name = "QUIET_CAR"
    lookdev.setup_render(scene, res=res, samples=samples)
    lay = common.load("set_layout.json")
    cues = common.load("cue-stack.json")
    build_set.build(lay)
    figures.build(lay, poses)
    light_rig.build(lay, cues)
    cue_driver.build(cues, lay)
    cams = cameras.build(lay)
    scene.camera = cams["CAM_MASTER_32"]
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
