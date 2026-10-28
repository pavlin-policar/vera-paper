"""
The parameter-sensitivity figures of the supplementary material (Figs.
S5-S9), on the abalone embedding.

Each figure is a single grid whose rows carry a bold row title, drawn in the
style of the supplement's other figures (figstyle):
  - region-bins, region-bandwidth, region-merge: the regions of four
    attributes, one per column, at a low, the default, and a high value of
    the discretization bins, the bandwidth scale factor, and the post hoc
    merge threshold, one value per row;
  - contrastive-parameters: the contrastive explanations at three
    contrastive merge thresholds (contrastive_rows), one per row, following
    the panels of four attributes;
  - descriptive-parameters: the descriptive explanations at the defaults,
    without background enrichment, and at the largest overlap tolerance swept.

Every parameter not named in a row is at its default, that of the
parameter study (../parameter-study/config.json). The figures are saved as
figures/fig_supp_<name>.{pdf,png}.

Usage:
    python figS05_S09_parameters.py
"""

import json
import os
from importlib.util import module_from_spec, spec_from_file_location

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.colors  # noqa: E402
import matplotlib.transforms  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import vera  # noqa: E402
import vera.explain  # noqa: E402
import vera.label_placement  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "figures")
CONFIG = os.path.join(HERE, "..", "parameter-study", "config.json")


def load_module(name, rel):
    spec = spec_from_file_location(name, os.path.join(HERE, "..", "supplement-data", rel))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ds = load_module("_supplement_datasets", "datasets.py")
fs = load_module("_supplement_figstyle", "figstyle.py")

DATASET = "abalone"
# The attributes of the region figures, kept by VERA at every value shown:
# those of the manuscript's abalone figure, with height in place of sex. They
# are numeric, since the discretization changes only the bins of numeric
# attributes
REGION_ATTRIBUTES = ["age", "shucked weight", "diameter", "height"]
# (figure, parameter, row title of a value, values) of the region figures
REGION_FIGURES = [
    ("region-bins", "n_discretization_bins", "Discretization bins k = {:g}", [3, 5, 10]),
    ("region-bandwidth", "scale_factor", "Bandwidth scale factor {:g}", [0.25, 1, 2]),
    ("region-merge", "merge_min_sample_overlap", "Post hoc merge threshold {:g}", [0.5, 0.8, 0.95]),
]
# The contrastive merge thresholds of the contrastive figure's rows: as no
# abalone attributes merge above 0.8, 0.75 (the manuscript's abalone figure),
# 0.8, and the default
CONTRASTIVE_THRESHOLDS = [0.75, 0.8, 0.95]
# Attributes whose contrastive panels the contrastive figure follows across
# its rows, one per column, since the merge threshold changes which
# attributes are merged and the ranking changes with the merges, so that the
# top panels of the rows would show different attributes: whole weight,
# merged with viscera weight at 0.8 and also with shucked weight at 0.75,
# shucked weight, and the two highest-ranked attributes, which never merge
CONTRASTIVE_ATTRIBUTES = ["whole weight", "shucked weight", "length", "age"]
DESCRIPTIVE_ROWS = [
    ("Defaults (background enrichment on, overlap tolerance 0)", {}),
    ("Background enrichment off", {"enrich_with_background": False}),
    ("Overlap tolerance 0.25", {"max_overlap": 0.25}),
]
PANEL_TITLE = dict(fontsize=6, loc="left", pad=2)
ROW_TITLE_PT = 7
# Space between a row title and the panel titles below it, in points
ROW_TITLE_SPACE = 2.75
# Vertical gap between rows, in panel heights: room for the next row's
# panel and row titles
ROW_GAP = 0.23
# Axis padding of the region panels, as a fraction of the embedding's extent,
# the same in every panel so that the embedding is drawn at one size
REGION_PADDING = 0.3


def base_feature_names(ra):
    """Names of the input features a region annotation's descriptor draws on."""
    names = []
    for v in getattr(ra.descriptor, "variables", [ra.descriptor]):
        base = v
        while getattr(base, "base_variable", None) is not None:
            base = base.base_variable
        if base.name not in names:
            names.append(base.name)
    return names


def grid(nrows, ncols):
    """figstyle's grid of square panels filling the supplement's text width,
    with ROW_GAP between rows."""
    width = fs.SUPPLEMENT_TEXTWIDTH_IN
    panel = width / (ncols + (ncols - 1) * fs.PANEL_GAP)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, dpi=150,
                             figsize=(width, panel * (nrows + (nrows - 1) * ROW_GAP)))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=fs.PANEL_GAP, hspace=ROW_GAP)
    return fig, np.asarray(axes).reshape(nrows, ncols)


def row_titles(fig, axes, titles):
    """Each row's title, left-aligned with its first panel, just above the
    row's panel titles, or above its panels where they have none."""
    renderer = fig.canvas.get_renderer()
    to_figure = fig.transFigure.inverted()
    height = fig.get_size_inches()[1]
    for row, text in zip(axes, titles):
        tops = [row[0].get_position().y1]
        tops += [t.get_window_extent(renderer).transformed(to_figure).y1
                 for ax in row for t in (ax.title, ax._left_title) if t.get_text()]
        fig.text(row[0].get_position().x0, max(tops) + ROW_TITLE_SPACE / 72 / height, text,
                 fontsize=ROW_TITLE_PT, fontweight="bold", ha="left", va="bottom")


def save(fig, name):
    """Saved as figures/fig_supp_<name>, spanning the figure's width (the
    supplement's text width) and reaching from the panels' bottom to just
    above the first row title."""
    renderer = fig.canvas.get_renderer()
    tight = fig.get_tightbbox(renderer)
    width = fig.get_size_inches()[0]
    area = matplotlib.transforms.Bbox([[min(0, tight.x0), tight.y0], [max(width, tight.x1), tight.y1 + 0.03]])
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, "fig_supp_" + name)
    fig.savefig(path + ".pdf", dpi=300, transparent=True, bbox_inches=area)
    fig.savefig(path + ".png", dpi=300, bbox_inches=area, facecolor="white")
    plt.close(fig)
    print(f"wrote {path}.pdf")


def rank_colors(group):
    """Colors of a numeric attribute's regions by the rank of their values: the
    lowest region blue, the highest green, and those between orange and then
    red (tab10), so that the ends of the range keep one color in every panel
    however many regions it is split into."""
    palette = [matplotlib.colors.to_rgb(c) for c in vera.pl.get_cmap_colors("tab10")]

    def bounds(ra):
        # The interval of the region's rule; a region's samples include
        # samples of other intervals, so their values would misorder it
        rules = [v.rule for v in getattr(ra.descriptor, "variables", [ra.descriptor])]
        return min(r.lower for r in rules), max(r.upper for r in rules)
    order = sorted(group, key=bounds)
    if len(order) == 1:
        return {order[0]: palette[0]}
    middle = [1, 3] + list(range(4, 10))
    indices = [0] + middle[:len(order) - 2] + [2]
    return {ra: palette[i] for ra, i in zip(order, indices)}


def matched_row_colors(rows, min_jaccard=0.5, by_column=False):
    """Region colors of rows of layouts, in which a region keeps the color of
    the region of the first row it matches. The first row takes VERA's colors;
    a later region takes the color of the first row's region with the same
    samples, or failing that the one with the largest Jaccard similarity of at
    least `min_jaccard` whose color is still free in its panel, and otherwise
    the color VERA gives it in its own row. With `by_column`, a region is
    matched only to the regions of the first row's panel in its column, as
    when the columns follow one attribute's panel and other panels hold
    regions of the same samples."""
    colors = vera.pl.layout_variable_colors(rows[0])
    reference = [[(set(ra.contained_samples), colors[ra]) for ra in layout] for layout in rows[0]]
    for row in rows[1:]:
        own = vera.pl.layout_variable_colors(row)
        for c, layout in enumerate(row):
            candidates = reference[c] if by_column else [x for panel in reference for x in panel]
            used = []
            for ra in sorted(layout, key=lambda r: len(r.contained_samples), reverse=True):
                samples = set(ra.contained_samples)
                scored = sorted(((len(samples & s) / len(samples | s), color) for s, color in candidates),
                                key=lambda x: x[0], reverse=True)
                match = next((color for j, color in scored if j >= min_jaccard and color not in used), None)
                colors[ra] = match if match is not None else own[ra]
                used.append(colors[ra])
    return colors


def label_problems(ax, letter, renderer, margin=1):
    """The labels on `ax` that come within `margin` points of its frame (the
    labels are clipped to the frame) or overlap the panel `letter`."""
    frame = ax.get_window_extent(renderer)
    m = margin * ax.figure.dpi / 72
    lb = letter.get_window_extent(renderer)
    out = []
    # VERA adds each label as one artist that draws a Text per line
    for t in ax.artists:
        if not isinstance(t, vera.label_placement.Label):
            continue
        b = t.get_window_extent(renderer)
        text = " ".join(line.get_text() for line in t.texts)[:40]
        if b.x0 < frame.x0 + m or b.x1 > frame.x1 - m or b.y0 < frame.y0 + m or b.y1 > frame.y1 - m:
            out.append(f"at the frame: {text!r}")
        if b.overlaps(lb):
            out.append(f"over the panel letter: {text!r}")
    return out


def report(fig, axes, name):
    renderer = fig.canvas.get_renderer()
    for i, ax in enumerate(np.ravel(axes)):
        if not ax.axison or not ax.texts:
            continue
        for problem in label_problems(ax, ax.texts[-1], renderer):
            print(f"[{name}] panel {'abcdefghijklmnopqrstuvwxyz'[i]}: label {problem}")


def data_limits(embedding, padding):
    """Axis limits of the square around `embedding`, padded by `padding` of its
    extent on every side."""
    X = embedding
    square = vera.label_placement.set_bbox_square_aspect(np.hstack([X.min(axis=0), X.max(axis=0)]))
    return vera.label_placement.add_bbox_padding(square, (padding, padding))


def plot(ax, layout, colors, axis_limits=None):
    labels = dict(fs.RULE_LABEL_KWARGS)
    vera.pl.plot_annotation(
        layout, ax=ax, ra_colors=colors, indicate_membership=True,
        label_kwargs=fs.LABEL_KWARGS, scatter_kwargs=fs.SCATTER_KWARGS,
        leader_kwargs=fs.LEADER_KWARGS, axis_limits=axis_limits, **labels,
    )


def attribute_regions(features, embedding, kwargs):
    """The regions of each of REGION_ATTRIBUTES and whether VERA keeps them:
    an attribute whose regions all merge into one is filtered as
    uninformative, and is then drawn with that single region."""
    attributes = REGION_ATTRIBUTES

    def find(groups):
        return {a: g for g in groups for a in attributes if a in base_feature_names(g[0])}
    kept = find(vera.an.generate_region_annotations(features, embedding, **kwargs))
    out = {a: (kept[a], True) for a in kept}
    if len(out) < len(attributes):
        unfiltered = find(vera.an.generate_region_annotations(
            features, embedding, filter_uninformative=False, **kwargs))
        out.update({a: (unfiltered[a], False) for a in attributes if a not in out})
    return out


def region_colors(group, default_group, features, attribute):
    """Numeric attributes are colored by the rank of their regions' values;
    a categorical attribute's regions take the colors of the default regions
    holding most of their samples (figstyle.matched_colors)."""
    if pd.api.types.is_numeric_dtype(features[attribute]):
        return rank_colors(group)
    return fs.matched_colors([default_group, group])


def region_figure(data, config, name, param, row_title, values):
    """The regions of REGION_ATTRIBUTES, one per column, at each of `values`
    of `param`, one per row."""
    attributes = REGION_ATTRIBUTES
    defaults = config["defaults"]
    limits = data_limits(data.embedding, REGION_PADDING)
    default_groups = attribute_regions(data.features, data.embedding, defaults)

    fig, axes = grid(len(values), len(attributes))
    titles = []
    for r, v in enumerate(values):
        groups = attribute_regions(data.features, data.embedding, dict(defaults, **{param: v}))
        for c, attribute in enumerate(attributes):
            group, kept = groups[attribute]
            ax = axes[r, c]
            colors = region_colors(group, default_groups[attribute][0], data.features, attribute)
            plot(ax, group, colors, axis_limits=limits)
            ax.set_title(attribute + ("" if kept else ", filtered as uninformative"), **PANEL_TITLE)
            fs.letter(ax, r * len(attributes) + c)
        titles.append(row_title.format(v) + (" (default)" if v == defaults[param] else ""))
    row_titles(fig, axes, titles)
    report(fig, axes, name)
    save(fig, name)


def contrastive_rows(config):
    """(row title, contrastive kwargs) of the contrastive figure's rows."""
    default = config["contrastive_defaults"]["merge_threshold"]
    rows = []
    for t in CONTRASTIVE_THRESHOLDS:
        title = f"Contrastive merge threshold {t:g}" + (" (default)" if t == default else "")
        rows.append((title, {"merge_threshold": t}))
    return rows


def panel_of(layout, attribute):
    """The panel of `layout` whose regions describe `attribute`."""
    return next(p for p in layout if attribute in base_feature_names(p[0]))


def explanation_figure(regions, config, kind, rows, name, tracked=None, padding=None):
    """Rows of explanations of `kind`: the top panels of each row or, given
    `tracked` attributes, the panel of each attribute, titled with it. VERA
    picks each panel's axis padding unless one `padding` is given for all."""
    explain = getattr(vera.explain, kind)
    defaults = dict(config[f"{kind}_defaults"])
    n = config["max_panels"] if tracked is None else len(tracked)
    limits = None if padding is None else data_limits(regions[0][0].region.embedding.X, padding)
    fig, axes = grid(len(rows), n)
    if tracked is None:
        row_layouts = [explain(regions, max_panels=n, **dict(defaults, **kwargs)) for _, kwargs in rows]
    else:
        full = [explain(regions, max_panels=len(regions), **dict(defaults, **kwargs)) for _, kwargs in rows]
        row_layouts = [[panel_of(layout, a) for a in tracked] for layout in full]
    colors = matched_row_colors(row_layouts, by_column=tracked is not None)
    for r, layouts in enumerate(row_layouts):
        for c in range(n):
            ax = axes[r, c]
            if c >= len(layouts):
                fs.blank(ax)
                continue
            plot(ax, layouts[c], colors, axis_limits=limits)
            if tracked is not None:
                ax.set_title(tracked[c], **PANEL_TITLE)
            fs.letter(ax, r * n + c)
    row_titles(fig, axes, [title for title, _ in rows])
    report(fig, axes, name)
    save(fig, name)


def main():
    fs.setup()
    with open(CONFIG) as f:
        config = json.load(f)
    data = ds.Dataset.load(DATASET)
    for figure in REGION_FIGURES:
        region_figure(data, config, *figure)
    regions = vera.an.generate_region_annotations(data.features, data.embedding, **config["defaults"])
    explanation_figure(regions, config, "contrastive", contrastive_rows(config), "contrastive-parameters",
                       tracked=CONTRASTIVE_ATTRIBUTES)
    explanation_figure(regions, config, "descriptive", DESCRIPTIVE_ROWS, "descriptive-parameters")


if __name__ == "__main__":
    main()
