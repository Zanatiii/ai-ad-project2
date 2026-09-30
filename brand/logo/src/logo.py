"""Procedural rebuild of the halftone 'S' mark.

Coordinates: origin at the rotation centre, y down, units = px of the
original 2000x1493 reference. The teal half is the copper half rotated 180deg.
"""
import math
import numpy as np

PHI = math.radians(52.0)                              # slash angle
D = np.array([math.cos(PHI), -math.sin(PHI)])         # along slash -> top-right
NL = np.array([-math.sin(PHI), -math.cos(PHI)])       # normal -> upper-left


def ab(a, b):
    return a * D + b * NL


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def catmull(pts, n=600, alpha=0.5):
    """Centripetal Catmull-Rom through pts, returns dense polyline."""
    P = np.asarray(pts, float)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    segs = len(P) - 3
    per = max(8, n // segs)
    for i in range(segs):
        p0, p1, p2, p3 = P[i:i + 4]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** alpha
        t2 = t1 + np.linalg.norm(p2 - p1) ** alpha
        t3 = t2 + np.linalg.norm(p3 - p2) ** alpha
        for t in np.linspace(t1, t2, per, endpoint=(i == segs - 1)):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    return np.array(out)


def arclen(poly):
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    return np.concatenate([[0], np.cumsum(seg)])


def resample(poly, n):
    s = arclen(poly)
    t = np.linspace(0, s[-1], n)
    return np.column_stack([np.interp(t, s, poly[:, 0]), np.interp(t, s, poly[:, 1])])


def right_normals(poly):
    """Per-vertex miter normals on the visual right-hand side (y-down)."""
    d = np.diff(poly, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    segn = np.column_stack([-d[:, 1], d[:, 0]])
    n = np.zeros_like(poly)
    n[0], n[-1] = segn[0], segn[-1]
    for i in range(1, len(poly) - 1):
        m = segn[i - 1] + segn[i]
        m /= np.linalg.norm(m)
        n[i] = m / max(0.2, np.dot(m, segn[i]))      # miter length
    return n


def point_at(poly, s, dist):
    return np.column_stack([np.interp(dist, s, poly[:, 0]), np.interp(dist, s, poly[:, 1])])


# --------------------------------------------------------------------------
# Parameters (tuned against the reference)
# --------------------------------------------------------------------------
P = dict(
    tip_len=492.0,      # blade tip distance from centre along the slash
    apex_a=-20.0,       # chevron apex position along slash (copper side)
    cut_b=30.0,         # distance of the hook's end-cuts from the slash
    hook_lines=8,
    hook_pitch=11.6,
    hook_r=1.0,
    spine_lines=7,
    arm_angle=30.0,     # direction the arm enters the apex (deg below horizontal)
    dot_r=0.40,
    dot_rmax=0.80,         # dot radius as fraction of line spacing (open halftone)
    melt=dict(b0=60, bf=-50, bw=100),
    cres=dict(ua=40.0, ub=260.0, melt=2.6),
    W=74.0, horn_len=250.0, blade_w=21.0, neck_len=200.0,
)


def seg_intersect(A, B):
    """First intersection between polylines A and B (index in A, index in B, point)."""
    for i in range(len(A) - 1, 0, -1):
        p, r = A[i - 1], A[i] - A[i - 1]
        q = B[:-1]
        sv = B[1:] - B[:-1]
        den = r[0] * sv[:, 1] - r[1] * sv[:, 0]
        ok = np.abs(den) > 1e-12
        qp = q - p
        t = np.where(ok, (qp[:, 0] * sv[:, 1] - qp[:, 1] * sv[:, 0]) / np.where(ok, den, 1), -1)
        w = np.where(ok, (qp[:, 0] * r[1] - qp[:, 1] * r[0]) / np.where(ok, den, 1), -1)
        hit = np.where(ok & (t >= 0) & (t <= 1) & (w >= 0) & (w <= 1))[0]
        if len(hit):
            j = hit[0]
            return i, j, p + t[j] * r
    return None


def spine_parts():
    """Inner edge E of the spine: curved arm (crescent tip -> apex) and straight leg."""
    V = ab(P['apex_a'], 0.0)
    # final approach into the apex is straight so the chevron corner is crisp
    ang = math.radians(P['arm_angle'])
    adir = np.array([math.cos(ang), math.sin(ang)])
    Q = V - adir * 55
    pts = [(-146, -266), (-158, -208), (-152, -152), (-131, -104), (-99, -63),
           tuple(Q - adir * 18), tuple(Q)]
    curve = catmull(pts, n=500)
    straight = np.linspace(Q, V, 40)[1:]
    arm = np.vstack([curve, straight])
    T = ab(-P['tip_len'], 0.0)
    leg = np.linspace(V, T, 500)
    return arm, leg


def spine_width(u, Lc, Lt):
    """Ribbon outline width: sharp horn -> full ribbon -> concave blade."""
    u = np.asarray(u, float)
    Wm, Lh = P['W'], P['horn_len']
    horn = Wm * smooth(u / Lh)
    xp = np.clip(u - Lc, 0, Lt - Lc)
    Wb = P['blade_w']
    blade = Wb * (1 - xp / (Lt - Lc)) ** 1.15 + (Wm - Wb) * (1 - smooth(xp / P['neck_len']))
    return np.where(u <= Lc, horn, blade)


def line_width(u, Lc, Lt):
    """Width the dot lines are spread over: constant on the arm, converging on the leg."""
    u = np.asarray(u, float)
    return np.where(u <= Lc, P['W'], spine_width(u, Lc, Lt))


def crescent_thickness(u, Lc, Lt):
    """Solid band hugging the outer edge; C1-smooth so the horn has no kinks."""
    c = P['cres']
    u = np.asarray(u, float)
    W = spine_width(u, Lc, Lt)
    return np.where(u <= Lc, W * (1 - smooth((u - c['ua']) / (c['ub'] - c['ua']))), 0.0)


def offset_line(arm, leg, sa, sl, Lc, Lt, f, wfn):
    A = arm + right_normals(arm) * (wfn(sa, Lc, Lt) * f)[:, None]
    B = leg + right_normals(leg) * (wfn(sl, Lc, Lt) * f)[:, None]
    if f == 0:
        return np.vstack([A, B[1:]]), np.concatenate([sa, sl[1:]]), len(A) - 1
    i, j, X = seg_intersect(A, B)
    line = np.vstack([A[:i], X, B[j + 1:]])
    u = np.concatenate([sa[:i], [0.5 * (sa[i - 1] + sl[j + 1])], sl[j + 1:]])
    return line, u, i


def blade_solidity(u, f, Lc):
    m = P['melt']
    return smooth((u - (Lc + m['b0'] - m['bf'] * f)) / m['bw'])


def build_spine():
    arm, leg = spine_parts()
    sa = arclen(arm)
    Lc = sa[-1]
    sl = Lc + arclen(leg)
    Lt = sl[-1]
    K = P['spine_lines']
    h0 = P['W'] / K
    dots = []
    for k in range(K):
        f = (k + 0.5) / K
        line, u_line, ic = offset_line(arm, leg, sa, sl, Lc, Lt, f, line_width)
        ls = arclen(line)
        c = ls[ic]

        def step(cur, sign):
            out = []
            while True:
                u = np.interp(cur, ls, u_line)
                h = float(line_width(u, Lc, Lt)) / K
                cur += sign * max(h, 1.6)
                if cur <= 0 or cur >= ls[-1]:
                    return out
                out.append(cur)
        pos = np.array(sorted(step(c, -1) + [c] + step(c, 1)))
        pts = point_at(line, ls, pos)
        u = np.interp(pos, ls, u_line)
        h = line_width(u, Lc, Lt) / K
        o = f * line_width(u, Lc, Lt)
        W = spine_width(u, Lc, Lt)
        T = crescent_thickness(u, Lc, Lt)
        excess = (W - T) - o                  # distance from the solid band (<0 = inside)
        M = P['cres']['melt'] * h0 * smooth(T / 10) + 1e-3
        rc = np.clip(1 - np.maximum(excess, 0) / M, 0, 1) ** 1.3 * (T > 0.3)
        rb = smooth(blade_solidity(u, f, Lc))
        rho = np.maximum(rc, rb)
        r = h * (P['dot_r'] + (P['dot_rmax'] - P['dot_r']) * rho)
        mm = P['melt']
        in_blade = u > Lc + mm['b0'] + max(0, -mm['bf']) + mm['bw'] + 25
        keep = (o - r < W) & (r > 0.3) & ~in_blade
        for p, rr, sg in zip(pts[keep], r[keep], rho[keep]):
            dots.append((p[0], p[1], rr, sg))

    # outline (clip) and solids
    E, uE, _ = offset_line(arm, leg, sa, sl, Lc, Lt, 0.0, spine_width)
    outer, uO, _ = offset_line(arm, leg, sa, sl, Lc, Lt, 1.0, spine_width)
    ribbon = np.vstack([E, outer[::-1]])

    # blade: everything past the melt cut
    fs = np.linspace(0, 1, 41)
    mm = P['melt']
    lines = [offset_line(arm, leg, sa, sl, Lc, Lt, f, spine_width)[:2] for f in fs]

    def at(lu, u):
        line, uu_ = lu
        return np.array([np.interp(u, uu_, line[:, 0]), np.interp(u, uu_, line[:, 1])])
    ub = np.full_like(fs, Lc + mm['b0'] + max(0, -mm['bf']) + mm['bw'] + 10)
    blade = [np.array([at(l, u) for l, u in zip(lines, ub)])]
    blade.append(outer[uO >= ub[-1]])
    blade.append(E[uE >= ub[0]][::-1])
    solids = [np.vstack(blade)]
    return dict(E=E, outer=outer, ribbon=ribbon, dots=dots, solids=solids)


def hook_curves():
    c = P['cut_b']
    O = [tuple(ab(497, c)), (160, -398), (60, -386), (-20, -364), (-88, -326),
         (-128, -272), (-140, -214), (-128, -160), (-100, -112), (-62, -72), tuple(ab(36, c))]
    I = [tuple(ab(292, c)), (104, -252), (54, -242), (16, -222), (-6, -192),
         (-10, -158), (4, -126), tuple(ab(96, c))]
    return resample(catmull(O, 900), 1200), resample(catmull(I, 900), 1200)


def build_hook():
    O, I = hook_curves()
    K = P['hook_lines']
    dots = []
    for k in range(K):
        f = k / (K - 1)
        # ease the fan: spacing opens toward the tail
        line = O * (1 - f) + I * f
        ls = arclen(line)
        L = ls[-1]
        # target pitch; snap so both ends land exactly on the cuts
        n = max(2, int(round(L / P['hook_pitch'])))
        pos = np.linspace(0, L, n + 1)
        pts = point_at(line, ls, pos)
        t = pos / L                      # 0 = tail (top right), 1 = head (centre)
        r = P['hook_r'] * (2.5 + 2.2 * smooth((t - 0.05) / 0.75))
        r *= (1.0 - 0.12 * f)            # inner lines a touch finer
        for p, rr in zip(pts, r):
            dots.append((p[0], p[1], rr, 0.0))
    return dict(dots=dots, O=O, I=I)
