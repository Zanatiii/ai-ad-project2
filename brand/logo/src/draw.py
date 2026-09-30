"""SVG rendering for the constructed S mark."""
import numpy as np
import mark

PALETTES = {
    'gradient': dict(copper=[('0', '#C9603A'), ('0.5', '#E5825B'), ('1', '#F4AA84')],
                     teal=[('0', '#1E9FAC'), ('0.5', '#43C4CB'), ('1', '#78E2DE')]),
    'flat': dict(copper=[('0', '#E5825B')], teal=[('0', '#43C4CB')]),
    'onlight': dict(copper=[('0', '#B9532D'), ('1', '#D8724A')],
                    teal=[('0', '#0C7F8C'), ('1', '#1FA7B2')]),
    'white': dict(copper=[('0', '#FFFFFF')], teal=[('0', '#FFFFFF')]),
    'black': dict(copper=[('0', '#0E0F12')], teal=[('0', '#0E0F12')]),
}
DARK = '#0E0F12'


def f(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def _grad(gid, stops, p0, p1):
    st = ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{f(p0[0])}" y1="{f(-p0[1])}" '
            f'x2="{f(p1[0])}" y2="{f(-p1[1])}">{st}</linearGradient>')


def _half(m, sgn, fill):
    g = [f'<g fill="{fill}">']
    for poly in m['solids']:
        q = sgn * np.asarray(poly)
        g.append('<path d="M' + ' L'.join(f'{f(x)} {f(-y)}' for x, y in q) + 'Z"/>')
    for x, y, r in m['dots']:
        g.append(f'<circle cx="{f(sgn * x)}" cy="{f(-sgn * y)}" r="{f(r)}"/>')
    g.append('</g>')
    return '\n'.join(g)


def bounds(m):
    pts = [np.array([[x - r, y - r], [x + r, y + r]]) for x, y, r in m['dots']]
    pts += [np.asarray(s) for s in m['solids']]
    a = np.vstack(pts)
    a = np.vstack([a, -a])
    return a.min(0), a.max(0)


def view(m, pad=0.06, square=False):
    lo, hi = bounds(m)
    w, h = hi - lo
    if square:
        s = max(w, h) * (1 + 2 * pad)
        c = (lo + hi) / 2
        return (c[0] - s / 2, -c[1] - s / 2, s, s)
    p = max(w, h) * pad
    return (lo[0] - p, -hi[1] - p, w + 2 * p, h + 2 * p)


def svg(m, mode='gradient', bg=DARK, vb=None, size=None, extra=''):
    pal = PALETTES[mode]
    vb = vb or view(m)
    w, h = size or (vb[2], vb[3])
    defs, fills = '', []
    tip = m['G']['tip']
    tail = np.array([abs(tip[0]) * 0.9, abs(tip[1]) * 1.05])
    for name, sgn, gid in (('copper', 1, 'gC'), ('teal', -1, 'gT')):
        stops = pal[name]
        if len(stops) == 1:
            fills.append(stops[0][1])
        else:
            defs += _grad(gid, stops, sgn * tip, sgn * tail)
            fills.append(f'url(#{gid})')
    bgr = '' if bg is None else f'<rect x="{f(vb[0])}" y="{f(vb[1])}" width="{f(vb[2])}" height="{f(vb[3])}" fill="{bg}"/>'
    body = _half(m, 1, fills[0]) + _half(m, -1, fills[1])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(w)}" height="{f(h)}" '
            f'viewBox="{" ".join(f(v) for v in vb)}"><defs>{defs}</defs>{bgr}\n{body}\n{extra}</svg>')


if __name__ == '__main__':
    import cairosvg
    m = mark.build()
    s = svg(m)
    open('v2.svg', 'w').write(s)
    cairosvg.svg2png(bytestring=s.encode(), write_to='v2.png', output_width=1400)
