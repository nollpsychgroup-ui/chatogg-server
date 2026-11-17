"""Turnaround/expression test renders for the head rigs (Cycles, real overhead panel lights only).
python3 film/design/rig/test_render.py [--quick]"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from heads import build_head, build_neck, place, set_expression  # noqa: E402
from sheets_data import EXPRESSIONS  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
QUICK = "--quick" in sys.argv


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 24 if QUICK else 64
    sc.cycles.use_denoising = True
    sc.render.resolution_percentage = 100
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.world = w
    sc.view_settings.view_transform = "Standard"
    return sc


def panels(sc, kelvin_rgb=(1.0, 1.0, 0.97), power=25.0, lit=(True, True, True), y0=0.35, step=1.083):
    """A row of ceiling panels running away from the face: the catchlight row."""
    for i, on in enumerate(lit):
        ld = bpy.data.lights.new(f"P{i+1}", "AREA")
        ld.shape = "RECTANGLE"
        ld.size, ld.size_y = 0.6, 0.64
        ld.energy = power * (1.0 if on else 0.0)
        ld.color = kelvin_rgb
        ob = bpy.data.objects.new(f"P{i+1}", ld)
        ob.location = (0, y0 + i * step, 2.29 - 1.25)
        sc.collection.objects.link(ob)
        # visible diffuser so the cornea has something to reflect
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y0 + i * step, 2.29 - 1.25 + 0.001))
        pl = bpy.context.active_object
        pl.scale = (0.6, 0.64, 1)
        m = bpy.data.materials.new(f"diff{i}")
        m.use_nodes = True
        e = m.node_tree.nodes.new("ShaderNodeEmission")
        e.inputs[0].default_value = tuple(kelvin_rgb) + (1,)
        e.inputs[1].default_value = 6.0 if on else 0.0
        m.node_tree.links.new(e.outputs[0], m.node_tree.nodes["Material Output"].inputs[0])
        pl.data.materials.append(m)
        pl.visible_diffuse = False


def camera(sc, target, dist=0.55, lens=75, height=-0.02):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cam = bpy.data.objects.new("cam", cd)
    cam.location = Vector(target) + Vector((0, -dist, height))
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(cam)
    sc.camera = cam


def render(sc, path, w, h):
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("wrote", path)


def lineup():
    sc = reset()
    xs = {"WALTER": -0.36, "NOOR": -0.12, "BEA": 0.12, "KAI": 0.36}
    for n, x in xs.items():
        r = build_head(n)
        place(r, (x, 0, 0), (0, -1, 0))
    panels(sc, y0=-0.55)
    camera(sc, (0, 0, -0.01), dist=1.6, lens=60)
    render(sc, os.path.join(OUT, "heads_lineup.png"), 1280, 420)


def three_quarter(n):
    sc = reset()
    r = build_head(n)
    place(r, (0, 0, 0), (-0.75, -1, 0))
    panels(sc, y0=-0.55)
    camera(sc, (0, 0, -0.005), dist=0.62, lens=75)
    render(sc, os.path.join(OUT, f"{n.lower()}_3q.png"), 640, 640)


def expressions(n):
    sc = reset()
    items = EXPRESSIONS[n.lower()]["items"]
    k = len(items)
    roots = []
    for i, it in enumerate(items):
        r = build_head(n)
        place(r, ((i - (k - 1) / 2) * 0.24, 0, 0), (0, -1, 0))
        p = {kk: v for kk, v in it["p"].items() if kk not in ("catch", "phone_catch", "catch_col")}
        # sheets: "_L" was camera-left (= character's right). Mirror into the rig's convention.
        p2 = {}
        for kk, v in p.items():
            if kk.endswith("_L"):
                p2[kk[:-2] + "_R"] = v
            elif kk.endswith("_R"):
                p2[kk[:-2] + "_L"] = v
            elif kk == "gaze_x":
                p2[kk] = v
            else:
                p2[kk] = v
        set_expression(r, p2, from_neutral=True)
        roots.append(r)
    panels(sc, y0=-0.55)
    camera(sc, (0, 0, -0.01), dist=0.42 * k, lens=60)
    render(sc, os.path.join(OUT, f"{n.lower()}_expressions.png"), 280 * k, 330)


def bea_dark():
    """Director F2: Bea, eyes closed but awake, under asleep / brownout / one dipped panel."""
    states = [("asleep", (1.0, 1.0, 0.95), 25.0, (True, True, True)),
              ("brownout", (1.0, 0.55, 0.22), 25.0 * 0.18, (True, True, True)),
              ("edge_of_dark", (1.0, 1.0, 0.95), 25.0, (True, False, False))]
    for tag, rgb, pw, lit in states:
        sc = reset()
        r = build_head("BEA")
        place(r, (0, 0, 0), (0, -1, 0))
        set_expression(r, dict(lid_up=0.0, tension=0.7, brow_in=-0.15, press=0.25, smile=-0.05), from_neutral=True)
        panels(sc, kelvin_rgb=rgb, power=pw, lit=lit, y0=0.2 if tag == "edge_of_dark" else -0.55)
        camera(sc, (0, 0, -0.005), dist=0.5, lens=75)
        if tag == "brownout":
            sc.view_settings.exposure = 1.2  # exposed for the brownout, as the DP grades it
        render(sc, os.path.join(OUT, f"bea_dark_{tag}.png"), 420, 420)


def catchlights():
    """Style guide 8c: the panel row shows in the cornea, and panels going out leave it."""
    for tag, lit in (("12_lit", (True,) * 12), ("2_lit", (True, True) + (False,) * 10)):
        sc = reset()
        r = build_head("NOOR")
        place(r, (0, 0, 0), (0, -1, 0))
        set_expression(r, dict(gaze_y=-0.3), from_neutral=True)
        # the row runs away down the car in front of her, as on the 40 mm (P1 above, P2.. ahead)
        panels(sc, lit=lit, y0=-0.15, step=-1.083)
        # C75 framing: 75 mm at ~0.9 m, full face in a 2.39 frame; then an unscaled 1:1 crop of her eyes
        camera(sc, (0.0, 0.0, 0.0), dist=0.9, lens=75, height=-0.04)
        sc.render.use_border = True
        sc.render.use_crop_to_border = True
        sc.render.border_min_x, sc.render.border_max_x = 0.36, 0.64
        sc.render.border_min_y, sc.render.border_max_y = 0.52, 0.70
        render(sc, os.path.join(OUT, f"catchlight_{tag}.png"), 1920, 804)


def walter_s38():
    """Shot 38 check: Walter's speech, 50 mm, his own top panel only (P3 slightly in front, above)."""
    for tag, ex in (("speech", "walter/speech"), ("speech_end", "walter/speech_end")):
        sc = reset()
        r = build_head("WALTER")
        build_neck(r, "WALTER")
        place(r, (0, 0, 0), (0, -1, 0))
        import json
        L = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "expressions", "shot_expressions.json")))["library"]
        set_expression(r, L[ex], from_neutral=True)
        panels(sc, power=25.0, lit=(True,), y0=-0.25)
        # the white newspaper on his lap: real panel light bounces up off it (paper albedo + GI, no fill)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.30, -0.42))
        paper = bpy.context.active_object
        paper.scale = (0.55, 0.36, 1)
        paper.rotation_euler = (math.radians(-35), 0, 0)
        from heads import _mat, _lin
        paper.data.materials.append(_mat("newsprint", _lin("#D9D3C3")))
        camera(sc, (0, 0, -0.06), dist=1.15, lens=50, height=0.0)
        render(sc, os.path.join(OUT, f"walter_s38_{tag}.png"), 960, 402)


if __name__ == "__main__":
    if "--s38" in sys.argv:
        os.makedirs(OUT, exist_ok=True)
        walter_s38()
        sys.exit()
    if "--catch" in sys.argv:
        os.makedirs(OUT, exist_ok=True)
        catchlights()
        sys.exit()
    os.makedirs(OUT, exist_ok=True)
    lineup()
    for n in ("NOOR", "WALTER", "BEA", "KAI"):
        three_quarter(n)
        expressions(n)
    bea_dark()
    catchlights()
    walter_s38()
