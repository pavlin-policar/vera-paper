"""ccPCA: contrasting clusters in PCA (Fujiwara, Kwon, and Ma, TVCG 2020).

A NumPy/SciPy implementation of the method and of the feature-contribution
(FC) heatmap organization described in the paper:

* cPCA (Abid et al., 2018) finds directions v maximizing
  v^T (C_target - alpha C_background) v.
* ccPCA explains one cluster K at a time with target E = K u R (all data) and
  background R (all other points), so that the first contrastive principal
  component (cPC) separates K from R.
* alpha is chosen automatically (paper Eq. 4): among alpha = 0 and
  n_alphas - 1 log-spaced values in [10^-1, 10^max_log_alpha], take the one
  that maximizes the discrepancy 1 / HI(K', R') between the histograms of
  K and R projected on the first cPC, subject to the scaled variance of K'
  staying at least var_thres_ratio times its value at alpha = 0.
* The feature contributions are the first cPC loadings sqrt(|lambda|) v.

Details the paper leaves open follow the authors' code
(github.com/takanori-fujiwara/ccpca):

* target and background are each centered and, with `standardize=True`
  (the authors' default), divided by their own standard deviation;
* histogram bins have Scott's width computed on the pooled projections after
  min-max scaling to [0, 1];
* a later alpha replaces the current best only on a strictly larger
  discrepancy.

The authors' two implementations differ in what is projected for the alpha
search. Their C++ code, released with the paper, projects K and R as given,
uncentered and in their original units (`projection="raw"`); their current
Python code projects the rows of the centered, standardized target, the
space in which the cPC is computed (`projection="standardized"`, the
default here). With raw projections the histograms are dominated by the
features with the largest units.
"""
import numpy as np
from scipy.cluster.hierarchy import fcluster, leaves_list, linkage, optimal_leaf_ordering
from scipy.linalg import eigh
from scipy.spatial.distance import pdist


def _center_scale(x, standardize):
    """Center the columns and, optionally, scale them to unit variance. A
    constant column becomes zero; it is detected on the input, because
    centering can leave a constant rounding residue that would otherwise be
    scaled up to +-1."""
    constant = np.ptp(x, axis=0) == 0
    x = x - x.mean(axis=0)
    if standardize:
        sd = x.std(axis=0)
        x = x / np.where(constant | (sd == 0), 1.0, sd)
    x[:, constant] = 0.0
    return x


def _cov(x):
    return x.T @ x / max(x.shape[0] - 1, np.finfo(float).tiny)


def _scaled_var(a, b):
    """Variance of `a` after min-max scaling of a and b jointly."""
    lo, hi = min(a.min(), b.min()), max(a.max(), b.max())
    rng = max(hi - lo, np.finfo(np.float32).tiny)
    return np.mean(((a - a.mean()) / rng) ** 2)


def _hist_intersection(a, b):
    """Histogram intersection (in counts) of a and b on shared Scott bins."""
    lo, hi = min(a.min(), b.min()), max(a.max(), b.max())
    rng = max(hi - lo, np.finfo(np.float32).tiny)
    ta, tb = (a - lo) / rng, (b - lo) / rng
    pooled = np.concatenate([ta, tb])
    n = len(pooled)
    sd = pooled.std(ddof=1) if n > 1 else 0.0
    width = max(3.5 * sd / n ** (1 / 3), np.finfo(np.float32).tiny)
    n_bins = int(1.0 / width) + 1
    ca = np.bincount((ta / width).astype(int), minlength=n_bins)
    cb = np.bincount((tb / width).astype(int), minlength=n_bins)
    return int(np.minimum(ca, cb).sum())


class CPCA:
    """Contrastive PCA with a fixed alpha on precomputed covariances."""

    def __init__(self, target, background, standardize=True):
        self.target = _center_scale(np.asarray(target, dtype=float), standardize)
        self.background = _center_scale(np.asarray(background, dtype=float), standardize)
        self.target_cov = _cov(self.target)
        self.background_cov = _cov(self.background)

    def first_component(self, alpha):
        """Top eigenvalue and eigenvector of C_target - alpha C_background."""
        w, v = eigh(self.target_cov - alpha * self.background_cov)
        return w[-1], v[:, -1]


class CCPCA:
    """Contrast one cluster K against the remaining points R.

    After `fit`, `best_alpha_`, `eigenvalue_` (top eigenvalue of the
    contrastive covariance), `component_` (first cPC), `feat_contribs_`
    (first cPC loadings), the target and background covariances, and
    `report_` (one entry per candidate alpha) are set.
    """

    def __init__(self, standardize=True, n_alphas=40, max_log_alpha=3.0, var_thres_ratio=0.5,
                 projection="standardized"):
        if projection not in ("standardized", "raw"):
            raise ValueError(f"unknown projection {projection!r}")
        self.standardize = standardize
        self.projection = projection
        self.n_alphas = n_alphas
        self.max_log_alpha = max_log_alpha
        self.var_thres_ratio = var_thres_ratio

    def alphas(self):
        return np.concatenate([[0.0], np.logspace(-1, self.max_log_alpha, self.n_alphas - 1)])

    def fit(self, K, R):
        K, R = np.asarray(K, dtype=float), np.asarray(R, dtype=float)
        cpca = CPCA(np.vstack([K, R]), R, standardize=self.standardize)
        if self.projection == "standardized":
            K_proj, R_proj = cpca.target[:len(K)], cpca.target[len(K):]
        else:
            K_proj, R_proj = K, R
        best_alpha, best_disc, base_var = 0.0, None, None
        # (alpha, discrepancy, scaled variance of K', first cPC) per candidate
        self.report_ = []
        for alpha in self.alphas():
            _, v = cpca.first_component(alpha)
            pk, pr = K_proj @ v, R_proj @ v
            var_k = _scaled_var(pk, pr)
            disc = 1.0 / max(float(_hist_intersection(pk, pr)), np.finfo(np.float32).tiny)
            if base_var is None:
                base_var, best_disc = var_k, disc
            elif var_k >= base_var * self.var_thres_ratio and disc > best_disc:
                best_alpha, best_disc = alpha, disc
            self.report_.append((alpha, disc, var_k, v))
        lam, v = cpca.first_component(best_alpha)
        self.best_alpha_ = best_alpha
        self.eigenvalue_ = lam
        self.component_ = v
        self.feat_contribs_ = np.sqrt(abs(lam)) * v
        self.target_cov_ = cpca.target_cov
        self.background_cov_ = cpca.background_cov
        return self


def contrast_clusters(X, labels, **ccpca_kwargs):
    """Run ccPCA for every cluster in `labels`.

    Returns the cluster ids in order of first appearance after sorting, the
    feature contributions (n_features x n_clusters), the first cPCs (same
    shape), and the selected alphas.
    """
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels)
    clusters = np.unique(labels)
    fcs, comps, alphas = [], [], []
    for c in clusters:
        m = labels == c
        model = CCPCA(**ccpca_kwargs).fit(X[m], X[~m])
        fcs.append(model.feat_contribs_)
        comps.append(model.component_)
        alphas.append(model.best_alpha_)
    return clusters, np.column_stack(fcs), np.column_stack(comps), np.array(alphas)


def optimal_sign_flip(components):
    """Signs phi in {-1, 1} per column approximately maximizing paper Eq. 5,
    sum_{i != j} phi_i phi_j cos(v_i, v_j), with the paper's greedy heuristic:
    starting from phi = 1, repeatedly consider the not-yet-checked cluster
    whose sum of signed similarities is most negative and flip it if that
    increases the objective; stop when no cluster has a negative sum or every
    cluster has been checked."""
    v = np.asarray(components, dtype=float)
    v = v / np.linalg.norm(v, axis=0, keepdims=True)
    sim = v.T @ v
    np.fill_diagonal(sim, 0.0)
    phi = np.ones(sim.shape[0])
    checked = np.zeros(sim.shape[0], dtype=bool)

    def objective(p):
        return p @ sim @ p

    while True:
        sums = phi * (sim @ phi)
        candidates = np.where(~checked & (sums < 0))[0]
        if len(candidates) == 0:
            break
        i = candidates[np.argmin(sums[candidates])]
        checked[i] = True
        flipped = phi.copy()
        flipped[i] = -flipped[i]
        if objective(flipped) > objective(phi):
            phi = flipped
    return phi


def scale_columns(fcs):
    """Divide each cluster's contributions by their maximum absolute value."""
    m = np.abs(fcs).max(axis=0, keepdims=True)
    return fcs / np.where(m > 0, m, 1.0)


def _distances(x, metric):
    d = pdist(x, metric)
    # Cosine distance is undefined for an all-zero row (a constant feature)
    return np.nan_to_num(d, nan=1.0)


def _tree(x, metric):
    d = _distances(x, metric)
    return optimal_leaf_ordering(linkage(d, method="complete"), d)


def reorder(fcs, metric="cosine"):
    """Row (feature) and column (cluster) orders from complete-linkage
    hierarchical clustering with optimal leaf ordering (paper Sec. 5.2.2).
    The paper does not name the distance; cosine is the authors' default."""
    rows = leaves_list(_tree(fcs, metric)) if fcs.shape[0] > 2 else np.arange(fcs.shape[0])
    cols = leaves_list(_tree(fcs.T, metric)) if fcs.shape[1] > 2 else np.arange(fcs.shape[1])
    return rows, cols


def aggregate(fcs, names, max_rows=40, metric="cosine"):
    """Aggregate features into `max_rows` groups cut from the complete-linkage
    tree when there are more than `max_rows` features (paper Sec. 5.2.3).

    Each group keeps, per cluster, the contribution of largest absolute
    value, and is named after its feature of largest absolute contribution
    with the number of other features in the group ("name, N more").
    Returns the aggregated contributions, row names, and member indices.
    """
    names = list(names)
    if fcs.shape[0] <= max_rows:
        return fcs, names, [[i] for i in range(len(names))]
    groups = fcluster(_tree(fcs, metric), t=max_rows, criterion="maxclust")
    out, out_names, members = [], [], []
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        block = fcs[idx]
        pick = np.abs(block).argmax(axis=0)
        out.append(block[pick, np.arange(block.shape[1])])
        top = idx[np.unravel_index(np.abs(block).argmax(), block.shape)[0]]
        out_names.append(names[top] if len(idx) == 1 else f"{names[top]}, {len(idx) - 1} more")
        members.append(idx.tolist())
    return np.array(out), out_names, members
