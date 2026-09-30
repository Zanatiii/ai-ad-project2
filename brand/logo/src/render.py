import sys
import numpy as np
import logo

COLORS = {
    'gradient': dict(
        copper=[('0', '#C9603A'), ('0.55', '#E8845C'), ('1', '#F6B08A')],
        teal=[('0', '#1E9FAC'), ('0.55', '#43C4CB'), ('1', '#79E6E1')],
    ),
    'flat': dict(copper=[('0', '#E5825B'), ('1', '#E5825B')],
                 teal=[('0', '#43C4CB'), ('1', '#43C4CB')]),
    'onlight': dict(
        copper=[('0', '#B9532D'), ('0.55', '#D2693F'), ('1', '#E3845C')],
        teal=[('0', '#0C7F8C'), ('0.55', '#199FAB'), ('1', '#2FB9C1')],
    ),
    'white': dict(copper=[('0', '#FFFFFF'), ('1', '#FFFFFF')],
                  teal=[('0', '#FFFFFF'), ('1', '#FFFFFF')]),
    'black': dict(copper=[('0', '#0E0F12'), ('1', '#0E0F12')],
                  teal=[('0', '#0E0F12'), ('1', '#0E0F12')]),
}


def fmt(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def poly_d(pts):
    return 'M' + ' L'.join(f'{fmt(x)} {fmt(y)}' for x, y in pts) + ' Z'


def half_svg(sp, hk, fill, rot=False):
    tf = (lambda p: -p) if rot else (lambda p: p)
    out = []
    cid = 'clipT' if rot else 'clipC'
    out.append(f'<clipPath id="{cid}"><path d="{poly_d(tf(sp["ribbon"]))}"/></clipPath>')
    out.append(f'<g fill="url(#{fill})">')
    out.append(f'<g clip-path="url(#{cid})">')
    for poly in sp['solids']:
        out.append(f'<path d="{poly_d(tf(poly))}"/>')
    for x, y, r, sg in sp['dots']:
        p = tf(np.array([x, y]))
        out.append(f'<circle cx="{fmt(p[0])}" cy="{fmt(p[1])}" r="{fmt(r)}"/>')
    out.append('</g>')
    for x, y, r, _ in hk['dots']:
        p = tf(np.array([x, y]))
        out.append(f'<circle cx="{fmt(p[0])}" cy="{fmt(p[1])}" r="{fmt(r)}"/>')
    out.append('</g>')
    return '\n'.join(out)


def grad(gid, stops, p0, p1):
    st = ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
            f'x1="{fmt(p0[0])}" y1="{fmt(p0[1])}" x2="{fmt(p1[0])}" y2="{fmt(p1[1])}">{st}</linearGradient>')


def build_svg(mode='gradient', bg='#0E0F12', view=None, size=None):
    sp = logo.build_spine()
    hk = logo.build_hook()
    col = COLORS[mode]
    # copper: deep at blade tip (bottom-left) -> light at hook tail (top-right)
    a0 = logo.ab(-500, 0) + np.array([0, 0])
    a1 = logo.ab(420, 220)
    defs = grad('gC', col['copper'], a0, a1) + grad('gT', col['teal'], -a0, -a1)
    vb = view or (-420, -460, 840, 920)
    w, h = size or (vb[2], vb[3])
    bgr = '' if bg is None else f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="{bg}"/>'
    body = half_svg(sp, hk, 'gC') + '\n' + half_svg(sp, hk, 'gT', rot=True)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="{" ".join(map(str, vb))}"><defs>{defs}</defs>{bgr}\n{body}\n</svg>')


if __name__ == '__main__':
    import cairosvg
    mode = sys.argv[1] if len(sys.argv) > 1 else 'gradient'
    svg = build_svg(mode)
    open('preview.svg', 'w').write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to='preview.png', output_width=1680)
