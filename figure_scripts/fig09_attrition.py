"""Render the attrition case-study figure of the manuscript (Fig. 9,
`fig:attrition`, `case_study-attrition.pdf`).

VERA's four top-ranked contrastive explanations (a-d) and four descriptive
explanations (e-h) of the t-SNE embedding of the IBM Employee Attrition
dataset (`supplement-data/data/attrition`), at VERA's default parameters.

The contrastive panels share colors across panels: panel (a) takes VERA's
default colors, and a region of a later panel takes the color of the region
of (a) that holds at least half of its samples, the largest regions choosing
first, so that one cluster is drawn in one color throughout. The regions
left without a color then take the panel's free colors in palette order
(`figstyle.matched_colors`). The
descriptive panels color each descriptor consistently across panels, as
VERA does.

Writes `figures/case_study-attrition.pdf` and `.png`, a full-width figure.

Usage: python fig09_attrition.py
"""
import os
from importlib.util import module_from_spec, spec_from_file_location

import matplotlib
matplotlib.use("Agg")

import numpy as np  # noqa: E402
import vera  # noqa: E402
import vera.explain  # noqa: E402
import vera.label_placement  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "figures")


def load_module(name, rel):
    spec = spec_from_file_location(name, os.path.join(HERE, "..", "supplement-data", rel))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ds = load_module("_supplement_datasets", "datasets.py")
fs = load_module("_supplement_figstyle", "figstyle.py")

# VERA's defaults; the seed fixes the k-means discretization
RANDOM_STATE = 0
N_PANELS = 4
# Axis padding of every panel, as a fraction of the embedding's extent, so
# that the embedding is drawn at one size in all of them; the descriptive
# labels, of up to seven rules, need this much room
PADDING = 0.8
# Line width of the descriptive labels, in characters; at VERA's default of
# 40 the two labels below panel (e) overlap
DESCRIPTIVE_LABEL_WIDTH = 32


def main():
    fs.setup()
    data = ds.Dataset.load("attrition")
    region_annotations = vera.an.generate_region_annotations(
        data.features, data.embedding, indicator_columns=data.indicator_columns, random_state=RANDOM_STATE,
    )
    contrastive = vera.explain.contrastive(region_annotations, max_panels=N_PANELS)
    descriptive = vera.explain.descriptive(region_annotations, max_panels=N_PANELS)

    X = data.embedding
    square = vera.label_placement.set_bbox_square_aspect(np.hstack([X.min(axis=0), X.max(axis=0)]))
    limits = vera.label_placement.add_bbox_padding(square, padding=(PADDING, PADDING))
    kwargs = dict(indicate_membership=True, label_kwargs=fs.LABEL_KWARGS, scatter_kwargs=fs.SCATTER_KWARGS,
                  leader_kwargs=fs.LEADER_KWARGS, axis_limits=limits)

    fig, axes = fs.grid(2, N_PANELS, figwidth=fs.TEXTWIDTH_IN, row_titles=True)
    contrastive_colors = fs.matched_colors(contrastive)
    for ax, layout in zip(axes[:N_PANELS], contrastive):
        vera.pl.plot_annotation(layout, ax=ax, ra_colors=contrastive_colors, only_color_inside_members=False,
                                **kwargs)
    descriptive_colors = vera.pl.layout_variable_colors(descriptive)
    for ax, layout in zip(axes[N_PANELS:], descriptive):
        vera.pl.plot_annotation(layout, ax=ax, ra_colors=descriptive_colors, max_width=DESCRIPTIVE_LABEL_WIDTH,
                                **kwargs)
    for idx, ax in enumerate(axes):
        fs.letter(ax, idx)
    fs.row_title(axes[0], "Contrastive Explanations", fontsize=10)
    fs.row_title(axes[N_PANELS], "Descriptive Explanations", fontsize=10)

    os.makedirs(FIG_DIR, exist_ok=True)
    fs.save(fig, os.path.join(FIG_DIR, "case_study-attrition"), pad_inches=0)
    print(f"wrote {os.path.join(FIG_DIR, 'case_study-attrition')}.pdf")


if __name__ == "__main__":
    main()
