"""Scripted carriage set: shell, windows, doors, seats, rails, end walls, sign, display, platform.
Everything is generated from data/set_layout.json."""
import math

import bpy

from . import lookdev as ld
from .common import load, link, panel_x
from .mesh import box, plane, text


def _subtract(span, holes):
    """[a,b] minus a list of [c,d] intervals -> list of intervals."""
    out = [list(span)]
    for c, d in sorted(holes):
        nxt = []
        for a, b in out:
            if d <= a or c >= b:
                nxt.append([a, b]); continue
            if c > a:
                nxt.append([a, c])
            if d < b:
                nxt.append([d, b])
        out = nxt
    return [i for i in out if i[1] - i[0] > 1e-3]


def build(layout=None):
    lay = layout or load("set_layout.json")
    car = lay["car"]
    L, W, H = car["length"], car["width"], car["height"]
    sill, head = car["window_sill"], car["window_head"]
    door_h = 2.0
    T = 0.06  # wall thickness

    m_wall = ld.paint_material("laminate", "laminate", stroke_scale=7.0, stretch=6.0)
    m_ceil = ld.paint_material("ceiling", "ceiling", stroke_scale=6.0, stretch=4.0, variation=0.10)
    m_floor = ld.paint_material("floor", "floor", stroke_scale=5.0, stretch=8.0, roughness=0.55)
    m_seat = ld.paint_material("moquette", "moquette", stroke_scale=14.0, stretch=2.0, variation=0.22, roughness=0.9, bump=0.08)
    m_frame = ld.paint_material("seat_frame", "seat_frame", roughness=0.5)
    m_steel = ld.paint_material("steel", "steel", metallic=1.0, roughness=0.3, variation=0.10, stretch=12.0)
    m_door = ld.paint_material("door", "door", stroke_scale=8.0, stretch=1.5)
    m_end = ld.paint_material("end_wall", "end_wall", stroke_scale=7.0, stretch=1.0)
    m_glass = ld.glass_material()

    # floor / ceiling
    plane("FLOOR", (L / 2, 0, 0), (L, W), m_floor)
    plane("CEILING", (L / 2, 0, H), (L, W), m_ceil, normal="-Z")
    # ceiling coves (the curved shoulders of a carriage roof, faceted)
    for s in (-1, 1):
        cv = plane(f"COVE_{'R' if s > 0 else 'L'}", (L / 2, s * (W / 2 - 0.22), H - 0.1), (L, 0.5), m_ceil, normal="-Z")
        cv.rotation_euler = (s * -math.radians(28), 0, 0)

    # side walls with window and door openings
    doors = [(d["x"] - d["width"] / 2, d["x"] + d["width"] / 2) for d in car["doors"]]
    wins = [tuple(w) for w in car["window_bays"]]
    for s in (-1, 1):
        side = "R" if s > 0 else "L"
        y = s * (W / 2 + T / 2)
        nrm = "-Y" if s > 0 else "Y"
        bands = [((0.0, sill), doors), ((sill, head), doors + wins), ((head, door_h), doors), ((door_h, H), [])]
        for bi, ((z0, z1), holes) in enumerate(bands):
            for k, (a, b) in enumerate(_subtract((0.0, L), holes)):
                box(f"WALL_{side}_{bi}_{k}", ((a + b) / 2, y, (z0 + z1) / 2), (b - a, T, z1 - z0), m_wall)
        # window glass + reveals
        for k, (a, b) in enumerate(wins):
            g = plane(f"GLASS_{side}_{k}", ((a + b) / 2, s * (W / 2 + 0.01), (sill + head) / 2), (b - a, head - sill), m_glass, normal=nrm)
            g.visible_shadow = False  # glass never shadows the interior bounce
            box(f"SILL_{side}_{k}", ((a + b) / 2, s * (W / 2 - 0.04), sill - 0.02), (b - a, 0.1, 0.04), m_frame)
        # doors: two leaves, each with a glass pane (exterior seen through them at the platform)
        for d in car["doors"]:
            x0, w = d["x"], d["width"]
            for li, sx in enumerate((-1, 1)):
                cx = x0 + sx * w / 4
                nm = f"{d['name']}_{side}_LEAF{li}"
                box(nm + "_LOW", (cx, s * (W / 2 + 0.02), 0.5), (w / 2 - 0.01, 0.04, 1.0), m_door)
                box(nm + "_TOP", (cx, s * (W / 2 + 0.02), 1.93), (w / 2 - 0.01, 0.04, 0.14), m_door)
                box(nm + "_STILE", (cx + sx * (w / 4 - 0.04), s * (W / 2 + 0.02), 1.43), (0.08, 0.04, 0.86), m_door)
                box(nm + "_MULL", (cx - sx * (w / 4 - 0.03), s * (W / 2 + 0.02), 1.43), (0.06, 0.04, 0.86), m_door)
                gp = plane(nm + "_GLASS", (cx, s * (W / 2 + 0.02), 1.43), (w / 2 - 0.12, 0.86), m_glass, normal=nrm)
                gp.visible_shadow = False
            box(f"{d['name']}_{side}_HEADER", (x0, s * (W / 2 - 0.02), door_h + 0.03), (w + 0.1, 0.1, 0.06), m_frame)

    # end walls
    plane("END_WALL_NEAR", (0, 0, H / 2), (W, H), m_end, normal="X")
    plane("END_WALL_FAR", (L, 0, H / 2), (W, H), m_end, normal="-X")
    # rear cab door outline on the far wall
    box("FAR_DOOR", (L - 0.02, 0, 0.98), (0.03, 0.8, 1.96), m_door)
    box("FAR_DOOR_WIN", (L - 0.04, 0, 1.45), (0.01, 0.4, 0.5), ld.paint_material("black_glass", (0.004, 0.004, 0.004), roughness=0.05, variation=0.0))

    # QUIET CAR sign (vinyl) and LED destination display
    m_vinyl = ld.paint_material("sign_vinyl", "sign_vinyl", stroke_scale=12.0, stretch=1.0)
    m_type = ld.paint_material("sign_type", "sign_type", stroke_scale=30.0, variation=0.06)
    box("SIGN_QUIET_CAR", (L - 0.015, 0, 2.08), (0.01, 1.05, 0.22), m_vinyl)
    text("SIGN_TEXT", "QUIET CAR", (L - 0.025, 0, 2.08), 0.14, m_type)
    m_bezel = ld.paint_material("display_bezel", "display_bezel", roughness=0.3, variation=0.0)
    box("DISPLAY_BEZEL", (L - 0.02, 0, 1.86), (0.04, 1.3, 0.16), m_bezel)
    m_led = ld.emission_material("display_led", (0.62, 0.95, 0.80), 6.0)  # cool green-white LED, never orange
    d = text("DISPLAY_TEXT", "NEXT STOP: HOLLOWAY   11 MIN", (L - 0.045, 0, 1.86), 0.075, m_led)
    d.visible_diffuse = False
    d.visible_shadow = False

    # seats: transverse 2+2 bays
    S = lay["seats"]
    pw = S["pair_width"]
    for i, r in enumerate(S["rows"]):
        x, f = r["x"], r["facing"]
        for s in (-1, 1):
            side = "R" if s > 0 else "L"
            yc = s * (W / 2 - 0.04 - pw / 2)
            nm = f"SEAT_{i:02d}_{side}"
            box(nm + "_CUSH", (x, yc, 0.44), (0.48, pw, 0.11), m_seat, bevel=0.025)
            back = box(nm + "_BACK", (x - f * 0.25, yc, 0.76), (0.09, pw, 0.58), m_seat, bevel=0.025)
            back.rotation_euler = (0, -f * math.radians(9), 0)
            box(nm + "_BASE", (x, yc, 0.19), (0.38, pw - 0.1, 0.38), m_frame)

    # grab rails along the ceiling shoulders, poles in the vestibules
    for s in (-1, 1):
        box(f"RAIL_{'R' if s > 0 else 'L'}", (L / 2, s * 0.62, 1.98), (L - 0.6, 0.03, 0.03), m_steel)
    for d in car["doors"]:
        for s in (-1, 1):
            box(f"POLE_{d['name']}_{'R' if s > 0 else 'L'}", (d["x"], s * 0.55, H / 2), (0.035, 0.035, H), m_steel)

    # light trough baffles: hard-edged sections so the dark walks up the aisle (DP: no spill)
    P = lay["panels"]
    for i in range(P["count"] + 1):
        bx = panel_x(lay, 1) - P["pitch"] / 2 + i * P["pitch"]
        box(f"BAFFLE_{i:02d}", (bx, 0, H - 0.03), (0.03, 0.62, 0.06), m_ceil)
    for s in (-1, 1):
        box(f"TROUGH_{'R' if s > 0 else 'L'}", (L / 2 + 0.5, s * 0.31, H - 0.03), (L - 3.2, 0.03, 0.06), m_ceil)

    _platform(lay)
    _window_chase(lay)


def _platform(lay):
    """Short platform flat outside door A on the platform side, one cold-white lamp, light haze."""
    car = lay["car"]
    s = car["platform_side"]
    W = car["width"]
    da = car["doors"][0]
    m_conc = ld.paint_material("platform_concrete", (0.16, 0.16, 0.16), stroke_scale=4.0, stretch=2.0)
    m_edge = ld.paint_material("platform_edge", (0.45, 0.45, 0.42), stroke_scale=8.0)
    plane("PLATFORM_FLOOR", (da["x"], s * (W / 2 + 3.0), 0.0), (12.0, 5.8), m_conc, coll="EXTERIOR")
    box("PLATFORM_EDGE", (da["x"], s * (W / 2 + 0.25), 0.01), (12.0, 0.3, 0.02), m_edge, coll="EXTERIOR")
    box("PLATFORM_POST", (da["x"] + 1.4, s * (W / 2 + 2.6), 1.6), (0.08, 0.08, 3.2), m_conc, coll="EXTERIOR")


def _window_chase(lay):
    """Passing tunnel lights. Only visible in the glass (camera + glossy rays), they never light
    faces or panels (DP's flagged window rig). Strength is driven by the WINDOWS channel."""
    car = lay["car"]
    L, W = car["length"], car["width"]
    for s in (-1, 1):
        side = "R" if s > 0 else "L"
        mat = bpy.data.materials.new(f"window_chase_{side}")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission"); em.name = "EMIT"
        em.inputs["Color"].default_value = (0.75, 0.85, 1.0, 1)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping"); mp.name = "SCROLL"
        wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = "BANDS"; wave.bands_direction = "X"
        wave.inputs["Scale"].default_value = 0.08
        wave.inputs["Distortion"].default_value = 0.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.93
        ramp.color_ramp.elements[1].position = 0.97
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
        nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.name = "LEVEL"
        mul.inputs[1].default_value = 0.0
        nt.links.new(ramp.outputs["Color"], mul.inputs[0])
        nt.links.new(mul.outputs[0], em.inputs["Strength"])
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        ob = plane(f"WINDOW_CHASE_{side}", (L / 2, s * (W / 2 + 1.2), 1.4), (L + 40, 1.6), mat, coll="EXTERIOR",
                   normal="-Y" if s > 0 else "Y")
        for attr in ("visible_diffuse", "visible_shadow", "visible_volume_scatter"):
            setattr(ob, attr, False)
