"""Weighted fractional ranks, the shared foundation of every index here.

Almost every distributional statistic in this package is a covariance between a
variable and somebody's *position* in a distribution. The position is a weighted
fractional rank: the share of the population poorer than you, plus half your own
share. Get this wrong and the Gini coefficient, the concentration index and the
Lorenz curve are all wrong together, in ways that look plausible.

Two decisions are made here rather than in each index.

**Ties take the midpoint of the tie group.** If four hundred households sit in
wealth quintile 2, every one of them gets the same rank: the midpoint of the
block of population that quintile 2 occupies. The alternative, breaking ties by
row order, silently makes the answer depend on how the file was sorted, and
wealth quintiles are exactly the kind of coarse variable this package is pointed
at. Stata's `conindex` and the World Bank's ADePT do the same thing.

**Weights are relative, not absolute.** Everything divides by the total weight,
so a DHS `v005` normalised to average one and a PLFS multiplier expanding to
1.4 billion give the same answer. That is the property that lets these functions
be handed either without a footnote.

The midpoint rank has one arithmetic property worth stating, because three
proofs downstream lean on it: the weighted mean rank is exactly 0.5, for any
weights and any pattern of ties. `test_inequality.py` asserts it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["fractional_rank", "prepare", "weighted_mean"]


def prepare(values, weights=None, *, name: str = "values"):
    """Coerce a value/weight pair to clean float arrays, dropping missing rows.

    Returns ``(values, weights)`` with any row missing either one removed. A
    missing value is not a zero: a household that did not report consumption is
    absent from the distribution, and treating it as destitute would push every
    inequality measure up. Rows are dropped pairwise and the caller can compare
    lengths if it needs to report how many.

    Raises on a negative weight, on a weight total of zero, and on an empty
    result, because each of those produces a number rather than an error further
    down.
    """
    v = np.asarray(pd.to_numeric(pd.Series(values), errors="coerce"), dtype=float)
    if weights is None:
        w = np.ones_like(v, dtype=float)
    else:
        w = np.asarray(pd.to_numeric(pd.Series(weights), errors="coerce"), dtype=float)
        if w.shape != v.shape:
            raise ValueError(
                f"{name} has {v.shape[0]} rows but weights has {w.shape[0]}")

    keep = np.isfinite(v) & np.isfinite(w)
    v, w = v[keep], w[keep]

    if v.size == 0:
        raise ValueError(f"{name}: no rows left after dropping missing values")
    if np.any(w < 0):
        raise ValueError(f"{name}: negative weights are not a thing; check the weight column")
    total = w.sum()
    if total <= 0:
        raise ValueError(f"{name}: weights sum to {total}, so nothing can be estimated")
    return v, w


def weighted_mean(values, weights=None) -> float:
    """Weighted arithmetic mean, with missing rows dropped pairwise."""
    v, w = prepare(values, weights)
    return float(np.sum(v * w) / np.sum(w))


def fractional_rank(values, weights=None) -> np.ndarray:
    """Weighted fractional rank in [0, 1], ties sharing the group midpoint.

    For observation *i* the rank is the population share strictly poorer than
    *i*, plus half the share at *i*'s own value. Returned in the caller's row
    order, so it can be assigned straight back onto a data frame column.

    Missing values rank as NaN rather than sorting to one end, which is the
    behaviour you want when the living-standards variable has gaps: those rows
    then fall out of the covariance instead of being counted as poorest.

    >>> fractional_rank([1, 2, 3, 4, 5]).round(2)
    array([0.1, 0.3, 0.5, 0.7, 0.9])
    >>> fractional_rank([1, 1, 2]).round(4)          # the tie shares a rank
    array([0.3333, 0.3333, 0.8333])
    """
    v = np.asarray(pd.to_numeric(pd.Series(values), errors="coerce"), dtype=float)
    if weights is None:
        w = np.ones_like(v, dtype=float)
    else:
        w = np.asarray(pd.to_numeric(pd.Series(weights), errors="coerce"), dtype=float)
    ok = np.isfinite(v) & np.isfinite(w)
    if not ok.any():
        raise ValueError("fractional_rank: every row is missing a value or a weight")
    if np.any(w[ok] < 0):
        raise ValueError("fractional_rank: negative weights are not a thing")

    out = np.full(v.shape, np.nan, dtype=float)
    vv, ww = v[ok], w[ok]
    total = ww.sum()
    if total <= 0:
        raise ValueError("fractional_rank: weights sum to zero")

    order = np.argsort(vv, kind="mergesort")     # stable, so ties keep input order
    sv, sw = vv[order], ww[order]

    cum_before = np.concatenate(([0.0], np.cumsum(sw)[:-1]))

    # Collapse ties: every row sharing a value gets the midpoint of the whole
    # block that value occupies, so the answer cannot depend on row order.
    starts = np.concatenate(([True], sv[1:] != sv[:-1]))
    group = np.cumsum(starts) - 1
    block_start = cum_before[starts]              # weight strictly below each value
    block_weight = np.zeros(group[-1] + 1)
    np.add.at(block_weight, group, sw)            # total weight sharing each value

    ranks_sorted = (block_start[group] + block_weight[group] / 2.0) / total

    inv = np.empty_like(order)
    inv[order] = np.arange(order.size)
    out[ok] = ranks_sorted[inv]
    return out
