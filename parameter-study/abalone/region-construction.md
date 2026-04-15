# Region Construction — abalone

This page shows how the region construction parameters affect the extracted region annotations. Each figure shows the raw region annotations for all features — one panel per feature (or feature group after post-hoc merging).

## Default parameters

| Parameter | Default value |
|---|---|
| Number of bins | `5` |
| Contour level | `0.25` |
| Bandwidth scale factor | `1.0` |
| Merge overlap threshold | `0.8` |

## Default region annotations

![region annotations (defaults)](figures/defaults-regions.png)

## Varying: Number of bins

Default value: `5`. All other parameters held at their defaults.

| Number of bins | Region annotations |
|---|---|
| `3` | ![](figures/n_discretization_bins=3-regions.png) |
| `5` **(default)** | ![](figures/n_discretization_bins=5-regions.png) |
| `10` | ![](figures/n_discretization_bins=10-regions.png) |

## Varying: Contour level

Default value: `0.25`. All other parameters held at their defaults.

| Contour level | Region annotations |
|---|---|
| `0.1` | ![](figures/contour_level=0.1-regions.png) |
| `0.25` **(default)** | ![](figures/contour_level=0.25-regions.png) |
| `0.5` | ![](figures/contour_level=0.5-regions.png) |

## Varying: Bandwidth scale factor

Default value: `1.0`. All other parameters held at their defaults.

| Bandwidth scale factor | Region annotations |
|---|---|
| `0.5` | ![](figures/scale_factor=0.5-regions.png) |
| `1` **(default)** | ![](figures/scale_factor=1-regions.png) |
| `2` | ![](figures/scale_factor=2-regions.png) |

## Varying: Merge overlap threshold

Default value: `0.8`. All other parameters held at their defaults.

| Merge overlap threshold | Region annotations |
|---|---|
| `0.5` | ![](figures/merge_min_sample_overlap=0.5-regions.png) |
| `0.7` | ![](figures/merge_min_sample_overlap=0.7-regions.png) |
| `0.8` **(default)** | ![](figures/merge_min_sample_overlap=0.8-regions.png) |
| `0.9` | ![](figures/merge_min_sample_overlap=0.9-regions.png) |
| `0.95` | ![](figures/merge_min_sample_overlap=0.95-regions.png) |
