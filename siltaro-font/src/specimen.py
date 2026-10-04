"""Render specimen images straight from the glyph outlines (same data as the font)."""
import os
import cairosvg
import build

UPM = 1000


def text_svg(gl, text, size, x, y, color, alt=None, tracking=0):
    run, _ = build.layout(gl, text, alt)
    s = size / UPM
    parts = []
    for i, (n, gx) in enumerate(run):
        d = build.svg_path(gl[n]['path'])
        if d:
            parts.append(f'<path transform="translate({x + (gx + i * tracking) * s:.2f},{y:.2f}) scale({s:.5f},{-s:.5f})" d="{d}" fill="{color}"/>')
    return ''.join(parts)


def width(gl, text, size, alt=None, tracking=0):
    run, w = build.layout(gl, text, alt)
    return (w + tracking * max(0, len(run) - 1)) * size / UPM


def render(svg_body, W, H, bg, out):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="{bg}"/>{svg_body}</svg>'
    cairosvg.svg2png(bytestring=svg.encode(), write_to=out)


def proof(gl, out):
    names = [n for n in gl if n != 'space']
    cols, cell, size = 9, 300, 200
    rows = (len(names) + cols - 1) // cols
    body = []
    for i, n in enumerate(names):
        cx, cy = (i % cols) * cell, (i // cols) * cell
        s = size / UPM
        base = cy + 240
        body.append(f'<line x1="{cx}" x2="{cx + cell}" y1="{base}" y2="{base}" stroke="#d33" stroke-width="1"/>')
        body.append(f'<line x1="{cx}" x2="{cx + cell}" y1="{base - 700 * s}" y2="{base - 700 * s}" stroke="#39c" stroke-width="1"/>')
        body.append(f'<rect x="{cx + 20}" y="{base - 800 * s}" width="{gl[n]["adv"] * s}" height="{1000 * s}" fill="none" stroke="#bbb"/>')
        d = build.svg_path(gl[n]['path'])
        body.append(f'<path transform="translate({cx + 20},{base}) scale({s},{-s})" d="{d}" fill="#000"/>')
        body.append(f'<text x="{cx + 6}" y="{cy + 290}" font-family="DejaVu Sans" font-size="13" fill="#888">{n}</text>')
    render(''.join(body), cols * cell, rows * cell, '#fff', out)


def phase1(gl, out):
    W = 3000
    lines = [
        ('SILTARO', 300, {}, 40),
        ('SILTARO', 300, {'R': 'R.ss01'}, 40),
        ('SILTARO AI SOLUTIONS', 150, {}, 30),
        ('0123456789', 150, {}, 20),
        ('TURN HOW YOUR BUSINESS WORKS', 95, {}, 12),
        ('INTO INTELLIGENT TECHNOLOGY.', 95, {}, 12),
    ]
    gap = [140, 160, 130, 140, 70, 0]
    labels = ['Regular', 'ss01: tail R', '', 'figures', '', '']
    panels = []
    for bg, fg, mute in (('#FFFFFF', '#000000', '#9aa0a6'), ('#0B0D0F', '#E6E8EB', '#5b6168')):
        y, body = 170, []
        for (t, size, alt, trk), g, lab in zip(lines, gap, labels):
            y += size * 0.7
            x = (W - width(gl, t, size, alt, trk)) / 2
            body.append(text_svg(gl, t, size, x, y, fg, alt, trk))
            if lab:
                body.append(f'<text x="80" y="{y}" font-family="DejaVu Sans" font-size="26" fill="{mute}">{lab}</text>')
            y += g + (size * 0.25 if alt else 0)
        H = int(y + 170)
        panels.append((bg, ''.join(body), H))
    total = sum(h for _, _, h in panels)
    parts, oy = [], 0
    for bg, body, h in panels:
        parts.append(f'<g transform="translate(0,{oy})"><rect width="{W}" height="{h}" fill="{bg}"/>{body}</g>')
        oy += h
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total}">{"".join(parts)}</svg>'
    cairosvg.svg2png(bytestring=svg.encode(), write_to=out)
