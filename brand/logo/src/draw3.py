import numpy as np
import cairosvg
import mark3
import logo

PAL = {
    'gradient': dict(copper=[('0', '#C9603A'), ('0.5', '#E5825B'), ('1', '#F4AA84')],
                     teal=[('0', '#1E9FAC'), ('0.5', '#43C4CB'), ('1', '#78E2DE')]),
    'flat': dict(copper=[('0', '#E5825B')], teal=[('0', '#43C4CB')]),
    'onlight': dict(copper=[('0', '#B9532D'), ('1', '#D8724A')], teal=[('0', '#0C7F8C'), ('1', '#1FA7B2')]),
    'white': dict(copper=[('0', '#FFFFFF')], teal=[('0', '#FFFFFF')]),
    'black': dict(copper=[('0', '#0E0F12')], teal=[('0', '#0E0F12')]),
}
DARK = '#0E0F12'


def f(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def bounds(m):
    pts = [np.array([[x - r, y - r], [x + r, y + r]]) for x, y, r in m['dots']] + [np.asarray(s) for s in m['solids']]
    a = np.vstack(pts)
    a = np.vstack([a, -a])
    return a.min(0), a.max(0)


def view(m, pad=0.06, square=False):
    lo, hi = bounds(m)
    w, h = hi - lo
    if square:
        s = max(w, h) * (1 + 2 * pad)
        c = (lo + hi) / 2
        return (c[0] - s / 2, c[1] - s / 2, s, s)
    q = max(w, h) * pad
    return (lo[0] - q, lo[1] - q, w + 2 * q, h + 2 * q)


def svg(m, mode='gradient', bg=DARK, vb=None, size=None):
    vb = vb or view(m)
    w, h = size or (vb[2], vb[3])
    p0, p1 = logo.ab(-500, 0), logo.ab(430, 200)
    defs, fills = '', []
    for name, sgn, gid in (('copper', 1, 'gC'), ('teal', -1, 'gT')):
        st = PAL[mode][name]
        if len(st) == 1:
            fills.append(st[0][1]); continue
        a, b = sgn * p0, sgn * p1
        stops = ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in st)
        defs += (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{f(a[0])}" y1="{f(a[1])}" '
                 f'x2="{f(b[0])}" y2="{f(b[1])}">{stops}</linearGradient>')
        fills.append(f'url(#{gid})')
    body = []
    for sgn, fill in ((1, fills[0]), (-1, fills[1])):
        g = [f'<g fill="{fill}">']
        for poly in m['solids']:
            g.append('<path d="M' + ' L'.join(f'{f(sgn*x)} {f(sgn*y)}' for x, y in poly) + 'Z"/>')
        g += [f'<circle cx="{f(sgn*x)}" cy="{f(sgn*y)}" r="{f(r)}"/>' for x, y, r in m['dots']]
        g.append('</g>')
        body.append('\n'.join(g))
    bgr = '' if bg is None else f'<rect x="{f(vb[0])}" y="{f(vb[1])}" width="{f(vb[2])}" height="{f(vb[3])}" fill="{bg}"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(w)}" height="{f(h)}" viewBox="{" ".join(f(v) for v in vb)}">'
            f'<defs>{defs}</defs>{bgr}{"".join(body)}</svg>')


if __name__ == '__main__':
    from PIL import Image
    m = mark3.build()
    cairosvg.svg2png(bytestring=svg(m).encode(), write_to='v3.png', output_width=1400)
    ov = svg(m, 'flat', None, vb=(-995, -755, 2000, 1493), size=(2000, 1493))
    cairosvg.svg2png(bytestring=ov.encode(), write_to='ov.png')
    ref = np.asarray(Image.open('../../images/1.jpg').convert('RGB')).astype(float)
    lay = np.asarray(Image.open('ov.png').convert('RGBA')).astype(float)
    g = ref.mean(-1, keepdims=True) * 0.9
    al = lay[..., 3:4] / 255 * 0.55
    mix = np.repeat(g, 3, -1) * (1 - al) + np.array([255, 60, 200]) * al
    Image.fromarray(mix.clip(0, 255).astype(np.uint8)).crop((650, 320, 1350, 1200)).save('overlay.png')
    o = Image.open('../../images/1.jpg').convert('RGB').crop((650, 320, 1350, 1200))
    n = Image.open('v3.png').convert('RGB'); n = n.resize((int(880 * n.width / n.height), 880))
    s = Image.new('RGB', (720 + n.width, 880), (14, 15, 18)); s.paste(o, (0, 0)); s.paste(n, (720, 0)); s.save('side.png')
