"""S mark v3: the original's curves (traced), rebuilt with an ordered dot system.

Coordinates: origin at the centre of rotation, y down, units = px of the 2000px reference.
Teal half = copper half rotated 180 deg.
"""
import json
import sys
import os
import numpy as np
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logo  # noqa: E402  (traced curves + geometry helpers)
from logo import smooth, arclen, resample, right_normals, catmull  # noqa: E402

P = dict(
    P=9.8,           # hook dot pitch (dots nearly touch along a line)
    D=7.6,           # hook dot diameter
    NH=8,            # hook lines
    TAPER=0.5,       # hook tails shrink to this dot scale
    SS=10.5,         # spine line spacing
    NS=8,            # spine lines (clipped to the silhouette)
    PS=9.2,          # spine dot pitch
    DS=7.6,          # spine dot diameter
    CRES=(28.0, 70.0, 250.0),  # crescent band: max thickness, full until, gone by (arc length)
    BLADE_AT=215.0,
    FAIR=10.0,       # smoothing of the traced arm  # blade is solid beyond this distance from the centre along the slash
)


def fit_dots(poly, pitch):
    s = arclen(poly)
    n = max(1, int(round(s[-1] / pitch)))
    t = np.linspace(0, s[-1], n + 1)
    return np.column_stack([np.interp(t, s, poly[:, 0]), np.interp(t, s, poly[:, 1])])


def extend(poly, d=160):
    a = poly[0] + (poly[0] - poly[3]) / np.linalg.norm(poly[0] - poly[3]) * d
    b = poly[-1] + (poly[-1] - poly[-4]) / np.linalg.norm(poly[-1] - poly[-4]) * d
    return np.vstack([np.linspace(a, poly[0], 40)[:-1], poly, np.linspace(poly[-1], b, 40)[1:]])


def cut_to(poly, c):
    """Keep the stretch of poly with NL.p >= c, with exact end points on that line."""
    b = poly @ logo.NL - c
    idx = np.where(b >= 0)[0]
    i0, i1 = idx[0], idx[-1]
    out = poly[i0:i1 + 1]
    if i0 > 0:
        t = b[i0 - 1] / (b[i0 - 1] - b[i0])
        out = np.vstack([poly[i0 - 1] + t * (poly[i0] - poly[i0 - 1]), out])
    if i1 < len(poly) - 1:
        t = b[i1] / (b[i1] - b[i1 + 1])
        out = np.vstack([out, poly[i1] + t * (poly[i1 + 1] - poly[i1])])
    return out


# ---------------------------------------------------------------- hook
def hook_lines(p=P):
    """Original fan: at every cross-section the lines are evenly spaced between the
    outer and inner curve, so spacing opens smoothly toward the tail."""
    O, I = logo.hook_curves()
    return [O * (1 - k / (p['NH'] - 1)) + I * (k / (p['NH'] - 1)) for k in range(p['NH'])]


def hook_dots(p=P):
    r = p['D'] / 2
    out = []
    for line in hook_lines(p):
        pts = fit_dots(line, p['P'])
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
        sc = p['TAPER'] + (1 - p['TAPER']) * np.clip(s / (0.42 * s[-1]), 0, 1)
        out += [(x, y, r * k) for (x, y), k in zip(pts, sc)]
    return out


# ---------------------------------------------------------------- spine
def spine_frame():
    # slash-side edge of the ribbon: crescent -> chevron corner, then straight down the slash
    Vx = logo.ab(logo.P['apex_a'], 0.0)
    ang = np.radians(logo.P['arm_angle'])
    adir = np.array([np.cos(ang), np.sin(ang)])
    Q = Vx - adir * 55
    pts = [(-146, -266), (-156, -208), (-146, -152), (-121, -104), (-86, -64),
           tuple(Q - adir * 18), tuple(Q)]
    arm = np.vstack([catmull(pts, n=500), np.linspace(Q, Vx, 40)[1:]])
    leg = np.linspace(Vx, logo.ab(-logo.P['tip_len'], 0.0), 500)
    # fair the arm: uniform resample + gaussian so offsets far from it stay smooth
    n = int(arclen(arm)[-1])
    arm = resample(arm, n)
    V = arm[-1].copy()
    arm = np.column_stack([gaussian_filter1d(arm[:, 0], 14, mode='nearest'),
                           gaussian_filter1d(arm[:, 1], 14, mode='nearest')])
    arm[-1] = V
    sa = arclen(arm)
    Lc = sa[-1]
    sl = Lc + arclen(leg)
    return arm, leg, sa, sl, Lc, sl[-1]


def ribbon_w(p=P):
    return p['NS'] * p['SS']


def leg_width(u, Lc, Lt, p=P):
    """Leg narrows from the ribbon width to BLADE_W, then the blade tapers to the tip."""
    x = np.clip(np.asarray(u, float) - Lc, 0, Lt - Lc)
    W0, Wb, Ba = ribbon_w(p), p['BLADE_W'], p['BLADE_AT']
    neck = W0 + (Wb - W0) * smooth(x / Ba)
    blade = Wb * np.clip(1 - (x - Ba) / (Lt - Lc - Ba), 0, 1)
    return np.where(x <= Ba, neck, blade)


def arm_width(u, p=P):
    """Ribbon is narrower at the top (under the crescent) and opens to full width."""
    W0 = ribbon_w(p)
    return p['TOP_W'] + (W0 - p['TOP_W']) * smooth(np.asarray(u, float) / p['OPEN'])


def line_w(p=P):
    def f(u, Lc, Lt):
        u = np.asarray(u, float)
        return np.where(u <= Lc, arm_width(u, p), leg_width(u, Lc, Lt, p))
    return f


def crescent(arm, sa, p=P):
    """Horn on the ribbon's outer edge: sharp tip at the top, thickest just under it,
    then tapering along the edge into the dots."""
    r = p['DS'] / 2
    a, b = p['CRES_END']
    T = p['CRES_T'] * smooth(sa / p['CRES_UP']) * (1 - smooth((sa - a) / (b - a)))
    m = T > 0.05
    N = right_normals(arm)
    edge = arm_width(sa, p) * (1 - 0.5 / p['NS']) + r                              # flush with the outer line's dot edges
    outer = arm + N * edge[:, None]
    inner = arm + N * (edge - T)[:, None]
    return np.vstack([outer[m], inner[m][::-1]])


OUTLINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spine_outline.json')


def spine_outline():
    """Crescent + ribbon + blade as one silhouette, traced from the original."""
    return Polygon(json.load(open(OUTLINE)))


def inner_edge(S):
    """The outline's right-hand side: crescent tip -> chevron -> down the slash to the tip."""
    c = np.asarray(S.exterior.coords)[:-1]
    top, tip = np.argmin(c[:, 1]), np.argmax(c[:, 1])
    a = np.roll(c, -top, axis=0)
    k = (tip - top) % len(c)
    h1, h2 = a[:k + 1], np.vstack([a[k:], a[:1]])[::-1]
    return h1 if h1[:, 0].mean() > h2[:, 0].mean() else h2


def outer_edge(S):
    """The outline's left-hand side, from the crescent tip downward."""
    c = np.asarray(S.exterior.coords)[:-1]
    top, tip = np.argmin(c[:, 1]), np.argmax(c[:, 1])
    a = np.roll(c, -top, axis=0)
    k = (tip - top) % len(c)
    h1, h2 = a[:k + 1], np.vstack([a[k:], a[:1]])[::-1]
    o = h2 if h1[:, 0].mean() > h2[:, 0].mean() else h1
    return resample(o, int(arclen(o)[-1]))


def fair_edge(e, p=P):
    """Smooth the traced arm, keep the chevron corner sharp, and make the leg an exact
    straight line along the slash to the blade tip."""
    e = resample(e, int(arclen(e)[-1]))
    ic = corner_index(e)
    arm, tip = e[:ic + 1], e[-1]
    sm = np.column_stack([gaussian_filter1d(arm[:, 0], p['FAIR'], mode='nearest'),
                          gaussian_filter1d(arm[:, 1], p['FAIR'], mode='nearest')])
    w = smooth(np.linspace(0, 1, len(arm)) * 12)          # pin the start
    w = np.minimum(w, smooth((1 - np.linspace(0, 1, len(arm))) * 12))  # and the corner
    arm = arm * (1 - w[:, None]) + sm * w[:, None]
    leg = np.linspace(arm[-1], tip, 400)[1:]
    return np.vstack([arm, leg])


def corner_index(e):
    """Concave corner on the outer edge: right-most point below the crescent."""
    lo = len(e) // 3
    return lo + int(np.argmax(e[lo:, 0]))


def dedupe(dots, min_d):
    out = []
    for d in dots:
        if all((d[0] - q[0]) ** 2 + (d[1] - q[1]) ** 2 >= min_d ** 2 for q in out[-400:]):
            out.append(d)
    return out


def spine(p=P):
    S = spine_outline()
    r = p['DS'] / 2
    # solid zones: crescent (top of the silhouette) and blade (far end along the slash)
    U = np.array([np.cos(np.radians(51.8)), -np.sin(np.radians(51.8))])
    far = 2000
    # crescent: a band along the outer edge, full width at the tip, tapering into the dots
    O = outer_edge(S)
    so = arclen(O)
    Tm, a, b = p['CRES']
    T = Tm * (1 - smooth((so - a) / (b - a)))
    keep = T > 0.3
    cres_zone = unary_union([Point(x, y).buffer(t, quad_segs=8) for (x, y), t in zip(O[keep][::2], T[keep][::2])])
    B = -U * p['BLADE_AT']
    n = np.array([U[1], -U[0]])
    blade_zone = Polygon([B + n * far, B - n * far, B - n * far - U * far, B + n * far - U * far])
    solids = [S.intersection(cres_zone), S.intersection(blade_zone)]
    solids = [max(getattr(g, 'geoms', [g]), key=lambda q: q.area) for g in solids]
    block = unary_union([g.buffer(-r * 2.5) for g in solids])   # dots overlap the solid edge: fused
    # fan: every line runs between the faired inner and outer edge, evenly spaced across
    Ei = fair_edge(inner_edge(S), p)
    Eo = fair_edge(outer_edge(S), p)
    ci, co = corner_index(Ei), corner_index(Eo)
    def stations(e, c, n1, n2):
        return np.vstack([resample(e[:c + 1], n1), resample(e[c:], n2)[1:]])
    n1, n2 = 600, 600
    A, B = stations(Ei, ci, n1, n2), stations(Eo, co, n1, n2)
    dots = []
    for j in range(p['NS']):
        t = (j + 0.5) / p['NS']
        line = LineString(A * (1 - t) + B * t).difference(block)
        for q in getattr(line, 'geoms', [line]):
            if q.is_empty or q.length < p['PS']:
                continue
            dots += [(x, y, r) for x, y in fit_dots(np.asarray(q.coords), p['PS'])]
    inside = S.buffer(-r * 0.95)
    solid = unary_union(solids)
    dots = [d for d in dots if inside.contains(Point(d[0], d[1])) and not solid.buffer(-r * 0.9).contains(Point(d[0], d[1]))]
    dots = dedupe(dots, p['DS'] * 0.95)
    solids = [g.buffer(3).buffer(-3) for g in solids]                       # clean edges
    return dots, [np.asarray(g.exterior.coords) for g in solids]


def build(p=P):
    d1 = hook_dots(p)
    d2, solids = spine(p)
    return dict(dots=d1 + d2, solids=solids)
