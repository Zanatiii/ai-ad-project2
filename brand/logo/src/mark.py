"""Constructed halftone S mark.

Construction rules (y-up, origin = centre of rotation):
  * Two directions only for straight elements: the slash at +A and its mirror at -A,
    where A = arccos(1/phi) = 51.83 deg (golden angle). Hook tails are horizontal,
    which is the bisector of the two.
  * One centre per half. Hook lines and spine lines are concentric circles around it,
    so line spacing and the hook/spine gap are constant everywhere.
  * Every straight run of a line is tangent to its circle -> no kinks.
  * Line spacing S, dot pitch P, dot diameter D are fixed modules.
  * Teal half = copper half rotated 180 deg.
"""
import math
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

GOLD = (1 + 5 ** 0.5) / 2
A = math.acos(1 / GOLD)
U = np.array([math.cos(A), math.sin(A)])        # slash direction
V = np.array([-math.sin(A), math.cos(A)])       # slash normal (upper-left)
H = -V                                          # perpendicular to the slash, heading into the apex -> right-angle chevrons

P = dict(
    S=15.0,          # line spacing
    P=11.5,          # dot pitch along a line
    D=8.4,           # dot diameter
    NH=8,            # hook lines
    NS=5,            # spine lines
    GAP=1.5,         # hook -> spine gap, in line spacings
    C=(40.0, 220.0), # centre of the copper system
    L=492.0,         # blade tip distance from centre
    E0=0.5,          # first spine line sits E0*S above the slash
    CUT=0.5,         # hook ends sit on the line CUT*S above the slash
    TH1=140.0,       # crescent tip angle (deg)
    TH2=216.0,       # crescent lower tip angle (deg)
    CRES=2.6,        # crescent max thickness, in line spacings
    BLADE=0.52,      # where the blade starts, fraction of tip->apex distance
    TAPER=0.5,       # hook tails shrink linearly to this dot scale
    MELT=(),         # optional dot scale ramp into the crescent (off: uniform dots)
)


def arc_pts(c, r, t0, t1, n=None):
    n = n or max(8, int(abs(t1 - t0) * r / 2))
    t = np.linspace(t0, t1, n)
    return np.column_stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t)])


def arclen(poly):
    return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))])


def along(poly, dist):
    s = arclen(poly)
    return np.column_stack([np.interp(dist, s, poly[:, 0]), np.interp(dist, s, poly[:, 1])])


def fit_dots(poly, pitch):
    """Dots at a uniform pitch with a dot exactly on both ends."""
    L = arclen(poly)[-1]
    n = max(1, int(round(L / pitch)))
    return along(poly, np.linspace(0, L, n + 1))


def geometry(p=P):
    S, NH, NS = p['S'], p['NH'], p['NS']
    C = np.array(p['C'])
    # departure: where a CCW circle heads along -A (down-right) -> angle = -A - 90deg
    phid = math.atan2(H[1], H[0]) - math.pi / 2 + 2 * math.pi   # CCW circle heading along H
    w = np.array([math.cos(phid), math.sin(phid)])
    vh = V @ H                                        # -sin(2A)
    uh = U @ H                                        # cos(2A)
    e0 = p['E0'] * S
    g = p['P'] / 2                                    # apex half gap: centre dots one pitch apart
    # solve rho0 so spine line 0 turns onto the slash-parallel line v.x=e0 exactly at u.x=-g
    # K0 = C + rho w + t H, with v.K0 = e0 -> t = (e0 - v.C - rho v.w)/vh
    # u.K0 = u.C + rho u.w + t uh = -g
    a1 = U @ C + uh * (e0 - V @ C) / vh
    b1 = U @ w - uh * (V @ w) / vh
    rho0 = (-g - a1) / b1
    r_out = rho0 - p['GAP'] * S
    radii_h = [r_out - k * S for k in range(NH)]      # k=0 outermost hook line
    radii_s = [rho0 + j * S for j in range(NS)]
    cut = p['CUT'] * S
    tip = -p['L'] * U
    return dict(C=C, phid=phid, w=w, rho0=rho0, radii_h=radii_h, radii_s=radii_s,
                cut=cut, e0=e0, g=g, tip=tip)


def hook_paths(G, p=P):
    C, phid, cut = G['C'], G['phid'], G['cut']
    paths = []
    for r in G['radii_h']:
        top = C + np.array([0, r])
        t_tail = (V @ top - cut) / math.sin(A)       # horizontal run to the cut line
        tail = np.array([top + np.array([t_tail, 0]), top])
        D = C + r * G['w']
        t_stub = (V @ D - cut) / -(V @ H)
        if t_stub >= 0:
            body = arc_pts(C, r, math.pi / 2, phid)
            stub = np.array([D, D + t_stub * H])
            path = np.vstack([tail, body[1:], stub[1:]])
        else:
            # circle reaches the cut before the departure angle
            # solve v.(C + r(cos t, sin t)) = cut
            vc = V @ C
            amp = r
            base = math.atan2(V[1], V[0])
            t = base + math.acos((cut - vc) / amp)
            t = t if t > math.pi / 2 else t + 2 * math.pi
            path = np.vstack([tail, arc_pts(C, r, math.pi / 2, t)[1:]])
        paths.append((path, float(np.linalg.norm(tail[0] - tail[1]))))
    return paths


def spine_paths(G, p=P):
    C, phid, S = G['C'], G['phid'], p['S']
    out = []
    for j, rho in enumerate(G['radii_s']):
        D = C + rho * G['w']
        lvl = G['e0'] + j * S
        t = (lvl - V @ D) / (V @ H)
        K = D + t * H                                 # chevron corner
        arm = np.vstack([arc_pts(C, rho, math.radians(p['TH1'] - 25), phid), [K]])
        out.append(dict(arm=arm, K=K, rho=rho))
    return out


def leg_dots(G, sp, p=P):
    """Fan of straight lines from each chevron corner to the blade tip. Dots shrink in
    proportion to their distance from the tip (similar-triangle grid), and every line
    lands a dot exactly on its corner and exactly one clearance before the blade."""
    tip = G['tip']
    t_ref = np.linalg.norm(sp[0]['K'] - tip)
    base = p['BLADE'] * t_ref                         # blade base distance from tip
    k = (p['P'] - p['D'] / 2) / t_ref                 # (gap + r) at unit scale
    t_end = base / (1 - k)                            # last dot: t_end - (gap+r)(t_end/t_ref) = base
    dots = []
    for s_ in sp:
        K = s_['K']
        t0 = np.linalg.norm(K - tip)
        dirn = (K - tip) / t0
        q_nom = 1 - p['P'] / t0
        n = max(1, int(round(math.log(t_end / t0) / math.log(q_nom))))
        q = (t_end / t0) ** (1 / n)
        for i in range(1, n + 1):                     # i=0 is the corner, owned by the arm
            t = t0 * q ** i
            dots.append((*(tip + dirn * t), p['D'] / 2 * t / t_ref))
    return dots, base


def blade_poly(G, sp, base, p=P):
    tip = G['tip']
    t_ref = np.linalg.norm(sp[0]['K'] - tip)
    half = p['D'] / 2 * base / t_ref                  # dot radius at the base, for flush edges
    pts = []
    for s_, sgn in ((sp[0], 1), (sp[-1], -1)):
        d = (s_['K'] - tip) / np.linalg.norm(s_['K'] - tip)
        n = np.array([d[1], -d[0]]) * sgn             # outward normal of the fan
        pts.append(tip + d * base + n * half)
    return np.array([tip, pts[0], pts[1]])


def crescent_poly(G, p=P):
    """Lune on the ribbon's outer edge: outer arc = ribbon outer circle from TH1 to TH2,
    inner arc = circle through both tips with thickness CRES*S at the middle."""
    C = G['C']
    Ro = G['radii_s'][-1] + p['D'] / 2
    t1, t2 = math.radians(p['TH1']), math.radians(p['TH2'])
    P1 = C + Ro * np.array([math.cos(t1), math.sin(t1)])
    P2 = C + Ro * np.array([math.cos(t2), math.sin(t2)])
    tm = (t1 + t2) / 2
    Q = C + (Ro - p['CRES'] * p['S']) * np.array([math.cos(tm), math.sin(tm)])
    (ax, ay), (bx, by), (cx, cy) = P1, Q, P2
    dd = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / dd
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / dd
    Ci = np.array([ux, uy])
    Ri = np.linalg.norm(P1 - Ci)
    b1 = math.atan2(*(P1 - Ci)[::-1])
    b2 = math.atan2(*(P2 - Ci)[::-1])
    best = None
    for k in (-1, 0, 1):
        arc = arc_pts(Ci, Ri, b2, b1 + 2 * math.pi * k, 240)
        dq = np.linalg.norm(arc[120] - Q)
        if best is None or dq < best[0]:
            best = (dq, arc)
    outer = arc_pts(C, Ro, t1, t2, 240)
    return np.vstack([outer, best[1][1:-1]]), P1


def clipped_dots(path, blockers, pitch, min_len=0.0, touch=None, touch_d=0.0):
    """Split a path where it meets blockers, then fit dots to each remaining piece so
    every piece starts and ends exactly on a dot. Returns (dots, starts_at_touch)."""
    rest = LineString(path).difference(blockers)
    parts = getattr(rest, 'geoms', [rest])
    out = []
    for g in parts:
        if g.is_empty or g.length < min_len:
            continue
        pts = fit_dots(np.asarray(g.coords), pitch)
        at = touch is not None and abs(touch.distance(Point(pts[0])) - touch_d) < 0.5
        out.append((pts, at))
    return out


def build(p=P):
    G = geometry(p)
    r = p['D'] / 2
    clear = p['P'] - p['D']
    dots = []
    for path, tail in hook_paths(G, p):
        pts = fit_dots(path, p['P'])
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
        k = np.clip(s / tail, 0, 1)
        scale = p['TAPER'] + (1 - p['TAPER']) * k
        dots += [(x, y, r * sc) for (x, y), sc in zip(pts, scale)]
    sp = spine_paths(G, p)
    lune, P1 = crescent_poly(G, p)
    lune_poly = Polygon(lune)
    far = 2000
    tm = math.radians((p['TH1'] + p['TH2']) / 2)
    er = np.array([math.cos(tm), math.sin(tm)])
    et = np.array([-er[1], er[0]])
    C = G['C']
    start = Polygon([C - er * far, C + er * far, C + er * far - et * far, C - er * far - et * far])
    block = unary_union([lune_poly.buffer(r + clear, quad_segs=32), start])
    for s_ in sp:
        for pts, at in clipped_dots(s_['arm'], block, p['P'], min_len=p['P'] * 1.5,
                                    touch=lune_poly, touch_d=r + clear):
            scale = np.ones(len(pts))
            if at:
                m = p['MELT'][:len(pts) - 1]
                scale[:len(m)] = m
            dots += [(x, y, r * sc) for (x, y), sc in zip(pts, scale)]
    ld, base = leg_dots(G, sp, p)
    dots += ld
    solids = [lune, blade_poly(G, sp, base, p)]
    return dict(G=G, dots=dots, solids=solids, spine=sp)
