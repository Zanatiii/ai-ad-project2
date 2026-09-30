import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure, morphology, segmentation, feature

a = np.asarray(Image.open('../../images/1.jpg').convert('RGB')).astype(float)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
fields = {'copper': np.clip(R - B, 0, None), 'teal': np.clip(G - R, 0, None)}
out = {}
for name, s in fields.items():
    s = ndi.gaussian_filter(s, 0.8)
    mask = s > 40
    # solids: pixels whose brightness continues in some direction (a dot is dark all round)
    top = s >= 0.85 * ndi.maximum_filter(s, footprint=morphology.disk(4))
    frac = np.zeros_like(s)
    K = 24
    for t in np.linspace(0, 2 * np.pi, K, endpoint=False):
        sh = ndi.shift(s, (6.5 * np.sin(t), 6.5 * np.cos(t)), order=1, mode='constant')
        frac += sh >= 0.8 * s
    frac /= K
    core = (s > 50) & top & (frac >= 0.2)
    core = morphology.remove_small_objects(core, max_size=60)
    solid = core.copy()
    for _ in range(5):
        solid = ndi.binary_dilation(solid) & (s > 22) & (s > 0.5 * ndi.maximum_filter(s, footprint=morphology.disk(7)))
    solid = morphology.remove_small_objects(solid, max_size=1500)   # only crescents and blades
    solid = ndi.binary_fill_holes(solid)
    # dots: local maxima of the colour strength, outside the solids
    pk = feature.peak_local_max(s, min_distance=3, threshold_abs=25, exclude_border=False)
    far = ndi.distance_transform_edt(~solid)
    pk = pk[far[pk[:, 0], pk[:, 1]] > 2]
    markers = np.zeros(s.shape, int)
    markers[pk[:, 0], pk[:, 1]] = np.arange(1, len(pk) + 1)
    lab = segmentation.watershed(-s, markers, mask=mask & ~solid)
    peak = s[pk[:, 0], pk[:, 1]]
    half = s > 0.5 * peak[np.maximum(lab - 1, 0)]
    area = ndi.sum(half & (lab > 0), lab, range(1, len(pk) + 1))
    cy, cx = pk[:, 0].astype(float), pk[:, 1].astype(float)
    # subpixel centre = intensity centroid of each watershed cell
    com = ndi.center_of_mass(s * (lab > 0), lab, range(1, len(pk) + 1))
    com = np.array(com)
    r = np.sqrt(area / np.pi)
    dots = np.column_stack([com[:, 1], com[:, 0], r])
    dots = dots[(r > 1.2)]
    # drop dots that sit on or right at the tip of a solid (they are part of it)
    dist = ndi.distance_transform_edt(~solid)
    iy, ix = np.clip(dots[:, 1].round().astype(int), 0, s.shape[0] - 1), np.clip(dots[:, 0].round().astype(int), 0, s.shape[1] - 1)
    dots = dots[dist[iy, ix] > dots[:, 2] * 0.6]
    # isolated dots just past a solid are blade tips: extend the solid to a sharp point there
    from scipy.spatial import cKDTree
    kd = cKDTree(dots[:, :2])
    nn = kd.query(dots[:, :2], k=2)[0][:, 1]
    iy, ix = dots[:, 1].round().astype(int), dots[:, 0].round().astype(int)
    tips = (dist[iy, ix] < 22) & (nn > 16)
    for x, y, _ in dots[tips]:
        x0, y0 = int(x) - 40, int(y) - 40
        win = solid[y0:y0 + 81, x0:x0 + 81].copy()
        yy, xx = np.mgrid[0:81, 0:81]
        near = win & ((yy - 40) ** 2 + (xx - 40) ** 2 < 32 ** 2)
        near[40, 40] = True
        solid[y0:y0 + 81, x0:x0 + 81] |= morphology.convex_hull_image(near)
    dots = dots[~tips]
    # thin blade tips fade below the threshold: follow them at a low threshold, away from dots
    dm = np.ones(s.shape, bool)
    dm[dots[:, 1].round().astype(int), dots[:, 0].round().astype(int)] = False
    away = ndi.distance_transform_edt(dm) > 9
    faint = (s > 5) & (s > 0.5 * ndi.maximum_filter(s, footprint=morphology.disk(7))) & away
    for _ in range(80):
        solid = solid | (ndi.binary_dilation(solid) & faint)
    # solid contours
    cs = measure.find_contours(ndi.gaussian_filter(solid.astype(float), 1.6), 0.5)
    cs = [np.column_stack([c[:, 1], c[:, 0]]) for c in cs if len(c) > 30]
    out[name] = dict(dots=dots, solids=cs)
    print(name, 'dots', len(dots), 'solids', len(cs), 'r median', np.median(dots[:, 2]).round(2))
np.save('trace.npy', out, allow_pickle=True)
