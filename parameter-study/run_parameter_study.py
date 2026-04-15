"""
Parameter sensitivity study for VERA.

Reads a config.json specifying datasets and parameter variations, generates
VERA region annotations and explanation layouts under different parameter
settings, saves the figures, and produces per-dataset Markdown reports.

Output per dataset:
  - region-construction.md  — raw region annotations under varying parameters
  - explanation-construction.md — contrastive & descriptive explanations under
    varying explanation-construction parameters

Usage:
    python run_parameter_study.py config.json
"""

import argparse
import json
import os
from importlib.util import module_from_spec, spec_from_file_location

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt

import vera  # noqa: E402
import vera.explain  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGION_PARAM_LABELS = {
    "n_discretization_bins": "Number of bins",
    "contour_level": "Contour level",
    "scale_factor": "Bandwidth scale factor",
    "merge_min_sample_overlap": "Merge overlap threshold",
    "sample_size": "Sample size",
    "random_state": "Random state",
}

EXPLANATION_PARAM_LABELS = {
    "merge_threshold": "Merge threshold",
    "enrich_with_background": "Enrich with background",
    "max_overlap": "Max overlap",
}


def load_datasets_module():
    module_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "supplement-data",
        "datasets.py",
    )
    spec = spec_from_file_location("_supplement_datasets", module_path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ds = load_datasets_module()


def generate_region_annotations(features, embedding, ra_kwargs: dict):
    """Run VERA region construction and return raw region annotations."""
    return vera.an.generate_region_annotations(features, embedding, **ra_kwargs)


def make_explanations(
    region_annotations,
    explanation_types: list[str],
    max_panels: int,
    contrastive_kwargs: dict | None = None,
    descriptive_kwargs: dict | None = None,
) -> dict[str, list]:
    """Generate contrastive/descriptive explanations from region annotations."""
    contrastive_kwargs = contrastive_kwargs or {}
    descriptive_kwargs = descriptive_kwargs or {}

    results = {}
    if "contrastive" in explanation_types:
        results["contrastive"] = vera.explain.contrastive(
            region_annotations, max_panels=max_panels, **contrastive_kwargs
        )
    if "descriptive" in explanation_types:
        results["descriptive"] = vera.explain.descriptive(
            region_annotations, max_panels=max_panels, **descriptive_kwargs
        )
    return results


def save_figure(
    layout,
    save_path: str,
    per_row: int = 4,
    figwidth: float = 16,
):
    """Plot a VERA layout and save to disk."""
    fig, ax = vera.pl.plot_annotations(
        layout,
        per_row=per_row,
        figwidth=figwidth,
        return_ax=True,
        indicate_membership=True,
        scatter_kwargs={"rasterized": True, "s": 2, "lw": 0},
        label_kwargs={"fontsize": 6, "clip_on": True},
    )
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches="tight", transparent=False)
    plt.close(fig)


def param_tag(param_name: str, value) -> str:
    """Create a short filename-safe tag for a parameter value."""
    return f"{param_name}={value}"


def explanation_tag(explanation_type: str, param_name: str, value) -> str:
    return f"{explanation_type}-{param_tag(param_name, value)}"


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def generate_region_construction_md(
    dataset_name: str,
    config: dict,
    fig_dir_name: str = "figures",
) -> str:
    """Build the region-construction Markdown report for one dataset."""
    defaults = config["defaults"]
    variations = config["parameter_variations"]

    lines = [
        f"# Region Construction — {dataset_name}",
        "",
        "This page shows how the region construction parameters affect the "
        "extracted region annotations. Each figure shows the raw region "
        "annotations for all features — one panel per feature (or feature group "
        "after post-hoc merging).",
        "",
        "## Default parameters",
        "",
        "| Parameter | Default value |",
        "|---|---|",
    ]
    for param, val in defaults.items():
        lines.append(f"| {REGION_PARAM_LABELS.get(param, param)} | `{val}` |")
    lines.append("")

    # --- Default region annotations ---
    lines.append("## Default region annotations")
    lines.append("")
    lines.append(f"![region annotations (defaults)]({fig_dir_name}/defaults-regions.png)")
    lines.append("")

    # --- Per-parameter variations ---
    for param_name, values in variations.items():
        label = REGION_PARAM_LABELS.get(param_name, param_name)
        lines.append(f"## Varying: {label}")
        lines.append("")
        lines.append(
            f"Default value: `{defaults[param_name]}`. "
            f"All other parameters held at their defaults."
        )
        lines.append("")
        lines.append(f"| {label} | Region annotations |")
        lines.append("|---|---|")
        for val in values:
            tag = param_tag(param_name, val)
            fname = f"{tag}-regions.png"
            default_marker = " **(default)**" if val == defaults[param_name] else ""
            lines.append(
                f"| `{val}`{default_marker} "
                f"| ![]({fig_dir_name}/{fname}) |"
            )
        lines.append("")

    return "\n".join(lines)


def generate_explanation_construction_md(
    dataset_name: str,
    config: dict,
    fig_dir_name: str = "figures",
) -> str:
    """Build the explanation-construction Markdown report for one dataset."""
    region_defaults = config["defaults"]
    contrastive_defaults = config.get("contrastive_defaults", {})
    contrastive_variations = config.get("contrastive_parameter_variations", {})
    descriptive_defaults = config.get("descriptive_defaults", {})
    descriptive_variations = config.get("descriptive_parameter_variations", {})
    explanation_types = config.get("explanation_types", ["contrastive", "descriptive"])

    lines = [
        f"# Explanation Construction — {dataset_name}",
        "",
        "This page shows how explanation-construction parameters affect the "
        "final contrastive and descriptive explanations generated from the "
        "default region annotations.",
        "",
        "## Default region-construction parameters",
        "",
        "| Parameter | Default value |",
        "|---|---|",
    ]
    for param, val in region_defaults.items():
        lines.append(f"| {REGION_PARAM_LABELS.get(param, param)} | `{val}` |")
    lines.append("")

    if "contrastive" in explanation_types:
        lines.append("## Contrastive defaults")
        lines.append("")
        lines.append("| Parameter | Default value |")
        lines.append("|---|---|")
        for param, val in contrastive_defaults.items():
            lines.append(f"| {EXPLANATION_PARAM_LABELS.get(param, param)} | `{val}` |")
        lines.append("")
        lines.append(f"![contrastive (defaults)]({fig_dir_name}/defaults-contrastive.png)")
        lines.append("")

        for param_name, values in contrastive_variations.items():
            label = EXPLANATION_PARAM_LABELS.get(param_name, param_name)
            lines.append(f"## Contrastive: varying {label}")
            lines.append("")
            lines.append(
                f"Default value: `{contrastive_defaults[param_name]}`. "
                f"All other contrastive parameters held at their defaults."
            )
            lines.append("")
            lines.append(f"| {label} | Explanation |")
            lines.append("|---|---|")
            for val in values:
                tag = explanation_tag("contrastive", param_name, val)
                fname = f"{tag}.png"
                default_marker = " **(default)**" if val == contrastive_defaults[param_name] else ""
                lines.append(f"| `{val}`{default_marker} | ![]({fig_dir_name}/{fname}) |")
            lines.append("")

    if "descriptive" in explanation_types:
        lines.append("## Descriptive defaults")
        lines.append("")
        lines.append("| Parameter | Default value |")
        lines.append("|---|---|")
        for param, val in descriptive_defaults.items():
            lines.append(f"| {EXPLANATION_PARAM_LABELS.get(param, param)} | `{val}` |")
        lines.append("")
        lines.append(f"![descriptive (defaults)]({fig_dir_name}/defaults-descriptive.png)")
        lines.append("")

        for param_name, values in descriptive_variations.items():
            label = EXPLANATION_PARAM_LABELS.get(param_name, param_name)
            lines.append(f"## Descriptive: varying {label}")
            lines.append("")
            lines.append(
                f"Default value: `{descriptive_defaults[param_name]}`. "
                f"All other descriptive parameters held at their defaults."
            )
            lines.append("")
            lines.append(f"| {label} | Explanation |")
            lines.append("|---|---|")
            for val in values:
                tag = explanation_tag("descriptive", param_name, val)
                fname = f"{tag}.png"
                default_marker = " **(default)**" if val == descriptive_defaults[param_name] else ""
                lines.append(f"| `{val}`{default_marker} | ![]({fig_dir_name}/{fname}) |")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(config_path: str):
    with open(config_path) as f:
        config = json.load(f)

    output_dir = os.path.dirname(os.path.abspath(config_path))
    dataset_names = config["datasets"]
    defaults = config["defaults"]
    variations = config["parameter_variations"]
    contrastive_defaults = config.get("contrastive_defaults", {})
    contrastive_variations = config.get("contrastive_parameter_variations", {})
    descriptive_defaults = config.get("descriptive_defaults", {})
    descriptive_variations = config.get("descriptive_parameter_variations", {})
    explanation_types = config.get("explanation_types", ["contrastive", "descriptive"])
    max_panels = config.get("max_panels", 4)

    for dataset_name in dataset_names:
        print(f"\n{'='*60}")
        print(f"Dataset: {dataset_name}")
        print(f"{'='*60}")

        # Load dataset
        data = ds.Dataset.load(dataset_name)
        features, embedding = data.features, data.embedding

        ds_dir = os.path.join(output_dir, dataset_name)
        fig_dir = os.path.join(ds_dir, "figures")
        os.makedirs(fig_dir, exist_ok=True)

        # --- 1. Default run: region annotations + explanations ---
        print(f"  [defaults] generating region annotations...")
        default_ras = generate_region_annotations(features, embedding, defaults)

        # Save raw region annotations
        save_path = os.path.join(fig_dir, "defaults-regions.png")
        save_figure(default_ras, save_path)
        print(f"    saved {os.path.relpath(save_path, output_dir)}")

        # Save contrastive/descriptive explanations
        print(f"  [defaults] generating explanations...")
        explanations = make_explanations(
            default_ras,
            explanation_types,
            max_panels,
            contrastive_kwargs=contrastive_defaults,
            descriptive_kwargs=descriptive_defaults,
        )
        for etype, layout in explanations.items():
            save_path = os.path.join(fig_dir, f"defaults-{etype}.png")
            save_figure(layout, save_path)
            print(f"    saved {os.path.relpath(save_path, output_dir)}")

        # --- 2. Parameter variations: region annotations only ---
        for param_name, values in variations.items():
            for val in values:
                tag = param_tag(param_name, val)
                print(f"  [{tag}] generating region annotations...")

                # Build kwargs: start from defaults, override one parameter
                ra_kwargs = dict(defaults)
                ra_kwargs[param_name] = val

                try:
                    ras = generate_region_annotations(
                        features, embedding, ra_kwargs
                    )
                    save_path = os.path.join(fig_dir, f"{tag}-regions.png")
                    save_figure(ras, save_path)
                    print(f"    saved {os.path.relpath(save_path, output_dir)}")
                except Exception as exc:
                    print(f"    ERROR: {exc}")

        # --- 3. Explanation parameter variations ---
        if "contrastive" in explanation_types:
            for param_name, values in contrastive_variations.items():
                for val in values:
                    tag = explanation_tag("contrastive", param_name, val)
                    print(f"  [{tag}] generating explanation...")

                    kwargs = dict(contrastive_defaults)
                    kwargs[param_name] = val

                    try:
                        layout = vera.explain.contrastive(
                            default_ras,
                            max_panels=max_panels,
                            **kwargs,
                        )
                        save_path = os.path.join(fig_dir, f"{tag}.png")
                        save_figure(layout, save_path)
                        print(f"    saved {os.path.relpath(save_path, output_dir)}")
                    except Exception as exc:
                        print(f"    ERROR: {exc}")

        if "descriptive" in explanation_types:
            for param_name, values in descriptive_variations.items():
                for val in values:
                    tag = explanation_tag("descriptive", param_name, val)
                    print(f"  [{tag}] generating explanation...")

                    kwargs = dict(descriptive_defaults)
                    kwargs[param_name] = val

                    try:
                        layout = vera.explain.descriptive(
                            default_ras,
                            max_panels=max_panels,
                            **kwargs,
                        )
                        save_path = os.path.join(fig_dir, f"{tag}.png")
                        save_figure(layout, save_path)
                        print(f"    saved {os.path.relpath(save_path, output_dir)}")
                    except Exception as exc:
                        print(f"    ERROR: {exc}")

        # --- 4. Generate Markdown reports ---
        md = generate_region_construction_md(dataset_name, config)
        md_path = os.path.join(ds_dir, "region-construction.md")
        with open(md_path, "w") as md_file:
            md_file.write(md)
        print(f"  wrote {os.path.relpath(md_path, output_dir)}")

        md = generate_explanation_construction_md(dataset_name, config)
        md_path = os.path.join(ds_dir, "explanation-construction.md")
        with open(md_path, "w") as md_file:
            md_file.write(md)
        print(f"  wrote {os.path.relpath(md_path, output_dir)}")

    print(f"\nDone. Results in: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VERA parameter sensitivity study")
    parser.add_argument("config", help="Path to config.json")
    args = parser.parse_args()
    run(args.config)
