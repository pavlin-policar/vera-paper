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
│   ├── fig*.py                    # One script per figure or group of figures
│   ├── prepare_football.py        # Builds the football data (Fig. 2, Fig. S3)
│   ├── prepare_single_cell.py     # Downloads and embeds the single-cell data (Fig. S4)
│   ├── run_benchmarks.py          # Reruns the runtime benchmarks (Fig. 12)
│   ├── related_methods/           # Reimplemented related methods of Fig. 2
│   ├── data/benchmarks/           # Runtime benchmark results
│   └── figures/                   # Rendered figures (PNG)
├── supplement-data/               # Downloader of the shared datasets, and the figure style
├── parameter-study/               # Full parameter sensitivity study
├── region-method-comparison/      # KDE regions against rangeset regions, for every dataset
├── purity-indication-comparison/  # Purity-based visual emphasis, for every dataset
├── bookworm/                      # Fictional Bookworm dataset of Fig. 3 and its generator
├── orange-workflow-examples/      # Orange workflows and screenshots
├── user-study/                    # User-study materials
└── requirements.txt               # Python dependencies
```

The manuscript and the supplementary document (`supplementary-material.tex`) live in `2026-tvcg-resubmission-2/`, together with every figure they include. `figure_scripts/` renders those figures. The remaining directories hold the full studies the supplement summarizes, the Bookworm example data, the user-study materials, and the Orange workflows.

## User study

The complete user-study materials, in the form participants saw them, are in [`user-study/`](user-study/): the tool introductions, the six quizzes with the VERA explanations shown for each data set, the tool surveys, and the final comparative survey. Its README describes the study design and the order in which each group saw the materials.

## Setup

From the repository root, create an environment and install the dependencies, which include VERA 1.2.0 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then download the eight shared datasets (Iris, Penguins, Abalone, Titanic, Employee Attrition, Wine Quality, Adult, Forest Covertype):

```bash
python supplement-data/download_data.py
```

## Reproduce the figures

`figure_scripts/README.md` lists every figure of the manuscript and the supplement with the script that renders it and the data it needs. Run the scripts from the repository root, after the setup above.

First build the football and single-cell data. The runtime benchmarks of Fig. 12 are tracked in `figure_scripts/data/benchmarks/`, so rerunning them is optional.

```bash
python figure_scripts/prepare_football.py
python figure_scripts/prepare_single_cell.py
python figure_scripts/run_benchmarks.py  # optional
```

Then render the figures of the manuscript:

```bash
python figure_scripts/fig02_related_methods.py
python figure_scripts/fig09_attrition.py
python figure_scripts/fig10_abalone.py
python figure_scripts/fig12_benchmarks.py
```

and of the supplement:

```bash
python figure_scripts/figS01_S02_rangesets.py
python figure_scripts/figS03_football.py
python figure_scripts/figS04_single_cell.py
python figure_scripts/figS05_S09_parameters.py
python figure_scripts/figS10_S11_distortion.py
```

The scripts write PDF and PNG files to `figure_scripts/figures/` (only the PNGs are tracked), and a re-rendered PDF is copied into the paper folder under the same name. Figures are drawn in the manuscript's style (`supplement-data/figstyle.py`), at the width at which the paper includes them.

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
