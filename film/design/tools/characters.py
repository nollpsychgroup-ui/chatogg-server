"""Full-figure turnaround drawings (front and three-quarter) and silhouettes."""
from svglib import smooth, poly, mirror, View, Layer, THE_RED
from face import draw_face, draw_head_silhouette, CHAR

PX_PER_M = 448  # sheet scale: 1.83 m (Walter) = 820 px

HEIGHT_M = {"noor": 1.66, "kai": 1.78, "bea": 1.62, "walter": 1.83}
SEATED_EYE_M = {"noor": 1.16, "kai": 1.14, "bea": 1.13, "walter": 1.20}  # seat 0.45 m, slouch etc.

COL = {
    "noor": dict(suit="#3A3B40", suit_d="#2C2D31", skirt="#36373C", blouse="#C8CED4", tights="#2F2B2B", shoe="#161515",
                 badge="#EEEEE8", bag="#25221F", strap=THE_RED),
    "kai": dict(hood="#76787B", hood_d="#5E6063", jeans="#2A2C30", shoe="#D8D6CF", sole="#9A9893", string="#C9C9C4", phone="#1B1C1F",
                screen="#CFE0F5"),
    "bea": dict(scrub="#22314F", scrub_d="#1A263D", cardi="#B7AC95", cardi_d="#9C917B", tote="#5A4A3B", clog="#2B3550", watch="#B9BDC0"),
    "walter": dict(coat="#A8875A", coat_d="#8C6F48", scarf="#77777A", shirt="#B9C4CC", trousers="#4E4A45", shoe="#3E3328",
                   paper="#D9D3C3", ink="#2B2B2B"),
}


def _sym(pts):
    return mirror(pts)


def figure(L, char, cx, ground, turn=0.0, sil=False, scale=1.0, face_params=None, opts=None):
    """Draw a standing figure into Layer L. Returns anchor points for callouts."""
    opts = opts or {}
    h_px = HEIGHT_M[char] * PX_PER_M * scale
    u = h_px / 6.5
    top = ground - h_px
    v = View(cx, top, u, turn)
    c = COL[char]
    sk = CHAR[char]["skin"]
    A = {}

    def F(col):
        return "#141414" if sil else col

    def shape(pts, col, sm=True, tension=0.5, op=1.0, extra=""):
        d = smooth(v.pts(pts), tension=tension) if sm else poly(v.pts(pts))
        L.path(d, fill=F(col), op=1.0 if sil else op, extra=extra)

    def line(pts, col, w, op=1.0):
        if sil:
            return
        L.path(smooth(v.pts(pts), closed=False), stroke=col, sw=w * u, op=op)

    def legs(right, col):
        shape(right, col, tension=0.35)
        shape([(-x, y) for x, y in right], col, tension=0.35)

    head_dx, head_dy = 0.0, 0.0

    if char == "noor":
        # laptop bag behind/at her side (camera-left), strap over the shoulder
        legs([(0.08, 4.45), (0.34, 4.45), (0.31, 5.3), (0.26, 6.2), (0.15, 6.22), (0.13, 5.3)], c["tights"])
        for s in (1, -1):
            shape([(s * 0.12, 6.15), (s * 0.31, 6.15), (s * 0.36, 6.42), (s * 0.34, 6.5), (s * 0.1, 6.5)], c["shoe"], tension=0.3)
        shape(_sym([(0.12, 0.9), (0.13, 1.3)]), sk, sm=False)
        shape(_sym([(0.68, 3.15), (0.69, 3.6), (0.62, 4.55)]), c["skirt"], tension=0.3)
        shape(_sym([(0.18, 1.17), (0.56, 1.27), (0.9, 1.36), (0.93, 1.6), (0.8, 2.2), (0.71, 2.7), (0.75, 3.1), (0.74, 3.38)]), c["suit"], tension=0.35)
        shape([(-0.17, 1.18), (0.17, 1.18), (0.05, 2.1), (-0.05, 2.1)], c["blouse"], sm=False)
        for s in (1, -1):  # lapels
            shape([(s * 0.17, 1.18), (s * 0.33, 1.33), (s * 0.27, 1.62), (s * 0.05, 2.15)], c["suit_d"], sm=False)
            shape([(s * 0.86, 1.35), (s * 0.99, 1.5), (s * 1.02, 2.3), (s * 1.03, 3.08), (s * 0.85, 3.12), (s * 0.82, 2.4), (s * 0.77, 1.7)], c["suit_d"], tension=0.35)
            shape([(s * 0.86, 3.08), (s * 1.02, 3.08), (s * 1.03, 3.4), (s * 0.97, 3.58), (s * 0.88, 3.5)], sk)
        if not sil:
            L.circle(*v.p(0, 2.5), u * 0.035, "#1C1C1F")
        # lanyard: THE RED strap, badge face-out
        if not opts.get("no_lanyard"):
            for s in (1, -1):
                d = smooth(v.pts([(s * 0.15, 1.14), (s * 0.12, 1.6), (s * 0.05, 2.2), (s * 0.02, 2.48)]), closed=False)
                L.path(d, stroke=F(c["strap"]), sw=u * 0.055)
            shape([(-0.03, 2.45), (0.03, 2.45), (0.03, 2.56), (-0.03, 2.56)], "#9A9EA2", sm=False)
            shape([(-0.17, 2.55), (0.17, 2.55), (0.17, 3.02), (-0.17, 3.02)], c["badge"], sm=False)
            if not sil:
                shape([(-0.12, 2.62), (0.0, 2.62), (0.0, 2.78), (-0.12, 2.78)], "#8A7F76", sm=False)
                shape([(0.03, 2.64), (0.13, 2.64), (0.13, 2.67), (0.03, 2.67)], "#4B5867", sm=False)
                shape([(-0.12, 2.86), (0.12, 2.86), (0.12, 2.92), (-0.12, 2.92)], "#4B5867", sm=False)
            A["strap"] = v.p(0.12, 1.65)
            A["badge"] = v.p(0.17, 2.8)
        # bag on the camera-left shoulder
        d = smooth(v.pts([(-0.7, 1.3), (-0.95, 2.1), (-1.18, 2.95)]), closed=False)
        L.path(d, stroke=F("#1A1816"), sw=u * 0.05)
        shape([(-1.48, 2.95), (-0.98, 2.92), (-0.95, 3.8), (-1.5, 3.82)], c["bag"], sm=False)
        A.update(suit=v.p(0.85, 2.0), blouse=v.p(0.0, 1.75), skirt=v.p(0.6, 4.0), bag=v.p(-1.22, 3.4), shoe=v.p(0.3, 6.4))

    if char == "kai":
        legs([(0.05, 3.5), (0.52, 3.5), (0.5, 4.6), (0.45, 6.05), (0.13, 6.05), (0.08, 4.6)], c["jeans"])
        for s in (1, -1):
            shape([(s * 0.06, 5.98), (s * 0.5, 5.98), (s * 0.6, 6.28), (s * 0.6, 6.5), (s * 0.04, 6.5), (s * 0.04, 6.2)], c["shoe"], tension=0.3)
            shape([(s * 0.04, 6.4), (s * 0.6, 6.4), (s * 0.6, 6.5), (s * 0.04, 6.5)], c["sole"], sm=False)
        shape(_sym([(0.13, 0.9), (0.14, 1.3)]), sk, sm=False)
        shape(_sym([(0.0, 0.98), (0.42, 1.02), (0.58, 1.3), (0.3, 1.42)]), c["hood_d"])
        shape(_sym([(0.2, 1.17), (0.62, 1.3), (0.9, 1.5), (0.96, 1.95), (0.88, 2.6), (0.9, 3.3), (0.86, 3.62)]), c["hood"], tension=0.4)
        shape([(0.46, 2.72), (0.56, 3.3), (-0.56, 3.3), (-0.46, 2.72)], c["hood_d"], sm=False, op=0.8)
        for s in (1, -1):
            shape([(s * 0.86, 1.45), (s * 1.06, 1.75), (s * 1.13, 2.6), (s * 1.12, 3.35), (s * 1.08, 3.48), (s * 0.92, 3.48), (s * 0.9, 2.6), (s * 0.82, 1.9)], c["hood"], tension=0.4)
            shape([(s * 0.9, 3.3), (s * 1.12, 3.3), (s * 1.1, 3.48), (s * 0.92, 3.48)], c["hood_d"], tension=0.3)
            line([(s * 0.1, 1.32), (s * 0.12, 1.7), (s * 0.13, 2.05)], c["string"], 0.025)
        # hands; phone in camera-right hand, glowing
        shape([(-1.08, 3.45), (-0.93, 3.45), (-0.94, 3.75), (-1.06, 3.78)], sk)
        if not sil:
            L.circle(*v.p(1.0, 3.62), u * 0.35, "#CFE0F5", op=0.25, ) if False else None
        shape([(0.92, 3.44), (1.08, 3.44), (1.12, 3.72), (0.95, 3.75)], sk)
        shape([(0.93, 3.32), (1.13, 3.36), (1.09, 3.72), (0.89, 3.68)], c["phone"], sm=False)
        if not sil:
            shape([(0.94, 3.35), (1.11, 3.38), (1.08, 3.69), (0.91, 3.66)], c["screen"], sm=False)
            shape([(0.94, 3.55), (1.08, 3.44), (1.12, 3.72), (0.95, 3.75)], sk)
        A.update(hoodie=v.p(0.8, 2.2), jeans=v.p(0.35, 4.8), shoe=v.p(0.5, 6.3), phone=v.p(1.08, 3.4), earbud=v.p(0.45, 0.57))

    if char == "bea":
        legs([(0.06, 3.3), (0.62, 3.3), (0.6, 4.6), (0.54, 6.12), (0.14, 6.12), (0.1, 4.6)], c["scrub"])
        for s in (1, -1):
            shape([(s * 0.1, 6.05), (s * 0.56, 6.05), (s * 0.62, 6.4), (s * 0.6, 6.5), (s * 0.08, 6.5)], c["clog"], tension=0.3)
        shape(_sym([(0.14, 0.9), (0.15, 1.3)]), sk, sm=False)
        shape(_sym([(0.17, 1.18), (0.6, 1.3), (0.88, 1.5), (0.92, 2.0), (0.9, 2.8), (0.95, 3.35)]), c["scrub"], tension=0.4)
        shape([(-0.16, 1.17), (0.16, 1.17), (0.0, 1.62)], sk, sm=False)
        if not sil:
            L.circle(*v.p(0.21, 1.78), u * 0.055, c["watch"], stroke="#7E8487", sw=1.5)
            L.circle(*v.p(0.21, 1.78), u * 0.035, "#EDEDE8")
        for s in (1, -1):
            shape([(s * 0.2, 1.2), (s * 0.62, 1.27), (s * 0.95, 1.5), (s * 1.02, 2.0), (s * 1.02, 3.0), (s * 1.04, 3.62),
                   (s * 0.48, 3.64), (s * 0.36, 2.6), (s * 0.3, 1.8)], c["cardi"], tension=0.4)
            shape([(s * 0.88, 1.45), (s * 1.09, 1.75), (s * 1.14, 2.5), (s * 0.98, 3.05), (s * 0.45, 3.22), (s * 0.42, 3.02), (s * 0.84, 2.62), (s * 0.85, 1.9)], c["cardi_d"], tension=0.4)
        # tote held in front with both hands
        if not sil:
            for s in (1, -1):
                L.path(smooth(v.pts([(s * 0.42, 3.15), (s * 0.3, 2.85), (s * 0.15, 3.15)]), closed=False), stroke=c["tote"], sw=u * 0.04)
        shape([(-0.62, 3.12), (0.62, 3.12), (0.7, 3.98), (-0.7, 3.98)], c["tote"], sm=False)
        for s in (1, -1):
            shape([(s * 0.42, 3.0), (s * 0.12, 3.06), (s * 0.12, 3.24), (s * 0.44, 3.24)], sk)
        A.update(scrubs=v.p(0.8, 2.3), cardigan=v.p(-0.98, 2.4), tote=v.p(0.62, 3.6), clogs=v.p(0.5, 6.3), watch=v.p(0.26, 1.75))

    if char == "walter":
        head_dx, head_dy = -0.05 - 0.12 * turn, 0.05 + 0.04 * turn
        legs([(0.08, 5.0), (0.38, 5.0), (0.37, 6.15), (0.13, 6.15)], c["trousers"])
        for s in (1, -1):
            shape([(s * 0.1, 6.12), (s * 0.4, 6.12), (s * 0.5, 6.38), (s * 0.5, 6.5), (s * 0.08, 6.5)], c["shoe"], tension=0.3)
        shape(_sym([(0.12, 0.95), (0.14, 1.3)]), sk, sm=False)
        shape(_sym([(0.18, 1.2), (0.55, 1.3), (0.8, 1.44), (0.86, 1.8), (0.82, 2.6), (0.84, 3.4), (0.92, 4.4), (0.97, 5.2)]), c["coat"], tension=0.35)
        for s in (1, -1):
            shape([(s * 0.16, 1.2), (s * 0.38, 1.38), (s * 0.31, 1.95), (s * 0.04, 2.35)], c["coat_d"], sm=False)
        line([(0.03, 2.3), (0.04, 3.6), (0.06, 5.2)], "#6E5537", 0.025)
        for yy in (2.55, 3.15, 3.75):
            if not sil:
                L.circle(*v.p(0.12, yy), u * 0.04, "#4E3B26")
        shape([(-0.06, 1.25), (0.06, 1.25), (0.08, 1.9), (-0.08, 1.9)], c["shirt"], sm=False)
        shape(_sym([(0.22, 1.08), (0.27, 1.32), (0.14, 1.62)]), c["scarf"])
        shape([(-0.2, 1.5), (0.0, 1.5), (-0.02, 2.4), (-0.22, 2.42)], c["scarf"], sm=False)
        for s in (1, -1):
            shape([(s * 0.78, 1.42), (s * 0.97, 1.65), (s * 1.03, 2.5), (s * 1.05, 3.45), (s * 0.83, 3.5), (s * 0.8, 2.5)], c["coat_d"], tension=0.35)
        # big hands; newspaper folded to one page in the camera-left hand
        shape([(0.84, 3.44), (1.06, 3.42), (1.1, 3.85), (0.98, 3.98), (0.86, 3.85)], sk)
        shape([(-1.25, 2.95), (-0.88, 2.9), (-0.82, 3.95), (-1.19, 4.0)], c["paper"], sm=False)
        if not sil:
            for k in range(7):
                yy = 3.1 + k * 0.11
                line([(-1.18, yy), (-0.92, yy - 0.01)], "#8D877A", 0.02)
        shape([(-1.06, 3.4), (-0.84, 3.38), (-0.82, 3.78), (-0.96, 3.88), (-1.08, 3.72)], sk)
        A.update(coat=v.p(0.85, 3.0), scarf=v.p(0.24, 1.3), paper=v.p(-1.2, 3.3), hands=v.p(1.08, 3.7), shoe=v.p(0.45, 6.35), trousers=v.p(0.35, 5.6))

    # head
    W, H = 0.74 * u, 1.0 * u
    hx = v.x(0) + head_dx * u
    if sil:
        draw_head_silhouette(L, hx, top + head_dy * u, W, H, char, turn=turn, opts=opts)
    else:
        draw_face(L, hx, top + head_dy * u, W, H, char, face_params, turn=turn, opts=opts)
    A["face"] = (hx + 0.4 * W, top + 0.55 * H)
    A["hair"] = (hx - 0.3 * W, top + 0.05 * H)
    A["_top"] = top
    A["_u"] = u
    return A
