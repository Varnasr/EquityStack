"""Concentration indices: inequality in one variable, ranked by another.

The Gini asks how unequally consumption is spread. It cannot answer the question
an equity analyst actually has, which is whether *stunting*, or *institutional
delivery*, or *out-of-pocket health spending* falls more heavily on the poor,
and by how much. That needs two variables: the outcome, and a living-standards
rank to order people by.

The concentration index is the answer, and it is one line of arithmetic:

    CI = 2 · cov(h, r) / h̄

where ``h`` is the health or service variable and ``r`` is the weighted
fractional rank of the living-standards variable. It runs from -1 to +1.
**Negative means concentrated among the poor.** Stunting gives a negative index;
private hospital use gives a positive one. Zero means the outcome is spread
evenly across the distribution, which for a bad outcome is not good news, it is
an absence of a gradient.

Three things this module handles that a hand-rolled version usually does not.

**Bounded variables need a correction.** The index's theoretical range shrinks
as the mean of a binary variable moves away from 0.5, so a raw CI on an outcome
with 8 per cent prevalence cannot be compared with one at 60 per cent, and
comparing them across states or years is exactly what people do. Both standard
fixes are here: Erreygers (2009) and Wagstaff (2005). Say which you used.

**Ranks come from the living-standards variable, not the outcome.** Reversing
them is the commonest error and it produces a number in the right range with the
wrong meaning. The argument order here makes it hard: outcome first, then
``rank_by=``.

**A wealth quintile is a legitimate rank variable.** Ties get the block
midpoint, so 20 per cent of the population sitting on the integer 2 all rank at
0.3, which is what the World Bank's own DHS equity reports do. It is coarser
than a continuous consumption measure and the index is attenuated accordingly;
that is a property of the data, not a bug in the code.

References: O'Donnell, van Doorslaer, Wagstaff and Lindelow, *Analyzing Health
Equity Using Household Survey Data* (World Bank 2008), chapters 8 and 15;
Erreygers, "Correcting the concentration index", *Journal of Health Economics*
28(2), 2009, 504-515; Wagstaff, "The bounds of the concentration index when the
variable of interest is binary", *Health Economics* 14(4), 2005, 429-432.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .ranks import fractional_rank

__all__ = [
    "concentration_index", "erreygers_index", "wagstaff_index",
    "concentration_curve", "concentration_index_by", "achievement_index",
]


def _aligned(outcome, rank_by, weights):
    """Drop rows missing any of outcome, rank variable or weight, pairwise."""
    h = np.asarray(pd.to_numeric(pd.Series(outcome), errors="coerce"), dtype=float)
    x = np.asarray(pd.to_numeric(pd.Series(rank_by), errors="coerce"), dtype=float)
    if h.shape != x.shape:
        raise ValueError(
            f"outcome has {h.shape[0]} rows but rank_by has {x.shape[0]}")
    if weights is None:
        w = np.ones_like(h)
    else:
        w = np.asarray(pd.to_numeric(pd.Series(weights), errors="coerce"), dtype=float)
        if w.shape != h.shape:
            raise ValueError(
                f"outcome has {h.shape[0]} rows but weights has {w.shape[0]}")

    keep = np.isfinite(h) & np.isfinite(x) & np.isfinite(w)
    h, x, w = h[keep], x[keep], w[keep]
    if h.size == 0:
        raise ValueError("no rows left after dropping missing values")
    if np.any(w < 0):
        raise ValueError("negative weights are not a thing; check the weight column")
    if w.sum() <= 0:
        raise ValueError("weights sum to zero, so nothing can be estimated")
    return h, x, w


def concentration_index(outcome, rank_by, weights=None) -> float:
    """Concentration index of ``outcome`` over the ranking of ``rank_by``.

    Parameters
    ----------
    outcome
        The health, service or spending variable. Binary is fine and common.
    rank_by
        The living-standards variable people are ordered by: a consumption
        aggregate, a wealth index, or a quintile. Higher must mean better off.
    weights
        Survey weights. Relative or absolute, it makes no difference.

    Returns a number in [-1, 1]. Negative: concentrated among the poor.

    >>> # an outcome that falls entirely on the poorest gives a strong negative
    >>> round(concentration_index([1, 0, 0, 0], rank_by=[1, 2, 3, 4]), 4)
    -0.75
    """
    h, x, w = _aligned(outcome, rank_by, weights)
    mean = np.sum(w * h) / np.sum(w)
    if mean == 0:
        raise ValueError(
            "concentration_index: the weighted mean of the outcome is zero, so the "
            "index is undefined. Nobody in the sample has the outcome.")
    r = fractional_rank(x, w)
    return float(2.0 * np.sum(w * h * r) / (np.sum(w) * mean) - 1.0)


def erreygers_index(outcome, rank_by, weights=None, *,
                    bounds: tuple[float, float] = (0.0, 1.0)) -> float:
    """Erreygers-corrected concentration index, comparable across prevalences.

    ``E = 4 · μ / (b − a) · CI``, where ``(a, b)`` are the variable's true
    bounds. For a binary outcome the default (0, 1) is right and ``E = 4 μ CI``.

    Use this when comparing the same indicator across states, years or surveys
    whose mean differs. Two states can have identical raw concentration indices
    and very different absolute gradients, and it is the absolute gradient that
    a programme budget responds to.
    """
    a, b = bounds
    if not b > a:
        raise ValueError("erreygers_index: bounds must satisfy b > a")
    h, x, w = _aligned(outcome, rank_by, weights)
    lo, hi = np.nanmin(h), np.nanmax(h)
    if lo < a - 1e-12 or hi > b + 1e-12:
        raise ValueError(
            f"erreygers_index: the outcome runs [{lo:g}, {hi:g}], outside the stated "
            f"bounds [{a:g}, {b:g}]. The correction is meaningless on the wrong bounds.")
    mean = np.sum(w * h) / np.sum(w)
    ci = concentration_index(h, x, w)
    return float(4.0 * mean / (b - a) * ci)


def wagstaff_index(outcome, rank_by, weights=None, *, upper: float = 1.0) -> float:
    """Wagstaff-normalised concentration index for a bounded variable.

    ``W = CI / (1 − μ/b)``. Defined for a variable on [0, b]; undefined when the
    mean reaches the upper bound, because then no inequality is possible and the
    denominator is zero.

    Erreygers and Wagstaff answer different normative questions and disagree,
    sometimes about direction of change over time. Erreygers keeps absolute
    differences comparable; Wagstaff keeps relative ones. Pick one, state it,
    and do not switch between them inside a single table.
    """
    if upper <= 0:
        raise ValueError("wagstaff_index: upper must be positive")
    h, x, w = _aligned(outcome, rank_by, weights)
    if np.nanmin(h) < -1e-12 or np.nanmax(h) > upper + 1e-12:
        raise ValueError(
            f"wagstaff_index: the outcome falls outside [0, {upper:g}]")
    mean = np.sum(w * h) / np.sum(w)
    denom = 1.0 - mean / upper
    if abs(denom) < 1e-12:
        raise ValueError(
            "wagstaff_index: the mean equals the upper bound, so the normalisation "
            "divides by zero. Everyone has the outcome; there is no gradient to scale.")
    return float(concentration_index(h, x, w) / denom)


def concentration_curve(outcome, rank_by, weights=None) -> pd.DataFrame:
    """Points on the concentration curve, poorest to richest.

    Cumulative share of the outcome against cumulative share of the population
    ranked by living standards. Above the 45 degree line means concentrated
    among the poor.

    Sign convention, since it is the easy thing to get backwards: with ``A`` the
    area under the curve, ``CI = 2 · (0.5 − A)``. A curve above the line has
    ``A > 0.5`` and a negative index. `test_inequality.py` checks that identity
    by trapezoid against `concentration_index`.

    One row per distinct value of the rank variable, plus the origin, so a
    wealth quintile gives six rows.
    """
    h, x, w = _aligned(outcome, rank_by, weights)
    if np.any(h < 0):
        raise ValueError("concentration_curve: a negative outcome makes the curve non-monotone")
    order = np.argsort(x, kind="mergesort")
    sh, sx, sw = h[order], x[order], w[order]

    starts = np.concatenate(([True], sx[1:] != sx[:-1]))
    group = np.cumsum(starts) - 1
    gw = np.zeros(group[-1] + 1)
    gh = np.zeros(group[-1] + 1)
    np.add.at(gw, group, sw)
    np.add.at(gh, group, sw * sh)

    total_h = gh.sum()
    pop = np.concatenate(([0.0], np.cumsum(gw) / gw.sum()))
    val = np.concatenate(([0.0], np.cumsum(gh) / total_h)) if total_h > 0 else pop.copy()
    return pd.DataFrame({"population_share": pop, "outcome_share": val,
                         "rank_value": np.concatenate(([np.nan], sx[starts]))})


def concentration_index_by(df: pd.DataFrame, outcome: str, rank_by: str, *,
                           by: str, weights: str | None = None,
                           bounds: tuple[float, float] = (0.0, 1.0)) -> pd.DataFrame:
    """One concentration index per group, with the mean and Erreygers alongside.

    The usual table: an equity gradient per state, per survey round, per sex.
    Groups whose index cannot be computed (nobody has the outcome, one row, no
    variation in the rank variable) come back with NaN and a stated ``note``
    rather than being dropped, so a state missing from the output is visible.

    **Each group is ranked within itself.** A state's index answers "is this
    unequal *within* this state", not "are people in this state poor relative to
    India". Those are different questions and pooling the rank would answer the
    second while looking like the first.
    """
    for col in (outcome, rank_by, by) + ((weights,) if weights else ()):
        if col not in df.columns:
            raise KeyError(f"concentration_index_by: no column {col!r} in the frame")

    rows = []
    for key, g in df.groupby(by, dropna=False, observed=True):
        w = g[weights] if weights else None
        note = ""
        ci = erre = mean = np.nan
        try:
            h, x, ww = _aligned(g[outcome], g[rank_by], w)
            mean = float(np.sum(ww * h) / np.sum(ww))
            if len(np.unique(x)) < 2:
                note = "the rank variable takes one value in this group"
            elif mean == 0:
                note = "nobody in this group has the outcome"
            else:
                ci = concentration_index(h, x, ww)
                erre = 4.0 * mean / (bounds[1] - bounds[0]) * ci
        except ValueError as exc:
            note = str(exc)
        rows.append({by: key, "n": len(g), "mean": mean,
                     "concentration_index": ci, "erreygers": erre, "note": note})
    return pd.DataFrame(rows)


def achievement_index(outcome, rank_by, weights=None, *, v: float = 2.0) -> float:
    """Wagstaff's achievement index: the mean, discounted for how unequal it is.

    ``A = μ · (1 − CI)`` at the usual inequality aversion of ``v = 2``. It
    collapses level and distribution into one number, so a programme that raises
    coverage only among the better-off scores worse than its headline coverage
    suggests.

    Reported alongside the mean, never instead of it. A single number that mixes
    level and distribution cannot be read backwards into either.
    """
    if v < 1:
        raise ValueError("achievement_index: v must be at least 1")
    h, x, w = _aligned(outcome, rank_by, weights)
    mean = float(np.sum(w * h) / np.sum(w))
    if mean == 0:
        return 0.0
    r = fractional_rank(x, w)
    weight = v * (1.0 - r) ** (v - 1.0)
    return float(np.sum(w * weight * h) / np.sum(w))
