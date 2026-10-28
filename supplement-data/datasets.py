"""
Shared dataset loader for supplementary VERA studies.

Loads pre-computed datasets (embedding + features + metadata) from the local
`data/` directory inside `supplement-data`.
"""

import json
import os
from os import path
from typing import Any

import numpy as np
import pandas as pd


BASE_DIR = path.dirname(__file__)
DATA_DIR = path.join(BASE_DIR, "data")


class Dataset:
    def __init__(
        self,
        name: str,
        embedding: np.ndarray,
        features: pd.DataFrame,
        metadata: dict[str, Any] | None = None,
        labels: pd.DataFrame | None = None,
    ):
        self.name = name

        if embedding.shape[0] != features.shape[0]:
            raise ValueError(
                "Embedding and features must have the same number of rows"
            )
        self.embedding = embedding
        self.features = features
        self.metadata = metadata or {}
        # Post hoc labels (class, cuisine, genre, ...) used only to read an
        # embedding, never to construct it
        self.labels = labels

    @property
    def data_dir(self) -> str:
        return path.join(DATA_DIR, self.name)

    @property
    def indicator_columns(self):
        """Columns to hand to VERA as presence indicators, or None."""
        return self.metadata.get("indicator_cols", None)

    @classmethod
    def load(cls, name: str, embedding: str = None) -> "Dataset":
        """Load a prepared dataset.

        `embedding` selects an alternative layout stored next to the default
        one, e.g. ``"umap"`` reads ``embedding_umap.csv``.
        """
        embedding_basename = "embedding.csv" if embedding is None else f"embedding_{embedding}.csv"
        embedding_fname = path.join(DATA_DIR, name, embedding_basename)
        features_fname = path.join(DATA_DIR, name, "features.csv")

        if not path.exists(embedding_fname):
            raise FileNotFoundError(
                f"Embedding file not found: {embedding_fname}. "
                "Run `python supplement-data/download_data.py` first "
                "or see the supplementary README files for setup instructions."
            )
        if not path.exists(features_fname):
            raise FileNotFoundError(
                f"Features file not found: {features_fname}. "
                "Run `python supplement-data/download_data.py` first "
                "or see the supplementary README files for setup instructions."
            )

        embedding = pd.read_csv(embedding_fname, header=None).values
        features = pd.read_csv(
            features_fname, encoding="utf-8", compression="gzip"
        )

        metadata_fname = path.join(DATA_DIR, name, "metadata.json")
        metadata = {}
        if os.path.exists(metadata_fname):
            with open(metadata_fname, "r") as f:
                metadata = json.load(f)

        labels = None
        labels_fname = path.join(DATA_DIR, name, metadata.get("label_col_file", "labels.csv"))
        if os.path.exists(labels_fname):
            labels = pd.read_csv(labels_fname)

        dataset = cls(name, embedding, features, metadata=metadata, labels=labels)

        categorical_cols = dataset.metadata.get("categorical_cols", None)
        if categorical_cols is not None:
            for col in categorical_cols:
                if col in dataset.features.columns:
                    dataset.features[col] = dataset.features[col].astype("category")

        return dataset
