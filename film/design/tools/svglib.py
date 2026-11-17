"""Shared drawing helpers for THE QUIET CAR design sheets.

Everything is generated: run `python3 film/design/tools/build.py` to rebuild every SVG.
Coordinates: figures are built in "head units" (u) relative to the top-centre of the head,
then transformed for front (turn=0) or three-quarter (turn=1) views.
"""
from xml.sax.saxutils import escape

THE_RED = "#C8102E"

# ---------------------------------------------------------------- paths


def smooth(pts, closed=True, tension=0.5):
    """Catmull-Rom spline through pts -> SVG path data."""
    if len(pts) < 3:
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + (" Z" if closed else "")
    n = len(pts)
    d = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[(i + 1) % n]
        k = tension / 3 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        d.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    if closed:
        d.append("Z")
    return " ".join(d)


def poly(pts, closed=True):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + (" Z" if closed else "")


def mirror(right):
    """Right-side outline (top->bottom, x>=0) -> full closed outline."""
    left = [(-x, y) for x, y in reversed(right)]
    return right + left


# ---------------------------------------------------------------- view transform


class View:
    """Maps head-unit coords to page px for a given view.

    turn=0: front. turn=1: three-quarter, figure turned to camera-left
    (camera-left side compressed, centre line shifted left).
    """

    def __init__(self, cx, top, u, turn=0.0):
        self.cx, self.top, self.u, self.turn = cx, top, u, turn

    def x(self, x, depth=1.0):
        t = self.turn
        if x < 0:
            x = x * (1 - 0.34 * t)
        else:
            x = x * (1 - 0.04 * t)
        return self.cx + (x - 0.10 * t * depth) * self.u

    def p(self, x, y, depth=1.0):
        return (self.x(x, depth), self.top + y * self.u)

    def pts(self, pts, depth=1.0):
        return [self.p(x, y, depth) for x, y in pts]


# ---------------------------------------------------------------- svg document


class Doc:
    def __init__(self, w, h, bg="#ECEAE4"):
        self.w, self.h, self.bg = w, h, bg
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def path(self, d, fill="none", stroke=None, sw=1, op=1.0, extra=""):
        st = f' stroke="{stroke}" stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round"' if stroke else ""
        o = f' opacity="{op:.2f}"' if op < 1 else ""
        self.add(f'<path d="{d}" fill="{fill}"{st}{o} {extra}/>')

    def text(self, x, y, s, size=14, fill="#2A2A2A", weight="normal", anchor="start", family="Helvetica, Arial, sans-serif", style=""):
        self.add(
            f'<text xml:space="preserve" x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {style}>{escape(s)}</text>'
        )

    def lines(self, x, y, rows, size=14, lh=1.35, **kw):
        for i, r in enumerate(rows):
            self.text(x, y + i * size * lh, r, size=size, **kw)
        return y + len(rows) * size * lh

    def rect(self, x, y, w, h, fill, stroke=None, sw=1, rx=0, op=1.0):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        o = f' opacity="{op}"' if op < 1 else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"{st}{o}/>')

    def circle(self, x, y, r, fill, stroke=None, sw=1, op=1.0):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        o = f' opacity="{op}"' if op < 1 else ""
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"{st}{o}/>')

    def group(self, inner, attrs=""):
        self.add(f"<g {attrs}>")
        self.parts.extend(inner)
        self.add("</g>")

    def svg(self, title=""):
        defs = DEFS
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">\n'
            f"<title>{escape(title)}</title>\n{defs}\n"
            f'<rect width="{self.w}" height="{self.h}" fill="{self.bg}"/>\n' + "\n".join(self.parts) + "\n</svg>\n"
        )


class Layer(Doc):
    """Collects primitives without a document wrapper (for grouping under a filter)."""

    def __init__(self):
        self.parts = []


DEFS = """<defs>
  <!-- Painterly treatment for the design sheets: edges broken by a fixed noise displacement,
       plus stroke-shaped value variation multiplied into the fill. Fixed seeds: nothing boils. -->
  <filter id="paint" x="-4%" y="-4%" width="108%" height="108%" color-interpolation-filters="sRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.022 0.06" numOctaves="2" seed="4" result="warp"/>
    <feDisplacementMap in="SourceGraphic" in2="warp" scale="4" xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.09 0.025" numOctaves="3" seed="11" result="n"/>
    <feColorMatrix in="n" type="matrix" values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 0 1" result="g"/>
    <feComposite in="d" in2="g" operator="arithmetic" k1="0.34" k2="0.84" k3="0" k4="0" result="t"/>
    <feComposite in="t" in2="d" operator="in"/>
  </filter>
  <filter id="paintFine" x="-4%" y="-4%" width="108%" height="108%" color-interpolation-filters="sRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.05 0.12" numOctaves="2" seed="5" result="warp"/>
    <feDisplacementMap in="SourceGraphic" in2="warp" scale="1.6" xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.16 0.05" numOctaves="2" seed="13" result="n"/>
    <feColorMatrix in="n" type="matrix" values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 0 1" result="g"/>
    <feComposite in="d" in2="g" operator="arithmetic" k1="0.14" k2="0.94" k3="0" k4="0" result="t"/>
    <feComposite in="t" in2="d" operator="in"/>
  </filter>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.2"/></filter>
  <filter id="softer" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="10"/></filter>
  <filter id="grey"><feColorMatrix type="saturate" values="0"/></filter>
</defs>"""


def swatch(doc, x, y, hexv, name, note="", w=34, h=24):
    doc.rect(x, y, w, h, hexv, stroke="#00000033", sw=1)
    doc.text(x + w + 10, y + 11, name, size=14, weight="bold")
    doc.text(x + w + 10, y + 26, f"{hexv}  {note}", size=12, fill="#555")
