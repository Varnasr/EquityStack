"""Summary measures of inequality in a continuous variable, survey-weighted.

Consumption, income, land, a school-quality score: anything where the question
is how unequally the total is spread. Every function here takes weights, drops
missing rows pairwise, and is scale invariant, so the answer does not depend on
whether the variable is in rupees, thousands of rupees or 2011 PPP dollars.

Which measure to reach for, since they are not interchangeable:

- **Gini** for the headline. Comparable with almost every published figure,
  and most sensitive around the middle of the distribution.
- **Theil (GE(1)) or mean log deviation (GE(0))** when the question is *where*
  inequality sits, because both decompose exactly into a within-group and a
  between-group part. `decomposition.theil_decomposition` does that.
- **Atkinson** when you want to state the aversion to inequality explicitly
  rather than let the index choose one for you. A(0.5) and A(2) answer
  different normative questions about the same data.
- **Palma and the 80/20 ratio** when the audience is not technical. Both are
  ratios of shares, so they are read off a table without a formula.

None of these say anything about *who* is where. For that, an inequality
measure has to be crossed with a living-standards rank, which is the
concentration index in `concentration.py`.

Sources for the definitions: Cowell, *Measuring Inequality* (3rd edn, OUP 2011),
chapters 2 and 3; Haughton and Khandker, *Handbook on Poverty and Inequality*
(World Bank 2009), chapter 6.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .ranks import fractional_rank, prepare

__all__ = [
    "gini", "lorenz_curve", "share_of_top", "share_of_bottom", "quantile_shares",
    "palma_ratio", "ratio_80_20", "generalised_entropy", "theil_t", "theil_l",
    "atkinson", "weighted_quantile",
]


def gini(values, weights=None, *, small_sample_correction: bool = False) -> float:
    """Gini coefficient, 0 at perfect equality and 1 at perfect concentration.

    Computed as ``2 · cov(y, F(y)) / ȳ`` using midpoint fractional ranks, which
    is the population (not sample) Gini and matches the mean-difference
    definition ``Δ / 2ȳ`` exactly.

    Parameters
    ----------
    small_sample_correction
        Multiply by ``n / (n - 1)``. The population formula is biased downward
        in a small sample. Leave it off to compare against published national
        figures, which are almost always uncorrected; turn it on for a survey of
        a few dozen units where the bias is not negligible. With weights, *n* is
        the number of rows, not the weighted total.

    Negative values raise. A Gini on a variable that can go negative (net income
    after debt, farm profit in a bad year) is not bounded by 1 and is not
    comparable with anything; the fix is a decision about the data, not a
    silently different formula.

    >>> round(gini([1, 2, 3, 4, 5]), 6)
    0.266667
    >>> round(gini([10, 10, 10]), 12)
    0.0
    """
    v, w = prepare(values, weights, name="gini")
    if np.any(v < 0):
        raise ValueError(
            "gini: the variable contains negative values. The Gini is not bounded "
            "by 1 on a variable that can go negative, and the result would not be "
            "comparable with any published figure. Decide what a negative means "
            "(censor at zero, drop, or use a different measure) before calling this.")
    mean = np.sum(v * w) / np.sum(w)
    if mean == 0:
        return 0.0
    r = fractional_rank(v, w)
    g = 2.0 * np.sum(w * v * r) / (np.sum(w) * mean) - 1.0
    if small_sample_correction:
        n = v.size
        if n < 2:
            raise ValueError("gini: the small-sample correction needs at least 2 rows")
        g *= n / (n - 1)
    return float(g)


def lorenz_curve(values, weights=None) -> pd.DataFrame:
    """Points on the Lorenz curve: cumulative population share against value share.

    Returns a frame with ``population_share`` and ``value_share``, opening with
    the origin (0, 0) and closing at (1, 1), ordered from poorest to richest.
    One row per distinct value, so a wealth-quintile variable gives six rows
    rather than a row per household.

    The area between this curve and the 45 degree line is half the Gini, which
    `test_inequality.py` checks by trapezoid against `gini` directly.
    """
    v, w = prepare(values, weights, name="lorenz_curve")
    if np.any(v < 0):
        raise ValueError("lorenz_curve: negative values make the curve non-monotone")
    order = np.argsort(v, kind="mergesort")
    sv, sw = v[order], w[order]

    starts = np.concatenate(([True], sv[1:] != sv[:-1]))
    group = np.cumsum(starts) - 1
    gw = np.zeros(group[-1] + 1)
    gv = np.zeros(group[-1] + 1)
    np.add.at(gw, group, sw)
    np.add.at(gv, group, sw * sv)

    total_w, total_v = gw.sum(), gv.sum()
    pop = np.concatenate(([0.0], np.cumsum(gw) / total_w))
    val = np.concatenate(([0.0], np.cumsum(gv) / total_v)) if total_v > 0 else pop.copy()
    return pd.DataFrame({"population_share": pop, "value_share": val})


def _share(values, weights, lower: float, upper: float) -> float:
    """Share of the total held by the population between two rank cut-points.

    The cut-point almost never falls on a row boundary once weights are
    involved, so the marginal row is split proportionally rather than assigned
    whole to one side. Assigning it whole is the usual shortcut and it makes the
    top-decile share jump around when a single large-weight household crosses
    the line.
    """
    v, w = prepare(values, weights, name="share")
    order = np.argsort(v, kind="mergesort")
    sv, sw = v[order], w[order]
    total_w = sw.sum()
    total_v = np.sum(sv * sw)
    if total_v == 0:
        return 0.0

    cum = np.cumsum(sw) / total_w
    start = np.concatenate(([0.0], cum[:-1]))
    frac = np.clip((np.minimum(cum, upper) - np.maximum(start, lower))
                   / np.where(cum - start > 0, cum - start, 1.0), 0.0, 1.0)
    return float(np.sum(frac * sw * sv) / total_v)


def share_of_top(values, weights=None, *, p: float = 0.10) -> float:
    """Share of the total held by the richest ``p`` of the population."""
    if not 0 < p <= 1:
        raise ValueError("share_of_top: p must be in (0, 1]")
    return _share(values, weights, 1.0 - p, 1.0)


def share_of_bottom(values, weights=None, *, p: float = 0.40) -> float:
    """Share of the total held by the poorest ``p`` of the population."""
    if not 0 < p <= 1:
        raise ValueError("share_of_bottom: p must be in (0, 1]")
    return _share(values, weights, 0.0, p)


def quantile_shares(values, weights=None, *, q: int = 5) -> pd.DataFrame:
    """Share of the total held by each equal-sized population group.

    ``q=5`` gives quintiles, ``q=10`` deciles. Groups are equal shares of
    *population*, cut with the marginal observation split, so the shares sum to
    exactly 1 whatever the weights look like.
    """
    if q < 2:
        raise ValueError("quantile_shares: q must be at least 2")
    edges = np.linspace(0, 1, q + 1)
    rows = [{"group": i + 1,
             "population_share": edges[i + 1] - edges[i],
             "value_share": _share(values, weights, edges[i], edges[i + 1])}
            for i in range(q)]
    out = pd.DataFrame(rows)
    out["ratio_to_equal_share"] = out["value_share"] * q
    return out


def palma_ratio(values, weights=None) -> float:
    """Richest 10 per cent's share divided by the poorest 40 per cent's.

    Gabriel Palma's observation is that the middle five deciles take a stable
    half of national income almost everywhere, so the distributional fight is
    between the top decile and the bottom four. At perfect equality the ratio is
    0.25; India's is usually reported somewhere above 1.5.
    """
    bottom = share_of_bottom(values, weights, p=0.40)
    if bottom == 0:
        return float("inf")
    return share_of_top(values, weights, p=0.10) / bottom


def ratio_80_20(values, weights=None) -> float:
    """Richest fifth's share over the poorest fifth's (Eurostat's S80/S20)."""
    bottom = share_of_bottom(values, weights, p=0.20)
    if bottom == 0:
        return float("inf")
    return share_of_top(values, weights, p=0.20) / bottom


def generalised_entropy(values, weights=None, *, alpha: float = 1.0) -> float:
    """Generalised entropy index GE(α).

    ``alpha`` sets where the index is sensitive. GE(0), the mean log deviation,
    weights the bottom of the distribution; GE(1), Theil's T, is neutral;
    GE(2), half the squared coefficient of variation, weights the top. Only
    GE(0) and GE(1) decompose additively into within and between components,
    which is why those two have their own names below.

    Zero and negative values raise for α ≤ 1, where the logarithm or the
    negative power is undefined. That is a real constraint on consumption data
    with zeros in it, and it is better as an error than as a NaN in a table.
    """
    v, w = prepare(values, weights, name="generalised_entropy")
    mean = np.sum(v * w) / np.sum(w)
    if mean <= 0:
        raise ValueError("generalised_entropy: the weighted mean must be positive")
    if alpha <= 1 and np.any(v <= 0):
        raise ValueError(
            f"generalised_entropy: GE({alpha:g}) is undefined where the variable is "
            "zero or negative. Either drop those rows and say so, or use alpha > 1.")
    if np.any(v < 0):
        raise ValueError("generalised_entropy: negative values are undefined here")

    p = w / np.sum(w)
    ratio = v / mean
    if np.isclose(alpha, 0.0):
        return float(np.sum(p * np.log(1.0 / ratio)))
    if np.isclose(alpha, 1.0):
        with np.errstate(divide="ignore", invalid="ignore"):
            term = np.where(ratio > 0, ratio * np.log(ratio), 0.0)
        return float(np.sum(p * term))
    return float(np.sum(p * (ratio ** alpha - 1.0)) / (alpha * (alpha - 1.0)))


def theil_t(values, weights=None) -> float:
    """Theil's T index, GE(1). Decomposes by income share."""
    return generalised_entropy(values, weights, alpha=1.0)


def theil_l(values, weights=None) -> float:
    """Mean log deviation, GE(0), sometimes Theil's L. Decomposes by population share."""
    return generalised_entropy(values, weights, alpha=0.0)


def atkinson(values, weights=None, *, epsilon: float = 1.0) -> float:
    """Atkinson index at inequality aversion ``epsilon``.

    Reads as a fraction of total income society would be willing to give up to
    have the remainder distributed equally. A(0) is 0 by construction: no
    aversion, no cost. A(2) is the usual high-aversion figure. The index is
    weakly increasing in ``epsilon``, which `test_inequality.py` checks.

    Undefined at ``epsilon`` ≥ 1 with any zero in the data: one destitute
    household drives the equally-distributed-equivalent income to zero and the
    index to 1, correctly but uninformatively. That case raises.
    """
    if epsilon < 0:
        raise ValueError("atkinson: epsilon must be non-negative")
    v, w = prepare(values, weights, name="atkinson")
    if np.any(v < 0):
        raise ValueError("atkinson: negative values are undefined here")
    mean = np.sum(v * w) / np.sum(w)
    if mean <= 0:
        raise ValueError("atkinson: the weighted mean must be positive")
    if epsilon >= 1 and np.any(v <= 0):
        raise ValueError(
            f"atkinson: at epsilon = {epsilon:g} a single zero forces the index to 1. "
            "Drop or censor the zeros and say which you did.")

    p = w / np.sum(w)
    ratio = v / mean
    if np.isclose(epsilon, 0.0):
        return 0.0
    if np.isclose(epsilon, 1.0):
        return float(1.0 - np.exp(np.sum(p * np.log(ratio))))
    ede = np.sum(p * ratio ** (1.0 - epsilon)) ** (1.0 / (1.0 - epsilon))
    return float(1.0 - ede)


def weighted_quantile(values, q, weights=None) -> float:
    """Value at weighted quantile ``q``, interpolated on the midpoint rank.

    Used for cut-points (a poverty line at the 20th percentile, a top-decile
    threshold). Consistent with `fractional_rank`, so a household at the
    returned value has rank ``q`` by this package's definition rather than by
    numpy's, which handles ties and weights differently.
    """
    if not 0 <= q <= 1:
        raise ValueError("weighted_quantile: q must be in [0, 1]")
    v, w = prepare(values, weights, name="weighted_quantile")
    order = np.argsort(v, kind="mergesort")
    sv, sw = v[order], w[order]
    cum = (np.cumsum(sw) - 0.5 * sw) / sw.sum()
    return float(np.interp(q, cum, sv))
