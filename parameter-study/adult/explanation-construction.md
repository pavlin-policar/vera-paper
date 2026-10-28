# Explanation Construction — adult

This page shows how explanation-construction parameters affect the final contrastive and descriptive explanations generated from the default region annotations.

## Default region-construction parameters

| Parameter | Default value |
|---|---|
| Number of bins | `5` |
| Contour level | `0.25` |
| Bandwidth scale factor | `1.0` |
| Merge overlap threshold | `0.8` |
| Sample size | `5000` |
| Random state | `0` |

## Contrastive defaults

| Parameter | Default value |
|---|---|
| Merge threshold | `0.95` |

![contrastive (defaults)](figures/defaults-contrastive.png)

## Contrastive: varying Merge threshold

Default value: `0.95`. All other contrastive parameters held at their defaults.

| Merge threshold | Explanation |
|---|---|
| `0.8` | ![](figures/contrastive-merge_threshold=0.8.png) |
| `0.9` | ![](figures/contrastive-merge_threshold=0.9.png) |
| `0.95` **(default)** | ![](figures/contrastive-merge_threshold=0.95.png) |
| `0.99` | ![](figures/contrastive-merge_threshold=0.99.png) |

## Descriptive defaults

| Parameter | Default value |
|---|---|
| Merge threshold | `0.8` |
| Enrich with background | `True` |
| Max overlap | `0.0` |

![descriptive (defaults)](figures/defaults-descriptive.png)

## Descriptive: varying Merge threshold

Default value: `0.8`. All other descriptive parameters held at their defaults.

| Merge threshold | Explanation |
|---|---|
| `0.5` | ![](figures/descriptive-merge_threshold=0.5.png) |
| `0.7` | ![](figures/descriptive-merge_threshold=0.7.png) |
| `0.8` **(default)** | ![](figures/descriptive-merge_threshold=0.8.png) |
| `0.9` | ![](figures/descriptive-merge_threshold=0.9.png) |
| `0.95` | ![](figures/descriptive-merge_threshold=0.95.png) |

## Descriptive: varying Enrich with background

Default value: `True`. All other descriptive parameters held at their defaults.

| Enrich with background | Explanation |
|---|---|
| `True` **(default)** | ![](figures/descriptive-enrich_with_background=True.png) |
| `False` | ![](figures/descriptive-enrich_with_background=False.png) |

## Descriptive: varying Max overlap

Default value: `0.0`. All other descriptive parameters held at their defaults.

| Max overlap | Explanation |
|---|---|
| `0.0` **(default)** | ![](figures/descriptive-max_overlap=0.0.png) |
| `0.1` | ![](figures/descriptive-max_overlap=0.1.png) |
| `0.25` | ![](figures/descriptive-max_overlap=0.25.png) |
