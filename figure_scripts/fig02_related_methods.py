"""The manuscript's comparison figure: related methods and VERA on one
embedding, two rows of four panels at the full text width, with text at
TEXT_PT and panel titles at TITLE_PT so that it is legible in print.

  Row 1, methods that explain a clustering of the embedding through
  additional views, all following one cluster, outlined in black:
  (a) the DBSCAN clusters both methods explain, numbered by size;
  (b) ccPCA's (Fujiwara et al., 2020) histograms of the cluster against the
      rest, for its three attributes of largest contribution, in a narrower
      column;
  (c) IXVC (Bibal et al., 2021): the decision tree separating the clusters,
      to depth 2, the path that follows most of the cluster in bold and
      ending in a box with the cluster's share; every split sends TRUE to
      its upper child, and dashed boxes are collapsed subtrees;
  (d) ccPCA's feature contributions of each cluster, the cluster's column
      outlined.
  Row 2, methods that overlay the embedding with explanatory elements:
  (e) rangesets (Sohns et al., 2022) of one attribute;
  (f) attribute-based explanation (da Silva et al., 2015), the top-ranked
      dimension under the variance ranking;
  (g) column selection method (Joia et al., 2015) on standardized
      attributes, each group's two most relevant attributes as one label in
      place of its word cloud, as many groups as DBSCAN clusters
      (--joia-unscaled: on unscaled attributes, as the method is
      implemented);
  (h) VERA's highest-ranked descriptive explanation (--vera-panel 2: its
      second), its labels kept clear of the panel's top left corner, and
      its descriptors wrapped (--no-wrap: one per line, unwrapped).
  Each panel's letter stands left of its title.
Every panel draws its points in a fixed random order, so that no colour is
drawn systematically over the others.

The related methods are the reimplementations in related_methods/, with the
settings in config.json, which also holds VERA's. The manuscript's figure
(Fig. 2) is drawn on the football players dataset (DATASET) without options,
with its entries in RANGESET_ATTRIBUTE, DBSCAN, VERA_PADDING, and
VERA_FIGURE_WIDTH_BY_KEY.

Usage: python fig02_related_methods.py [--config config.json] [--dataset NAME]
           [--attribute ATTRIBUTE] [--focus 2] [--frames] [--vera-panel 2]
           [--merge-threshold 0.9] [--min-region-size 50] [--embedding umap]
           [--no-wrap] [--hist-features 4] [--joia-unscaled] [--vera-padding 0.3]

Writes figures/fig_related_methods.{pdf,png}, with another dataset's name and
the options given appended to the name. The manuscript's copy of the PDF is
finished by hand in Illustrator.
"""
import argparse
import json
import os
import re
import string

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.transforms as mtransforms  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402

import vera  # noqa: E402
import vera.explain  # noqa: E402
import vera.plotting  # noqa: E402
from vera import metrics  # noqa: E402

from related_methods import attribute_explanation as ae  # noqa: E402
from related_methods import ccpca  # noqa: E402
from related_methods import common  # noqa: E402
from related_methods import rangesets as rs  # noqa: E402
from related_methods import ixvc  # noqa: E402
from related_methods import representative_groups as rg  # noqa: E402
from related_methods import views as rx  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "figures")
# The manuscript's dataset
DATASET = "football_players_wyscout"

fs = common.figstyle
TITLE = dict(fontsize=6, loc="left", pad=2)
# The figure's text: TEXT_PT for labels, legends, and the tree, TITLE_PT for
# panel titles, which keeps it legible at the manuscript's text width
TEXT_PT = 6
TITLE_PT = 7
FIGURE_TITLE = dict(TITLE, fontsize=TITLE_PT)
# Axis padding of the scatter panels, matching plot_annotation's default, so
# that the embedding is drawn at the same size in every panel
PADDING = 0.25
DESCRIPTOR_RANKING = "purity_lift"
TREE_DEPTH = 2
TREE_WRAP = 18
# The followed cluster's outline, heatmap column, and tree path
FOCUS_COLOR = "black"
# The attribute each dataset's rangesets panel shows; other datasets need
# --attribute
RANGESET_ATTRIBUTE = {
    "football_players_wyscout": "crosses per 90",
}
# DBSCAN settings for this figure, giving four to eight clusters of at least
# 2% of the points with at most 10% noise; other datasets get
# DEFAULT_DBSCAN. Settings keyed by "dataset/embedding" apply to that
# embedding variant
DBSCAN = {
    "football_players_wyscout": {"min_samples": 40, "eps_quantile": 0.6},
}
DEFAULT_DBSCAN = {"min_samples": 10, "eps_quantile": 0.95}
# Fixed axis padding of VERA's panel, where VERA's own choice draws the
# embedding much smaller than in the other panels, or where it was chosen with
# the embedding's rotation (prepare_tabular.ROTATE) for the label layout
VERA_PADDING = {
    "football_players_wyscout": 0.4,
}
# A box in the top left corner of VERA's panel (axes fractions) that its
# labels are laid out to keep clear of. The panel letters sit in the title
# line, outside the panel; the box remains part of the layout because the
# embedding rotations (prepare_tabular.ROTATE) were chosen for the label
# layouts it produces
LETTER_CORNER = (0, 0.86, 0.12, 1)
# Each panel's letter, left of its title, and the title's offset from the
# panel's left edge (points)
LETTER_PT = 9
LETTER_TITLE_GAP = 9.5
# VERA's label budget in the comparison figure: two descriptors per label,
# lines wrapped at VERA_FIGURE_WIDTH characters and the number of further
# descriptors as VERA's "(+n more)" on a line of its own, so that at TEXT_PT
# two labels fit side by side
VERA_DESCRIPTORS = 2
VERA_FIGURE_WIDTH = 20
# Per dataset and embedding: each descriptor on one line, unwrapped
VERA_FIGURE_WIDTH_BY_KEY = {
    "football_players_wyscout": 100,
}
# The line width with --no-wrap, beyond any descriptor's length, so that
# each descriptor takes one line
VERA_NOWRAP_WIDTH = 100
# The label width of the supplement's VERA panels, drawn at 4 pt
VERA_LABEL_WIDTH = 30
# The attribute-based panel's colours, whose legend entries take a line each
# at TEXT_PT
DASILVA_COLORS = 3
# Column selection's attributes per group label, whether it standardizes
# the attributes (unscaled, as the method is implemented, large-range
# attributes come first in every group), and its
# polygon edge limit (a fraction of the view),
# above the config's 0.05 so that the polygons of sparse embeddings close
# their holes
JOIA_WORDS = 2
JOIA_SCALE = True
JOIA_ALPHA = 0.1
# Gap between the rows, in panel heights: the clusters' legend below the top
# row and the bottom row's titles
ROW_GAP = 0.25
# The linked-view row, left to right: the clusters (one panel), the
# histogram column, the tree, and the heatmap; widths in panel widths, the
# histogram column taking the rest of the text width. LINKED_GAPS widens the
# gaps before the histograms, the tree and the heatmap beyond the gap between
# panels, so that the white space between all four panels is about equal. TREE_MARGINS (depth units) leave just the root's and the
# leaves' half widths beside the tree. The histograms show HIST_FEATURES
# attributes of the followed cluster
TREE_WIDTH = 1.3
TREE_MARGINS = (0.4, 0.55)
HEAT_WIDTH = 1.05
LINKED_GAPS = (0.0, 0.026, 0.056)
# The heatmap's row labels, in panel widths
HEAT_LABEL_WIDTH = 0.56
# The heatmap's cells, in fractions of the panel height from its bottom; the
# histograms beside it span the same height
HEAT_BOTTOM = 0.02
HEAT_TOP = 0.88
HIST_FEATURES = 3
# Legends below a panel, as many columns as fit within its width
LEGEND_BELOW = dict(below=True, loc="upper center", bbox_to_anchor=(0.5, -0.01), frameon=False, handlelength=0.8,
                    handletextpad=0.5, columnspacing=1.2, borderaxespad=0.2, labelspacing=0.4)
FIGURE_LEGEND = dict(LEGEND_BELOW, fontsize=TEXT_PT, markerscale=1.5, handletextpad=0.3, columnspacing=0.9,
                     labelspacing=0.3)


def grid(nrows, ncols, hgap, width=fs.TEXTWIDTH_IN):
    """figstyle's grid of square panels filling `width` (the manuscript's
    text width), with a vertical gap of `hgap` panel heights between rows
    (room for a row's legends below it and the next row's titles)."""
    panel = width / (ncols + (ncols - 1) * fs.PANEL_GAP)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(width, panel * (nrows + (nrows - 1) * hgap)), dpi=150)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=fs.PANEL_GAP, hspace=hgap)
    return fig, list(axes.ravel())


def rangesets_panel(ax, features, embedding, rcfg, attribute, legend_loc="lower right", legend_kwargs=None,
                    title=TITLE):
    eps = rcfg["eps_factor"] * rs.wilkinson_eps(embedding)
    bins = rs.rangeset(features[attribute].values, embedding, eps, bins=rcfg["bins"])
    rx.rangeset_view(ax, embedding, bins, legend_loc=legend_loc, legend_kwargs=legend_kwargs)
    rx.square_limits(ax, embedding, pad=PADDING)
    ax.set_title(f"Rangesets: {attribute}", **title)


def dasilva_panel(ax, features, embedding, acfg, ranking="variance", n_colors=ae.N_COLORS, legend_loc="lower left",
                  legend_kwargs=None, title=TITLE):
    """Each point coloured by its top-ranked dimension under the variance or
    the Euclidean ranking; the `n_colors` most frequent in colour."""
    if acfg["categorical"] == "exclude":
        features = features[[c for c in features.columns if not common.is_categorical(features[c])]]
    X, names, _ = common.numeric_matrix(features)
    diam = ae.diameter(embedding)
    rho = acfg["rho"] * diam
    nbrs = ae.neighbourhoods(embedding, rho)
    ranks, keep = ae.variance_ranking(X, nbrs) if ranking == "variance" else ae.euclidean_ranking(X, nbrs)
    kept = [n for n, k in zip(names, keep) if k]
    rx.square_limits(ax, embedding, pad=PADDING)
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    rx.dasilva_view(ax, embedding, np.argmin(ranks, axis=1), lambda k: kept[int(k)], acfg["rho_c"] * rho, xlim, ylim,
                    acfg["fill_radius"] * diam, n_colors=n_colors, legend_loc=legend_loc, legend_kwargs=legend_kwargs)
    ax.set_title(f"Attribute-based ({ranking.capitalize()})", **title)


def by_size(labels):
    """`labels` with the clusters renumbered from the largest (0) to the
    smallest, ties in DBSCAN's order; noise stays -1."""
    ids, counts = np.unique(labels[labels >= 0], return_counts=True)
    order = ids[np.argsort(-counts, kind="stable")]
    new = np.full(labels.max() + 2, -1)
    new[order] = np.arange(len(order))
    return new[labels]


def cluster_palette(labels):
    """A colour per cluster, black for noise."""
    real = sorted(set(labels) - {-1})
    col_of = dict(zip(real, rx.palette(len(real))))
    col_of[-1] = (0, 0, 0)
    return col_of


def clusters_panel(ax, embedding, labels, focus, fontsize=TEXT_PT):
    """The DBSCAN clusters, the `focus` cluster outlined, with a colour
    legend below the panel; noise in grey; no frame."""
    col_of = cluster_palette(labels)
    noise = labels < 0
    ax.scatter(*embedding[noise].T, color="0.85", **fs.SCATTER_KWARGS)
    ax.scatter(*embedding[~noise].T, c=[col_of[l] for l in labels[~noise]], **fs.SCATTER_KWARGS)
    rx.square_limits(ax, embedding, pad=PADDING)
    outline(ax, embedding[labels == focus])
    clusters = sorted(set(labels) - {-1})
    handles = [plt.Line2D([], [], marker="s", ls="", ms=3, color=col_of[c], label=f"C{c + 1}") for c in clusters]
    rx.fit_legend_below(ax, handles, **{k: v for k, v in dict(FIGURE_LEGEND, fontsize=fontsize).items()
                                        if k != "below"})
    rx.bare(ax)
    # Unframed, like the other panels of its row
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("DBSCAN clusters", **FIGURE_TITLE)


def outline(ax, points):
    """A dashed outline around the footprint of `points`: the union of discs
    of radius 1.5% of the view around them, closed over gaps of twice that,
    dropping parts under 2% of the footprint's area, with the boundary
    simplified and rounded by Chaikin's corner cutting."""
    from shapely.geometry import MultiPoint
    r = 0.015 * np.diff(ax.get_xlim())[0]
    shape = MultiPoint(points).buffer(r).buffer(2 * r).buffer(-2 * r)
    parts = getattr(shape, "geoms", [shape])
    for part in parts:
        if part.area < 0.02 * shape.area:
            continue
        ring = np.asarray(part.exterior.simplify(0.5 * r).coords)
        for _ in range(4):
            q, nxt = ring[:-1], np.roll(ring[:-1], -1, axis=0)
            ring = np.empty((2 * len(q), 2))
            ring[0::2], ring[1::2] = 0.75 * q + 0.25 * nxt, 0.25 * q + 0.75 * nxt
            ring = np.vstack([ring, ring[:1]])
        ax.plot(*ring.T, color=FOCUS_COLOR, lw=0.8, ls=(0, (3, 1.5)), zorder=3)


def ccpca_heatmap_panel(ax, X, names, labels, ccfg, focus, max_rows=8, fontsize=TEXT_PT, label_chars=26,
                        label_share=0.62):
    """ccPCA's feature-contribution heatmap (features x clusters), sign-flipped
    and reordered as in its view, filling the panel right of its row labels,
    which take `label_share` of its width and are cut at `label_chars`
    characters; the `focus` cluster's column is boxed. DBSCAN's noise points
    are background for every cluster but get no column."""
    clusters, fcs, comps, _ = ccpca.contrast_clusters(X, labels, **ccfg)
    keep = clusters != -1
    clusters, fcs, comps = clusters[keep], fcs[:, keep], comps[:, keep]
    fcs = fcs * ccpca.optimal_sign_flip(comps)
    agg, agg_names, _ = ccpca.aggregate(ccpca.scale_columns(fcs), names, max_rows=max_rows)
    # A merged row "feature, n more" is written as "feature (+n)", as VERA
    # writes its truncated labels
    agg_names = [re.sub(r", (\d+) more$", r" (+\1)", n) for n in agg_names]
    rows, cols = ccpca.reorder(agg)
    col_of = cluster_palette(labels)
    rx.bare(ax)
    # The panel may be narrower than tall
    ax.set_aspect("auto")
    for sp in ax.spines.values():
        sp.set_visible(False)
    pos = ax.get_position()
    hax = ax.figure.add_axes([pos.x0 + pos.width * label_share, pos.y0 + pos.height * HEAT_BOTTOM,
                              pos.width * (1 - label_share), pos.height * (HEAT_TOP - HEAT_BOTTOM)])
    hax.imshow(agg[rows][:, cols], cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto", interpolation="nearest")
    hax.set_yticks(range(len(rows)))
    hax.set_yticklabels([agg_names[i] if len(agg_names[i]) <= label_chars else agg_names[i][:label_chars - 1] + "…"
                         for i in rows], fontsize=fontsize, fontfamily="Arial")
    hax.set_xticks(range(len(cols)))
    hax.set_xticklabels([f"C{clusters[j] + 1}" for j in cols], fontsize=fontsize, fontfamily="Arial")
    for tick, j in zip(hax.get_xticklabels(), cols):
        tick.set_bbox(dict(boxstyle="square,pad=0.1", fc=col_of[clusters[j]], ec="none"))
    fj = list(clusters[cols]).index(focus)
    hax.add_patch(plt.Rectangle((fj - 0.5, -0.5), 1, len(rows), fill=False, ec=FOCUS_COLOR, lw=1.2, clip_on=False))
    hax.xaxis.tick_top()
    hax.tick_params(length=0, pad=1)
    for sp in hax.spines.values():
        sp.set_linewidth(0.3)
    ax.set_title("ccPCA: feature contributions", **FIGURE_TITLE)


def ixvc_tree_panel(ax, X, names, labels, focus, fontsize=TEXT_PT):
    """IXVC's decision tree separating the clusters, to TREE_DEPTH, with the
    path that follows most of the `focus` cluster drawn bold."""
    tree, _, _ = ixvc.fit_tree(X, labels)
    col_of = cluster_palette(labels)
    rx.ixvc_tree_view(ax, ixvc.tree_structure(tree, X[labels >= 0]), list(tree.classes_), col_of, names, TREE_DEPTH,
                      compact=True, focus=focus, focus_color=FOCUS_COLOR, wrap_width=TREE_WRAP, group_name="C{}",
                      fontsize=fontsize, subtree_note=False, link_labels="root", focus_share=True,
                      margins=TREE_MARGINS)
    ax.set_title(f"IXVC: decision tree ({tree.get_n_leaves()} leaves, depth {TREE_DEPTH} shown)", **FIGURE_TITLE)


def joia_label_panel(ax, X, names, embedding, labels, jcfg, n_words=2, scale=None, fontsize=TEXT_PT,
                     title=TITLE):
    """Column selection method with each group's `n_words` most relevant
    attributes as one label, its top attribute first, in the group's colour
    at the most interior point of its polygon and pushed off overlapping
    labels, in place of the method's word cloud, whose words do not fit thin
    polygons at a legible size. As many groups as DBSCAN clusters; `scale`
    overrides the config's attribute scaling. Each label's white halo is a
    copy behind it, because a PDF draws text with a path effect as outlines,
    which keeps the labels themselves text."""
    import matplotlib.patheffects as pe
    from scipy import ndimage
    scale = jcfg["scale"] if scale is None else scale
    n_clusters = max(2, len(set(labels) - {-1}))
    reps, _, _ = rg.representatives(X, jcfg["fraction"], center=True, scale=scale)
    groups, _ = rg.cluster(embedding, reps, n_clusters)
    attrs = rg.relevant_attributes(X, groups, center=True, scale=scale)
    tri, owner = rg.cluster_polygons(embedding, groups, jcfg["alpha"])
    colors = rx.palette(n_clusters)
    pastel = [tuple(0.62 + 0.38 * np.array(c)) for c in colors]
    rx.bare(ax)
    rx.square_limits(ax, embedding, pad=PADDING)
    rx.joia_polygons(ax, embedding, tri, owner, pastel)
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    res = 500
    owner_px = rg.raster(tri, owner, xlim, ylim, res)
    texts, anchors, text_colors = [], [], []
    for c in range(len(attrs)):
        mask = owner_px == c
        if not mask.any():
            continue
        depth = ndimage.distance_transform_edt(mask)
        y, x = np.unravel_index(np.argmax(depth), depth.shape)
        xy = (xlim[0] + x / (res - 1) * (xlim[1] - xlim[0]), ylim[0] + y / (res - 1) * (ylim[1] - ylim[0]))
        pi, _ = attrs[c]
        top = np.argsort(-pi, kind="stable")[:n_words]
        color = tuple(0.75 * np.array(colors[c]))
        texts.append(ax.text(*xy, "\n".join(names[f] for f in top), fontsize=fontsize, ha="center", va="center",
                             fontfamily="Arial", color=color, zorder=4, linespacing=1.0))
        anchors.append(xy)
        text_colors.append(color)
    ax.figure.canvas.draw()
    repel(ax, texts, anchors, text_colors)
    for t in texts:
        ax.text(*t.get_position(), t.get_text(), fontproperties=t.get_fontproperties(), ha="center",
                va="center", color="white", zorder=3.9, linespacing=1.0,
                path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])
    ax.set_title("Column selection", **title)


def wrap_to_width(text, width_pt, fontsize, family="Arial"):
    """`text` broken into lines at spaces, each at most `width_pt` wide when
    set at `fontsize`; a word wider than that stays whole on its own line."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextToPath

    prop = FontProperties(family=family, size=fontsize)
    width = lambda s: TextToPath().get_text_width_height_descent(s, prop, ismath=False)[0]
    lines = []
    for word in text.split(" "):
        if lines and width(lines[-1] + " " + word) <= width_pt:
            lines[-1] += " " + word
        else:
            lines.append(word)
    return "\n".join(lines)


def ccpca_hist_panel(ax, X, names, bases, labels, ccfg, focus, n_features=HIST_FEATURES, fontsize=TEXT_PT):
    """ccPCA's histograms of the `focus` cluster (its colour) against the rest
    (grey), stacked in one column below the panel title: the `n_features`
    attributes whose strongest column has the largest |contribution|. A
    one-hot attribute is shown by its column of the cluster's most frequent
    value, so that a cluster of one genre is shown by that genre rather than
    by the genres it lacks, whose columns share the contribution."""
    clusters, fcs, _, _ = ccpca.contrast_clusters(X, labels, **ccfg)
    j = int(np.where(clusters == focus)[0][0])
    m = labels == focus
    strength = {}
    for f, b in enumerate(bases):
        strength[b] = max(strength.get(b, 0.0), abs(fcs[f, j]))
    shown = []
    for b in sorted(strength, key=lambda b: -strength[b])[:n_features]:
        cols = [f for f, bb in enumerate(bases) if bb == b]
        shown.append(cols[0] if len(cols) == 1 else max(cols, key=lambda f: X[m, f].mean()))
    col = cluster_palette(labels)[focus]
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    pos = ax.get_position()
    # The histograms span the heatmap's cells beside them, leaving the band of
    # its column labels empty: the first title starts at the
    # heatmap's top and the last axis lies on its bottom edge; each histogram
    # has its title's lines above its bars and, but for the last, a line of
    # tick labels below
    fig_w, fig_h = ax.figure.get_size_inches()
    line = 1.5 * fontsize / 72 / fig_h
    top, bottom = pos.y0 + pos.height * HEAT_TOP, pos.y0 + pos.height * HEAT_BOTTOM
    # Titles wrap to the histograms' width, and take as many lines as they need
    hist_x0, hist_w = pos.x0 + pos.width * 0.06, pos.width * 0.9
    titles = [wrap_to_width(names[f], hist_w * fig_w * 72, fontsize) for f in shown]
    n_title_lines = sum(t.count("\n") + 1 for t in titles)
    bar_h = (top - bottom - (n_title_lines + n_features - 1) * line) / n_features
    y = top
    for n, f in enumerate(shown):
        y_top = y - (titles[n].count("\n") + 1) * line
        y = y_top - bar_h - line
        hax = ax.figure.add_axes([hist_x0, y_top - bar_h, hist_w, bar_h])
        v = X[:, f]
        values = np.unique(v)
        binary = len(values) <= 2
        # An attribute of a few integer values gets a bar per value
        integer = not binary and len(values) <= 10 and np.all(values == np.round(values))
        bins = np.array([-0.5, 0.5, 1.5]) if binary else \
            np.arange(values.min() - 0.5, values.max() + 1) if integer else np.linspace(v.min(), v.max(), 16)
        hax.hist(v[~m], bins=bins, weights=np.full((~m).sum(), 1 / (~m).sum()), color="0.75", lw=0)
        hax.hist(v[m], bins=bins, weights=np.full(m.sum(), 1 / m.sum()), color=col, alpha=0.75, lw=0)
        hax.set_title(titles[n], fontsize=fontsize, fontfamily="Arial", pad=1.5, loc="left", linespacing=1.0)
        hax.set_yticks([])
        if binary:
            hax.set_xticks([0, 1])
        elif integer:
            hax.set_xticks(values)
        elif v.max() - v.min() >= 2:
            # Whole-number ticks at the smallest step of 1, 2, 5, 10, ... that
            # leaves at most five of them within the attribute's range
            def n_ticks(step):
                return int(np.floor(v.max() / step) - np.ceil(v.min() / step)) + 1
            step = next(s * 10 ** k for k in range(12) for s in (1, 2, 5) if n_ticks(s * 10 ** k) <= 5)
            hax.xaxis.set_major_locator(plt.MultipleLocator(step))
        else:
            hax.xaxis.set_major_locator(plt.MaxNLocator(3))
        hax.tick_params(labelsize=fontsize, length=1.5, pad=1, width=0.4)
        for sp in hax.spines.values():
            sp.set_linewidth(0.4)
        hax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_title(f"C{focus + 1} vs. rest", **FIGURE_TITLE)


def place_labels_off_long_side(embedding, label_targets, **kwargs):
    """VERA's initial label placement, except that for an embedding at least
    1.4 times wider than tall (or taller than wide) the labels start in the
    free bands above and below it (left and right of it), where the square
    panel has room, instead of around it; VERA then optimizes them as
    usual."""
    pos = _vera_initial_placement(embedding, label_targets, **kwargs)
    lo, hi = embedding.min(axis=0), embedding.max(axis=0)
    for long_axis, short_axis in ((0, 1), (1, 0)):
        if (hi - lo)[long_axis] >= 1.4 * (hi - lo)[short_axis]:
            band = ((hi - lo)[long_axis] - (hi - lo)[short_axis]) / 4
            mid = (lo[short_axis] + hi[short_axis]) / 2
            pos = np.array(label_targets, dtype=float)
            pos[:, short_axis] = np.where(pos[:, short_axis] >= mid, hi[short_axis] + band, lo[short_axis] - band)
    return pos


_vera_initial_placement = vera.plotting.initial_text_location_placement


def repel(ax, texts, anchors, colors, iterations=300, margin=2):
    """Push overlapping text boxes apart (display units), along the axis of
    their smaller overlap, keep them inside the axes, and connect every box
    that moved off its anchor to it with a thin line in its colour."""
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    for _ in range(iterations):
        boxes = [t.get_window_extent(renderer) for t in texts]
        moved = False
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = boxes[i], boxes[j]
                ox = min(a.x1, b.x1) - max(a.x0, b.x0) + margin
                oy = min(a.y1, b.y1) - max(a.y0, b.y0) + margin
                if ox <= 0 or oy <= 0:
                    continue
                moved = True
                if oy < ox:
                    d = np.array([0, oy / 2 * (1 if (a.y0 + a.y1) >= (b.y0 + b.y1) else -1)])
                else:
                    d = np.array([ox / 2 * (1 if (a.x0 + a.x1) >= (b.x0 + b.x1) else -1), 0])
                for t, sign in ((texts[i], 1), (texts[j], -1)):
                    xy = ax.transData.transform(t.get_position()) + sign * d
                    t.set_position(ax.transData.inverted().transform(xy))
        rx.keep_inside(ax, texts, margin=6)
        if not moved:
            break
    for t, anchor, color in zip(texts, anchors, colors):
        bb = t.get_window_extent(renderer)
        ax_xy = ax.transData.transform(anchor)
        if not (bb.x0 <= ax_xy[0] <= bb.x1 and bb.y0 <= ax_xy[1] <= bb.y1):
            ax.plot(*np.array([anchor, t.get_position()]).T, color=color, lw=0.5, zorder=2.5)


def title_letter(ax, idx):
    """Panel letter `idx` in the title line of `ax`, at the panel's left
    edge, with the left-aligned title moved right to make room for it."""
    title = ax._left_title
    ax.text(0, 1, string.ascii_lowercase[idx], fontsize=LETTER_PT, fontweight="bold", ha="left", va="baseline",
            transform=mtransforms.offset_copy(ax.transAxes, ax.figure, y=TITLE["pad"] + 0.6, units="points"))
    # matplotlib keeps a title's x (axes fractions) and recomputes only its y
    title.set_x(LETTER_TITLE_GAP / (ax.get_position().width * ax.figure.get_figwidth() * 72))


def plot_vera(ax, layout, fixed_padding=None, keep_clear=None, **kwargs):
    """VERA's `plot_annotation` of `layout` on `ax`. VERA picks the axis
    padding (the margin around the embedding, as a fraction of its extent)
    that lays out its labels best; a given `fixed_padding` is used instead, with
    the labels laid out for it, so that the embedding is drawn at the size of
    the other panels. Leader lines are drawn at the figure style's width.
    `keep_clear`, a box (x0, y0, x1, y1) in axes fractions such as
    LETTER_CORNER, is added to the data footprint that VERA keeps labels
    off; the panel is then laid out twice, first to find its axis limits."""
    kwargs.setdefault("leader_kwargs", fs.LEADER_KWARGS)
    original = vera.plotting.add_bbox_padding
    footprint = vera.plotting.data_footprint

    def fixed(bbox, padding=(1, 1)):
        return original(bbox, padding if fixed_padding is None else (fixed_padding, fixed_padding))

    def plot():
        vera.pl.plot_annotation(layout, ax=ax, ra_colors=vera.pl.layout_variable_colors([layout]), **kwargs)

    vera.plotting.add_bbox_padding = fixed
    try:
        plot()
        if keep_clear is not None:
            (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
            bx0, by0, bx1, by1 = keep_clear
            box = shapely.box(x0 + bx0 * (x1 - x0), y0 + by0 * (y1 - y0), x0 + bx1 * (x1 - x0), y0 + by1 * (y1 - y0))
            vera.plotting.data_footprint = lambda X, radius: footprint(X, radius).union(box)
            ax.cla()
            plot()
    finally:
        vera.plotting.add_bbox_padding = original
        vera.plotting.data_footprint = footprint


def vera_layouts(features, embedding, ind, cfg, dataset_cfg=None, descriptive_kw=None, n_panels=2):
    """VERA's `n_panels` highest-ranked descriptive and contrastive layouts,
    with the dataset's own settings from config.json where it has them and
    `descriptive_kw` overriding the descriptive settings."""
    dataset_cfg = dataset_cfg or {}
    region_kw = dict(cfg["region_defaults"], sample_size=None)
    if "uninformative_max_sample_coverage" in dataset_cfg:
        region_kw["uninformative_max_sample_coverage"] = dataset_cfg["uninformative_max_sample_coverage"]
    ra = vera.an.generate_region_annotations(features, embedding, indicator_columns=ind, **region_kw)
    des = vera.explain.descriptive(ra, **dict(cfg["descriptive_defaults"], max_panels=n_panels,
                                              **dict(dataset_cfg.get("descriptive", {}), **(descriptive_kw or {}))))
    con = vera.explain.contrastive(ra, max_panels=n_panels)
    layouts = des[:n_panels] + con[:n_panels]
    for layout in layouts:
        for r in layout:
            r.descriptor = r.descriptor.ranked_by(
                lambda r=r: metrics.descriptor_scores(r, method=DESCRIPTOR_RANKING))
    return layouts, len(des[:n_panels])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "config.json"))
    ap.add_argument("--dataset", default=DATASET)
    ap.add_argument("--attribute", help="the rangesets panel's attribute (default: RANGESET_ATTRIBUTE)")
    ap.add_argument("--focus", type=int, help="the cluster the linked views explain, as numbered in the figure")
    ap.add_argument("--frames", action="store_true", help="frame the embedding panels")
    ap.add_argument("--hist-features", type=int, help=f"histograms in panel (b) (default {HIST_FEATURES})")
    ap.add_argument("--joia-unscaled", action="store_true",
                    help="column selection on unscaled attributes, as the method is implemented")
    ap.add_argument("--vera-panel", type=int, default=1,
                    help="which of VERA's descriptive layouts panel (h) shows, by rank (1 or 2)")
    ap.add_argument("--merge-threshold", type=float, help="VERA's descriptive merge threshold (default 0.8)")
    ap.add_argument("--min-region-size", type=int,
                    help="VERA's descriptive cluster_min_samples, the smallest region it shows (default 5)")
    ap.add_argument("--vera-padding", type=float,
                    help="a fixed axis padding for VERA's panel (default: VERA_PADDING, or VERA's own choice)")
    ap.add_argument("--no-wrap", action="store_true",
                    help="VERA's descriptors one per line, unwrapped (default: wrapped at VERA_FIGURE_WIDTH)")
    ap.add_argument("--embedding", help="an embedding variant of the dataset, e.g. umap (default: the dataset's "
                                         "default)")
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    key = f"{args.dataset}/{args.embedding}" if args.embedding else args.dataset
    dbscan = DBSCAN.get(key, DEFAULT_DBSCAN)
    fs.setup()
    # Attribute names such as "net price, income $0-30k ($)" hold dollar
    # signs, not mathtext
    matplotlib.rcParams["text.parse_math"] = False
    vera.plotting.initial_text_location_placement = place_labels_off_long_side
    data = common.datasets.Dataset.load(args.dataset, embedding=args.embedding)
    features, embedding = common.load(args.dataset, embedding=args.embedding)
    X, names, bases = common.numeric_matrix(features)
    labels, _ = common.dbscan_labels(embedding, **dbscan)
    labels = by_size(labels)

    attribute = args.attribute or RANGESET_ATTRIBUTE[args.dataset]
    # Top row, methods that explain the embedding in linked views: the
    # clusters, the IXVC tree, the ccPCA heatmap and histograms; bottom row,
    # methods that overlay the embedding: rangesets, attribute-based, column
    # selection, VERA
    fig, axes = grid(2, 4, ROW_GAP)
    linked, overlay = axes[:4], axes[4:]
    rangesets_panel(overlay[0], features, embedding, cfg["rangesets"], attribute, legend_kwargs=FIGURE_LEGEND,
                    title=FIGURE_TITLE)
    dasilva_panel(overlay[1], features, embedding, cfg["dasilva"], "variance", n_colors=DASILVA_COLORS,
                  legend_kwargs=FIGURE_LEGEND, title=FIGURE_TITLE)
    joia_label_panel(overlay[2], X, names, embedding, labels, dict(cfg["joia"], alpha=JOIA_ALPHA),
                     n_words=JOIA_WORDS, scale=JOIA_SCALE and not args.joia_unscaled, title=FIGURE_TITLE)
    # Without --focus, the linked views follow the largest cluster, C1
    focus = (args.focus or 1) - 1
    clusters_panel(linked[0], embedding, labels, focus)
    # The linked-view row after the clusters: the histogram column, the
    # tree, TREE_WIDTH panels wide, and the heatmap, HEAT_WIDTH panels wide
    order = ("hist", "tree", "heat")
    p0, p1 = linked[0].get_position(), linked[1].get_position()
    panel_w, gap = p0.width, p1.x0 - p0.x1
    for ax in linked[1:]:
        ax.remove()
    widths = {"tree": TREE_WIDTH * panel_w, "heat": HEAT_WIDTH * panel_w}
    widths["hist"] = 1 - p0.x1 - 3 * gap - sum(LINKED_GAPS) * panel_w - widths["tree"] - widths["heat"]
    x = p0.x1
    view_axes = {}
    for kind, extra in zip(order, LINKED_GAPS):
        x += gap + extra * panel_w
        view_axes[kind] = fig.add_axes([x, p0.y0, widths[kind], p0.height])
        x += widths[kind]
    tree_ax, heat_ax, hist_ax = view_axes["tree"], view_axes["heat"], view_axes["hist"]
    ixvc_tree_panel(tree_ax, X, names, labels, focus)
    ccpca_heatmap_panel(heat_ax, X, names, labels, cfg["ccpca"], focus, label_share=HEAT_LABEL_WIDTH / HEAT_WIDTH)
    ccpca_hist_panel(hist_ax, X, names, bases, labels, cfg["ccpca"], focus,
                     n_features=args.hist_features or HIST_FEATURES)
    print(f"[{args.dataset}] related methods done", flush=True)

    descriptive_kw = {}
    if args.merge_threshold is not None:
        descriptive_kw["merge_threshold"] = args.merge_threshold
    if args.min_region_size is not None:
        descriptive_kw["cluster_min_samples"] = args.min_region_size
    layouts, n_des = vera_layouts(features, embedding, data.indicator_columns, cfg,
                                  cfg["datasets"].get(args.dataset), descriptive_kw)
    layout = layouts[min(args.vera_panel, n_des) - 1]
    plot_vera(overlay[3], layout, fixed_padding=args.vera_padding if args.vera_padding is not None else
              VERA_PADDING.get(key), keep_clear=LETTER_CORNER, indicate_membership=True,
                            max_descriptors=VERA_DESCRIPTORS,
                            max_width=VERA_NOWRAP_WIDTH if args.no_wrap else
                            VERA_FIGURE_WIDTH_BY_KEY.get(key, VERA_FIGURE_WIDTH),
                            label_kwargs=dict(fs.LABEL_KWARGS, fontsize=TEXT_PT),
                            scatter_kwargs=fs.SCATTER_KWARGS)
    overlay[3].set_title("VERA (ours)", **FIGURE_TITLE)
    if not args.frames:
        for ax in overlay + [linked[0], heat_ax, hist_ax]:
            for sp in ax.spines.values():
                sp.set_visible(False)
    panels = [linked[0]] + [view_axes[k] for k in order] + overlay
    for i, ax in enumerate(panels):
        title_letter(ax, i)
    for ax in fig.axes:
        fs.shuffle_points(ax)
    os.makedirs(FIG_DIR, exist_ok=True)
    suffix = ("" if args.dataset == DATASET else f"-{args.dataset}") + ("-framed" if args.frames else "") + (f"-{args.attribute.split()[0]}" if args.attribute else "") + \
        (f"-vera{args.vera_panel}" if args.vera_panel != 1 else "") + \
        (f"-merge{args.merge_threshold:g}" if args.merge_threshold is not None else "") + \
        (f"-min{args.min_region_size}" if args.min_region_size is not None else "") + \
        (f"-{args.embedding}" if args.embedding else "") + \
        (f"-pad{args.vera_padding:g}" if args.vera_padding is not None else "") + \
        ("-nowrap" if args.no_wrap else "") + \
        ("-unscaled" if args.joia_unscaled else "") + \
        (f"-hist{args.hist_features}" if args.hist_features else "")
    path = os.path.join(FIG_DIR, "fig_related_methods" + suffix)
    fig.savefig(path + ".pdf", dpi=300, transparent=True, bbox_inches="tight", pad_inches=0)
    fig.savefig(path + ".png", dpi=cfg.get("png_dpi", 450), bbox_inches="tight", pad_inches=0, facecolor="white")
    print(f"wrote {path}.png ({fig.get_size_inches()[0]:.2f} x {fig.get_size_inches()[1]:.2f} in)")


if __name__ == "__main__":
    main()
