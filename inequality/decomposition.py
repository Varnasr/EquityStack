"""Decompositions: where inequality sits, and how much of a gap is explained.

Two questions a summary index cannot answer.

*Where does the inequality sit?* A national Gini of 0.35 is consistent with
every state being identical internally and very different from each other, and
with every state being internally unequal and identical on average. Those imply
opposite policy responses. `theil_decomposition` splits the total exactly into a
within-group and a between-group part, which is the property GE(0) and GE(1)
have and the Gini does not.

*How much of a gap is composition?* Scheduled Tribe households have lower mean
consumption than others. Some of that gap is that they hold less land and less
schooling; some of it is a different return on the same land and the same
schooling. `oaxaca_blinder` separates the two. The second part is often labelled
discrimination, and that label is a claim the arithmetic does not support: it is
the residual, and it carries every determinant left out of the model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .indices import generalised_entropy
from .ranks import prepare

__all__ = ["theil_decomposition", "oaxaca_blinder"]


def theil_decomposition(values, groups, weights=None, *, alpha: float = 1.0) -> dict:
    """Split GE(0) or GE(1) into within-group and between-group inequality.

    Parameters
    ----------
    alpha
        1 for Theil's T, which weights groups by their share of the total; 0 for
        the mean log deviation, which weights them by population share. No other
        value decomposes additively, and passing one raises rather than
        returning a number whose parts do not sum.

    Returns a dict with ``total``, ``within``, ``between``, ``between_share``
    and a per-group frame. ``within + between == total`` to floating-point
    tolerance, asserted in the tests, because a decomposition whose parts do not
    add up is worse than no decomposition.

    The between-group share is the interpretable number. Reading it: a between
    share of 0.15 means that if you equalised every state's internal
    distribution while leaving state means alone, 85 per cent of national
    inequality would remain. Across Indian states, consumption inequality is
    overwhelmingly within rather than between, which is the standard finding
    and the reason state-level averages mislead.
    """
    if not (np.isclose(alpha, 0.0) or np.isclose(alpha, 1.0)):
        raise ValueError(
            f"theil_decomposition: alpha = {alpha:g} does not decompose additively. "
            "Only GE(0) and GE(1) do. Use alpha=0 or alpha=1.")

    v = pd.Series(pd.to_numeric(pd.Series(values).reset_index(drop=True), errors="coerce"))
    g = pd.Series(groups).reset_index(drop=True)
    w = (pd.Series(np.ones(len(v))) if weights is None
         else pd.Series(pd.to_numeric(pd.Series(weights).reset_index(drop=True), errors="coerce")))
    if not (len(v) == len(g) == len(w)):
        raise ValueError("theil_decomposition: values, groups and weights differ in length")

    frame = pd.DataFrame({"v": v, "g": g, "w": w}).dropna(subset=["v", "w"])
    if frame.empty:
        raise ValueError("theil_decomposition: no rows left after dropping missing values")
    if (frame["v"] <= 0).any():
        raise ValueError(
            "theil_decomposition: the variable must be strictly positive. Both GE(0) "
            "and GE(1) take a logarithm of it.")

    total_w = frame["w"].sum()
    grand_mean = float((frame["v"] * frame["w"]).sum() / total_w)
    total = generalised_entropy(frame["v"], frame["w"], alpha=alpha)

    rows, within = [], 0.0
    for key, part in frame.groupby("g", dropna=False, observed=True):
        pw = part["w"].sum()
        pop_share = float(pw / total_w)
        mean = float((part["v"] * part["w"]).sum() / pw)
        value_share = float((part["v"] * part["w"]).sum() / (grand_mean * total_w))
        inner = (generalised_entropy(part["v"], part["w"], alpha=alpha)
                 if len(part) > 1 else 0.0)
        share = value_share if np.isclose(alpha, 1.0) else pop_share
        within += share * inner
        rows.append({"group": key, "n": len(part), "population_share": pop_share,
                     "value_share": value_share, "mean": mean,
                     "within_group_index": inner,
                     "contribution_to_within": share * inner})

    by_group = pd.DataFrame(rows)
    if np.isclose(alpha, 1.0):
        between = float((by_group["value_share"]
                         * np.log(by_group["mean"] / grand_mean)).sum())
    else:
        between = float((by_group["population_share"]
                         * np.log(grand_mean / by_group["mean"])).sum())

    return {
        "index": "GE(1), Theil T" if np.isclose(alpha, 1.0) else "GE(0), mean log deviation",
        "total": float(total),
        "within": float(within),
        "between": between,
        "between_share": float(between / total) if total != 0 else float("nan"),
        "grand_mean": grand_mean,
        "by_group": by_group,
    }


def oaxaca_blinder(df: pd.DataFrame, outcome: str, group: str, predictors: list[str], *,
                   weights: str | None = None, advantaged=None,
                   reference: str = "pooled") -> dict:
    """Blinder-Oaxaca decomposition of the mean gap between two groups.

    Splits ``ȳ_A − ȳ_B`` into a part explained by differences in the predictors
    (endowments) and a part explained by differences in the coefficients on
    them.

    Parameters
    ----------
    group
        A column with exactly two distinct values.
    advantaged
        Which value is group A. Defaults to whichever has the higher weighted
        mean outcome, so the reported gap is positive and reads naturally.
    reference
        Which coefficient vector counts as non-discriminatory. ``"pooled"``
        (Neumark 1988) fits one model on both groups and is the usual default.
        ``"advantaged"`` or ``"disadvantaged"`` use one group's own
        coefficients, which is the classic twofold form. ``"threefold"`` returns
        the endowments / coefficients / interaction split instead, with the
        disadvantaged group's coefficients as the base.

    Returns a dict with the gap, the components, and a per-predictor frame
    showing each variable's contribution.

    **On what the unexplained part is.** It is a residual. It contains genuine
    differences in returns, and it also contains every predictor you left out,
    every mismeasured one, and the consequences of selection into the sample. A
    large unexplained share is a reason to look harder, not a measurement of
    discrimination, and the index cannot tell the two apart. The identification
    problem is Oaxaca's own; see Fortin, Lemieux and Firpo, "Decomposition
    methods in economics", *Handbook of Labor Economics* 4A (2011), section 3.
    """
    import statsmodels.api as sm

    for col in [outcome, group, *predictors] + ([weights] if weights else []):
        if col not in df.columns:
            raise KeyError(f"oaxaca_blinder: no column {col!r} in the frame")

    cols = [outcome, group, *predictors] + ([weights] if weights else [])
    data = df[cols].dropna()
    if data.empty:
        raise ValueError("oaxaca_blinder: no complete rows")

    levels = pd.unique(data[group])
    if len(levels) != 2:
        raise ValueError(
            f"oaxaca_blinder: {group!r} takes {len(levels)} values; this decomposition "
            "compares exactly two groups. Subset the frame first.")

    w_all = data[weights].to_numpy(float) if weights else np.ones(len(data))

    def wmean(mask, col):
        return float(np.sum(data.loc[mask, col].to_numpy(float) * w_all[mask])
                     / np.sum(w_all[mask]))

    if advantaged is None:
        means = {lv: wmean((data[group] == lv).to_numpy(), outcome) for lv in levels}
        advantaged = max(means, key=means.get)
    if advantaged not in set(levels):
        raise ValueError(f"oaxaca_blinder: advantaged={advantaged!r} is not one of {list(levels)}")
    disadvantaged = [lv for lv in levels if lv != advantaged][0]

    def fit(mask):
        X = sm.add_constant(data.loc[mask, predictors].to_numpy(float), has_constant="add")
        y = data.loc[mask, outcome].to_numpy(float)
        return sm.WLS(y, X, weights=w_all[mask]).fit()

    mask_a = (data[group] == advantaged).to_numpy()
    mask_b = (data[group] == disadvantaged).to_numpy()
    for name, mask in (("advantaged", mask_a), ("disadvantaged", mask_b)):
        if mask.sum() <= len(predictors) + 1:
            raise ValueError(
                f"oaxaca_blinder: the {name} group has {mask.sum()} rows for "
                f"{len(predictors) + 1} parameters. The fit is not identified.")

    fit_a, fit_b = fit(mask_a), fit(mask_b)
    beta_a, beta_b = fit_a.params, fit_b.params

    names = ["(intercept)", *predictors]
    xbar_a = np.array([1.0] + [wmean(mask_a, p) for p in predictors])
    xbar_b = np.array([1.0] + [wmean(mask_b, p) for p in predictors])
    gap = wmean(mask_a, outcome) - wmean(mask_b, outcome)

    if reference == "threefold":
        endow = (xbar_a - xbar_b) * beta_b
        coeff = xbar_b * (beta_a - beta_b)
        inter = (xbar_a - xbar_b) * (beta_a - beta_b)
        parts = pd.DataFrame({"term": names, "endowments": endow,
                              "coefficients": coeff, "interaction": inter})
        out = {"form": "threefold (base: disadvantaged group)",
               "endowments": float(endow.sum()), "coefficients": float(coeff.sum()),
               "interaction": float(inter.sum())}
    else:
        if reference == "pooled":
            X = sm.add_constant(data[predictors].to_numpy(float), has_constant="add")
            beta_star = sm.WLS(data[outcome].to_numpy(float), X, weights=w_all).fit().params
            label = "twofold, pooled reference (Neumark)"
        elif reference == "advantaged":
            beta_star, label = beta_a, "twofold, advantaged group's coefficients"
        elif reference == "disadvantaged":
            beta_star, label = beta_b, "twofold, disadvantaged group's coefficients"
        else:
            raise ValueError(
                "oaxaca_blinder: reference must be 'pooled', 'advantaged', "
                "'disadvantaged' or 'threefold'")
        explained = (xbar_a - xbar_b) * beta_star
        unexplained = xbar_a * (beta_a - beta_star) + xbar_b * (beta_star - beta_b)
        parts = pd.DataFrame({"term": names, "explained": explained,
                              "unexplained": unexplained})
        out = {"form": label, "explained": float(explained.sum()),
               "unexplained": float(unexplained.sum())}

    out.update({
        "advantaged": advantaged, "disadvantaged": disadvantaged,
        "mean_advantaged": wmean(mask_a, outcome),
        "mean_disadvantaged": wmean(mask_b, outcome),
        "gap": gap,
        "n_advantaged": int(mask_a.sum()), "n_disadvantaged": int(mask_b.sum()),
        "by_term": parts,
    })
    return out
