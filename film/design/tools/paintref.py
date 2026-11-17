"""Noor painterly reference for the TA's v2 style frames: stroke direction on the face, how strokes
break at the edges, and how the paint behaves in the darks."""
import math
import random

from svglib import Doc, Layer, smooth, poly
from face import draw_face, FaceView, CHAR

SK = CHAR["noor"]
# value plan for Noor's skin, light -> dark (albedo under the asleep car's top light, for reference only)
LADDER = [
    ("lit plane", "#C08661", "top planes facing the panel: forehead, cheekbone tops, nose ridge, lower lip, chin top"),
    ("halftone", "#A9714F", "her albedo: planes turning away"),
    ("terminator", "#8E5E45", "where strokes break up: 2–3 strokes wide (~1–1.5 cm on her face)"),
    ("core shadow", "#6B5248", "cooler and greyer: grey-green bounce off the teal and laminate, never red"),
    ("shadow in near-dark", "#3B302C", "strokes merge into larger, quieter shapes; chroma drops"),
    ("true black", "#000000", "0,0,0: no texture, no grain, no lift"),
]


def direction(xr, yr):
    """Stroke angle (radians, 0 = horizontal) for a point on Noor's face in head units."""
    s = 1 if xr >= 0 else -1
    if yr < 0.35:  # forehead: across, curving down at the sides
        return 0.55 * xr
    if abs(xr) > 0.38 and yr < 0.68:  # temples / side planes: down the side of the head
        return s * math.radians(78)
    if abs(xr) < 0.075 and 0.4 < yr < 0.74:  # nose ridge: down the nose
        return math.radians(90)
    if 0.38 <= yr < 0.6:  # eye zone: along the lids and the socket
        return 0.35 * xr
    if abs(xr) < 0.2 and 0.72 <= yr < 0.88:  # upper lip and mouth: short vertical-ish
        return math.radians(90) - 0.6 * xr
    if yr >= 0.88:  # chin: around the form
        return -1.3 * xr
    # cheeks: down and in, from cheekbone to mouth corner, turning along the jaw near the edge
    a = math.radians(58) if abs(xr) < 0.33 else math.radians(70)
    return s * a


def value(xr, yr, turn):
    """0 = lit plane .. 4 = shadow in near-dark (top light from the panel above)."""
    v = 1.0
    if yr < 0.3:
        v = 0.2 + 1.2 * max(0.0, abs(xr) - 0.25)
    elif 0.4 < yr < 0.48 and 0.1 < abs(xr) < 0.32:  # brow ridge, shallow socket below
        v = 0.6
    elif 0.48 <= yr < 0.6 and 0.1 < abs(xr) < 0.33:
        v = 1.6
    elif 0.58 <= yr < 0.7 and 0.15 < abs(xr) < 0.38:  # cheekbone tops
        v = 0.5
    elif abs(xr) < 0.07 and 0.45 < yr < 0.7:  # nose ridge
        v = 0.4
    elif 0.73 <= yr < 0.79 and abs(xr) < 0.17:  # under the nose
        v = 2.4
    elif 0.86 <= yr < 0.93 and abs(xr) < 0.16:  # chin top
        v = 0.7
    elif yr >= 0.93:
        v = 3.0
    side = abs(xr) - 0.36
    if side > 0:
        v += side * 9
    if turn > 0.5 and xr < -0.1:  # far side in 3/4 turns from the light
        v += (-0.1 - xr) * 7
    if yr > 0.78 and abs(xr) > 0.25:  # under the jaw
        v += 1.2
    return max(0.0, min(4.2, v))


def lerp_hex(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def colour(v, rnd):
    v = max(0.0, min(4.0, v + rnd.uniform(-0.25, 0.25)))
    i = min(3, int(v))
    c = lerp_hex(LADDER[i][1], LADDER[i + 1][1], v - i)
    return c


def strokes(L, fv, turn, seed=3, step=0.032, show_dir=False):
    rnd = random.Random(seed)
    W = fv.W
    y = -0.05
    while y < 1.02:
        x = -0.56
        while x < 0.56:
            xr, yr = x + rnd.uniform(-0.01, 0.01), y + rnd.uniform(-0.01, 0.01)
            ax = abs(xr)
            hairline = 0.125 + (0.0 if ax < 0.24 else (ax - 0.24) * 0.75) + (0.12 if ax > 0.40 else 0)
            if not show_dir and (yr < hairline or (ax > 0.46 and yr < 0.46)):
                x += step
                continue
            a = direction(xr, yr) + rnd.uniform(-0.12, 0.12)
            v = value(xr, yr, turn)
            # darks merge: strokes get bigger and quieter as the value drops
            k = 1.0 + 0.35 * max(0.0, v - 1.5)
            ln, wd = 0.065 * k, 0.024 * k
            cx, cy = fv.p(xr, yr, True)
            dx, dy = math.cos(a) * ln * W / 2, math.sin(a) * ln * W / 2
            nx, ny = -math.sin(a) * wd * W / 2, math.cos(a) * wd * W / 2
            pts = [(cx - dx, cy - dy), (cx + nx * 0.8, cy + ny * 0.8), (cx + dx, cy + dy), (cx - nx, cy - ny)]
            if show_dir:
                L.path(poly([(cx - dx, cy - dy), (cx + dx, cy + dy)], closed=False), stroke="#1E1E1E", sw=1.3, op=0.55)
            else:
                L.path(smooth(pts, tension=0.6), fill=colour(v, rnd), op=0.92)
            x += step * (1.6 if show_dir else 1.0)
        y += step * (1.6 if show_dir else 1.0) * 0.8


def head_clip(L, fv, cid, feature_holes=True):
    head = SK["head"]
    outline = head + [(-x, y) for x, y in reversed(head)]
    if fv.t > 0.5:
        near = [(x * (1.09 if y < 0.66 else 1.0), y) for x, y in head]
        far = [(-0.12, 0.99), (-0.30, 0.88), (-0.40, 0.72), (-0.47, 0.57), (-0.46, 0.38), (-0.42, 0.17), (-0.30, 0.03)]
        outline = near + far
    d = smooth(fv.pts(outline))
    holes = ""
    if feature_holes:
        for (x, y, rx, ry) in ((0.205, 0.505, 0.15, 0.085), (-0.205, 0.505, 0.15, 0.085), (0, 0.81, 0.21, 0.07),
                               (0.2, 0.41, 0.15, 0.04), (-0.2, 0.41, 0.15, 0.04)):
            cx, cy = fv.p(x, y, True)
            sx = 0.7 if (fv.t > 0.5 and x < 0) else 1.0
            holes += f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx * fv.W * sx:.1f}" ry="{ry * fv.H:.1f}" fill="black" filter="url(#soft)"/>'
    L.add(f'<mask id="{cid}"><path d="{d}" fill="white"/>{holes}</mask>')


def build(out, header):
    d = Doc(1800, 1220)
    header(d, "Noor: painted face reference", "For the TA's v2 style frames: stroke direction on the face, how strokes break at the edges, painted darks. Same rules as style-guide.md sections 3–5.")
    # A. direction map
    d.rect(40, 130, 520, 700, "#F6F5F1", stroke="#D3CFC6")
    d.text(60, 158, "A  STROKE DIRECTION ON THE FACE", size=14, weight="bold", fill="#333")
    L = Layer()
    fv = draw_face(L, 300, 210, 300, 390, "noor", {}, turn=0.0)
    d.group(L.parts, 'filter="url(#paintFine)" opacity="0.55"')
    L = Layer()
    strokes(L, FaceView(300, 210, 300, 390, 0.0), 0.0, show_dir=True)
    head_clip(L, FaceView(300, 210, 300, 390, 0.0), "dirmask", feature_holes=False)
    d.group(L.parts, 'mask="url(#dirmask)"')
    d.lines(60, 640, [
        "Forehead: across, curving down at the temples.",
        "Temples and side planes: down the side of the head.",
        "Eye zone: along the lids and the socket.",
        "Nose: down the ridge. Cheeks: down and in, from the",
        "cheekbone toward the mouth corner, turning along the jaw.",
        "Upper lip: short and near-vertical. Chin: around the form.",
        "Hair: along the sweep, back toward the bun (not strands).",
        "Strokes are locked to the surface (UV/object space).",
    ], size=13.5, fill="#2A2A2A")

    # B. painted study, 3/4
    d.rect(580, 130, 600, 700, "#F6F5F1", stroke="#D3CFC6")
    d.text(600, 158, "B  PAINTED STUDY: 3/4, ASLEEP-CAR TOP LIGHT", size=14, weight="bold", fill="#333")
    L = Layer()
    neck = [(840, 600), (930, 600), (945, 700), (830, 700)]
    L.path(poly(neck), fill="#6B5248")
    L.path(smooth([(720, 760), (820, 690), (960, 690), (1060, 760), (1060, 830), (720, 830)]), fill="#3A3B40")
    L.path(poly([(850, 690), (930, 690), (890, 770)]), fill="#C8CED4")
    for s in (-1, 1):
        L.path(smooth([(890 + s * 38, 688), (890 + s * 26, 740), (890 + s * 8, 800)], closed=False), stroke="#C8102E", sw=8)
    fv = draw_face(L, 880, 200, 310, 405, "noor", {}, turn=1.0)
    d.group(L.parts, 'filter="url(#paintFine)"')
    L = Layer()
    fvs = FaceView(880, 200, 310, 405, 1.0)
    head_clip(L, fvs, "studymask", feature_holes=True)
    strokes(L, fvs, 1.0)
    d.group(L.parts, 'mask="url(#studymask)" filter="url(#paintFine)"')
    d.lines(600, 860 - 30, [], size=13)
    # C. edges
    d.rect(1200, 130, 560, 700, "#F6F5F1", stroke="#D3CFC6")
    d.text(1220, 158, "C  HOW STROKES BREAK AT THE EDGES", size=14, weight="bold", fill="#333")
    rnd = random.Random(9)

    def ball(cx, cy, r, mode):
        d.circle(cx, cy, r + 2, "#1A1A1A") if mode == "lost" else None
        Lb = Layer()
        Lb.add(f'<clipPath id="ball{mode}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
        Lb.add(f'<g clip-path="url(#ball{mode})">')
        Lb.circle(cx, cy, r, "#8E5E45" if mode != "lost" else "#3B302C")
        for i in range(520):
            a = rnd.uniform(0, 2 * math.pi)
            rr = r * math.sqrt(rnd.uniform(0, 1))
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            lit = (cy - y) / r * 0.8 + (cx - x) / r * 0.3  # light from above-left
            if mode == "terminator":
                lit += rnd.uniform(-0.45, 0.45) * (1 - min(1, abs(lit) * 1.5))
            v = 2.0 - lit * 2.2
            if mode == "lost":
                v = max(v, 0) * 1.25
            ang = 0.9 * ((x - cx) / r) * ((y - cy) / r) + rnd.uniform(-0.15, 0.15)
            ln, wd = 15 * (1 + 0.3 * max(0, v - 1.5)), 6
            dx, dy = math.cos(ang) * ln / 2, math.sin(ang) * ln / 2
            nx, ny = -math.sin(ang) * wd / 2, math.cos(ang) * wd / 2
            col = colour(min(4.0, v), rnd) if v < 4.4 else "#000000"
            Lb.path(smooth([(x - dx, y - dy), (x + nx, y + ny), (x + dx, y + dy), (x - nx, y - ny)], tension=0.6), fill=col)
        Lb.add("</g>")
        d.parts.extend(Lb.parts)

    rows = [("firm", 230, "LIT EDGE: firm. Where a form faces the panel, its", "edge against the background stays crisp."),
            ("terminator", 440, "TERMINATOR: light-to-shadow breaks into strokes", "2–3 wide, driven by the real light. It moves when the light moves."),
            ("lost", 650, "SHADOW EDGE: lost. As the form turns away, the", "edge softens and merges with the dark behind it.")]
    for mode, cy, t1, t2 in rows:
        if mode == "lost":
            d.rect(1225, cy - 85, 170, 170, "#141414")
        ball(1310, cy, 75, mode)
        d.text(1410, cy - 10, t1, size=12.5, fill="#2A2A2A")
        d.text(1410, cy + 8, t2, size=12.5, fill="#2A2A2A")
    d.text(1220, 790, "Facial features are always firm; they are the last thing the shadow takes.", size=12.5, fill="#2A2A2A", weight="bold")

    # D. painted darks ladder
    d.text(40, 870, "D  PAINTED DARKS: NOOR'S SKIN FROM LIT PLANE TO TRUE BLACK", size=14, weight="bold", fill="#333")
    x = 40
    for i, (name, hexv, note) in enumerate(LADDER):
        w = 285
        Lb = Layer()
        Lb.add(f'<clipPath id="lad{i}"><rect x="{x}" y="890" width="{w - 10}" height="120"/></clipPath><g clip-path="url(#lad{i})">')
        Lb.rect(x, 890, w - 10, 120, hexv)
        if hexv != "#000000":
            k = 1 + 0.5 * i
            for j in range(int(90 / k)):
                sx, sy = x + rnd.uniform(0, w - 10), 890 + rnd.uniform(0, 120)
                a = rnd.uniform(-0.3, 0.3)
                ln, wd = 30 * k, 10 * k
                dx, dy = math.cos(a) * ln / 2, math.sin(a) * ln / 2
                nx, ny = -math.sin(a) * wd / 2, math.cos(a) * wd / 2
                jit = max(0.0, min(5.0, i + rnd.uniform(-0.3, 0.3) * (1.0 / k)))
                col = colour(min(4.0, jit), rnd)
                Lb.path(smooth([(sx - dx, sy - dy), (sx + nx, sy + ny), (sx + dx, sy + dy), (sx - nx, sy - ny)], tension=0.6), fill=col, op=0.9)
        Lb.add("</g>")
        d.group(Lb.parts, 'filter="url(#paintFine)"' if hexv != "#000000" else "")
        d.text(x, 1032, f"{name}", size=14, weight="bold")
        d.text(x, 1050, hexv, size=12, fill="#555", family="Menlo, monospace")
        words, line, yy = note.split(), "", 1068
        for wds in words:
            if len(line) + len(wds) > 40:
                d.text(x, yy, line, size=12, fill="#444")
                yy += 15
                line = ""
            line += wds + " "
        d.text(x, yy, line, size=12, fill="#444")
        x += w + 5
    d.lines(40, 1135, [
        "These are albedo/value targets for reading, NOT colours to paint into textures: the real light produces them. Two build suggestions for a stronger painted look that stay physically lit:",
        "(1) Planes in the geometry: give the face soft planar facets (forehead, temple, cheek front/side, jaw, nose sides) so the panel light lays down painter's planes by itself.",
        "(2) Darks merge: blend a larger Kuwahara kernel into the low-luminance areas (a luminance mask), so shadows become bigger, quieter shapes while lit features stay crisp. Blackout stays 0.",
    ], size=13, fill="#2A2A2A")
    out("sheets/noor-paint-reference.svg", d, "Noor painted face reference")
