"""Download and preprocess the four single-cell data sets of the supplement's
single-cell figure (Fig. S4, figS04_single_cell.py).

For each data set this
  * downloads the raw counts into `supplement-data/data/raw/single_cell/<data
    set>/` (PBMC 3k is fetched by scanpy itself; files already present are
    skipped),
  * keeps the cells and genes of the published analysis and their published
    cell types,
  * ranks the genes by their analytic Pearson-residual variance on the raw
    counts, without reference to cell types,
  * preprocesses the counts as in the scanpy clustering tutorial (total-count
    normalization, log1p, highly variable genes, regression of total counts
    and mitochondrial fraction, scaling, PCA) and embeds the leading principal
    components with t-SNE (openTSNE) and UMAP, or takes the embedding
    published with the data,
and writes `cache/single_cell/<data set>.npz` with the log-normalized
expression of the genes the figure can use, both embeddings, the cell types,
and the gene ranking.

Usage: python prepare_single_cell.py [--datasets pbmc3k pancreas macosko baron] [--force]
"""
import argparse
import json
import os
import shutil
import tarfile
import time
import urllib.request

import numpy as np
import pandas as pd
import scanpy as sc
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "..", "supplement-data", "data", "raw", "single_cell")
CACHE_DIR = os.path.join(HERE, "cache", "single_cell")
CONFIG = os.path.join(HERE, "config_single_cell.json")

GEO = "https://ftp.ncbi.nlm.nih.gov/geo/series"
OPENTSNE = "http://file.biolab.si/opentsne/h5ad"
BARON_DONORS = [
    "GSM2230757_human1_umifm_counts.csv.gz",
    "GSM2230758_human2_umifm_counts.csv.gz",
    "GSM2230759_human3_umifm_counts.csv.gz",
    "GSM2230760_human4_umifm_counts.csv.gz",
]

# Data set -> list of (url, file name in RAW_DIR/<data set>/, kind, members);
# "tar" files are unpacked and removed, keeping only `members` when given.
# PBMC 3k is fetched by scanpy
SOURCES = {
    "pbmc3k": [],
    "pancreas": [(
        "https://github.com/theislab/scvelo_notebooks/raw/master/data/Pancreas/endocrinogenesis_day15.h5ad",
        "endocrinogenesis_day15.h5ad", "file", None,
    )],
    "macosko": [(f"{OPENTSNE}/macosko_2015.h5ad.tar.gz", "macosko_2015.h5ad", "tar", None)],
    "baron": [(f"{GEO}/GSE84nnn/GSE84133/suppl/GSE84133_RAW.tar", BARON_DONORS[0], "tar", BARON_DONORS)],
}


# --------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------
def fetch(url, path):
    print(f"  {url}", flush=True)
    tmp = path + ".part"
    request = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(request) as response, open(tmp, "wb") as f:
        shutil.copyfileobj(response, f)
    os.replace(tmp, path)


def download(name):
    out_dir = os.path.join(RAW_DIR, name)
    os.makedirs(out_dir, exist_ok=True)
    for url, target, kind, members in SOURCES[name]:
        if os.path.exists(os.path.join(out_dir, target)):
            print(f"  {target} is present", flush=True)
            continue
        if kind == "file":
            fetch(url, os.path.join(out_dir, target))
            continue
        archive = os.path.join(out_dir, os.path.basename(url))
        fetch(url, archive)
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                if members is None or member.name in members:
                    tar.extract(member, out_dir, filter="data")
        os.remove(archive)


# --------------------------------------------------------------------------
# Loading: raw counts with the published cell types in obs["cell_type"]
# --------------------------------------------------------------------------
def load_pbmc3k(dcfg):
    """Raw counts of the cells that pass the tutorial's QC, with the tutorial's
    Louvain cell types."""
    sc.settings.datasetdir = os.path.join(RAW_DIR, "pbmc3k")
    adata = sc.datasets.pbmc3k()
    adata.var_names_make_unique()
    q = dcfg["cell_qc"]
    sc.pp.filter_cells(adata, min_genes=q["min_genes"])
    sc.pp.filter_genes(adata, min_cells=dcfg["min_cells"])
    adata.var["mt"] = adata.var_names.str.startswith("MT-")
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True)
    adata = adata[(adata.obs.n_genes_by_counts < q["max_genes"])
                  & (adata.obs.pct_counts_mt < q["max_pct_mt"])].copy()
    labels = sc.datasets.pbmc3k_processed().obs["louvain"].astype(str)
    adata.obs["cell_type"] = labels.reindex(adata.obs_names).values
    return adata


def load_pancreas(dcfg):
    """Raw counts of the scvelo pancreas data (Bastidas-Ponce et al., 2019),
    with the authors' cell types and their published UMAP in
    `obsm["X_umap"]`."""
    adata = sc.read_h5ad(os.path.join(RAW_DIR, "pancreas", "endocrinogenesis_day15.h5ad"))
    adata = sc.AnnData(adata.X, obs=adata.obs[["clusters"]], var=adata.var[[]],
                       obsm={"X_umap": adata.obsm["X_umap"]})
    sc.pp.filter_genes(adata, min_cells=dcfg["min_cells"])
    adata.var["mt"] = adata.var_names.str.startswith("mt-")
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True)
    adata.obs["cell_type"] = adata.obs["clusters"].astype(str).values
    return adata


def load_macosko(dcfg):
    """Raw UMI counts of the Macosko et al. (2015) mouse retina (the openTSNE
    paper's `macosko_2015.h5ad`), with the authors' 39 clusters merged into
    their 12 cell types."""
    adata = sc.read_h5ad(os.path.join(RAW_DIR, "macosko", "macosko_2015.h5ad"))
    adata = sc.AnnData(adata.X.tocsr(), obs=adata.obs[["labels"]], var=pd.DataFrame(index=adata.var_names))
    sc.pp.filter_genes(adata, min_cells=dcfg["min_cells"])
    adata.var["mt"] = adata.var_names.str.startswith("MT-")
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True)
    adata.obs["cell_type"] = adata.obs["labels"].astype(str).values
    return adata


def load_baron(dcfg):
    """Raw UMI counts of the four human donors of Baron et al. (2016)
    (GEO GSE84133), with the authors' cell types."""
    d = os.path.join(RAW_DIR, "baron")
    tables = [pd.read_csv(os.path.join(d, f), index_col=0) for f in sorted(os.listdir(d)) if f.endswith(".csv.gz")]
    table = pd.concat(tables)
    counts = table.drop(columns=["barcode", "assigned_cluster"])
    adata = sc.AnnData(sp.csr_matrix(counts.values.astype(np.float32)), obs=pd.DataFrame(index=counts.index),
                       var=pd.DataFrame(index=counts.columns))
    adata.obs_names_make_unique()
    sc.pp.filter_genes(adata, min_cells=dcfg["min_cells"])
    adata.var["mt"] = adata.var_names.str.startswith("MT-")
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True)
    adata.obs["cell_type"] = table["assigned_cluster"].astype(str).values
    return adata


LOADERS = {"pbmc3k": load_pbmc3k, "pancreas": load_pancreas, "macosko": load_macosko, "baron": load_baron}


# --------------------------------------------------------------------------
# Preprocessing and embeddings
# --------------------------------------------------------------------------
def preprocess(adata, cfg):
    """QC-filtered raw counts -> tutorial PCA, plus log-normalized expression
    and the Pearson-residual gene ranking computed on the same cells."""
    p = cfg["preprocessing"]

    # Explanatory-gene ranking on raw counts; uses no cell-type information
    pr = sc.experimental.pp.highly_variable_genes(
        adata, flavor="pearson_residuals", n_top_genes=cfg["explanatory_genes"]["n_genes"],
        inplace=False,
    )
    residual_variance = pd.Series(np.asarray(pr["residual_variances"]), index=adata.var_names)

    sc.pp.normalize_total(adata, target_sum=p["target_sum"])
    sc.pp.log1p(adata)
    adata.raw = adata
    sc.pp.highly_variable_genes(adata, **p["hvg"])

    adata_pca = adata[:, adata.var.highly_variable].copy()
    # Data without mitochondrial genes have no mitochondrial fraction
    regressors = ["total_counts"] + (["pct_counts_mt"] if adata.var["mt"].any() else [])
    sc.pp.regress_out(adata_pca, regressors)
    sc.pp.scale(adata_pca, max_value=10)
    sc.tl.pca(adata_pca, n_comps=p["n_pcs"], svd_solver="arpack", random_state=0)
    pcs = adata_pca.obsm["X_pca"][:, :p["n_pcs_embedding"]]

    lognorm = adata.raw.to_adata()
    return lognorm, pcs, residual_variance


def compute_embeddings(pcs, params, precomputed):
    """t-SNE and UMAP of `pcs`, except those given in `precomputed`."""
    from openTSNE import TSNE
    import umap

    out = dict(precomputed)
    if "tsne" not in out:
        c = params["tsne"]
        out["tsne"] = np.asarray(TSNE(perplexity=c["perplexity"], random_state=c["random_state"],
                                      n_jobs=8).fit(pcs))
    if "umap" not in out:
        c = params["umap"]
        out["umap"] = umap.UMAP(n_neighbors=c["n_neighbors"], min_dist=c["min_dist"],
                                random_state=c["random_state"]).fit_transform(pcs)
    return out


def prepare(name, cfg):
    """Writes CACHE_DIR/<name>.npz from the raw counts."""
    dcfg = cfg["datasets"][name]
    t = time.time()
    adata = LOADERS[name](dcfg)
    labels = adata.obs["cell_type"].astype(str)
    if labels.isna().any() or not labels.isin(list(dcfg["cell_types"])).all():
        raise RuntimeError(f"unlabelled or unknown cell types: {sorted(set(labels) - set(dcfg['cell_types']))}")
    precomputed = {e: np.asarray(adata.obsm[key]) for e, key in dcfg.get("published_embeddings", {}).items()}
    lognorm, pcs, resvar = preprocess(adata, cfg)
    embeddings = compute_embeddings(pcs, cfg["embeddings"], precomputed)

    # Only the explanatory genes and the reference markers are kept; a dense
    # matrix of all genes does not fit in memory for the larger data sets
    keep = set(resvar.sort_values(ascending=False).index[:cfg["explanatory_genes"]["n_genes"]]) | set(dcfg["markers"])
    lognorm = lognorm[:, lognorm.var_names.isin(keep)]
    X = lognorm.X.toarray() if hasattr(lognorm.X, "toarray") else np.asarray(lognorm.X)
    meta = {"n_cells": int(X.shape[0]), "n_genes_after_qc": int(len(resvar)),
            "embedding_params": cfg["embeddings"], "seconds": round(time.time() - t, 1)}
    os.makedirs(CACHE_DIR, exist_ok=True)
    np.savez_compressed(
        os.path.join(CACHE_DIR, f"{name}.npz"), expr=X.astype(np.float32), cells=np.asarray(lognorm.obs_names),
        genes=np.asarray(lognorm.var_names), tsne=embeddings["tsne"], umap=embeddings["umap"],
        labels=labels.values, resvar=resvar.values, all_genes=np.asarray(resvar.index), meta=json.dumps(meta),
        pcs=np.asarray(pcs, dtype=np.float32),
    )


def main():
    with open(CONFIG) as f:
        cfg = json.load(f)
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="*", default=list(cfg["datasets"]), choices=list(cfg["datasets"]))
    ap.add_argument("--force", action="store_true", help="rebuild data sets whose cache exists")
    args = ap.parse_args()
    for name in args.datasets:
        print(f"== {name}", flush=True)
        if os.path.exists(os.path.join(CACHE_DIR, f"{name}.npz")) and not args.force:
            print("  cached", flush=True)
            continue
        download(name)
        prepare(name, cfg)


if __name__ == "__main__":
    main()
