"""Rangesets (Sohns et al., 2022) against VERA's contrastive explanations of
the same attributes, for the supplement.

One column per attribute: the four attributes of the dataset's case-study
figure in the manuscript (CASE_STUDY_ATTRIBUTES), or else of VERA's
highest-ranked contrastive explanations:
  row 1  the attribute's rangeset view (related_methods/rangesets.py, with
         the settings in config.json);
  row 2  VERA's contrastive explanation of the attribute, on its default KDE
         regions;
  row 3  VERA's contrastive explanation of the attribute on rangeset regions
         (VERA's region_method="rangeset"), so that rows 1 and 3 share the
         region primitive and differ only in VERA's filtering, merging, and
         labelling.

Usage: python figS01_S02_rangesets.py [--config config.json]
           [--dataset attrition abalone] [--padding 0.1]
           [--embedding umap] [--attributes a b c d]

Without --dataset, it draws the supplement's two figures (DATASETS), saved
as figures/fig_supp_rangeset-contrastive-<dataset>.{pdf,png}, with an
embedding variant or padding other than the default appended to the name.
Every panel is framed and drawn with the same axis padding: PADDING, or the
dataset's entry in DATASET_PADDING, unless --padding is given.
"""
import argparse
import json
import os

import matplotlib
import matplotlib.transforms  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import numpy as np  # noqa: E402
import vera  # noqa: E402
import vera.label_placement  # noqa: E402
import vera.explain  # noqa: E402
import vera.plotting  # noqa: E402
from vera import metrics  # noqa: E402

import fig02_related_methods as mrf  # noqa: E402

common, fs = mrf.common, mrf.fs
N_ATTRIBUTES = 4
MAX_DESCRIPTORS = 3
# Gap between rows, in panel heights: room for a row title above the panel
# titles, and a few points between it and the row above
ROW_GAP = 0.23
# Space between a row title and its panels' titles, in points
ROW_TITLE_SPACE = 2.75
ROW_TITLES = [
    "Rangesets, one feature per view",
    "VERA contrastive explanations of the same features",
    "VERA contrastive explanations on rangeset regions",
]
# Corners a rangeset legend may take, the first preferred on a tie
LEGEND_CORNERS = ["lower right", "lower left", "upper right"]
# The datasets of the manuscript's case studies, whose figures the
# supplement shows
DATASETS = ["attrition", "abalone"]
# The attributes of the manuscript's case-study figures, in their order:
# attrition's are VERA's four top-ranked contrastive attributes. Abalone's
# sexes are interleaved, so on rangeset regions VERA merges them into one
# region and drops the attribute; height takes that column
CASE_STUDY_ATTRIBUTES = {
    "attrition": ["Department", "EducationField", "JobRole", "StockOptionLevel"],
    "abalone": ["age", "height", "shucked weight", "diameter"],
}
# Axis padding of every panel, as a fraction of the embedding's extent: the
# smallest at which VERA's labels keep clear of the frame, the panel
# letters, and one another
PADDING = 0.2
# Datasets whose labels need more room: attrition's nine job roles crowd
# its JobRole panels; only at 0.5, with labels wrapped at
# DATASET_LABEL_WIDTH, does no label overlap another, a panel letter, or the
# frame
DATASET_PADDING = {"attrition": 0.5}
# Datasets whose VERA labels wrap at a width other than the comparison
# figure's (make_related_figure.VERA_LABEL_WIDTH), in characters
DATASET_LABEL_WIDTH = {"attrition": 27}


def base_feature_names(ra):
    """The names of the attributes that the descriptor of region annotation
    `ra` derives from, in order and without repeats."""
    desc = ra.descriptor
    names = []
    for v in getattr(desc, "variables", [desc]):
        base = v
        while getattr(base, "base_variable", None) is not None:
            base = base.base_variable
        if base.name not in names:
            names.append(base.name)
    return names


def contrastive_of(regions, attribute):
    """VERA's contrastive layout whose regions describe `attribute`, or None."""
    for layout in vera.explain.contrastive(regions, max_panels=len(regions)):
        if any(attribute in base_feature_names(r) for r in layout):
            return layout
    return None


_add_bbox_padding = vera.plotting.add_bbox_padding


def plot_layout(ax, layout, cfg, fixed=None, colors=None, max_width=None):
    """VERA's layout on `ax`. VERA picks the axis padding (the margin around
    the embedding, as a fraction of its extent) that lays out the labels
    best; a `fixed` padding is used instead if given, and VERA lays out the
    labels for it. `colors` gives the regions' colors in layout order, and
    VERA's own colors are used without it. Labels wrap at `max_width`
    characters, by default the comparison figure's width. Returns the
    padding used.

    VERA pads the axis limits it finds after drawing the regions, which
    extend past the data by a different amount in every layout; with a
    `fixed` padding, the limits are padded from the square around the data
    instead, so that every layout of one embedding gets the same limits."""
    used = []
    X = layout[0].region.embedding.X
    data_bbox = vera.label_placement.set_bbox_square_aspect(np.hstack([X.min(axis=0), X.max(axis=0)]))

    def add_bbox_padding(bbox, padding=(1, 1)):
        p = padding if fixed is None else (fixed, fixed)
        used.append(p[0])
        return _add_bbox_padding(bbox if fixed is None else data_bbox, p)

    for r in layout:
        r.descriptor = r.descriptor.ranked_by(lambda r=r: metrics.descriptor_scores(r, method=cfg["descriptor_ranking"]))
    ra_colors = dict(zip(layout, colors)) if colors else vera.pl.layout_variable_colors([layout])
    vera.plotting.add_bbox_padding = add_bbox_padding
    try:
        vera.pl.plot_annotation(layout, ax=ax, ra_colors=ra_colors,
                                indicate_membership=True, max_descriptors=MAX_DESCRIPTORS,
                                max_width=max_width or mrf.VERA_LABEL_WIDTH, label_kwargs=fs.LABEL_KWARGS,
                                scatter_kwargs=fs.SCATTER_KWARGS, leader_kwargs=fs.LEADER_KWARGS)
    finally:
        vera.plotting.add_bbox_padding = _add_bbox_padding
    # The last padding applied is the one VERA kept
    return used[-1]


def label_problems(ax, letter, renderer, margin=1):
    """The label lines on `ax` that come within `margin` points of its frame
    (the labels are clipped to the frame), overlap the panel `letter`, or
    overlap a line of another label, as (problem, line text) pairs. VERA
    draws each label as a `Label` artist holding one `Text` per line."""
    frame = ax.get_window_extent(renderer)
    m = margin * ax.figure.dpi / 72
    lb = letter.get_window_extent(renderer)
    labels = [a.texts for a in ax.artists if isinstance(a, vera.label_placement.Label)]
    labels += [[t] for t in ax.texts if t is not letter]
    lines = [(i, t, t.get_window_extent(renderer)) for i, texts in enumerate(labels)
             for t in texts if t.get_text().strip()]
    out = []
    for j, (i, t, b) in enumerate(lines):
        text = t.get_text()
        if b.x0 < frame.x0 + m or b.x1 > frame.x1 - m or b.y0 < frame.y0 + m or b.y1 > frame.y1 - m:
            out.append(("at the frame", text))
        if b.overlaps(lb):
            out.append(("over the panel letter", text))
        # Lines overlapping by more than a quarter of a line height in both
        # directions, so that lines that merely touch do not count
        inset = b.height / 4
        if any(k != i and min(b.x1, o.x1) - max(b.x0, o.x0) > inset and min(b.y1, o.y1) - max(b.y0, o.y0) > inset
               for k, _, o in lines[j + 1:]):
            out.append(("over another label", text))
    return out


def points_under_legend(ax, embedding, renderer):
    """The number of embedding points drawn under the legend of `ax`."""
    legend = ax.get_legend()
    if legend is None:
        return 0
    return int(legend.get_window_extent(renderer).count_contains(ax.transData.transform(embedding)))


def draw(dataset, args, cfg):
    """The comparison figure of `dataset`, saved to figures/."""
    default_padding = DATASET_PADDING.get(dataset, PADDING)
    padding = default_padding if args.padding is None else args.padding
    variant = args.embedding
    data = common.datasets.Dataset.load(dataset, embedding=variant)
    features, embedding = common.load(dataset, embedding=variant)
    region_kw = dict(cfg["region_defaults"], sample_size=None)
    region_kw.update({k: v for k, v in cfg["datasets"].get(dataset, {}).items()
                      if k == "uninformative_max_sample_coverage"})
    ind = data.indicator_columns

    kde = vera.an.generate_region_annotations(features, embedding, indicator_columns=ind, **region_kw)
    rangeset = vera.an.generate_region_annotations(features, embedding, indicator_columns=ind,
                                                   region_method="rangeset", **region_kw)
    attributes = args.attributes or CASE_STUDY_ATTRIBUTES.get(dataset)
    if not attributes:
        attributes = []
        for layout in vera.explain.contrastive(kde, max_panels=len(kde)):
            for name in base_feature_names(layout[0]):
                if name not in attributes:
                    attributes.append(name)
        attributes = attributes[:N_ATTRIBUTES]
    print(f"[{dataset}] attributes: {attributes}", flush=True)

    n = len(attributes)
    # Each row carries a bold row title above its panels' attribute titles
    fig, axes = mrf.grid(3, n, ROW_GAP, width=fs.SUPPLEMENT_TEXTWIDTH_IN)
    # Text is measured at the figure's resolution, both by VERA's label
    # placement and by the checks below, and grows slightly wider at a
    # higher one; drawing at the PNG's resolution keeps labels that fit
    # from being clipped in the PNG
    fig.set_dpi(cfg.get("png_dpi", 450))
    layouts = {n + j: contrastive_of(kde, a) for j, a in enumerate(attributes)}
    layouts.update({2 * n + j: contrastive_of(rangeset, a) for j, a in enumerate(attributes)})
    # VERA filters out an attribute whose regions all merge into one, a
    # region whose rule (abalone's "sex in {female, infant, male}") holds for
    # every sample; such an attribute is drawn with that single region,
    # regenerated without the filter, so that the panel shows why VERA
    # explains nothing
    unfiltered = {}
    single_region = set()
    for i in [i for i, layout in layouts.items() if not layout]:
        method = "kde" if i < 2 * n else "rangeset"
        if method not in unfiltered:
            unfiltered[method] = vera.an.generate_region_annotations(
                features, embedding, indicator_columns=ind, region_method=method,
                filter_uninformative=False, **region_kw)
        attribute = attributes[i % n]
        layouts[i] = next((g for g in unfiltered[method]
                           if any(attribute in base_feature_names(r) for r in g)), None)
        if layouts[i]:
            single_region.add(i)
    # Each VERA row draws a cluster in one color across its panels, the
    # colors of its first panel (figstyle.matched_colors); the colors are
    # listed per panel in layout order, since ranking a layout's descriptors
    # replaces them
    colors = {}
    for first in (n, 2 * n):
        row = fs.matched_colors([layouts[i] for i in range(first, first + n)])
        colors.update({i: [row[ra] for ra in layouts[i]] for i in range(first, first + n) if layouts[i]})
    # One padding for every panel, so that the embedding is drawn at one
    # size; VERA's own choice varies per panel. The rangesets take the same
    # limits
    for i, layout in layouts.items():
        if layout:
            plot_layout(axes[i], layout, cfg, fixed=padding, colors=colors[i],
                        max_width=DATASET_LABEL_WIDTH.get(dataset))
    ref = next(i for i in layouts if layouts[i])
    # An attribute without any region keeps its framed panel with the bare
    # embedding, in VERA's grey
    for i, layout in layouts.items():
        if not layout:
            axes[i].scatter(*embedding.T, **dict(fs.SCATTER_KWARGS, c="#999999"))
            axes[i].set(xticks=[], yticks=[])
    for j, attribute in enumerate(attributes):
        mrf.rangesets_panel(axes[j], features, embedding, cfg["rangesets"], attribute)
    for i in range(len(axes)):
        if not layouts.get(i):
            axes[i].set_xlim(axes[ref].get_xlim())
            axes[i].set_ylim(axes[ref].get_ylim())
    height = fig.get_size_inches()[1]
    renderer = fig.canvas.get_renderer()
    to_figure = fig.transFigure.inverted()
    letters = {}
    for row, text in enumerate(ROW_TITLES):
        titles = []
        for j, attribute in enumerate(attributes):
            ax = axes[row * n + j]
            titles.append(ax.set_title(attribute, **mrf.TITLE))
            fs.letter(ax, row * n + j)
            letters[row * n + j] = ax.texts[-1]
        # The row title sits just above its panels' titles, so that it reads
        # as the heading of its row rather than of the gap between rows
        top = max(t.get_window_extent(renderer).transformed(to_figure).y1 for t in titles)
        fig.text(axes[row * n].get_position().x0, top + ROW_TITLE_SPACE / 72 / height, text,
                 fontsize=7, fontweight="bold", ha="left", va="bottom")
    # Report what a smaller padding can break: labels pressed against the
    # frame, over the panel letter, or over one another, rangeset legends over
    # the data, and attributes with no contrastive layout
    for j, attribute in enumerate(attributes):
        place_legend(axes[j], embedding, renderer)
        covered = points_under_legend(axes[j], embedding, renderer)
        if covered:
            print(f"[{dataset}] panel {j} ({attribute}): legend over {covered} points")
    for i, layout in layouts.items():
        where = f"[{dataset}] panel {i} ({attributes[i % n]})"
        if not layout:
            print(f"{where}: no regions, embedding only")
            continue
        if i in single_region:
            print(f"{where}: filtered out by VERA, drawn with its single merged region")
        for problem, text in label_problems(axes[i], letters[i], renderer):
            print(f"{where}: label {problem}: {text!r}")
    os.makedirs(mrf.FIG_DIR, exist_ok=True)
    path = os.path.join(mrf.FIG_DIR, f"fig_supp_rangeset-contrastive-{dataset}" +
                        (f"-{variant}" if variant else "") +
                        (f"-padding-{padding:g}" if padding != default_padding else ""))
    # The saved area spans the figure's width, the supplement's text width,
    # widened only by the outer frames' line width, so that the figure is
    # included there at its drawn size; it reaches from the panels' bottom
    # to just above the row titles
    tight = fig.get_tightbbox(renderer)
    width = fig.get_size_inches()[0]
    area = matplotlib.transforms.Bbox([[min(0, tight.x0), tight.y0], [max(width, tight.x1), tight.y1 + 0.03]])
    fig.savefig(path + ".pdf", dpi=300, transparent=True, bbox_inches=area)
    fig.savefig(path + ".png", dpi=cfg.get("png_dpi", 450), bbox_inches=area, facecolor="white")
    plt.close(fig)
    print(f"wrote {path}.png ({fig.get_size_inches()[0]:.2f} x {fig.get_size_inches()[1]:.2f} in)")


def place_legend(ax, embedding, renderer):
    """Moves the legend of `ax` to the corner where it covers the fewest
    embedding points; the upper left holds the panel letter."""
    legend = ax.get_legend()
    if legend is None:
        return
    covered = {}
    for loc in LEGEND_CORNERS:
        legend.set_loc(loc)
        covered[loc] = points_under_legend(ax, embedding, renderer)
    legend.set_loc(min(LEGEND_CORNERS, key=covered.get))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(mrf.HERE, "config.json"))
    ap.add_argument("--dataset", nargs="+", default=DATASETS, help="the datasets to draw (default: DATASETS)")
    ap.add_argument("--attributes", nargs="+", help="the columns' attributes (default: the case-study figure's, or VERA's top contrastive)")
    ap.add_argument("--embedding", help="an embedding variant of the dataset, e.g. umap (default: the dataset's default)")
    ap.add_argument("--padding", type=float,
                    help="the axis padding of every panel, as a fraction of the embedding's extent")
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    fs.setup()
    for dataset in args.dataset:
        draw(dataset, args, cfg)


if __name__ == "__main__":
    main()
