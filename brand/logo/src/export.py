"""Export the traced S mark. Run trace.py first (needs the reference image)."""
import os, sys
import numpy as np
import cairosvg

T = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trace.npy'), allow_pickle=True).item()
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

PAL = {
    'gradient': dict(copper=('#C9603A', '#E5825B', '#F4AA84'), teal=('#1E9FAC', '#43C4CB', '#78E2DE')),
    'flat': dict(copper=('#E5825B',), teal=('#43C4CB',)),
    'onlight': dict(copper=('#B9532D', '#D8724A'), teal=('#0C7F8C', '#1FA7B2')),
    'white': dict(copper=('#FFFFFF',), teal=('#FFFFFF',)),
    'black': dict(copper=('#0E0F12',), teal=('#0E0F12',)),
}
DARK, LIGHT = '#0E0F12', '#F4F1EC'


def bounds():
    pts = []
    for v in T.values():
        pts += [np.array([[x - r, y - r], [x + r, y + r]]) for x, y, r in v['dots']]
        pts += list(v['solids'])
    a = np.vstack(pts)
    return a.min(0), a.max(0)


def svg(mode, bg, vb):
    defs, groups = '', []
    # gradients run along the slash: deep at the blade tip, light at the far end
    lo, hi = bounds()
    ends = dict(copper=((lo[0], hi[1]), (hi[0], lo[1])), teal=((hi[0], lo[1]), (lo[0], hi[1])))
    for name in ('copper', 'teal'):
        cols = PAL[mode][name]
        if len(cols) == 1:
            fill = cols[0]
        else:
            (x1, y1), (x2, y2) = ends[name]
            stops = ''.join(f'<stop offset="{i / (len(cols) - 1):.2f}" stop-color="{c}"/>' for i, c in enumerate(cols))
            defs += (f'<linearGradient id="g{name}" gradientUnits="userSpaceOnUse" x1="{x1:.1f}" y1="{y1:.1f}" '
                     f'x2="{x2:.1f}" y2="{y2:.1f}">{stops}</linearGradient>')
            fill = f'url(#g{name})'
        g = [f'<g fill="{fill}">']
        g += ['<path d="M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in c) + 'Z"/>' for c in T[name]['solids']]
        g += [f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}"/>' for x, y, r in T[name]['dots']]
        g.append('</g>')
        groups.append('\n'.join(g))
    b = '' if bg is None else f'<rect x="{vb[0]:.1f}" y="{vb[1]:.1f}" width="{vb[2]:.1f}" height="{vb[3]:.1f}" fill="{bg}"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{vb[2]:.0f}" height="{vb[3]:.0f}" '
            f'viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}"><defs>{defs}</defs>{b}\n{"".join(groups)}\n</svg>')


def view(pad, square=False, aspect=None):
    lo, hi = bounds()
    c, (w, h) = (lo + hi) / 2, hi - lo
    if aspect:
        H = h / 0.6
        W = H * aspect
    elif square:
        W = H = max(w, h) * (1 + 2 * pad)
    else:
        W, H = w + 2 * pad * max(w, h), h + 2 * pad * max(w, h)
    return (c[0] - W / 2, c[1] - H / 2, W, H)


def save(name, mode, bg, vb, width, keep_svg=True):
    s = svg(mode, bg, vb)
    if keep_svg:
        open(f'{OUT}/{name}.svg', 'w').write(s)
    cairosvg.svg2png(bytestring=s.encode(), write_to=f'{OUT}/{name}.png', output_width=width)


vb = view(0.06)
save('s-mark', 'gradient', None, vb, 4096)
save('s-mark-flat', 'flat', None, vb, 4096)
save('s-mark-on-dark', 'gradient', DARK, vb, 4096)
save('s-mark-on-light', 'onlight', LIGHT, vb, 4096)
save('s-mark-white', 'white', None, vb, 4096)
save('s-mark-black', 'black', None, vb, 4096)
sq = view(0.1, square=True)
save('s-mark-app-icon', 'gradient', DARK, sq, 1024)
save('showcase', 'gradient', DARK, view(0, aspect=1.6), 3200, keep_svg=False)
