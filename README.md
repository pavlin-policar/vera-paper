# VERA: Accompanying paper code

This repository contains the manuscript revision package and supplementary material for the VERA paper.

## Repository contents

- `2026-tvcg-resubmission-1/`: current TVCG resubmission package, including the manuscript, cover letter, and reviewer-response material
- `supplement-data/`: shared downloader and local dataset cache used by the supplementary studies
- `parameter-study/`: parameter sensitivity study for VERA, covering both region construction and explanation construction
- `region-method-comparison/`: comparison between the paper's KDE-based region construction backend and a rangeset-inspired alternative motivated by Sohns et al.; includes both raw region-construction comparisons and the resulting VERA explanations with the downstream pipeline kept fixed
- `user-study/`: full catalog of user-study questions, participant-facing materials, and questionnaires
- `orange-workflow-examples/`: Orange workflows and screenshots used to document the interactive baseline and related embedding-interpretation workflows

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

These two studies address several of the reviewer concerns raised in the TVCG revision, in particular:

- robustness of VERA to parameter choices
- practical guidance for default settings
- positioning of VERA relative to alternative region-construction backends such as rangesets

Additional details, study outputs, and supporting materials are documented in:

- `parameter-study/README.md`
- `region-method-comparison/README.md`
- `supplement-data/README.md`
- `user-study/README.md`
- `orange-workflow-examples/README.md`
