"""Rangesets (Sohns, Schmitt, Jirasek, Hasse, and Leitte, IEEE TVCG 28(1),
2022), as proposed in the paper and released in the authors' NoLiES code
(github.com/leitte/NoLiES, Embedding/Rangeset.py).

Method (paper Sec. 4.2-4.4):
* one attribute at a time is discretized: a continuous attribute into 5
  equal-width bins over [min, max] (values outside a user range fall into
  the extreme bins), a categorical one into one bin per category; in the
  code an attribute with fewer than 15 distinct values is categorical;
* for each bin, the embedded points of that bin alone are triangulated
  (Delaunay), and every triangle with an edge longer than eps is removed;
  the union of the remaining triangles is the bin's region, holes included
  (Sec. 4.2.1); regions of different bins may overlap (Sec. 2.1);
* a point of the bin that does not touch its region is an outlier (the
  code's definition, which produced the figures; the paper's wording is a
  nearest neighbour farther than eps);
* the default eps is Wilkinson's rule on the minimum spanning tree of the
  embedding, eps = q75 + 1.5 (q75 - q25) over its edge lengths
  (Sec. 4.2.2), which the paper usually raises by hand (wine: 0.96 -> 2);
* rendering (Sec. 4.4 and the code): each region filled in its bin's
  colour at alpha 0.5 without outline, below the points, in ascending bin
  order; every point opaque in its bin colour, outliers with about 2.5
  times the diameter of inliers; continuous bins coloured #2b83ba #afcc50
  #ffe05c #f5a60a #d7191c (very low to very high).

Details the paper leaves open, and the values used here:
* the edge test is d <= eps, as the paper writes it (the code tests <);
  `strict=True` reproduces the code;
* eps is twice Wilkinson's value unless given (the paper's wine example
  raises it by a factor of 2.1; the released notebooks hard-code eps per
  dataset);
* categorical attributes use Category10 (Category20 above 10 categories),
  as in the paper's figures (the code uses its own 8-colour palette);
* the triangulation is GEOS's (shapely), as in the authors' code;
* no attribute ranking: the paper has none, and the analyst picks the
  attribute.
"""
import numpy as np
import pandas as pd
import shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial import Delaunay
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

CONTINUOUS_COLORS = ["#2b83ba", "#afcc50", "#ffe05c", "#f5a60a", "#d7191c"]
CONTINUOUS_LABELS = ["very low", "low", "medium", "high", "very high"]
CATEGORY10 = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
              "#bcbd22", "#17becf"]
CATEGORY20 = ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a", "#d62728", "#ff9896",
              "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7",
              "#bcbd22", "#dbdb8d", "#17becf", "#9edae5"]
MAX_CATEGORIES = 15


def is_categorical(values):
    s = pd.Series(values)
    return (isinstance(s.dtype, pd.CategoricalDtype) or s.dtype == object or s.dtype == bool
            or s.nunique() < MAX_CATEGORIES)


def discretize(values, bins=5, val_range=None):
    """Bin index of every value (-1 for missing), the bin labels, and the bin
    colours. Continuous: equal-width bins over `val_range` (default the data
    range), the outer edges stretched to the data; categorical: one bin per
    category in sorted order."""
    s = pd.Series(values).reset_index(drop=True)
    missing = s.isna().values
    if is_categorical(s):
        cats = sorted(s.dropna().unique(), key=lambda v: (str(type(v)), v))
        index = {c: i for i, c in enumerate(cats)}
        b = np.array([index.get(v, -1) if not m else -1 for v, m in zip(s, missing)])
        colors = CATEGORY10[:len(cats)] if len(cats) <= 10 else CATEGORY20[:len(cats)]
        return b, [str(c) for c in cats], colors
    x = s.astype(float).values
    lo, hi = (np.nanmin(x), np.nanmax(x)) if val_range is None else val_range
    # Edges accumulate the step as in the authors' code, so that a value
    # lying on an edge falls into the same bin
    step = (hi - lo) / bins
    edges = np.array([lo + i * step for i in range(bins + 1)])
    b = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, bins - 1)
    b = np.where(missing, -1, b)

    def fmt(v):
        # Three significant digits, without exponents for large values
        return f"{float(f'{v:.3g}'):,.0f}" if abs(v) >= 1000 else f"{v:.3g}"

    labels = [f"{fmt(edges[k])}–{fmt(edges[k + 1])}" for k in range(bins)]
    return b, labels, CONTINUOUS_COLORS[:bins] if bins == 5 else None


def mst_edge_lengths(points):
    """Edge lengths of the Euclidean minimum spanning tree, computed on the
    Delaunay graph, which contains it."""
    tri = Delaunay(np.unique(points, axis=0))
    s = tri.simplices
    i = np.concatenate([s[:, 0], s[:, 1], s[:, 2]])
    j = np.concatenate([s[:, 1], s[:, 2], s[:, 0]])
    w = np.linalg.norm(tri.points[i] - tri.points[j], axis=1)
    g = coo_matrix((w, (np.minimum(i, j), np.maximum(i, j))), shape=(len(tri.points),) * 2).tocsr()
    return minimum_spanning_tree(g).data


def wilkinson_eps(points):
    """eps = q75 + 1.5 (q75 - q25) of the MST edge lengths (Sec. 4.2.2)."""
    q25, q75 = np.quantile(mst_edge_lengths(points), [0.25, 0.75])
    return float(q75 + 1.5 * (q75 - q25))


def region(points, eps, strict=False):
    """The bin's region and the inlier mask: the union of the Delaunay
    triangles of `points` whose edges are all at most eps (shorter than eps
    if `strict`), and whether each point touches that region."""
    inlier = np.zeros(len(points), bool)
    if len(points) < 3:
        return MultiPolygon(), inlier
    # GEOS (shapely) triangulates every distinct point; Qhull (scipy) drops
    # points it considers coincident with a neighbour, which changes the
    # regions where points nearly coincide
    tris = shapely.get_parts(shapely.delaunay_triangles(shapely.multipoints(points)))
    if len(tris) == 0:
        return MultiPolygon(), inlier
    p = shapely.get_coordinates(tris).reshape(len(tris), 4, 2)[:, :3]
    longest = np.max(np.stack([np.linalg.norm(p[:, a] - p[:, b], axis=1) for a, b in ((0, 1), (1, 2), (2, 0))]),
                     axis=0)
    keep = longest < eps if strict else longest <= eps
    if not keep.any():
        return MultiPolygon(), inlier
    poly = unary_union(tris[keep])
    if isinstance(poly, Polygon):
        poly = MultiPolygon([poly])
    # A point is an inlier if it touches the region: a vertex of a kept
    # triangle, or a point on one of its edges (collinear points)
    return poly, shapely.intersects_xy(poly, points[:, 0], points[:, 1])


def rangeset(values, embedding, eps, bins=5, val_range=None, strict=False):
    """Rangeset of one attribute: per bin its label, colour, region, and the
    indices of its inliers and outliers."""
    b, labels, colors = discretize(values, bins, val_range)
    out = []
    for k, (label, color) in enumerate(zip(labels, colors)):
        idx = np.where(b == k)[0]
        poly, inlier = region(embedding[idx], eps, strict)
        out.append(dict(label=label, color=color, region=poly, inliers=idx[inlier], outliers=idx[~inlier]))
    return out
