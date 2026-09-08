"""
Design-based estimation for complex survey data: weighted proportions and means
with standard errors that account for stratification and clustering.

Most Python survey work stops at a weighted mean. The weights are the easy half.
A national household survey is stratified and clustered, so an unadjusted
standard error is too small, often by a factor of two or more, and every
confidence interval and significance test built on it is wrong in the direction
that flatters the finding.

This module implements the Taylor linearisation (ultimate cluster) variance
estimator, which is what Stata's `svy:` prefix and R's `survey` package use.

    from survey_estimation import svy_prop_by
    svy_prop_by(df, "stunted", by="wealth_quintile")

Works with any survey that carries a weight, a PSU and a stratum. It is not
specific to DHS; see dhs_stunting_example.py for one worked application.
"""

from __future__ import annotations

import warnings
from statistics import NormalDist

import numpy as np
import pandas as pd

try:
    from scipy import stats as _st
    _HAVE_SCIPY = True
except ImportError:  # pragma: no cover - depends on the environment
    _HAVE_SCIPY = False

_SCIPY_WARNED = False


def _t_quantile(conf: float, df: float) -> tuple[float, str]:
    """Two-sided t quantile, and the name of the distribution actually used.

    A survey design has finite degrees of freedom, clusters minus strata, and
    with a few dozen clusters the t quantile is visibly larger than 1.96. Where
    scipy is unavailable this falls back to the normal, which makes every
    interval slightly too narrow, so the fallback says so out loud and the
    returned distribution name records which one produced the number.
    """
    global _SCIPY_WARNED
    alpha = 1 - conf
    if _HAVE_SCIPY and df > 0:
        return float(_st.t.ppf(1 - alpha / 2, df)), f"t({df:g})"
    if not _SCIPY_WARNED:
        warnings.warn(
            "scipy is not installed, so confidence intervals use the normal "
            "quantile rather than t on the design's degrees of freedom. Intervals "
            "will be slightly too narrow. Install scipy to fix this.",
            RuntimeWarning, stacklevel=3)
        _SCIPY_WARNED = True
    return float(NormalDist().inv_cdf(1 - alpha / 2)), "normal (scipy absent)"


def _linearised_variance(u: pd.Series, psu: pd.Series, strata: pd.Series,
                         singleunit: str = "centered") -> float:
    """Ultimate cluster variance of a total whose linearised values are `u`.

    The sum of squared deviations is taken between PSU totals within each
    stratum, which is what makes this a *cluster* standard error rather than an
    independence one.

    A stratum containing a single PSU has no within-stratum variation to
    measure. `singleunit="centered"` centres its contribution on the grand mean
    of the PSU totals, matching Stata's `singleunit(centered)`;
    `"certainty"` treats it as a certainty unit contributing nothing.
    """
    frame = pd.DataFrame({"u": u.to_numpy(), "psu": psu.to_numpy(),
                          "strata": strata.to_numpy()})
    psu_totals = frame.groupby(["strata", "psu"], sort=False)["u"].sum().reset_index()
    grand_mean = psu_totals["u"].mean()

    variance = 0.0
    for _stratum, block in psu_totals.groupby("strata", sort=False):
        n_h = len(block)
        if n_h > 1:
            centre = block["u"].mean()
            variance += (n_h / (n_h - 1)) * float(((block["u"] - centre) ** 2).sum())
        elif singleunit == "centered":
            variance += float(((block["u"] - grand_mean) ** 2).sum())
        # "certainty" adds nothing: a stratum with one PSU is taken as selected
        # with certainty and contributes no sampling variance.
    return variance


def svy_prop(df: pd.DataFrame, outcome: str, weight: str = "weight",
             psu: str = "psu", strata: str = "strata", domain=None,
             conf: float = 0.95, ci: str = "logit",
             singleunit: str = "centered") -> dict:
    """Design-based estimate of a proportion or mean, with its standard error.

    Parameters
    ----------
    df : DataFrame
        The full sample. Do not subset it to estimate a subgroup; pass `domain`
        instead, for the reason given below.
    outcome : str
        Column to average. Binary 0/1 for a proportion, numeric for a mean.
        Rows where it is missing are dropped from the numerator and denominator
        but their PSUs still count towards the degrees of freedom.
    weight, psu, strata : str
        Survey design columns.
    domain : array-like of bool, optional
        Subgroup indicator. Estimating a subgroup by filtering the DataFrame
        first understates the standard error, because PSUs that contain no
        members of the subgroup still belong to the design and still count in
        the stratum's PSU total. Passing `domain` keeps them.
    ci : {"logit", "linear"}
        Logit keeps a proportion's interval inside [0, 1], which matters when
        the estimate is near either bound. Ignored for a non-binary outcome.

    Returns
    -------
    dict with estimate, se, ci_low, ci_high, n (unweighted rows used),
    n_clusters, n_strata, df (degrees of freedom) and deff for binary outcomes.
    """
    for col in (outcome, weight, psu, strata):
        if col not in df.columns:
            raise KeyError(f"column {col!r} is not in the DataFrame")

    d = df.copy()
    d["_in"] = np.ones(len(d)) if domain is None else np.asarray(domain, dtype=float)
    y = pd.to_numeric(d[outcome], errors="coerce")
    # A missing outcome leaves the estimate but not the design: the PSU stays.
    d["_in"] = d["_in"].where(y.notna(), 0.0)
    d["_y"] = y.fillna(0.0)
    w = pd.to_numeric(d[weight], errors="coerce").fillna(0.0)

    denom = float((w * d["_in"]).sum())
    if denom <= 0:
        raise ValueError("The domain has no weighted observations.")
    est = float((w * d["_in"] * d["_y"]).sum()) / denom

    # Linearised value of the ratio estimator: the residual, weighted, scaled by
    # the estimated domain size.
    u = w * d["_in"] * (d["_y"] - est) / denom
    var = _linearised_variance(u, d[psu], d[strata], singleunit=singleunit)
    se = float(np.sqrt(max(var, 0.0)))

    n_clusters = int(d.groupby([strata, psu], sort=False).ngroups)
    n_strata = int(d[strata].nunique())
    dof = max(n_clusters - n_strata, 1)
    tq, ci_dist = _t_quantile(conf, dof)

    n_used = int(d["_in"].sum())
    binary = bool(np.isin(d.loc[d["_in"] > 0, "_y"].dropna().unique(), [0, 1]).all())

    if binary and ci == "logit" and 0 < est < 1 and se > 0:
        # Delta-method SE on the logit scale, back-transformed. Keeps the
        # interval inside [0, 1] instead of reporting a negative lower bound.
        logit = np.log(est / (1 - est))
        se_logit = se / (est * (1 - est))
        lo, hi = (1 / (1 + np.exp(-(logit + s * tq * se_logit))) for s in (-1, 1))
    else:
        lo, hi = est - tq * se, est + tq * se

    out = {"estimate": est, "se": se, "ci_low": float(lo), "ci_high": float(hi),
           "n": n_used, "n_clusters": n_clusters, "n_strata": n_strata, "df": dof,
           "ci_dist": ci_dist}

    if binary and n_used > 1:
        var_srs = est * (1 - est) / (n_used - 1)
        out["deff"] = float(var / var_srs) if var_srs > 0 else float("nan")
    return out


def svy_prop_by(df: pd.DataFrame, outcome: str, by: str, weight: str = "weight",
                psu: str = "psu", strata: str = "strata", conf: float = 0.95,
                ci: str = "logit", singleunit: str = "centered",
                include_total: bool = True) -> pd.DataFrame:
    """`svy_prop` across the levels of `by`, one row per level.

    Each level is estimated as a domain of the full sample rather than by
    subsetting, so the standard errors are right.
    """
    if by not in df.columns:
        raise KeyError(f"column {by!r} is not in the DataFrame")
    rows = []
    for level in sorted(df[by].dropna().unique()):
        res = svy_prop(df, outcome, weight=weight, psu=psu, strata=strata,
                       domain=(df[by] == level), conf=conf, ci=ci,
                       singleunit=singleunit)
        rows.append({by: level, **res})
    if include_total:
        res = svy_prop(df, outcome, weight=weight, psu=psu, strata=strata,
                       conf=conf, ci=ci, singleunit=singleunit)
        rows.append({by: "Total", **res})
    return pd.DataFrame(rows)


def compare_to_published(estimates: pd.DataFrame, published: pd.DataFrame,
                         on: str, est_col: str = "estimate",
                         pub_col: str = "published", scale: float = 100.0,
                         tolerance: float = 1.0) -> pd.DataFrame:
    """Line your estimates up against a published table and flag the gaps.

    Reproducing the published figures is the only cheap check that a survey
    pipeline is correct end to end. A weight left unscaled, a domain filtered
    too early, an anthropometry flag kept as data: each of these produces a
    number that looks reasonable on its own and visibly wrong beside the
    report the survey agency published.

    `tolerance` is in the same units as `published` (percentage points by
    default). A difference inside it is consistent with rounding in the
    published table; outside it, something in the pipeline needs finding.
    """
    merged = estimates.merge(published, on=on, how="outer", suffixes=("", "_pub"))
    merged["estimate_pct"] = merged[est_col] * scale
    merged["difference"] = merged["estimate_pct"] - merged[pub_col]
    merged["within_tolerance"] = merged["difference"].abs() <= tolerance
    return merged[[on, "estimate_pct", pub_col, "difference", "within_tolerance"]]
