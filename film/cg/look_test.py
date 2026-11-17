"""Look test (Director, after the Designer's skin finding): a 3-up of the same frames in
(a) the approved look, (b) white balance 4300 K, (c) approved WB with less highlight desaturation
(Khronos PBR Neutral view transform; AgX 'Base' look as fallback). Also reports blackout 0 per variant.

    python film/cg/look_test.py --out <dir>      (bpy)   then the sheet is built with PIL
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import build_scene  # noqa: E402
import previs  # noqa: E402
from lib import common  # noqa: E402

FRAMES = [("38 Walter", 310.0), ("58 C75", 490.0), ("4 Meter BASE", 43.0), ("16 BROWN", 134.0), ("blackout", 143.0)]


def render_set(tag, out, view=None, look=None, exposure=None):
    sc = bpy.context.scene
    if exposure is not None:
        sc.view_settings.exposure = exposure
    if view:
        try:
            sc.view_settings.view_transform = view
        except TypeError:
            sc.view_settings.view_transform = "AgX"
            sc.view_settings.look = "AgX - Base"
            tag += "_fallback"
    if look:
        sc.view_settings.look = look
    paths = []
    for name, t in FRAMES:
        sc.frame_set(round(t * 24))
        p = os.path.join(out, f"{tag}_{int(t):03d}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths


def build(wb=None):
    if wb:
        orig = common.load
        def patched(name, *a, **k):
            d = orig(name, *a, **k)
            if name == "build.json":
                d["white_balance_k"] = wb
            return d
        common.load = patched
    D = common.dp()
    sc = build_scene.build(res=(640, 268), samples=8, previs=True)
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.max_bounces, sc.cycles.diffuse_bounces, sc.cycles.glossy_bounces, sc.cycles.transmission_bounces = 4, 2, 2, 3
    previs.key_cameras(D)
    return sc


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = argv[argv.index("--out") + 1]
    os.makedirs(out, exist_ok=True)
    which = argv[argv.index("--variant") + 1] if "--variant" in argv else "ac"
    if "a" in which or "c" in which:
        build()
        if "a" in which:
            render_set("a_current", out)
        if "c" in which:
            render_set("c_neutral", out, view="Khronos PBR Neutral")
    if "2" in which:
        build()
        ev = float(argv[argv.index("--ev") + 1]) if "--ev" in argv else -0.55
        render_set("c2_neutral_ev", out, view="Khronos PBR Neutral", exposure=ev)
    if "b" in which:
        build(wb=4300.0)
        render_set("b_wb4300", out)
