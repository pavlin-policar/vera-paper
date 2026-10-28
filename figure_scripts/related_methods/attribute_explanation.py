"""Attribute-based visual explanation of projections (da Silva, Rauber,
Martins, Minghim, and Telea, EuroVA 2015).

Every projected point is explained by the dimension whose values vary least
in its neighbourhood, relative to the whole dataset.

Method (paper Sec. 3):
* the 2D neighbourhood of point i is every projected point within radius
  rho, the paper's value being 10% of the projection diameter (largest
  distance between two points); its nD counterpart nu_i is the same points
  in the data space;
* variance ranking (Eq. 4), used in all of the paper's examples:
  mu_i^j = (LV_i^j / GV^j) / sum_j (LV_i^j / GV^j), with LV_i the variance
  of each dimension over nu_i and GV over the whole dataset;
  Euclidean ranking (Eqs. 1-3): lc_i^j is the mean over r in nu_i of
  (p_i^j - r^j)^2 / ||p_i - r||^2, gc^j the same with the centroid as the
  focal point and every point as its neighbourhood, and
  mu_i^j = (lc_i^j / gc^j) / sum_j (lc_i^j / gc^j);
  a low rank means the dimension explains the neighbourhood well;
* single-dimension explanation: each point's top-ranked (lowest mu)
  dimension; the C = 9 dimensions that are top-ranked for most points get
  categorical colours, all others the reserved dark blue (Sec. 3.2);
* dimension-set explanation: the top-ranked dimensions whose ranks sum to
  the user threshold tau or just above it (tau = 0.05 in the paper's
  examples); the C most frequent sets get colours (Sec. 3.3);
* confidence: computed over a smaller radius rho_c < rho, as the share of
  the top-rank weight in that neighbourhood that falls on point i's own
  top-ranked dimension. The paper describes summing "the top-ranks of all
  points" in the rho_c neighbourhood into a ranking vector; here every
  point contributes one vote to its top-ranked dimension (or set), so the
  confidence is the fraction of points within rho_c that share point i's
  explanation. The paper gives no value of rho_c; rho / 2 is used;
* display: a dense map by nearest-neighbour (Voronoi) interpolation, with
  the explanation as colour and the confidence as brightness (Sec. 3.2).
  The interpolation is limited to pixels within `fill_radius` of a point so
  that empty space stays blank; the paper does not say how far its dense
  map extends.

Dimensions that are constant over the dataset have no defined global
variance and are left out. Categorical attributes are one-hot encoded, each
category being one dimension.
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import pdist

N_COLORS = 9
DARK_BLUE = (0.05, 0.1, 0.35)


def diameter(points):
    """Largest distance between two points (computed on the convex hull)."""
    from scipy.spatial import ConvexHull
    hull = points[ConvexHull(points).vertices]
    return float(pdist(hull).max())


def neighbourhoods(points, radius):
    return cKDTree(points).query_ball_point(points, r=radius)


def variance_ranking(x, nbrs):
    gv = x.var(axis=0)
    keep = gv > 0
    x, gv = x[:, keep], gv[keep]
    ratio = np.stack([x[idx].var(axis=0) for idx in nbrs]) / gv
    return ratio / np.maximum(ratio.sum(axis=1, keepdims=True), 1e-300), keep


def euclidean_ranking(x, nbrs):
    gv = x.var(axis=0)
    keep = gv > 0
    x = x[:, keep]

    def contribution(p, r):
        d = (p - r) ** 2
        tot = d.sum(axis=1, keepdims=True)
        ok = tot[:, 0] > 0
        return (d[ok] / tot[ok]).mean(axis=0) if ok.any() else np.zeros(x.shape[1])

    gc = contribution(x.mean(axis=0), x)
    lc = np.stack([contribution(x[i], x[idx]) for i, idx in enumerate(nbrs)])
    ratio = lc / gc
    return ratio / np.maximum(ratio.sum(axis=1, keepdims=True), 1e-300), keep


def dimension_sets(ranks, tau):
    """Per point, the lowest-ranked dimensions whose ranks sum to tau or
    just above it, as a sorted tuple of column indices."""
    order = np.argsort(ranks, axis=1)
    sorted_ranks = np.take_along_axis(ranks, order, axis=1)
    cum = np.cumsum(sorted_ranks, axis=1)
    n = np.minimum((cum < tau).sum(axis=1) + 1, ranks.shape[1])
    return [tuple(sorted(int(j) for j in order[i, :n[i]])) for i in range(len(ranks))]


def confidence(points, explanation, radius):
    """Fraction of the points within `radius` that share each point's
    explanation."""
    nbrs = neighbourhoods(points, radius)
    expl = np.asarray(explanation, dtype=object)
    return np.array([np.mean([expl[j] == expl[i] for j in idx]) for i, idx in enumerate(nbrs)])


def colour_classes(explanation, n_colors=N_COLORS):
    """The `n_colors` most frequent explanations, most frequent first."""
    values, counts = np.unique(np.array([str(e) for e in explanation]), return_counts=True)
    return list(values[np.argsort(-counts)][:n_colors])


def dense_map(points, colours, conf, xlim, ylim, fill_radius, resolution=500):
    """Nearest-neighbour interpolated RGBA image: the colour of the nearest
    point, darkened by (1 - confidence), transparent beyond `fill_radius`."""
    xs = np.linspace(*xlim, resolution)
    ys = np.linspace(*ylim, resolution)
    gx, gy = np.meshgrid(xs, ys)
    dist, idx = cKDTree(points).query(np.column_stack([gx.ravel(), gy.ravel()]))
    rgb = colours[idx] * conf[idx, None]
    alpha = (dist <= fill_radius).astype(float)
    return np.column_stack([rgb, alpha]).reshape(resolution, resolution, 4)
