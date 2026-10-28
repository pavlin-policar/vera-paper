"""Representative groups and their relevant attributes (Joia, Petronetto,
and Nonato, CGF 2015), which the paper calls the Column Selection Method.

Method (paper Sec. 3):
* A is the n x m matrix with the m instances as columns (Sec. 3.1). With
  the SVD A = U Sigma V^T, Sigma^-1 U^T A = V^T (Eq. 1), and the score of
  column j is pi_j = sum_{i=1}^k (v^i_j)^2 (Eq. 3), its rank-k leverage
  score; Algorithm 1 keeps the c columns with the largest pi, and the
  default rank is k = min{m, n} \\ 2 + 1 (integer division);
* representative instances: Algorithm 1 on A (Sec. 3.1);
* the instances are projected to 2D (Sec. 3.2); here the given embedding
  is used, the paper's method being independent of the projection;
* clustering (Sec. 3.2): EM clusters the representatives in the visual
  space, and every instance takes the cluster of its nearest
  representative;
* relevant attributes (Sec. 3.3): Algorithm 1 on A_i^T, the transpose of
  cluster i's submatrix, scores the attributes; the top c are shown;
* layout (Sec. 3.3, supplement Sec. 1): every cluster becomes an
  alpha-shape polygon built from the Delaunay triangulation of all points,
  filled with a word cloud of its relevant attributes, the font size a
  linear map of pi, the most relevant word nearest the polygon's centroid,
  rotations in 5 degree steps up to 90, and every word shrunk by 0.925 and
  the placement restarted when a word does not fit.

Details the paper leaves open, and the values used here:
* the attributes are mean-centred and not scaled (the paper calls the
  columns of U principal components, which implies centring, and its
  Dermatology example ranks the one large-range attribute first in every
  cluster, which implies no scaling); scaling is optional;
* k is capped at the numerical rank of the matrix, since beyond the rank
  every score is 1;
* c is 15% of the instances (the paper uses 10-50%), and the 9 most
  relevant attributes are shown (its Dermatology setting);
* EM is a Gaussian mixture with full covariances, 10 initializations, and a
  fixed seed, on the representatives' 2D coordinates; the number of
  clusters is given (the paper uses the number of classes);
* the polygon is the union of the Delaunay triangles of all points with at
  least one vertex in the cluster and every edge shorter than alpha times
  the extent of the view; the paper's alpha = 0.4 has no stated
  convention or unit, so alpha is a parameter;
* the word cloud is placed on a raster of the polygon; words are
  horizontal or rotated by 90 degrees;
* categorical attributes are one-hot encoded, each category being an
  attribute.
"""
import numpy as np
from scipy.spatial import Delaunay, cKDTree
from sklearn.mixture import GaussianMixture


def default_rank(m, n):
    return min(m, n) // 2 + 1


def leverage_scores(A, k=None, tol=1e-10):
    """pi_j of every column of A (Eq. 3) and the rank k used."""
    _, s, vt = np.linalg.svd(A, full_matrices=False)
    rank = int((s > tol * s[0]).sum()) if len(s) and s[0] > 0 else 0
    k = default_rank(*A.shape[::-1]) if k is None else k
    k = max(1, min(k, rank))
    return (vt[:k] ** 2).sum(axis=0), k


def _prepare(X, center=True, scale=False):
    Z = X - X.mean(axis=0) if center else X.copy()
    if scale:
        sd = X.std(axis=0)
        Z = Z / np.where(sd > 0, sd, 1)
    return Z


def representatives(X, fraction=0.15, k=None, center=True, scale=False):
    """Indices of the representative instances (Algorithm 1 on A = X^T)
    and their scores."""
    pi, k = leverage_scores(_prepare(X, center, scale).T, k)
    c = max(1, int(round(fraction * len(X))))
    order = np.lexsort((np.arange(len(pi)), -pi))
    return order[:c], pi, k


def cluster(embedding, reps, n_clusters, random_state=0):
    """EM on the representatives in 2D, then every instance takes the label
    of its nearest representative."""
    gm = GaussianMixture(n_components=n_clusters, covariance_type="full", n_init=10, random_state=random_state)
    rep_labels = gm.fit_predict(embedding[reps])
    _, nearest = cKDTree(embedding[reps]).query(embedding)
    return rep_labels[nearest], rep_labels


def relevant_attributes(X, labels, k=None, center=True, scale=False):
    """Per cluster, the attribute scores pi (Algorithm 1 on A_i^T) and the
    rank used."""
    out = {}
    for c in np.unique(labels):
        Xi = X[labels == c]
        pi, kk = leverage_scores(_prepare(Xi, center, scale), k)
        out[int(c)] = (pi, kk)
    return out


def cluster_polygons(points, labels, alpha=0.05):
    """The Delaunay triangulation of all points and the owning cluster of
    every triangle: the cluster holding at least two of its vertices, if its
    longest edge is at most alpha times the larger side of the bounding
    box, and -1 otherwise. A cluster's polygon is the union of its
    triangles; requiring two vertices keeps neighbouring polygons from
    overlapping."""
    tri = Delaunay(points)
    s = tri.simplices
    p = points[s]
    edges = np.stack([np.linalg.norm(p[:, a] - p[:, b], axis=1) for a, b in ((0, 1), (1, 2), (2, 0))], axis=1)
    extent = (points.max(axis=0) - points.min(axis=0)).max()
    short = edges.max(axis=1) <= alpha * extent
    lab = labels[s]
    owner = np.where(lab[:, 0] == lab[:, 1], lab[:, 0], np.where(lab[:, 2] == lab[:, 1], lab[:, 1],
                     np.where(lab[:, 0] == lab[:, 2], lab[:, 0], -1)))
    return tri, np.where(short, owner, -1)


def raster(tri, owner, xlim, ylim, resolution):
    """Owning cluster of every pixel of a resolution x resolution raster
    (rows = y, -1 outside every polygon)."""
    xs = np.linspace(*xlim, resolution)
    ys = np.linspace(*ylim, resolution)
    gx, gy = np.meshgrid(xs, ys)
    simplex = tri.find_simplex(np.column_stack([gx.ravel(), gy.ravel()]))
    return np.where(simplex >= 0, owner[simplex], -1).reshape(resolution, resolution)


def _box_sums(integral, bw, bh):
    """Sum of the underlying raster over every bw x bh box, indexed by the
    box's top-left cell."""
    return integral[bh:, bw:] - integral[:-bh, bw:] - integral[bh:, :-bw] + integral[:-bh, :-bw]


def word_cloud(mask, words, sizes, measure, rotations=(0, 90), shrink=0.925, max_restarts=60):
    """Greedy placement of words on a boolean raster `mask` (rows = y).

    `measure(word, size)` returns the word's (width, height) in raster
    cells at the given font size. Words are placed in order, each at the
    free position nearest the mask's centroid at which its box lies inside
    the mask, horizontal before rotated; if one does not fit, every size is
    multiplied by `shrink` and the placement restarts. Returns
    [(word, size, x, y, rotation)] with box centres in raster coordinates,
    or [] if nothing fits."""
    h, w = mask.shape
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return []
    cy, cx = ys.mean(), xs.mean()
    outside = np.pad(np.cumsum(np.cumsum(~mask, axis=0), axis=1), ((1, 0), (1, 0)))
    sizes = np.asarray(sizes, float)
    for _ in range(max_restarts):
        used = np.zeros(mask.shape, int)
        placed = []
        for word, size in zip(words, sizes):
            occupied = np.pad(np.cumsum(np.cumsum(used, axis=0), axis=1), ((1, 0), (1, 0)))
            best = None
            for rot in rotations:
                bw, bh = measure(word, size)
                if rot == 90:
                    bw, bh = bh, bw
                bw, bh = max(1, int(np.ceil(bw))), max(1, int(np.ceil(bh)))
                if bw >= w or bh >= h:
                    continue
                free = (_box_sums(outside, bw, bh) == 0) & (_box_sums(occupied, bw, bh) == 0)
                yy, xx = np.nonzero(free)
                if len(yy) == 0:
                    continue
                d = (yy + bh / 2 - cy) ** 2 + (xx + bw / 2 - cx) ** 2
                i = int(np.argmin(d))
                best = (xx[i], yy[i], bw, bh, rot)
                break
            if best is None:
                break
            x0, y0, bw, bh, rot = best
            used[y0:y0 + bh, x0:x0 + bw] = 1
            placed.append((word, size, x0 + bw / 2, y0 + bh / 2, rot))
        else:
            return placed
        sizes = sizes * shrink
    return []
