"""
Compare default VERA outputs with purity indication disabled and enabled.

For each dataset, this script generates:
  - README.md
  - figures/regular-regions.png
  - figures/indicate-purity-regions.png
  - figures/regular-contrastive.png
  - figures/indicate-purity-contrastive.png
  - figures/regular-descriptive.png
  - figures/indicate-purity-descriptive.png

The underlying region annotations and explanations are identical across the two
variants; only plotting changes via the `indicate_purity` flag.
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


DATASET_LABELS = {
    "iris": "Iris",
    "penguins": "Penguins",
    "abalone": "Abalone",
    "titanic": "Titanic",
    "attrition": "Employee Attrition",
    "wine_quality": "Wine Quality",
    "adult": "Adult",
    "forest_covertype": "Forest Covertype",
}

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
    return vera.an.generate_region_annotations(features, embedding, **ra_kwargs)


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
    indicate_purity: bool,
    per_row: int = 4,
    figwidth: float = 16,
):
    variable_colors = vera.pl.layout_variable_colors(layout)
    fig, ax = vera.pl.plot_annotations(
        layout,
        per_row=per_row,
        figwidth=figwidth,
        return_ax=True,
        indicate_purity=indicate_purity,
        indicate_membership=True,
        variable_colors=variable_colors,
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
        f"Dataset size: `{num_samples}` samples. The comparison uses the same "
        f"fixed random sample of `{sample_size}` points (`random_state={random_state}`) "
        "for both plotting variants, so the underlying annotations and "
        "explanations remain directly comparable."
    )


def generate_dataset_readme(
    dataset_name: str,
    config: dict,
    num_samples: int,
    fig_dir_name: str = "figures",
) -> str:
    defaults = config["defaults"]
    contrastive_defaults = config.get("contrastive_defaults", {})
    descriptive_defaults = config.get("descriptive_defaults", {})
    variants = config["plot_variants"]
    explanation_types = config.get("explanation_types", ["contrastive", "descriptive"])
    dataset_label = DATASET_LABELS.get(dataset_name, dataset_name)

    purity_variant = next(variant for variant in variants if variant["indicate_purity"])
    regular_variant = next(variant for variant in variants if not variant["indicate_purity"])

    lines = [
        f"# Purity Indication Comparison — {dataset_label}",
        "",
        "This page compares the default final VERA outputs with opacity-based "
        "purity indication disabled and enabled. The extracted regions and the "
        "constructed explanations are the same in both columns; only the "
        "rendering changes through the `indicate_purity` plotting flag.",
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

    lines.extend(
        [
            "",
            "## Region annotations",
            "",
            f"### {purity_variant['label']} (`indicate_purity=True`)",
            "",
            f"![]({fig_dir_name}/{purity_variant['tag']}-regions.png)",
            "",
            f"### {regular_variant['label']} (`indicate_purity=False`)",
            "",
            f"![]({fig_dir_name}/{regular_variant['tag']}-regions.png)",
            "",
        ]
    )

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
                f"### {purity_variant['label']} (`indicate_purity=True`)",
                "",
                f"![]({fig_dir_name}/{purity_variant['tag']}-contrastive.png)",
                "",
                f"### {regular_variant['label']} (`indicate_purity=False`)",
                "",
                f"![]({fig_dir_name}/{regular_variant['tag']}-contrastive.png)",
                "",
            ]
        )

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
                f"### {purity_variant['label']} (`indicate_purity=True`)",
                "",
                f"![]({fig_dir_name}/{purity_variant['tag']}-descriptive.png)",
                "",
                f"### {regular_variant['label']} (`indicate_purity=False`)",
                "",
                f"![]({fig_dir_name}/{regular_variant['tag']}-descriptive.png)",
                "",
            ]
        )

    return "\n".join(lines)


def generate_top_level_readme(config: dict) -> str:
    lines = [
        "# Purity Indication Comparison",
        "",
        "This directory compares the default final VERA outputs with the "
        "`indicate_purity` plotting flag disabled and enabled.",
        "",
        "For each dataset, we provide one `README.md` page that shows stacked "
        "comparisons of:",
        "",
        "- region annotations",
        "- contrastive explanations",
        "- descriptive explanations",
        "",
        "## Datasets",
        "",
        "| Dataset | Comparison page |",
        "|---|---|",
    ]

    for dataset_name in config["datasets"]:
        dataset_label = DATASET_LABELS.get(dataset_name, dataset_name)
        lines.append(f"| {dataset_label} | [comparison]({dataset_name}/README.md) |")

    lines.extend(
        [
            "",
            "## Structure",
            "",
            "```text",
            "purity-indication-comparison/",
            "├── config.json",
            "├── run_purity_indication_comparison.py",
            "├── README.md",
            "├── iris/",
            "│   ├── README.md",
            "│   └── figures/",
            "├── penguins/",
            "├── abalone/",
            "├── titanic/",
            "├── attrition/",
            "├── wine_quality/",
            "├── adult/",
            "└── forest_covertype/",
            "```",
            "",
            "## Running the comparison",
            "",
            "Set up the environment and download the datasets as described in the "
            "repository-level `README.md`, then from this directory run:",
            "",
            "```bash",
            "python run_purity_indication_comparison.py config.json",
            "```",
            "",
            "## Modifying the comparison",
            "",
            "Edit `config.json` to add or remove datasets or adjust the shared "
            "VERA defaults. The script will regenerate all per-dataset pages and figures.",
        ]
    )

    return "\n".join(lines)


def run(config_path: str):
    with open(config_path) as f:
        config = json.load(f)

    output_dir = os.path.dirname(os.path.abspath(config_path))
    dataset_names = config["datasets"]
    variants = config["plot_variants"]
    defaults = config["defaults"]
    contrastive_defaults = config.get("contrastive_defaults", {})
    descriptive_defaults = config.get("descriptive_defaults", {})
    explanation_types = config.get("explanation_types", ["contrastive", "descriptive"])
    max_panels = config.get("max_panels", 4)

    top_level_readme = generate_top_level_readme(config)
    top_level_readme_path = os.path.join(output_dir, "README.md")
    with open(top_level_readme_path, "w") as readme_file:
        readme_file.write(top_level_readme)
    print(f"wrote {os.path.relpath(top_level_readme_path, output_dir)}")

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

        print("  generating region annotations...")
        region_annotations = generate_region_annotations(features, embedding, defaults)

        print("  generating explanations...")
        explanations = make_explanations(
            region_annotations,
            explanation_types,
            max_panels,
            contrastive_kwargs=contrastive_defaults,
            descriptive_kwargs=descriptive_defaults,
        )

        print("  saving figures...")
        for variant in variants:
            region_save_path = os.path.join(fig_dir, f"{variant['tag']}-regions.png")
            save_figure(
                region_annotations,
                region_save_path,
                indicate_purity=variant["indicate_purity"],
            )
            print(f"    saved {os.path.relpath(region_save_path, output_dir)}")

            for explanation_type, layout in explanations.items():
                save_path = os.path.join(fig_dir, f"{variant['tag']}-{explanation_type}.png")
                save_figure(
                    layout,
                    save_path,
                    indicate_purity=variant["indicate_purity"],
                )
                print(f"    saved {os.path.relpath(save_path, output_dir)}")

        readme = generate_dataset_readme(dataset_name, config, num_samples)
        readme_path = os.path.join(ds_dir, "README.md")
        with open(readme_path, "w") as readme_file:
            readme_file.write(readme)
        print(f"  wrote {os.path.relpath(readme_path, output_dir)}")

    print(f"\nDone. Results in: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VERA purity indication comparison")
    parser.add_argument("config", help="Path to config.json")
    args = parser.parse_args()
    run(args.config)
