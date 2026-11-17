"""Build every design sheet. Run from the repo root:  python3 film/design/tools/build.py"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from svglib import Doc, Layer, swatch, THE_RED, smooth, poly  # noqa: E402
from face import draw_face, CHAR  # noqa: E402
from characters import figure, COL, HEIGHT_M, SEATED_EYE_M, PX_PER_M  # noqa: E402
from sheets_data import SHEETS, EXPRESSIONS  # noqa: E402

COSTUME_TOP = {'noor': '#3A3B40', 'kai': '#76787B', 'bea': '#B7AC95', 'walter': '#A8875A'}
DESIGN = os.path.dirname(HERE)


def out(rel, doc, title):
    path = os.path.join(DESIGN, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(doc.svg(title))
    print("wrote", rel)


def header(d, title, sub, right="THE QUIET CAR · character design · v1"):
    d.text(40, 62, title, size=44, weight="bold", fill="#1E1E1E", family="Georgia, serif")
    d.text(40, 94, sub, size=17, fill="#444")
    d.text(d.w - 40, 40, right, size=13, fill="#777", anchor="end")
    d.add(f'<line x1="40" y1="112" x2="{d.w-40}" y2="112" stroke="#BDB9B0" stroke-width="1"/>')


def char_sheet(key):
    S = SHEETS[key]
    d = Doc(1800, 1120)
    header(d, S["name"], S["sub"])
    ground = 1060
    # stage floor lines
    d.add(f'<line x1="60" y1="{ground}" x2="1140" y2="{ground}" stroke="#C9C5BB" stroke-width="2"/>')
    d.text(300, 140, "FRONT", size=13, fill="#777", anchor="middle", weight="bold")
    d.text(720, 140, "THREE-QUARTER", size=13, fill="#777", anchor="middle", weight="bold")

    L = Layer()
    A = figure(L, key, 300, ground, 0.0, opts=S.get("opts", {}))
    d.group(L.parts, 'filter="url(#paint)"')
    L = Layer()
    figure(L, key, 720, ground, 1.0, opts=S.get("opts", {}))
    d.group(L.parts, 'filter="url(#paint)"')

    # height marks
    top = A["_top"]
    d.add(f'<line x1="70" y1="{top:.0f}" x2="120" y2="{top:.0f}" stroke="#999" stroke-dasharray="4 3"/>')
    d.text(70, top - 8, f'{HEIGHT_M[key]:.2f} m', size=13, fill="#666")

    # numbered callouts on the front view
    for i, (anchor, _label) in enumerate(S["callouts"], 1):
        x, y = A[anchor]
        lx = 520 if x > 300 else 70
        lx = x + 60 if lx == 520 else x - 60
        d.add(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{lx:.0f}" y2="{y:.0f}" stroke="#555" stroke-width="1"/>')
        d.circle(lx, y, 11, "#1E1E1E")
        d.text(lx, y + 4.5, str(i), size=12, fill="#fff", anchor="middle", weight="bold")

    # silhouette test
    d.rect(960, 130, 200, 420, "#F6F5F1", stroke="#D3CFC6")
    d.text(1060, 152, "SILHOUETTE TEST", size=12, fill="#777", anchor="middle", weight="bold")
    for tx, tt in ((1010, 0.0), (1110, 1.0)):
        L = Layer()
        figure(L, key, tx, 530, tt, sil=True, scale=0.42, opts=S.get("opts", {}))
        d.group(L.parts)
    d.lines(970, 575, S["silhouette"], size=13, fill="#333")

    # right column: colour + costume callouts
    x0 = 1200
    d.text(x0, 150, "COSTUME AND COLOUR", size=13, fill="#777", weight="bold")
    y = 170
    for i, (anchor, label) in enumerate(S["callouts"], 1):
        hexv, name, note = label
        d.circle(x0 + 11, y + 12, 11, "#1E1E1E")
        d.text(x0 + 11, y + 16.5, str(i), size=12, fill="#fff", anchor="middle", weight="bold")
        swatch(d, x0 + 34, y, hexv, name, note)
        y += 42
    y += 6
    d.text(x0, y, "SKIN AND HAIR", size=13, fill="#777", weight="bold")
    y += 18
    c = CHAR[key]
    for hexv, name, note in (
        (c["skin"], "Skin", "ochre/umber halftones"),
        (c["shade"], "Skin shadow", "cool, never red"),
        (c["lip"], "Lips", "desaturated, no red"),
        (c["hair"], "Hair", S.get("hair_note", "")),
    ):
        swatch(d, x0 + 34, y, hexv, name, note)
        y += 40
    y += 10
    d.text(x0, y, "NOTES", size=13, fill="#777", weight="bold")
    d.lines(x0, y + 22, S["notes"], size=14, fill="#2A2A2A")
    out(f"sheets/{key}.svg", d, f"{S['name']} design sheet")


def expr_sheet(key):
    E = EXPRESSIONS[key]
    n = len(E["items"])
    cols = min(n, 4) if n != 5 else 5
    cw = 340
    d = Doc(max(1800, 60 + cols * cw), 1000)
    header(d, f"{SHEETS[key]['name']}: key expressions", E["sub"])
    for i, it in enumerate(E["items"]):
        cx = 40 + cw * i + cw / 2
        top = 186
        W, H = 230, 300
        d.rect(cx - cw / 2 + 10, 128, cw - 20, 850, "#F6F5F1", stroke="#D3CFC6")
        L = Layer()
        sk = CHAR[key]["skin"]
        neck = [(cx - 0.17 * W, top + 0.8 * H), (cx + 0.17 * W, top + 0.8 * H), (cx + 0.2 * W, top + 1.12 * H), (cx - 0.2 * W, top + 1.12 * H)]
        L.path(poly(neck), fill=CHAR[key]["shade"])
        L.path(smooth([(cx - 0.62 * W, top + 1.3 * H), (cx - 0.25 * W, top + 1.08 * H), (cx + 0.25 * W, top + 1.08 * H), (cx + 0.62 * W, top + 1.3 * H)]), fill=COSTUME_TOP[key])
        draw_face(L, cx, top, W, H, key, it["p"], turn=it.get("turn", 0.35), opts=it.get("opts", {}))
        d.group(L.parts, 'filter="url(#paintFine)"')
        y = top + H + 130
        d.text(cx - cw / 2 + 26, y, it["title"], size=19, weight="bold", fill="#1E1E1E", family="Georgia, serif")
        if it.get("line"):
            d.text(cx - cw / 2 + 26, y + 26, it["line"], size=15, fill="#3B3B3B", style='font-style="italic"')
        y2 = d.lines(cx - cw / 2 + 26, y + 58, it["notes"], size=13.5, fill="#2A2A2A")
        # control readout
        y2 += 12
        d.text(cx - cw / 2 + 26, y2, "RIG VALUES", size=11, fill="#888", weight="bold")
        rows = [f"{k} {v:+.2f}" if isinstance(v, float) else f"{k} {v}" for k, v in it["p"].items() if not k.startswith("catch")]
        line = ""
        yy = y2 + 18
        for r in rows:
            if len(line) + len(r) > 38:
                d.text(cx - cw / 2 + 26, yy, line, size=12, fill="#555", family="Menlo, monospace")
                yy += 16
                line = ""
            line += r + "   "
        if line:
            d.text(cx - cw / 2 + 26, yy, line, size=12, fill="#555", family="Menlo, monospace")
    if key == "bea":
        dark_check(d)
    out(f"expressions/{key}-expressions.svg", d, f"{SHEETS[key]['name']} expressions")


def dark_check(d):
    """F2: Bea's acting zones under the dark states (approximate grade, for design only)."""
    d.h = 1400
    d.text(40, 1030, "F2 · DARK-STATE CHECK: eyes closed but awake, under each light (approximation; the TA's brownout style frame is the real test)", size=13, fill="#777", weight="bold")
    d.add('<filter id="brown" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0.62 0.08 0 0 0  0.30 0.24 0 0 0  0.08 0.06 0.06 0 0  0 0 0 1 0"/></filter>')
    d.add('<filter id="edge" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0.30 0 0 0 0  0 0.31 0 0 0  0 0 0.32 0 0  0 0 0 1 0"/></filter>')
    states = [("Asleep car (~4300 K)", None), ("Brownout, cue 3 (exposed for it)", "brown"), ("Edge of the creeping dark, cue 7", "edge")]
    for i, (lab, f) in enumerate(states):
        cx = 220 + i * 420
        L = Layer()
        L.path(smooth([(cx - 120, 1330), (cx - 50, 1270), (cx + 50, 1270), (cx + 120, 1330)]), fill="#B7AC95")
        L.path(poly([(cx - 30, 1240), (cx + 30, 1240), (cx + 30, 1290), (cx - 30, 1290)]), fill="#22314F")
        draw_face(L, cx, 1060, 150, 195, "bea", dict(lid_up=0.0, tension=0.7, brow_in=-0.15, press=0.25, smile=-0.05), turn=0.35)
        d.group(L.parts, f'filter="url(#{f})"' if f else 'filter="url(#paintFine)"')
        d.text(cx, 1360, lab, size=13, anchor="middle", fill="#333")
    d.lines(1300, 1080, [
        "Bea's dark skin sits close in value to",
        "her navy scrubs, so the dark states",
        "could swallow her acting. Fix, per",
        "Director F2: lift the SCLERA (#F3F0E8)",
        "and LID-LINE contrast (near-black ink,",
        "35% heavier line, slightly lighter lid",
        "albedo), never her skin value. The",
        "oatmeal cardigan frames her face.",
        "TA: include Bea in the brownout",
        "style frame as an explicit check.",
    ], size=13.5, fill="#2A2A2A")


def lineup():
    d = Doc(1800, 1120)
    header(d, "Lineup, silhouettes and value check", "Heights to scale · shape ideas · greyscale check (the brownout collapses hue, so value must separate them)")
    ground = 590
    xs = {"walter": 190, "noor": 470, "bea": 750, "kai": 1030}
    for k, x in xs.items():
        L = Layer()
        figure(L, k, x, ground, 0.0, scale=0.55)
        d.group(L.parts, 'filter="url(#paint)"')
        L = Layer()
        figure(L, k, x, ground, 0.0, scale=0.55)
        d.group(L.parts, 'filter="url(#grey)" transform="translate(0,505)"')
        d.text(x, ground + 24, SHEETS[k]["name"], size=16, weight="bold", anchor="middle")
        d.text(x, ground + 40, f'{HEIGHT_M[k]:.2f} m · {SHEETS[k]["shape"]}', size=12, fill="#555", anchor="middle")
    for yy in (ground, ground + 505):
        d.add(f'<line x1="60" y1="{yy}" x2="1180" y2="{yy}" stroke="#C9C5BB" stroke-width="2"/>')
    for m in (1.0, 1.5):
        yy = ground - m * PX_PER_M * 0.55
        d.add(f'<line x1="60" y1="{yy:.0f}" x2="1180" y2="{yy:.0f}" stroke="#D6D2C8" stroke-dasharray="5 5"/>')
        d.text(62, yy - 5, f"{m:.1f} m", size=11, fill="#888")
    d.text(60, ground + 70, "GREYSCALE", size=12, fill="#777", weight="bold")
    # silhouettes row
    x0 = 1240
    d.rect(x0, 130, 520, 520, "#F6F5F1", stroke="#D3CFC6")
    d.text(x0 + 20, 155, "SILHOUETTES (must read with no interior detail)", size=12, fill="#777", weight="bold")
    for i, k in enumerate(["walter", "noor", "bea", "kai"]):
        L = Layer()
        figure(L, k, x0 + 75 + i * 125, 600, 1.0 if k in ("walter", "kai") else 0.0, sil=True, scale=0.5)
        d.group(L.parts)
    d.text(x0, 690, "PROXY SIZES FOR PREVIS (Milestone 4)", size=13, fill="#777", weight="bold")
    rows = ["Character   height   seated eye   shoulder w", "-" * 44]
    for k in ("noor", "kai", "bea", "walter"):
        sw = {"noor": 0.44, "kai": 0.46, "bea": 0.43, "walter": 0.45}[k]
        rows.append(f"{SHEETS[k]['name']:<11} {HEIGHT_M[k]:.2f} m   {SEATED_EYE_M[k]:.2f} m      {sw:.2f} m")
    d.lines(x0, 715, rows, size=14, family="Menlo, monospace", fill="#2A2A2A")
    d.lines(x0, 830, [
        "Seated eye height: from the floor, on a 0.45 m seat.",
        "Walter sits upright but stoops forward; Kai slouches",
        "(eye height drops to ~1.05 m when he's on his phone).",
        "Head length = 1/6.5 of standing height for all four.",
        "",
        "Shape ideas: Noor the upright rectangle, Kai the",
        "slouched triangle, Bea the rounded bell, Walter the",
        "tall leaning wedge.",
    ], size=14, fill="#2A2A2A")
    out("sheets/lineup.svg", d, "Lineup and silhouettes")


if __name__ == "__main__":
    for k in ("noor", "kai", "bea", "walter"):
        char_sheet(k)
        expr_sheet(k)
    lineup()
    import props
    props.build(out)
    import seated
    seated.build(out, header)
