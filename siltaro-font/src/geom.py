"""Geometry primitives for Siltaro Display.

Everything is built from straight lines and circular / elliptical arcs (exact cubic
approximations), expanded to outlines with a uniform stroke and flat (butt) caps by
Skia, then merged with boolean ops. Font coordinates: y up, baseline 0.
"""
import math

import pathops
from pathops import LineCap, LineJoin, PathOp

KAPPA_SPLIT = math.pi / 2  # arcs are split into segments of at most 90 degrees


class Skel:
    """An open skeleton path made of lines and arcs."""

    def __init__(self):
        self.p = pathops.Path()
        self.cur = None

    def move(self, x, y):
        self.p.moveTo(x, y)
        self.cur = (x, y)
        return self

    def line(self, x, y):
        self.p.lineTo(x, y)
        self.cur = (x, y)
        return self

    def arc(self, cx, cy, rx, ry, a0, a1):
        """Elliptical arc from angle a0 to a1 (degrees, CCW positive; a1 < a0 = clockwise)."""
        a0, a1 = math.radians(a0), math.radians(a1)
        sx, sy = cx + rx * math.cos(a0), cy + ry * math.sin(a0)
        if self.cur is None:
            self.move(sx, sy)
        elif abs(self.cur[0] - sx) > 1e-6 or abs(self.cur[1] - sy) > 1e-6:
            self.line(sx, sy)
        n = max(1, math.ceil(abs(a1 - a0) / KAPPA_SPLIT - 1e-9))
        d = (a1 - a0) / n
        k = 4 / 3 * math.tan(d / 4)
        for i in range(n):
            t0, t1 = a0 + i * d, a0 + (i + 1) * d
            p0 = (cx + rx * math.cos(t0), cy + ry * math.sin(t0))
            p3 = (cx + rx * math.cos(t1), cy + ry * math.sin(t1))
            c1 = (p0[0] - k * rx * math.sin(t0), p0[1] + k * ry * math.cos(t0))
            c2 = (p3[0] + k * rx * math.sin(t1), p3[1] - k * ry * math.cos(t1))
            self.p.cubicTo(*c1, *c2, *p3)
            self.cur = p3
        return self

    def stroke(self, w, miter=20.0):
        out = pathops.Path()
        out.addPath(self.p)
        out.stroke(w, LineCap.BUTT_CAP, LineJoin.MITER_JOIN, miter)
        return simplify(out)


def poly(*pts):
    p = pathops.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def rect(x0, y0, x1, y1):
    return poly((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def ellipse(cx, cy, rx, ry):
    s = Skel().arc(cx, cy, rx, ry, 0, 360)
    s.p.close()
    return s.p


def simplify(p):
    q = pathops.Path()
    q.addPath(p)
    q.simplify(fix_winding=True, keep_starting_points=False)
    return q


def union(*paths):
    """Union in one pass: normalise each shape's winding, then resolve them together."""
    out = pathops.Path()
    for p in paths:
        out.addPath(simplify(p))
    return simplify(out)


def diff(a, b):
    return pathops.op(a, b, PathOp.DIFFERENCE, fix_winding=True)


def inter(a, b):
    return pathops.op(a, b, PathOp.INTERSECTION, fix_winding=True)


def line(x0, y0, x1, y1, w):
    return Skel().move(x0, y0).line(x1, y1).stroke(w)


def ring(cx, cy, rx, ry, w, a0=0, a1=360):
    """A monoline elliptical stroke (full ring, or an open arc with flat cuts)."""
    if a1 - a0 >= 360:
        return diff(ellipse(cx, cy, rx + w / 2, ry + w / 2), ellipse(cx, cy, rx - w / 2, ry - w / 2))
    return Skel().arc(cx, cy, rx, ry, a0, a1).stroke(w)


def fillet(x, y, dx, dy, r):
    """Round an inner (concave) corner at (x, y); (dx, dy) point into the counter."""
    sq = rect(min(x, x + dx * r), min(y, y + dy * r), max(x, x + dx * r), max(y, y + dy * r))
    return diff(sq, ellipse(x + dx * r, y + dy * r, r, r))


def band(p, y0, y1, x0=-5000, x1=5000):
    """Clip to a horizontal band: this is what makes diagonal ends cut flat."""
    return inter(p, rect(x0, y0, x1, y1))


def slash_cut(p, x, y, angle):
    """Remove everything below-right of the line through (x, y) rising at `angle` degrees.
    The brand detail: one thin diagonal slash, always at the same angle."""
    t = math.tan(math.radians(angle))
    far = 4000
    cut = poly((x, y), (x + far, y + far * t), (x + far, y - far), (x - far, y - far), (x - far, y - far * t))
    return diff(p, cut)


def translate(p, dx, dy=0):
    return p.transform(1, 0, 0, 1, dx, dy)


def hermite_side(f, df, t0, t1, n):
    """Cubic segments through f(t) using exact tangents: for variable-width strokes."""
    segs = []
    ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
    for a, b in zip(ts, ts[1:]):
        p0, p3 = f(a), f(b)
        d0, d3 = df(a), df(b)
        h = (b - a) / 3
        segs.append((p0, (p0[0] + d0[0] * h, p0[1] + d0[1] * h), (p3[0] - d3[0] * h, p3[1] - d3[1] * h), p3))
    return segs


def foot_slice(p, angle, which='right'):
    """Slice the foot of a leg cleanly with the brand slash: the cut runs from the foot's
    inner corner on the baseline, rising at `angle`, through the whole leg."""
    strip = inter(p, rect(-5000, 0, 5000, 1))
    comps = [c for c in strip.contours]
    feet = sorted(((c.bounds[0], c.bounds[2]) for c in comps), key=lambda b: b[0])
    x0, x1 = feet[-1] if which == 'right' else feet[0]
    return slash_cut(p, x0, 0, angle)
