"""Scripted light rig.

P1..P12 are named Cycles area lights (one per ceiling panel = one DMX channel = one hum partial).
Each panel light carries custom properties that the cue driver keyframes:
    ["level"]  1.0 = baseline output (0 = off, 1.1 = relight overshoot)
    ["rgb"]    colour (from Kelvin; 4300 K + green at rest, 2200 K sodium in the brownout)
    ["breath"] 1 = this panel breathes while the car is awake
Drivers turn those into light energy/colour AND the matching diffuser emission, so the
visible panel and the light it casts can never disagree.
Scene properties: ["awake"] (0/1), ["breath_depth"], ["breath_period_f"].

Practical channels (DISPLAY, WINDOWS, PLATFORM, PHONE_NOOR, PHONE_KAI, DOOR_LIGHT) are empties
named CTRL_<channel> with a ["level"] property.
"""
import bpy

from . import lookdev as ld
from .common import kelvin_rgb, link, load, panel_names, panel_x
from .mesh import box, plane

PANEL_WATTS = 95.0        # area light power at level 1.0
DIFFUSER_STRENGTH = 4.0   # diffuser emission at level 1.0 (what the camera sees)
PANEL_SPREAD_DEG = 90.0  # snoot: keeps each panel's pool in its own section
PRACTICALS = ["DISPLAY", "WINDOWS", "PLATFORM", "PHONE_NOOR", "PHONE_KAI", "DOOR_LIGHT"]


def _var(drv, name, id_type, idb, path):
    v = drv.variables.new()
    v.name = name
    v.type = "SINGLE_PROP"
    v.targets[0].id_type = id_type
    v.targets[0].id = idb
    v.targets[0].data_path = path
    return v


def _breath_vars(drv, scene, ob):
    _var(drv, "lvl", "OBJECT", ob, '["level"]')
    _var(drv, "br", "OBJECT", ob, '["breath"]')
    _var(drv, "aw", "SCENE", scene, '["awake"]')
    _var(drv, "d", "SCENE", scene, '["breath_depth"]')
    _var(drv, "pf", "SCENE", scene, '["breath_period_f"]')


def _breath_expr(base):
    return f"{base}*lvl*(1+d*aw*br*sin(frame*6.283185/pf))"


def _drive_level(idb, path, ctrl, base, index=-1):
    fc = idb.driver_add(path, index) if index >= 0 else idb.driver_add(path)
    drv = fc.driver
    drv.type = "SCRIPTED"
    _var(drv, "lvl", "OBJECT", ctrl, '["level"]')
    drv.expression = f"{base}*lvl"
    return fc


def build(layout=None, cues=None):
    lay = layout or load("set_layout.json")
    cue = cues or load("cue-stack.json")
    scene = bpy.context.scene
    fps = cue["fps"]
    scene["awake"] = float(cue["initial"].get("awake", 0))
    scene["breath_depth"] = float(cue["breathing"]["depth"])
    scene["breath_period_f"] = float(cue["breathing"]["period_s"] * fps)

    P = lay["panels"]
    H = lay["car"]["height"]
    base_rgb = kelvin_rgb(cue["baseline"]["kelvin"], cue["baseline"]["green_tint"])
    for i, name in enumerate(panel_names(P["count"]), start=1):
        x = panel_x(lay, i)
        ldata = bpy.data.lights.new(name, "AREA")
        ldata.shape = "RECTANGLE"
        ldata.size, ldata.size_y = P["size"]
        ldata.spread = PANEL_SPREAD_DEG * 3.14159265 / 180
        ldata.energy = PANEL_WATTS
        ob = bpy.data.objects.new(name, ldata)
        ob.location = (x, 0, P["z"] - 0.01)
        link(ob, "LIGHT_RIG")
        ob["level"] = 1.0
        ob["breath"] = 1.0
        ob["rgb"] = list(base_rgb)
        ob["partial"] = i + 1 if i < 12 else 17
        # diffuser the camera sees
        mat = ld.emission_material(f"diffuser_{name}", base_rgb, DIFFUSER_STRENGTH)
        dif = plane(f"DIFFUSER_{name}", (x, 0, P["z"]), tuple(P["size"]), mat, coll="LIGHT_RIG", normal="-Z")
        for attr in ("visible_diffuse", "visible_shadow", "visible_volume_scatter", "visible_transmission"):
            setattr(dif, attr, False)
        dif["panel"] = name
        # drivers
        fc = ldata.driver_add("energy"); _breath_vars(fc.driver, scene, ob); fc.driver.expression = _breath_expr(PANEL_WATTS)
        em = mat.node_tree.nodes["EMIT"]
        fc = em.inputs["Strength"].driver_add("default_value"); _breath_vars(fc.driver, scene, ob)
        fc.driver.expression = _breath_expr(DIFFUSER_STRENGTH)
        for c in range(3):
            fc = ldata.driver_add("color", c); _var(fc.driver, "c", "OBJECT", ob, f'["rgb"][{c}]'); fc.driver.expression = "c"
            fc = em.inputs["Color"].driver_add("default_value", c); _var(fc.driver, "c", "OBJECT", ob, f'["rgb"][{c}]'); fc.driver.expression = "c"

    ctrls = {}
    for ch in PRACTICALS:
        e = bpy.data.objects.new(f"CTRL_{ch}", None)
        e["level"] = float(cue["initial"].get(ch, {}).get("level", 0.0))
        link(e, "LIGHT_RIG")
        ctrls[ch] = e

    # DISPLAY
    led = bpy.data.materials["display_led"].node_tree.nodes["EMIT"]
    _drive_level(led.inputs["Strength"], "default_value", ctrls["DISPLAY"], 6.0)

    # WINDOWS: passing lights (strength + scroll)
    for side in ("L", "R"):
        nt = bpy.data.materials[f"window_chase_{side}"].node_tree
        _drive_level(nt.nodes["LEVEL"].inputs[1], "default_value", ctrls["WINDOWS"], 30.0)
        fc = nt.nodes["SCROLL"].inputs["Location"].driver_add("default_value", 0)
        fc.driver.type = "SCRIPTED"; fc.driver.expression = "frame*0.9"

    # PLATFORM: one cold-white lamp outside door A
    car = lay["car"]
    s = car["platform_side"]
    da = car["doors"][0]
    pk = cue["platform"]["kelvin"]
    lamp = bpy.data.lights.new("PLATFORM_LAMP", "SPOT")
    lamp.energy = 650.0
    lamp.spot_size = 2.0
    lamp.spot_blend = 0.5
    lamp.color = kelvin_rgb(pk)
    lamp.shadow_soft_size = 0.15
    lob = bpy.data.objects.new("PLATFORM_LAMP", lamp)
    lob.location = (da["x"] + 1.4, s * (car["width"] / 2 + 2.3), 3.15)
    link(lob, "EXTERIOR")
    _drive_level(lamp, "energy", ctrls["PLATFORM"], 650.0)
    m_head = ld.emission_material("platform_lamp_head", kelvin_rgb(pk), 20.0)
    head = box("PLATFORM_LAMP_HEAD", (lob.location.x, lob.location.y, 3.2), (0.5, 0.18, 0.05), m_head, coll="EXTERIOR")
    head.visible_diffuse = False
    _drive_level(m_head.node_tree.nodes["EMIT"].inputs["Strength"], "default_value", ctrls["PLATFORM"], 20.0)

    # DOOR_LIGHT: open-door indicators above each door (cool green, not orange)
    m_dl = ld.emission_material("door_light", (0.3, 1.0, 0.45), 0.0)
    _drive_level(m_dl.node_tree.nodes["EMIT"].inputs["Strength"], "default_value", ctrls["DOOR_LIGHT"], 12.0)
    for d in car["doors"]:
        for side, sy in (("L", -1), ("R", 1)):
            box(f"DOOR_LIGHT_{d['name']}_{side}", (d["x"], sy * (car["width"] / 2 - 0.08), 2.1), (0.12, 0.03, 0.03), m_dl, coll="LIGHT_RIG")

    # PHONES: screens and their small soft lights are created by figures.py; connect them here
    for ch, key in (("PHONE_NOOR", "noor"), ("PHONE_KAI", "kai")):
        mat = bpy.data.materials.get(f"screen_{key}")
        if mat:
            _drive_level(mat.node_tree.nodes["EMIT"].inputs["Strength"], "default_value", ctrls[ch], 3.0)
        lo = bpy.data.objects.get(f"{ch}_LIGHT")
        if lo:
            _drive_level(lo.data, "energy", ctrls[ch], 3.0)
    return ctrls
