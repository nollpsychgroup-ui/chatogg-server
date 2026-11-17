"""The light rig, from camera/cues.json (DP) + data/build.json (TA wattages).

P1..P12 are Cycles area lights named exactly as the cue numbering (one panel = one light = one
hum partial). Each carries ["level"], ["rgb"], ["breath"], ["partial"]. Drivers feed BOTH the light
and its visible diffuser from those properties, so a panel can never look lit while casting
nothing. Breathing: energy = W x level x (1 + depth x awake x breath x sin(2 pi f / period)),
with depth/period read from cues.json (shared by name with the Composer's hum build).

Each panel's direct light is linked to its own section of the set (LL_Pn) plus every character
and prop: virtual baffles give the DP's hard edge on floor/seats/walls in cue 7 while faces at
the edge still catch the neighbour's spill. Bounce light is unrestricted.

Practical channels are empties CTRL_<name> with ["level"]: DISPLAY, WINDOWS, PLATFORM, DOOR,
PHONE_NOOR, PHONE_KAI.
"""
import math

import bpy

from . import lookdev as ld
from .common import coll, kelvin_rgb, link, load, dp
from .mesh import box

PRACTICALS = ["DISPLAY", "WINDOWS", "PLATFORM", "DOOR", "PHONE_NOOR", "PHONE_KAI"]


def _var(drv, name, id_type, idb, path):
    v = drv.variables.new()
    v.name, v.type = name, "SINGLE_PROP"
    v.targets[0].id_type = id_type
    v.targets[0].id = idb
    v.targets[0].data_path = path


def _breath(fc, scene, ob, base):
    d = fc.driver
    d.type = "SCRIPTED"
    _var(d, "lvl", "OBJECT", ob, '["level"]')
    _var(d, "br", "OBJECT", ob, '["breath"]')
    _var(d, "aw", "SCENE", scene, '["awake"]')
    _var(d, "dp", "SCENE", scene, '["breath_depth"]')
    _var(d, "pf", "SCENE", scene, '["breath_period_f"]')
    d.expression = f"{base}*lvl*(1+dp*aw*br*sin(frame*6.283185/pf))"


def drive_level(idb, path, ctrl, base, index=-1):
    fc = idb.driver_add(path, index) if index >= 0 else idb.driver_add(path)
    fc.driver.type = "SCRIPTED"
    _var(fc.driver, "lvl", "OBJECT", ctrl, '["level"]')
    fc.driver.expression = f"{base}*lvl"
    return fc


def look_rgb(look, B):
    return kelvin_rgb(look.get("kelvin", 4300), look.get("green", 0.0), B["white_balance_k"])


def build(D=None, B=None, sections=None):
    D = D or dp()
    B = B or load("build.json")
    scene = bpy.context.scene
    fps = D["fps"]
    scene["awake"] = 0.0
    scene["breath_depth"] = float(D["breath"]["depth"])
    scene["breath_period_f"] = float(D["breath"]["period_s"] * fps)
    R = B["panel_rig"]
    base_rgb = look_rgb(D["looks"]["BASE"], B)
    char_coll = coll("CHARACTERS")
    props_coll = coll("PROPS_LOOSE")
    for p in D["panels"]:
        name = p["id"]
        sx, sy = p["size_m"]
        ldata = bpy.data.lights.new(name, "AREA")
        ldata.shape = "RECTANGLE"
        ldata.size, ldata.size_y = sx, sy
        ldata.spread = math.radians(R["spread_deg"])
        ob = bpy.data.objects.new(name, ldata)
        ob.location = (0, p["y"], R["z"] - 0.005)
        link(ob, "LIGHT_RIG")
        ob["level"] = 1.0
        ob["breath"] = 1.0
        ob["rgb"] = list(base_rgb)
        ob["partial"] = p["partial"]
        mat = ld.emission(f"diffuser_{name}", base_rgb, R["diffuser_strength"])
        dif = box(f"DIFFUSER_{name}", (0, p["y"], R["z"]), (sx, sy, 0.004), mat, "LIGHT_RIG")
        for a in ("visible_diffuse", "visible_shadow", "visible_volume_scatter"):
            setattr(dif, a, False)
        skirt = ld.paint("panel_skirt", "set/trim")
        for k, (cx, cy, w, d) in enumerate(((sx / 2 + 0.01, 0, 0.02, sy + 0.04), (-sx / 2 - 0.01, 0, 0.02, sy + 0.04),
                                            (0, sy / 2 + 0.01, sx, 0.02), (0, -sy / 2 - 0.01, sx, 0.02))):
            sk = box(f"SKIRT_{name}_{k}", (cx, p["y"] + cy, R["z"] + 0.0), (w, d, R["skirt_depth"] + 0.01), skirt, "LIGHT_RIG")
            sk.visible_shadow = False
        _breath(ldata.driver_add("energy"), scene, ob, R["watts"])
        em = mat.node_tree.nodes["EMIT"]
        _breath(em.inputs["Strength"].driver_add("default_value"), scene, ob, R["diffuser_strength"])
        for c in range(3):
            for tgt, path in ((ldata, "color"), (em.inputs["Color"], "default_value")):
                fc = tgt.driver_add(path, c)
                fc.driver.type = "SCRIPTED"
                _var(fc.driver, "c", "OBJECT", ob, f'["rgb"][{c}]')
                fc.driver.expression = "c"
        # light linking: own section + every character and loose prop
        if sections is not None:
            rc = sections[name]
            for child in (char_coll, props_coll):
                if child.name not in rc.children:
                    rc.children.link(child)
            ob.light_linking.receiver_collection = rc

    ctrls = {}
    for ch in PRACTICALS:
        e = bpy.data.objects.new(f"CTRL_{ch}", None)
        e["level"] = 0.0
        link(e, "LIGHT_RIG")
        ctrls[ch] = e

    drive_level(bpy.data.materials["display_led"].node_tree.nodes["EMIT"].inputs["Strength"], "default_value", ctrls["DISPLAY"], 5.0)
    for side in ("A", "B"):
        nt = bpy.data.materials[f"window_chase_{side}"].node_tree
        drive_level(nt.nodes["LEVEL"].inputs[1], "default_value", ctrls["WINDOWS"], 6.0)
        fc = nt.nodes["SCROLL"].inputs["Location"].driver_add("default_value", 1)
        fc.driver.type = "SCRIPTED"
        fc.driver.expression = "frame*0.9"

    # PLATFORM: one cold-white lamp, ~5000 K, slight green (mercury-vapour look)
    S = D["set"]
    HW = S["half_width"]
    dy = sum(S["doors"]["y"]) / 2
    rig = bpy.data.objects["PLATFORM_RIG"]
    prgb = kelvin_rgb(5000, 0.35, B["white_balance_k"])
    lamp = bpy.data.lights.new("PLATFORM_LAMP", "SPOT")
    lamp.spot_size = math.radians(110)
    lamp.spot_blend = 0.6
    lamp.color = prgb
    lamp.shadow_soft_size = 0.12
    lob = bpy.data.objects.new("PLATFORM_LAMP", lamp)
    lob.location = (HW + 2.0, dy + 1.6, 3.15)
    lob.parent = rig
    link(lob, "EXTERIOR")
    drive_level(lamp, "energy", ctrls["PLATFORM"], B["platform"]["lamp_watts"])
    m_head = ld.emission("platform_lamp_head", prgb, 25.0)
    head = box("PLATFORM_LAMP_HEAD", (HW + 2.0, dy + 1.6, 3.2), (0.55, 0.2, 0.05), m_head, "EXTERIOR")
    head.visible_diffuse = False
    head.parent = rig
    drive_level(m_head.node_tree.nodes["EMIT"].inputs["Strength"], "default_value", ctrls["PLATFORM"], 25.0)
    # platform light reaches only the platform and whoever stands on it (not the car interior)
    plc = bpy.data.collections.get("LL_PLATFORM") or bpy.data.collections.new("LL_PLATFORM")
    for o in coll("EXTERIOR").objects:
        if o.type == "MESH" and o.name not in plc.objects:
            plc.objects.link(o)
    for child in (coll("CHARACTERS"),):
        if child.name not in plc.children:
            plc.children.link(child)
    lob.light_linking.receiver_collection = plc

    # DOOR: open-door indicator (cool green, not orange)
    m_dl = ld.emission("door_light", (0.3, 1.0, 0.45), 0.0)
    drive_level(m_dl.node_tree.nodes["EMIT"].inputs["Strength"], "default_value", ctrls["DOOR"], 12.0)
    for y in S["doors"]["y"]:
        box(f"DOOR_INDICATOR_{y:.1f}", (HW - 0.06, y, 2.09), (0.03, 0.12, 0.03), m_dl, "LIGHT_RIG")

    # PHONES: screens/lights are created with the figures; connect them here
    for ch, key in (("PHONE_NOOR", "noor"), ("PHONE_KAI", "kai")):
        for mname in (f"screen_{key}", f"endcall_{key}"):
            m = bpy.data.materials.get(mname)
            if m:
                drive_level(m.node_tree.nodes["EMIT"].inputs["Strength"], "default_value", ctrls[ch], 6.0)
        lo = bpy.data.objects.get(f"{ch}_LIGHT")
        if lo:
            drive_level(lo.data, "energy", ctrls[ch], 2.5)
    return ctrls
