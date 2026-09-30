"""S mark v3: the original's curves (traced), rebuilt with an ordered dot system.

Coordinates: origin at the centre of rotation, y down, units = px of the 2000px reference.
Teal half = copper half rotated 180 deg.
"""
import sys
import os
import numpy as np
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import LineString, Polygon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logo  # noqa: E402  (traced curves + geometry helpers)
from logo import smooth, arclen, resample, right_normals, catmull  # noqa: E402

P = dict(
    P=11.5,          # dot pitch along a line
    D=8.4,           # dot diameter
    SH=16.0,         # hook line spacing
    NH=8,            # hook lines
    SS=12.0,         # spine line spacing
    NS=7,            # spine lines
    CUT=30.0,        # hook ends sit on the line CUT px from the slash
    TAPER=0.5,       # hook tails shrink to this dot scale
    HEAD=(1.1, 1.2, 1.3),           # dot growth into the hook ends at the centre
    APEX=(1.1, 1.2, 1.3),           # dot growth into the chevron corners
    HORN=160.0,      # length of the crescent horn along the arm
    CRES=(125.0, 265.0),              # crescent: solid horn until ua, tapered away by ub
    NECK=220.0,      # leg narrowing length
    BLADE_W=30.0,    # blade width scale
    BLADE_AT=240.0,
    BLADE_IN=18.0,
    LEG_MIN=0.8,     # leg dots never shrink below this scale   # blade starts this far past the corner on the slash side   # blade becomes solid this far down the leg (from the apex)
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
        head = p['HEAD']
        sc[-len(head):] = np.maximum(sc[-len(head):], head)
        out += [(x, y, r * k) for (x, y), k in zip(pts, sc)]
    return out


# ---------------------------------------------------------------- spine
def spine_frame():
    arm, leg = logo.spine_parts()
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
    W0 = ribbon_w(p)
    x = np.clip(np.asarray(u, float) - Lc, 0, Lt - Lc)
    Wb = p['BLADE_W']
    return Wb * (1 - x / (Lt - Lc)) ** 1.15 + (W0 - Wb) * (1 - smooth(x / p['NECK']))


def line_w(p=P):
    def f(u, Lc, Lt):
        u = np.asarray(u, float)
        return np.where(u <= Lc, ribbon_w(p), leg_width(u, Lc, Lt, p))
    return f


def horn_w(p=P):
    def f(u, Lc, Lt):
        u = np.asarray(u, float)
        return np.where(u <= Lc, ribbon_w(p) * smooth(u / p['HORN']), leg_width(u, Lc, Lt, p))
    return f


def crescent(arm, sa, p=P):
    W0 = ribbon_w(p)
    Wh = W0 * smooth(sa / p['HORN'])
    ua, ub = p['CRES']
    T = Wh * (1 - smooth((sa - ua) / (ub - ua)))            # C1-smooth: no kinks
    m = T > 0.05
    N = right_normals(arm)
    r = p['D'] / 2
    Th = (T + r) * smooth(T / (3 * r))                          # thickness, tapers to a point
    outer = arm + N * (Wh + r)[:, None]                         # flush with the dot edges
    inner = arm + N * (Wh + r - Th)[:, None]
    return np.vstack([outer[m], inner[m][::-1]])


def spine(p=P):
    arm, leg, sa, sl, Lc, Lt = spine_frame()
    r = p['D'] / 2
    clear = p['P'] - p['D']
    W0 = ribbon_w(p)
    # crescent traced from the original: outer edge, then inner edge back to the tip
    co = [(-160, -257), (-184, -212), (-199, -168), (-206, -122), (-202, -78), (-186, -38), (-152, -2)]
    ci = [(-152, -2), (-166, -42), (-173, -84), (-173, -128), (-169, -174), (-164, -218), (-160, -257)]
    lune = Polygon(np.vstack([catmull(co, 200), catmull(ci, 200)[1:-1]]))
    left = Polygon(np.vstack([catmull(co, 200), [(-600, 60), (-600, -400)]]))
    block = lune.buffer(r * 0.25, quad_segs=32)
    # the horn outline: lines only exist where the ribbon has grown wide enough
    N = right_normals(arm)
    Wh = W0 * smooth(sa / p['HORN'])
    outline = Polygon(np.vstack([arm, (arm + N * Wh[:, None])[::-1]])).buffer(0.5)
    dots = []
    for j in range(p['NS']):
        f = (j + 0.5) / p['NS']
        line, u, ic = logo.offset_line(arm, leg, sa, sl, Lc, Lt, f, line_w(p))
        # arm: from the top down to the chevron corner, split around the crescent
        armline = line[:ic + 1]
        rest = LineString(armline).intersection(outline).difference(block).difference(left)
        parts = [g for g in getattr(rest, 'geoms', [rest]) if not g.is_empty and g.length > 1.5 * p['P']]
        for k, g in enumerate(parts):
            pts = fit_dots(np.asarray(g.coords), p['P'])
            sc = np.ones(len(pts))
            if k == len(parts) - 1:                       # grow into the corner
                ap = p['APEX']
                sc[-len(ap) - 1:-1] = ap
                sc[-1] = ap[-1]
            dots += [(x, y, r * s) for (x, y), s in zip(pts, sc)]
        # leg: from the corner toward the blade, dots scale with the converging width
        legline, ul = line[ic:], u[ic:]
        ls = arclen(legline)
        end_s = np.interp(Lc + p['BLADE_IN'] + (p['BLADE_AT'] - p['BLADE_IN']) * f, ul, ls)
        pos, cur = [], 0.0
        while True:
            w = max(p['LEG_MIN'], float(leg_width(np.interp(cur, ls, ul), Lc, Lt, p)) / W0)
            cur += p['P'] * w
            if cur - (r + clear) * w >= end_s:
                break
            pos.append(cur)
        if not pos:
            continue
        w_last = max(p['LEG_MIN'], float(leg_width(np.interp(pos[-1], ls, ul), Lc, Lt, p)) / W0)
        target = end_s - (r + clear) * w_last
        pos = np.array(pos) * target / pos[-1]
        ramp = list(p['APEX'][::-1][1:])                # mirror the arm's growth out of the corner
        for i, s_ in enumerate(pos):
            uu = np.interp(s_, ls, ul)
            w = max(p['LEG_MIN'], float(leg_width(uu, Lc, Lt, p)) / W0)
            x, y = np.interp(s_, ls, legline[:, 0]), np.interp(s_, ls, legline[:, 1])
            g = ramp[i] if i < len(ramp) else 1.0
            dots.append((x, y, r * w * g))
    # blade: ribbon outline from the blade cut to the tip
    E, uE, _ = logo.offset_line(arm, leg, sa, sl, Lc, Lt, 0.0, line_w(p))
    Ou, uO, _ = logo.offset_line(arm, leg, sa, sl, Lc, Lt, 1.0, line_w(p))
    fs = np.linspace(0, 1, 30)
    cut = []
    for ff in fs:
        ln, uu, _ = logo.offset_line(arm, leg, sa, sl, Lc, Lt, ff, line_w(p))
        uc = Lc + p['BLADE_IN'] + (p['BLADE_AT'] - p['BLADE_IN']) * ff
        cut.append([np.interp(uc, uu, ln[:, 0]), np.interp(uc, uu, ln[:, 1])])
    cut = np.array(cut)
    u_in = Lc + p['BLADE_IN']
    blade = np.vstack([E[uE >= u_in][::-1], cut, Ou[uO >= p['BLADE_AT'] + Lc]])
    return dots, [np.asarray(lune.exterior.coords), blade]


def build(p=P):
    d1 = hook_dots(p)
    d2, solids = spine(p)
    return dict(dots=d1 + d2, solids=solids)
