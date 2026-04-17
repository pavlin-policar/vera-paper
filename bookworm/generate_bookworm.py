import os

import numpy as np
import pandas as pd

DATA_DIR = "data"


def rotate(theta) -> np.ndarray:
    """Construct a rotation matrix for a given angle."""
    return np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta), np.cos(theta)],
    ])


def connect_clusters(x1, x2, num_points):
    c1_centroid = np.mean(x1, axis=0)
    c2_centroid = np.mean(x2, axis=0)

    # Estimate standard deviation of the first cluster
    c1_std = np.mean(np.std(x1, axis=0, ddof=1))
    # The standard deviation of the connection will be half that of the clusters
    effective_std = 0.5 * c1_std

    t = np.random.beta(2.5, 2.5, size=num_points)[:, None]
    midpoints = t * c1_centroid + (1 - t) * c2_centroid
    midpoints += np.random.normal(0, effective_std * c1_std, size=midpoints.shape)

    return midpoints


def make_column(source_col: pd.Series, val_proportions: dict[str, dict[str, float]]) -> pd.Series:
    vals = pd.Series(pd.NA, index=source_col.index)

    for value in val_proportions:
        for group_id, p in val_proportions[value].items():
            # Determine which points are in this particular group
            mask = source_col == group_id
            group_idx = np.argwhere(mask).ravel()

            # How many samples do we need to set?
            num_samples = int(len(group_idx) * p)
            available_idx = set(np.argwhere(vals.isna()).ravel())
            used_idx = set(range(len(vals))) - available_idx
            group_available_idx = set(group_idx) - set(used_idx)
            if len(group_available_idx) < num_samples:
                num_samples = len(group_available_idx)

            idx_sample = np.random.choice(
                list(group_available_idx), size=num_samples, replace=False
            )
            vals.loc[idx_sample] = value

    return vals.astype("category")


def generate_values_in_range(n_samples, val_range, dist_params=(2, 2)):
    val_span = val_range[1] - val_range[0]
    return val_range[0] + np.random.beta(*dist_params, size=n_samples) * val_span


np.random.seed(0)

# Generate initial clusters
n_groups = 4
samples_per_group = [200, 200, 200, 300]
std = 0.6

angle = 2 * np.pi / n_groups
r = 4

x, y = [], []
for group_idx in range(n_groups):
    n_samples = samples_per_group[group_idx]
    xi = np.random.normal(loc=0, scale=std, size=(n_samples, 2))
    xi = (xi + [0, r]) @ rotate(group_idx * angle)

    yi = [f"C{group_idx}"] * n_samples
    x.append(xi), y.append(yi)

x = np.vstack(x)
x = x @ rotate(2 * np.pi / 360 * 45)

y = pd.Series(np.hstack(y))
y = y.replace({"C0": "top-right", "C1": "bottom-right", "C2": "bottom-left", "C3": "top-left"})


# Make connections between clusters
to_connect = [
    ("connection-right", "top-right", "bottom-right", 200),
    ("connection-bottom", "bottom-right", "bottom-left", 200),
    ("connection-top", "top-right", "top-left", 200),
]
for name, c1, c2, n_samples in to_connect:
    midpoints = connect_clusters(x[y == c1], x[y == c2], num_points=n_samples)
    y_midpoints = [name] * midpoints.shape[0]

    x = np.vstack([x, midpoints])
    y = np.hstack([y, y_midpoints])

# x is finalized, convert to dataframe for easier saving
x = pd.DataFrame(x)

# Generate features
features = pd.DataFrame()
features["cluster"] = pd.Series(y).astype("category")
features["Language"] = make_column(
    features["cluster"],
    {
        "DE": {"top-right": 1},
        "EN": {"top-left": 1, "bottom-right": 1, "bottom-left": 1, "connection-bottom": 1, "connection-right": 0.2, "connection-top": 0.2},
    }
)
features["Genre"] = make_column(
    features["cluster"],
    {
        "Childrens": {"top-left": 0.75, "bottom-left": 1},
        "Science Fiction": {"bottom-right": 1},
        "Classics": {"top-right": 1},
    }
)
features["Country Purchased"] = make_column(
    features["cluster"],
    {
        "UK": {"bottom-left": 0.9, "bottom-right": 0.9, "connection-bottom": 0.8},
        "Germany": {"top-left": 0.9, "top-right": 0.9, "connection-top": 0.8},
    }
)
features["Number of Children"] = make_column(
    features["cluster"],
    {
        "0": {"bottom-left": 1, "bottom-right": 1, "connection-bottom": 1},
        "1": {"top-left": 1, "top-right": 0.75, "connection-top": 1},
    }
)
features["Use"] = make_column(
    features["cluster"],
    {
        "Personal": {"bottom-left": 1, "bottom-right": 1, "top-right": 1, "connection-bottom": 1, "connection-right": 1},
        "Gift": {"top-left": 1},
    }
)

# Generate year-bought feature
year_bought = np.full_like(features["cluster"], np.nan, dtype=np.float32)
birth_year = 1970

mask = features["cluster"] == "bottom-left"
year_bought[mask] = generate_values_in_range(
    mask.sum(), [birth_year + 5, birth_year + 8], dist_params=(1, 1)
)

mask = features["cluster"] == "connection-bottom"
year_bought[mask] = generate_values_in_range(
    mask.sum(), [birth_year + 8, birth_year + 12], dist_params=(1, 1)
)

mask = features["cluster"] == "bottom-right"
year_bought[mask] = generate_values_in_range(
    mask.sum(), [birth_year + 12, birth_year + 18], dist_params=(1, 1)
)

mask = features["cluster"] == "connection-right"
year_bought[mask] = generate_values_in_range(
    mask.sum(), [birth_year + 18, birth_year + 24], dist_params=(1, 1)
)

mask = features["cluster"] == "top-right"
year_bought[mask] = generate_values_in_range(
    mask.sum(), [birth_year + 24, birth_year + 80], dist_params=(1, 1)
)

mask = features["cluster"] == "connection-top"
year_bought[mask] = generate_values_in_range(
    mask.sum(), [birth_year + 24, birth_year + 80], dist_params=(1, 1)
)

mask = features["cluster"] == "top-left"
year_bought[mask] = generate_values_in_range(
    mask.sum(), [birth_year + 24, birth_year + 80], dist_params=(1, 1)
)

features["Year Purchased"] = year_bought

# Generate num pages feature
num_pages = np.full_like(features["cluster"], np.nan, dtype=np.float32)

mask = features["cluster"].isin(["bottom-right", "connection-right", "top-right"])
num_pages[mask] = generate_values_in_range(mask.sum(), [150, 300], dist_params=(1, 1))

mask = features["cluster"].isin(["bottom-left", "top-left"])
num_pages[mask] = generate_values_in_range(mask.sum(), [20, 50], dist_params=(1, 1))

features["Number of Pages"] = num_pages

# Write files to disk
x.to_csv(os.path.join(DATA_DIR, "bookwork_embedding.csv"), index=False)
features.to_csv(os.path.join(DATA_DIR, "bookwork_features.csv"), index=False)
