"""Render the runtime figure of the manuscript (Fig. `fig:benchmarks`).

Reads the benchmark results in `data/benchmarks/` (produced by
`run_benchmarks.py`) and writes `figures/benchmarks.pdf` and `.png`, a
single-column figure with two panels:
(a) runtime against the number of samples for several feature counts, and
(b) explanation-generation runtime against the number of region
annotations left after post hoc merging and filtering, with a log-log regression fit and a one-standard-deviation band.
"""
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.legend_handler import HandlerBase
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
from sklearn.linear_model import LinearRegression

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data", "benchmarks")
FIG_DIR = os.path.join(HERE, "figures")

COLWIDTH_IN = 251.31898 / 72
FIG_HEIGHT_IN = 73.3332 / 72
FONTSIZE = 6
LINEWIDTH = 0.6

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": FONTSIZE,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.major.size": 2,
    "ytick.major.size": 2,
    "xtick.major.pad": 1.5,
    "ytick.major.pad": 1.5,
    "axes.labelpad": 1.5,
    "hatch.linewidth": 0.4,
    "pdf.fonttype": 42,
})

GRID_KWARGS = dict(zorder=1, linestyle="dashed", linewidth=0.25, color="#ebebeb")
CONTRASTIVE = dict(marker="o", line="dashdot", face="#cccccc", alpha=1, hatch="///")
DESCRIPTIVE = dict(marker="^", line="dashed", face="#cccccc", alpha=0.25, hatch="\\\\\\")


def thousands(x, _):
    """Format ticks with a dot as the thousands separator."""
    return format(int(x), ",").replace(",", ".")


def minutes(x, _):
    return int(x / 60)


def style_axis(ax):
    ax.grid(**GRID_KWARGS)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_position(("outward", 3))
    ax.xaxis.set_major_formatter(FuncFormatter(thousands))
    ax.yaxis.set_major_formatter(FuncFormatter(minutes))


def fit_line(x, y, x_min, x_max):
    """Fit a line in log-log space and return it with a +-1 residual SD band."""
    x_log, y_log = np.log(x)[:, None], np.log(y)
    lr = LinearRegression().fit(x_log, y_log)
    residual_std = np.std(lr.predict(x_log) - y_log)

    x_plt = np.linspace(x_min, x_max)
    y_log_plt = lr.predict(np.log(x_plt[:, None]))
    return (
        x_plt,
        np.exp(y_log_plt),
        np.exp(y_log_plt - residual_std),
        np.exp(y_log_plt + residual_std),
    )


class BandWithMarker(HandlerBase):
    """Legend entry showing the fit band with its line, followed by the marker."""

    def __init__(self, style):
        super().__init__()
        self.style = style

    def create_artists(self, legend, orig_handle, xdescent, ydescent, width,
                       height, fontsize, trans):
        band_width = 0.7 * width
        band = Rectangle(
            (-xdescent, -ydescent), band_width, height,
            facecolor=self.style["face"], alpha=self.style["alpha"],
            hatch=self.style["hatch"], edgecolor="k", lw=0.4,
            linestyle=self.style["line"], transform=trans,
        )
        line = Line2D(
            [-xdescent, -xdescent + band_width], [height / 2 - ydescent] * 2,
            color="k", lw=0.5, linestyle=self.style["line"], transform=trans,
        )
        marker = Line2D(
            [-xdescent + width + 0.35 * height], [height / 2 - ydescent],
            marker=self.style["marker"], markersize=3.5, markerfacecolor="none",
            markeredgecolor="k", markeredgewidth=0.5, linestyle="none",
            transform=trans,
        )
        return [band, line, marker]


def plot_samples(ax):
    data = pd.read_csv(os.path.join(DATA_DIR, "sample-final.csv"))
    agg = (
        data.groupby(["N", "F"])["duration"].mean().reset_index()
        .query("F in [1, 100, 200, 300, 400, 500]")
    )

    ax.set_xlim(0, 20_000)
    ax.set_ylim(0, 390)
    for key, subset in agg.groupby("F"):
        subset = subset.sort_values("N")
        ax.plot(subset["N"], subset["duration"], color="k", lw=LINEWIDTH, zorder=2)

    # Label each line at its right end, rotated along its last segment
    fig = ax.get_figure()
    fig.canvas.draw()
    for key, subset in agg.groupby("F"):
        subset = subset.sort_values("N")
        (x0, y0), (x1, y1) = ax.transData.transform(
            subset[["N", "duration"]].values[-2:]
        )
        angle = np.degrees(np.arctan2(y1 - y0, x1 - x0))
        ax.text(
            subset["N"].iloc[-1], subset["duration"].iloc[-1] + 6, f"|F|={key}",
            va="bottom", ha="right", rotation=angle, rotation_mode="anchor",
            fontsize=FONTSIZE - 1, zorder=3,
        )

    style_axis(ax)
    ax.set_xticks(range(0, 20_001, 5000))
    ax.set_yticks(range(0, 400, 120))
    ax.set_xlabel("Dataset size [samples]")
    # Kept below the panel letter, which shares the left margin
    ax.set_ylabel("Runtime [min]", fontsize=FONTSIZE - 0.5)
    ax.yaxis.set_label_coords(-0.15, 0.42)


def plot_features(ax):
    contrastive = pd.read_csv(os.path.join(DATA_DIR, "feature-contrastive.csv"))
    descriptive = pd.read_csv(os.path.join(DATA_DIR, "feature-descriptive.csv"))

    for data, style in [(contrastive, CONTRASTIVE), (descriptive, DESCRIPTIVE)]:
        ax.scatter(
            data["region_annotations"], data["duration_expl"],
            marker=style["marker"], s=8, lw=0.5, color="k", facecolor="none",
            zorder=3,
        )
        x_plt, y_plt, y_lower, y_upper = fit_line(
            data["region_annotations"].values, data["duration_expl"].values, 5, 1000,
        )
        ax.plot(x_plt, y_plt, color="k", linestyle=style["line"], lw=0.5, zorder=3)
        ax.fill_between(
            x_plt, y_lower, y_upper, color="k", facecolor=style["face"],
            alpha=style["alpha"], linestyle=style["line"], hatch=style["hatch"],
            zorder=2, lw=0.4,
        )

    handles = [Rectangle((0, 0), 1, 1), Rectangle((0, 0), 1, 1)]
    ax.legend(
        handles, ["Contrastive", "Descriptive"],
        handler_map={handles[0]: BandWithMarker(CONTRASTIVE),
                     handles[1]: BandWithMarker(DESCRIPTIVE)},
        loc="upper left", bbox_to_anchor=(0.0, 1.04), frameon=False,
        handlelength=2.6, handletextpad=1.2, labelspacing=0.3, borderaxespad=0,
    )

    style_axis(ax)
    ax.set_xlim(0, 1000)
    ax.set_ylim(1, 600)
    ax.set_yticks(range(0, 600, 180))
    ax.set_xlabel("Region annotations")


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    fig = plt.figure(figsize=(COLWIDTH_IN, FIG_HEIGHT_IN))
    ax_a = fig.add_axes([0.08, 0.33, 0.37, 0.64])
    ax_b = fig.add_axes([0.545, 0.33, 0.375, 0.64])

    plot_samples(ax_a)
    plot_features(ax_b)

    for ax, letter, x in [(ax_a, "a", 0.0), (ax_b, "b", 0.475)]:
        fig.text(x, 1.0, letter, fontsize=FONTSIZE + 4, fontweight="bold",
                 va="top", ha="left")

    fig.savefig(os.path.join(FIG_DIR, "benchmarks.pdf"), dpi=300)
    fig.savefig(os.path.join(FIG_DIR, "benchmarks.png"), dpi=600)


if __name__ == "__main__":
    main()
