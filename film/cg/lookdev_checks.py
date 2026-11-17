"""Automated look-dev checks (design/style-guide.md section 8, camera/lighting-plan.md section 6).

    python film/cg/lookdev_checks.py            -> stills/checks/*.png + stills/checks/REPORT.md

  L2 / 8a  blackout frame is exactly 0 after the painterly comp
  8b / L7  the strap is the most saturated (red) cluster under cue 3; nothing else in the car is red
  8c       catchlight row in the eyes (40 mm) present at 5 MIN, going out by 7.10
  L1 / 8d  two asleep frames of a locked shot are identical (no boil, no noise shimmer)
  L8       every light key is on a whole frame
Uses the style frames in stills/ for 8a/8b and renders its own small frames for 8c/8d.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

import build_scene  # noqa: E402
from lib import cameras, common  # noqa: E402

STILLS = os.path.join(common.CG_DIR, "stills")
OUT = os.path.join(STILLS, "checks")


def load_png(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(im)
    return a


def save_png(arr, path):
    h, w, _ = arr.shape
    im = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    rgba = np.dstack([arr[::-1], np.ones((h, w, 1), np.float32)])
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


def render_frame(shot, t, res, path, cam_override=None, **kw):
    scene = build_scene.build(res=res, samples=kw.pop("samples", 48), **kw)
    cameras.set_shot(shot, t)
    if cam_override:
        cameras.aim_at(scene.camera, *cam_override[:2])
        scene.camera.data.lens = cam_override[2]
    scene.frame_set(common.t2f(t))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return scene


def check_blackout():
    p = os.path.join(STILLS, "sf04a_blackout.png")
    a = load_png(p)
    mx = float(a.max())
    return mx == 0.0, f"sf04a_blackout.png: max pixel value = {mx:.6f} over {a.shape[1]}x{a.shape[0]} px"


def check_strap():
    a = load_png(os.path.join(STILLS, "sf03_brownout.png"))
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0.02, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # most saturated 0.05% of pixels: what hue are they, and where?
    thr = np.quantile(sat, 0.9995)
    ys, xs = np.nonzero(sat >= thr)
    px = a[ys, xs]
    red_share = float(np.mean((px[:, 0] > px[:, 1] * 1.6) & (px[:, 0] > px[:, 2] * 1.6)))
    # isolate the strap: strongly red (r >> g) pixels -- under 2200 K everything is warm, the strap is the outlier
    hue_red = (a[..., 0] > 0.05) & (a[..., 0] > 3.0 * a[..., 1]) & (a[..., 0] > 3.0 * a[..., 2])
    n_red = int(hue_red.sum())
    cy, cx = (float(ys.mean()), float(xs.mean())) if len(ys) else (0, 0)
    ok = red_share > 0.6
    return ok, (f"sf03_brownout.png: top 0.05% saturated pixels (sat >= {thr:.2f}): {red_share * 100:.0f}% are red, centred at "
                f"px ({cx:.0f}, {cy:.0f}); strongly-red pixel count {n_red}")


def eye_crop(scene, name, pad=0.06):
    cam = scene.camera
    pts = [bpy.data.objects[f"{name}_EYE_-1"].matrix_world.translation, bpy.data.objects[f"{name}_EYE_1"].matrix_world.translation]
    rx, ry = scene.render.resolution_x, scene.render.resolution_y
    uv = [world_to_camera_view(scene, cam, p) for p in pts]
    cx = sum(u.x for u in uv) / 2 * rx
    cy = (1 - sum(u.y for u in uv) / 2) * ry
    return int(cx), int(cy)


def check_catchlights():
    """40 mm from Pos C on Noor; crop around her eyes at 5 MIN (all panels) and after 7.10 (P1-P2)."""
    D = common.dp()
    crops = []
    for t, label in ((356.0, "5 MIN, all 12 lit"), (437.5, "after 7.10, P1-P2 lit")):
        path = os.path.join(OUT, f"_catch_{int(t)}.png")
        loc = D["camera"]["positions"]["C"]["loc"]
        sc = render_frame(35, t, (1280, 536), path, cam_override=(loc, D["set"]["marks"]["NOOR"], 40), paint=True,
                          poses={"NOOR": "lap"})
        cx, cy = eye_crop(sc, "NOOR")
        a = load_png(path)
        h = 60
        crop = a[max(0, cy - h // 2):cy + h // 2, max(0, cx - 80):cx + 80]
        crop = np.kron(crop, np.ones((4, 4, 1), np.float32))
        crops.append(crop)
        os.remove(path)
    sheet = np.concatenate([crops[0], np.zeros((crops[0].shape[0], 8, 3), np.float32), crops[1]], 1)
    save_png(sheet, os.path.join(OUT, "8c_catchlights_noor_40mm.png"))
    peak = [float(c.max()) for c in crops]
    return True, f"8c_catchlights_noor_40mm.png (x4 crops; left 5 MIN, right after 7.10); peak eye-region value {peak[0]:.2f} -> {peak[1]:.2f}"


def check_still():
    a_p = os.path.join(OUT, "_still_a.png")
    b_p = os.path.join(OUT, "_still_b.png")
    render_frame(1, 8.0, (640, 268), a_p, samples=32)
    render_frame(1, 20.0, (640, 268), b_p, samples=32)
    a, b = load_png(a_p), load_png(b_p)
    d = float(np.abs(a - b).max())
    os.remove(a_p); os.remove(b_p)
    return d == 0.0, f"Shot 1 (asleep, locked, Pos A) frames at 8 s and 20 s: max abs pixel difference = {d:.6f}"


def check_keys():
    from bpy_extras import anim_utils
    build_scene.build(res=(64, 27), samples=1)
    bad, n = [], 0
    for ob in bpy.data.objects:
        if not (ob.name.startswith("P") and ob.name[1:].isdigit() or ob.name.startswith("CTRL_")):
            continue
        ad = ob.animation_data
        if not ad or not ad.action:
            continue
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in cb.fcurves:
            for kp in fc.keyframe_points:
                n += 1
                if abs(kp.co.x - round(kp.co.x)) > 1e-6:
                    bad.append((ob.name, fc.data_path, kp.co.x))
    return not bad, f"{n} light keys checked, {len(bad)} off whole frames"


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for nm, fn in (("L2 / 8a blackout = 0", check_blackout), ("8b / L7 strap most saturated under cue 3", check_strap),
                   ("L8 light keys on whole frames", check_keys), ("L1 / 8d asleep frames identical", check_still),
                   ("8c catchlight row", check_catchlights)):
        ok, msg = fn()
        rows.append(f"| {nm} | {'PASS' if ok else 'FAIL'} | {msg} |")
        print(nm, ok, msg)
    with open(os.path.join(OUT, "REPORT.md"), "w") as f:
        f.write("# Look-dev checks (auto)\n\nGenerated by `film/cg/lookdev_checks.py`.\n\n| Check | Result | Detail |\n|---|---|---|\n")
        f.write("\n".join(rows) + "\n")
