# Parameter Sensitivity Study

This directory contains the parameter sensitivity analysis for VERA, prepared as supplementary material for our paper.

The purpose of this supplement is to document how VERA's core region-construction parameters affect the extracted annotations and how key explanation-construction parameters affect the final contrastive and descriptive layouts. For each dataset, we provide:

- a `region-construction.md` page showing the full parameter sweep
- an `explanation-construction.md` page showing the effect of selected explanation-construction parameters on the final contrastive and descriptive explanations

## Datasets


| Dataset            | Region construction sweep                                      | Explanation construction sweep                               |
| ------------------ | -------------------------------------------------------------- | ------------------------------------------------------------ |
| Iris               | [region-construction](iris/region-construction.md)             | [explanations](iris/explanation-construction.md)             |
| Penguins           | [region-construction](penguins/region-construction.md)         | [explanations](penguins/explanation-construction.md)         |
| Abalone            | [region-construction](abalone/region-construction.md)          | [explanations](abalone/explanation-construction.md)          |
| Titanic            | [region-construction](titanic/region-construction.md)          | [explanations](titanic/explanation-construction.md)          |
| Employee Attrition | [region-construction](attrition/region-construction.md)        | [explanations](attrition/explanation-construction.md)        |
| Wine Quality       | [region-construction](wine_quality/region-construction.md)     | [explanations](wine_quality/explanation-construction.md)     |
| Adult              | [region-construction](adult/region-construction.md)            | [explanations](adult/explanation-construction.md)            |
| Forest Covertype   | [region-construction](forest_covertype/region-construction.md) | [explanations](forest_covertype/explanation-construction.md) |


## Structure

```text
parameter-study/
├── config.json                  # Parameter ranges and dataset list
├── run_parameter_study.py       # Main script
├── README.md
├── iris/                        # One directory per dataset
│   ├── region-construction.md
│   ├── explanation-construction.md
│   └── figures/
├── penguins/
├── abalone/
├── titanic/
├── attrition/
├── wine_quality/
├── adult/
└── forest_covertype/
```

## Parameters varied

Each parameter is varied independently while all others are held at their defaults.

### Region construction


| Parameter                     | Default | Values tested            |
| ----------------------------- | ------- | ------------------------ |
| Number of discretization bins | 5       | 3, 5, 10                 |
| KDE contour level             | 0.25    | 0.10, 0.25, 0.50         |
| Bandwidth scale factor        | 1.0     | 0.5, 1, 2                |
| Merge overlap threshold       | 0.8     | 0.5, 0.7, 0.8, 0.9, 0.95 |
| Sample size                   | 5000    | fixed                    |
| Random state                  | 0       | fixed                    |


### Explanation construction

**Contrastive explanations**


| Parameter       | Default | Values tested        |
| --------------- | ------- | -------------------- |
| Merge threshold | 0.95    | 0.8, 0.9, 0.95, 0.99 |


**Descriptive explanations**


| Parameter              | Default | Values tested            |
| ---------------------- | ------- | ------------------------ |
| Merge threshold        | 0.8     | 0.5, 0.7, 0.8, 0.9, 0.95 |
| Enrich with background | `True`  | `True`, `False`          |
| Max overlap            | 0.0     | 0.0, 0.1, 0.25           |


## What to look for

**Important:** Different parameter settings can yield a different number of region annotations across variables. During region construction, VERA merges spatially overlapping sub-regions belonging to the same feature. If, after merging, a feature's sub-regions collapse into a single region, that feature is filtered out — a single region covering the entire embedding is not informative, since it does not distinguish any spatial structure. This means that more aggressive merging (e.g., a low merge overlap threshold) tends to reduce the number of annotated features, because more sub-regions are consolidated and more features end up with only one surviving region. Conversely, less aggressive merging preserves finer distinctions and retains more features. Keep this in mind when comparing outputs across parameter settings: changes in the *number* of annotated features are just as telling as changes in region shape or size.

### Number of discretization bins

This parameter controls how continuous (numeric) features are discretized before region construction. Setting the number of bins to 3, for example, means each continuous feature is split into at most 3 intervals, each of which becomes a candidate region. Note that this only applies to continuous features — categorical features are unaffected and may still produce more regions than the bin count.

In practice, the post-hoc merging step often absorbs much of the difference between bin counts. When samples from adjacent bins occupy the same area of the embedding, their regions are merged into a single annotation. As a result, the final explanations are frequently identical or very similar across different bin settings, particularly for features with smooth spatial distributions. The main effect of increasing the bin count is finer granularity in the region boundaries; decreasing it produces coarser, broader regions.

### KDE contour level

The contour level determines the minimum density threshold at which a region boundary is drawn. At lower contour levels (e.g., 0.10), regions extend further from the dense core of the point distribution, producing larger regions with more padding around the points. At higher contour levels (e.g., 0.50), only the densest parts of the embedding are enclosed, resulting in smaller, more tightly fitting, and often more disjoint regions that cover fewer points.

### Bandwidth scale factor

The bandwidth scale factor controls the width of the Gaussian kernels placed on each data point during density estimation. Unlike the contour level, which determines *where* to draw the boundary given a density surface, the bandwidth controls *how smooth* the density surface is in the first place. A smaller scale factor (e.g., 0.5) places narrow Gaussians on each point, producing a rougher density surface with many small, disjoint, and numerous regions. A larger scale factor (e.g., 2.0) uses wider Gaussians, yielding a smoother surface where regions are larger, more connected, and encompass more points.

### Merge overlap threshold

The merge overlap threshold governs the post-hoc merging step, in which region annotations from the same feature that spatially overlap are consolidated into a single annotation. A lower threshold (e.g., 0.5) means regions need only moderate overlap to be merged, resulting in more aggressive consolidation — separate but nearby regions are more readily combined, producing fewer, larger annotations. A higher threshold (e.g., 0.95) requires near-perfect overlap before merging, preserving finer spatial distinctions and producing more, smaller annotations. When the threshold is high, subtle differences in the spatial distribution of adjacent bins or categories are retained; when it is low, only clearly separated regions remain distinct.

This parameter has a particularly strong effect on how many features survive filtering. Because a lower threshold merges sub-regions more readily, more features end up with all their sub-regions merged into a single region, and single-region features are filtered out as uninformative. Raising the threshold makes merging more conservative, keeping more sub-regions distinct and thereby retaining more features in the final output. When reviewing the results, pay attention not only to how region boundaries change but also to how many features appear (or disappear) as the threshold varies.

## Practical guidance

The figures in this supplement are intended to support qualitative parameter selection rather than prescribe a single optimal setting for all datasets. In our experience, the defaults used in the paper are a good starting point, and the main parameters can be adjusted as follows:

- For datasets with more than `5000` samples, the study uses a fixed random sample of `5000` points (`random_state=0`) before region construction. This keeps the study tractable and reproducible while preserving the overall spatial structure of the embedding.
- Start with the defaults and change one parameter at a time. Across the datasets in this supplement, the default settings generally preserve the main explanatory structure while avoiding overly coarse or overly fragmented results.
- Use `5` discretization bins as a balanced default for numeric features. Fewer bins (e.g., `3`) produce coarser summaries, while more bins (e.g., `10`) preserve finer gradients but can introduce additional small regions before post-hoc merging.
- Use a contour level of `0.25` as a middle ground between padded and overly tight regions. Lower values (e.g., `0.10`) produce larger regions with more padding around points, while higher values (e.g., `0.50`) restrict regions to dense cores and can fragment them.
- Treat the bandwidth scale factor as the main smoothness control. Smaller values (e.g., `0.5`) produce many fine-grained, disjoint regions, whereas larger values (e.g., `2.0`) smooth over local structure and can merge distinct areas into broad annotations.
- Use the region-construction merge overlap threshold to control consolidation. Lower values merge more aggressively and often reduce the number of surviving features, while higher values preserve finer distinctions at the cost of more visual complexity. The default value `0.8` is a reasonable compromise.
- Use a high contrastive merge threshold when you want to merge only very closely aligned features. In our examples, `0.95` works as a conservative default that preserves the intended meaning of merged contrastive explanations.
- For descriptive explanations, enabling background enrichment produces richer but longer labels; disabling it produces shorter, more conservative descriptions. This is therefore a specificity-versus-conciseness tradeoff rather than a strict quality improvement.
- Keep descriptive `max_overlap` low when readability is the priority. Allowing larger overlap can increase coverage, but it also makes the resulting panels harder to parse visually.

## Running the study

Set up the environment and download the datasets as described in the repository-level `README.md`, then from this directory run:

```bash
python run_parameter_study.py config.json
```

Results are written to per-dataset directories. Each directory contains:
- `region-construction.md` — raw region annotations under varying parameters
- `explanation-construction.md` — contrastive and descriptive explanations under varying explanation parameters
- `figures/` — all generated images

## Modifying the study

Edit `config.json` to add/remove datasets or change parameter ranges. The script will regenerate all outputs on the next run.
