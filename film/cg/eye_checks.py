"""High-resolution eye crops for the Director's and Designer's catchlight / face-read checks.

    python film/cg/eye_checks.py   ->  stills/checks/eyes_*.png  (and appends to checks/REPORT.md)

E1  shot 58 (75 mm): P12's catchlight returns in Noor's corneas at 8.10 (frame before vs. frame of)
E2  shot 53 (50 mm): Walter's lit-side eye keeps a catchlight at the dark edge
E3  Bea, eyes closed but awake (design-notes F2): face read under cue 3 BROWN and at the 7.10 edge
Each crop is rendered as a 3840-wide frame with a border around the eyes, then upscaled x3 nearest.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402

import build_scene  # noqa: E402
from lib import cameras, common  # noqa: E402
from lookdev_checks import load_png, save_png, OUT  # noqa: E402


def crop_render(shot, frames, who, aim=None, closed=(), pad=(0.045, 0.03), res_w=3840, poses=None, label=""):
    scene = build_scene.build(res=(res_w, round(res_w / 2.39)), samples=96, closed=closed, poses=poses)
    D = common.dp()
    t0 = frames[0] / D["fps"]
    cameras.set_shot(shot, t0, aim_override=aim)
    scene.frame_set(frames[0])
    cam = scene.camera
    eyes = [bpy.data.objects[f"{who}_EYE_{s}"].matrix_world.translation for s in (-1, 1)]
    uv = [world_to_camera_view(scene, cam, p) for p in eyes]
    cx, cy = sum(u.x for u in uv) / 2, sum(u.y for u in uv) / 2
    # border in normalised frame coords: width from the eye spacing
    span = abs(uv[0].x - uv[1].x)
    hw = max(span * 1.4, 0.012)
    hh = hw * 2.39 * 0.45
    r = scene.render
    r.use_border, r.use_crop_to_border = True, True
    r.border_min_x, r.border_max_x = max(0, cx - hw), min(1, cx + hw)
    r.border_min_y, r.border_max_y = max(0, cy - hh), min(1, cy + hh)
    tiles = []
    for f in frames:
        scene.frame_set(f)
        p = os.path.join(OUT, f"_eye_{f}.png")
        r.filepath = p
        bpy.ops.render.render(write_still=True)
        a = load_png(p)
        os.remove(p)
        tiles.append(np.kron(a, np.ones((3, 3, 1), np.float32)))
    return tiles


def sheet(tiles, path):
    h = max(t.shape[0] for t in tiles)
    pad = np.zeros((h, 10, 3), np.float32)
    row = []
    for t in tiles:
        if t.shape[0] < h:
            t = np.vstack([t, np.zeros((h - t.shape[0], t.shape[1], 3), np.float32)])
        row += [t, pad]
    save_png(np.concatenate(row[:-1], 1), path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    D = common.dp()
    f810 = common.t2f(next(c["t"] for c in D["cues"] if c["id"] == "8.10"))
    rows = []
    # E1: frame before 8.10 vs. the 8.10 frame (P12 at 110%) and 12 frames later (settled)
    t = crop_render(58, [f810 - 1, f810, f810 + 12], "NOOR", poses={"NOOR": "phone_ear"})
    sheet(t, os.path.join(OUT, "eyes_E1_noor_8.10_P12_return.png"))
    d = [float(np.abs(t[1] - t[0]).max()), float((np.abs(t[1] - t[0]).max(2) > 0.05).sum())]
    rows.append(f"| E1 P12 catchlight returns in Noor's eyes at 8.10 (shot 58, 75 mm) | {'MEASURABLE' if d[1] > 0 else 'FAIL'} | "
                f"eyes_E1_noor_8.10_P12_return.png: frame {f810 - 1} / {f810} (P12 on, 110%) / {f810 + 12}; "
                f"{int(d[1])} crop pixels change by >5% (max {d[0]:.2f}) |")
    # E2: Walter at the dark edge, shot 53
    sh53 = next(s for s in D["shots"] if s["shot"] == 53)
    f53 = common.t2f((sh53["in"] + sh53["out"]) / 2)
    t = crop_render(53, [f53], "WALTER")
    sheet(t, os.path.join(OUT, "eyes_E2_walter_shot53.png"))
    rows.append(f"| E2 Walter's lit-side catchlight, shot 53 | REVIEW | eyes_E2_walter_shot53.png at frame {f53} (P1-P2 lit, Walter under dark P3) |")
    # E3: Bea, eyes closed, under BROWN (from Pos C, 50 mm, aimed at Bea) and at the 7.10 edge (shot 49)
    t1 = crop_render(34, [common.t2f(147.0)], "BEA", closed=("BEA",))
    t2 = crop_render(49, [common.t2f(438.0)], "BEA", closed=("BEA",))
    sheet(t1 + t2, os.path.join(OUT, "eyes_E3_bea_closed_brown_and_edge.png"))
    rows.append("| E3 Bea eyes closed (F2): face read under BROWN and at the 7.10 edge | REVIEW | eyes_E3_bea_closed_brown_and_edge.png (left: cue 3 hold, Pos C 50 mm; right: after 7.10, shot 49) |")
    rep = os.path.join(OUT, "REPORT.md")
    with open(rep, "a") as fh:
        fh.write("\n## Eye checks (`eye_checks.py`)\n\n| Check | Result | Detail |\n|---|---|---|\n" + "\n".join(rows) + "\n")
    print("\n".join(rows))
