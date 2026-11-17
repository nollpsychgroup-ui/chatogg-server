"""Parametric painted face. The parameters are the rig controls in expressions/face-rig.md.

All controls are normalised. Defaults are each character's neutral.
  brow_in, brow_out   -1 (down/knit) .. +1 (up)        per side with _L/_R suffix
  lid_up              0 (closed) .. 1 (wide)            per side
  lid_low             0 .. 1  lower-lid raise / cheek raise (real smile, held tears)
  tension             0 .. 1  lid squeeze while closed (awake vs asleep)
  smile               -1 (down) .. +1 (up) mouth corners, per side
  press               0 .. 1  lip press / thinning
  jaw                 0 .. 1  mouth open
  chin                0 .. 1  mentalis (chin pucker, holding back tears)
  naso                0 .. 1  nasolabial fold depth
  gaze_x, gaze_y      -1 .. 1 (camera-left/right, up=-1)
  tear                0/1
  catch               number of lit panels reflected in the eye (0..3 drawn)
"""
from svglib import smooth, poly, Layer

CHAR = {
    "noor": dict(
        skin="#A9714F", shade="#7E5A47", lip="#8A5A52", hair="#1E1A19", hair_hi="#3A302C",
        brow="#231B18", iris="#3B2A20", eye_tilt=-0.012, brow_th=0.03, brow_arch=0.025,
        head=[(0, 0), (0.30, 0.03), (0.45, 0.17), (0.50, 0.38), (0.48, 0.58), (0.42, 0.75), (0.30, 0.90), (0.14, 0.985), (0, 1.0)],
        mouth_w=0.165, lip_th=1.0, age=0.25,
    ),
    "kai": dict(
        skin="#D6B08C", shade="#A68D78", lip="#A57E72", hair="#1A1817", hair_hi="#35302C",
        brow="#1E1A18", iris="#2C211B", eye_tilt=-0.006, brow_th=0.034, brow_arch=0.008,
        head=[(0, 0), (0.32, 0.03), (0.47, 0.18), (0.50, 0.40), (0.49, 0.60), (0.45, 0.76), (0.33, 0.90), (0.16, 0.98), (0, 1.0)],
        mouth_w=0.17, lip_th=0.9, age=0.0,
    ),
    "bea": dict(
        skin="#5E3C2C", shade="#46322A", lip="#5A3A35", hair="#45413E", hair_hi="#9A9590",
        brow="#231915", iris="#1F1612", eye_tilt=0.0, brow_th=0.03, brow_arch=0.018,
        head=[(0, 0), (0.33, 0.03), (0.48, 0.17), (0.52, 0.40), (0.52, 0.60), (0.47, 0.77), (0.34, 0.91), (0.16, 0.985), (0, 1.0)],
        mouth_w=0.175, lip_th=1.15, age=0.55,
    ),
    "walter": dict(
        skin="#D9B79E", shade="#A9978A", lip="#A88378", hair="#DCD8D0", hair_hi="#F2EFE8",
        brow="#B9B3AA", iris="#4A5660", eye_tilt=0.016, brow_th=0.042, brow_arch=0.012,
        head=[(0, 0), (0.30, 0.02), (0.43, 0.15), (0.46, 0.38), (0.455, 0.58), (0.42, 0.76), (0.32, 0.90), (0.15, 0.98), (0, 1.0)],
        mouth_w=0.165, lip_th=0.75, age=1.0,
    ),
}

NEUTRAL = {
    "noor": dict(lid_up=0.82, naso=0.2),
    "kai": dict(lid_up=0.7, naso=0.1),
    "bea": dict(lid_up=0.7, naso=0.35, lid_low=0.1),
    "walter": dict(lid_up=0.62, naso=0.6),
}

INK = "#24180F"
_uid = [0]


def _p(p, k, side=None, default=0.0):
    if side and f"{k}_{side}" in p:
        return p[f"{k}_{side}"]
    return p.get(k, default)


class FaceView:
    def __init__(self, cx, top, W, H, turn):
        self.cx, self.top, self.W, self.H, self.t = cx, top, W, H, turn

    def x(self, xr, feat=False):
        t = self.t
        xr2 = xr * (1 - 0.32 * t) if xr < 0 else xr * (1 - 0.02 * t)
        shift = -0.10 * t - (0.07 * t if feat else 0)
        return self.cx + (xr2 + shift) * self.W

    def p(self, xr, yr, feat=False):
        return (self.x(xr, feat), self.top + yr * self.H)

    def pts(self, pts, feat=False):
        return [self.p(x, y, feat) for x, y in pts]


def hair_back(L, fv, char, opts):
    c = CHAR[char]
    if char == "noor":
        # low bun at the nape; visible behind the head in 3/4
        if fv.t > 0.3:
            bx, by = fv.p(0.50, 0.80)
            L.path(smooth([(bx - 0.13 * fv.W, by - 0.1 * fv.H), (bx + 0.09 * fv.W, by - 0.12 * fv.H), (bx + 0.15 * fv.W, by + 0.02 * fv.H),
                           (bx + 0.02 * fv.W, by + 0.12 * fv.H), (bx - 0.14 * fv.W, by + 0.06 * fv.H)]), fill=c["hair"])
        back = [(0, -0.05), (0.34, -0.015), (0.53, 0.17), (0.56, 0.40), (0.52, 0.60), (0.40, 0.72)]
        L.path(smooth(fv.pts(back + [(-x, y) for x, y in reversed(back)])), fill=c["hair"])
    if char == "kai":
        back = [(0, -0.12), (0.36, -0.07), (0.56, 0.12), (0.58, 0.40), (0.52, 0.62), (0.40, 0.70)]
        L.path(smooth(fv.pts(back + [(-x, y) for x, y in reversed(back)])), fill=c["hair"])
    if char == "bea":
        back = [(0, -0.10), (0.36, -0.06), (0.56, 0.14), (0.58, 0.42), (0.53, 0.62), (0.42, 0.68)]
        L.path(smooth(fv.pts(back + [(-x, y) for x, y in reversed(back)])), fill=c["hair"])


def hair_front(L, fv, char, opts):
    c = CHAR[char]
    if char == "noor":
        cap = [(-0.50, 0.44), (-0.535, 0.22), (-0.42, 0.03), (-0.20, -0.05), (0.02, -0.06), (0.26, -0.035), (0.46, 0.06),
               (0.535, 0.22), (0.50, 0.44), (0.47, 0.30), (0.40, 0.18), (0.24, 0.115), (0.07, 0.125), (0.035, 0.075),
               (-0.02, 0.13), (-0.24, 0.125), (-0.40, 0.19), (-0.47, 0.31)]
        L.path(smooth(fv.pts(cap), tension=0.35), fill=c["hair"])
        # the sweep: a few lighter lock shapes
        for a in ([(0.05, 0.05), (0.25, 0.0), (0.42, 0.1), (0.3, 0.05)], [(-0.05, 0.05), (-0.25, 0.01), (-0.4, 0.12), (-0.28, 0.06)]):
            L.path(smooth(fv.pts(a)), fill=c["hair_hi"], op=0.55)
        if opts.get("strand"):
            s = fv.pts([(0.40, 0.14), (0.49, 0.30), (0.50, 0.48), (0.54, 0.62)])
            L.path(smooth(s, closed=False), stroke=c["hair"], sw=fv.W * 0.02)
    if char == "kai":
        cap = [(-0.51, 0.40), (-0.56, 0.15), (-0.46, -0.05), (-0.30, -0.13), (-0.15, -0.10), (-0.04, -0.16), (0.10, -0.11),
               (0.26, -0.15), (0.41, -0.06), (0.55, 0.08), (0.56, 0.30), (0.51, 0.42), (0.47, 0.25), (0.36, 0.17), (0.22, 0.15),
               (0.12, 0.21), (0.0, 0.14), (-0.10, 0.12), (-0.25, 0.14), (-0.39, 0.19), (-0.47, 0.30)]
        L.path(smooth(fv.pts(cap), tension=0.3), fill=c["hair"])
        for a in ([(-0.2, -0.05), (0.0, -0.1), (0.15, 0.0), (0.0, -0.03)], [(0.2, -0.06), (0.38, 0.0), (0.35, 0.1), (0.25, 0.0)]):
            L.path(smooth(fv.pts(a)), fill=c["hair_hi"], op=0.6)
    if char == "bea":
        cap = [(-0.52, 0.45), (-0.565, 0.20), (-0.44, -0.01), (-0.22, -0.09), (0, -0.11), (0.22, -0.09), (0.44, -0.01),
               (0.565, 0.20), (0.52, 0.45), (0.485, 0.31), (0.42, 0.17), (0.25, 0.10), (0, 0.085), (-0.25, 0.10),
               (-0.42, 0.17), (-0.485, 0.31)]
        L.path(smooth(fv.pts(cap), tension=0.4), fill=c["hair"])
        import random
        rnd = random.Random(7)
        for _ in range(26):  # grey coming through
            x, y = rnd.uniform(-0.38, 0.34), rnd.uniform(-0.04, 0.12)
            if abs(x) > 0.3 and y > 0.1:
                continue
            a, b = fv.p(x, y), fv.p(x + 0.04, y + 0.01)
            L.path(poly([a, b], closed=False), stroke=c["hair_hi"], sw=fv.W * 0.012, op=0.7)
    if char == "walter":
        for sgn in (1, -1):
            if sgn < 0 and fv.t > 0.5:
                side = [(-0.44, 0.24), (-0.47, 0.40), (-0.45, 0.52), (-0.42, 0.44), (-0.41, 0.30)]
            else:
                side = [(sgn * 0.44, 0.20), (sgn * 0.495, 0.30), (sgn * 0.50, 0.46), (sgn * 0.47, 0.56), (sgn * 0.43, 0.48), (sgn * 0.42, 0.32)]
            L.path(smooth(fv.pts(side)), fill=c["hair"])
        wisp = [(-0.34, 0.08), (-0.1, -0.005), (0.18, 0.0), (0.38, 0.08), (0.22, 0.05), (0.0, 0.035), (-0.2, 0.05)]
        L.path(smooth(fv.pts(wisp)), fill=c["hair"], op=0.85)


def draw_face(L, cx, top, W, H, char, params=None, turn=0.0, opts=None):
    """Draws a head (no neck). Returns the FaceView for attaching extras."""
    opts = opts or {}
    c = CHAR[char]
    p = dict(NEUTRAL[char])
    p.update(params or {})
    fv = FaceView(cx, top, W, H, turn)
    _uid[0] += 1
    uid = f"f{_uid[0]}"

    hair_back(L, fv, char, opts)

    # head
    head = c["head"]
    outline = head + [(-x, y) for x, y in reversed(head)]
    if turn > 0.5:
        # near cheekbone shows more, far cheek tucks behind the nose line
        near = [(x * (1.09 if y < 0.66 else 1.0), y) for x, y in head]
        far = [(-0.12, 0.99), (-0.30, 0.88), (-0.40, 0.72), (-0.47, 0.57), (-0.46, 0.38), (-0.42, 0.17), (-0.30, 0.03)]
        outline = near + far
    L.add(f'<clipPath id="{uid}h"><path d="{smooth(fv.pts(outline))}"/></clipPath>')
    L.path(smooth(fv.pts(outline)), fill=c["skin"])

    # ears (near side always; far side only in front view)
    for sgn in (1, -1):
        if sgn < 0 and turn > 0.5:
            continue
        ex = 0.47 if char != "walter" else 0.445
        e = [(sgn * ex, 0.44), (sgn * (ex + 0.07), 0.45), (sgn * (ex + 0.08), 0.55), (sgn * (ex + 0.05), 0.66), (sgn * (ex - 0.01), 0.66)]
        if char == "walter":
            e = [(sgn * ex, 0.42), (sgn * (ex + 0.08), 0.43), (sgn * (ex + 0.09), 0.56), (sgn * (ex + 0.06), 0.70), (sgn * (ex - 0.01), 0.70)]
        if turn > 0.5 and sgn > 0:
            e = [(x - 0.05, y) for x, y in e]
        L.path(smooth(fv.pts(e)), fill=c["skin"])
        L.path(smooth(fv.pts([(x * 0.98 + sgn * 0.005, y + 0.01) for x, y in e[1:4]]), closed=False), stroke=c["shade"], sw=W * 0.012, op=0.8)
        if char == "kai" and sgn > 0:  # one white earbud
            bx, by = fv.p(e[2][0] - 0.03 * sgn, 0.56)
            L.circle(bx, by, W * 0.03, "#F4F4F0", stroke="#B8B8B2", sw=1)
            L.path(poly([(bx, by + W * 0.02), (bx, by + W * 0.09)], closed=False), stroke="#F4F4F0", sw=W * 0.025)

    # form shadow (sheet light = asleep car: soft top light). Far side in 3/4.
    L.add(f'<g clip-path="url(#{uid}h)">')
    if turn > 0.5:
        L.path(smooth(fv.pts([(-0.6, 0.1), (-0.3, 0.2), (-0.36, 0.6), (-0.25, 1.0), (-0.6, 1.0)])), fill=c["shade"], op=0.55, extra='filter="url(#softer)"')
    for sgn in (1, -1):
        L.path(smooth(fv.pts([(sgn * 0.62, 0.2), (sgn * 0.40, 0.3), (sgn * 0.36, 0.62), (sgn * 0.25, 0.95), (sgn * 0.62, 1.0)])), fill=c["shade"], op=0.5, extra='filter="url(#softer)"')
    for sgn in (1, -1):  # eye sockets, shallow by design (top light)
        L.path(smooth(fv.pts([(sgn * 0.1, 0.45), (sgn * 0.22, 0.42), (sgn * 0.33, 0.46), (sgn * 0.22, 0.5)], True)), fill=c["shade"], op=0.22, extra='filter="url(#soft)"')
    L.path(smooth(fv.pts([(-0.6, 0.93), (0, 1.02), (0.6, 0.93), (0.6, 1.2), (-0.6, 1.2)])), fill=c["shade"], op=0.5, extra='filter="url(#soft)"')
    L.add("</g>")

    # under-eye (age, tiredness)
    for sgn in (1, -1):
        ex = sgn * 0.205
        if sgn < 0 and turn > 0.5:
            ex = -0.2
        a = c["age"] + (0.6 if char == "bea" else 0)
        if a > 0.2:
            u = [(ex - 0.08, 0.565), (ex, 0.6 + 0.01 * a), (ex + 0.085, 0.565)]
            L.path(smooth(fv.pts(u, True), closed=False), stroke=c["shade"], sw=W * 0.012, op=min(0.8, 0.35 * a))

    # eyes
    for side, sgn in (("R", 1), ("L", -1)):
        _eye(L, fv, c, p, side, sgn, W, H, uid, turn)

    # brows
    for side, sgn in (("R", 1), ("L", -1)):
        bi, bo = _p(p, "brow_in", side), _p(p, "brow_out", side)
        y0 = 0.40
        xi, xm, xo = sgn * 0.085, sgn * 0.20, sgn * 0.32
        yi = y0 - 0.055 * bi
        yo = y0 + 0.015 - 0.04 * bo + (0.02 if char == "walter" else 0)
        ym = (yi + yo) / 2 - c["brow_arch"] - 0.01 * max(0, bi)
        th = c["brow_th"]
        top = [(xi, yi - th * 0.6), (xm, ym - th * 0.5), (xo, yo - th * 0.1)]
        bot = [(xo, yo + th * 0.15), (xm, ym + th * 0.45), (xi, yi + th * 0.6)]
        L.path(smooth(fv.pts(top + bot, True), tension=0.4), fill=c["brow"])
        if char == "walter":  # bushy
            for k in range(5):
                xx = xi + (xo - xi) * k / 4
                yy = yi + (yo - yi) * k / 4 - 0.01
                a, b = fv.p(xx, yy, True), fv.p(xx + sgn * 0.03, yy - 0.025, True)
                L.path(poly([a, b], closed=False), stroke=c["brow"], sw=W * 0.012)
    bi_mean = (_p(p, "brow_in", "L") + _p(p, "brow_in", "R")) / 2
    if bi_mean > 0.2:  # grief / worry: centre forehead lines
        for k, yy in enumerate((0.25, 0.29)):
            d = smooth(fv.pts([(-0.09, yy + 0.01), (0, yy - 0.005), (0.09, yy + 0.01)], True), closed=False)
            L.path(d, stroke=c["shade"], sw=W * 0.01, op=min(0.7, bi_mean))
    if bi_mean < -0.15:  # knit
        for sgn in (1, -1):
            d = poly(fv.pts([(sgn * 0.035, 0.37), (sgn * 0.03, 0.44)], True), closed=False)
            L.path(d, stroke=c["shade"], sw=W * 0.012, op=min(0.8, -bi_mean * 1.5))
    if char == "walter":
        for yy in (0.17, 0.215, 0.26):
            L.path(smooth(fv.pts([(-0.25, yy + 0.01), (0, yy), (0.25, yy + 0.01)], True), closed=False), stroke=c["shade"], sw=W * 0.008, op=0.45)

    # nose
    sh = c["shade"]
    if turn < 0.5:
        L.path(smooth(fv.pts([(0.035, 0.47), (0.055, 0.6), (0.075, 0.67)], True), closed=False), stroke=sh, sw=W * 0.012, op=0.6)
        L.path(smooth(fv.pts([(-0.1, 0.735), (0, 0.76), (0.1, 0.735), (0.08, 0.77), (0, 0.785), (-0.08, 0.77)], True)), fill=sh, op=0.35, extra='filter="url(#soft)"')
        L.path(smooth(fv.pts([(-0.095, 0.69), (-0.105, 0.725), (-0.06, 0.74), (0, 0.735), (0.06, 0.74), (0.105, 0.725), (0.095, 0.69)], True), closed=False), stroke=sh, sw=W * 0.013, op=0.8)
        for sgn in (1, -1):
            nx, ny = fv.p(sgn * 0.04, 0.728, True)
            L.add(f'<ellipse cx="{nx:.1f}" cy="{ny:.1f}" rx="{W*0.022:.1f}" ry="{W*0.011:.1f}" fill="{INK}" opacity="0.55"/>')
    else:
        prof = [(0.03, 0.46), (-0.035, 0.60), (-0.11, 0.69), (-0.085, 0.73), (-0.02, 0.735), (0.02, 0.72)]
        L.path(smooth(fv.pts(prof, True), tension=0.4), fill=c["skin"], stroke=sh, sw=W * 0.008)
        L.path(smooth(fv.pts([(0.02, 0.69), (0.09, 0.71), (0.08, 0.735), (0.02, 0.735)], True)), fill=sh, op=0.5)
        nx, ny = fv.p(0.015, 0.727, True)
        L.add(f'<ellipse cx="{nx:.1f}" cy="{ny:.1f}" rx="{W*0.022:.1f}" ry="{W*0.01:.1f}" fill="{INK}" opacity="0.55"/>')
        L.path(smooth(fv.pts([(-0.03, 0.745), (0.06, 0.77), (0.0, 0.775)], True)), fill=sh, op=0.35, extra='filter="url(#soft)"')

    # nasolabial folds
    naso = p.get("naso", 0) + 0.4 * max(0, (_p(p, "smile", "L") + _p(p, "smile", "R")) / 2) * (0.5 + p.get("lid_low", 0))
    for side, sgn in (("R", 1), ("L", -1)):
        if sgn < 0 and turn > 0.5:
            pts = [(-0.08, 0.72), (-0.13, 0.79), (-0.14, 0.86)]
        else:
            pts = [(sgn * 0.12, 0.71), (sgn * 0.18, 0.78), (sgn * 0.2, 0.86)]
        L.path(smooth(fv.pts(pts, True), closed=False), stroke=sh, sw=W * 0.022, op=min(0.85, naso), extra='filter="url(#soft)"')

    _mouth(L, fv, c, p, W, H, turn)

    # chin / mentalis
    ch = p.get("chin", 0)
    if ch > 0.05:
        L.path(smooth(fv.pts([(-0.07, 0.905), (0, 0.885 - 0.01 * ch), (0.07, 0.905)], True), closed=False), stroke=sh, sw=W * 0.012, op=min(0.8, ch))
        for k in range(3):
            dx = (k - 1) * 0.035
            x, y = fv.p(dx, 0.93, True)
            L.circle(x, y, W * 0.008, sh, op=0.6 * ch)
    if char == "walter":
        for sgn in (1, -1):
            if sgn < 0 and turn > 0.5:
                continue
            L.path(smooth(fv.pts([(sgn * 0.27, 0.84), (sgn * 0.29, 0.92)], True), closed=False), stroke=sh, sw=W * 0.012, op=0.5)

    # tear: a wet line from the camera-side lower lid
    if p.get("tear"):
        tx = 0.25 if turn < 0.5 else 0.22
        tr = fv.pts([(tx - 0.03, 0.58), (tx - 0.01, 0.66), (tx, 0.74)], True)
        L.path(smooth(tr, closed=False), stroke="#E8EEF2", sw=W * 0.012, op=0.85)
        L.path(smooth(fv.pts([(tx - 0.11, 0.565), (tx - 0.04, 0.578), (tx + 0.02, 0.565)], True), closed=False), stroke="#E8EEF2", sw=W * 0.008, op=0.8)

    hair_front(L, fv, char, opts)
    return fv


def _eye(L, fv, c, p, side, sgn, W, H, uid, turn):
    far = sgn < 0 and turn > 0.5
    ex = sgn * 0.205
    ew = 0.195
    eh = 0.098
    ey = 0.505
    up = max(0.0, min(1.1, _p(p, "lid_up", side, 0.8)))
    low = _p(p, "lid_low", side)
    tilt = c["eye_tilt"]
    inner = (ex - sgn * ew / 2, ey)
    outer = (ex + sgn * ew / 2, ey + tilt)
    # upper lid control points: peak toward the inner third
    uy = ey - eh * up * 0.78
    upper = [inner, (ex - sgn * ew * 0.12, uy), (ex + sgn * ew * 0.22, uy + eh * 0.08 * up), outer]
    ly = ey + eh * 0.36 * (1 - 0.75 * low)
    lower = [outer, (ex + sgn * ew * 0.15, ly), (ex - sgn * ew * 0.2, ly - 0.005), inner]
    eye_pts = upper + lower[1:-1]
    eid = f"{uid}{side}"
    closed = up < 0.12
    if not closed:
        shape = smooth(fv.pts(eye_pts, True), tension=0.45)
        L.add(f'<clipPath id="{eid}"><path d="{shape}"/></clipPath>')
        L.path(shape, fill="#E9E6DE")
        L.add(f'<g clip-path="url(#{eid})">')
        gx, gy = p.get("gaze_x", 0), p.get("gaze_y", 0)
        ix, iy = fv.p(ex + gx * 0.04 - 0.012 * turn, ey - 0.012 + gy * 0.025, True)
        r = W * 0.052
        L.circle(ix, iy, r, c["iris"])
        L.circle(ix, iy, r * 0.45, "#0C0908")
        # lid shadow on the eyeball
        L.path(smooth(fv.pts(upper + [(ex + sgn * ew * 0.5, ey - eh * 1.5), (ex - sgn * ew * 0.5, ey - eh * 1.5)], True)), fill="#00000030")
        # catchlights: the panel row, reflected. Real reflections in the film; drawn here as a reminder.
        n = int(p.get("catch", 3))
        cc = p.get("catch_col", "#F6F8F2")
        for k in range(n):
            cxk = ix - r * 0.55 + k * r * 0.42
            L.rect(cxk, iy - r * 0.62, r * 0.3, r * 0.14, cc, rx=1)
        if p.get("phone_catch"):
            L.rect(ix - r * 0.1, iy + r * 0.35, r * 0.22, r * 0.22, "#D8E6FF", rx=1)
        L.add("</g>")
        # upper lid line + lashes
        L.path(smooth(fv.pts(upper, True), closed=False), stroke=INK, sw=W * 0.02)
        L.path(smooth(fv.pts(upper[1:], True), closed=False), stroke=INK, sw=W * 0.026)
        # lid crease
        cre = [(ex - sgn * ew * 0.36, uy - eh * 0.1), (ex + sgn * ew * 0.05, uy - eh * 0.42), (ex + sgn * ew * 0.42, uy - eh * 0.15)]
        L.path(smooth(fv.pts(cre, True), closed=False), stroke=c["shade"], sw=W * 0.012, op=0.75)
        # lower lid
        L.path(smooth(fv.pts(lower, True), closed=False), stroke=c["shade"], sw=W * 0.009, op=0.8)
        if low > 0.2:
            L.path(smooth(fv.pts([(ex - sgn * ew * 0.35, ly + 0.03), (ex, ly + 0.045), (ex + sgn * ew * 0.45, ly + 0.025)], True), closed=False),
                   stroke=c["shade"], sw=W * 0.012, op=min(0.7, low))
    else:
        tension = p.get("tension", 0)
        cl = [inner, (ex - sgn * ew * 0.1, ey + eh * 0.32 - 0.02 * tension), (ex + sgn * ew * 0.25, ey + eh * 0.3 - 0.01 * tension), (outer[0], outer[1] + 0.005)]
        L.path(smooth(fv.pts(cl, True), closed=False), stroke=INK, sw=W * 0.022)
        # lid surface
        L.path(smooth(fv.pts([inner, (ex, ey - eh * 0.7), outer, (ex + sgn * ew * 0.2, ey + eh * 0.28), (ex - sgn * ew * 0.1, ey + eh * 0.3)], True)),
               fill=c["shade"], op=0.25)
        if tension > 0.2:
            # awake: a squeeze crease at the outer corner and under the brow
            for k in range(2):
                a = (outer[0] + sgn * 0.02, outer[1] - 0.01 + k * 0.025)
                b = (outer[0] + sgn * 0.065, outer[1] - 0.02 + k * 0.04)
                L.path(poly(fv.pts([a, b], True), closed=False), stroke=c["shade"], sw=W * 0.01, op=min(0.9, tension))
            L.path(smooth(fv.pts([(ex - sgn * ew * 0.4, ey - eh * 0.6), (ex, ey - eh * 0.85), (ex + sgn * ew * 0.45, ey - eh * 0.55)], True), closed=False),
                   stroke=c["shade"], sw=W * 0.012, op=0.8 * tension)
        else:
            cre = [(ex - sgn * ew * 0.35, ey - eh * 0.35), (ex, ey - eh * 0.5), (ex + sgn * ew * 0.45, ey - eh * 0.2)]
            L.path(smooth(fv.pts(cre, True), closed=False), stroke=c["shade"], sw=W * 0.01, op=0.5)


def _mouth(L, fv, c, p, W, H, turn):
    my = 0.81 if fv else 0.81
    mw = c["mouth_w"]
    sl, sr = _p(p, "smile", "L"), _p(p, "smile", "R")
    press = p.get("press", 0)
    jaw = p.get("jaw", 0)
    th = c["lip_th"] * (1 - 0.6 * press)
    cl = (-mw - 0.012 * sl, my - 0.055 * sl)
    cr = (mw + 0.012 * sr, my - 0.055 * sr)
    open_ = jaw * 0.07
    up_top = [cl, (-0.06, my - 0.026 * th), (-0.015, my - 0.032 * th), (0, my - 0.024 * th), (0.015, my - 0.032 * th), (0.06, my - 0.026 * th), cr]
    mid_u = [cr, (0.06, my - 0.002 + 0.005 * (sr < 0)), (0, my + 0.002), (-0.06, my - 0.002), cl]
    mid_l = [cl, (-0.06, my + open_ * 0.9), (0, my + open_ + 0.002), (0.06, my + open_ * 0.9), cr]
    low_b = [cr, (0.08, my + open_ + 0.035 * th), (0, my + open_ + 0.045 * th), (-0.08, my + open_ + 0.035 * th), cl]
    # lips
    L.path(smooth(fv.pts(up_top + mid_u[1:-1], True), tension=0.45), fill=c["lip"], op=0.9)
    L.path(smooth(fv.pts(mid_l + low_b[1:-1], True), tension=0.45), fill=c["lip"], op=0.75)
    if open_ > 0.004:
        L.path(smooth(fv.pts(mid_u + mid_l[1:-1], True), tension=0.45), fill="#2E1E1A")
        if open_ > 0.012:
            L.path(smooth(fv.pts([(-0.07, my), (0, my + 0.002), (0.07, my), (0, my + open_ * 0.35)], True)), fill="#D9D2C6", op=0.8)
    L.path(smooth(fv.pts(mid_u, True), closed=False), stroke=INK, sw=W * 0.014, op=0.85)
    # corners
    for (x, y), sg in ((cl, -1), (cr, 1)):
        s = sl if sg < 0 else sr
        L.path(poly(fv.pts([(x, y), (x + sg * 0.02, y - 0.012 * s + 0.01 * press + 0.006 * (s < 0))], True), closed=False), stroke=c["shade"], sw=W * 0.012, op=0.7)
    # lower lip shadow
    L.path(smooth(fv.pts([(-0.06, my + open_ + 0.06 * th), (0, my + open_ + 0.07 * th), (0.06, my + open_ + 0.06 * th)], True), closed=False),
           stroke=c["shade"], sw=W * 0.02, op=0.45, extra='filter="url(#soft)"')


def draw_head_silhouette(L, cx, top, W, H, char, turn=0.0, opts=None):
    """Head + hair as one flat black shape, for silhouette tests."""
    import re
    c = CHAR[char]
    fv = FaceView(cx, top, W, H, turn)
    tmp = Layer()
    hair_back(tmp, fv, char, opts or {})
    head = c["head"]
    outline = head + [(-x, y) for x, y in reversed(head)]
    if turn > 0.5:
        near = [(x * (1.09 if y < 0.66 else 1.0), y) for x, y in head]
        far = [(-0.12, 0.99), (-0.30, 0.88), (-0.40, 0.72), (-0.47, 0.57), (-0.46, 0.38), (-0.42, 0.17), (-0.30, 0.03)]
        outline = near + far
    tmp.path(smooth(fv.pts(outline)), fill="#141414")
    hair_front(tmp, fv, char, opts or {})
    for part in tmp.parts:
        if not part.startswith("<path") or 'fill="none"' in part:
            continue
        part = re.sub(r'fill="#[0-9A-Fa-f]+"', 'fill="#141414"', part)
        part = re.sub(r' opacity="[0-9.]+"', "", part)
        L.add(part)
