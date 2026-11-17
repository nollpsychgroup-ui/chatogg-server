"""Cue driver: keyframes lighting cues 0-8 (and the practical channels) from data/cue-stack.json.

Run after light_rig.build(). Every value comes from the data file; nothing is hand-keyed.
Interpolation rule: a key's `interp` says how the value ARRIVES at that key from the previous one
('const' = snap on that frame, 'linear', 'smooth'). Timeline markers are added for every cue so
the edit, the DP and the Composer see the same numbering in Blender.
"""
from collections import defaultdict

import bpy
from bpy_extras import anim_utils

from .common import kelvin_rgb, load, panel_names

INTERP = {"const": "CONSTANT", "linear": "LINEAR", "smooth": "BEZIER"}


def _fcurve(idb, path, index):
    ad = idb.animation_data
    act = ad.action
    cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
    return cb.fcurves.find(path, index=index)


def build(cues=None, layout=None):
    cue = cues or load("cue-stack.json")
    lay = layout or load("set_layout.json")
    scene = bpy.context.scene
    fps = cue["fps"]
    panels = panel_names(lay["panels"]["count"])
    to_frame = lambda t: 1 + round(t * fps)

    base = cue["baseline"]
    rgb_state = {p: kelvin_rgb(base["kelvin"], base["green_tint"]) for p in panels}
    keys = defaultdict(list)  # (object name or SCENE, path, index) -> [(frame, value, interp)]

    def add(obname, path, frame, value, interp, index=0):
        keys[(obname, path, index)].append((frame, value, interp))

    # initial state on frame 1
    init = cue["initial"]
    for p in panels:
        add(p, '["level"]', 1, init["ALL"]["level"], "const")
        add(p, '["breath"]', 1, init["ALL"].get("breath", 1), "const")
        for c in range(3):
            add(p, '["rgb"]', 1, rgb_state[p][c], "const", c)
    for ch, v in init.items():
        if ch not in ("ALL", "awake"):
            add(f"CTRL_{ch}", '["level"]', 1, v["level"], "const")
    add("SCENE", '["awake"]', 1, init.get("awake", 0), "const")

    scene.timeline_markers.clear()
    for c in sorted(cue["cues"], key=lambda c: c["tc"]):
        t0 = c["tc"]
        scene.timeline_markers.new(f"{c['id']} {c['label']}", frame=to_frame(t0))
        if "awake" in c:
            add("SCENE", '["awake"]', to_frame(t0), c["awake"], "const")
        for ev in c["events"]:
            tgt = ev["target"]
            targets = panels if tgt == "ALL" else [tgt]
            for name in targets:
                obname = name if name in panels else f"CTRL_{name}"
                for off, lvl, interp in ev["keys"]:
                    add(obname, '["level"]', to_frame(t0 + off), lvl, interp)
                if "breath" in ev:
                    add(obname, '["breath"]', to_frame(t0), ev["breath"], "const")
                if "kelvin" in ev and name in panels:
                    k = ev["kelvin"]
                    tint = base["green_tint"] if k == base["kelvin"] else cue["sodium"].get("green_tint", 0.0)
                    new = kelvin_rgb(k, tint)
                    fade = ev.get("kelvin_fade_s", 0.0)
                    for ci in range(3):
                        if fade > 0:
                            add(obname, '["rgb"]', to_frame(t0), rgb_state[name][ci], "smooth", ci)
                            add(obname, '["rgb"]', to_frame(t0 + fade), new[ci], "smooth", ci)
                        else:
                            add(obname, '["rgb"]', to_frame(t0), new[ci], "const", ci)
                    rgb_state[name] = new

    # insert, then set interpolation so each segment arrives the way its END key asks
    for (obname, path, index), ks in keys.items():
        idb = scene if obname == "SCENE" else bpy.data.objects[obname]
        ks.sort(key=lambda k: k[0])
        dedup = {}
        for f, v, it in ks:
            dedup[f] = (v, it)
        frames = sorted(dedup)
        for f in frames:
            v = dedup[f][0]
            if path == '["rgb"]':
                arr = list(idb["rgb"]); arr[index] = v; idb["rgb"] = arr
                idb.keyframe_insert(path, index=index, frame=f)
            else:
                idb[path[2:-2]] = v
                idb.keyframe_insert(path, frame=f)
        fc = _fcurve(idb, path, index)
        pts = sorted(fc.keyframe_points, key=lambda k: k.co.x)
        for i, kp in enumerate(pts):
            nxt = dedup[frames[i + 1]][1] if i + 1 < len(frames) else "const"
            kp.interpolation = INTERP[nxt]
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
        fc.update()

    scene.frame_start = 1
    scene.frame_end = to_frame(cue["duration_s"])
    return keys


def cue_frames(cues=None):
    cue = cues or load("cue-stack.json")
    return {c["id"]: 1 + round(c["tc"] * cue["fps"]) for c in cue["cues"]}
