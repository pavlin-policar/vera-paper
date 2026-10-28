"""Figure conventions shared by the supplementary studies.

Reproduces the styling of the manuscript's usage-scenario figures: panels sized
to the IEEE two-column text width, small Arial labels, rasterized 1-pt scatter
points, and bold lowercase panel letters in the top-left corner of each axis.
"""
import string

import matplotlib
import matplotlib.pyplot as plt

# \textwidth and \columnwidth of the manuscript (IEEEtran, journal, letter
# paper), measured with LaTeX. LaTeX's points are 1/72.27 in, smaller than
# PDF points (1/72 in)
TEXTWIDTH_PT = 516.0
COLWIDTH_PT = 252.0
PT_PER_INCH = 72.27

TEXTWIDTH_IN = TEXTWIDTH_PT / PT_PER_INCH
COLWIDTH_IN = COLWIDTH_PT / PT_PER_INCH

# \textwidth of supplementary-material.tex (article, 10 pt, 1 in margins on
# letter paper), measured with LaTeX. Figures included at \textwidth there
# print their fonts at the manuscript's sizes only when rendered at this width.
SUPPLEMENT_TEXTWIDTH_PT = 469.75502
SUPPLEMENT_TEXTWIDTH_IN = SUPPLEMENT_TEXTWIDTH_PT / PT_PER_INCH

LABEL_KWARGS = {"fontsize": 4, "clip_on": True, "fontfamily": "Arial"}
SCATTER_KWARGS = {"rasterized": True, "s": 1, "lw": 0}
# Presence-style descriptors are bare names, so a wrapped comma-separated run
# reads better than one name per line; the count of further names takes a
# line of its own
INDICATOR_LABEL_KWARGS = {"sep": ", ", "truncation_sep": "\n", "max_width": 32}
# Rule descriptors of tabular data, at most five per label and wrapped at 28
# characters, so that labels of four or five rules fit around the data of a
# supplement-width panel
RULE_LABEL_KWARGS = {"max_descriptors": 5, "max_width": 28}
# VERA's 1.5 pt default leader lines outweigh 4 pt labels at print size
LEADER_KWARGS = {"lw": 0.75}


def shuffle_points(ax, seed: int = 0):
    """Draw the points of each scatter in `ax` in a random order, fixed by
    `seed`, so that no colour is systematically drawn over the others."""
    from matplotlib.collections import PathCollection
    import numpy as np

    rng = np.random.default_rng(seed)
    for coll in ax.collections:
        if not isinstance(coll, PathCollection):
            continue
        n = len(coll.get_offsets())
        if n < 2:
            continue
        perm = rng.permutation(n)
        coll.set_offsets(np.asarray(coll.get_offsets())[perm])
        # Colour-mapped values are coloured at draw time; explicit colours
        # are per point only where there is one for every point
        if coll.get_array() is not None and len(coll.get_array()) == n:
            coll.set_array(np.asarray(coll.get_array())[perm])
        else:
            for get, set_ in ((coll.get_facecolors, coll.set_facecolors), (coll.get_edgecolors, coll.set_edgecolors)):
                colors = get()
                if len(colors) == n:
                    set_(colors[perm])
        if len(coll.get_sizes()) == n:
            coll.set_sizes(coll.get_sizes()[perm])
        if len(coll.get_linewidths()) == n:
            coll.set_linewidths(np.asarray(coll.get_linewidths())[perm])


def matched_colors(layouts, min_shared: float = 0.5):
    """Region colors for a row of contrastive layouts, in which one cluster
    keeps one color across panels.

    The first layout takes VERA's default colors (tab10, in layout order). A
    region of a later layout takes the color of the first layout's region
    that holds at least `min_shared` of its samples, the largest regions
    choosing first; the regions left without a color then take the panel's
    free colors in palette order. `None` entries are skipped."""
    import glasbey
    import matplotlib.colors as mcolors

    layouts = [layout for layout in layouts if layout]
    n_colors = max(len(layout) for layout in layouts)
    palette = glasbey.extend_palette("tab10", palette_size=n_colors) if n_colors > 10 else "tab10"
    palette = [mcolors.to_rgb(c) for c in (palette if isinstance(palette, list)
                                           else plt.get_cmap(palette).colors)]

    reference = {ra: palette[i] for i, ra in enumerate(layouts[0])}
    ref_samples = {ra: set(ra.contained_samples) for ra in layouts[0]}
    colors = dict(reference)
    for layout in layouts[1:]:
        used = []
        unmatched = []
        for ra in sorted(layout, key=lambda r: len(r.contained_samples), reverse=True):
            own = set(ra.contained_samples)
            shared = {ref: len(own & s) / len(own) for ref, s in ref_samples.items()}
            candidates = [ref for ref in sorted(shared, key=shared.get, reverse=True)
                          if shared[ref] >= min_shared and reference[ref] not in used]
            if candidates:
                colors[ra] = reference[candidates[0]]
                used.append(colors[ra])
            else:
                unmatched.append(ra)
        for ra in unmatched:
            colors[ra] = next(c for c in palette if c not in used)
            used.append(colors[ra])
    return colors


def setup():
    """Arial, fonts embedded as TrueType (Type 42) so that the PDFs' text is
    editable, and VERA's background-enrichment descriptors in the same
    upright face as the others: VERA sets them in italics by default."""
    import vera.plotting

    matplotlib.rcParams["font.family"] = "Arial"
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    vera.plotting.DEFAULT_BACKGROUND_LABEL_KWARGS = {}


# Gap between panels as a fraction of panel width; the axes fill the rest of
# the figure so that a four-panel row at text width gives ~1.7 in panels, the
# size at which 4 pt labels fit around the data
PANEL_GAP = 0.06


# Vertical gap between rows that carry a row title above their first panel
ROW_TITLE_GAP = 0.16


def grid(nrows: int, ncols: int, figwidth: float = TEXTWIDTH_IN, dpi: int = 150, row_titles: bool = False):
    """A panel grid of square axes filling `figwidth`, with no outer margins."""
    hgap = ROW_TITLE_GAP if row_titles else PANEL_GAP
    panel = figwidth / (ncols + (ncols - 1) * PANEL_GAP)
    figheight = panel * (nrows + (nrows - 1) * hgap)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(figwidth, figheight), dpi=dpi)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=PANEL_GAP, hspace=hgap)
    axes = [axes] if nrows * ncols == 1 else list(axes.ravel())
    return fig, axes


def letter(ax, idx: int, offset: float = 0.025, fontsize: int = 9):
    ax.text(
        offset, 1 - offset, string.ascii_lowercase[idx % 26],
        transform=ax.transAxes, va="top", ha="left", fontweight="bold", fontsize=fontsize,
    )


def row_title(ax, text: str, fontsize: int = 7):
    ax.set_title(text, loc="left", fontsize=fontsize, fontweight="bold", pad=3)


def blank(ax):
    ax.axis("off")


def save(fig, path_without_ext: str, dpi: int = 300, pad_inches: float = 0.1, tight: bool = True,
         formats: tuple = ("pdf", "png")):
    """With `pad_inches=0`, a grid saves at exactly its figure width, so it can
    be included at that width without rescaling. Figures whose content does not
    span their width, such as plots with axis labels, are saved with
    `tight=False` at exactly their figure size instead. PNGs are written at
    half of `dpi`."""
    bbox = dict(bbox_inches="tight", pad_inches=pad_inches) if tight else {}
    if "pdf" in formats:
        fig.savefig(path_without_ext + ".pdf", dpi=dpi, transparent=True, **bbox)
    if "png" in formats:
        fig.savefig(path_without_ext + ".png", dpi=dpi // 2, facecolor="white", **bbox)
    plt.close(fig)
