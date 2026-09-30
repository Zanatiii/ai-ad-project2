"""Export the brand kit into <out>/ ."""
import os, sys
import cairosvg
import mark, draw, construction

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
BOLD = dict(C=(30.0, 230.0), S=25.0, P=19.0, D=14.0, NH=5, NS=3, GAP=1.5)


def save(m, name, mode, bg, vb, png_w, svg=True):
    s = draw.svg(m, mode, bg, vb=vb)
    if svg:
        open(f'{OUT}/{name}.svg', 'w').write(s)
    cairosvg.svg2png(bytestring=s.encode(), write_to=f'{OUT}/{name}.png', output_width=png_w)


m = mark.build()
vb = draw.view(m)
save(m, 's-mark', 'gradient', None, vb, 4096)
save(m, 's-mark-flat', 'flat', None, vb, 4096)
save(m, 's-mark-on-dark', 'gradient', draw.DARK, vb, 4096)
save(m, 's-mark-on-light', 'onlight', '#F4F1EC', vb, 4096)
save(m, 's-mark-white', 'white', None, vb, 4096)
save(m, 's-mark-black', 'black', None, vb, 4096)

lo, hi = draw.bounds(m)
H = (hi[1] - lo[1]) / 0.58
W = H * 1.6
c = (lo + hi) / 2
save(m, 'showcase', 'gradient', draw.DARK, (c[0] - W / 2, -c[1] - H / 2, W, H), 3200, svg=False)

s = construction.build_sheet()
cairosvg.svg2png(bytestring=s.encode(), write_to=f'{OUT}/construction.png', output_width=2400)

p = dict(mark.P); p.update(BOLD)
mb = mark.build(p)
vbs = draw.view(mb, pad=0.12, square=True)
save(mb, 's-mark-bold', 'gradient', None, vbs, 2048)
save(mb, 's-mark-bold-app-icon', 'gradient', draw.DARK, vbs, 1024)
for w in (512, 180, 64):
    cairosvg.svg2png(bytestring=draw.svg(mb, 'gradient', draw.DARK, vb=vbs).encode(),
                     write_to=f'{OUT}/s-mark-bold-{w}.png', output_width=w)
print('ok')
