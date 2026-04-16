# VERA: Supplementary Material

This repository contains the manuscript package and supplementary material for the VERA paper.

## Repository contents

```text
tvcg-embedding-annotation/
├── 2026-tvcg-resubmission-1/  # manuscript and cover letter
├── supplement-data/           # Data downloader
├── parameter-study/           # Parameter sensitivity study for VERA
├── region-method-comparison/  # KDE-versus-rangeset comparison
├── user-study/                # User-study materials
└── orange-workflow-examples/  # Orange workflows and screenshots documenting the interactive baseline and related embedding-interpretation workflows
```

## Setup

From the repository root, create an environment and install the shared supplementary dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then download the eight shared datasets used by the supplementary studies:

```bash
python supplement-data/download_data.py
```

The datasets are stored in `supplement-data/data/` and reused by both studies.

## Run the studies

Parameter sensitivity study:

```bash
python parameter-study/run_parameter_study.py parameter-study/config.json
```

Region-method comparison:

```bash
python region-method-comparison/run_region_method_comparison.py region-method-comparison/config.json
```

These two studies document several important methodological aspects of VERA, in particular:

- robustness of VERA to parameter choices
- practical guidance for default settings
- positioning of VERA relative to alternative region-construction backends such as rangesets

Additional details, study outputs, and supporting materials are documented in:

- `parameter-study/README.md`
- `region-method-comparison/README.md`
- `supplement-data/README.md`
- `user-study/README.md`
- `orange-workflow-examples/README.md`

