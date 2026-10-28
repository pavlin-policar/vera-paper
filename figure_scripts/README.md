# Figure scripts

Every script that renders a figure of the manuscript or the supplementary material. Each writes its figure as PDF and PNG to `figures/`, under the name the paper folder (`2026-tvcg-resubmission-2/`) uses. The PNGs are tracked; the PDFs and `cache/` are git-ignored.

Run the commands from the repository root with the project environment (`.venv/`, see the repository README), after downloading the shared datasets (`supplement-data/download_data.py`).

| Figure | Script | Command | Input data |
|---|---|---|---|
| Manuscript Fig. 2, related methods and VERA (`fig_related_methods`) | `fig02_related_methods.py` | `.venv/bin/python figure_scripts/fig02_related_methods.py` | `supplement-data/data/football_players_wyscout` (`prepare_football.py`) |
| Manuscript Fig. 9, attrition case study (`case_study-attrition`) | `fig09_attrition.py` | `.venv/bin/python figure_scripts/fig09_attrition.py` | `supplement-data/data/attrition` |
| Manuscript Fig. 10, abalone case study (`case_study-abalone`) | `fig10_abalone.py` | `.venv/bin/python figure_scripts/fig10_abalone.py` | `supplement-data/data/abalone` |
| Manuscript Fig. 12, runtime (`benchmarks`) | `fig12_benchmarks.py` | `.venv/bin/python figure_scripts/fig12_benchmarks.py` | `data/benchmarks/*.csv` (`run_benchmarks.py`) |
| Supplement Figs. S1 and S2, rangesets against contrastive explanations (`fig_supp_rangeset-contrastive-abalone`, `-attrition`) | `figS01_S02_rangesets.py` | `.venv/bin/python figure_scripts/figS01_S02_rangesets.py` | `supplement-data/data/{abalone,attrition}` |
| Supplement Fig. S3, VERA's explanations of the football players (`fig_supp_football`) | `figS03_football.py` | `.venv/bin/python figure_scripts/figS03_football.py` | `supplement-data/data/football_players_wyscout` |
| Supplement Fig. S4, single-cell data (`fig_supp_singlecell`), and its rows as `singlecell-<data set>` | `figS04_single_cell.py` | `.venv/bin/python figure_scripts/figS04_single_cell.py` | `cache/single_cell/` (`prepare_single_cell.py`) |
| Supplement Figs. S5-S9, parameter sensitivity on abalone (`fig_supp_region-bins`, `-region-bandwidth`, `-region-merge`, `-contrastive-parameters`, `-descriptive-parameters`) | `figS05_S09_parameters.py` | `.venv/bin/python figure_scripts/figS05_S09_parameters.py` | `supplement-data/data/abalone`, `parameter-study/config.json` |
| Supplement Figs. S10 and S11, distortion weighting (`fig_supp_distortion-abalone`, `-attrition-pca`) | `figS10_S11_distortion.py` | `.venv/bin/python figure_scripts/figS10_S11_distortion.py` | `supplement-data/data/{abalone,attrition}`; the PCA embedding and neighbor preservation are cached in `cache/distortion/` |

**Data preparation.**
- `prepare_football.py` builds `supplement-data/data/football_players_wyscout/` from the Wyscout soccer-logs, which it downloads to `supplement-data/data/raw/`.
- `prepare_single_cell.py` downloads the four single-cell data sets of Fig. S4 (PBMC 3k, mouse pancreas, mouse retina, human pancreas) to `supplement-data/data/raw/single_cell/`. It preprocesses them as in the scanpy tutorial, embeds them, and writes `cache/single_cell/<data set>.npz`. `figS04_single_cell.py` caches VERA's layouts next to them (`<data set>-<embedding>-layout.pkl`) and draws from the cached layouts; `--recompute` runs VERA again.
- `run_benchmarks.py` reruns the runtime benchmarks into `data/benchmarks/`.

**Configuration.**
- `config.json` holds VERA's settings for Fig. 2 and Figs. S1-S3 and the settings of the reimplemented related methods in `related_methods/`, a package whose README describes the methods.
- `config_single_cell.json` holds the single-cell data sets, their cell types and reference markers, and the preprocessing and VERA settings of Fig. S4.

The other figure scripts set their parameters in the script.

**Updating the paper.** The paper folder (`2026-tvcg-resubmission-2/`) holds the PDFs the manuscript and the supplement include, under the same names as in `figures/`; a re-rendered figure is copied there by hand. The paper's Fig. 2 (`fig_related_methods.pdf`) is finished by hand in Illustrator after `fig02_related_methods.py` renders it, so a new rendering has to be finished again before it replaces the paper's copy. The per-dataset single-cell figures (`singlecell-<data set>`) are shown only in this repository.

**Static figures.** No script renders manuscript Figs. 1, 3-8, and 11 (`fig_motivation`, `fig_variable_values`, `fig_construct_regions`, `fig_contrastive_merge`, `fig_contrastive_selection`, `fig_descriptive_merge`, `fig_descriptive_selection`, `case_study-iris-penguins`), or the Orange screenshots of the supplement (`orange-workflow-examples/screenshots/`). Their PDFs and images in the paper folder are the sources.
