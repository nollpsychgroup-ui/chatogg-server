"""Shared helpers: paths, data loading (DP cues, Designer palette, TA build), colour temperature."""
import json
import math
import os

import bpy

CG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM_DIR = os.path.dirname(CG_DIR)
DATA_DIR = os.path.join(CG_DIR, "data")
CACHE_DIR = os.path.join(CG_DIR, ".cache")  # git-ignored

DP_CUES = os.path.join(FILM_DIR, "camera", "cues.json")       # DP owns values; do not edit
PALETTE = os.path.join(FILM_DIR, "design", "palette.json")    # Character Designer owns values


def load(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


def dp():
    with open(DP_CUES) as f:
        return json.load(f)


_PAL = None


def pal(key):
    """Linear RGB from design/palette.json. Accepts 'set/moquette' or 'THE_RED'."""
    global _PAL
    if _PAL is None:
        with open(PALETTE) as f:
            _PAL = json.load(f)["colours"]
    for k, v in _PAL.items():
        if k == key or k.split(" ")[0] == key:
            return tuple(v["linear"])
    raise KeyError(key)


def _bb(k):
    t = k / 100.0
    if t <= 66:
        r = 255.0
        g = 99.4708025861 * math.log(t) - 161.1195681661
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    if t >= 66:
        b = 255.0
    elif t <= 19:
        b = 0.0
    else:
        b = 138.5177312231 * math.log(t - 10) - 305.0447927307
    srgb = [max(0.0, min(255.0, c)) / 255.0 for c in (r, g, b)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]


def kelvin_rgb(k, green=0.0, wb=4000.0):
    """Blackbody colour (linear RGB, max 1), white-balanced to `wb` K like a camera.
    `green` is the DP's look value (0..1); 0.25 = the slight green of real fluorescent tubes."""
    lin = _bb(k)
    ref = _bb(wb)
    lin = [c / r for c, r in zip(lin, ref)]
    g = green * 0.25
    lin[1] *= 1.0 + g
    lin[0] *= 1.0 - g * 0.4
    m = max(lin)
    return tuple(c / m for c in lin)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def link(obj, collection_name):
    coll(collection_name).objects.link(obj)
    return obj


def panels(d=None):
    return (d or dp())["panels"]


def section_bounds(d=None):
    """Y extents of each panel's section of the car (the joins are midway between panels)."""
    ps = panels(d)
    L = (d or dp())["set"]["length"]
    ys = [p["y"] for p in ps]
    out = {}
    for i, p in enumerate(ps):
        hi = L if i == 0 else (ys[i - 1] + ys[i]) / 2
        lo = 0.0 if i == len(ps) - 1 else (ys[i] + ys[i + 1]) / 2
        out[p["id"]] = (lo, hi)
    return out


def t2f(t, fps=24):
    """Seconds -> whole frame (DP: lights on ones, every key on a whole frame; frame 0 = 0 s)."""
    return int(round(t * fps))
