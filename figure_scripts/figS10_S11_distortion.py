"""Effect of down-weighting poorly embedded samples during region construction
(supplement, Figs. S10 and S11).

The per-sample distortion measure is k-nearest-neighbor preservation: the
fraction of a sample's k nearest neighbors in the input space that are also
among its k nearest neighbors in the embedding. It lies in [0, 1] and serves
as the sample weight as it is.
The weight multiplies the indicator values that act as KDE weights
(`generate_region_annotations(..., sample_weights=...)`).

For each entry of `FIGURE_VARIABLES`, the script runs region construction with
and without the weights and renders the embedding colored by preservation, the
outlines of the regions of three variables without and with weights, with a
legend of their rules, and the labelled regions of two further variables, each
without and with weights. The figures go to
`figures/fig_supp_distortion-ENTRY.{pdf,png}`, with `:` in the entry replaced
by `-` and, for k other than N_NEIGHBORS, `-k{k}` appended.

An entry is a dataset name, for the embedding the manuscript shows, or
`name:pca` for a two-component PCA computed here from the rebuilt input space,
a linear projection that preserves neighborhoods poorly. Computed embeddings
and preservation scores are cached in `cache/distortion/`, not stored with
the data. The input space is rebuilt
from `features.csv` with the preprocessing of vera's `experiments/datasets.py`
(`INPUT_SPACES`).

Usage: python figS10_S11_distortion.py [--k 100]
Requires a vera with `sample_weights` support.
"""
import argparse
import os
from importlib.util import module_from_spec, spec_from_file_location
from unittest import mock

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import glasbey
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

import vera

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "cache", "distortion")
FIG_DIR = os.path.join(HERE, "figures")

N_NEIGHBORS = 100
RANDOM_STATE = 0
# The smallest axis padding VERA's label placement tries, as a fraction of the
# data frame on each side
LABEL_PADDING = 0.1
# Panel a colors samples by weight on a diverging scale centered at one half,
# red (poorly preserved) through grey to blue (well preserved), drawing the
# poorly preserved ones on top
WEIGHT_CMAP = mcolors.LinearSegmentedColormap.from_list("recall", [(0, "#ff0000"), (0.5, "#b4b4b4"), (1, "#0000b3")])
# Space, in panel heights, for the "without weights" and "with weights"
# captions between the rows, and for the brackets that join each pair of
# labelled panels below the last row
CAPTION_GAP = 0.1
BRACKET_SPACE = 0.13


def load_module(name, rel):
    spec = spec_from_file_location(name, os.path.join(HERE, "..", "supplement-data", rel))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ds = load_module("_supplement_datasets", "datasets.py")
fs = load_module("_supplement_figstyle", "figstyle.py")

# Per entry: the variables whose region outlines without and with weights are
# overlaid in panels b-d, the two variables whose labelled regions panels e-f
# and g-h show without and with weights, and optionally, per labelled
# variable, keyword arguments that override `figstyle.RULE_LABEL_KWARGS`
FIGURE_VARIABLES = {
    "abalone": dict(
        overlays=["shucked weight", "diameter", "sex"],
        labelled=["length", "shell weight"],
    ),
    "attrition:pca": dict(
        overlays=["YearsSinceLastPromotion", "YearsInCurrentRole", "YearsWithCurrManager"],
        labelled=["MonthlyIncome", "JobRole"],
        # Wrapped at 28 characters, the JobRole label of panel g takes eight
        # lines and does not fit inside the panel
        rule_label_kwargs={"JobRole": dict(max_width=32)},
    ),
}

# How the input space is rebuilt from the stored features: the method of the
# stored embedding (`embedding.csv`), the columns used (or all but `exclude`),
# whether continuous columns are standardized, and the metric
INPUT_SPACES = {
    "abalone": dict(embedding="umap", columns=["length", "diameter", "height", "whole weight", "shucked weight",
                             "viscera weight", "shell weight", "age"],
                    standardize=True, metric="cosine"),
    "attrition": dict(embedding="tsne", exclude=["Attrition"], standardize=True, metric="euclidean"),
}


def input_space(features: pd.DataFrame, spec: dict) -> np.ndarray:
    if "columns" in spec:
        x = features[spec["columns"]].copy()
    else:
        x = features.drop(columns=spec["exclude"])
    numeric = [c for c in x.columns if pd.api.types.is_numeric_dtype(x[c])]
    if spec["standardize"] and numeric:
        x[numeric] = StandardScaler().fit_transform(x[numeric].values)
    return pd.get_dummies(x).values.astype(np.float32)


def pca_embedding(name: str, x: np.ndarray) -> np.ndarray:
    os.makedirs(CACHE_DIR, exist_ok=True)
    fname = os.path.join(CACHE_DIR, f"{name}-pca-embedding.npy")
    if os.path.exists(fname):
        return np.load(fname)
    embedding = PCA(n_components=2).fit_transform(x)
    np.save(fname, embedding)
    return embedding


def load(entry: str):
    """The dataset of `entry` with the embedding it names, its variant, and
    the rebuilt input space with its metric."""
    name, _, variant = entry.partition(":")
    spec = dict(INPUT_SPACES[name])
    dataset = ds.Dataset.load(name)
    x = input_space(dataset.features, spec)
    if variant == "pca":
        # Computed here from the rebuilt input space with the Euclidean metric
        dataset.embedding = pca_embedding(name, x)
        spec["metric"] = "euclidean"
    else:
        variant = spec["embedding"]
    return name, variant, dataset, x, spec["metric"]


def knn_preservation(x, embedding, k, metric) -> np.ndarray:
    """Fraction of each point's k input-space neighbors that are also among its
    k embedding neighbors."""
    def neighbors(data, metric):
        nn = NearestNeighbors(n_neighbors=k + 1, metric=metric, n_jobs=-1).fit(data)
        idx = nn.kneighbors(data, return_distance=False)
        # Drop the query point itself, wherever ties placed it
        return [set(row[row != q][:k]) for q, row in enumerate(idx)]

    hd = neighbors(x, metric)
    ld = neighbors(embedding, "euclidean")
    return np.array([len(a & b) / k for a, b in zip(hd, ld)])


def preservation_for(name: str, variant: str, x, embedding, metric: str, k: int) -> np.ndarray:
    os.makedirs(CACHE_DIR, exist_ok=True)
    fname = os.path.join(CACHE_DIR, f"{name}-{variant}-knn{k}.npz")
    if os.path.exists(fname):
        cached = np.load(fname)
        if cached["preservation"].shape[0] == embedding.shape[0]:
            return cached["preservation"]
    preservation = knn_preservation(x, embedding, k, metric)
    np.savez(fname, preservation=preservation)
    return preservation


def region_annotation_groups(features, embedding, indicator_columns, sample_weights=None):
    return vera.an.generate_region_annotations(
        features,
        embedding,
        sample_size=None,
        indicator_columns=indicator_columns,
        sample_weights=sample_weights,
        random_state=RANDOM_STATE,
    )


def variable_name(ra) -> str:
    base = getattr(ra.descriptor, "base_variable", None)
    return base.name if base is not None else str(ra.descriptor)


def variable_group(groups, variable):
    return {variable_name(group[0]): group for group in groups}[variable]


def plot_outline(ax, polygon, **kwargs):
    for part in polygon.geoms:
        ax.plot(*part.exterior.xy, **kwargs)
        for hole in part.interiors:
            ax.plot(*hole.xy, **kwargs)


def descriptor_order(groups):
    """The distinct rules of `groups`, ordered by value."""
    descriptors = {str(ra.descriptor): ra.descriptor for group in groups for ra in group}
    return [str(d) for d in sorted(descriptors.values())]


def descriptor_palette(groups):
    """One color per rule, shared by every panel that shows it."""
    descriptors = sorted({str(ra.descriptor) for group in groups for ra in group})
    colors = plt.get_cmap("tab10").colors
    if len(descriptors) > len(colors):
        colors = [mcolors.to_rgb(c) for c in glasbey.extend_palette("tab10", palette_size=len(descriptors))]
    return dict(zip(descriptors, colors))


def open_space(fig, axes, ncols: int):
    """Widen the gaps between rows to `CAPTION_GAP` panel heights and add
    `BRACKET_SPACE` panel heights below the last row, keeping every panel's
    size and the figure's width."""
    width, height = fig.get_size_inches()
    # The original positions: the active ones re-apply each panel's aspect to
    # the figure's current size
    positions = [ax.get_position(original=True) for ax in axes]
    panel = positions[0].height * height
    extra = panel * (CAPTION_GAP - fs.PANEL_GAP)
    bottom = panel * BRACKET_SPACE
    nrows = int(np.ceil(len(axes) / ncols))
    new_height = height + extra * (nrows - 1) + bottom
    fig.set_size_inches(width, new_height)
    for i, (ax, pos) in enumerate(zip(axes, positions)):
        # Every row moves up by the space below it
        y0 = pos.y0 * height + extra * (nrows - 1 - i // ncols) + bottom
        ax.set_position([pos.x0, y0 / new_height, pos.width, pos.height * height / new_height])


def group_pair(fig, pair, variable: str):
    """Caption two adjacent panels "without weights" and "with weights" above
    them, and join them below with a bracket, its ends turned up, over the
    variable's name."""
    left, right = (ax.get_position() for ax in pair)
    for pos, caption in zip((left, right), ["without weights", "with weights"]):
        fig.text((pos.x0 + pos.x1) / 2, pos.y1 + left.height * 0.012, caption, ha="center", va="bottom",
                 fontsize=4, fontfamily="Arial")
    space = left.height * BRACKET_SPACE
    y, tick = left.y0 - space * 0.25, space * 0.15
    fig.add_artist(plt.Line2D([left.x0, left.x0, right.x1, right.x1], [y + tick, y, y, y + tick],
                              transform=fig.transFigure, color="black", lw=0.5))
    fig.text((left.x0 + right.x1) / 2, y - space * 0.08, variable, ha="center", va="top",
             fontsize=5, fontfamily="Arial")


def figure(entry: str, k: int):
    name, variant, dataset, x, metric = load(entry)
    embedding = dataset.embedding
    preservation = preservation_for(name, variant, x, embedding, metric, k)
    features = dataset.features
    plain = region_annotation_groups(features, embedding, dataset.indicator_columns)
    weighted = region_annotation_groups(features, embedding, dataset.indicator_columns, preservation)
    spec = FIGURE_VARIABLES[entry]

    fs.setup()
    n_panels = 1 + len(spec["overlays"]) + 2 * len(spec["labelled"])
    ncols = 4
    fig, axes = fs.grid(int(np.ceil(n_panels / ncols)), ncols, figwidth=fs.SUPPLEMENT_TEXTWIDTH_IN)

    ax = axes[0]
    order = np.argsort(-preservation, kind="stable")
    points = ax.scatter(*embedding[order].T, c=preservation[order], cmap=WEIGHT_CMAP, vmin=0, vmax=1,
                        **fs.SCATTER_KWARGS)
    cax = ax.inset_axes([0.62, 0.06, 0.32, 0.03])
    cbar = fig.colorbar(points, cax=cax, orientation="horizontal", ticks=[0, 0.5, 1])
    cbar.ax.tick_params(labelsize=4, length=1.5, width=0.3, pad=1)
    cbar.outline.set_linewidth(0.3)
    cbar.set_label("sample weight", fontsize=4, labelpad=1)
    cbar.ax.xaxis.set_label_position("top")

    # Every panel shows the data in one square frame: the data's square
    # bounding box with matplotlib's default 5% margins, padded on each side by
    # LABEL_PADDING. VERA's label placement tries several paddings and keeps
    # the best-scoring one, which would size the labelled panels differently;
    # replacing its padding function makes it place labels in this frame
    center = (embedding.min(axis=0) + embedding.max(axis=0)) / 2
    half = (embedding.max(axis=0) - embedding.min(axis=0)).max() / 2 * 1.1 * (1 + 2 * LABEL_PADDING)
    frame = (center[0] - half, center[1] - half, center[0] + half, center[1] + half)

    overlay_axes = axes[1:1 + len(spec["overlays"])]
    for ax, variable in zip(overlay_axes, spec["overlays"]):
        pair = [variable_group(groups, variable) for groups in (plain, weighted)]
        palette = descriptor_palette(pair)
        ax.scatter(*embedding.T, c="#c8c8c8", **fs.SCATTER_KWARGS)
        for group, linestyle in zip(pair, ["--", "-"]):
            for ra in group:
                plot_outline(ax, ra.region.polygon, color=palette[str(ra.descriptor)],
                             lw=0.6, linestyle=linestyle)
        ax.text(0.5, 0.02, variable, transform=ax.transAxes, ha="center", va="bottom",
                fontsize=4, fontfamily="Arial")
        # A legend names the rule behind each color
        rules = descriptor_order(pair)
        handles = [plt.Line2D([], [], color=palette[rule], lw=0.6) for rule in rules]
        ax.legend(handles, rules, loc="upper right", frameon=False, handlelength=1.2, handletextpad=0.4,
                  labelspacing=0.2, borderaxespad=0.3, prop={"size": 4, "family": "Arial"})

    # Each labelled variable takes two adjacent panels, without and with weights
    labelled_axes = axes[1 + len(spec["overlays"]):n_panels]
    pairs = []
    for i, variable in enumerate(spec["labelled"]):
        shown = [variable_group(groups, variable) for groups in (plain, weighted)]
        palette = descriptor_palette(shown)
        pair = labelled_axes[2 * i:2 * i + 2]
        rule_label_kwargs = {**fs.RULE_LABEL_KWARGS, **spec.get("rule_label_kwargs", {}).get(variable, {})}
        for ax, group in zip(pair, shown):
            with mock.patch.object(vera.pl, "add_bbox_padding", lambda bbox, padding: frame):
                vera.pl.plot_annotation(
                    group, ax=ax, ra_colors={ra: palette[str(ra.descriptor)] for ra in group},
                    label_kwargs=fs.LABEL_KWARGS, scatter_kwargs=fs.SCATTER_KWARGS,
                    leader_kwargs=fs.LEADER_KWARGS, **rule_label_kwargs,
                )
        pairs.append((pair, variable))

    for i, ax in enumerate(axes):
        if i >= n_panels:
            fs.blank(ax)
            continue
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_xlim(frame[0], frame[2])
        ax.set_ylim(frame[1], frame[3])
        ax.set_aspect("equal", adjustable="box")
        fs.letter(ax, i)

    # VERA places labels for the figure's size, so the space that holds the
    # pair captions and brackets opens only once the labels are in place
    open_space(fig, axes, ncols)
    for pair, variable in pairs:
        group_pair(fig, pair, variable)

    os.makedirs(FIG_DIR, exist_ok=True)
    name = f"fig_supp_distortion-{entry.replace(':', '-')}" + ("" if k == N_NEIGHBORS else f"-k{k}")
    fs.save(fig, os.path.join(FIG_DIR, name), pad_inches=0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--k", type=int, default=N_NEIGHBORS)
    args = parser.parse_args(argv)
    for entry in FIGURE_VARIABLES:
        print(f"== figure {entry}, k={args.k}", flush=True)
        figure(entry, args.k)


if __name__ == "__main__":
    main()
