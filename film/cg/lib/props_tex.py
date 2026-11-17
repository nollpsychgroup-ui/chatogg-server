"""Textures for Walter's newspaper (design/props/props.md section 2), generated at build time.

- newsprint page: #D9D3C3 paper, masthead THE EVENING LEDGER in black, a headline band and greeked
  columns in low-contrast greys (no colour, no red), so it reads as a newspaper and never competes
  with the handwriting.
- the two margin notes, in blue-black ballpoint #1F2A44, letters ~25 mm tall, written with a small
  single-stroke capital font and two hands:
    WALTER  tall, narrow, careful capitals: upright, even spacing, almost no wobble
    BEA     rounder and quicker: wider letters, corners smoothed, forward slant, baseline drift
  Hand = glyph skeleton + per-hand shape transform + seeded per-letter jitter. Deterministic.

Needs Pillow in the Blender python (pip install pillow).
"""
import math
import os
import random

from PIL import Image, ImageDraw

from .common import CACHE_DIR, pal

PX_PER_M = 2400          # texture density: 0.36 m page side -> 864 px
INK = "#1F2A44"
PAPER = "#D9D3C3"

# single-stroke capitals in a unit box (x 0..1, y 0..1 up). Each glyph: list of polylines.
def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


GLYPHS = {
    "A": [[(0, 0), (0.5, 1), (1, 0)], [(0.22, 0.42), (0.78, 0.42)]],
    "D": [[(0, 0), (0, 1)] + _arc(0.35, 0.5, 0.65, 0.5, 90, -90) + [(0, 0)]],
    "E": [[(1, 1), (0, 1), (0, 0), (1, 0)], [(0, 0.52), (0.75, 0.52)]],
    "H": [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, 0.5), (1, 0.5)]],
    "I": [[(0.5, 0), (0.5, 1)]],
    "K": [[(0, 0), (0, 1)], [(1, 1), (0, 0.42)], [(0.3, 0.6), (1, 0)]],
    "L": [[(0, 1), (0, 0), (0.9, 0)]],
    "N": [[(0, 0), (0, 1), (1, 0), (1, 1)]],
    "O": [_arc(0.5, 0.5, 0.5, 0.5, 90, 450, 20)],
    "R": [[(0, 0), (0, 1)] + _arc(0.42, 0.74, 0.55, 0.26, 90, -90) + [(0, 0.48), (1, 0)]],
    "S": [_arc(0.5, 0.75, 0.48, 0.25, 20, 270, 10) + _arc(0.5, 0.25, 0.48, 0.25, 90, -160, 10)],
    "T": [[(0, 1), (1, 1)], [(0.5, 1), (0.5, 0)]],
    "U": [[(0, 1)] + _arc(0.5, 0.35, 0.5, 0.35, 180, 360) + [(1, 1)]],
    "W": [[(0, 1), (0.25, 0), (0.5, 0.65), (0.75, 0), (1, 1)]],
    "Y": [[(0, 1), (0.5, 0.5), (1, 1)], [(0.5, 0.5), (0.5, 0)]],
    "'": [[(0.5, 1), (0.42, 0.72)]],
    ".": [[(0.5, 0), (0.52, 0.04)]],
    " ": [],
}
NARROW = {"I": 0.15, "'": 0.15, ".": 0.15, " ": 0.45, "W": 1.3}

HANDS = {
    #          width  slant  jitter  drift  smooth  space  stroke(px)
    "WALTER": (0.50, 0.00, 0.020, 0.010, 0, 0.32, 3.0),
    "BEA":    (0.82, 0.22, 0.055, 0.045, 3, 0.20, 3.4),
}


def _chaikin(pts, n):
    for _ in range(n):
        if len(pts) < 3:
            return pts
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1])
        pts = out
    return pts


def handwriting(lines, hand, letter_h_m=0.020, seed=1):
    """RGBA image (ink on transparent) of `lines` in `hand`; returns (image, width_m, height_m)."""
    width, slant, jit, drift, smooth, space, stroke = HANDS[hand]
    rng = random.Random(seed)
    h = letter_h_m * PX_PER_M
    lead = h * 1.6
    pen_lines = []
    max_x = 0.0
    for li, line in enumerate(lines):
        x, base = 0.0, li * lead
        strokes = []
        for ch in line:
            w = NARROW.get(ch, 1.0) * width
            g_h = h * (1 + rng.gauss(0, jit))
            dy = rng.gauss(0, drift) * h
            for poly in GLYPHS[ch]:
                pts = [((px * w + rng.gauss(0, jit * 0.5)) * h, (py + rng.gauss(0, jit * 0.5)) * g_h) for px, py in poly]
                pts = _chaikin(pts, smooth)
                strokes.append([(x + px + py * slant, base - py - dy) for px, py in pts])
            x += (w + space) * h
        max_x = max(max_x, x)
        pen_lines.append(strokes)
    pad = int(h * 0.6)
    W = int(max_x + h * 0.6 + 2 * pad)
    H = int(lead * (len(lines) - 1) + h + 2 * pad)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ink = tuple(int(INK[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    for strokes in pen_lines:
        for s in strokes:
            s = [(pad + px, pad + h + py) for px, py in s]
            if len(s) > 1:
                d.line(s, fill=ink, width=round(stroke), joint="curve")
            for p in (s[0], s[-1]):
                d.ellipse((p[0] - stroke / 2, p[1] - stroke / 2, p[0] + stroke / 2, p[1] + stroke / 2), fill=ink)
    return im, W / PX_PER_M, H / PX_PER_M


def newsprint(w_m=0.36, h_m=0.30, seed=7):
    """The folded broadsheet quarter: masthead, headline band, greeked columns."""
    W, H = int(w_m * PX_PER_M), int(h_m * PX_PER_M)
    rng = random.Random(seed)
    paper = tuple(int(PAPER[i:i + 2], 16) for i in (1, 3, 5))
    im = Image.new("RGB", (W, H), paper)
    d = ImageDraw.Draw(im)
    grey = lambda v: (v, v, v - 4)
    m = int(0.012 * PX_PER_M)
    # masthead (black, as the props sheet says) and rule
    d.rectangle((m, m, W - m, m + int(0.030 * PX_PER_M)), fill=paper)
    for i in range(18):   # blocky greeked masthead letters
        x0 = m + int(i * (W - 2 * m) / 18) + 3
        d.rectangle((x0, m + 6, x0 + int((W - 2 * m) / 18) - 8, m + int(0.022 * PX_PER_M)), fill=grey(72))
    y = m + int(0.034 * PX_PER_M)
    d.line((m, y, W - m, y), fill=grey(70), width=3)
    # headline band
    y += 10
    for k in range(2):
        x = m
        while x < W - m - 40:
            wd = rng.randint(40, 110)
            d.rectangle((x, y, min(W - m, x + wd), y + 18), fill=grey(138))
            x += wd + 16
        y += 34
    y += 8
    # columns of greeked body text, low contrast
    cols = 4
    cw = (W - 2 * m - (cols - 1) * 16) / cols
    for c in range(cols):
        x0 = m + c * (cw + 16)
        yy = y
        while yy < H - m:
            if rng.random() < 0.06:
                yy += 14
                continue
            ln = cw * (rng.uniform(0.55, 1.0) if rng.random() < 0.15 else 1.0)
            d.line((x0, yy, x0 + ln, yy), fill=grey(rng.randint(166, 180)), width=4)
            yy += 11
        if c < cols - 1:
            d.line((x0 + cw + 8, y, x0 + cw + 8, H - m), fill=grey(170), width=1)
    return im


def build_textures():
    out = os.path.join(CACHE_DIR, "props")
    os.makedirs(out, exist_ok=True)
    paths = {}
    p = os.path.join(out, "newsprint.png")
    newsprint().save(p)
    paths["page"] = (p, 0.36, 0.30)
    for key, hand, lines, seed in (("note_walter", "WALTER", ["DON'T LIE IN HERE."], 3),
                                   ("note_bea", "BEA", ["IT'S AWAKE NOW.", "YOU WOKE IT."], 5)):
        im, w, h = handwriting(lines, hand, seed=seed)
        p = os.path.join(out, f"{key}.png")
        im.save(p)
        paths[key] = (p, w, h)
    return paths
