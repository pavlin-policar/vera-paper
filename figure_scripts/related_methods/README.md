# Related methods: reimplementations

Python reimplementations of the five related embedding-explanation methods drawn in the manuscript's comparison figure (Fig. 2), which `../fig02_related_methods.py` composes. The folder is a Python package of modules, without scripts of its own.

| Method | Module | Panel of Fig. 2 |
|---|---|---|
| ccPCA, Fujiwara, Kwon, and Ma, TVCG 2020 | `ccpca.py` | (b) histograms of the followed cluster against the rest, (d) feature-contribution heatmap |
| IXVC, Bibal, Clarinval, Dumas, and Frénay, Array 2021 | `ixvc.py` | (c) decision tree separating the DBSCAN clusters |
| Rangesets, Sohns, Schmitt, Jirasek, Hasse, and Leitte, TVCG 2022 | `rangesets.py` | (e) rangesets of one attribute |
| Attribute-based explanation, da Silva et al., EuroVA 2015 | `attribute_explanation.py` | (f) top-ranked dimension per point |
| Column selection method, Joia, Petronetto, and Nonato, CGF 2015 | `representative_groups.py` | (g) groups of representatives, labelled with their most relevant attributes |

The other files:

- `views.py`: the methods' matplotlib views (rangeset regions, the attribute-based dense map, the column selection polygons, the IXVC tree) and the legend, palette, and axis helpers the figure shares.
- `common.py`: loads a dataset of `supplement-data/` (a fixed random sample of 5,000 rows above that size), one-hot encodes categorical attributes, and clusters the embedding with DBSCAN.
- The methods' settings are in `../config.json`, beside VERA's: the choices an analyst makes interactively in the original tools.
  - **ccPCA:** standardization and the alpha search.
  - **Attribute-based explanation:** ρ, ρc, the dense map's fill radius, and whether categorical attributes are included.
  - **Column selection method:** the share of representatives, attribute scaling, and the polygon's α.
  - **Rangesets:** the number of bins and eps, as a multiple of Wilkinson's value.

  The DBSCAN clusters (shared by ccPCA, IXVC, and the number of column-selection groups), the rangeset attribute, and the figure's overrides of these settings are in `../fig02_related_methods.py`.

Each module's docstring states the method's equations, cites the paper section for every step, and lists every detail the paper leaves open with the value chosen here. The main choices:

- **ccPCA** follows the authors' current Python code (github.com/takanori-fujiwara/ccpca) where the paper is open: target and background are each standardized, histogram bins use Scott's width on the pooled projections, and alpha is searched in the standardized space (`projection="standardized"`; `"raw"` reproduces their C++ code). Signs are flipped and rows and columns reordered as in their `fc_view`. DBSCAN noise is background for every cluster but gets no column.
- **IXVC** has no public code. One multiclass scikit-learn tree (entropy criterion) maps the selected points' attributes to their groups, with min_samples_leaf in [10, 50) chosen by 10-fold cross-validation. The groups are DBSCAN clusters instead of lasso selections, and a split on a 0/1 column is drawn as "attribute = value".
- **Rangesets** follow the paper and the authors' NoLiES code (github.com/leitte/NoLiES): five equal-width bins (one per value for categorical attributes or numeric ones with fewer than 15 values), each bin's Delaunay triangulation without edges longer than eps, and points off their bin's region drawn as outliers. eps is twice Wilkinson's value (q75 + 1.5·IQR of the embedding's MST edge lengths).
- **Attribute-based explanation** has no public code. It uses the variance ranking in radius-ρ neighbourhoods (ρ = 10% of the projection diameter), ρc = ρ/2 for the confidence, which is the share of points within ρc that share the point's top-ranked dimension, and a nearest-neighbour dense map. Categorical attributes are left out, as the paper applies the method only to numeric data.
- **Column selection method** has no public code. Leverage scores select 15% of the instances as representatives, EM clusters them in the embedding (as many clusters as DBSCAN finds), and every instance joins its nearest representative's cluster; attribute relevance is the per-cluster leverage. The given embedding replaces LAMP. The figure standardizes the attributes and labels each group with its two most relevant attributes instead of a word cloud (see `../fig02_related_methods.py`).

Categorical attributes are one-hot encoded for every method.
