"""Data loading and preprocessing shared by the related methods."""
import os
from importlib.util import module_from_spec, spec_from_file_location

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

HERE = os.path.dirname(os.path.abspath(__file__))
SUPPLEMENT_DATA = os.path.join(HERE, "..", "..", "supplement-data")
SUBSAMPLE = 5000
RANDOM_STATE = 0


def _load_module(name, rel):
    spec = spec_from_file_location(name, os.path.join(SUPPLEMENT_DATA, rel))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


datasets = _load_module("_supplement_datasets", "datasets.py")
figstyle = _load_module("_supplement_figstyle", "figstyle.py")


def load(name, subsample=SUBSAMPLE, embedding=None):
    """Features and embedding (the default one, or the named variant) of a
    supplementary dataset, with a fixed random subsample of at most
    `subsample` rows."""
    data = datasets.Dataset.load(name, embedding=embedding)
    n = data.features.shape[0]
    if n > subsample:
        idx = np.sort(np.random.RandomState(RANDOM_STATE).choice(n, subsample, replace=False))
    else:
        idx = np.arange(n)
    features = data.features.iloc[idx].reset_index(drop=True)
    # Some sources pad category values with spaces (" Male" in adult)
    for c in features.columns:
        if is_categorical(features[c]):
            features[c] = features[c].astype(str).str.strip().astype("category")
    return features, data.embedding[idx]


def is_categorical(s):
    return isinstance(s.dtype, pd.CategoricalDtype) or s.dtype == object or s.dtype == bool


def numeric_matrix(features):
    """Numeric columns as they are, categorical columns one-hot encoded as
    "attribute = value" columns. Returns the matrix, column names, and the
    source attribute of every column."""
    cols, names, bases = [], [], []
    for c in features.columns:
        s = features[c]
        if is_categorical(s):
            for v in pd.Series(s).astype("category").cat.categories:
                cols.append((s == v).astype(float).values)
                names.append(f"{c} = {v}")
                bases.append(c)
        else:
            x = s.astype(float).values
            cols.append(np.where(np.isnan(x), np.nanmean(x), x))
            names.append(c)
            bases.append(c)
    return np.column_stack(cols), names, bases


def dbscan_labels(embedding, eps_quantile=0.95, min_samples=10, eps=None):
    """DBSCAN on the 2D embedding, the clustering ccPCA's system applies by
    default. The paper leaves eps to the user; unless given, eps is the
    `eps_quantile` quantile of the distances to the `min_samples`-th
    neighbour. Noise points get the label -1."""
    if eps is None:
        nn = NearestNeighbors(n_neighbors=min_samples).fit(embedding)
        d, _ = nn.kneighbors(embedding)
        eps = float(np.quantile(d[:, -1], eps_quantile))
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(embedding)
    return labels, eps
