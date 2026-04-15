# Supplement Data

This directory contains the datasets used by the supplementary studies in this repository.

The downloaded directory structure is:

```text
supplement-data/
├── data/
│   └── <dataset>/
│       ├── embedding.csv
│       ├── features.csv
│       └── metadata.json
├── datasets.json
├── datasets.py
└── download_data.py
```

## Datasets

The directory contains the eight datasets used by both the parameter sensitivity study and the region-method comparison:

- Iris
- Penguins
- Abalone
- Titanic
- Employee Attrition
- Wine Quality
- Adult
- Forest Covertype

## Download the data

Run:

```bash
python download_data.py
```
