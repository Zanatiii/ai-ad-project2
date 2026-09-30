"""Export the brand kit into <out>/ ."""
import os, sys
import cairosvg
import mark3, draw3

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
BOLD = dict(P=14.0, D=11.0, NH=5, NS=5, PS=13.0, DS=10.5)


def save(m, name, mode, bg, vb, w, svg=True):
    s = draw3.svg(m, mode, bg, vb=vb)
    if svg:
        open(f'{OUT}/{name}.svg', 'w').write(s)
    cairosvg.svg2png(bytestring=s.encode(), write_to=f'{OUT}/{name}.png', output_width=w)


m = mark3.build()
vb = draw3.view(m)
for name, mode, bg in (('s-mark', 'gradient', None), ('s-mark-flat', 'flat', None),
                       ('s-mark-on-dark', 'gradient', draw3.DARK), ('s-mark-on-light', 'onlight', '#F4F1EC'),
                       ('s-mark-white', 'white', None), ('s-mark-black', 'black', None)):
    save(m, name, mode, bg, vb, 4096)
lo, hi = draw3.bounds(m)
H = (hi[1] - lo[1]) / 0.58
W = H * 1.6
c = (lo + hi) / 2
save(m, 'showcase', 'gradient', draw3.DARK, (c[0] - W / 2, c[1] - H / 2, W, H), 3200, svg=False)

p = dict(mark3.P); p.update(BOLD)
mb = mark3.build(p)
vbs = draw3.view(mb, 0.12, True)
save(mb, 's-mark-bold', 'gradient', None, vbs, 2048)
save(mb, 's-mark-bold-app-icon', 'gradient', draw3.DARK, vbs, 1024)
for w in (512, 180, 64):
    cairosvg.svg2png(bytestring=draw3.svg(mb, 'gradient', draw3.DARK, vb=vbs).encode(),
                     write_to=f'{OUT}/s-mark-bold-{w}.png', output_width=w)
