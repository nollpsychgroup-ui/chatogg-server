"""Render the Milestone 3 style frames (low-res PNGs) into film/cg/stills/.

    python film/cg/render_styleframes.py [--only sf01] [--samples 64] [--raw]

Each frame is a real frame of the cue-driven scene: the lighting state comes from
data/cue-stack.json at that cue's frame, nothing is lit by hand. --raw skips the painterly
compositor (useful to check the physical light underneath).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import build_scene  # noqa: E402
from lib import common, figures, lookdev  # noqa: E402
from lib.mesh import limb  # noqa: E402

STILLS = os.path.join(common.CG_DIR, "stills")


def frame_at(cue_id, offset_s=0.0):
    cues = common.load("cue-stack.json")
    c = next(c for c in cues["cues"] if c["id"] == cue_id)
    return 1 + round((c["tc"] + offset_s) * cues["fps"])


def kai_gone():
    """After the blackout: Kai is removed, his phone lies face-up on the cushion, call connected."""
    figures.set_visible("KAI", False)
    rig = bpy.data.objects["PHONE_KAI_RIG"]
    lay = common.load("set_layout.json")
    k = lay["characters"]["KAI"]
    W = lay["car"]["width"]
    rig.location = (k["x"] + 0.04, k["side"] * (W / 2 - 0.04 - 0.75 * lay["seats"]["pair_width"]), 0.506)
    rig.rotation_euler = (0, 0, math.radians(25))
    for ob in rig.children:
        ob.hide_render = False
        ob.hide_viewport = False
    # keep the phone objects renderable even though the KAI collection is hidden
    coll = bpy.data.collections.get("PROPS_LOOSE") or bpy.data.collections.new("PROPS_LOOSE")
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for ob in [rig] + list(rig.children):
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)


def lanyard_thrown():
    """Cue 7.5 onward: Noor's lanyard is on the floor in the aisle (still the only red in the car)."""
    for n in ("NOOR_LANYARD_-1", "NOOR_LANYARD_1", "NOOR_BADGE"):
        bpy.data.objects[n].hide_render = True
    red = bpy.data.materials["lanyard_red"]
    pts = [(3.25, -0.30, 0.012), (3.45, -0.18, 0.012), (3.52, -0.02, 0.012), (3.38, 0.06, 0.012), (3.20, -0.05, 0.012)]
    for i in range(len(pts) - 1):
        limb(f"LANYARD_FLOOR_{i}", pts[i], pts[i + 1], 0.009, red, "PROPS_LOOSE")
    from lib.mesh import box
    b = box("BADGE_FLOOR", (3.18, -0.10, 0.008), (0.075, 0.10, 0.008), bpy.data.materials["char_badge"], coll="PROPS_LOOSE")
    b.rotation_euler = (0, 0, math.radians(30))


SETUPS = {"kai_gone": kai_gone, "lanyard_thrown": lanyard_thrown}
BEATS = common.load("styleframes.json")["frames"]


def render(name, beat, samples, paint):
    scene = build_scene.build(samples=samples, paint=paint, poses=beat.get("poses"))
    for fn in beat.get("setup", []):
        SETUPS[fn]()
    scene.camera = bpy.data.objects[beat["camera"]]
    scene.frame_set(frame_at(beat["cue"], beat.get("offset", 0.0)))
    os.makedirs(STILLS, exist_ok=True)
    scene.render.filepath = os.path.join(STILLS, name + ("" if paint else "_raw") + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", scene.render.filepath, "frame", scene.frame_current)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64
    paint = "--raw" not in argv
    for name, beat in BEATS.items():
        if only and not name.startswith(only):
            continue
        render(name, beat, samples, paint)
