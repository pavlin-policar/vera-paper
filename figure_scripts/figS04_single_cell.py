"""The supplement's single-cell figure (Fig. S4): VERA on four single-cell
RNA-seq data sets, given gene expression as binary indicators.

For each data set and embedding of `supplement_figure` in
config_single_cell.json, the script
  * selects the explanatory genes without reference to cell types: the genes
    with the largest analytic Pearson-residual variance on the raw counts,
  * runs VERA on one binary indicator per gene, flagging the cells whose
    log-normalized expression exceeds a threshold, and builds its descriptive
    explanations, their descriptors ranked by purity lift,
  * draws the published cell types, which VERA never sees, next to VERA's
    first three descriptive panels, the canonical markers of each region's
    majority cell type set in bold.
Fig. S4 has one such row per data set; each row is also saved as a figure of
its own.

VERA's layouts are cached in `cache/single_cell/<data set>-<embedding>-layout.pkl`
and the figures are drawn from them; a data set without a cached layout, or
every data set with --recompute, is run through VERA from the preprocessed
data that prepare_single_cell.py writes to `cache/single_cell/<data set>.npz`.

Writes figures/fig_supp_singlecell.{pdf,png} and
figures/singlecell-<data set>.{pdf,png}.

Usage: python figS04_single_cell.py [--recompute]
"""
import argparse
import json
import os
import pickle
import re
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patheffects  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import vera  # noqa: E402
import vera.explain  # noqa: E402
from vera.label_placement import Label  # noqa: E402
from vera.plotting import _format_descriptor_lines  # noqa: E402
from vera import metrics  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "cache", "single_cell")
FIG_DIR = os.path.join(HERE, "figures")
CONFIG = os.path.join(HERE, "config_single_cell.json")


def load_module(name, rel):
    spec = spec_from_file_location(name, os.path.join(HERE, "..", "supplement-data", rel))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fs = load_module("_supplement_figstyle", "figstyle.py")


# --------------------------------------------------------------------------
# VERA
# --------------------------------------------------------------------------
def load_data(name):
    """The log-normalized expression, embeddings, cell types, and gene
    ranking that prepare_single_cell.py writes."""
    z = np.load(os.path.join(CACHE_DIR, f"{name}.npz"), allow_pickle=True)
    expr = pd.DataFrame(z["expr"], index=z["cells"], columns=z["genes"])
    embeddings = {"tsne": z["tsne"], "umap": z["umap"]}
    return expr, embeddings, pd.Series(z["labels"], index=z["cells"]), pd.Series(z["resvar"], index=z["all_genes"])


def rerank(layout, method):
    for panel in layout:
        for ra in panel:
            ra.descriptor = ra.descriptor.ranked_by(
                lambda ra=ra: metrics.descriptor_scores(ra, method=method)
            )


def compute_layout(name, emb_name, cfg):
    """VERA's descriptive layout of one data set and embedding, with the cell
    types of the cells it is computed on."""
    dcfg = cfg["datasets"][name]
    expr, embeddings, labels, resvar = load_data(name)
    genes = list(resvar.sort_values(ascending=False).index)[:cfg["explanatory_genes"]["n_genes"]]
    threshold = dcfg.get("indicator_threshold", cfg["indicators"]["threshold"])
    # One boolean indicator per gene: is it expressed above the threshold?
    features = expr[genes] > threshold
    embedding = embeddings[emb_name]
    lab = labels.values
    # Draw VERA's sample here, as VERA would draw it, so that region members
    # index the same cells as the labels; a data set may set its own sample
    # size, and None uses every cell
    region_kwargs = dict(cfg["region_defaults"])
    n_sample = dcfg.get("sample_size", region_kwargs.pop("sample_size"))
    if n_sample is not None and len(features) > n_sample:
        idx = np.random.RandomState(region_kwargs["random_state"]).choice(len(features), n_sample, replace=False)
        features, embedding, lab = features.iloc[idx], embedding[idx], lab[idx]
    print(f"[{name} {emb_name}] {features.shape[0]} cells, {features.shape[1]} gene indicators", flush=True)
    ra = vera.an.generate_region_annotations(
        features, embedding, indicator_columns="all",
        uninformative_max_sample_coverage=cfg["indicators"]["uninformative_max_sample_coverage"],
        sample_size=None, **region_kwargs,
    )
    des = vera.explain.descriptive(ra, **cfg["descriptive_defaults"])
    rerank(des, cfg["descriptor_ranking"])
    return {"des": des, "lab": lab, "colors": None, "threshold": threshold}


def layout(name, emb_name, cfg, recompute=False):
    """The cached layout of one data set and embedding, computed and cached
    first if there is none or `recompute` is set."""
    path = os.path.join(CACHE_DIR, f"{name}-{emb_name}-layout.pkl")
    if os.path.exists(path) and not recompute:
        with open(path, "rb") as f:
            return pickle.load(f)
    saved = compute_layout(name, emb_name, cfg)
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(saved, f)
    return saved


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
def composition(idx, labels):
    """The majority cell type of the cells at positions `idx`."""
    idx = list(idx)
    if not idx:
        return None
    return Counter(labels[idx]).most_common(1)[0][0]


def scatter_kwargs(n):
    """Point style for `n` cells: points shrink for data sets with more than
    5,000 cells, so that dense clusters do not hide one another."""
    return {**fs.SCATTER_KWARGS, "s": fs.SCATTER_KWARGS["s"] * min(1.0, (5000 / n) ** 0.5)}


def square_frame(X, padding):
    """(x_min, y_min, x_max, y_max) of a square centred on the points `X`,
    spanning their larger extent plus `padding` of it on each side."""
    (cx, cy) = (X.min(axis=0) + X.max(axis=0)) / 2
    half = (X.max(axis=0) - X.min(axis=0)).max() * (0.5 + padding)
    return cx - half, cy - half, cx + half, cy + half


def plot_reference(ax, embedding, labels, cell_types, palette=None, cell_colors=None, padding=0.05):
    """The published cell types; `cell_types` maps each to its short name.
    `palette` maps cell types to the data set's standard colours, and
    `cell_colors`, when given, colours each cell instead."""
    colors = plt.get_cmap("tab10").colors
    if len(cell_types) > 10:
        colors = plt.get_cmap("tab20").colors + plt.get_cmap("tab20b").colors[::2]
    if cell_colors is not None:
        ax.scatter(embedding[:, 0], embedding[:, 1], c=cell_colors, **scatter_kwargs(len(embedding)))
    for i, (ct, short) in enumerate(cell_types.items()):
        m = labels == ct
        if not m.any():
            continue
        if cell_colors is None:
            c = palette[ct] if palette else colors[i % len(colors)]
            ax.scatter(embedding[m, 0], embedding[m, 1], c=[c], **scatter_kwargs(len(embedding)))
        cx, cy = np.median(embedding[m], axis=0)
        # Names sit on the data with a thin white outline, as in scanpy's
        # `legend_loc="on data"`
        ax.text(cx, cy, short, ha="center", va="center", **fs.LABEL_KWARGS,
                path_effects=[patheffects.withStroke(linewidth=1.5, foreground="white")])
    x_min, y_min, x_max, y_max = square_frame(embedding, padding)
    ax.set(xticks=[], yticks=[], xlim=(x_min, x_max), ylim=(y_min, y_max))


def label_format(cfg):
    """How VERA's labels are written: the manuscript's indicator style, with
    the line width and truncation marker of `cfg["labels"]` when given."""
    return {"truncation_template": "(+{n} more)", **fs.INDICATOR_LABEL_KWARGS, **cfg.get("labels", {})}


def highlight_markers(ax, panel, cell_labels, cfg, markers_by_gene, max_descriptors):
    """Set in bold the canonical markers in a region's label whose cell types
    include the region's majority cell type. Labels are matched to regions by
    their text, whose lines VERA builds with `_format_descriptor_lines` and
    draws as the lines of a `Label` artist."""
    labels = {a.get_text(): a for a in ax.artists if isinstance(a, Label)}
    for ra in panel:
        majority = composition(ra.contained_samples, cell_labels)
        markers = [g for g, types in markers_by_gene.items() if majority in types]
        lines = _format_descriptor_lines(ra.descriptor, max_descriptors=max_descriptors, **label_format(cfg))
        label = labels.get("\n".join(line for line, _ in lines))
        if label is None:
            print(f"  could not match the label of {ra.descriptor} to its text", flush=True)
            continue
        if not markers:
            continue
        pattern = r"(?<![\w-])(" + "|".join(map(re.escape, markers)) + r")(?![\w-])"
        for t in label.texts:
            t.set_text(re.sub(pattern, r"$\\mathbf{\1}$", t.get_text()))


def draw_panels(axes, layout, cfg, dcfg, cell_labels, reference=False, cell_colors=None, first_letter=0):
    """VERA panels into `axes`, canonical markers in bold; with `reference`, the
    first axis shows the published cell types.

    Every panel uses the same square frame relative to the data: the data's
    extent plus `cfg["frame_padding"]` of it on each side, so the embedding
    has the same size everywhere. VERA lays out its labels inside that frame
    instead of choosing its own padding per panel."""
    X = layout[0][0].region.embedding.X  # VERA's rescaled copy of the embedding
    colors = vera.pl.layout_variable_colors(layout)
    offset = int(reference)
    frame = square_frame(X, cfg["frame_padding"])
    # A data set with crowded panels shows fewer genes per label
    max_descriptors = dcfg.get("figure_max_descriptors", cfg["max_descriptors"])
    for i, ax in enumerate(axes[offset:]):
        if i >= len(layout):
            fs.blank(ax)
            continue
        vera.pl.plot_annotation(
            layout[i], ax=ax, ra_colors=colors, indicate_membership=True,
            max_descriptors=max_descriptors, label_kwargs=fs.LABEL_KWARGS,
            scatter_kwargs=scatter_kwargs(len(X)), leader_kwargs=fs.LEADER_KWARGS,
            axis_limits=frame, **label_format(cfg),
        )
        highlight_markers(ax, layout[i], cell_labels, cfg, dcfg["markers"], max_descriptors)
        fs.letter(ax, first_letter + i + offset)
    if reference:
        plot_reference(axes[0], X, cell_labels, dcfg["cell_types"],
                       dcfg.get("cell_type_colors"), cell_colors, padding=cfg["frame_padding"])
        axes[0].text(0.5, 0.03, f"{dcfg['label_source']}\n(reference only; not given to VERA)",
                     transform=axes[0].transAxes, ha="center", va="bottom", **fs.LABEL_KWARGS)
        fs.letter(axes[0], first_letter)


def draw_row(axes, saved, cfg, dcfg, first_letter=0):
    """One data set's row: the published cell types and VERA's first three
    descriptive panels, under the data set's name."""
    draw_panels(axes, saved["des"][:3], cfg, dcfg, saved["lab"], reference=True,
                cell_colors=saved["colors"], first_letter=first_letter)
    fs.row_title(axes[0], dcfg["name"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recompute", action="store_true",
                    help="run VERA again instead of drawing the cached layouts")
    args = ap.parse_args()
    with open(CONFIG) as f:
        cfg = json.load(f)
    fs.setup()
    # Bold marker names inside labels are typeset as mathtext in Arial
    matplotlib.rcParams.update({"mathtext.fontset": "custom", "mathtext.rm": "Arial",
                                "mathtext.bf": "Arial:bold"})
    entries = cfg["supplement_figure"]
    os.makedirs(FIG_DIR, exist_ok=True)

    fig, axes = fs.grid(len(entries), 4, figwidth=fs.SUPPLEMENT_TEXTWIDTH_IN, row_titles=True)
    for r, entry in enumerate(entries):
        saved = layout(entry["dataset"], entry["embedding"], cfg, args.recompute)
        draw_row(axes[4 * r:4 * (r + 1)], saved, cfg, cfg["datasets"][entry["dataset"]], first_letter=4 * r)
    fs.save(fig, os.path.join(FIG_DIR, "fig_supp_singlecell"), pad_inches=0)
    print(f"wrote {os.path.join(FIG_DIR, 'fig_supp_singlecell')}.pdf", flush=True)

    # Each row on its own, drawn from the cached layout (read again, so that
    # it is drawn from the same state as in Fig. S4)
    for entry in entries:
        saved = layout(entry["dataset"], entry["embedding"], cfg)
        fig, axes = fs.grid(1, 4, figwidth=fs.SUPPLEMENT_TEXTWIDTH_IN, row_titles=True)
        draw_row(axes, saved, cfg, cfg["datasets"][entry["dataset"]])
        path = os.path.join(FIG_DIR, f"singlecell-{entry['dataset']}")
        fs.save(fig, path, pad_inches=0)
        print(f"wrote {path}.pdf", flush=True)


if __name__ == "__main__":
    main()
