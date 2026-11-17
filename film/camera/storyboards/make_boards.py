#!/usr/bin/env python3
"""Storyboard generator for THE QUIET CAR (DP, Milestone 3).

The perspective frames (Pos A, the Meter, and Pos B, Noor's end) are drawn from the
real set geometry in camera/lighting-plan.md: 12 panels about 1.08 m apart along a
13 m seating section, 2.8 m wide and 2.3 m high, plus a 4 m unlit vestibule. They are
projected through a 32 mm lens on a Super 35 sensor cropped to 2.39:1. Each frame's
panel states come straight from the lighting-plan cue list, so the boards show what the
cue stack actually does.

Run: python3 make_boards.py    (writes NN-*.svg next to this file; no dependencies)
"""
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))
W, H, BAND = 956, 400, 44          # 2.39:1 image plus a caption band
CX, CY = W / 2, H / 2

# ---- set geometry (metres) -------------------------------------------------------
LEN = 13.0                          # seating section, z = 0 (end B) .. 13 (end A, Noor)
HALF = 1.4                          # half width
CEIL = 2.3
N = 12
SPACING = LEN / N
def pz(i):                          # panel i (1..12) centre; P1 at end A, P12 at end B
    return LEN - (i - 0.5) * SPACING

# ---- colour ----------------------------------------------------------------------
COOL = (226, 236, 226)              # 4300 K plus a touch of green
SODIUM = (255, 146, 58)             # 2200 K brownout
PLATFORM = (214, 232, 236)          # cold mercury-vapour white
def mix(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)
def hexc(c):
    return "#%02x%02x%02x" % c
def tint(base, light, level):
    """Surface colour = surface albedo x light colour x level (level 0..1.1)."""
    return hexc(tuple(max(0, min(255, int(b * l / 255 * min(level, 1.1)))) for b, l in zip(base, light)))

WALL, FLOOR, CEILC, SEAT = (205, 208, 200), (120, 122, 118), (180, 182, 178), (60, 128, 124)
SKIN, NOOR_SUIT, BEA_C, WALT_C, KAI_C = (190, 150, 125), (58, 60, 66), (40, 52, 92), (150, 118, 80), (118, 118, 122)

# ---- camera ----------------------------------------------------------------------
class Cam:
    def __init__(self, x, y, z, f=1229.0, look=+1):
        self.x, self.y, self.z, self.f, self.look = x, y, z, f, look
    def p(self, X, Y, Z):
        d = (Z - self.z) * self.look
        if d < 0.05:
            d = 0.05
        sx = (X - self.x) * self.look
        return (CX + self.f * sx / d, CY - self.f * (Y - self.y) / d)
    def depth(self, Z):
        return (Z - self.z) * self.look

def poly(pts, fill, extra=""):
    return '<polygon points="%s" fill="%s" %s/>' % (" ".join("%.1f,%.1f" % q for q in pts), fill, extra)

def scene(cam, levels, light=COOL, figures=(), phone_glow=None, display="NEXT STOP: HOLLOWAY",
          display_on=True, extras=""):
    """Render the carriage. levels: dict panel -> 0..1.1. figures: (name, x, z, seated)."""
    out = ['<rect width="%d" height="%d" fill="#000"/>' % (W, H)]
    # sections, far to near (painter's algorithm)
    order = sorted(range(1, N + 1), key=lambda i: -cam.depth(pz(i)))
    for i in order:
        z0, z1 = pz(i) - SPACING / 2, pz(i) + SPACING / 2
        L = levels.get(i, 0)
        # spill: a dark section gets a trace from lit neighbours (−4 stops), so the edge reads hard
        spill = max(levels.get(i - 1, 0), levels.get(i + 1, 0)) * 0.06 if L == 0 else 0
        k = L if L > 0 else spill
        col = light if L > 0 or spill > 0 else COOL
        fl = tint(FLOOR, col, k); wl = tint(WALL, col, k * 0.9); ce = tint(CEILC, col, k * 0.75)
        out.append(poly([cam.p(-HALF, 0, z0), cam.p(HALF, 0, z0), cam.p(HALF, 0, z1), cam.p(-HALF, 0, z1)], fl))
        out.append(poly([cam.p(-HALF, CEIL, z0), cam.p(HALF, CEIL, z0), cam.p(HALF, CEIL, z1), cam.p(-HALF, CEIL, z1)], ce))
        for sx in (-HALF, HALF):
            out.append(poly([cam.p(sx, 0, z0), cam.p(sx, CEIL, z0), cam.p(sx, CEIL, z1), cam.p(sx, 0, z1)], wl))
            # black window, with the panel's reflection
            out.append(poly([cam.p(sx, 0.95, z0 + 0.12), cam.p(sx, 1.85, z0 + 0.12),
                             cam.p(sx, 1.85, z1 - 0.12), cam.p(sx, 0.95, z1 - 0.12)], "#050607"))
            if L > 0:
                rz = pz(i)
                out.append(poly([cam.p(sx, 1.70, rz - 0.22), cam.p(sx, 1.76, rz - 0.22),
                                 cam.p(sx, 1.76, rz + 0.22), cam.p(sx, 1.70, rz + 0.22)],
                                tint((255, 255, 255), col, L * 0.45)))
        # benches (not at Noor's bay, which has the transverse seat)
        if i != 1:
            sc = tint(SEAT, col, k)
            for sx, inner in ((-HALF, -HALF + 0.5), (HALF, HALF - 0.5)):
                out.append(poly([cam.p(sx, 0.46, z0 + 0.04), cam.p(inner, 0.46, z0 + 0.04),
                                 cam.p(inner, 0.46, z1 - 0.04), cam.p(sx, 0.46, z1 - 0.04)], sc))
                out.append(poly([cam.p(inner, 0, z0 + 0.04), cam.p(inner, 0.46, z0 + 0.04),
                                 cam.p(inner, 0.46, z1 - 0.04), cam.p(inner, 0, z1 - 0.04)], tint(SEAT, col, k * 0.7)))
        # the panel itself
        pc = tint((255, 255, 255), col, 0.18 + 0.92 * L) if L > 0 else "#101112"
        out.append(poly([cam.p(-0.32, CEIL - 0.01, pz(i) - 0.3), cam.p(0.32, CEIL - 0.01, pz(i) - 0.3),
                         cam.p(0.32, CEIL - 0.01, pz(i) + 0.3), cam.p(-0.32, CEIL - 0.01, pz(i) + 0.3)], pc,
                        'stroke="#2a2b2c" stroke-width="0.6"'))
    # doors: side B between P6 and P7
    dz0, dz1 = pz(7) - 0.55, pz(6) + 0.55
    dl = max(levels.get(6, 0), levels.get(7, 0))
    out.append(poly([cam.p(HALF - 0.001, 0, dz0), cam.p(HALF - 0.001, 2.05, dz0),
                     cam.p(HALF - 0.001, 2.05, dz1), cam.p(HALF - 0.001, 0, dz1)], tint((150, 152, 150), light, dl),
                    'stroke="#000" stroke-width="1"'))
    for a, b in ((dz0 + 0.12, (dz0 + dz1) / 2 - 0.05), ((dz0 + dz1) / 2 + 0.05, dz1 - 0.12)):
        out.append(poly([cam.p(HALF - 0.002, 1.0, a), cam.p(HALF - 0.002, 1.9, a),
                         cam.p(HALF - 0.002, 1.9, b), cam.p(HALF - 0.002, 1.0, b)], "#040506"))
    # end wall A, with the sign and the display
    if cam.look == +1:
        ea = max(levels.get(1, 0), 0.04)
        out.append(poly([cam.p(-HALF, 0, LEN), cam.p(HALF, 0, LEN), cam.p(HALF, CEIL, LEN), cam.p(-HALF, CEIL, LEN)],
                        tint(WALL, light, ea * 0.85)))
        sx0, sy0 = cam.p(-0.55, 2.2, LEN); sx1, sy1 = cam.p(0.55, 1.95, LEN)
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (sx0, sy0, sx1 - sx0, sy1 - sy0, tint((40, 70, 120), light, ea)))
        fs = max(3.0, (sy1 - sy0) * 0.7)
        out.append('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s" text-anchor="middle" font-family="Helvetica,Arial" font-weight="bold">QUIET CAR</text>'
                   % ((sx0 + sx1) / 2, sy1 - (sy1 - sy0) * 0.22, fs, tint((255, 255, 255), light, ea)))
        dx0, dy0 = cam.p(-0.7, 1.9, LEN); dx1, dy1 = cam.p(0.7, 1.74, LEN)
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#08090a"/>' % (dx0, dy0, dx1 - dx0, dy1 - dy0))
        if display_on:
            out.append('<text x="%.1f" y="%.1f" font-size="%.1f" fill="#e8f4ea" text-anchor="middle" font-family="Courier New,monospace">%s</text>'
                       % ((dx0 + dx1) / 2, dy1 - (dy1 - dy0) * 0.25, max(2.5, (dy1 - dy0) * 0.62), display))
    else:
        ez = 0.0
        eb = max(levels.get(12, 0), 0.04)
        out.append(poly([cam.p(-HALF, 0, ez), cam.p(HALF, 0, ez), cam.p(HALF, CEIL, ez), cam.p(-HALF, CEIL, ez)], tint(WALL, light, eb * 0.8)))
        gx0, gy0 = cam.p(-0.45, 1.95, ez); gx1, gy1 = cam.p(0.45, 0, ez)
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#050505"/>' % (gx0, gy0, gx1 - gx0, gy1 - gy0))
    # figures, far to near
    for f in sorted(figures, key=lambda f: -cam.depth(f[2])):
        out.append(figure(cam, f, levels, light))
    if phone_glow is not None:
        gx, gz, gl = phone_glow
        x, y = cam.p(gx, 0.48, gz)
        r = max(3, 900 / max(cam.depth(gz), 0.5) * 0.08)
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="url(#phone)" opacity="%.2f"/>' % (x, y, r * 3, gl))
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#cfe3ff"/>' % (x - r * 0.35, y - r * 0.22, r * 0.7, r * 0.44))
    out.append(extras)
    return "\n".join(out)

def panel_at(z):
    return max(1, min(N, int((LEN - z) / SPACING) + 1))

def figure(cam, f, levels, light):
    name, x, z, seated = f
    L = levels.get(panel_at(z), 0)
    edge = max(levels.get(panel_at(z) - 1, 0), levels.get(panel_at(z) + 1, 0)) * 0.12 if L == 0 else 0
    k = max(L, edge)
    body = {"NOOR": NOOR_SUIT, "BEA": BEA_C, "WALTER": WALT_C, "KAI": KAI_C}[name]
    hy = 1.22 if seated else 1.62
    by0 = 0.46 if seated else 0.0
    w = 0.22
    pts = [cam.p(x - w, by0, z), cam.p(x - w, hy - 0.16, z), cam.p(x + w, hy - 0.16, z), cam.p(x + w, by0, z)]
    s = poly(pts, tint(body, light, max(k, 0.03)))
    hx, hyy = cam.p(x, hy, z)
    r = cam.f * 0.105 / max(cam.depth(z), 0.3)
    s += '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (hx, hyy, r, tint(SKIN, light, max(k, 0.03)))
    if name == "NOOR" and k > 0.3:                      # the red lanyard
        lx, ly = cam.p(x, hy - 0.3, z)
        s += '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#c8102e"/>' % (lx, ly, max(0.8, r * 0.28))
    if name == "WALTER":                                 # the newspaper
        nx0, ny0 = cam.p(x + 0.05, 0.95, z - 0.18); nx1, ny1 = cam.p(x + 0.35, 0.65, z - 0.18)
        s += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (min(nx0, nx1), ny0, abs(nx1 - nx0) + 1, ny1 - ny0, tint((228, 224, 210), light, max(k, 0.03)))
    return s

DEFS = """<defs>
<radialGradient id="phone"><stop offset="0" stop-color="#9cc4ff" stop-opacity="0.9"/><stop offset="1" stop-color="#9cc4ff" stop-opacity="0"/></radialGradient>
<radialGradient id="phoneface" cx="0.5" cy="1" r="0.9"><stop offset="0" stop-color="#a9cbff" stop-opacity="0.75"/><stop offset="1" stop-color="#a9cbff" stop-opacity="0"/></radialGradient>
<linearGradient id="topdown" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<radialGradient id="lamp" cx="0.5" cy="0" r="1"><stop offset="0" stop-color="#e6f6f8" stop-opacity="0.95"/><stop offset="0.6" stop-color="#9fb8bd" stop-opacity="0.25"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
</defs>"""

def write(num, slug, body, caption):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">\n%s\n'
           '<g>%s</g>\n<rect y="%d" width="%d" height="%d" fill="#111"/>\n'
           '<text x="12" y="%d" font-family="Helvetica,Arial" font-size="15" fill="#ddd">%s</text>\n</svg>\n'
           % (W, H + BAND, W, H + BAND, DEFS, body, H, W, BAND, H + 28, caption))
    with open(os.path.join(OUT, "%02d-%s.svg" % (num, slug)), "w") as fh:
        fh.write(svg)

# ---- cameras ---------------------------------------------------------------------
A = Cam(0.0, 1.65, -3.5)                       # the Meter: vestibule, standing height, 32 mm
A_IN = Cam(0.0, 1.65, 1.0)                     # the Meter after the creep push
B = Cam(0.55, 1.0, LEN - 0.15, look=-1)       # Noor's end, side B corner, low, looking down the car

ALL = {i: 1.0 for i in range(1, N + 1)}
NOOR = ("NOOR", 0.0, 12.75, True)
WALT = ("WALTER", -1.0, pz(3), True)
BEA = ("BEA", 1.0, pz(3), True)
KAI = ("KAI", 1.05, pz(8), True)
KAI_PHONE = (1.05, pz(8))
CAST = [NOOR, WALT, BEA, KAI]

def lit(*ps, level=1.0):
    return {i: level for i in ps}

# ---- 2D helpers for the closer frames --------------------------------------------
def ceiling_strip(panels, light=COOL, y=0, h=70):
    """panels: list of (x_centre, width, level) along a low-angle ceiling band at the top of frame."""
    s = ['<rect y="%d" width="%d" height="%d" fill="%s"/>' % (y, W, h, tint(CEILC, light, max([p[2] for p in panels] + [0.05]) * 0.7))]
    for xc, wd, L in panels:
        col = tint((255, 255, 255), light, 0.18 + 0.92 * L) if L > 0 else "#0e0f10"
        s.append('<rect x="%.0f" y="%d" width="%.0f" height="%d" rx="3" fill="%s" stroke="#333" stroke-width="1"/>' % (xc - wd / 2, y + 12, wd, h - 30, col))
    return "\n".join(s)

def person(cx, base, scale, body, k, light=COOL, red=False, face_k=None):
    fk = k if face_k is None else face_k
    s = '<path d="M%.0f %.0f Q%.0f %.0f %.0f %.0f L%.0f %.0f Q%.0f %.0f %.0f %.0f Z" fill="%s"/>' % (
        cx - 150 * scale, base, cx - 140 * scale, base - 150 * scale, cx - 60 * scale, base - 165 * scale,
        cx + 60 * scale, base - 165 * scale, cx + 140 * scale, base - 150 * scale, cx + 150 * scale, base, tint(body, light, max(k, 0.03)))
    s += '<ellipse cx="%.0f" cy="%.0f" rx="%.0f" ry="%.0f" fill="%s"/>' % (cx, base - 250 * scale, 62 * scale, 80 * scale, tint(SKIN, light, max(fk, 0.03)))
    if red:
        s += '<path d="M%.0f %.0f L%.0f %.0f L%.0f %.0f" stroke="#c8102e" stroke-width="%.1f" fill="none"/>' % (
            cx - 45 * scale, base - 168 * scale, cx, base - 70 * scale, cx + 45 * scale, base - 168 * scale, 7 * scale)
        s += '<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" fill="%s" stroke="#999"/>' % (cx - 20 * scale, base - 75 * scale, 40 * scale, 52 * scale, tint((235, 238, 240), light, max(k, 0.05)))
    return s

def bg(light, k, top=(205, 208, 200)):
    return '<rect width="%d" height="%d" fill="%s"/>' % (W, H, tint(top, light, k))

# ---- the boards ------------------------------------------------------------------
def boards():
    # 00 floor plan
    sx, sy, sc = 70, 70, 50          # metres to px
    def X(z):                        # plan: end A on the left
        return sx + (LEN - z) * sc
    p = ['<rect width="%d" height="%d" fill="#15171a"/>' % (W, H)]
    p.append('<rect x="%.0f" y="%d" width="%.0f" height="%.0f" fill="#e9ece6" stroke="#888"/>' % (X(LEN), sy, LEN * sc, 2 * HALF * sc))
    p.append('<rect x="%.0f" y="%d" width="%.0f" height="%.0f" fill="#2a2d31" stroke="#666" stroke-dasharray="4 3"/>' % (X(0), sy, 4 * sc, 2 * HALF * sc))
    p.append('<text x="%.0f" y="%d" font-size="12" fill="#aaa" font-family="Helvetica">unlit vestibule</text>' % (X(0) + 18, sy + 85))
    for i in range(1, N + 1):
        p.append('<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" fill="#fff8c8" stroke="#b9a54a"/>' % (X(pz(i)) - 14, sy + HALF * sc - 10, 28, 20))
        p.append('<text x="%.0f" y="%.0f" font-size="12" text-anchor="middle" fill="#ddd" font-family="Helvetica">P%d</text>' % (X(pz(i)), sy + 2 * HALF * sc + 46, i))
    p.append('<rect x="%.0f" y="%.0f" width="%.0f" height="14" fill="%s"/>' % (X(LEN - 1.1), sy + 2 * HALF * sc - 14, (LEN - 1.1) * sc, hexc(SEAT)))
    p.append('<rect x="%.0f" y="%d" width="%.0f" height="14" fill="%s"/>' % (X(LEN - 1.1), sy, (LEN - 1.1) * sc, hexc(SEAT)))
    dz0, dz1 = pz(7) - 0.55, pz(6) + 0.55
    p.append('<rect x="%.0f" y="%.0f" width="%.0f" height="10" fill="#ff5a36"/>' % (X(dz1), sy + 2 * HALF * sc - 2, (dz1 - dz0) * sc))
    p.append('<text x="%.0f" y="%.0f" font-size="12" fill="#ff8a6a" text-anchor="middle" font-family="Helvetica">DOORS → platform</text>' % (X((dz0 + dz1) / 2), sy + 2 * HALF * sc + 24))
    def dot(z, x, label, c):
        yy = sy + (HALF - x) * sc
        p.append('<circle cx="%.0f" cy="%.0f" r="9" fill="%s"/><text x="%.0f" y="%.0f" font-size="12" fill="#111" text-anchor="middle" font-family="Helvetica" font-weight="bold">%s</text>' % (X(z), yy, c, X(z) - (22 if label == "WALTER" else 0), yy - 13, label))
    dot(12.6, 0, "NOOR", "#c8102e"); dot(pz(3), 0.9, "WALTER", hexc(WALT_C)); dot(pz(3), -1.0, "BEA", hexc(BEA_C)); dot(pz(8), -1.05, "KAI", hexc(KAI_C))
    def cam(z, x, label, ang, dx=6, dy=24):
        yy = sy + (HALF - x) * sc
        p.append('<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f" fill="#4fc3f7" transform="rotate(%d %.0f %.0f)"/>' % (X(z), yy, X(z) + 18, yy - 9, X(z) + 18, yy + 9, ang, X(z), yy))
        p.append('<text x="%.0f" y="%.0f" font-size="13" fill="#4fc3f7" font-family="Helvetica" font-weight="bold">%s</text>' % (X(z) + dx, yy + dy, label))
    cam(-3.5, 0, "A", 0); cam(LEN - 0.15, -0.75, "B", 180); cam(9.6, 1.2, "C", 180, 4, 26); cam(9.6, -1.2, "D", 180, 4, 30)
    cam(LEN - 0.3, 1.2, "E", 180, -4, 26); cam(pz(8), 1.25, "F", 270); cam((dz0 + dz1) / 2, 1.25, "G", 270)
    p.append('<text x="%.0f" y="%d" font-size="13" fill="#ccc" font-family="Helvetica">END WALL A: QUIET CAR sign + display</text>' % (X(LEN), sy - 14))
    p.append('<text x="%.0f" y="%d" font-size="13" fill="#ccc" font-family="Helvetica">END WALL B / gangway</text>' % (X(0) - 10, sy - 14))
    p.append('<text x="40" y="%d" font-size="12" fill="#999" font-family="Helvetica">side A (top) · side B (bottom) · 1 square ≈ 1.08 m · 13 m seating + 4 m vestibule</text>' % (H - 22))
    write(0, "set-plan", "\n".join(p), "00 · Set plan · panels P1–P12 · camera positions A–G (see lighting-plan.md §1)")

    write(1, "opening-meter", scene(A, ALL, figures=CAST),
          "01 · Shot 1 · Pos A, the Meter · 32 mm, vestibule, 1.65 m · asleep: all 12 panels lit · count them")

    # 02 lanyard tick: MCU, ceiling out
    b = bg(COOL, 0.85) + person(CX, H + 60, 1.25, NOOR_SUIT, 0.95, red=True)
    b += '<rect x="%d" y="%d" width="90" height="26" fill="#fff" opacity="0.18"/>' % (CX - 45, H - 120)
    b += '<text x="20" y="34" font-family="Helvetica" font-size="15" fill="#333">cue 0: the badge laminate and her hair blink for 2 frames, nothing else</text>'
    write(2, "lanyard-tick", b, "02 · Shot 2 · Pos C · 50 mm MCU · ceiling OUT (asleep) · cue 0, the subliminal tick")

    # 03 lie 2: low 40 with P1 and P2 in frame, both dipped
    b = bg(COOL, 0.6) + ceiling_strip([(CX - 260, 200, 0.12), (CX + 40, 170, 0.12)], h=90)
    b += '<text x="%d" y="122" font-family="Helvetica" font-size="13" fill="#444">P2</text><text x="%d" y="122" font-family="Helvetica" font-size="13" fill="#444">P1</text>' % (CX - 270, CX + 30)
    b += person(CX + 40, H + 40, 1.05, NOOR_SUIT, 0.55, red=True)
    write(3, "lie-two", b, "03 · Shot 9 · Pos C · 40 mm low · \"The Henley account. Again.\" · cue 2: TWO panels in frame, both dipped")

    write(4, "brownout", scene(A, {i: 0.32 for i in ALL}, light=SODIUM, figures=CAST),
          "04 · Shot 16 · Pos A · 32 mm · \"I'm at the library, Mum.\" · cue 3: every panel sags warm and HOLDS")
    write(5, "blackout", '<rect width="%d" height="%d" fill="#000"/>' % (W, H),
          "05 · Shot 18 · Pos A · cue 4: true black, every pixel 0 · digital zero on the soundtrack · held ~3 s")
    write(6, "lights-up-empty-seat", scene(A, ALL, figures=[NOOR, WALT, BEA], phone_glow=(1.05, pz(8), 0.9)),
          "06 · Shot 18 (no cut through the black) · Pos A · cue 4.up: snap up · Kai's seat empty, his phone glowing")

    # 07 newspaper
    b = bg((220, 220, 210), 0.5)
    b += '<rect x="170" y="40" width="620" height="330" fill="#e9e5d6" transform="rotate(-3 480 200)"/>'
    for yy in range(70, 360, 16):
        b += '<line x1="200" y1="%d" x2="440" y2="%d" stroke="#b8b4a6" stroke-width="5" transform="rotate(-3 480 200)"/>' % (yy, yy)
    b += '<text x="470" y="150" font-family="Comic Sans MS,Marker Felt,cursive" font-size="34" fill="#15151a" transform="rotate(-3 480 200)">DON\'T LIE</text>'
    b += '<text x="470" y="195" font-family="Comic Sans MS,Marker Felt,cursive" font-size="34" fill="#15151a" transform="rotate(-3 480 200)">IN HERE.</text>'
    b += '<text x="462" y="262" font-family="Georgia,serif" font-style="italic" font-size="24" fill="#1d2a4a" transform="rotate(-3 480 200)">IT\'S AWAKE NOW.</text>'
    b += '<text x="462" y="296" font-family="Georgia,serif" font-style="italic" font-size="24" fill="#1d2a4a" transform="rotate(-3 480 200)">YOU WOKE IT.</text>'
    write(7, "newspaper", b, "07 · Shot 23 · insert · 50 mm · two hands: Walter's block capitals, Bea's tidy nurse's script")

    # 08 hard dip: Noor standing under P4, Walter seated, P3 P4 P5 in frame
    b = bg(COOL, 0.42) + ceiling_strip([(CX - 330, 150, 0.4), (CX, 170, 0.05), (CX + 330, 150, 0.4)], h=80)
    for xx, lab in ((CX - 340, "P4"), (CX - 10, "P3"), (CX + 320, "P2")):
        b += '<text x="%d" y="110" font-family="Helvetica" font-size="13" fill="#555">%s</text>' % (xx, lab)
    b += person(CX - 60, H + 30, 0.95, NOOR_SUIT, 0.3, red=True)
    b += person(CX + 250, H + 90, 0.8, WALT_C, 0.35)
    b += '<path d="M%d %d Q%d %d %d %d" stroke="%s" stroke-width="22" fill="none" stroke-linecap="round"/>' % (CX + 170, H - 70, CX + 90, H - 120, CX + 20, H - 140, tint(WALT_C, COOL, 0.35))
    write(8, "hard-dip", b, "08 · Shot 26 · Pos E · 40 mm · \"My name is S—\" · Walter clamps her wrist · cue 5: P3 near black, P2 and P4 dip")

    # 09 thumb over the red button
    b = bg(COOL, 0.35)
    b += '<rect x="330" y="70" width="300" height="300" rx="34" fill="#0b0c0e"/>'
    b += '<rect x="346" y="88" width="268" height="262" rx="22" fill="#d9e6f5"/>'
    b += '<text x="480" y="150" font-family="Helvetica" font-size="30" fill="#223" text-anchor="middle">Mum</text>'
    b += '<text x="480" y="186" font-family="Helvetica" font-size="18" fill="#556" text-anchor="middle">12:04</text>'
    b += '<circle cx="480" cy="290" r="38" fill="#e0242f"/><rect x="458" y="284" width="44" height="12" rx="6" fill="#fff"/>'
    b += '<path d="M640 400 Q600 300 520 268 Q492 258 488 280 Q500 320 560 400 Z" fill="%s"/>' % tint(SKIN, COOL, 0.6)
    b += '<rect width="%d" height="%d" fill="url(#phoneface)"/>' % (W, H)
    write(9, "end-call", b, "09 · Shot 32 · Pos F · 40 mm · her thumb over the red end-call button · she can't do it · the red must read")

    # 10 creep: after 7.7, mid-push
    write(10, "creep-dolly", scene(Cam(0.0, 1.65, -1.0), lit(*range(1, 10)), figures=CAST),
          "10 · Shot 42 · Pos A → A2 push · 32 mm · after cue 7.3: P10–P12 dark · the camera rides in behind the dark edge")
    # 11 reverse from Noor's end, mid-sequence (after 7.5)
    write(11, "dark-toward-camera", scene(B, lit(1, 2, 3, 4, 5, 6, 7), figures=[WALT, BEA, KAI], phone_glow=(1.05, pz(8), 1.0)),
          "11 · Shot 44 · Pos B · 32 mm low · after cue 7.5: the dark comes toward camera · Kai's phone glows in it")
    write(12, "two-left", scene(Cam(0.0, 1.65, -1.0), lit(1, 2), figures=CAST[:3], phone_glow=(1.05, pz(8), 1.0), display="NEXT STOP: HOLLOWAY — 2 MIN"),
          "12 · Shot 50 · Pos A2 · 32 mm · after cue 7.10: TWO panels left · Noor in the last pool · display: 2 MIN")

    # 13 Walter half lit
    b = '<rect width="%d" height="%d" fill="#000"/>' % (W, H)
    b += '<defs><linearGradient id="edge" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0.85"/><stop offset="0.42" stop-color="#fff" stop-opacity="0.35"/><stop offset="0.5" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    b += '<clipPath id="w"><ellipse cx="%d" cy="%d" rx="95" ry="122"/><path d="M%d %d Q%d %d %d %d L%d %d Q%d %d %d %d Z"/></clipPath></defs>' % (
        CX, H - 230, CX - 230, H + 20, CX - 215, H - 110, CX - 90, H - 140, CX + 90, H - 140, CX + 215, H - 110, CX + 230, H + 20)
    b += '<g clip-path="url(#w)"><rect width="%d" height="%d" fill="%s"/><rect width="%d" height="%d" fill="url(#edge)"/></g>' % (W, H, tint(SKIN, COOL, 0.07), W, H)
    b += '<text x="20" y="30" font-family="Helvetica" font-size="14" fill="#777">P2 spill from frame right (Noor\'s side) · the shadow line on his cheek · −3 stops must hold</text>'
    write(13, "walter-edge", b, "13 · Shot 53 · Pos D · 50 mm MCU · \"He's asking.\" · Walter half-lit at the edge of the dark")

    # 14 confession CU
    b = bg(COOL, 0.16)
    b += person(CX, H + 160, 1.9, NOOR_SUIT, 0.3, face_k=0.55)
    b += '<rect width="%d" height="%d" fill="url(#phoneface)" opacity="0.7"/>' % (W, H)
    b += '<rect x="%d" y="0" width="%d" height="%d" fill="url(#topdown)" opacity="0.35"/>' % (CX - 140, 280, H)
    b += '<rect x="%d" y="150" width="70" height="150" rx="12" fill="#0b0c0e"/>' % (CX + 120)
    b += '<text x="20" y="30" font-family="Helvetica" font-size="14" fill="#bbb">75 mm, the only time · each relight down the car adds front light to her face · the push lands before 8.10</text>'
    write(14, "confession-75", b, "14 · Shots 54 / 56 / 58 · Pos C · 75 mm CU, slow push · \"I'm not leaving the office.\" · cues 8.0–8.10")

    write(15, "relight", scene(A, {**lit(*range(2, 11)), 1: 1.1}, figures=[NOOR, WALT, BEA], phone_glow=(1.05, pz(8), 0.7)),
          "15 · Shot 57 · Pos A · 32 mm · cue 8.8: relights running toward us · Kai's empty seat back in the light · P11, P12 still dark")

    # 16 doors / platform, from G
    b = bg(COOL, 0.95, top=(200, 204, 196))
    b += '<rect x="250" y="40" width="460" height="360" fill="#9a9d98"/>'
    b += '<rect x="290" y="60" width="380" height="340" fill="#06080a"/>'
    b += '<ellipse cx="480" cy="70" rx="200" ry="330" fill="url(#lamp)"/>'
    b += '<rect x="290" y="330" width="380" height="70" fill="%s"/>' % tint((120, 124, 122), PLATFORM, 0.7)
    b += '<rect x="455" y="20" width="50" height="16" fill="#e8f6f8"/>'
    b += person(480, 360, 0.62, NOOR_SUIT, 0.85, light=PLATFORM)
    b += '<rect x="500" y="170" width="18" height="34" rx="4" fill="#0b0c0e"/>'
    b += '<rect x="250" y="40" width="40" height="360" fill="#8d908b"/><rect x="670" y="40" width="40" height="360" fill="#8d908b"/>'
    write(16, "platform", b, "16 · Shot 62 · Pos G · 32 mm, locked · doors open · cold-white platform lamp · we stay inside · she slides away in the glass")

    write(17, "innocent-car", scene(A, ALL, figures=[WALT, BEA], phone_glow=(1.05, pz(8), 0.25), display="NOW ARRIVING: HOLLOWAY"),
          "17 · Shot 63 · Pos A · 32 mm · the opening frame again · Walter turns the page · Kai's phone dims · no light change · the car looks innocent")

if __name__ == "__main__":
    boards()
    print("wrote", len([f for f in os.listdir(OUT) if f.endswith('.svg')]), "boards to", OUT)
