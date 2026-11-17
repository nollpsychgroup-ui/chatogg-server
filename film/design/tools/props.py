"""Props that act: lanyard and badge, Walter's newspaper and pen, the two phones."""
from svglib import Doc, Layer, THE_RED, smooth, poly
from face import draw_face

HAND_W = "font-family=\"'Segoe Print','Bradley Hand','Comic Sans MS',cursive\""


def phone(d, x, y, w, h, case, screen_fn, label, sub, crack=False, dim=1.0):
    d.rect(x - 6, y - 6, w + 12, h + 12, case, rx=26)
    d.rect(x, y, w, h, "#0B0C0E", rx=20)
    screen_fn(x, y, w, h)
    if dim < 1.0:
        d.rect(x, y, w, h, "#000", rx=20, op=1 - dim)
    if crack:
        d.path(poly([(x + w - 4, y + h - 70), (x + w - 34, y + h - 40), (x + w - 52, y + h - 6)], closed=False), stroke="#FFFFFFAA", sw=1.2)
        d.path(poly([(x + w - 34, y + h - 40), (x + w - 6, y + h - 30)], closed=False), stroke="#FFFFFF88", sw=1)
    d.text(x + w / 2, y + h + 34, label, size=15, weight="bold", anchor="middle")
    d.lines(x + w / 2, y + h + 54, sub, size=12.5, fill="#555", anchor="middle")


def build(out):
    d = Doc(1800, 1180)
    d.text(40, 62, "Props that act", size=44, weight="bold", fill="#1E1E1E", family="Georgia, serif")
    d.text(40, 94, "Lanyard and badge · Walter's newspaper and pen · the two phones. All built to tier C (full detail): each one gets an insert.", size=17, fill="#444")
    d.text(1760, 40, "THE QUIET CAR · character design · v1", size=13, fill="#777", anchor="end")
    d.add('<line x1="40" y1="112" x2="1760" y2="112" stroke="#BDB9B0" stroke-width="1"/>')

    # ---------------------------------------------------- 1. lanyard + badge
    d.rect(40, 130, 560, 1010, "#F6F5F1", stroke="#D3CFC6")
    d.text(60, 158, "1  NOOR'S LANYARD AND BADGE", size=14, weight="bold", fill="#333")
    L = Layer()
    # strap loop (long, so it comes off over her head in one pull)
    L.path(smooth([(170, 190), (140, 330), (220, 470), (238, 520)], closed=False), stroke=THE_RED, sw=16)
    L.path(smooth([(330, 190), (360, 330), (280, 470), (262, 520)], closed=False), stroke=THE_RED, sw=16)
    L.path(smooth([(170, 190), (250, 172), (330, 190)], closed=False), stroke=THE_RED, sw=16)
    d.group(L.parts, 'filter="url(#paintFine)"')
    for k in range(6):  # tonal woven repeat
        d.text(150 + k * 2, 240 + k * 45, "A&L", size=9, fill="#9E0D24", style=f'transform="rotate({78 - k * 6} {150 + k * 2} {240 + k * 45})"')
    d.rect(238, 515, 24, 22, "#A6ABAF", rx=4)
    d.circle(250, 545, 9, "none", stroke="#8C9195", sw=4)
    # badge front
    bx, by, bw, bh = 150, 560, 200, 316
    d.rect(bx - 6, by - 6, bw + 12, bh + 12, "#E2E6E8", stroke="#B9BFC3", rx=10)
    d.rect(bx, by, bw, bh, "#EEEEE8", rx=8)
    d.rect(bx + 70, by + 10, 60, 10, "#C9CDD0", rx=5)
    d.rect(bx, by + 30, bw, 38, "#4B5867")
    d.text(bx + bw / 2, by + 55, "ASHGROVE & LYLE", size=15, weight="bold", fill="#EEEEE8", anchor="middle", family="Georgia, serif")
    d.rect(bx + 40, by + 84, 120, 140, "#B9BEC2")
    L = Layer()
    draw_face(L, bx + 100, by + 100, 84, 110, "noor", dict(smile=0.5, lid_up=0.85), turn=0.0)
    d.add(f'<clipPath id="photoclip"><rect x="{bx+40}" y="{by+84}" width="120" height="140"/></clipPath>')
    d.group(L.parts, 'clip-path="url(#photoclip)"')
    d.text(bx + bw / 2, by + 252, "NOOR AZIZ", size=18, weight="bold", fill="#2A2C30", anchor="middle")
    d.text(bx + bw / 2, by + 272, "Client Accounts", size=13, fill="#4B5867", anchor="middle")
    d.text(bx + bw / 2, by + 300, "ID 40217 · VALID TO 09/2026", size=10, fill="#6A7480", anchor="middle", family="Menlo, monospace")
    # badge back
    bx2 = 380
    d.rect(bx2 - 6, by - 6, bw * 0.8 + 12, bh * 0.8 + 12, "#E2E6E8", stroke="#B9BFC3", rx=10)
    d.rect(bx2, by, bw * 0.8, bh * 0.8, "#EEEEE8", rx=8)
    d.rect(bx2, by + 40, bw * 0.8, 30, "#3A3B40")
    d.lines(bx2 + 14, by + 110, ["If found, please", "return to reception.", "", "This card remains", "the property of", "Ashgrove & Lyle."], size=11, fill="#666")
    d.text(bx2 + 80, by + bh * 0.8 + 26, "back (she turns it over)", size=11, fill="#777", anchor="middle")
    d.lines(60, 920, [
        "Strap: 20 mm woven polyester in THE RED #C8102E,",
        "tonal 'A&L' repeat woven in (still red: same hue).",
        "Loop long enough (~90 cm) to pull over her head in",
        "one move. NO breakaway clasp: if it popped, the",
        "throw would read as an accident, not a choice.",
        "Badge: white PVC, CR80 portrait in a clear holder.",
        "Logo bar slate #4B5867 (no red on the badge itself).",
        "Photo: her 'fine' smile, mouth only, a year younger.",
        "VALID TO 09/2026 is a fair-play clue for the second",
        "viewing (she was let go in September). Never featured.",
        "Name and company are placeholders: Director to confirm.",
    ], size=13, fill="#2A2A2A")

    # ---------------------------------------------------- 2. newspaper + pen
    d.rect(620, 130, 560, 1010, "#F6F5F1", stroke="#D3CFC6")
    d.text(640, 158, "2  WALTER'S NEWSPAPER AND PEN", size=14, weight="bold", fill="#333")
    # folded quarter page
    px, py, pw, ph = 660, 190, 230, 330
    L = Layer()
    L.rect(px, py, pw, ph, "#D9D3C3")
    L.rect(px + 4, py + 4, pw, ph, "#CFC8B6", op=0.5)
    d.group(L.parts, 'filter="url(#paintFine)"')
    d.text(px + 12, py + 30, "THE EVENING LEDGER", size=15, weight="bold", fill="#2B2B2B", family="Georgia, serif")
    d.add(f'<line x1="{px+10}" y1="{py+40}" x2="{px+pw-10}" y2="{py+40}" stroke="#2B2B2B" stroke-width="1.5"/>')
    for col in range(3):
        for k in range(22):
            yy = py + 56 + k * 12
            ww = 58 if (k % 7) != 6 else 30
            d.rect(px + 12 + col * 72, yy, ww, 3.5, "#8D877A")
    d.text(px + pw / 2, py + ph + 24, "carried: folded to one page", size=12, fill="#666", anchor="middle")
    # margin note 1
    nx, ny = 920, 190
    d.rect(nx, ny, 230, 330, "#D9D3C3")
    for k in range(24):
        d.rect(nx + 60, ny + 20 + k * 12, 150, 3.5, "#8D877A")
    d.add(f'<text x="{nx+30}" y="{ny+40}" {HAND_W} font-size="30" fill="#1F2A44" transform="rotate(-90 {nx+30} {ny+40})" text-anchor="end">DON\'T LIE IN HERE.</text>')
    d.rect(nx + 8, ny + 10, 44, 310, "none", stroke="#00000000")
    d.text(nx + 115, ny + ph + 24, "beat 1: Walter's margin note", size=12, fill="#666", anchor="middle")
    # margin note 2 (held up turned)
    nx2, ny2 = 660, 570
    d.rect(nx2, ny2, 490, 230, "#D9D3C3")
    for k in range(9):
        d.rect(nx2 + 20, ny2 + 120 + k * 11, 450, 3.5, "#8D877A")
    d.add(f'<text x="{nx2+24}" y="{ny2+48}" {HAND_W} font-size="32" fill="#1F2A44" letter-spacing="2">DON\'T LIE IN HERE.</text>')
    d.add(f'<text x="{nx2+30}" y="{ny2+92}" {HAND_W} font-size="27" fill="#1F2A44" font-style="italic">IT\'S AWAKE NOW. YOU WOKE IT.</text>')
    d.text(nx2 + 245, ny2 + 254, "beat 2: Bea's line underneath, a rounder, faster hand", size=12, fill="#666", anchor="middle")
    # pen
    d.rect(700, 850, 300, 16, "#1E1F22", rx=8)
    d.rect(1000, 852, 40, 12, "#B9BDC0", rx=4)
    d.rect(700, 846, 90, 24, "#2A2B2F", rx=8)
    d.rect(712, 844, 60, 4, "#B9BDC0", rx=2)
    d.text(870, 892, "ballpoint: black barrel, black cap, blue-black ink", size=12, fill="#666", anchor="middle")
    d.lines(640, 935, [
        "Newsprint #D9D3C3, ink #2B2B2B. Masthead BLACK: no red",
        "masthead, no colour photos on the visible pages.",
        "Printed text is never legible (greeked), so it can't",
        "compete with the handwriting.",
        "Two hands, one pen: Walter writes tall, careful capitals;",
        "Bea's line is rounder and quicker. Blue-black ink reads",
        "as 'pen', not colour. Letters ~25 mm tall so the notes",
        "read at 40–50 mm across the car. One prop per beat.",
        "The fold is soft and worn: same page every night.",
        "Final beat: he unfolds it and turns the page (first time).",
    ], size=13, fill="#2A2A2A")

    # ---------------------------------------------------- 3. phones
    d.rect(1200, 130, 560, 1010, "#F6F5F1", stroke="#D3CFC6")
    d.text(1220, 158, "3  THE PHONES", size=14, weight="bold", fill="#333")
    pw, ph = 150, 300

    def bg(x, y, w, h, top="#2D3A55", bot="#18202F"):
        gid = f"g{int(x)}{int(y)}"
        d.add(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>')
        d.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="url(#{gid})"/>')

    def noor_incoming(x, y, w, h):
        bg(x, y, w, h, "#AFC3E0", "#6E86AD")
        d.text(x + w / 2, y + 90, "MARK", size=26, weight="bold", fill="#FFFFFF", anchor="middle")
        d.text(x + w / 2, y + 112, "mobile", size=12, fill="#EEF3FA", anchor="middle")
        d.circle(x + 40, y + h - 50, 22, "#5A6170")
        d.circle(x + w - 40, y + h - 50, 22, "#E9EEF5")
        d.text(x + 40, y + h - 18, "decline", size=9, fill="#fff", anchor="middle")
        d.text(x + w - 40, y + h - 18, "accept", size=9, fill="#fff", anchor="middle")

    def noor_incall(x, y, w, h):
        bg(x, y, w, h, "#3A4866", "#1C2433")
        d.text(x + w / 2, y + 80, "Mark", size=22, weight="bold", fill="#FFFFFF", anchor="middle")
        d.text(x + w / 2, y + 102, "00:41", size=12, fill="#C9D3E2", anchor="middle")
        d.circle(x + w / 2, y + h - 52, 24, "#5A6170")
        d.text(x + w / 2, y + h - 20, "end (grey: not red)", size=9, fill="#fff", anchor="middle")

    def kai_incoming(x, y, w, h):
        bg(x, y, w, h, "#AFC3E0", "#6E86AD")
        d.text(x + w / 2, y + 90, "MUM", size=26, weight="bold", fill="#FFFFFF", anchor="middle")
        d.rect(x + 18, y + h - 70, w - 36, 40, "#FFFFFF55", rx=20)
        d.circle(x + 38, y + h - 50, 16, "#FFFFFF")
        d.text(x + w / 2 + 14, y + h - 46, "slide to answer", size=10, fill="#fff", anchor="middle")

    def kai_incall(x, y, w, h):
        bg(x, y, w, h, "#3A4866", "#1C2433")
        d.text(x + w / 2, y + 80, "Mum", size=22, weight="bold", fill="#FFFFFF", anchor="middle")
        d.text(x + w / 2, y + 102, "02:57", size=12, fill="#C9D3E2", anchor="middle")
        for k in range(3):
            d.circle(x + 35 + k * 40, y + 170, 15, "#FFFFFF33")
        d.circle(x + w / 2, y + h - 52, 26, THE_RED)
        d.path(smooth([(x + w / 2 - 13, y + h - 50), (x + w / 2, y + h - 56), (x + w / 2 + 13, y + h - 50)], closed=False), stroke="#fff", sw=4)

    phone(d, 1240, 190, pw, ph, "#2A3140", noor_incoming, "Noor: incoming", ["navy case; no red on", "her phone, ever"])
    phone(d, 1420, 190, pw, ph, "#2A3140", noor_incall, "Noor: in call", ["end button dark grey;", "lights her face from below"])
    phone(d, 1240, 640, pw, ph, "#8E9399", kai_incoming, "Kai: incoming", ["clear grey case,", "cracked protector"], crack=True)
    phone(d, 1420, 640, pw, ph, "#8E9399", kai_incall, "Kai: in call (insert)", ["THE RED end-call button:", "the second and last red"], crack=True)
    phone(d, 1600, 640, pw * 0.7, ph * 0.7, "#8E9399", kai_incall, "dims, then dark", ["final shot"], crack=True, dim=0.3)
    d.lines(1600, 230, [
        "Screens are the",
        "only light the car",
        "doesn't control:",
        "cold blue-white,",
        "emissive, low",
        "brightness. UI is",
        "plain and generic",
        "(no real OS look).",
        "",
        "Incoming screens",
        "have no red",
        "decline button.",
        "",
        "Kai's call timer",
        "keeps running all",
        "film: it's a clock.",
    ], size=12.5, fill="#2A2A2A")
    d.lines(1220, 1060, [
        "The 40 mm insert: Noor's thumb over Kai's red button, lit only by the screen and the",
        "panel. The button must stay readable as red under cue 7 light. It rhymes with her strap.",
    ], size=12.5, fill="#2A2A2A")
    out("props/props.svg", d, "Props that act")
