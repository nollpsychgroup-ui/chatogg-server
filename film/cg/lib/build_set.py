"""The carriage, built from camera/cues.json (DP layout) + data/build.json (TA detail).

Axes (DP): Z up; Y runs down the car from end wall B (y=0) to end wall A (y=13, Noor);
side A is -X, side B is +X. A 4 m unlit vestibule (y -4..0) sits beyond the gangway at wall B
for the Meter camera (Pos A). Longitudinal benches; sliding doors on side B between P6 and P7;
QUIET CAR sign and the destination display on wall A above Noor.
"""
import math

import bpy

from . import lookdev as ld
from .common import coll, dp, link, load, section_bounds, t2f
from .mesh import Sections, box, plane, text


def _subtract(span, holes):
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


def build(D=None, B=None):
    D = D or dp()
    B = B or load("build.json")
    S = D["set"]
    L, HW, H = S["length"], S["half_width"], S["ceiling"]
    W = 2 * HW
    win = B["windows"]
    sill, head = win["sill"], win["head"]
    door_h = B["door_height"]
    dy0, dy1 = S["doors"]["y"]
    T = 0.06
    sec = Sections(section_bounds(D))

    m_wall = ld.paint("laminate", "set/laminate", stretch=5.0)
    m_ceil = ld.paint("ceiling", "set/ceiling", variation=0.14)
    m_floor = ld.paint("floor", "set/floor", stretch=6.0, roughness=0.7)
    m_seat = ld.paint("moquette", "set/moquette", stroke_scale=26.0, stretch=2.5, variation=0.26, roughness=0.9, bump=0.08)
    m_pat = ld.paint("moquette_pattern", "set/moquette_pattern", stroke_scale=26.0, stretch=2.5, roughness=0.9)
    m_trim = ld.gloss("trim_steel", "set/trim", roughness=0.35, metallic=1.0)
    m_trim_p = ld.paint("trim_paint", "set/trim")
    m_glass = ld.glass()

    # floor, ceiling, coves (section-split so each panel lights only its own section)
    sec.yplane("FLOOR", 0, 0, L, 0, W, "Z", m_floor)
    sec.yplane("CEILING", 0, 0, L, H, W, "-Z", m_ceil)
    for s in (-1, 1):
        for ob in sec.yplane(f"COVE_{'B' if s > 0 else 'A'}", s * (HW - 0.22), 0, L, H - 0.1, 0.5, "-Z", m_ceil):
            ob.rotation_euler = (0, s * math.radians(28), 0)

    # side walls: bands around window bays and the side-B doors
    for s, side in ((-1, "A"), (1, "B")):
        x = s * (HW + T / 2)
        bays = [tuple(b) for b in win[f"bays_{side}"]]
        doors = [(dy0, dy1)] if side == "B" else []
        bands = [((0.0, sill), doors), ((sill, head), doors + bays), ((head, door_h), doors), ((door_h, H), [])]
        for bi, ((z0, z1), holes) in enumerate(bands):
            for k, (a, b) in enumerate(_subtract((0.0, L), holes)):
                sec.ybox(f"WALL_{side}{bi}{k}", x, a, b, (z0 + z1) / 2, T, z1 - z0, m_wall)
        for k, (a, b) in enumerate(bays):
            for g in sec.yplane(f"GLASS_{side}{k}", s * (HW + 0.01), a, b, (sill + head) / 2, head - sill,
                                "-X" if s > 0 else "X", m_glass):
                g.visible_shadow = False
            sec.ybox(f"SILL_{side}{k}", s * (HW - 0.03), a, b, sill - 0.015, 0.08, 0.03, m_trim_p)

    # sliding doors (side B): two leaves with glass, on rig empties so M4 can animate them
    dmid, dw = (dy0 + dy1) / 2, (dy1 - dy0)
    for li, sy in enumerate((-1, 1)):
        rig = bpy.data.objects.new(f"DOOR_LEAF_{li}", None)
        rig.location = (HW + 0.03, dmid + sy * dw / 4, 0)
        link(rig, "SET")
        parts = [
            box(f"DOOR_LEAF_{li}_LOW", (0, 0, 0.5), (0.04, dw / 2 - 0.01, 1.0), m_trim_p),
            box(f"DOOR_LEAF_{li}_TOP", (0, 0, 1.93), (0.04, dw / 2 - 0.01, 0.14), m_trim_p),
            box(f"DOOR_LEAF_{li}_STILE", (0, sy * (dw / 4 - 0.04), 1.43), (0.04, 0.08, 0.86), m_trim_p),
            box(f"DOOR_LEAF_{li}_MEET", (0, -sy * (dw / 4 - 0.03), 1.43), (0.04, 0.06, 0.86), m_trim_p),
            plane(f"DOOR_LEAF_{li}_GLASS", (0, 0, 1.43), (dw / 2 - 0.12, 0.86), m_glass, normal="-X"),
        ]
        for p in parts:
            p.parent = rig
        parts[-1].visible_shadow = False
        sec.assign(rig, [])
        for p in parts:
            sec.assign(p, ["P6", "P7"])
    box("DOOR_HEADER", (HW - 0.03, dmid, door_h + 0.03), (0.08, dw + 0.12, 0.06), m_trim_p)
    sec.assign(bpy.data.objects["DOOR_HEADER"], ["P6", "P7"])
    for s in (-1, 1):
        for y in (dy0 - 0.04, dy1 + 0.04):
            ob = box(f"DOOR_POLE_{y:.1f}_{s}", (HW - 0.12, y, H / 2), (0.035, 0.035, H), m_trim)
            sec.assign(ob, [sec.which(y)])
        break

    # longitudinal benches (teal moquette), side B split by the doors
    bn = B["benches"]
    for s, side in ((-1, "A"), (1, "B")):
        spans = [(bn["end_gap"], L - 0.62)] if side == "A" else [(bn["end_gap"], dy0 - 0.08), (dy1 + 0.08, L - 0.62)]
        for k, (a, b) in enumerate(spans):
            xc = s * (HW - bn["depth"] / 2 - 0.02)
            sec.ybox(f"BENCH_{side}{k}_CUSH", xc, a, b, bn["seat_z"] - 0.06, bn["depth"], 0.12, m_seat, bevel=0.02)
            sec.ybox(f"BENCH_{side}{k}_BASE", xc + s * 0.04, a, b, 0.2, bn["depth"] - 0.1, 0.4, m_trim_p)
            for ob in sec.ybox(f"BENCH_{side}{k}_BACK", s * (HW - 0.06), a, b, (bn["seat_z"] + bn["back_top"]) / 2 + 0.02,
                               0.08, bn["back_top"] - bn["seat_z"], m_pat, bevel=0.02):
                ob.rotation_euler = (0, -s * math.radians(8), 0)
            # armrest dividers every ~1.6 m
            n = max(1, int((b - a) / 1.6))
            for j in range(n + 1):
                y = a + j * (b - a) / n
                ob = box(f"BENCH_{side}{k}_ARM{j}", (s * (HW - 0.25), y, bn["seat_z"] + 0.12), (0.42, 0.04, 0.05), m_trim_p)
                sec.assign(ob, [sec.which(y)])

    # Noor's single transverse seat against wall A, facing down the car
    ns = B["noor_seat"]
    for nm, c, sz, m in (("NOOR_SEAT_CUSH", (0, L - 0.04 - ns["depth"] / 2, bn["seat_z"] - 0.06), (ns["width"], ns["depth"], 0.12), m_seat),
                         ("NOOR_SEAT_BASE", (0, L - 0.04 - ns["depth"] / 2 + 0.04, 0.2), (ns["width"] - 0.1, ns["depth"] - 0.1, 0.4), m_trim_p),
                         ("NOOR_SEAT_BACK", (0, L - 0.06, 0.74), (ns["width"], 0.08, 0.54), m_pat)):
        ob = box(nm, c, sz, m, bevel=0.02)
        sec.assign(ob, ["P1"])

    # grab rails along the ceiling shoulders
    for s in (-1, 1):
        sec.ybox(f"RAIL_{'B' if s > 0 else 'A'}", s * 0.62, 0.3, L - 0.3, 1.98, 0.03, 0.03, m_trim)

    # end wall A: QUIET CAR sign + destination display (cold white-green LED, never amber)
    for ob in (plane("WALL_A", (0, L, H / 2), (W, H), m_wall, normal="-Y"),):
        sec.assign(ob, ["P1", "P2"])
    m_vinyl = ld.paint("sign_vinyl", "set/sign_vinyl", tier="costume", variation=0.06)
    m_type = ld.paint("sign_text", "set/sign_text", tier="costume", variation=0.0)
    sv = box("SIGN_QUIET_CAR", (0, L - 0.01, 2.10), (1.0, 0.01, 0.2), m_vinyl)
    st = text("SIGN_TEXT", "QUIET CAR", (0, L - 0.022, 2.10), 0.15, m_type)
    bz = box("DISPLAY_BEZEL", (0, L - 0.027, 1.84), (1.25, 0.05, 0.17), ld.gloss("bezel", (0.004, 0.004, 0.004), roughness=0.3))
    for ob in (sv, st, bz):
        sec.assign(ob, ["P1", "P2"])
    _display(D, L)

    # end wall B with the open gangway, and the unlit vestibule (real geometry for Pos A)
    gw = B["gangway"]
    for nm, c, sz in (("WALL_B_L", (-(HW + gw["half_width"]) / 2, 0, H / 2), (HW - gw["half_width"], T, H)),
                      ("WALL_B_R", ((HW + gw["half_width"]) / 2, 0, H / 2), (HW - gw["half_width"], T, H)),
                      ("WALL_B_TOP", (0, 0, (gw["height"] + H) / 2), (2 * gw["half_width"], T, H - gw["height"]))):
        sec.assign(box(nm, c, sz, m_wall), ["P12"])
    v0, v1 = S["vestibule_y"]
    m_vest = ld.paint("vestibule", "set/floor", variation=0.12)
    vest = [plane("VEST_FLOOR", (0, (v0 + v1) / 2, 0), (W, v1 - v0), m_floor, normal="Z"),
            plane("VEST_CEIL", (0, (v0 + v1) / 2, H), (W, v1 - v0), m_vest, normal="-Z"),
            plane("VEST_WALL_A", (-HW, (v0 + v1) / 2, H / 2), (v1 - v0, H), m_vest, normal="X"),
            plane("VEST_WALL_B", (HW, (v0 + v1) / 2, H / 2), (v1 - v0, H), m_vest, normal="-X"),
            plane("VEST_END", (0, v0, H / 2), (W, H), m_vest, normal="Y")]
    for ob in vest:
        sec.assign(ob, ["P12"])

    _platform(D, B)
    _window_chase(D)
    return sec


def _display(D, L):
    """One text object per display state (events D0..D4, NOW ARRIVING), switched by keyed visibility.
    All share the display_led material, whose strength is the DISPLAY channel."""
    m_led = ld.emission("display_led", "set/led_display", 5.0)
    states = [("D0", "NEXT STOP: HOLLOWAY"), ("D1", "NEXT STOP: HOLLOWAY - 11 MIN"), ("D2", "NEXT STOP: HOLLOWAY - 8 MIN"),
              ("D3", "NEXT STOP: HOLLOWAY - 5 MIN"), ("D4", "NEXT STOP: HOLLOWAY - 2 MIN"), ("train_slows", "NOW ARRIVING: HOLLOWAY")]
    times = {e["id"]: e["t"] for e in D["events"]}
    seq = sorted(((times[k], k, body) for k, body in states if k in times))
    for i, (t, k, body) in enumerate(seq):
        ob = text(f"DISPLAY_{k}", body, (0, L - 0.056, 1.84), 0.075, m_led)
        ob.visible_diffuse = False
        ob.visible_shadow = False
        t_end = seq[i + 1][0] if i + 1 < len(seq) else None
        for f, hide in ((0, True), (t2f(t), False)) + (((t2f(t_end), True),) if t_end is not None else ()):
            ob.hide_render = hide
            ob.keyframe_insert("hide_render", frame=f)


def _platform(D, B):
    """Platform flat outside the side-B doors: concrete, edge line, lamp post, light ground haze.
    It sits on a rig empty so it can slide away during the pull-away."""
    S = D["set"]
    HW = S["half_width"]
    dy = sum(S["doors"]["y"]) / 2
    rig = bpy.data.objects.new("PLATFORM_RIG", None)
    link(rig, "EXTERIOR")
    m_conc = ld.paint("platform_concrete", (0.12, 0.12, 0.115), stroke_scale=10.0, stretch=1.5)
    m_edge = ld.paint("platform_edge", (0.42, 0.42, 0.40))
    parts = [plane("PLATFORM_FLOOR", (HW + 3.1, dy, -0.02), (5.8, 16.0), m_conc, "EXTERIOR"),
             box("PLATFORM_EDGE", (HW + 0.35, dy, -0.01), (0.3, 16.0, 0.02), m_edge, "EXTERIOR"),
             box("PLATFORM_POST", (HW + 2.4, dy + 1.6, 1.6), (0.09, 0.09, 3.2), m_conc, "EXTERIOR")]
    # light ground haze: a low volume box (only the platform lamp lights it)
    haze = box("PLATFORM_HAZE", (HW + 3.0, dy, 0.6), (5.4, 16.0, 1.2), None, "EXTERIOR")
    hm = bpy.data.materials.new("haze"); hm.use_nodes = True
    nt = hm.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Density"].default_value = 0.02
    nt.links.new(vs.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    haze.data.materials.append(hm)
    parts.append(haze)
    for p in parts:
        p.parent = rig


def _window_chase(D):
    """Passing tunnel lights: emissive bands outside the side windows, visible only to camera and
    glossy/transmission rays, so they show in the glass and never light anything (DP: light-linked strips)."""
    S = D["set"]
    L, HW = S["length"], S["half_width"]
    for s, side in ((-1, "A"), (1, "B")):
        mat = bpy.data.materials.new(f"window_chase_{side}")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission"); em.name = "EMIT"
        em.inputs["Color"].default_value = (0.75, 0.85, 1.0, 1)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping"); mp.name = "SCROLL"
        wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = "BANDS"; wave.bands_direction = "Y"
        wave.inputs["Scale"].default_value = 0.08
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.93
        ramp.color_ramp.elements[1].position = 0.97
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.name = "LEVEL"; mul.inputs[1].default_value = 0.0
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
        nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], mul.inputs[0])
        nt.links.new(mul.outputs[0], em.inputs["Strength"])
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        ob = plane(f"WINDOW_CHASE_{side}", (s * (HW + 1.2), L / 2, 1.4), (L + 40, 1.6), mat, "EXTERIOR",
                   normal="-X" if s > 0 else "X")
        for attr in ("visible_diffuse", "visible_shadow", "visible_volume_scatter"):
            setattr(ob, attr, False)
