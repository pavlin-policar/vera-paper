"""Views of the reimplemented methods, drawn on matplotlib axes, that
fig02_related_methods.py composes into the manuscript's comparison figure:
rangesets, the attribute-based explanation's dense map, the column selection
method's polygons, and IXVC's decision tree, with the legend, palette, and
axis helpers they share."""
import textwrap

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

from . import attribute_explanation as ae
from . import ixvc

TITLE = dict(fontsize=6, loc="left", pad=2)


def row_major(handles, ncol):
    """Legend handles reordered so that a legend of `ncol` columns, which
    matplotlib fills column by column, reads row by row."""
    nrow = -(-len(handles) // ncol)
    return [handles[r * ncol + c] for c in range(ncol) for r in range(nrow) if r * ncol + c < len(handles)]


def fit_legend_below(ax, handles, **kwargs):
    """A legend below `ax` with as many columns as fit within the width of
    the axes, read row by row; `kwargs` are passed on to `ax.legend`."""
    renderer = ax.figure.canvas.get_renderer()
    width = ax.get_window_extent(renderer).width
    for ncol in range(len(handles), 0, -1):
        legend = ax.legend(handles=row_major(handles, ncol), ncol=ncol, **kwargs)
        if ncol == 1 or legend.get_window_extent(renderer).width <= width:
            return legend
        legend.remove()


def palette(n):
    base = [mcolors.to_rgb(c) for c in plt.get_cmap("tab10").colors]
    if n <= len(base):
        return base[:n]
    import glasbey
    return [mcolors.to_rgb(c) for c in glasbey.extend_palette("tab10", palette_size=n, colorblind_safe=True)[:n]]


def square_limits(ax, xy, pad=0.08):
    lo, hi = np.nanmin(xy, axis=0), np.nanmax(xy, axis=0)
    c, half = (lo + hi) / 2, max(hi - lo) / 2 * (1 + pad)
    ax.set_xlim(c[0] - half, c[0] + half)
    ax.set_ylim(c[1] - half, c[1] + half)


def bare(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")


DASILVA_PALETTE = [mcolors.to_rgb(col) for col in plt.get_cmap("Set1").colors]


def dasilva_view(ax, embedding, explanation, label_of, rho_c, xlim, ylim, fill, title=None, n_colors=ae.N_COLORS,
                 legend_loc="lower left", legend_kwargs=None):
    """Dense map of per-point explanations: the `n_colors` most frequent in
    colour, the rest dark blue, brightness the confidence within rho_c."""
    classes = ae.colour_classes(explanation, n_colors)
    colour_of = {k: DASILVA_PALETTE[i] for i, k in enumerate(classes)}
    keys = [str(e) for e in explanation]
    cols = np.array([colour_of.get(k, ae.DARK_BLUE) for k in keys])
    conf = ae.confidence(embedding, keys, rho_c)
    img = ae.dense_map(embedding, cols, conf, xlim, ylim, fill)
    ax.imshow(img, origin="lower", extent=(*xlim, *ylim), interpolation="nearest")
    counts = {k: keys.count(k) for k in classes}
    def short(text):
        return text if len(text) <= 42 else text[:41] + "\u2026"
    handles = [plt.Line2D([], [], marker="s", ls="", ms=3, color=colour_of[k],
                          label=f"{short(label_of(k))} ({counts[k] / len(keys):.0%})") for k in classes]
    if len(set(keys)) > len(classes):
        handles.append(plt.Line2D([], [], marker="s", ls="", ms=3, color=ae.DARK_BLUE, label="other"))
    if legend_kwargs and legend_kwargs.get("below"):
        fit_legend_below(ax, handles, **{"fontsize": 3.5, **{k: v for k, v in legend_kwargs.items() if k != "below"}})
    else:
        ax.legend(handles=handles, loc=legend_loc, fontsize=3.5, frameon=True, framealpha=0.85, edgecolor="none",
                  handletextpad=0.2, borderaxespad=0.2, borderpad=0.3)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    bare(ax)
    if title is not None:
        ax.set_title(title, **TITLE)
    return classes, conf


def keep_inside(ax, texts, margin=2):
    """Shift each text so that its box lies inside the axes (display units),
    without changing its size."""
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    box = ax.get_window_extent(renderer)
    inv = ax.transData.inverted()
    for t in texts:
        bb = t.get_window_extent(renderer)
        dx = max(0, box.x0 + margin - bb.x0) - max(0, bb.x1 - (box.x1 - margin))
        dy = max(0, box.y0 + margin - bb.y0) - max(0, bb.y1 - (box.y1 - margin))
        if dx or dy:
            x, y = ax.transData.transform(t.get_position())
            t.set_position(inv.transform((x + dx, y + dy)))


def joia_polygons(ax, embedding, tri, owner, pastel):
    """Each cluster's polygon (its Delaunay triangles) in its pastel colour."""
    for c in range(len(pastel)):
        tris = tri.simplices[owner == c]
        if len(tris):
            ax.tripcolor(embedding[:, 0], embedding[:, 1], tris, facecolors=np.zeros(len(tris)),
                         cmap=mcolors.ListedColormap([pastel[c]]), edgecolors="face", lw=0.1, zorder=0,
                         rasterized=True)


def tree_layout(nodes, max_depth):
    """Positions of the drawn nodes: depth as x, terminal slots as y. Nodes
    below `max_depth` are collapsed into their ancestor at that depth."""
    pos, depth, slot = {}, {}, [0]

    def visit(i, d):
        node = nodes[i]
        depth[i] = d
        if node["leaf"] or d == max_depth:
            pos[i] = (d, slot[0])
            slot[0] += 1
            return pos[i][1]
        a = visit(node["left"], d + 1)
        b = visit(node["right"], d + 1)
        pos[i] = (d, (a + b) / 2)
        return pos[i][1]

    visit(0, 0)
    return pos, slot[0]


def ixvc_tree_view(tax, nodes, classes, col_of, names, draw_depth, pos=None, n_slots=None, compact=False,
                   focus=None, focus_color="black", wrap_width=None, group_name="group {}", fontsize=3.5,
                   subtree_note=True, link_labels="all", focus_share=False, margins=None):
    """The decision tree, root on the left, TRUE (the split's rule holds)
    above FALSE; subtrees below `draw_depth` collapsed into a summary box.
    `compact` boxes show only the split, or a leaf's majority group with its
    share of the samples. With a `focus` group, the path that follows most
    of its samples is drawn bold: its links in `focus_color`, its split boxes
    outlined in `focus_color`, and its last box in its group's colour with a
    thicker outline. With `wrap_width`, compact split labels longer than
    that many characters wrap. `group_name` formats a group's number. Boxes
    are set in `fontsize` points and their links' labels slightly smaller;
    without `subtree_note`, a compact collapsed subtree is drawn like a leaf,
    in a dashed box, without its leaf count. `link_labels` "root" labels
    only the root's links TRUE and FALSE, where narrow columns leave no room
    for the rest; every split sends TRUE to its upper child. With
    `focus_share`, the compact box that ends the focus group's path gives
    the focus group's share of its samples, in its colour, instead of the
    majority group's. `margins` (left, right), in depth units, overrides the
    room left of the root and right of the deepest boxes."""
    if pos is None:
        pos, n_slots = tree_layout(nodes, draw_depth)
    # The focus group's path runs from the root into whichever child holds
    # more of its samples, down to a drawn leaf or collapsed subtree
    on_path = set()
    if focus is not None:
        fi = classes.index(focus)
        i = 0
        while True:
            on_path.add(i)
            node = nodes[i]
            if node["leaf"] or node["left"] not in pos:
                break
            i = max((node["left"], node["right"]), key=lambda c: nodes[c]["counts"][fi])
    tax.axis("off")
    max_d = max(d for d, _ in pos.values())
    # Compact boxes sit in a square panel, where the root's box needs more
    # room on the left than the leaves' boxes on the right
    left, right = margins or ((0.75, 0.55) if compact else (0.3, 0.75))
    tax.set_xlim(-left, max_d + right)
    tax.set_ylim(n_slots - 0.5, -0.5)

    def descendants_leaves(i):
        node = nodes[i]
        return 1 if node["leaf"] else descendants_leaves(node["left"]) + descendants_leaves(node["right"])

    boxes = {}
    for i, (d, y) in pos.items():
        node = nodes[i]
        counts = node["counts"]
        maj = classes[node["majority"]]
        collapsed = not node["leaf"] and d == draw_depth
        if compact:
            if node["leaf"] or collapsed:
                shown = focus if focus_share and i in on_path else maj
                lines = [f"{group_name.format(shown + 1)}: {counts[classes.index(shown)] / node['samples']:.0%} of "
                         f"{node['samples']}"]
                if collapsed and subtree_note:
                    lines.append(f"(subtree of {descendants_leaves(i)} leaves)")
                ec, lw = col_of[shown], 0.8
            else:
                split = ixvc.split_rule(node, names)
                lines = textwrap.wrap(split, wrap_width) if wrap_width else [split]
                ec, lw = "black", 0.4
        elif node["leaf"] or collapsed:
            nz = [f"{classes[c] + 1}:{n}" for c, n in enumerate(counts) if n > 0]
            value = "[" + ", ".join(map(str, counts)) + "]" if len(counts) <= 6 else "{" + ", ".join(nz[:6]) + \
                (", …" if len(nz) > 6 else "") + "}"
            lines = [f"impurity = {node['entropy']:.2f}", f"samples = {node['samples']}", f"value = {value}"]
            if collapsed:
                lines.insert(0, f"… subtree of {descendants_leaves(i)} leaves")
            ec, lw = col_of[maj], 0.8
        else:
            lines = [ixvc.split_rule(node, names, digits=5, le="<="), f"entropy = {node['entropy']:.2f}",
                     f"samples = {node['samples']}"]
            ec, lw = "black", 0.4
        if i in on_path:
            ec, lw = (ec if node["leaf"] or collapsed else focus_color), 1.4
        ls = "--" if compact and collapsed and not subtree_note else "-"
        boxes[i] = tax.text(d, y, "\n".join(lines), fontsize=fontsize, ha="center", va="center", fontfamily="Arial",
                            zorder=3, linespacing=1.1,
                            bbox=dict(boxstyle="square,pad=0.35", fc="white", ec=ec, lw=lw, ls=ls))

    # Links run from a node's box to its children's boxes, which are sized
    # only once the figure is drawn
    fig = tax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = tax.transData.inverted()

    def x_edges(i):
        bb = boxes[i].get_bbox_patch().get_window_extent(renderer)
        return inv.transform((bb.x0, 0))[0], inv.transform((bb.x1, 0))[0]

    for i, (d, y) in pos.items():
        node = nodes[i]
        for child, lab in ((node["left"], "TRUE"), (node["right"], "FALSE")):
            if node["leaf"] or child not in pos:
                continue
            cy = pos[child][1]
            xs_ = np.linspace(x_edges(i)[1], x_edges(child)[0], 30)
            u = (xs_ - xs_[0]) / (xs_[-1] - xs_[0])
            ys_ = y + (cy - y) * (3 * u ** 2 - 2 * u ** 3)
            marked = child in on_path
            tax.plot(xs_, ys_, color=focus_color if marked else "0.6", lw=1.2 if marked else 0.4, zorder=1)
            if link_labels == "root" and i != 0:
                continue
            tax.text(xs_[15], ys_[15], lab, fontsize=fontsize * 6 / 7, color="0.4", ha="center", va="center",
                     fontfamily="Arial",
                     bbox=dict(fc="white", ec="none", pad=0.3), zorder=2)


RS_INLIER_S = 0.6
RS_OUTLIER_S = 4.0


def rangeset_view(ax, embedding, bins, legend=True, legend_loc="lower right", legend_kwargs=None):
    """Each bin's region at alpha 0.5 without outline, in ascending bin
    order, below every point drawn opaque in its bin colour; outliers about
    2.5 times the inliers' diameter."""
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path

    def path_of(poly):
        verts, codes = [], []
        for ring in [poly.exterior, *poly.interiors]:
            xy = np.asarray(ring.coords)
            verts.extend(xy)
            codes.extend([Path.MOVETO] + [Path.LINETO] * (len(xy) - 2) + [Path.CLOSEPOLY])
        return Path(verts, codes)

    for b in bins:
        for poly in b["region"].geoms:
            ax.add_patch(PathPatch(path_of(poly), fc=b["color"], ec="none", alpha=0.5, zorder=1, rasterized=True))
    # One scatter of every bin's inliers and one of the outliers, so that
    # the points of different bins can be drawn interleaved
    for kind, s, z in (("inliers", RS_INLIER_S, 2), ("outliers", RS_OUTLIER_S, 3)):
        idx = [np.asarray(b[kind], dtype=int) for b in bins]
        if sum(len(i) for i in idx):
            ax.scatter(*embedding[np.concatenate(idx)].T, c=[b["color"] for b, i in zip(bins, idx) for _ in i], s=s,
                       lw=0, zorder=z, rasterized=True)
    bare(ax)
    square_limits(ax, embedding)
    if legend:
        # A legend beside the data lists the highest range on top; one below
        # it reads from the lowest
        below = bool(legend_kwargs and legend_kwargs.get("below"))
        order = bins if below else bins[::-1]
        handles = [plt.Line2D([], [], marker="s", ls="", ms=3, color=b["color"], alpha=0.8, label=b["label"])
                   for b in order]
        handles.append(plt.Line2D([], [], marker="o", ls="", ms=2.2, color="0.3", label="outlier"))
        if below:
            fit_legend_below(ax, handles,
                             **{"fontsize": 3.5, **{k: v for k, v in legend_kwargs.items() if k != "below"}})
        else:
            ax.legend(handles=handles, loc=legend_loc, fontsize=3.5, frameon=False, handletextpad=0.2,
                      borderaxespad=0.2, labelspacing=0.3)
