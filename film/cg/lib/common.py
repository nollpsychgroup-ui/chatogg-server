"""Shared helpers: paths, data loading, colour temperature."""
import json
import math
import os

import bpy

CG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(CG_DIR, "data")
CACHE_DIR = os.path.join(CG_DIR, ".cache")  # git-ignored: generated textures, .blend files


def load(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


WHITE_BALANCE_K = 4000.0  # virtual camera white balance: 4300 K panels read cool, sodium reads orange


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


def kelvin_rgb(k, green_tint=0.0, balance=True):
    """Approximate blackbody colour (linear RGB, max channel 1), white-balanced to WHITE_BALANCE_K
    like a camera would be. green_tint adds the slight green cast of real fluorescent tubes."""
    lin = _bb(k)
    if balance:
        ref = _bb(WHITE_BALANCE_K)
        lin = [c / r for c, r in zip(lin, ref)]
    lin[1] *= 1.0 + green_tint
    lin[0] *= 1.0 - green_tint * 0.4
    m = max(lin)
    return tuple(c / m for c in lin)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def link(obj, collection_name):
    coll = bpy.data.collections.get(collection_name)
    if coll is None:
        coll = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(coll)
    coll.objects.link(obj)
    return obj


def panel_names(n=12):
    return [f"P{i}" for i in range(1, n + 1)]


def panel_x(layout, i):
    p = layout["panels"]
    return p["first_x"] + (i - 1) * p["pitch"]
