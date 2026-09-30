"""Export the brand kit into <out>/ ."""
import os, sys
import numpy as np
import cairosvg
import logo, render

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
BOLD = dict(hook_lines=5, spine_lines=4, hook_pitch=19.0, hook_r=1.75)


def bounds():
    sp, hk = logo.build_spine(), logo.build_hook()
    pts = [np.array([[x - r, y - r], [x + r, y + r]]) for x, y, r, _ in sp['dots'] + hk['dots']]
    pts += [sp['ribbon']]
    a = np.vstack(pts)
    a = np.vstack([a, -a])                      # teal half
    return a.min(0), a.max(0)


def view(pad=0.06, square=False):
    lo, hi = bounds()
    w, h = hi - lo
    if square:
        s = max(w, h) * (1 + 2 * pad)
        c = (lo + hi) / 2
        return (round(c[0] - s / 2, 2), round(c[1] - s / 2, 2), round(s, 2), round(s, 2))
    p = max(w, h) * pad
    return (round(lo[0] - p, 2), round(lo[1] - p, 2), round(w + 2 * p, 2), round(h + 2 * p, 2))


def save(name, mode, bg, vb, png_w=None, svg=True):
    s = render.build_svg(mode, bg=bg, view=vb)
    if svg:
        open(f'{OUT}/{name}.svg', 'w').write(s)
    if png_w:
        cairosvg.svg2png(bytestring=s.encode(), write_to=f'{OUT}/{name}.png', output_width=png_w)


DARK = '#0E0F12'
vb = view()
save('s-mark', 'gradient', None, vb, 4096)
save('s-mark-flat', 'flat', None, vb, 4096)
save('s-mark-on-dark', 'gradient', DARK, vb, 4096)
save('s-mark-on-light', 'onlight', '#F4F1EC', vb, 4096)
save('s-mark-white', 'white', None, vb, 4096)
save('s-mark-black', 'black', None, vb, 4096)

# showcase, framed like the reference
lo, hi = bounds()
H = (hi[1] - lo[1]) / 0.56
W = H * 1.6
c = (lo + hi) / 2
save('showcase', 'gradient', DARK, (c[0] - W / 2, c[1] - H / 2, W, H), 3200, svg=False)

# bold variant for avatars / app icons
logo.P.update(BOLD)
vbs = view(pad=0.12, square=True)
save('s-mark-bold', 'gradient', None, vbs, 2048)
save('s-mark-bold-app-icon', 'gradient', DARK, vbs, 1024)
for s in (512, 180, 64):
    svg = render.build_svg('gradient', bg=DARK, view=vbs)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f'{OUT}/s-mark-bold-{s}.png', output_width=s)
print('ok', vb, vbs)
