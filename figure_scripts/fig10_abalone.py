"""Render the abalone case-study figure of the manuscript (Fig. 10,
`fig:abalone`, `case_study-abalone.pdf`).

VERA's contrastive explanations of the UMAP embedding of the Abalone dataset
(`supplement-data/data/abalone`). The figure does not use VERA's defaults:
regions are merged post hoc at a maximum overlap of 0.9 (default 0.8), and
features are merged contrastively at a Jaccard similarity of 0.75 (default
0.95). At the defaults no two features merge, and panels (c) and (d) would
each show a single feature. At these settings VERA builds six contrastive
explanations; the figure shows four of them, chosen by hand: age, sex, the
three weights (shucked, viscera, whole), and the two size measurements
(diameter, length). Height and shell weight are left out.

Writes `figures/case_study-abalone.pdf` and `.png`, a single-column figure.

Usage: python fig10_abalone.py
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

REGION_KWARGS = dict(
    n_discretization_bins=5,
    scale_factor=1,
    contour_level=0.25,
    merge_min_sample_overlap=0.9,
)
CONTRASTIVE_MERGE_THRESHOLD = 0.75
# The features of each panel, in panel order
PANELS = [
    {"age"},
    {"sex"},
    {"shucked weight", "viscera weight", "whole weight"},
    {"diameter", "length"},
]
TITLE = "Abalone - Contrastive Explanations"
# Axis padding of every panel, as a fraction of the embedding's extent, so
# that the embedding is drawn at one size in all of them; VERA's own choice
# varies per panel
PADDING = 0.25


def features_of(layout):
    """The base features a contrastive layout describes. A descriptor is an
    indicator variable, or a merge of several with `variables`."""
    names = set()
    for ra in layout:
        for v in getattr(ra.descriptor, "variables", [ra.descriptor]):
            while getattr(v, "base_variable", None) is not None:
                v = v.base_variable
            names.add(v.name)
    return names


def main():
    fs.setup()
    data = ds.Dataset.load("abalone")
    region_annotations = vera.an.generate_region_annotations(
        data.features, data.embedding, indicator_columns=data.indicator_columns, **REGION_KWARGS,
    )
    layouts = vera.explain.contrastive(
        region_annotations, max_panels=len(region_annotations), filter_layouts=False,
        merge_threshold=CONTRASTIVE_MERGE_THRESHOLD,
    )
    by_features = {frozenset(features_of(layout)): layout for layout in layouts}
    missing = [sorted(p) for p in PANELS if frozenset(p) not in by_features]
    if missing:
        found = [sorted(f) for f in by_features]
        raise RuntimeError(f"no contrastive explanation of {missing}; VERA built {found}")

    X = data.embedding
    square = vera.label_placement.set_bbox_square_aspect(np.hstack([X.min(axis=0), X.max(axis=0)]))
    limits = vera.label_placement.add_bbox_padding(square, padding=(PADDING, PADDING))

    fig, axes = fs.grid(2, 2, figwidth=fs.COLWIDTH_IN)
    for idx, (ax, panel) in enumerate(zip(axes, PANELS)):
        vera.pl.plot_annotation(
            by_features[frozenset(panel)], ax=ax, only_color_inside_members=False,
            indicate_membership=True, label_kwargs=fs.LABEL_KWARGS,
            scatter_kwargs=fs.SCATTER_KWARGS, leader_kwargs=fs.LEADER_KWARGS, axis_limits=limits,
        )
        fs.letter(ax, idx)
    fs.row_title(axes[0], TITLE)

    os.makedirs(FIG_DIR, exist_ok=True)
    fs.save(fig, os.path.join(FIG_DIR, "case_study-abalone"), pad_inches=0)
    print(f"wrote {os.path.join(FIG_DIR, 'case_study-abalone')}.pdf")


if __name__ == "__main__":
    main()
