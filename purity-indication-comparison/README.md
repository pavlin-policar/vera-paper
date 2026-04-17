# Purity Indication Comparison

This directory compares the default final VERA outputs with the `indicate_purity` plotting flag disabled and enabled.

For each dataset, we provide one `README.md` page that shows stacked comparisons of:

- region annotations
- contrastive explanations
- descriptive explanations

## Datasets

| Dataset | Comparison page |
|---|---|
| Iris | [comparison](iris/README.md) |
| Penguins | [comparison](penguins/README.md) |
| Abalone | [comparison](abalone/README.md) |
| Titanic | [comparison](titanic/README.md) |
| Employee Attrition | [comparison](attrition/README.md) |
| Wine Quality | [comparison](wine_quality/README.md) |
| Adult | [comparison](adult/README.md) |
| Forest Covertype | [comparison](forest_covertype/README.md) |

## Structure

```text
purity-indication-comparison/
├── config.json
├── run_purity_indication_comparison.py
├── README.md
├── iris/
│   ├── README.md
│   └── figures/
├── penguins/
├── abalone/
├── titanic/
├── attrition/
├── wine_quality/
├── adult/
└── forest_covertype/
```

## Running the comparison

Set up the environment and download the datasets as described in the repository-level `README.md`, then from this directory run:

```bash
python run_purity_indication_comparison.py config.json
```

## Modifying the comparison

Edit `config.json` to add or remove datasets or adjust the shared VERA defaults. The script will regenerate all per-dataset pages and figures.