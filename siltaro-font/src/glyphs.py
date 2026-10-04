"""Glyph construction for Siltaro Display.

Each glyph is a function of the stroke weight W. Bodies start at x = 0; side bearings
are added at build time. All numbers are design decisions made for this typeface.
"""
import math

from geom import (Skel, band, ellipse, fillet, foot_slice, hermite_side, inter, line, poly, rect,
                  ring, slash_cut, translate, union)
import pathops

CAP = 700
SLASH = 52.0          # the one brand angle: diagonal terminals are sliced at this angle
SB_STRAIGHT, SB_ROUND, SB_DIAG = 72, 44, 18

GLYPHS = {}


def glyph(name, uni=None):
    def deco(fn):
        GLYPHS[name] = (fn, uni)
        return fn
    return deco


class M:
    """Metrics derived from the stroke weight."""

    def __init__(self, W):
        self.W = W
        self.h = W / 2
        self.os = round(W * 0.11)          # overshoot of round forms
        self.r = round(W * 0.25)           # inner corner radius
        self.top = CAP - self.h            # skeleton line of a top bar
        self.bot = self.h                  # skeleton line of a base bar


def cap(p):
    return band(p, 0, CAP)


# ------------------------------------------------------------------ straight letters
@glyph('I', 0x49)
def I_(m):
    return rect(0, 0, m.W, CAP), SB_STRAIGHT, SB_STRAIGHT


@glyph('L', 0x4C)
def L_(m):
    w = 500
    p = Skel().move(m.h, CAP).line(m.h, m.bot).line(w, m.bot).stroke(m.W)
    p = union(cap(p), fillet(m.W, m.W, 1, 1, m.r))
    return p, SB_STRAIGHT, 20


@glyph('T', 0x54)
def T_(m):
    w = 600
    p = union(rect(0, CAP - m.W, w, CAP), rect(w / 2 - m.h, 0, w / 2 + m.h, CAP))
    return p, 18, 18


@glyph('E', 0x45)
def E_(m):
    w = 540
    p = Skel().move(w, m.top).line(m.h, m.top).line(m.h, m.bot).line(w, m.bot).stroke(m.W)
    p = union(p, rect(m.W - 1, 350 - m.h, w - 40, 350 + m.h),
              fillet(m.W, CAP - m.W, 1, -1, m.r), fillet(m.W, m.W, 1, 1, m.r))
    return p, SB_STRAIGHT, 40


@glyph('F', 0x46)
def F_(m):
    w = 525
    p = Skel().move(w, m.top).line(m.h, m.top).line(m.h, -10).stroke(m.W)
    p = union(cap(p), rect(m.W - 1, 340 - m.h, w - 50, 340 + m.h), fillet(m.W, CAP - m.W, 1, -1, m.r))
    return p, SB_STRAIGHT, 30


@glyph('H', 0x48)
def H_(m):
    w = 620
    p = union(rect(0, 0, m.W, CAP), rect(w - m.W, 0, w, CAP), rect(m.W - 1, 350 - m.h, w - m.W + 1, 350 + m.h))
    return p, SB_STRAIGHT, SB_STRAIGHT


@glyph('N', 0x4E)
def N_(m):
    w = 640
    d = line(m.h, CAP + 40, w - m.h, -40, m.W)
    p = union(rect(0, 0, m.W, CAP), rect(w - m.W, 0, w, CAP), d)
    return cap(inter(p, rect(0, 0, w, CAP))), SB_STRAIGHT, SB_STRAIGHT


@glyph('K', 0x4B)
def K_(m):
    w = 590
    j = 330                                   # where the arms meet the stem
    arms = Skel().move(w - 30, CAP + 60).line(m.W - 10, j).line(w + 30, -60).stroke(m.W)
    p = cap(union(rect(0, 0, m.W, CAP), arms))
    p = inter(p, rect(0, 0, w, CAP))
    p = foot_slice(p, SLASH)                  # the lower leg is a '\' landing on the baseline
    return p, SB_STRAIGHT, SB_DIAG


# ------------------------------------------------------------------ diagonal letters
def chevron(m, w, up=True, pointed=True):
    """Λ (up) or V (down): two legs meeting in an apex.
    pointed: the outer miter is the apex, overshooting the cap height like a round form."""
    half = math.atan2(w / 2, CAP)                       # half-angle of the apex
    tip = m.h / math.sin(half)                          # outer miter beyond the skeleton apex
    if up:
        ya = CAP + m.os - tip if pointed else CAP + 140
        s = Skel().move(0, -60).line(w / 2, ya).line(w, -60)
        p = band(s.stroke(m.W, miter=80), 0, CAP + m.os if pointed else CAP)
    else:
        ya = -m.os + tip if pointed else -140
        s = Skel().move(0, CAP + 60).line(w / 2, ya).line(w, CAP + 60)
        p = band(s.stroke(m.W, miter=80), -m.os if pointed else 0, CAP)
    b = p.bounds
    return translate(p, -b[0]), b[2] - b[0]


@glyph('A', 0x41)
def A_(m):
    p, w = chevron(m, 660, up=True)
    # the right leg is a '\' landing on the baseline: sliced clean through by the brand slash
    p = foot_slice(p, SLASH)
    return p, SB_DIAG, SB_DIAG


@glyph('V', 0x56)
def V_(m):
    p, w = chevron(m, 660, up=False)
    return p, SB_DIAG, SB_DIAG


@glyph('W', 0x57)
def W_(m):
    """Two chevrons sharing a pointed middle apex; all vertices overshoot like the A and V."""
    w = 920
    q = w / 4
    half = math.atan2(q, CAP)                     # each leg spans one quarter of the width
    tip = m.h / math.sin(half)
    lo, hi = -m.os + tip, CAP + m.os - tip
    s = Skel().move(-q / 2, CAP + CAP / 2).line(q, lo).line(2 * q, hi).line(3 * q, lo).line(4 * q + q / 2, CAP + CAP / 2)
    p = band(s.stroke(m.W, miter=80), -m.os, CAP + m.os)
    # outer arms end flat at the cap height; only the middle apex overshoots
    p = inter(p, union(rect(-500, -100, 2000, CAP), rect(2 * q - 150, CAP - 10, 2 * q + 150, CAP + 100)))
    b = p.bounds
    return translate(p, -b[0]), SB_DIAG, SB_DIAG


@glyph('Y', 0x59)
def Y_(m):
    w, j = 620, 320
    arms = Skel().move(-10, CAP + 40).line(w / 2, j).line(w + 10, CAP + 40).stroke(m.W, miter=50)
    p = cap(union(arms, rect(w / 2 - m.h, 0, w / 2 + m.h, j + 10)))
    b = p.bounds
    return translate(p, -b[0]), SB_DIAG, SB_DIAG


# ------------------------------------------------------------------ round letters
def o_metrics(m):
    R = CAP / 2 + m.os               # outer radius: a perfect circle with overshoot
    return R, R - m.h, CAP / 2       # outer radius, skeleton radius, centre y


@glyph('O', 0x4F)
def O_(m):
    R, rs, cy = o_metrics(m)
    return ring(R, cy, rs, rs, m.W), SB_ROUND, SB_ROUND


@glyph('C', 0x43)
def C_(m):
    R, rs, cy = o_metrics(m)
    return ring(R, cy, rs, rs, m.W, 42, 318), SB_ROUND, 30


@glyph('G', 0x47)
def G_(m):
    R, rs, cy = o_metrics(m)
    arc = ring(R, cy, rs, rs, m.W, 42, 380)             # runs past 0 deg into the bar ...
    bar = rect(R + 30, cy - m.h, 2 * R, cy + m.h)       # ... a bar centred on the centre line
    p = union(arc, bar)
    # ... and is trimmed flush with the bar's top edge
    p = inter(p, union(rect(-100, -100, 2 * R + 100, cy + m.h), rect(-100, cy + 140, 2 * R + 100, 900),
                       rect(-100, -100, R + 30, 900)))
    p = inter(p, ellipse(R, cy, R, R))                  # the bar ends exactly on the outer circle
    return p, SB_ROUND, SB_ROUND


@glyph('U', 0x55)
def U_(m):
    w = 620
    rs = (w - m.W) / 2
    yc = -m.os + m.h + rs
    p = Skel().move(m.h, CAP).line(m.h, yc).arc(w / 2, yc, rs, rs, 180, 360).line(w - m.h, CAP).stroke(m.W)
    return p, SB_STRAIGHT, SB_STRAIGHT


def two_bowls(m, rxu, rxl, ryu=146):
    """S / 8 / 3 skeleton: two stacked ellipses that meet tangentially on a spine."""
    top, bot = CAP + m.os - m.h, -m.os + m.h
    ryl = (top - bot) / 2 - ryu
    yu, yl = top - ryu, bot + ryl
    return yu, ryu, yl, ryl


@glyph('S', 0x53)
def S_(m):
    rxu, rxl = 214, 230
    yu, ryu, yl, ryl = two_bowls(m, rxu, rxl)
    cx = rxl + m.h
    s = Skel().arc(cx, yu, rxu, ryu, 28, 270).arc(cx, yl, rxl, ryl, 90, -152)
    return s.stroke(m.W), SB_ROUND, SB_ROUND


# ------------------------------------------------------------------ bowl letters
def bowl(m, x0, ytop, ybot, right):
    """A D-shaped bowl from the stem: top bar, half circle, bottom bar."""
    r = (ytop - ybot) / 2
    xa = right - m.h - r
    return Skel().move(x0, ytop).line(xa, ytop).arc(xa, ybot + r, r, r, 90, -90).line(x0, ybot).stroke(m.W), xa


@glyph('P', 0x50)
def P_(m):
    b, _ = bowl(m, m.h, m.top, 300, 575)
    p = union(rect(0, 0, m.W, CAP), b, fillet(m.W, CAP - m.W, 1, -1, m.r))
    return p, SB_STRAIGHT, SB_ROUND


@glyph('R', 0x52)
def R_(m):
    b, xa = bowl(m, m.h, m.top, 320, 575)
    leg = band(line(xa - 70, 320, xa + 210, -40, m.W), 0, 320)
    p = union(rect(0, 0, m.W, CAP), b, leg, fillet(m.W, CAP - m.W, 1, -1, m.r))
    p = foot_slice(p, SLASH)
    return p, SB_STRAIGHT, SB_DIAG


@glyph('R.ss01')
def R_ss01(m):
    """The signature R: the leg becomes a long tail sweeping below the baseline to a hairline."""
    b, xa = bowl(m, m.h, m.top, 320, 575)
    P = [(xa - 60, 320), (xa + 60, 150), (xa + 230, -150), (xa + 760, -170)]

    def c(t):
        u = 1 - t
        return (u**3 * P[0][0] + 3 * u * u * t * P[1][0] + 3 * u * t * t * P[2][0] + t**3 * P[3][0],
                u**3 * P[0][1] + 3 * u * u * t * P[1][1] + 3 * u * t * t * P[2][1] + t**3 * P[3][1])

    def dc(t):
        u = 1 - t
        return (3 * u * u * (P[1][0] - P[0][0]) + 6 * u * t * (P[2][0] - P[1][0]) + 3 * t * t * (P[3][0] - P[2][0]),
                3 * u * u * (P[1][1] - P[0][1]) + 6 * u * t * (P[2][1] - P[1][1]) + 3 * t * t * (P[3][1] - P[2][1]))

    def half(t):                        # half width: full stroke, tapering to a hairline point
        return m.h * (1 - t) ** 0.85 if t < 1 else 0.0

    def side(sign):
        def f(t):
            x, y = c(t)
            dx, dy = dc(t)
            L = math.hypot(dx, dy)
            return (x - sign * dy / L * half(t), y + sign * dx / L * half(t))

        def df(t, e=1e-4):
            a, b = f(max(0, t - e)), f(min(1, t + e))
            return ((b[0] - a[0]) / (2 * e), (b[1] - a[1]) / (2 * e))
        return f, df

    tail = pathops.Path()
    fl, dfl = side(1)
    fr, dfr = side(-1)
    segs_l = hermite_side(fl, dfl, 0, 0.999, 8)
    segs_r = hermite_side(fr, dfr, 0, 0.999, 8)
    tail.moveTo(*segs_l[0][0])
    for _, c1, c2, p3 in segs_l:
        tail.cubicTo(*c1, *c2, *p3)
    tail.lineTo(*c(1.0))
    tail.lineTo(*segs_r[-1][3])
    for p0, c1, c2, _ in reversed(segs_r):
        tail.cubicTo(*c2, *c1, *p0)
    tail.close()
    tail = band(tail, -400, 320)
    p = union(rect(0, 0, m.W, CAP), b, tail, fillet(m.W, CAP - m.W, 1, -1, m.r))
    return p, SB_STRAIGHT, SB_DIAG, 575 + SB_DIAG     # explicit advance body: tail overhangs


@glyph('B', 0x42)
def B_(m):
    ym = 372
    up, _ = bowl(m, m.h, m.top, ym, 530)
    lo, _ = bowl(m, m.h, ym, m.bot, 575)
    p = union(rect(0, 0, m.W, CAP), up, lo, fillet(m.W, CAP - m.W, 1, -1, m.r), fillet(m.W, m.W, 1, 1, m.r))
    return p, SB_STRAIGHT, SB_ROUND


# ------------------------------------------------------------------ figures
@glyph('zero', 0x30)
def zero(m):
    """A stadium: tall, so it never reads as the perfectly circular O."""
    w = 520
    r = (w - m.W) / 2
    yt, yb = CAP + m.os - m.h - r, -m.os + m.h + r
    s = Skel().move(m.h, yb).line(m.h, yt).arc(w / 2, yt, r, r, 180, 0).line(w - m.h, yb).arc(w / 2, yb, r, r, 0, -180)
    outer = Skel().move(0, yb).line(0, yt).arc(w / 2, yt, r + m.h, r + m.h, 180, 0).line(w, yb).arc(w / 2, yb, r + m.h, r + m.h, 0, -180)
    inner = Skel().move(m.W, yb).line(m.W, yt).arc(w / 2, yt, r - m.h, r - m.h, 180, 0).line(w - m.W, yb).arc(w / 2, yb, r - m.h, r - m.h, 0, -180)
    outer.p.close()
    inner.p.close()
    from geom import diff
    return diff(outer.p, inner.p), SB_ROUND, SB_ROUND


@glyph('one', 0x31)
def one(m):
    x = 190
    flag = line(x + m.h, CAP - 20, 0, CAP - 200, m.W)
    p = union(rect(x, 0, x + m.W, CAP), band(flag, CAP - 260, CAP))
    p = inter(p, rect(0, 0, x + m.W, CAP))
    return p, 40, SB_STRAIGHT


@glyph('two', 0x32)
def two(m):
    """Arc, then a straight diagonal leaving it tangentially, then the base bar."""
    w = 530
    r = 200
    cx, cy = w / 2, CAP + m.os - m.h - r
    ex, ey = m.h + 6, m.bot                      # where the diagonal lands
    d = math.hypot(ex - cx, ey - cy)
    base = math.atan2(ey - cy, ex - cx)
    a = math.degrees(base + math.acos(r / d))    # tangent point on the right-hand side
    s = Skel().arc(cx, cy, r, r, 165, a).line(ex, ey).line(w, m.bot)
    return s.stroke(m.W, miter=8), SB_ROUND, 30


@glyph('three', 0x33)
def three(m):
    rxu, rxl = 176, 200
    yu, ryu, yl, ryl = two_bowls(m, rxu, rxl)
    cx = rxl + m.h + 20
    ym = yu - ryu
    p = union(Skel().arc(cx, yu, rxu, ryu, 160, -90).stroke(m.W),
              Skel().arc(cx, yl, rxl, ryl, 90, -158).stroke(m.W),
              rect(cx - 110, ym - m.h, cx + 1, ym + m.h))
    b = p.bounds
    return translate(p, -b[0]), SB_ROUND, SB_ROUND


@glyph('four', 0x34)
def four(m):
    w, xs, yb = 560, 400, 210
    d = line(xs + m.h, CAP + 30, -20, yb - 60, m.W)
    p = union(rect(xs, 0, xs + m.W, CAP), rect(0, yb - m.h, w, yb + m.h), band(d, yb, CAP))
    p = inter(p, rect(0, 0, w, CAP))
    return p, SB_DIAG, 40


@glyph('five', 0x35)
def five(m):
    w = 520
    xs = 40
    ry = 172
    yc = -m.os + m.h + ry
    rx = 200
    cx = w - m.h - rx
    s = Skel().move(w - 20, m.top).line(xs + m.h, m.top).line(xs + m.h, yc + ry).line(cx, yc + ry)
    s.arc(cx, yc, rx, ry, 90, -150)
    return s.stroke(m.W, miter=8), SB_ROUND, SB_ROUND


def six_paths(m):
    w = 520
    r = (w - m.W) / 2
    cx, cy = w / 2, -m.os + m.h + r
    bowl_ = ring(cx, cy, r, r, m.W)
    # a straight stroke tangent to the bowl's left side, rising to the cap height
    ex, ey = cx + 150, CAP + 200
    d = math.hypot(ex - cx, ey - cy)
    ang = math.atan2(ey - cy, ex - cx) + math.acos(r / d)
    tx, ty = cx + r * math.cos(ang), cy + r * math.sin(ang)
    stem = band(line(tx, ty, ex, ey, m.W), cy, CAP)
    return union(bowl_, stem)


@glyph('six', 0x36)
def six(m):
    p = six_paths(m)
    b = p.bounds
    return translate(p, -b[0]), SB_ROUND, SB_ROUND


@glyph('nine', 0x39)
def nine(m):
    p = six_paths(m)
    q = p.transform(-1, 0, 0, -1, 0, CAP)
    b = q.bounds
    return translate(q, -b[0]), SB_ROUND, SB_ROUND


@glyph('seven', 0x37)
def seven(m):
    w = 520
    s = Skel().move(0, m.top).line(w - 50, m.top).line(130, -120)
    p = cap(s.stroke(m.W, miter=8))
    return p, 30, SB_DIAG


@glyph('eight', 0x38)
def eight(m):
    rxu, rxl = 178, 204
    yu, ryu, yl, ryl = two_bowls(m, rxu, rxl)
    cx = rxl + m.h
    return union(ring(cx, yu, rxu, ryu, m.W), ring(cx, yl, rxl, ryl, m.W)), SB_ROUND, SB_ROUND


# ------------------------------------------------------------------ punctuation
@glyph('period', 0x2E)
def period(m):
    return rect(0, 0, m.W, m.W), 60, 60


@glyph('space', 0x20)
def space(m):
    return pathops.Path(), 0, 0, 250
