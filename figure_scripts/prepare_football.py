"""Build the football players dataset of the manuscript's comparison figure
(Fig. 2) and the supplement's football explanations (Fig. S3).

Source (downloaded into `supplement-data/data/raw/` on first use):
  football_players_wyscout
                       Wyscout soccer-logs (Pappalardo et al., 2019, CC BY
                       4.0), events of the 2017-18 season of the five big
                       European leagues aggregated per player; 1,634 players
                       with at least 900 minutes

Writes the standard supplement layout under
`supplement-data/data/football_players_wyscout/`:
  embedding.csv, embedding_<variant>.csv   headerless x,y
  features.csv                             gzip-compressed attribute table
  metadata.json                            column roles and provenance

Usage: python prepare_football.py
"""
import json
import os
import zipfile
from collections import Counter, defaultdict
from urllib.request import urlopen

import numpy as np
import pandas as pd
from scipy.stats import skew

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "supplement-data", "data")
RAW = os.path.join(DATA_DIR, "raw")
RANDOM_STATE = 0
MAX_ROWS = 5000
SKEW_LOG = 2.0

NAME = "football_players_wyscout"
# The parameters are the libraries' defaults, stated for the metadata; the
# t-SNE embedding is written to embedding.csv
VARIANTS = {
    "tsne": ("tsne", dict(perplexity=30)),
    "umap": ("umap", dict(n_neighbors=15, min_dist=0.1)),
}
DEFAULT_VARIANT = "tsne"
# The t-SNE embedding is centred and rotated clockwise by this angle (degrees),
# chosen for the comparison figure's VERA panel as the rotation whose label
# layout overlaps least; t-SNE is invariant to rotation
ROTATE = {"tsne": 5}


def rotate(emb, degrees):
    """`emb` centred and rotated clockwise by `degrees`."""
    t = np.radians(degrees)
    c, s = np.cos(t), np.sin(t)
    return (emb - emb.mean(axis=0)) @ np.array([[c, s], [-s, c]])


def fetch_url(url, fname):
    target = os.path.join(RAW, fname)
    if not os.path.exists(target):
        os.makedirs(RAW, exist_ok=True)
        print(f"fetch {url}", flush=True)
        with urlopen(url) as r, open(target, "wb") as f:
            f.write(r.read())
    return target


def subsample(df, n=MAX_ROWS, stratify=None):
    if len(df) <= n:
        return df.reset_index(drop=True)
    rng = np.random.RandomState(RANDOM_STATE)
    if stratify is None:
        idx = np.sort(rng.choice(len(df), n, replace=False))
        return df.iloc[idx].reset_index(drop=True)
    parts = [g.iloc[np.sort(rng.choice(len(g), n // df[stratify].nunique(), replace=False))]
             for _, g in df.groupby(stratify, sort=True, observed=True)]
    return pd.concat(parts).sort_index().reset_index(drop=True)


WY_URL = "https://ndownloader.figshare.com/files/{}"
WY_FILES = {"events": (14464685, "wyscout-events.zip"), "matches": (14464622, "wyscout-matches.zip"),
            "players": (15073721, "wyscout-players.json")}
WY_LEAGUES = ["England", "France", "Germany", "Italy", "Spain"]
# Per-player event counts of the five leagues, written on first use
WY_CACHE = "wyscout-2017-18-player-counts.csv"
WY_MIN_MINUTES = 900
# Wyscout sub-event ids and their names; offsides (event 6) have no sub-event
# and are counted as sub-event 60. Interruptions (50, 51) are not player
# actions; the rarer foul types (22-27) are not kept
WY_SUB = {
    10: "air duels", 11: "attacking duels", 12: "defending duels", 13: "loose-ball duels",
    20: "fouls", 21: "handballs", 30: "corners taken", 31: "free kicks taken", 32: "free-kick crosses",
    33: "free-kick shots", 34: "goal kicks", 35: "penalties taken", 36: "throw-ins",
    40: "rushes off the line", 60: "offsides", 70: "ball carries", 71: "clearances", 72: "ball touches",
    80: "crosses", 81: "hand passes", 82: "headed passes", 83: "high passes", 84: "long balls",
    85: "simple passes", 86: "smart passes", 90: "reflex saves", 91: "save attempts", 100: "shots",
}
WY_PASSES = [80, 81, 82, 83, 84, 85, 86]
WY_DUELS = [10, 11, 12, 13]
# Tags counted over all of a player's actions (tags2name.csv)
WY_TAGS = {
    301: "assists", 302: "key passes", 901: "through balls", 1901: "counter-attack actions",
    1401: "interceptions", 2001: "dangerous balls lost", 602: "anticipations", 601: "anticipated by opponent",
    1601: "sliding tackles", 503: "take-ons to the left", 504: "take-ons to the right", 1301: "feints",
    1302: "missed balls", 1702: "yellow cards", 201: "goal chances", 2101: "blocked actions",
}
# Sub-events split by pitch third and lane, and the success rates kept
WY_SPLIT = [10, 11, 12, 13, 20, 70, 71, 72, 80, 82, 83, 84, 85, 86, 100]
WY_ACCURATE = {80: "cross accuracy", 82: "headed pass accuracy", 83: "high pass accuracy", 84: "long ball accuracy",
               85: "simple pass accuracy", 86: "smart pass accuracy", 100: "shots on target", 71: "clearance accuracy",
               70: "successful ball carries", 72: "successful ball touches", 36: "throw-in accuracy"}
WY_WON = {10: "air duels won", 11: "attacking duels won", 12: "defending duels won", 13: "loose-ball duels won"}
WY_FAMILIES = {"passes": WY_PASSES, "duels": WY_DUELS, "touches": [70, 72]}
# Pitch of 105 x 68 m; Wyscout coordinates are percentages, x towards the
# opponent's goal, y from the attacking team's left. The penalty box spans
# x >= 84 and 19 <= y <= 81
WY_PITCH = (105, 68)
THIRDS = ["own third", "middle third", "final third"]
LANES = ["left", "centre", "right"]
LANE_NAMES = ["on the left", "in the centre", "on the right"]


def _zone(p):
    return min(int(p["x"] // (100 / 3)), 2), min(int(p["y"] // (100 / 3)), 2)


def _in_box(p):
    return p["x"] >= 84 and 19 <= p["y"] <= 81


def _wyscout_counts():
    """Event counts, minutes and position sums per player of the five leagues,
    cached in RAW."""
    cache = os.path.join(RAW, WY_CACHE)
    if os.path.exists(cache):
        return pd.read_csv(cache, index_col=0)
    paths = {k: fetch_url(WY_URL.format(fid), fname) for k, (fid, fname) in WY_FILES.items()}
    minutes, apps = Counter(), Counter()
    with zipfile.ZipFile(paths["matches"]) as zf:
        for lg in WY_LEAGUES:
            for m in json.load(zf.open(f"matches_{lg}.json")):
                for t in m["teamsData"].values():
                    f = t["formation"]
                    start = {p["playerId"]: 0 for p in f["lineup"]}
                    end = {}
                    for s in f["substitutions"] if isinstance(f["substitutions"], list) else []:
                        start[s["playerIn"]], end[s["playerOut"]] = s["minute"], s["minute"]
                    for p, s in start.items():
                        minutes[p] += max(end.get(p, 90) - s, 0)
                        apps[p] += 1
    cnt = defaultdict(Counter)
    with zipfile.ZipFile(paths["events"]) as zf:
        for lg in WY_LEAGUES:
            for e in json.load(zf.open(f"events_{lg}.json")):
                sid = 60 if e["eventId"] == 6 else e["subEventId"]
                if sid not in WY_SUB or not e["positions"]:
                    continue
                c, tags, p = cnt[e["playerId"]], {t["id"] for t in e["tags"]}, e["positions"][0]
                tz, lz = _zone(p)
                c[f"n|{sid}"] += 1
                c[f"n|{sid}|t{tz}"] += 1
                c[f"n|{sid}|l{lz}"] += 1
                c[f"n|{sid}|t{tz}l{lz}"] += 1
                c["n|all"] += 1
                c["x|sum"] += p["x"]
                c["y|sum"] += p["y"]
                for tag in (1801, 703):
                    if tag in tags:
                        c[f"{tag}|{sid}"] += 1
                        c[f"{tag}|{sid}|t{tz}"] += 1
                for tag in WY_TAGS:
                    if tag in tags:
                        c[f"tag|{tag}"] += 1
                if 1401 in tags and sid not in (12, 71):
                    c[f"int|t{tz}l{lz}"] += 1
                # Goals are tagged on the shot and on the goalkeeper's save attempt
                if 101 in tags:
                    c["goal|conceded" if sid in (90, 91) else "goal|scored"] += 1
                if sid == 100:
                    for tag in (401, 402, 403):
                        c[f"shot|{tag}"] += tag in tags
                    dx, dy = (100 - p["x"]) * WY_PITCH[0] / 100, (50 - p["y"]) * WY_PITCH[1] / 100
                    c["shot|dist"] += np.hypot(dx, dy)
                    c["shot|box"] += _in_box(p)
                if sid in WY_PASSES and len(e["positions"]) > 1:
                    q = e["positions"][1]
                    dx, dy = (q["x"] - p["x"]) * WY_PITCH[0] / 100, (q["y"] - p["y"]) * WY_PITCH[1] / 100
                    c["pass|n"] += 1
                    qt, ql = _zone(q)
                    c[f"pass|end|t{qt}l{ql}"] += 1
                    c["pass|len"] += np.hypot(dx, dy)
                    c["pass|gain"] += max(dx, 0)
                    c["pass|fwd"] += dx > 5
                    c["pass|back"] += dx < -5
                    c["pass|long"] += np.hypot(dx, dy) > 30
                    c["pass|final"] += p["x"] < 200 / 3 <= q["x"]
                    c["pass|box"] += _in_box(q) and not _in_box(p)
                    if 1801 in tags:
                        c["pass|final_acc"] += p["x"] < 200 / 3 <= q["x"]
                        c["pass|box_acc"] += _in_box(q) and not _in_box(p)
    out = pd.DataFrame.from_dict(cnt, orient="index").fillna(0)
    out["minutes"] = pd.Series(minutes).reindex(out.index).fillna(0)
    out["appearances"] = pd.Series(apps).reindex(out.index).fillna(0)
    out = out[out.index != 0]
    out.to_csv(cache)
    return out


def football_players_wyscout():
    c = _wyscout_counts()
    c = c[c.minutes >= WY_MIN_MINUTES]
    players = pd.DataFrame(json.load(open(fetch_url(WY_URL.format(WY_FILES["players"][0]),
                                                    WY_FILES["players"][1])))).set_index("wyId")
    c = c[c.index.isin(players.index)]
    g = lambda k: c[k] if k in c else pd.Series(0.0, index=c.index)  # noqa: E731
    per90 = 90 / c.minutes
    rate = lambda k: g(k) * per90  # noqa: E731
    out = {"minutes played": c.minutes, "matches played": c.appearances,
           "height (cm)": players.height.reindex(c.index).replace(0, np.nan)}
    for sid, name in WY_SUB.items():
        out[f"{name} per 90"] = rate(f"n|{sid}")
    for sid in WY_SPLIT:
        name = WY_SUB[sid]
        for i, t in enumerate(THIRDS):
            out[f"{name} in {t} per 90"] = rate(f"n|{sid}|t{i}")
        for i, lane in enumerate(LANE_NAMES):
            out[f"{name} {lane} per 90"] = rate(f"n|{sid}|l{i}")
    # Shares of all actions in each of the nine pitch zones, and per 90 by family
    for i, t in enumerate(THIRDS):
        for j, lane in enumerate(LANES):
            zone = sum(g(f"n|{s}|t{i}l{j}") for s in WY_SUB)
            out[f"actions in {t}, {lane} (%)"] = 100 * zone / c["n|all"]
            for fam, sids in WY_FAMILIES.items():
                out[f"{fam} in {t}, {lane} per 90"] = sum(g(f"n|{s}|t{i}l{j}") for s in sids) * per90
            out[f"passes ending in {t}, {lane} per 90"] = rate(f"pass|end|t{i}l{j}")
            # Defensive actions: defending duels, clearances and other actions
            # tagged as interceptions
            out[f"defending in {t}, {lane} per 90"] = (
                g(f"n|12|t{i}l{j}") + g(f"n|71|t{i}l{j}") + g(f"int|t{i}l{j}")) * per90
    # Success rates, defined when a player has at least 10 attempts
    for tag, names in ((1801, WY_ACCURATE), (703, WY_WON)):
        for sid, name in names.items():
            n = g(f"n|{sid}")
            out[f"{name} (%)"] = (100 * g(f"{tag}|{sid}") / n).where(n >= 10)
            for i, t in enumerate(THIRDS):
                n = g(f"n|{sid}|t{i}")
                out[f"{name}, {t} (%)"] = (100 * g(f"{tag}|{sid}|t{i}") / n).where(n >= 10)
            count_name = (f"{name} per 90" if tag == 703 or sid == 100 else f"accurate {WY_SUB[sid]} per 90")
            out[count_name] = rate(f"{tag}|{sid}")
            for i, t in enumerate(THIRDS):
                out[count_name.replace(" per 90", f" in {t} per 90")] = rate(f"{tag}|{sid}|t{i}")
    for tag, name in WY_TAGS.items():
        out[f"{name} per 90"] = rate(f"tag|{tag}")
    out.update({
        "goals per 90": rate("goal|scored"), "goals conceded per 90": rate("goal|conceded"),
        "left-foot shots per 90": rate("shot|401"), "right-foot shots per 90": rate("shot|402"),
        "headed shots per 90": rate("shot|403"), "shots inside the box per 90": rate("shot|box"),
        "shots outside the box per 90": rate("n|100") - rate("shot|box"),
        "average pass length (m)": g("pass|len") / g("pass|n"),
        "pass distance gained per 90 (m)": rate("pass|gain"),
        "forward passes (%)": 100 * g("pass|fwd") / g("pass|n"),
        "backward passes (%)": 100 * g("pass|back") / g("pass|n"),
        "passes over 30 m (%)": 100 * g("pass|long") / g("pass|n"),
        "passes into final third per 90": rate("pass|final"),
        "passes into the box per 90": rate("pass|box"),
        "accurate passes into final third per 90": rate("pass|final_acc"),
        "accurate passes into the box per 90": rate("pass|box_acc"),
        "actions per 90": rate("n|all"),
        "average position up the pitch (m)": c["x|sum"] / c["n|all"] * WY_PITCH[0] / 100,
        "average position from left touchline (m)": c["y|sum"] / c["n|all"] * WY_PITCH[1] / 100,
    })
    out = pd.DataFrame(out).replace([np.inf, -np.inf], np.nan)
    gk_only = [f"{WY_SUB[s]} per 90" for s in (91, 90, 40, 34, 81)] + ["goals conceded per 90"]
    # Features with values for at least 99% of players, non-zero for at least
    # 5% of them (goalkeeper actions kept), without constants and without one
    # of each pair with |r| > 0.98
    out = out.loc[:, (out.notna().mean() >= 0.99) & (((out > 0).mean() >= 0.05) | out.columns.isin(gk_only))]
    out = out.dropna()
    out = out.loc[:, out.nunique() > 1]
    # Goalkeeper actions are correlated through the goalkeepers' non-zero
    # values; they are considered first, so that saves are kept
    out = out[[c for c in gk_only if c in out] + [c for c in out if c not in gk_only]]
    r = out.corr().abs().values
    keep = []
    for i in range(r.shape[1]):
        if all(r[i, j] <= 0.98 for j in keep):
            keep.append(i)
    out = out.iloc[:, keep].round(3)
    out["position"] = players.role.reindex(out.index).map(lambda x: x["name"].lower())
    out = out.reset_index(drop=True)
    return (subsample(out), ["position"], ["position"],
            f"Wyscout soccer-logs 2017/18 (Pappalardo et al., 2019, Scientific Data 6:236, figshare collection "
            f"4415000, CC BY 4.0); {min(len(out), MAX_ROWS)} players of the English, French, German, Italian "
            f"and Spanish first divisions with at least {WY_MIN_MINUTES} minutes, event counts aggregated per player "
            f"(per 90 minutes, shares and success rates)")


# --- embedding --------------------------------------------------------------


def embedding_input(features, categorical, exclude):
    """Standardized numeric attributes (log1p first if positive and strongly
    right-skewed) and one-hot categorical attributes. Returns the matrix and
    the names of the log-transformed attributes."""
    blocks, logged = [], []
    for c in features.columns:
        if c in exclude:
            continue
        s = features[c]
        if c in categorical:
            blocks.append(pd.get_dummies(s, prefix=c, dtype=float).values)
            continue
        x = s.astype(float).values
        if x.min() >= 0 and skew(x) > SKEW_LOG:
            x = np.log1p(x)
            logged.append(c)
        sd = x.std()
        blocks.append(((x - x.mean()) / (sd if sd > 0 else 1.0))[:, None])
    return np.hstack(blocks).astype(np.float32), logged


def embed(x, method, params):
    if method == "tsne":
        import openTSNE
        return np.asarray(openTSNE.TSNE(metric="euclidean", random_state=RANDOM_STATE, n_jobs=1, **params).fit(x))
    import umap
    return umap.UMAP(metric="euclidean", random_state=RANDOM_STATE, **params).fit_transform(x)


def build():
    features, categorical, exclude, source = football_players_wyscout()
    out = os.path.join(DATA_DIR, NAME)
    os.makedirs(out, exist_ok=True)
    features.to_csv(os.path.join(out, "features.csv"), index=False, compression="gzip")
    x, logged = embedding_input(features, categorical, exclude)
    print(f"[{NAME}] {features.shape[0]} rows, {features.shape[1]} attributes, embedding input {x.shape[1]} columns",
          flush=True)

    variants = {}
    for variant, (method, params) in VARIANTS.items():
        emb = embed(x, method, params)
        if variant in ROTATE:
            emb = rotate(emb, ROTATE[variant])
        pd.DataFrame(emb).to_csv(os.path.join(out, f"embedding_{variant}.csv"), index=False, header=False)
        if variant == DEFAULT_VARIANT:
            pd.DataFrame(emb).to_csv(os.path.join(out, "embedding.csv"), index=False, header=False)
        variants[variant] = {"algorithm": method, "params": dict(params, random_state=RANDOM_STATE, metric="euclidean")}
        if variant in ROTATE:
            variants[variant]["rotated_clockwise_degrees"] = ROTATE[variant]
        print(f"[{NAME}]   {variant}", flush=True)

    meta = {
        "categorical_cols": categorical,
        "embedding": dict(variants[DEFAULT_VARIANT], variant=DEFAULT_VARIANT),
        "embedding_variants": variants,
        "embedding_input": {
            "excluded_cols": exclude,
            "log1p_cols": logged,
            "numeric": "standardized",
            "categorical": "one-hot",
        },
        "source": source,
    }
    with open(os.path.join(out, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    build()
