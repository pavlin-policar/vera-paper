# VERA: Paper Source and Supplementary Material

![VERA banner](readme-banner.png)

This repository contains the LaTeX source and supplementary material for the paper **"VERA: Generating Visual Explanations of Two-Dimensional Embeddings via Region Annotation."** It accompanies the open-source Python implementation of VERA in the [`vera`](https://github.com/pavlin-policar/vera) repository.

## Overview

VERA is a method for automatically generating static visual explanations of two-dimensional embeddings produced by techniques such as t-SNE and UMAP. Instead of requiring analysts to manually inspect clusters, transitions, and outliers one feature at a time, VERA identifies informative regions in the embedding and links them to human-interpretable feature values.

The goal is to provide a fast, high-level summary of what an embedding shows. VERA produces both contrastive explanations, which show how feature values vary across the embedding space, and descriptive explanations, which characterize individual regions. In the paper, we show that these generated explanations can support common embedding-interpretation tasks with comparable accuracy to an interactive analysis workflow while requiring substantially less user effort.

## Repository contents

```text
tvcg-embedding-annotation/
├── 2026-tvcg-resubmission-2/      # Current manuscript, response to reviewers, and supplement, with every figure they include
├── 2026-tvcg-resubmission-1/      # Previous revision (frozen)
├── figure_scripts/                # Scripts that render the manuscript's and the supplement's figures
├── supplement-data/               # Shared datasets, their downloader, and the figure style
├── parameter-study/               # Full parameter sensitivity study
├── region-method-comparison/      # KDE regions against rangeset regions, for every dataset
├── purity-indication-comparison/  # Purity-based visual emphasis, for every dataset
├── bookworm/                      # Synthetic book-purchase example data
├── orange-workflow-examples/      # Orange workflows and screenshots
└── user-study/                    # User-study materials
```

The manuscript and the supplementary document (`supplementary-material.tex`) live in `2026-tvcg-resubmission-2/`, together with every figure they include. `figure_scripts/` renders those figures. The remaining directories hold the full studies the supplement summarizes, the user-study materials, and the Orange workflows.

## User study

The complete user-study materials, in the form participants saw them, are in [`user-study/`](user-study/): the tool introductions, the six quizzes with the VERA explanations shown for each data set, the tool surveys, and the final comparative survey. Its README describes the study design and the order in which each group saw the materials.

## Setup

From the repository root, create an environment and install the dependencies, which include VERA 1.2.0 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The single-cell data of supplement Fig. S4 additionally needs `scanpy`.

Then download the eight shared datasets (Iris, Penguins, Abalone, Titanic, Employee Attrition, Wine Quality, Adult, Forest Covertype):

```bash
python supplement-data/download_data.py
```

## Reproduce the figures

`figure_scripts/README.md` lists every figure of the manuscript and the supplement with the script and command that render it and the data it needs. The scripts write PDF and PNG files to `figure_scripts/figures/` (only the PNGs are tracked), and a re-rendered PDF is copied into the paper folder under the same name. The football and single-cell data are built by `figure_scripts/prepare_football.py` and `figure_scripts/prepare_single_cell.py`. Figures are drawn in the manuscript's style (`supplement-data/figstyle.py`), at the width at which the paper includes them.

## Run the full studies

The supplement shows selected results of these studies on one or two datasets; each study covers the eight shared datasets.

```bash
python parameter-study/run_parameter_study.py parameter-study/config.json
python parameter-study/summarize_parameter_study.py parameter-study/config.json
python region-method-comparison/run_region_method_comparison.py region-method-comparison/config.json
python purity-indication-comparison/run_purity_indication_comparison.py purity-indication-comparison/config.json
```

Each study writes one report per dataset; the study READMEs describe the outputs:

- `parameter-study/README.md`
- `region-method-comparison/README.md`
- `purity-indication-comparison/README.md`
- `supplement-data/README.md`
- `user-study/README.md`
- `orange-workflow-examples/README.md`
