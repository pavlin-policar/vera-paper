"""
Compare KDE- and rangeset-based region construction across datasets.

For each dataset, this script generates:
  - region-construction.md
  - explanation-construction.md

Each page compares the outputs obtained with the two region-construction
backends while keeping the remaining VERA pipeline fixed.
"""

import argparse
import json
import os
from importlib.util import module_from_spec, spec_from_file_location

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import vera  # noqa: E402
import vera.explain  # noqa: E402


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

METHOD_LABELS = {
    "kde": "KDE",
    "rangeset": "Rangeset",
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
    return vera.an.generate_region_annotations(features, embedding, **ra_kwargs)


def filter_uninformative_region_annotations(layout: list[list]) -> list[list]:
    """Drop feature groups that collapse to a single extracted region."""
    return [region_annotations for region_annotations in layout if len(region_annotations) > 1]


def _annotation_group_sort_key(region_annotations: list) -> tuple:
    """Create a stable sort key for one feature's extracted regions."""
    contained_variable_names = sorted(
        {
            variable.name
            for region_annotation in region_annotations
            for variable in region_annotation.descriptor.contained_variables
        }
    )
    descriptor_labels = tuple(str(region_annotation.descriptor) for region_annotation in region_annotations)

    return tuple(contained_variable_names), descriptor_labels


def order_region_annotation_layout(layout: list[list]) -> list[list]:
    """Sort features and their regions for method-independent figure ordering."""
    normalized_layout = [sorted(region_annotations) for region_annotations in layout]
    return sorted(normalized_layout, key=_annotation_group_sort_key)


def make_explanations(
    region_annotations,
    explanation_types: list[str],
    max_panels: int,
    contrastive_kwargs: dict | None = None,
    descriptive_kwargs: dict | None = None,
) -> dict[str, list]:
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


def sampling_note(num_samples: int, defaults: dict) -> str:
    sample_size = defaults.get("sample_size")
    random_state = defaults.get("random_state")

    if sample_size is None or num_samples <= sample_size:
        return (
            f"Dataset size: `{num_samples}` samples. "
            "Sampling was not required for this dataset."
        )

    return (
        f"Dataset size: `{num_samples}` samples. Because rangesets can be slow "
        f"on larger datasets, both region-construction backends are evaluated on "
        f"the same fixed random sample of `{sample_size}` points "
        f"(`random_state={random_state}`). As a result, extracted regions may "
        "not cover every point in the full dataset."
    )


def generate_region_construction_md(
    dataset_name: str,
    config: dict,
    num_samples: int,
    fig_dir_name: str = "figures",
) -> str:
    defaults = config["defaults"]
    methods = config["methods"]

    lines = [
        f"# Region Construction Comparison — {dataset_name}",
        "",
        "This page compares the raw region annotations produced by the two "
        "region-construction backends while keeping the remaining VERA settings "
        "fixed.",
        "",
        sampling_note(num_samples, defaults),
        "",
        "## Default parameters",
        "",
        "| Parameter | Value |",
        "|---|---|",
    ]
    for param, val in defaults.items():
        lines.append(f"| {REGION_PARAM_LABELS.get(param, param)} | `{val}` |")
    lines.extend(
        [
            "",
            "## Region annotations",
            "",
            "| Method | Region annotations |",
            "|---|---|",
        ]
    )
    for method in methods:
        lines.append(
            f"| {METHOD_LABELS.get(method, method)} "
            f"| ![]({fig_dir_name}/{method}-regions.png) |"
        )
    lines.append("")

    return "\n".join(lines)


def generate_explanation_construction_md(
    dataset_name: str,
    config: dict,
    num_samples: int,
    fig_dir_name: str = "figures",
) -> str:
    defaults = config["defaults"]
    methods = config["methods"]
    contrastive_defaults = config.get("contrastive_defaults", {})
    descriptive_defaults = config.get("descriptive_defaults", {})
    explanation_types = config.get("explanation_types", ["contrastive", "descriptive"])

    lines = [
        f"# Explanation Construction Comparison — {dataset_name}",
        "",
        "This page compares the final contrastive and descriptive explanations "
        "obtained from different region-construction backends while keeping the "
        "remaining explanation settings fixed.",
        "",
        sampling_note(num_samples, defaults),
        "",
        "## Default region-construction parameters",
        "",
        "| Parameter | Value |",
        "|---|---|",
    ]
    for param, val in defaults.items():
        lines.append(f"| {REGION_PARAM_LABELS.get(param, param)} | `{val}` |")
    lines.append("")

    if "contrastive" in explanation_types:
        lines.extend(
            [
                "## Contrastive defaults",
                "",
                "| Parameter | Value |",
                "|---|---|",
            ]
        )
        for param, val in contrastive_defaults.items():
            lines.append(
                f"| {EXPLANATION_PARAM_LABELS.get(param, param)} | `{val}` |"
            )
        lines.extend(
            [
                "",
                "## Contrastive explanations",
                "",
                "| Method | Explanation |",
                "|---|---|",
            ]
        )
        for method in methods:
            lines.append(
                f"| {METHOD_LABELS.get(method, method)} "
                f"| ![]({fig_dir_name}/{method}-contrastive.png) |"
            )
        lines.append("")

    if "descriptive" in explanation_types:
        lines.extend(
            [
                "## Descriptive defaults",
                "",
                "| Parameter | Value |",
                "|---|---|",
            ]
        )
        for param, val in descriptive_defaults.items():
            lines.append(
                f"| {EXPLANATION_PARAM_LABELS.get(param, param)} | `{val}` |"
            )
        lines.extend(
            [
                "",
                "## Descriptive explanations",
                "",
                "| Method | Explanation |",
                "|---|---|",
            ]
        )
        for method in methods:
            lines.append(
                f"| {METHOD_LABELS.get(method, method)} "
                f"| ![]({fig_dir_name}/{method}-descriptive.png) |"
            )
        lines.append("")

    return "\n".join(lines)


def run(config_path: str):
    with open(config_path) as f:
        config = json.load(f)

    output_dir = os.path.dirname(os.path.abspath(config_path))
    dataset_names = config["datasets"]
    methods = config["methods"]
    defaults = config["defaults"]
    contrastive_defaults = config.get("contrastive_defaults", {})
    descriptive_defaults = config.get("descriptive_defaults", {})
    explanation_types = config.get("explanation_types", ["contrastive", "descriptive"])
    max_panels = config.get("max_panels", 4)

    for dataset_name in dataset_names:
        print(f"\n{'=' * 60}")
        print(f"Dataset: {dataset_name}")
        print(f"{'=' * 60}")

        data = ds.Dataset.load(dataset_name)
        features, embedding = data.features, data.embedding
        num_samples = features.shape[0]

        ds_dir = os.path.join(output_dir, dataset_name)
        fig_dir = os.path.join(ds_dir, "figures")
        os.makedirs(fig_dir, exist_ok=True)

        for method in methods:
            print(f"  [{method}] generating region annotations...")
            ra_kwargs = dict(defaults)
            ra_kwargs["region_method"] = method
            ra_kwargs["filter_uninformative"] = False
            region_annotations = generate_region_annotations(features, embedding, ra_kwargs)
            ordered_region_annotations = order_region_annotation_layout(region_annotations)
            filtered_region_annotations = filter_uninformative_region_annotations(
                region_annotations
            )

            save_path = os.path.join(fig_dir, f"{method}-regions.png")
            save_figure(ordered_region_annotations, save_path)
            print(f"    saved {os.path.relpath(save_path, output_dir)}")

            print(f"  [{method}] generating explanations...")
            explanations = make_explanations(
                filtered_region_annotations,
                explanation_types,
                max_panels,
                contrastive_kwargs=contrastive_defaults,
                descriptive_kwargs=descriptive_defaults,
            )
            for explanation_type, layout in explanations.items():
                save_path = os.path.join(fig_dir, f"{method}-{explanation_type}.png")
                save_figure(layout, save_path)
                print(f"    saved {os.path.relpath(save_path, output_dir)}")

        md = generate_region_construction_md(dataset_name, config, num_samples)
        md_path = os.path.join(ds_dir, "region-construction.md")
        with open(md_path, "w") as md_file:
            md_file.write(md)
        print(f"  wrote {os.path.relpath(md_path, output_dir)}")

        md = generate_explanation_construction_md(dataset_name, config, num_samples)
        md_path = os.path.join(ds_dir, "explanation-construction.md")
        with open(md_path, "w") as md_file:
            md_file.write(md)
        print(f"  wrote {os.path.relpath(md_path, output_dir)}")

    print(f"\nDone. Results in: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VERA region-method comparison")
    parser.add_argument("config", help="Path to config.json")
    args = parser.parse_args()
    run(args.config)
