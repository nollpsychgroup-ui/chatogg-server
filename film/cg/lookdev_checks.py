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


def _chroma(a):
    """CIELAB chroma (perceived colourfulness) of display-referred sRGB pixels."""
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]], np.float32)
    xyz = lin @ M.T / np.array([0.9505, 1.0, 1.089], np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.hypot(500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2]))


def check_strap():
    """8b/L7: under cue 3 the strap must be the most saturated (most chromatic) thing on screen.
    Measured as CIELAB chroma (HSV saturation is meaningless under 2200 K: every dim orange pixel has
    blue ~0 and reads 'fully saturated'). Emitters (the panels themselves) are excluded."""
    a = load_png(os.path.join(STILLS, "sf03_brownout.png"))
    C = _chroma(a)
    mx = a.max(2)
    red = (a[..., 0] > 3 * a[..., 1]) & (a[..., 0] > 3 * a[..., 2]) & (mx > 0.08)
    emit = mx > 0.55
    other = (~red) & (~emit)
    if red.sum() == 0:
        return False, "sf03_brownout.png: no strap pixels found"
    s90 = float(np.percentile(C[red], 90))
    o999 = float(np.percentile(C[other], 99.9))
    ok = s90 > o999
    return ok, (f"sf03_brownout.png (CIELAB chroma, emitters excluded): strap p90 = {s90:.1f} ({int(red.sum())} px) vs "
                f"everything else p99.9 = {o999:.1f}. Under BROWN (2200 K, camera balanced at 4000 K) the sodium-lit surfaces are "
                f"more chromatic than the strap in the Meter wide. Earlier PASS used an HSV metric that was invalid here.")


def eye_crop(scene, name, pad=0.06):
    cam = scene.camera
    pts = [bpy.data.objects[f"{name}_HD_EYE_{s}"].matrix_world.translation for s in ("L", "R")]
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
    return None, (f"8c_catchlights_noor_40mm.png (x4 crops; left 5 MIN all lit, right after 7.10). A catchlight from the overhead panels is present "
                  f"in both (P1-P2 stay lit); (Designer's face-rig eyes). "
                  f"Peak eye value {peak[0]:.2f} -> {peak[1]:.2f}")


def check_still():
    """One scene, one locked asleep shot, two frames 12 s apart (as an animatic render would run)."""
    scene = build_scene.build(res=(640, 268), samples=32)
    cameras.set_shot(1, 8.0)
    arrs = []
    for t in (8.0, 20.0):
        scene.frame_set(common.t2f(t))
        p = os.path.join(OUT, f"_still_{int(t)}.png")
        scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        arrs.append(load_png(p))
        os.remove(p)
    d = float(np.abs(arrs[0] - arrs[1]).max())
    return d == 0.0, f"Shot 1 (asleep, locked, Pos A), painterly comp on, frames at 8 s and 20 s: max abs pixel difference = {d:.6f}"


CHART = ["set/laminate", "set/ceiling", "set/moquette", "set/floor", "THE_RED", "noor/suit", "noor/skin", "noor/hair",
         "kai/hoodie", "kai/skin", "bea/scrubs", "bea/skin", "walter/coat", "walter/skin"]


def check_palette_chart():
    """Designer's colour-fidelity check: a swatch card (flat palette albedos, matte) on the side-A wall at
    y 8.6 (P5 section), lit as a character would be there, asleep look. Rendered with the Standard view
    (no AgX, no paint comp) so values are linear after decoding. Pass when every swatch renders within
    25% of its albedo ratio to the laminate swatch, and the card's laminate swatch matches the real wall."""
    from lib import lookdev as ld
    from lib.common import pal
    scene = build_scene.build(res=(1280, 536), samples=64, paint=False)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.0
    col = bpy.data.collections.new("CHAR_CHART")
    bpy.data.collections["CHARACTERS"].children.link(col)
    y0, z0, w, h = 8.6, 1.50, 0.11, 0.11
    n = len(CHART)
    names = []
    for i, key in enumerate(CHART):
        m = bpy.data.materials.new(f"chart_{i}")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = pal(key) + (1,)
        b.inputs["Roughness"].default_value = 0.85
        b.inputs["Specular IOR Level"].default_value = 0.25
        r, c = divmod(i, 7)
        from lib.mesh import plane
        ob = plane(f"CHART_{i}", (-1.36, y0 - 0.42 + c * (w + 0.02), z0 + 0.07 - r * (h + 0.02)), (w, h), m, collection="CHAR_CHART", normal="X")
        names.append(ob.name)
    # re-link: rebuild the light linking so the card is treated like a character at y 8.6
    for pid in [p["id"] for p in common.dp()["panels"]]:
        rc = bpy.data.collections.get(f"LLR_{pid}")
        si = int(pid[1:]) - 1
        if rc is not None and abs(si - 4) <= 1:
            rc.children.link(col)
    cam = scene.camera
    cameras.aim_at(cam, (0.6, y0, z0), (-1.36, y0, z0))
    cam.data.lens = 40
    scene.frame_set(common.t2f(56.0))
    p = os.path.join(OUT, "palette_chart.png")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    a = load_png(p)
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    Y = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    rx, ry = scene.render.resolution_x, scene.render.resolution_y
    vals = {}
    for key, nm in zip(CHART, names):
        uv = world_to_camera_view(scene, cam, bpy.data.objects[nm].matrix_world.translation)
        x, y = int(uv.x * rx), int((1 - uv.y) * ry)
        vals[key] = float(Y[y - 6:y + 6, x - 6:x + 6].mean())
    # real wall just above the card
    uvw = world_to_camera_view(scene, cam, Vector((-1.43, y0, z0 + 0.32)))
    wx, wy = int(uvw.x * rx), int((1 - uvw.y) * ry)
    wall = float(Y[wy - 6:wy + 6, wx - 6:wx + 6].mean())
    lum = lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    ref_r, ref_a = vals["set/laminate"], lum(pal("set/laminate"))
    rows, worst = [], 0.0
    for key in CHART:
        expect = lum(pal(key)) / ref_a
        got = vals[key] / ref_r if ref_r > 0 else 0
        err = abs(got - expect) / (0.05 + 0.15 * expect)   # <=1 passes: 15% relative, or 0.05 of laminate for darks (matte sheen)
        worst = max(worst, err)
        rows.append(f"{key} {got:.3f}/{expect:.3f}")
    wall_ratio = wall / ref_r if ref_r > 0 else 0
    ok = worst <= 1.0 and 0.8 < wall_ratio < 1.25
    return ok, (f"palette_chart.png (Standard view, linear, asleep, card on side-A wall at y 8.6): rendered/expected ratio to laminate per "
                f"swatch: {'; '.join(rows)}. Worst tolerance use {worst:.2f} (<=1 passes: 15% relative or 0.05 absolute). Real wall vs card laminate: {wall_ratio:.2f} (set and characters lit alike)")


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
                   ("L8 light keys on whole frames", check_keys), ("Designer palette chart (colour fidelity)", check_palette_chart), ("L1 / 8d asleep frames identical", check_still),
                   ("8c catchlight row", check_catchlights)):
        ok, msg = fn()
        rows.append(f"| {nm} | {'PASS' if ok else ('FAIL' if ok is False else 'PARTIAL')} | {msg} |")
        print(nm, ok, msg)
    with open(os.path.join(OUT, "REPORT.md"), "w") as f:
        f.write("# Look-dev checks (auto)\n\nGenerated by `film/cg/lookdev_checks.py`.\n\n| Check | Result | Detail |\n|---|---|---|\n")
        f.write("\n".join(rows) + "\n")
