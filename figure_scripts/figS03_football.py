"""The supplement's full VERA explanations of the football players dataset of
the manuscript's comparison figure (Fig. S3), in the style of the
manuscript's case-study figures: its four highest-ranked contrastive layouts
(a-d) above its four highest-ranked descriptive layouts (e-h), each row under
its title, at the supplement's text width.

The layouts are computed with the comparison figure's VERA settings
(fig02_related_methods.py): the same region construction, descriptor ranking,
label budget, and line width, except that a descriptive region holds at
least MIN_REGION_SIZE points: at VERA's default of 5, the third and fourth
descriptive layouts hold about ten small regions each, whose labels cannot be
laid out in a quarter of the text width. Panel e is the comparison figure's
VERA panel either way. Contrastive labels show up to CONTRASTIVE_DESCRIPTORS
descriptors and descriptive labels up to DESCRIPTIVE_DESCRIPTORS, more than
the comparison figure's two, since the supplement's labels are smaller.
Labels are at the supplement's label size,
figstyle.LABEL_KWARGS. Every panel is drawn at the same axis padding, PADDING
or --padding, so that the embedding is equally large in all of them; PADDING
is the smallest at which the labels of panels f and g still fit above the
embedding.

Writes figures/fig_supp_football.{pdf,png}, with the padding appended to the
name when it is not PADDING.

Usage: python figS03_football.py [--config config.json] [--padding 0.2]
"""
import argparse
import json
import os

import contextlib

import matplotlib
matplotlib.use("Agg")

import shapely.affinity  # noqa: E402
import vera.plotting  # noqa: E402

import fig02_related_methods as mrf  # noqa: E402

common, fs = mrf.common, mrf.fs
N_PANELS = 4
# fs.letter's corner, (x0, y0, x1, y1) in axes fractions, kept clear of
# labels
LETTER_CORNER = (0, 0.88, 0.1, 1)
ROW_TITLES = ("Contrastive Explanations", "Descriptive Explanations")
ROW_TITLE_PT = 9
MIN_REGION_SIZE = 100
CONTRASTIVE_DESCRIPTORS = 5
DESCRIPTIVE_DESCRIPTORS = 3
# The axis padding of every panel, as a fraction of the embedding's extent
PADDING = 0.1
# The figure's dpi while VERA lays out labels, which it measures on the
# canvas: at the default 150 dpi, 4 pt text is hinted a few percent narrower
# than it prints, and labels VERA lays out side by side touch
LAYOUT_DPI = 600


def separate_labels(boxes, regions, frame, gap, max_shift, max_rounds=20):
    """`boxes` with every overlapping pair moved `gap` (x, y in data units)
    apart, keeping every label inside `frame` (x0, y0, x1, y1).
    A pair is moved along the axis that needs the shorter move: horizontally,
    the label nearer the frame's centre moves as far as the frame lets it and
    the other the rest; vertically, the label nearer the centre moves, or
    else the other, by at most `max_shift` and not onto its own region in
    `regions`, so that a label is not moved far from or over its region. A
    pair neither move separates is moved apart horizontally as far as the
    frame lets it."""
    fx0, fy0, fx1, fy1 = frame
    centre = ((fx0 + fx1) / 2, (fy0 + fy1) / 2)
    boxes = list(boxes)

    def room(box, d, sign):
        x0, y0, x1, y1 = box.bounds
        lo, hi = ((x0, x1), (y0, y1))[d]
        return (((fx1, fy1)[d] - hi) if sign > 0 else (lo - (fx0, fy0)[d]))

    def move(k, d, shift):
        boxes[k] = shapely.affinity.translate(boxes[k], *((shift, 0) if d == 0 else (0, shift)))

    for _ in range(max_rounds):
        moved = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i].bounds, boxes[j].bounds
                overlap = [min(a[d + 2], b[d + 2]) - max(a[d], b[d]) for d in (0, 1)]
                if min(overlap) <= 0:
                    continue
                depth = [overlap[d] + gap[d] for d in (0, 1)]
                # Each label's direction away from the other along each axis,
                # and the pair ordered with the label nearer the centre first
                sign = [1 if (a[d] + a[d + 2]) > (b[d] + b[d + 2]) else -1 for d in (0, 1)]
                pair = lambda d: sorted(((i, sign[d]), (j, -sign[d])),
                                        key=lambda ks: abs((boxes[ks[0]].bounds[d] + boxes[ks[0]].bounds[d + 2]) / 2 - centre[d]))
                rooms = [[max(0, room(boxes[k], d, s)) for k, s in pair(d)] for d in (0, 1)]
                done = False
                for d in sorted((0, 1), key=lambda d: depth[d]):
                    if d == 0 and sum(rooms[0]) >= depth[0]:
                        (k, s), (m, t) = pair(0)
                        first = min(depth[0], rooms[0][0])
                        move(k, 0, s * first)
                        move(m, 0, t * (depth[0] - first))
                        done = True
                    elif d == 1 and depth[1] <= max_shift:
                        for (k, s), r in zip(pair(1), rooms[1]):
                            moved_box = shapely.affinity.translate(boxes[k], yoff=s * depth[1])
                            if r >= depth[1] and not (moved_box.intersects(regions[k])
                                                      and not boxes[k].intersects(regions[k])):
                                boxes[k] = moved_box
                                done = True
                                break
                    if done:
                        break
                moved |= done
                if not done:
                    for (k, s), r in zip(pair(0), rooms[0]):
                        move(k, 0, s * r)
        if not moved:
            break
    return boxes


@contextlib.contextmanager
def labels_clear_of(ax, corner, margin=0.03, side_margin=0.02, max_shift=0.12):
    """While plotting on `ax`, move every label that VERA's layout leaves
    over `corner` (axes fractions) right or down, whichever is shorter, until
    it is `margin` (axes fractions) clear of it, then every label that comes
    within `side_margin` of a side of the axes inside that margin, and then
    labels that these moves leave overlapping apart, by at most `max_shift`
    vertically (separate_labels). VERA draws each leader from its label's
    final position, so the leaders follow. Crowded panels can leave a label
    in the corner, although it is part of the footprint VERA keeps labels
    off, or past the frame, which clips it."""
    optimize = vera.plotting.optimize_label_positions

    def nudged(boxes, regions, *args, **kwargs):
        boxes, history = optimize(boxes, regions, *args, **kwargs)
        (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
        mx, my = margin * (x1 - x0), margin * (y1 - y0)
        sx, sy = side_margin * (x1 - x0), side_margin * (y1 - y0)
        cx1 = x0 + corner[2] * (x1 - x0) + mx
        cy0 = y0 + corner[1] * (y1 - y0) - my
        corner_box = shapely.box(x0 + corner[0] * (x1 - x0), cy0, cx1, y0 + corner[3] * (y1 - y0))
        out = []
        for box in boxes:
            if box.intersects(corner_box):
                bx0, _, _, by1 = box.bounds
                dx, dy = cx1 - bx0, by1 - cy0
                box = shapely.affinity.translate(box, xoff=dx) if dx <= dy else \
                    shapely.affinity.translate(box, yoff=-dy)
            bx0, by0, bx1, by1 = box.bounds
            dx = max(0, x0 + sx - bx0) - max(0, bx1 - (x1 - sx))
            dy = max(0, y0 + sy - by0) - max(0, by1 - (y1 - sy))
            out.append(shapely.affinity.translate(box, xoff=dx, yoff=dy))
        out = separate_labels(out, regions, (x0 + sx, y0 + sy, x1 - sx, y1 - sy), (mx / 2, my / 3),
                              max_shift * (y1 - y0))
        return out, history

    vera.plotting.optimize_label_positions = nudged
    try:
        yield
    finally:
        vera.plotting.optimize_label_positions = optimize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(mrf.HERE, "config.json"))
    ap.add_argument("--padding", type=float, default=PADDING, help=f"the axis padding of every panel (default {PADDING})")
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    fs.setup()
    matplotlib.rcParams["text.parse_math"] = False
    vera.plotting.initial_text_location_placement = mrf.place_labels_off_long_side
    data = common.datasets.Dataset.load(mrf.DATASET)
    features, embedding = common.load(mrf.DATASET)
    layouts, n_des = mrf.vera_layouts(features, embedding, data.indicator_columns, cfg,
                                      cfg["datasets"].get(mrf.DATASET),
                                      descriptive_kw={"cluster_min_samples": MIN_REGION_SIZE}, n_panels=N_PANELS)
    rows = (layouts[n_des:], layouts[:n_des])
    max_descriptors = (CONTRASTIVE_DESCRIPTORS, DESCRIPTIVE_DESCRIPTORS)

    fig, axes = fs.grid(2, N_PANELS, figwidth=fs.SUPPLEMENT_TEXTWIDTH_IN, dpi=LAYOUT_DPI, row_titles=True)
    for r, (row, title) in enumerate(zip(rows, ROW_TITLES)):
        row_axes = axes[r * N_PANELS:(r + 1) * N_PANELS]
        for i, ax in enumerate(row_axes):
            if i < len(row):
                with labels_clear_of(ax, LETTER_CORNER):
                    mrf.plot_vera(ax, row[i], fixed_padding=args.padding, keep_clear=LETTER_CORNER,
                                  indicate_membership=True,
                                  max_descriptors=max_descriptors[r],
                                  max_width=mrf.VERA_FIGURE_WIDTH_BY_KEY.get(mrf.DATASET, mrf.VERA_FIGURE_WIDTH),
                                  label_kwargs=fs.LABEL_KWARGS, scatter_kwargs=fs.SCATTER_KWARGS)
                fs.shuffle_points(ax)
            else:
                ax.set_xticks([])
                ax.set_yticks([])
            fs.letter(ax, r * N_PANELS + i)
        # After plotting, which clears the axes
        fs.row_title(row_axes[0], title, fontsize=ROW_TITLE_PT)
    os.makedirs(mrf.FIG_DIR, exist_ok=True)
    suffix = "" if args.padding == PADDING else f"-pad{args.padding:g}"
    path = os.path.join(mrf.FIG_DIR, "fig_supp_football" + suffix)
    fs.save(fig, path, pad_inches=0)
    print(f"wrote {path}.pdf", flush=True)


if __name__ == "__main__":
    main()
