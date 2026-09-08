"""Composite indices: combining several indicators into one score, defensibly.

Every access index, vulnerability index and readiness index is the same three
decisions, and almost every published one leaves at least two of them implicit:

1. **Direction.** Infant mortality and immunisation coverage both measure child
   health, and they point opposite ways. Averaging them raw cancels the signal.
2. **Normalisation.** Indicators arrive in incompatible units: a rate per
   thousand, a percentage, a rupee figure. How you put them on a common scale
   decides the answer, and min-max, z-score and goalpost give different
   rankings on the same data.
3. **Weights.** Equal weighting is a choice, not the absence of one. It says a
   percentage point of literacy is worth a percentage point of piped water.

This module makes all three arguments rather than assumptions, records what was
chosen on the result, and refuses the combinations that produce a number
somebody will quote and nobody can defend.

The predecessor of this file computed ``df[cols].mean(axis=1)`` and called the
result an access index. That is min-max-free, direction-free, weight-free, and
it silently ranks a district by whichever of its indicators happens to be
measured on the largest scale.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["normalise", "composite_index", "rank_sensitivity"]

_METHODS = ("minmax", "zscore", "goalpost", "rank")


def normalise(series, *, method: str = "minmax", direction: str = "higher_is_better",
              goalposts: tuple[float, float] | None = None) -> pd.Series:
    """Put one indicator on a common 0-1 scale (or a z-score).

    Parameters
    ----------
    method
        ``minmax``   rescales to [0, 1] using the observed range. Simple, and
                     the answer moves when you add a new district, so a series
                     of annual indices built this way is not comparable
                     year to year.
        ``zscore``   standardises to mean 0, sd 1. Keeps relative distances,
                     unbounded, and sensitive to outliers.
        ``goalpost`` rescales against fixed minimum and maximum values you
                     supply, the way the UNDP's Human Development Index does.
                     The only one of the four that is comparable across time
                     and across samples, because the scale does not depend on
                     the data in hand.
        ``rank``     replaces values with their fractional rank. Throws away
                     magnitude, immune to outliers and to skew.
    direction
        ``higher_is_better`` or ``lower_is_better``. For a mortality rate or a
        distance to the nearest facility, use the latter and the series is
        flipped so that a high score always means a good outcome.

    Returns a Series aligned to the input, NaN preserved.
    """
    if method not in _METHODS:
        raise ValueError(f"normalise: method must be one of {_METHODS}")
    if direction not in ("higher_is_better", "lower_is_better"):
        raise ValueError("normalise: direction must be 'higher_is_better' or 'lower_is_better'")

    s = pd.to_numeric(pd.Series(series), errors="coerce").astype(float)
    if s.notna().sum() == 0:
        raise ValueError("normalise: the indicator is entirely missing")

    if method == "goalpost":
        if goalposts is None:
            raise ValueError(
                "normalise: method='goalpost' needs explicit goalposts. That is the "
                "point of it: the scale must not depend on the sample, or the index "
                "is not comparable with the same index computed next year.")
        lo, hi = goalposts
        if not hi > lo:
            raise ValueError("normalise: goalposts must satisfy max > min")
        out = (s - lo) / (hi - lo)
        out = out.clip(0.0, 1.0)
    elif method == "minmax":
        lo, hi = s.min(), s.max()
        if hi == lo:
            out = pd.Series(np.where(s.notna(), 0.5, np.nan), index=s.index)
        else:
            out = (s - lo) / (hi - lo)
    elif method == "zscore":
        sd = s.std(ddof=0)
        out = (s - s.mean()) / sd if sd > 0 else pd.Series(
            np.where(s.notna(), 0.0, np.nan), index=s.index)
    else:  # rank
        out = s.rank(pct=True, na_option="keep")

    if direction == "lower_is_better":
        out = -out if method == "zscore" else 1.0 - out
    return out


def composite_index(df: pd.DataFrame, indicators, *, method: str = "minmax",
                    weights: dict | None = None,
                    directions: dict | None = None,
                    goalposts: dict | None = None,
                    aggregation: str = "arithmetic",
                    min_indicators: int | None = None,
                    name: str = "index") -> pd.DataFrame:
    """Combine indicators into one score, keeping every choice on the record.

    Parameters
    ----------
    indicators
        Column names to combine.
    weights
        ``{column: weight}``. Rescaled to sum to 1, so relative sizes are what
        matter. Omitted columns get the residual share equally. Default: equal.
    directions
        ``{column: 'lower_is_better'}`` for any indicator where a high value is
        a bad outcome. Anything unlisted is treated as higher-is-better.
    aggregation
        ``arithmetic`` for a weighted mean: indicators substitute freely, so a
        district can offset no piped water with excellent schools.
        ``geometric`` for a weighted geometric mean: they substitute poorly, so
        a near-zero on any one component drags the whole index down. The UNDP
        moved the HDI to geometric in 2010 for exactly that reason, and for an
        *access* index it is usually the more honest choice, because a household
        with no clinic within 40 km is not compensated by a nearby school.
    min_indicators
        Rows with fewer than this many non-missing indicators get NaN rather
        than a score built from whatever happened to be present. Defaults to
        all of them. This matters more than it sounds: a district reporting two
        of six indicators, both good, otherwise scores near the top.

    Returns the input frame with the score, the rank, and a per-indicator
    normalised column appended. The choices are recorded in ``.attrs`` so a
    saved result carries its own method statement.
    """
    indicators = list(indicators)
    missing = [c for c in indicators if c not in df.columns]
    if missing:
        raise KeyError(f"composite_index: no column(s) {missing} in the frame")
    if len(indicators) < 2:
        raise ValueError("composite_index: combining fewer than two indicators is not an index")
    if aggregation not in ("arithmetic", "geometric"):
        raise ValueError("composite_index: aggregation must be 'arithmetic' or 'geometric'")

    directions = dict(directions or {})
    goalposts = dict(goalposts or {})
    bad = set(directions) - set(indicators)
    if bad:
        raise KeyError(f"composite_index: directions names column(s) not in indicators: {sorted(bad)}")

    if weights is None:
        w = {c: 1.0 / len(indicators) for c in indicators}
    else:
        bad = set(weights) - set(indicators)
        if bad:
            raise KeyError(f"composite_index: weights names column(s) not in indicators: {sorted(bad)}")
        if any(v < 0 for v in weights.values()):
            raise ValueError("composite_index: negative weights")
        named = sum(weights.values())
        if named <= 0:
            raise ValueError("composite_index: weights sum to zero")
        rest = [c for c in indicators if c not in weights]
        if rest:
            residual = max(0.0, 1.0 - named)
            if residual == 0:
                raise ValueError(
                    f"composite_index: the named weights already sum to {named:g}, leaving "
                    f"nothing for {rest}. Name every indicator, or leave weights as None.")
            w = {**weights, **{c: residual / len(rest) for c in rest}}
        else:
            w = dict(weights)
        total = sum(w.values())
        w = {k: v / total for k, v in w.items()}

    out = df.copy()
    norm_cols = []
    for c in indicators:
        col = f"{c}__norm"
        out[col] = normalise(df[c], method=method,
                             direction=directions.get(c, "higher_is_better"),
                             goalposts=goalposts.get(c))
        norm_cols.append(col)

    normed = out[norm_cols]
    present = normed.notna().sum(axis=1)
    required = len(indicators) if min_indicators is None else min_indicators
    if required > len(indicators):
        raise ValueError("composite_index: min_indicators exceeds the number of indicators")

    wvec = np.array([w[c] for c in indicators])
    mask = normed.notna().to_numpy()
    vals = normed.to_numpy(dtype=float)

    # Reweight over the indicators actually present in each row, so a row with a
    # gap is scored on the same 0-1 scale rather than being pushed down.
    eff = np.where(mask, wvec, 0.0)
    denom = eff.sum(axis=1)

    if aggregation == "arithmetic":
        score = np.where(denom > 0, np.nansum(np.where(mask, vals * wvec, 0.0), axis=1) / denom, np.nan)
    else:
        if method == "zscore":
            raise ValueError(
                "composite_index: a geometric mean of z-scores is undefined, because "
                "half of them are negative. Use method='minmax', 'goalpost' or 'rank'.")
        floor = 1e-9   # a true zero would send the whole index to zero
        logv = np.where(mask, np.log(np.clip(vals, floor, None)), 0.0)
        score = np.where(denom > 0, np.exp(np.nansum(logv * eff, axis=1) / denom), np.nan)

    score = np.where(present.to_numpy() >= required, score, np.nan)
    out[name] = score
    out[f"{name}_rank"] = pd.Series(score, index=out.index).rank(ascending=False, method="min")
    out[f"{name}_n_indicators"] = present

    out.attrs["composite_index"] = {
        "indicators": indicators, "weights": w, "method": method,
        "aggregation": aggregation, "directions": directions,
        "goalposts": goalposts, "min_indicators": required,
    }
    return out


def rank_sensitivity(df: pd.DataFrame, indicators, *, unit: str,
                     methods=("minmax", "zscore", "rank"),
                     aggregations=("arithmetic", "geometric"),
                     **kwargs) -> pd.DataFrame:
    """How much the ranking moves when the normalisation choice moves.

    Run this before publishing any index. A district whose rank swings from 3rd
    to 24th depending on whether you min-max or z-score has not been measured,
    it has been assigned, and the sensible thing is to report a band rather than
    a position. Composite indices get quoted as facts and the arbitrariness in
    them is invisible once the number is in a headline.

    Returns one row per unit with the rank under each combination, plus the
    spread. ``zscore`` is skipped for the geometric aggregation, where it is
    undefined.
    """
    if unit not in df.columns:
        raise KeyError(f"rank_sensitivity: no column {unit!r} in the frame")
    ranks = pd.DataFrame({unit: df[unit].to_numpy()})
    for m in methods:
        for a in aggregations:
            if a == "geometric" and m == "zscore":
                continue
            r = composite_index(df, indicators, method=m, aggregation=a, **kwargs)
            ranks[f"{m}_{a}"] = r["index_rank"].to_numpy()
    cols = [c for c in ranks.columns if c != unit]
    ranks["best_rank"] = ranks[cols].min(axis=1)
    ranks["worst_rank"] = ranks[cols].max(axis=1)
    ranks["rank_spread"] = ranks["worst_rank"] - ranks["best_rank"]
    return ranks.sort_values("rank_spread", ascending=False).reset_index(drop=True)
