"""Cue driver: keyframes every light from camera/cues.json (the DP's shared sync file).

Nothing here is hand-copied: cue times, panels, shapes (frame offsets), looks (level + Kelvin),
breath on/off, the cue-5 sympathy/recovery, the cue-8 overshoot and every practical event are
read from the file, so the Composer's temp score and the Blender lights cannot drift.

Keys land on whole frames (frame = round(t x fps), frame 0 = 0 s) with CONSTANT interpolation,
except the eases the DP names: the cue-3 sag, the cue-5 recovery and the cue-8 overshoot settle.
A timeline marker is added for every cue and event.
"""
from collections import defaultdict

import bpy
from bpy_extras import anim_utils

from .common import dp, load, t2f
from .light_rig import look_rgb

INTERP = {"const": "CONSTANT", "linear": "LINEAR", "smooth": "BEZIER"}
EASED = {"3", "8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9", "8.10"}


class Keys:
    def __init__(self):
        self.k = defaultdict(dict)  # (target, path, index) -> {frame: (value, interp)}

    def add(self, tgt, path, frame, value, interp="const", index=0):
        self.k[(tgt, path, index)][int(frame)] = (float(value), interp)

    def rgb(self, tgt, frame, rgb, interp="const"):
        for i in range(3):
            self.add(tgt, '["rgb"]', frame, rgb[i], interp, i)

    def apply(self, scene):
        for (tgt, path, index), ks in self.k.items():
            idb = scene if tgt == "SCENE" else bpy.data.objects[tgt]
            frames = sorted(ks)
            for f in frames:
                v = ks[f][0]
                if path == '["rgb"]':
                    arr = list(idb["rgb"]); arr[index] = v; idb["rgb"] = arr
                    idb.keyframe_insert(path, index=index, frame=f)
                elif path.startswith('["'):
                    idb[path[2:-2]] = v
                    idb.keyframe_insert(path, frame=f)
                else:
                    if path == "location":
                        loc = list(idb.location); loc[index] = v; idb.location = loc
                        idb.keyframe_insert("location", index=index, frame=f)
                    else:
                        setattr(idb, path, v)
                        idb.keyframe_insert(path, frame=f)
            ad = idb.animation_data
            cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
            fc = cb.fcurves.find(path, index=index)
            pts = sorted(fc.keyframe_points, key=lambda p: p.co.x)
            for i, kp in enumerate(pts):
                nxt = ks[frames[i + 1]][1] if i + 1 < len(frames) else "const"
                kp.interpolation = INTERP[nxt]
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
            fc.update()


def build(D=None, B=None):
    D = D or dp()
    B = B or load("build.json")
    scene = bpy.context.scene
    fps = D["fps"]
    looks = D["looks"]
    base_rgb = look_rgb(looks["BASE"], B)
    pids = [p["id"] for p in D["panels"]]
    K = Keys()
    state = {p: {"level": 1.0, "rgb": base_rgb} for p in pids}

    # opening state, frame 0
    for p in pids:
        K.add(p, '["level"]', 0, 1.0); K.add(p, '["breath"]', 0, 1.0); K.rgb(p, 0, base_rgb)
    K.add("SCENE", '["awake"]', 0, 0)

    def resolve(v, p, sympathy=None):
        if isinstance(v, str):
            if sympathy is not None and v != "BASE":
                return sympathy, state[p]["rgb"] if state[p]["rgb"] else base_rgb
            lk = looks[v]
            return lk.get("level", 0.0), look_rgb(lk, B) if "kelvin" in lk else state[p]["rgb"]
        if v >= 1.0:
            return v, base_rgb
        return v, state[p]["rgb"]

    scene.timeline_markers.clear()
    chan = defaultdict(list)  # practical channel -> [(t, level, interp)]
    for c in sorted(D["cues"], key=lambda c: c["t"]):
        f0 = t2f(c["t"], fps)
        scene.timeline_markers.new(f"cue {c['id']}", frame=f0)
        lag = c.get("lag_frames", {})
        symp = c.get("sympathy", {})
        for p in c["panels"]:
            shape = c["shape"]
            for i, (off, v) in enumerate(shape):
                lvl, rgb = resolve(v, p, symp.get(p))
                f = f0 + off + lag.get(p, 0)
                interp = "smooth" if (c["id"] in EASED and i > 0) else "const"
                K.add(p, '["level"]', f, lvl, interp)
                if rgb != state[p]["rgb"] or i == 0:
                    if c["id"] == "3" and i > 0:
                        K.rgb(p, f0, state[p]["rgb"])
                    K.rgb(p, f, rgb, interp)
                state[p] = {"level": lvl, "rgb": rgb}
        if "recover" in c:
            r = c["recover"]
            fr = t2f(r["t"], fps)
            for p in c["panels"]:
                K.add(p, '["level"]', fr, state[p]["level"], "const"); K.rgb(p, fr, state[p]["rgb"])
                K.add(p, '["level"]', fr + r["frames"], 1.0, "smooth"); K.rgb(p, fr + r["frames"], base_rgb, "smooth")
                state[p] = {"level": 1.0, "rgb": base_rgb}
        if c.get("breath") == "on":
            K.add("SCENE", '["awake"]', f0, 1)
        if c.get("breath") == "off":
            K.add("SCENE", '["awake"]', f0, 0)
            K.add("P1", '["breath"]', f0, 1)
        if c["id"] == "8.0":
            K.add("P1", '["breath"]', f0, 0)
        for p, what in c.get("also", {}).items():
            K.add(p, '["level"]', f0, 1.0); K.rgb(p, f0, base_rgb)
            state[p] = {"level": 1.0, "rgb": base_rgb}
        if c.get("windows") == "off":
            chan["WINDOWS"].append((c["t"], 0.0, "const"))
        if c["type"] == "blackout":
            for ch in ("DISPLAY", "WINDOWS", "DOOR", "PHONE_NOOR", "PHONE_KAI"):
                chan[ch].append((c["t"], 0.0, "const"))
        if c["type"] == "lights_up":
            chan["DISPLAY"].append((c["t"], 1.0, "const"))
            chan["PHONE_KAI"].append((c["t"], 1.0, "const"))

    # practical events
    ev = {e["id"]: e["t"] for e in D["events"]}
    for e in D["events"]:
        scene.timeline_markers.new(e["id"], frame=t2f(e["t"], fps))
    P = B["platform"]
    chan["DISPLAY"] += [(0, 1.0, "const")]
    chan["PHONE_KAI"] += [(0, 1.0, "const"), (ev["phone_dims"], 1.0, "const"), (ev["phone_dims"] + 2.0, 0.0, "linear")]
    chan["PLATFORM"] += [(0, 1.0, "const"), (ev["doors_close"] + 2 + P["slide_s"], 0.0, "const"),
                         (ev["train_slows"], 1.0, "const"), (ev["pull_away"] + P["slide_s"], 0.0, "const")]
    chan["DOOR"] += [(0, 1.0, "const"), (ev["doors_close"], 0.0, "const"), (ev["doors_open"], 1.0, "const"),
                     (ev["doors_close_final"], 0.0, "const")]
    chan["WINDOWS"] += [(0, 0.0, "const"), (ev["doors_close"] + 2.0, 1.0, "const")]
    chan["PHONE_NOOR"] += [(0, 0.0, "const"), (ev["mark_call_1"], 1.0, "const"), (ev["love_you"] + 2.0, 0.0, "const"),
                           (ev["marks_call"], 1.0, "const")]
    for ch, ks in chan.items():
        for t, v, it in ks:
            K.add(f"CTRL_{ch}", '["level"]', t2f(t, fps), v, it)

    # doors slide open/closed; platform slides past in the glass
    S = D["set"]
    dw = S["doors"]["y"][1] - S["doors"]["y"][0]
    for li, sy in enumerate((-1, 1)):
        nm = f"DOOR_LEAF_{li}"
        y_closed = bpy.data.objects[nm].location.y
        y_open = y_closed + sy * dw / 2 * 0.92
        for t, y, it in ((0, y_open, "const"), (ev["doors_close"], y_open, "const"), (ev["doors_close"] + 1.5, y_closed, "smooth"),
                         (ev["doors_open"], y_closed, "const"), (ev["doors_open"] + 1.5, y_open, "smooth"),
                         (ev["doors_close_final"], y_open, "const"), (ev["doors_close_final"] + 1.5, y_closed, "smooth")):
            K.add(nm, "location", t2f(t, fps), y, it, index=1)
    for t, y, it in ((0, 0, "const"), (ev["doors_close"] + 2, 0, "const"), (ev["doors_close"] + 2 + P["slide_s"], -P["slide_m"], "smooth"),
                     (ev["train_slows"], P["slide_m"], "const"), (ev["arrival_chime"], 0, "smooth"),
                     (ev["pull_away"], 0, "const"), (ev["pull_away"] + P["slide_s"], -P["slide_m"], "smooth")):
        K.add("PLATFORM_RIG", "location", t2f(t, fps), y, it, index=1)

    K.apply(scene)
    scene.frame_start = 0
    scene.frame_end = t2f(D["duration_s"], fps)
    return K


def frame_of(cue_or_event, offset_s=0.0, D=None):
    D = D or dp()
    for c in D["cues"] + D["events"]:
        if c["id"] == cue_or_event:
            return t2f(c["t"] + offset_s, D["fps"])
    raise KeyError(cue_or_event)
