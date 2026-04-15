# Region Method Comparison

This directory compares two alternative region-construction backends in VERA:

- `kde`: the KDE-contour approach used in the paper
- `rangeset`: the triangulation-based rangeset variant inspired by Sohns et al.

For each of the eight datasets used in the supplementary parameter study, we provide:

- a `region-construction.md` page comparing the raw region annotations obtained with the two methods
- an `explanation-construction.md` page comparing the resulting contrastive and descriptive explanations when the downstream VERA pipeline is kept fixed

## Datasets


| Dataset            | Region construction comparison                                 | Explanation comparison                                       |
| ------------------ | -------------------------------------------------------------- | ------------------------------------------------------------ |
| Iris               | [region-construction](iris/region-construction.md)             | [explanations](iris/explanation-construction.md)             |
| Penguins           | [region-construction](penguins/region-construction.md)         | [explanations](penguins/explanation-construction.md)         |
| Abalone            | [region-construction](abalone/region-construction.md)          | [explanations](abalone/explanation-construction.md)          |
| Titanic            | [region-construction](titanic/region-construction.md)          | [explanations](titanic/explanation-construction.md)          |
| Employee Attrition | [region-construction](attrition/region-construction.md)        | [explanations](attrition/explanation-construction.md)        |
| Wine Quality       | [region-construction](wine_quality/region-construction.md)     | [explanations](wine_quality/explanation-construction.md)     |
| Adult              | [region-construction](adult/region-construction.md)            | [explanations](adult/explanation-construction.md)            |
| Forest Covertype   | [region-construction](forest_covertype/region-construction.md) | [explanations](forest_covertype/explanation-construction.md) |


## Sampling note

Rangesets can be comparatively slow on large datasets. To keep the comparison tractable, the comparison uses the same fixed random sample of `5000` points (`random_state=0`) for both backends whenever a dataset contains more than `5000` samples.

This means that, on larger datasets, the extracted regions are based on a representative subset rather than the full point set and may therefore not cover every point in the full embedding.

## Structure

```text
region-method-comparison/
├── config.json                      # Datasets and shared comparison settings
├── run_region_method_comparison.py  # Main script
├── README.md
├── iris/                            # One directory per dataset
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

## Running the study

Set up the environment and download the datasets as described in the repository-level `README.md`, then from this directory run:

```bash
python run_region_method_comparison.py config.json
```

## Modifying the study

Edit `config.json` to add/remove datasets or change parameter ranges. The script will regenerate all outputs on the next run.
