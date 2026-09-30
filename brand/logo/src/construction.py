"""Construction sheet: the mark with its geometry drawn on top."""
import math
import numpy as np
import mark
import draw

INK = '#FFFFFF'
ACC = '#F4AA84'
FONT = "font-family='DejaVu Sans Mono, monospace'"


def P(pt):
    return f'{pt[0]:.2f},{-pt[1]:.2f}'


def line(a, b, op=0.28, w=1.0, dash=None, col=INK):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{a[0]:.2f}" y1="{-a[1]:.2f}" x2="{b[0]:.2f}" y2="{-b[1]:.2f}" '
            f'stroke="{col}" stroke-opacity="{op}" stroke-width="{w}"{d}/>')


def circle(c, r, op=0.14, w=0.8, col=INK, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<circle cx="{c[0]:.2f}" cy="{-c[1]:.2f}" r="{r:.2f}" fill="none" '
            f'stroke="{col}" stroke-opacity="{op}" stroke-width="{w}"{d}/>')


def text(pt, s, size=11, op=0.75, anchor='start', col=INK):
    return (f"<text x='{pt[0]:.2f}' y='{-pt[1]:.2f}' {FONT} font-size='{size}' fill='{col}' "
            f"fill-opacity='{op}' text-anchor='{anchor}'>{s}</text>")


def build_sheet():
    m = mark.build()
    G, p = m['G'], mark.P
    U, V = mark.U, mark.V
    C = G['C']
    far = 620
    g = []
    # primary axes
    g.append(line(-far * U, far * U, op=0.45, w=1.1))
    g.append(line(-far * V, far * V, op=0.22, dash='4 5'))
    g.append(line(np.array([-far, 0]), np.array([far, 0]), op=0.22, dash='4 5'))
    # cut lines: s/2 either side of the slash
    for sgn in (1, -1):
        off = sgn * G['cut'] * V
        g.append(line(off - far * U, off + far * U, op=0.25, dash='2 4'))
    for sgn in (1, -1):
        c = sgn * C
        for r in G['radii_h'] + G['radii_s']:
            g.append(circle(c, r))
        # the line through the centre parallel to the slash: every line turns straight here
        g.append(line(c - 330 * U, c + 330 * U, op=0.3, dash='6 4', col=ACC))
        # spine start radius
        tm = math.radians((p['TH1'] + p['TH2']) / 2) + (math.pi if sgn < 0 else 0)
        er = np.array([math.cos(tm), math.sin(tm)])
        g.append(line(c, c + er * (G['radii_s'][-1] + 30), op=0.4, dash='3 3', col=ACC))
        g.append(f'<circle cx="{c[0]:.2f}" cy="{-c[1]:.2f}" r="3.2" fill="{ACC}"/>')
    g.append(text(C + np.array([10, 8]), 'C', 13, 0.9, col=ACC))
    g.append(text(-C + np.array([10, 8]), "C'", 13, 0.9, col=ACC))
    # angle between horizontal and slash, drawn in the empty space left of centre
    r_arc = 330
    a0 = np.array([-r_arc, 0])
    a1 = -r_arc * U
    g.append(f'<path d="M{P(a0)} A{r_arc},{r_arc} 0 0,0 {P(a1)}" fill="none" stroke="{ACC}" stroke-width="1.2" stroke-opacity="0.85"/>')
    g.append(text(np.array([-r_arc - 14, -92]), '51.83°', 12, 0.95, 'end', col=ACC))
    g.append(text(np.array([-r_arc - 14, -110]), '= arccos(1/φ)', 10, 0.7, 'end', col=ACC))
    # right-angle marker at the copper apex
    K0 = m['spine'][0]['K']
    q = 9
    sq = [K0 + q * (-U), K0 + q * (-U) + q * V, K0 + q * V]
    g.append(f'<polyline points="{" ".join(P(s) for s in sq)}" fill="none" stroke="{ACC}" stroke-width="1.1"/>')
    g.append(text(K0 + np.array([-16, 16]), '90°', 11, 0.9, 'end', col=ACC))
    # labels
    tip = G['tip']
    g.append(text(-tip + np.array([14, -6]), 'slash', 10, 0.6))
    cut_lbl = G['cut'] * V + 575 * U
    g.append(text(cut_lbl + np.array([-8, 6]), 'ends on S/2 offsets', 10, 0.6, 'end'))
    extra = '<g>' + ''.join(g) + '</g>'

    vb0 = draw.view(m, pad=0.1, square=True)
    s_ = vb0[2]
    vb = (vb0[0], vb0[1], s_, s_ * 1.12)
    legend_y = vb0[1] + s_ * 1.0
    lx = vb0[0] + s_ * 0.06
    legend = [
        f"S  line spacing  {p['S']:g}",
        f"P  dot pitch     {p['P']:g}",
        f"D  dot           {p['D']:g}",
        f"gap hook/spine   {p['GAP']:g} S",
        f"lines            {p['NH']} hook / {p['NS']} spine",
        "angles           slash, 90° to slash, 0°",
    ]
    fs = s_ * 0.0122
    leg = ''.join(
        f"<text x='{lx + (i // 3) * s_ * 0.42:.1f}' y='{legend_y + (i % 3) * fs * 1.6:.1f}' {FONT} "
        f"font-size='{fs:.1f}' fill='{INK}' fill-opacity='0.7' xml:space='preserve'>{t}</text>"
        for i, t in enumerate(legend))
    title = (f"<text x='{lx:.1f}' y='{vb0[1] + s_ * 0.05:.1f}' {FONT} font-size='{s_ * 0.018:.1f}' "
             f"fill='{INK}' fill-opacity='0.9'>S MARK / CONSTRUCTION</text>")
    body = draw.svg(m, 'gradient', draw.DARK, vb=vb, extra=extra + leg + title)
    # dim the mark under the guides
    body = body.replace('<g fill="url(#gC)">', '<g fill="url(#gC)" fill-opacity="0.55">')
    body = body.replace('<g fill="url(#gT)">', '<g fill="url(#gT)" fill-opacity="0.55">')
    return body


if __name__ == '__main__':
    import cairosvg
    s = build_sheet()
    cairosvg.svg2png(bytestring=s.encode(), write_to='construction.png', output_width=1800)
