"""Tabulate the parameter sensitivity study.

The study's figures show how each region-construction parameter changes the
extracted annotations. This script records the same sweep numerically so the
effect can be read off a table: for every dataset and parameter value, the
number of variables that survive filtering, the total number of region
annotations, and the mean number of regions per surviving variable; and for
the explanation-construction sweep, the number of panels and the mean number
of regions and descriptors per panel.

Usage: python summarize_parameter_study.py config.json
"""
import argparse
import json
import os
import time
from importlib.util import module_from_spec, spec_from_file_location

import numpy as np
import pandas as pd

import vera
import vera.explain

HERE = os.path.dirname(os.path.abspath(__file__))


def load_datasets_module():
    spec = spec_from_file_location("_supplement_datasets", os.path.join(HERE, "..", "supplement-data", "datasets.py"))
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ds = load_datasets_module()


def region_stats(ras):
    n_regions = [len(g) for g in ras]
    return dict(variables=len(ras), region_annotations=int(sum(n_regions)),
                regions_per_variable=float(np.mean(n_regions)) if n_regions else np.nan)


def layout_stats(layout):
    if not layout:
        return dict(panels=0, regions_per_panel=np.nan, descriptors_per_region=np.nan)
    # Background enrichment keeps the descriptors it adds apart from the core
    # description, in the group's background_variables
    n_desc = [len(getattr(ra.descriptor, "variables", [ra.descriptor]))
              + len(getattr(ra.descriptor, "background_variables", []))
              for p in layout for ra in p]
    return dict(panels=len(layout), regions_per_panel=float(np.mean([len(p) for p in layout])),
                descriptors_per_region=float(np.mean(n_desc)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    args = ap.parse_args()
    with open(args.config) as f:
        cfg = json.load(f)
    defaults, variations = cfg["defaults"], cfg["parameter_variations"]
    con_defaults, con_var = cfg.get("contrastive_defaults", {}), cfg.get("contrastive_parameter_variations", {})
    des_defaults, des_var = cfg.get("descriptive_defaults", {}), cfg.get("descriptive_parameter_variations", {})
    max_panels = cfg.get("max_panels", 4)

    region_rows, expl_rows = [], []
    for name in cfg["datasets"]:
        data = ds.Dataset.load(name)
        print(f"[{name}]", flush=True)
        default_ras = None
        for param, values in variations.items():
            for val in values:
                kw = dict(defaults)
                kw[param] = val
                t = time.time()
                ras = vera.an.generate_region_annotations(data.features, data.embedding, **kw)
                row = dict(dataset=name, parameter=param, value=val, is_default=(val == defaults[param]),
                           seconds=round(time.time() - t, 1), **region_stats(ras))
                region_rows.append(row)
                print(f"   {param}={val}: {row['variables']} variables, {row['region_annotations']} regions", flush=True)
                if val == defaults[param] and default_ras is None:
                    default_ras = ras
        for kind, fn, dflt, var in (("contrastive", vera.explain.contrastive, con_defaults, con_var),
                                    ("descriptive", vera.explain.descriptive, des_defaults, des_var)):
            for param, values in var.items():
                for val in values:
                    kw = dict(dflt)
                    kw[param] = val
                    layout = fn(default_ras, max_panels=max_panels, **kw)
                    expl_rows.append(dict(dataset=name, explanation=kind, parameter=param, value=val,
                                          is_default=(val == dflt.get(param)), **layout_stats(layout)))

    reg = pd.DataFrame(region_rows)
    exp = pd.DataFrame(expl_rows)
    reg.to_csv(os.path.join(HERE, "summary-region-construction.csv"), index=False)
    exp.to_csv(os.path.join(HERE, "summary-explanation-construction.csv"), index=False)

    md = ["# Parameter study summary", "",
          "## Region construction: variables kept / region annotations", ""]
    for param in variations:
        sub = reg[reg.parameter == param]
        vals = list(variations[param])
        md += [f"### {param} (default `{defaults[param]}`)", "",
               "| Dataset | " + " | ".join(f"`{v}`" for v in vals) + " |", "|---|" + "---|" * len(vals)]
        for name in cfg["datasets"]:
            cells = []
            for v in vals:
                r = sub[(sub.dataset == name) & (sub.value == v)]
                cells.append(f"{int(r.variables.iloc[0])} / {int(r.region_annotations.iloc[0])}" if len(r) else "-")
            md.append(f"| {name} | " + " | ".join(cells) + " |")
        md.append("")
    md += ["## Explanation construction: panels / regions per panel / descriptors per region", ""]
    for kind, var, dflt in (("contrastive", con_var, con_defaults), ("descriptive", des_var, des_defaults)):
        for param in var:
            sub = exp[(exp.explanation == kind) & (exp.parameter == param)]
            vals = list(var[param])
            md += [f"### {kind}: {param} (default `{dflt.get(param)}`)", "",
                   "| Dataset | " + " | ".join(f"`{v}`" for v in vals) + " |", "|---|" + "---|" * len(vals)]
            for name in cfg["datasets"]:
                cells = []
                for v in vals:
                    r = sub[(sub.dataset == name) & (sub.value == v)]
                    if len(r):
                        r = r.iloc[0]
                        cells.append(f"{int(r.panels)} / {r.regions_per_panel:.1f} / {r.descriptors_per_region:.1f}")
                    else:
                        cells.append("-")
                md.append(f"| {name} | " + " | ".join(cells) + " |")
            md.append("")
    with open(os.path.join(HERE, "SUMMARY.md"), "w") as f:
        f.write("\n".join(md))
    print("done", flush=True)


if __name__ == "__main__":
    main()
