"""Redline of the TA's Noor sculpt 01 (cg/stills/sf06_confession_75.png) against the design sheets."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import Doc, Layer  # noqa: E402
from face import draw_face  # noqa: E402

MARK = "#00A6C8"  # review colour (cyan, so no one mistakes a mark for THE RED)
NOTES = [
    (640, 120, "1", "Skin far too light and pink. Target #A9714F (warm mid-brown). Check albedo and the R2 exposure."),
    (600, 175, "2", "Eyes read startled: sclera shows all round. Upper lid edge must cover the top ~20% of the iris at 0.82."),
    (705, 130, "3", "Brows: thin, straight and too high. Groomed arch, thicker inner end, about half an eye-height lower."),
    (650, 225, "4", "Nose: long tube with a ball tip. Shorter wedge that widens to the nostrils."),
    (650, 290, "5", "Mouth OK. Widen it ~10% and soften the lip outline (no hard rim)."),
    (600, 30, "6", "Hair reads as a man's crop. Side parting, swept back over the top of the ears, low bun visible in 3/4."),
    (520, 175, "7", "Ears too big and too proud. Mostly covered by hair."),
    (620, 360, "8", "Neck too thick and exposed. ~0.5 head-width, blouse collar and blazer lapels framing it."),
    (800, 470, "9", "Blazer reads light grey stone/camouflage. Charcoal #3A3B40 with low dab contrast (about 6%)."),
    (600, 140, "10", "Skin dabs blotchy: they read as marks on the skin. Halve the value variation, follow the stroke map."),
]


def build(out):
    d = Doc(1800, 1080)
    d.text(40, 62, "Redline: Noor sculpt 01", size=44, weight="bold", fill="#1E1E1E", family="Georgia, serif")
    d.text(40, 94, "TA's sf06 (C75, 75 mm) against the design sheet and expression neutral. Cyan = review marks.", size=17, fill="#444")
    d.add('<line x1="40" y1="112" x2="1760" y2="112" stroke="#BDB9B0" stroke-width="1"/>')
    # the render, at 1:1 width 1280 -> scale 0.9
    sx = 0.9
    ox, oy = 40, 130
    d.add(f'<image href="../../cg/stills/sf06_confession_75.png" x="{ox}" y="{oy}" width="{1280*sx:.0f}" height="{536*sx:.0f}"/>')
    for x, y, n, _ in NOTES:
        X, Y = ox + x * sx, oy + y * sx
        d.circle(X, Y, 14, MARK, stroke="#fff", sw=2)
        d.text(X, Y + 5, n, size=13, weight="bold", fill="#fff", anchor="middle")
    # target face
    d.rect(1220, 130, 540, 482, "#F6F5F1", stroke="#D3CFC6")
    d.text(1240, 156, "TARGET (sheet neutral, 3/4)", size=13, weight="bold", fill="#777")
    L = Layer()
    draw_face(L, 1490, 175, 260, 340, "noor", {}, turn=0.6)
    d.group(L.parts, 'filter="url(#paintFine)"')
    y = 660
    d.text(40, y, "REDLINES", size=14, weight="bold", fill="#777")
    for i, (_, _, n, t) in enumerate(NOTES):
        col, row = i // 5, i % 5
        X, Y = 40 + col * 870, y + 30 + row * 56
        d.circle(X + 14, Y - 5, 14, MARK)
        d.text(X + 14, Y, n, size=13, weight="bold", fill="#fff", anchor="middle")
        words, line, yy = t.split(), "", Y
        for w in words:
            if len(line) + len(w) > 92:
                d.text(X + 38, yy, line, size=14, fill="#2A2A2A")
                yy += 18
                line = ""
            line += w + " "
        d.text(X + 38, yy, line, size=14, fill="#2A2A2A")
    d.text(40, 1050, "What's right: shallow sockets, glossy cornea with the panel row, pale sclera, low bun idea, squared shoulders, brush-dab scale on the face (~5 mm).",
           size=14, fill="#2A2A2A", weight="bold")
    out("redlines/noor-sculpt-01.svg", d, "Redline Noor sculpt 01")


if __name__ == "__main__":
    from build import out
    build(out)
