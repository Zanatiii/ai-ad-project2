# Siltaro Display: provenance log

Proof of original construction. No existing font was opened, downloaded, traced, measured or imitated.
The SILTARO logo was only looked at for overall spirit (wide, monoline, calm geometry). No letter was traced
or copied from it.

## Method
Every glyph is a Python function in `src/glyphs.py`. It builds a skeleton from two primitives only:
straight lines and circular or elliptical arcs (cubic approximation with k = 4/3·tan(θ/4), ≤ 90° per
segment). The skeleton is expanded with Skia's stroker using a uniform width and flat (butt) caps. The pieces
are merged with boolean union, and diagonal ends are cut flat by clipping to the 0–700 band. All of the
code is in `src/geom.py`.

## Metrics
UPM 1000 · cap 700 · baseline 0 · descender −200 · ascender 800.
Stroke W = 112 (16 % of cap; Regular). Overshoot = 0.11·W = 12. Inner corner radius = 0.25·W = 28.
Brand slash angle = 52°.

## Phase 1: 2026-10-04
Glyphs: A B C E F G H I K L N O P R S T U V W Y, R.ss01, 0–9, period, space.

| Glyph | Construction |
|---|---|
| I | rectangle W × 700 |
| L | polyline (W/2,700)→(W/2,W/2)→(470,W/2); inner fillet r=28 |
| T | bar 600 × W at the top + stem centred at x=300 |
| E | polyline top bar→stem→base bar (x=500); middle bar at y=350 to x=460; fillets top-left and bottom-left |
| F | top bar to x=490, stem; middle bar at y=340 to x=440; fillet top-left |
| H | two stems 620 apart (outer), bar at y=350 |
| N | stems at 0 and 640; diagonal from (W/2,740) to (640−W/2,−40), clipped to the box |
| K | stem; arms are one polyline (560,760)→(102,330)→(620,−60), clipped; lower leg sliced at 52° from (520,0) |
| A (Λ) | polyline (0,−60)→(320,840)→(640,−60), miter join, clipped to 0–700 so the apex is cut flat; no crossbar; right foot sliced at 52° |
| V | the same chevron inverted |
| W | polyline through x = 0, 225, 450, 675, 900, alternating below 0 and above 700, clipped |
| Y | arms meet at (310,320); stem to the baseline |
| O | perfect circle ring: outer radius 362 (350 + overshoot), stroke W |
| C | the O ring from 42° to 318°, radial flat cuts |
| G | the O ring from 42° to 360°; bar from x = R+40 to 2R, top edge on y=350 |
| U | stems joined by a half circle, radius (620−W)/2, bottom overshoot 12 |
| S | two ellipses, rx 196 (top) and 210 (bottom), ry 146 and 160, meeting tangentially on the spine; arcs 28°→270° and 90°→−152° |
| P | stem + D-bowl (top bar, half circle, bar at y=300), right edge 540 |
| R | the P bowl ending at y=320 + straight leg (xa−70,320)→(xa+210,−40), clipped; foot sliced at 52° |
| R.ss01 | bowl as in R; tail = cubic centreline (xa−60,320) (xa+60,150) (xa+230,−150) (xa+760,−170), half-width W/2·(1−t)^0.85 tapering to a point; both sides fitted with 8 Hermite cubic segments |
| B | stem + two D-bowls (upper right edge 500, lower 540), split at y=372 |
| 0 | stadium 520 wide: two half circles + straight sides |
| 1 | stem at x=190 + flag line to (0,500), clipped |
| 2 | arc r=196 from 168° to −38°, straight diagonal to the bottom-left, base bar to x=520 |
| 3 | the S/8 two-ellipse system (rx 176/200), right-hand arcs + a middle bar 110 long |
| 4 | stem at x=400, crossbar at y=210, diagonal from the stem top to the bar |
| 5 | top bar, short stem, lower ellipse bowl rx 200 ry 172 from 90° to −150° |
| 6 | full circle bowl (r = (520−W)/2) + a straight stroke tangent to its left side, rising to the cap height and cut flat |
| 9 | the 6 rotated 180° |
| 7 | top bar + a straight diagonal to (130,−120), clipped |
| 8 | two stacked ellipse rings (rx 178/204, ry 146/160) |
| . | W × W square |

## Phase 1 revision: 2026-10-04
Changes after the first review:
- **A / V:** the apex is now a true point. The skeleton apex sits at CAP + overshoot − (W/2)/sin(half-angle), so the outer miter lands exactly at 712 (or −12 for the V). Width 660.
- **Brand slash:** each '\' leg that lands on the baseline (A right leg, K lower leg, R leg) is now sliced clean through. The cut runs from the foot's inner baseline corner, rising at 52°. This replaces the small corner nick.
- **G:** the arc now runs 42°→380°. The bar is centred on y=350 and runs from x = R+30; the arc is trimmed flush with the bar's top edge, and the whole glyph is clipped to its outer circle so the bar ends exactly on the curve.
- **W:** pointed vertices built the same way as the A, with each leg spanning a quarter of the width (920). The middle apex stops below the cap height by construction.
- **2:** the diagonal now leaves the arc (r=200) tangentially. The tangent point is computed from the landing point (W/2+6, W/2).
- **Wider letters:** E 540, F 525, L 500, P/R bowl right edge 575, B 530/575, S rx 214/230.
