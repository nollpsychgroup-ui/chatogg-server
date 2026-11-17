"""Seated profile silhouettes: how each character reads down the carriage (they sit all film).
Coordinates in metres: x forward (toward the aisle), y up from the floor. Seat cushion top 0.45 m."""
from svglib import Doc, smooth, poly

K = "#141414"

POSES = {
    "noor": dict(title="NOOR: presenting, upright", shapes=[
        ("c", (0.09, 1.21, 0.105)), ("c", (-0.03, 1.17, 0.045)),
        ("p", [(0.04, 1.11), (0.12, 1.11), (0.13, 1.05)] + [(0.17, 1.03), (0.16, 0.8), (0.15, 0.52), (-0.03, 0.5), (-0.04, 0.8), (-0.03, 1.04), (0.03, 1.06)]),
        ("p", [(-0.03, 0.47), (0.46, 0.49), (0.47, 0.62), (0.0, 0.64)]),
        ("p", [(0.37, 0.6), (0.47, 0.6), (0.46, 0.06), (0.37, 0.06)]),
        ("p", [(0.36, 0.0), (0.58, 0.0), (0.56, 0.07), (0.36, 0.08)]),
        ("p", [(0.02, 1.0), (0.12, 1.0), (0.12, 0.76), (0.32, 0.66), (0.32, 0.6), (0.06, 0.66), (0.02, 0.76)]),
    ]),
    "walter": dict(title="WALTER: folded and still", shapes=[
        ("c", (0.21, 1.17, 0.115)),
        ("p", [(0.10, 1.10), (0.20, 1.08), (0.25, 1.0), (0.24, 0.8), (0.18, 0.52), (-0.05, 0.49), (-0.06, 0.8), (-0.01, 1.04)]),
        ("p", [(-0.05, 0.47), (0.52, 0.53), (0.55, 0.62), (0.40, 0.66), (0.0, 0.64)]),
        ("p", [(0.42, 0.62), (0.56, 0.6), (0.56, 0.25), (0.45, 0.24)]),
        ("p", [(0.45, 0.24), (0.55, 0.24), (0.53, 0.05), (0.46, 0.05)]),
        ("p", [(0.44, 0.0), (0.70, 0.0), (0.68, 0.07), (0.45, 0.08)]),
        ("p", [(0.08, 1.02), (0.2, 1.0), (0.24, 0.8), (0.42, 0.72), (0.40, 0.66), (0.16, 0.74), (0.08, 0.84)]),
        ("p", [(0.36, 0.68), (0.62, 0.86), (0.60, 0.9), (0.33, 0.73)]),
    ]),
    "bea": dict(title="BEA: upright, eyes shut, head back", shapes=[
        ("c", (0.0, 1.19, 0.11)),
        ("p", [(-0.06, 1.08), (0.08, 1.08), (0.17, 1.0), (0.21, 0.8), (0.22, 0.52), (-0.1, 0.49), (-0.12, 0.8), (-0.1, 1.0)]),
        ("p", [(-0.08, 0.47), (0.44, 0.49), (0.45, 0.62), (0.0, 0.65)]),
        ("p", [(0.35, 0.6), (0.46, 0.6), (0.45, 0.06), (0.35, 0.06)]),
        ("p", [(0.33, 0.0), (0.56, 0.0), (0.55, 0.09), (0.33, 0.09)]),
        ("p", [(0.17, 0.6), (0.42, 0.6), (0.44, 0.86), (0.19, 0.86)]),
        ("p", [(0.05, 0.98), (0.16, 0.98), (0.2, 0.82), (0.34, 0.86), (0.34, 0.8), (0.14, 0.74), (0.06, 0.84)]),
    ]),
    "kai": dict(title="KAI: slouched and loose", shapes=[
        ("c", (0.20, 0.99, 0.11)),
        ("p", [(-0.02, 1.0), (0.10, 1.02), (0.16, 0.92), (0.24, 0.72), (0.28, 0.5), (0.05, 0.47), (-0.04, 0.7), (-0.05, 0.92)]),
        ("p", [(0.05, 0.47), (0.55, 0.52), (0.58, 0.62), (0.08, 0.62)]),
        ("p", [(0.50, 0.6), (0.60, 0.58), (0.80, 0.08), (0.70, 0.06)]),
        ("p", [(0.68, 0.0), (0.92, 0.0), (0.92, 0.1), (0.70, 0.11)]),
        ("p", [(0.02, 0.92), (0.14, 0.9), (0.2, 0.75), (0.36, 0.80), (0.38, 0.74), (0.18, 0.66), (0.06, 0.76)]),
        ("p", [(0.33, 0.74), (0.39, 0.86), (0.36, 0.88), (0.30, 0.76)]),
    ]),
}


def draw(d, key, ox, floor, s, seat=True, label=True):
    def P(x, y):
        return (ox + x * s, floor - y * s)
    if seat:
        d.path(poly([P(-0.15, 0.45), P(0.5, 0.45), P(0.5, 0.33), P(-0.15, 0.33)]), fill="#3F6866", op=0.55)
        d.path(poly([P(-0.2, 0.33), P(-0.12, 0.33), P(-0.12, 1.05), P(-0.2, 1.05)]), fill="#3F6866", op=0.55)
    for kind, g in POSES[key]["shapes"]:
        if kind == "c":
            x, y, r = g
            d.circle(*P(x, y), r * s, K)
        else:
            d.path(smooth([P(x, y) for x, y in g], tension=0.25), fill=K)
    if label:
        d.text(ox + 0.2 * s, floor + 30, POSES[key]["title"], size=15, weight="bold", anchor="middle")


def build(out, header):
    d = Doc(1800, 1000)
    header(d, "Seated silhouettes", "They sit for the whole film. Profile silhouettes as the down-the-carriage 32 mm master sees them. Teal = seat.")
    order = ["noor", "walter", "bea", "kai"]
    for i, k in enumerate(order):
        draw(d, k, 170 + i * 420, 560, 300)
    d.add('<line x1="40" y1="560" x2="1760" y2="560" stroke="#C9C5BB" stroke-width="2"/>')
    d.text(40, 640, "AT DISTANCE (about the size they appear 6–10 m down the car on the master)", size=13, fill="#777", weight="bold")
    d.rect(40, 655, 1720, 150, "#A8ABA5")
    for i, k in enumerate(order):
        draw(d, k, 120 + i * 180, 790, 110, label=False)
    for i, k in enumerate(order):
        draw(d, k, 900 + i * 110, 790, 60, label=False)
    d.lines(40, 845, [
        "Test: each figure has to read with no interior detail, at the far end of the car, under one dipped panel.",
        "Noor: vertical spine, knees together, hands in lap, bun behind: a body presenting itself. (Over the film she slumps; by the confession she reads like Bea.)",
        "Walter: folded forward over the paper, long shins, coat over the knees, the paper angled up: still, economical.",
        "Bea: head back against the seat, bag on her lap, both hands on it: upright and closed. Kai: hips slid forward, legs out, head down to the glow: the loosest shape, so his empty seat is the emptiest.",
    ], size=14, fill="#2A2A2A")
    out("sheets/seated.svg", d, "Seated silhouettes")
