# Supplement Data

This directory contains the datasets used by the supplementary studies in this repository.

The downloaded directory structure is:

```text
supplement-data/
├── data/
│   └── <dataset>/
│       ├── embedding.csv
│       ├── embedding_<variant>.csv   (built datasets only)
│       ├── features.csv
│       └── metadata.json
├── datasets.json
├── datasets.py
├── download_data.py
└── figstyle.py
```

## Datasets

The directory contains the eight datasets used in the experiments included in this repository:

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

## Football players

`figure_scripts/prepare_football.py` builds the football dataset of the manuscript's comparison figure (Fig. 2) and of the supplement's football explanations (Fig. S3): 1,634 players of the 2017-18 season of the five major European leagues with at least 900 minutes, described by 238 per-90-minute counts, shares, and success rates aggregated from the Wyscout soccer-logs (Pappalardo et al., 2019, CC BY 4.0) and by their playing position. The raw files are downloaded to `data/raw/` on first use. Position is among the features but is left out of the embedding input. The dataset is embedded with t-SNE (rotated clockwise by 5 degrees; `embedding.csv`) and UMAP at their libraries' default settings; the embeddings are stored as `embedding_<variant>.csv` and read with `Dataset.load(name, embedding=<variant>)`.

```bash
python ../figure_scripts/prepare_football.py
```
