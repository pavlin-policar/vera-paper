"""IXVC: explaining visual clusters with decision trees (Bibal, Clarinval,
Dumas, and Frenay, Array 11, 2021).

Method (paper Sec. 3.3, Algorithm 1, and the settings in Sec. 6):
* the analyst selects p visual clusters in the given 2D view; only selected
  points take part (the paper's trees have 47 and 40 samples out of 50);
* one multiclass decision tree (scikit-learn CART) is learned with the
  cluster labels as the target and the original features as the input;
* the only tuned hyperparameter is min_samples_leaf, chosen among the 40
  values in [10, 50[ by 10-fold cross-validation as
  hp* = arg max_hp mean(score_{.,hp}); the tree is then refit on all
  selected points;
* the tree is drawn as a horizontal node-link diagram, root on the left,
  links labelled TRUE (feature <= threshold) and FALSE; internal nodes show
  the split, the entropy, and the sample count; leaves are outlined in the
  colour of their majority cluster and show the impurity, the sample count,
  and the per-cluster counts;
* the prediction view colours every selected point by its predicted
  cluster, marks errors with a cross, and maps the prediction confidence to
  opacity;
* the DR view shows each point's DR error as opacity (for t-SNE, the
  point's term of the KL divergence, D_KL(p_i || q_i) = p_i log(p_i/q_i)).

Details the paper leaves open, and the values used here:
* split criterion: entropy (every impurity printed in the paper's figures
  equals the entropy of the shown class counts);
* score: accuracy; folds: stratified, shuffled with a fixed seed; ties in
  the arg max go to the smallest min_samples_leaf (the paper's figures have
  leaves of exactly 10 samples);
* other tree settings are scikit-learn's defaults;
* prediction confidence: the majority fraction of the point's leaf;
* the cluster selection, which the analyst draws with a lasso in the
  original tool, is given as labels (here DBSCAN on the embedding), and
  noise points are left unselected;
* categorical attributes enter the tree one-hot encoded, and 0/1 columns
  (one-hot or indicator) can only be split at 0.5, so each such split is
  the rule "attribute = value" (or "indicator" present); it is drawn as
  that rule, with TRUE (the value holds) above FALSE, in place of
  scikit-learn's "attribute = value <= 0.5", whose TRUE branch is the
  value's absence; a split of an integer-valued column at k + 0.5 is drawn
  as "<= k", or "= k" where k is the column's minimum;
* the per-point DR error is computed for any given embedding as the point's
  KL term between perplexity-based input affinities (openTSNE, perplexity
  30, symmetrized and normalized) and Student-t output affinities.
"""
import numpy as np
from scipy import sparse
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

LEAF_GRID = tuple(range(10, 50))
N_FOLDS = 10


def fit_tree(X, y, leaf_grid=LEAF_GRID, n_folds=N_FOLDS, random_state=0):
    """CV-tuned entropy tree on the selected points (y >= 0). Returns the
    refit tree, the chosen min_samples_leaf, and the mean CV accuracy for
    every grid value."""
    sel = y >= 0
    Xs, ys = X[sel], y[sel]
    folds = min(n_folds, int(np.bincount(ys).min()))
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=random_state)
    scores = np.array([
        cross_val_score(DecisionTreeClassifier(criterion="entropy", min_samples_leaf=m, random_state=random_state),
                        Xs, ys, cv=cv, scoring="accuracy").mean()
        for m in leaf_grid])
    best = leaf_grid[int(np.argmax(scores))]
    tree = DecisionTreeClassifier(criterion="entropy", min_samples_leaf=best, random_state=random_state).fit(Xs, ys)
    return tree, best, dict(zip(leaf_grid, scores.tolist()))


def predictions(tree, X):
    """Predicted cluster and confidence (majority fraction of the leaf)."""
    proba = tree.predict_proba(X)
    return tree.classes_[proba.argmax(axis=1)], proba.max(axis=1)


def pointwise_kl(X, embedding, perplexity=30, random_state=0):
    """Each point's term of KL(P || Q): sum_j p_ij log(p_ij / q_ij), with P
    the symmetrized perplexity affinities of the standardized data and Q the
    Student-t affinities of the embedding, both normalized over all pairs."""
    from openTSNE.affinity import PerplexityBasedNN
    sd = X.std(axis=0)
    Z = (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1)
    P = PerplexityBasedNN(Z, perplexity=min(perplexity, (len(Z) - 1) / 3),
                          method="exact" if len(Z) < 1000 else "annoy", random_state=random_state, n_jobs=1,
                          verbose=False).P
    P = sparse.csr_matrix(P)
    P = P / P.sum()
    Y = np.asarray(embedding, float)
    sq = (Y ** 2).sum(axis=1)
    zsum = 0.0
    for s in range(0, len(Y), 1000):
        d2 = np.maximum(sq[s:s + 1000, None] + sq[None, :] - 2 * Y[s:s + 1000] @ Y.T, 0)
        zsum += (1.0 / (1.0 + d2)).sum() - min(1000, len(Y) - s)
    rows, cols = P.nonzero()
    p = np.asarray(P[rows, cols]).ravel()
    q = 1.0 / (1.0 + ((Y[rows] - Y[cols]) ** 2).sum(axis=1)) / zsum
    terms = p * np.log(p / q)
    return np.bincount(rows, weights=terms, minlength=len(X))


def tree_structure(tree, X):
    """Nodes of a tree fitted on `X` as dicts, in scikit-learn's node order.
    A split on a 0/1 column of `X` is an equality rule (`equals` is True):
    its `left` child holds the samples with value 1, and its `right` child
    those with 0. Every other split sends feature <= threshold `left`; on an
    integer-valued column, `bound` is the largest integer on the left and
    `at_min` tells whether it is the column's minimum."""
    t = tree.tree_
    binary = np.all((X == 0) | (X == 1), axis=0)
    integer = np.all(X == np.round(X), axis=0)
    col_min = X.min(axis=0)
    counts = t.value[:, 0, :] * t.weighted_n_node_samples[:, None]
    nodes = []
    for i in range(t.node_count):
        c = np.rint(counts[i]).astype(int)
        leaf = t.children_left[i] == -1
        left, right = int(t.children_left[i]), int(t.children_right[i])
        equals = not leaf and bool(binary[t.feature[i]])
        if equals:
            left, right = right, left
        bound = at_min = None
        if not leaf and not equals and integer[t.feature[i]]:
            bound = int(np.floor(t.threshold[i]))
            at_min = bound == col_min[t.feature[i]]
        nodes.append({
            "id": i, "left": left, "right": right,
            "feature": int(t.feature[i]), "threshold": float(t.threshold[i]), "equals": equals,
            "bound": bound, "at_min": at_min,
            "samples": int(t.n_node_samples[i]), "entropy": float(t.impurity[i]),
            "counts": c.tolist(), "majority": int(np.argmax(c)),
            "leaf": leaf,
        })
    return nodes


def split_rule(node, names, digits=3, le="≤"):
    """The rule of an internal node: "attribute = value" (or the indicator's
    name) for a split on a 0/1 column, "feature <= k" or "feature = k" for
    an integer-valued one, else "feature <= threshold"."""
    if node["equals"]:
        return names[node["feature"]]
    if node["bound"] is not None:
        return f"{names[node['feature']]} {'=' if node['at_min'] else le} {node['bound']}"
    return f"{names[node['feature']]} {le} {node['threshold']:.{digits}g}"
