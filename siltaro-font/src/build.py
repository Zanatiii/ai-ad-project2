"""Build Siltaro Display: glyph outlines -> OTF / TTF / WOFF2, plus SVG specimens.

Usage:  python3 build.py [--phase1]
"""
import os

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.svgPathPen import SVGPathPen

import glyphs as G
from geom import simplify

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UPM, ASC, DESC = 1000, 800, -200
WEIGHTS = {'Regular': 112, 'Light': 56}
VERSION = '1.000'

KERN = {
    ('T', 'A'): -70, ('A', 'T'): -70, ('L', 'T'): -90, ('T', 'O'): -20, ('T', 'E'): 0,
    ('A', 'V'): -60, ('V', 'A'): -60, ('A', 'Y'): -70, ('Y', 'A'): -70, ('A', 'W'): -45, ('W', 'A'): -45,
    ('L', 'Y'): -90, ('L', 'V'): -80, ('Y', 'O'): -25, ('W', 'O'): -15, ('O', 'W'): -15, ('O', 'Y'): -25,
    ('T', 'period'): -80, ('Y', 'period'): -80, ('V', 'period'): -70, ('W', 'period'): -50,
    ('R', 'T'): -20, ('R', 'V'): -20, ('P', 'A'): -50, ('F', 'A'): -50, ('T', 'L'): 0,
    ('T', 'comma'): -80, ('Y', 'comma'): -80, ('V', 'comma'): -70, ('W', 'comma'): -50,
    ('F', 'period'): -60, ('F', 'comma'): -60, ('P', 'period'): -60, ('P', 'comma'): -60,
    ('L', 'quotesingle'): -60, ('L', 'quotedbl'): -60, ('A', 'quotesingle'): -40, ('A', 'quotedbl'): -40,
    ('T', 'C'): -15, ('T', 'G'): -15, ('T', 'Q'): -20, ('C', 'T'): -15, ('O', 'T'): -20, ('O', 'V'): -20,
    ('V', 'O'): -20, ('O', 'A'): -20, ('A', 'O'): -15, ('D', 'A'): -25, ('A', 'C'): -15, ('A', 'G'): -15,
    ('L', 'O'): -20, ('K', 'O'): -25, ('X', 'O'): -20, ('Y', 'C'): -25, ('Y', 'G'): -25,
    ('F', 'O'): -10, ('P', 'J'): -40, ('T', 'J'): -60, ('A', 'U'): -10, ('U', 'A'): -15,
}


def build_glyphs(W):
    m = G.M(W)
    out = {}
    for name, (fn, uni) in G.GLYPHS.items():
        r = fn(m)
        path, lsb, rsb = r[0], r[1], r[2]
        path = simplify(path)
        if len(r) == 4:
            body = r[3] - rsb if name != 'space' else 0
            adv = r[3] if name == 'space' else lsb + r[3]
        else:
            b = path.bounds
            body = b[2]
            adv = round(lsb + body + rsb)
        from geom import translate
        path = translate(path, lsb)
        out[name] = dict(path=path, adv=round(adv), uni=uni)
    return out


def svg_path(path):
    pen = SVGPathPen(None)
    path.draw(pen)
    return pen.getCommands()


def build_font(W, style, outdir, names=None):
    gl = build_glyphs(W)
    order = ['.notdef'] + list(gl)
    fb_cff = FontBuilder(UPM, isTTF=False)
    fb_ttf = FontBuilder(UPM, isTTF=True)
    cmap = {}
    for n, g in gl.items():
        if g['uni']:
            cmap[g['uni']] = n
            if 0x41 <= g['uni'] <= 0x5A:
                cmap[g['uni'] + 32] = n              # lowercase maps to the caps
    metrics = {n: (g['adv'], round(g['path'].bounds[0]) if g['path'].bounds else 0) for n, g in gl.items()}
    metrics['.notdef'] = (500, 50)
    charstrings, ttglyphs = {}, {}
    from geom import rect
    for n in order:
        p = gl[n]['path'] if n in gl else None
        adv = metrics[n][0]
        cp = T2CharStringPen(adv, None)
        tp = TTGlyphPen(None)
        if p is not None:
            p.draw(cp)
            p.draw(Cu2QuPen(tp, max_err=0.5, reverse_direction=True))
        charstrings[n] = cp.getCharString()
        ttglyphs[n] = tp.glyph()
    family = 'Siltaro Display'
    nm = dict(familyName=family, styleName=style, uniqueFontIdentifier=f'SILTARO;{family}-{style};{VERSION}',
              fullName=f'{family} {style}', psName=f'SiltaroDisplay-{style}', version=f'Version {VERSION}',
              copyright='© 2026 SILTARO. All rights reserved.', manufacturer='SILTARO',
              licenseDescription='Proprietary. © 2026 SILTARO. All rights reserved.')
    for fb in (fb_cff, fb_ttf):
        fb.setupGlyphOrder(order)
        fb.setupCharacterMap(cmap)
    fb_cff.setupCFF(nm['psName'], {'FullName': nm['fullName'], 'FamilyName': family, 'Weight': style}, charstrings, {})
    fb_ttf.setupGlyf(ttglyphs)
    for fb in (fb_cff, fb_ttf):
        if fb.isTTF:
            mt = {n: (metrics[n][0], fb.font['glyf'][n].xMin if hasattr(fb.font['glyf'][n], 'xMin') else 0) for n in order}
        else:
            mt = metrics
        fb.setupHorizontalMetrics(mt)
        fb.setupHorizontalHeader(ascent=ASC, descent=DESC)
        fb.setupNameTable(nm)
        fb.setupOS2(sTypoAscender=ASC, sTypoDescender=DESC, sTypoLineGap=200, usWinAscent=900, usWinDescent=300,
                    sCapHeight=700, sxHeight=700, usWeightClass=400 if style == 'Regular' else 300,
                    fsType=0x0008, achVendID='SLTR')
        fb.setupPost()
        fea = feature_code(gl)
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
        addOpenTypeFeaturesFromString(fb.font, fea)
    os.makedirs(outdir, exist_ok=True)
    base = f'{outdir}/SiltaroDisplay-{style}'
    fb_cff.save(base + '.otf')
    fb_ttf.save(base + '.ttf')
    return gl


CAP_ = 700


def feature_code(gl):
    lines = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;', 'feature kern {']
    for (a, b), v in KERN.items():
        if a in gl and b in gl and v:
            lines.append(f'  pos {a} {b} {v};')
    lines.append('} kern;')
    if 'R.ss01' in gl:
        lines += ['feature ss01 {', '  featureNames { name "Tail R"; };', '  sub R by R.ss01;', '} ss01;']
    if 'A.ss02' in gl:
        lines += ['feature ss02 {', '  featureNames { name "Pyramid A (no crossbar)"; };', '  sub A by A.ss02;', '} ss02;']
    return '\n'.join(lines)


def layout(gl, text, alt=None):
    """Return [(glyph name, x)] and total width, applying kerning."""
    alt = alt or {}
    x, out, prev = 0, [], None
    names = {g['uni']: n for n, g in gl.items() if g['uni']}
    for ch in text:
        n = names.get(ord(ch.upper()))
        if n is None:
            continue
        n = alt.get(n, n)
        if prev:
            x += KERN.get((prev.split('.')[0], n.split('.')[0]), 0)
        out.append((n, x))
        x += gl[n]['adv']
        prev = n
    return out, x


if __name__ == '__main__':
    gl = build_font(WEIGHTS['Regular'], 'Regular', os.path.join(ROOT, 'build'))
    print('glyphs:', len(gl))
