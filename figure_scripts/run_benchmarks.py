"""The runtime benchmarks of the manuscript's runtime figure (Fig. 12,
fig12_benchmarks.py), on synthetic low-rank datasets, single-core. The
results go to `data/benchmarks/`: `feature-contrastive.csv` and
`feature-descriptive.csv` (explanation runtime against the number of region
annotations), and, from the commented-out sample benchmark,
`sample-final.csv` (region-construction runtime against the number of
samples).

Usage: python run_benchmarks.py
"""
import os
import time

import numpy as np
import pandas as pd

import vera

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "benchmarks")


def make_x(n_samples, n_features, rank, seed=0):
    np.random.seed(seed)
    zx = np.exp(np.random.normal(0, 1, size=(n_samples, rank)))
    zx /= zx.sum(axis=1, keepdims=True)
    zf = np.random.normal(0, 1, size=(rank, n_features))
    x = zx @ zf
    return x


RANK = 10
REPETITIONS = 6
SAMPLE_SIZES = [100, 1000, 5000, 10_000, 20_000]
FEATURE_SIZES = [10, 20, 30, 50, 100, 250, 500, 750, 1000, 1500]


# SAMPLE_SIZES = [100, 200, 300]
# FEATURE_SIZES = [5, 10, 20]

# print("=" * 80, "SAMPLE BENCHMARK", "=" * 80, sep="\n")
# datas = []
# for n_features in [1, 10, 100, 200, 300, 400, 500]:
#     # for n_samples in SAMPLE_SIZES:
#     for n_samples in [15_000]:
#         for repetition in range(REPETITIONS):
#             if n_features == 1:
#                 x = make_x(n_samples, 2, rank=RANK)
#                 x = pd.DataFrame(x, columns=[f"v{i + 1:02d}" for i in range(x.shape[1])])
#                 y = x.values[:, :2]
#                 x = x.iloc[:, :1]
#             else:
#                 x = make_x(n_samples, n_features, rank=RANK)
#                 x = pd.DataFrame(x, columns=[f"v{i + 1:02d}" for i in range(x.shape[1])])
#                 y = x.values[:, :2]
#
#             start = time.time()
#             region_annotations = vera.an.generate_region_annotations(
#                 x,
#                 y,
#                 n_discretization_bins=5,
#                 scale_factor=1,
#                 sample_size=None,
#                 contour_level=0.25,
#                 merge_min_sample_overlap=0.9,
#             )
#             stop = time.time()
#             duration = stop - start
#             print(f"N: {x.shape[0]} x F: {x.shape[1]} - {duration:.2f}")
#             datas.append({
#                 "rep": repetition,
#                 "N": x.shape[0],
#                 "F": x.shape[1],
#                 "rank": RANK,
#                 "duration": duration,
#                 "region_annotations": len(region_annotations),
#             })
#
# pd.DataFrame(datas).to_csv(os.path.join(DATA_DIR, "sample-final.csv"), index=False)


print("=" * 80, "FEATURE BENCHMARK - CONTRASTIVE", "=" * 80, sep="\n")
datas = []
for n_features in FEATURE_SIZES:
    for repetition in range(REPETITIONS):
        seed = 12+repetition
        x = make_x(1000, n_features, rank=RANK, seed=seed)
        x = pd.DataFrame(x, columns=[f"v{i + 1:02d}" for i in range(x.shape[1])])
        y = x.values[:, :2]

        start = time.time()
        region_annotations = vera.an.generate_region_annotations(
            x,
            y,
            n_discretization_bins=5,
            scale_factor=1,
            sample_size=None,
            contour_level=0.25,
            merge_min_sample_overlap=0.9,
        )
        stop = time.time()
        duration_ra = stop - start

        start = time.time()
        layouts = vera.explain.contrastive(region_annotations, max_panels=10)
        stop = time.time()
        duration_expl = stop - start

        duration = duration_ra + duration_expl

        print(f"N: {x.shape[0]} x F: {x.shape[1]} - {duration_expl:.2f} - {len(layouts)} layouts")
        datas.append({
            "type": "contrastive",
            "rep": seed,
            "N": x.shape[0],
            "F": x.shape[1],
            "rank": RANK,
            "duration_ra": duration_ra,
            "duration_expl": duration_expl,
            "duration": duration,
            "region_annotations": len(region_annotations),
            "panels": len(layouts),
        })

pd.DataFrame(datas).to_csv(os.path.join(DATA_DIR, "feature-contrastive.csv"), index=False)


print("=" * 80, "FEATURE BENCHMARK - DESCRIPTIVE", "=" * 80, sep="\n")
datas = []
for n_features in [10, 20, 30, 50, 100, 250, 500, 750, 1000]:
    for repetition in range(REPETITIONS):
        seed = 12+repetition
        x = make_x(1000, n_features, rank=RANK, seed=seed)
        x = pd.DataFrame(x, columns=[f"v{i + 1:02d}" for i in range(x.shape[1])])
        y = x.values[:, :2]

        start = time.time()
        region_annotations = vera.an.generate_region_annotations(
            x,
            y,
            n_discretization_bins=5,
            scale_factor=1,
            sample_size=None,
            contour_level=0.25,
            merge_min_sample_overlap=0.9,
        )
        stop = time.time()
        duration_ra = stop - start

        start = time.time()
        layouts = vera.explain.descriptive(
            region_annotations,
            allow_greedy_approx=False,
            max_panels=10,
        )
        stop = time.time()
        duration_expl = stop - start

        duration = duration_ra + duration_expl

        print(f"N: {x.shape[0]} x F: {x.shape[1]} - {duration_expl:.2f} - {len(layouts)} layouts")
        datas.append({
            "type": "descriptive",
            "rep": seed,
            "N": x.shape[0],
            "F": x.shape[1],
            "rank": RANK,
            "duration_ra": duration_ra,
            "duration_expl": duration_expl,
            "duration": duration,
            "region_annotations": len(region_annotations),
            "panels": len(layouts),
        })

pd.DataFrame(datas).to_csv(os.path.join(DATA_DIR, "feature-descriptive.csv"), index=False)
