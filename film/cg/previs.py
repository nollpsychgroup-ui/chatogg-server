"""Milestone 4 previs animatic: build the whole film once, key every shot's camera, and render a
frame plan (resumable) to film/cg/.cache/previs/frames/. assemble_previs.py turns it into the mp4.

    python film/cg/previs.py --plan                       # print the frame plan stats
    python film/cg/previs.py --from 0 --to 130            # render frames for 0-130 s
    python film/cg/previs.py --res 640 --samples 8

Frame plan (pass 1): a frame is rendered at every shot start; on ONES around every light cue and
its named eases; on TWOS for camera moves (pushes, handheld), walks, door/platform moves, phone dim
and face-expression changes; at 4 fps through the awake stretch (breathing); every 2 s while asleep
(nothing moves). Every other frame of the 24 fps timeline holds the last rendered frame of its shot.
Lights are keyed on ones in the scene; holds only affect what is rendered in pass 1.
"""
import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import build_scene  # noqa: E402
from lib import common  # noqa: E402

OUT = os.path.join(common.CACHE_DIR, "previs", "frames")
PLAN = os.path.join(common.CACHE_DIR, "previs", "plan.json")


def shot_of(D, f):
    for s in D["shots"]:
        if s["frames"][0] <= f < s["frames"][1]:
            return s
    return D["shots"][-1]


def key_cameras(D):
    """SHOT_CAM keyed per shot: constant at each cut, linear along path moves, a stand-in handheld on 20."""
    cam = bpy.data.objects["SHOT_CAM"]
    cam.data.dof.use_dof = False
    def put(f, loc, aim, lens, interp="CONSTANT"):
        cam.location = loc
        d = Vector(aim) - Vector(loc)
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
        cam.data.keyframe_insert("lens", frame=f)
    for s in D["shots"]:
        f0, f1 = s["frames"]
        loc, aim, lens = s["camera_loc"], s["aim"], s["lens_mm"]
        if s.get("path"):
            put(f0, s["path"]["from"], aim, lens)
            put(f1 - 1, s["path"]["to"], aim, lens)
        elif s["move"] == "handheld":
            # stand-in for the DP's recorded operator clip: a smooth, seeded wander (~4 cm, ~1.5 deg)
            # that settles to the base camera over the last 2 s
            rng = random.Random(20)
            px = py = pz = ax = 0.0
            for f in range(f0, f1, 2):
                u = (f - f0) / max(1, f1 - f0)
                settle = max(0.0, min(1.0, (f1 - 48 - f) / 48.0))
                px = 0.8 * px + rng.gauss(0, 0.012); py = 0.8 * py + rng.gauss(0, 0.012); pz = 0.8 * pz + rng.gauss(0, 0.008)
                ax = 0.8 * ax + rng.gauss(0, 0.02)
                l = Vector(loc) + Vector((px, py, pz)) * settle
                a = Vector(aim) + Vector((0, ax, ax * 0.5)) * settle
                put(f, tuple(l), tuple(a), lens)
        else:
            put(f0, loc, aim, lens)
    ad = cam.animation_data
    from bpy_extras import anim_utils
    for idb in (cam, cam.data):
        ad = idb.animation_data
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in cb.fcurves:
            pts = sorted(fc.keyframe_points, key=lambda k: k.co.x)
            for i, kp in enumerate(pts):
                s = shot_of(D, int(kp.co.x))
                nxt = pts[i + 1].co.x if i + 1 < len(pts) else None
                moving = bool(s.get("path")) or s["move"] == "handheld"
                kp.interpolation = "LINEAR" if (moving and nxt is not None and nxt < s["frames"][1]) else "CONSTANT"
    bpy.context.scene.camera = cam


def frame_plan(D):
    fps = D["fps"]
    F = round(D["duration_s"] * fps)
    want = set()
    T = lambda t: int(round(t * fps))
    def span(a, b, step):
        for f in range(max(0, a), min(F, b + 1), step):
            want.add(f)
    awake0 = T(next(c["t"] for c in D["cues"] if c["id"] == "1"))
    awake1 = T(next(c["t"] for c in D["cues"] if c["id"] == "8.10")) + 13
    span(0, F, 4)            # pass 2: everyone breathes, so every shot is drawn at least on fours (6 fps)
    for s in D["shots"]:
        want.add(s["frames"][0])
        if s.get("path") or s["move"] == "handheld":
            span(s["frames"][0], s["frames"][1] - 1, 2)
    for c in D["cues"]:
        f0 = T(c["t"])
        ext = max(int(k[0]) for k in c["shape"]) + max([0] + list(c.get("lag_frames", {}).values()))
        span(f0 - 1, f0 + ext + 2, 1)
        if "recover" in c:
            span(T(c["recover"]["t"]), T(c["recover"]["t"]) + c["recover"]["frames"], 2)
    ev = {e["id"]: e["t"] for e in D["events"]}
    for k, dur in (("doors_close", 2), ("doors_open", 2), ("doors_close_final", 2), ("phone_dims", 2.5)):
        if k in ev:
            span(T(ev[k]), T(ev[k] + dur), 2)
    for a, b in ((48, 80), (512, 521), (540, 549)):   # passing lights in the glass move: twos
        span(T(a), T(b), 2)
    for e in D["events"]:
        want.add(T(e["t"]))
    BL = common.load("blocking.json")
    for seg in BL["NOOR"]:
        want.add(T(seg["t"][0]))
        if seg["kind"] == "walk":
            span(T(seg["t"][0]), T(seg["t"][1]), 2)
    c0, c1 = BL["walter_clamp"]
    span(T(c0) - 3, T(c0) + 6, 1)
    span(T(BL["walter_paper"]["up"][0]), T(BL["walter_paper"]["up"][0]) + 14, 2)
    J = json.load(open(os.path.join(common.FILM_DIR, "design", "expressions", "shot_expressions.json")))
    cm = common.clock_map(D) if "v2" not in str(J.get("clock", "")) else (lambda t: t)
    for tr in J["tracks"].values():
        for t, name, _ in tr:
            span(T(cm(t)) - 8, T(cm(t)), 2)
    return sorted(f for f in want if 0 <= f < F)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
    D = common.dp()
    plan = frame_plan(D)
    os.makedirs(OUT, exist_ok=True)
    if "--frames" not in argv:
        json.dump({"frames": plan}, open(PLAN, "w"))
    t_from, t_to = arg("--from", 0.0), arg("--to", D["duration_s"])
    todo = [f for f in plan if t_from * 24 <= f < t_to * 24]
    if "--shots" in argv:   # re-render whole shots (plan frames inside them), replacing what is cached
        ids = set(arg("--shots", "").split(","))
        rng_ = [s["frames"] for s in D["shots"] if str(s["shot"]) in ids]
        todo = [f for f in plan if any(a <= f < b for a, b in rng_)]
        for f in (todo if "--plan" not in argv else []):
            p = os.path.join(OUT, f"{f:05d}.png")
            if os.path.exists(p):
                os.remove(p)
    if "--frames" in argv:   # spot checks: explicit frames (or times like 188s) to --out
        todo = [round(float(x[:-1]) * 24) if x.endswith("s") else int(x) for x in arg("--frames", "").split(",")]
        OUT = arg("--out", OUT)
        os.makedirs(OUT, exist_ok=True)
    print(f"plan: {len(plan)} frames of {round(D['duration_s'] * 24)}; this run: {len(todo)}")
    if "--plan" in argv:
        sys.exit(0)
    res_w = arg("--res", 640)
    scene = build_scene.build(res=(res_w, round(res_w / 2.39)), samples=arg("--samples", 8), previs=True)
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 3
    key_cameras(D)
    t_start = time.time()
    done = 0
    for f in todo:
        p = os.path.join(OUT, f"{f:05d}.png")
        if os.path.exists(p):
            continue
        scene.frame_set(f)
        scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        done += 1
        if done % 25 == 0:
            el = time.time() - t_start
            print(f"[previs] {done} rendered, {el / done:.1f} s/frame, frame {f}", flush=True)
    print("[previs] done", done)
