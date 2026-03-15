"""
Difference-in-Differences estimation for impact evaluation.
Provides functions for DiD estimation, parallel trends testing, and event study plots.
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf


def estimate_did(df, outcome, treatment, post, covariates=None):
    """
    Estimate DiD effect via OLS.

    Parameters
    ----------
    df : DataFrame
    outcome : str - outcome variable name
    treatment : str - binary treatment indicator
    post : str - binary post-period indicator
    covariates : list of str, optional - control variables

    Returns
    -------
    statsmodels RegressionResults
    """
    df = df.copy()
    df["_treat_post"] = df[treatment] * df[post]
    formula = f"{outcome} ~ {treatment} + {post} + _treat_post"
    if covariates:
        formula += " + " + " + ".join(covariates)
    return smf.ols(formula, data=df).fit()


def parallel_trends_test(df, outcome, treatment, time_var, pre_periods):
    """
    Test parallel trends by checking treatment-time interactions in pre-period.
    Returns OLS results; insignificant treatment-time interactions support DiD validity.
    """
    pre = df[df[time_var].isin(pre_periods)].copy()
    pre["_time_numeric"] = pre[time_var].rank(method="dense")
    pre["_treat_time"] = pre[treatment] * pre["_time_numeric"]
    model = smf.ols(
        f"{outcome} ~ {treatment} + _time_numeric + _treat_time", data=pre
    ).fit()
    return model


def event_study(df, outcome, treatment, time_var, ref_period):
    """
    Event study estimation: separate treatment effects by time period.
    Returns DataFrame with period-specific estimates and CIs.
    """
    df = df.copy()
    periods = sorted(df[time_var].unique())
    results = []

    for t in periods:
        if t == ref_period:
            results.append({"period": t, "estimate": 0, "se": 0, "ci_lower": 0, "ci_upper": 0})
            continue
        subset = df[df[time_var].isin([ref_period, t])].copy()
        subset["_post"] = (subset[time_var] == t).astype(int)
        subset["_treat_post"] = subset[treatment] * subset["_post"]
        model = smf.ols(
            f"{outcome} ~ {treatment} + _post + _treat_post", data=subset
        ).fit()
        coef = model.params["_treat_post"]
        se = model.bse["_treat_post"]
        results.append({
            "period": t,
            "estimate": round(coef, 3),
            "se": round(se, 3),
            "ci_lower": round(coef - 1.96 * se, 3),
            "ci_upper": round(coef + 1.96 * se, 3),
        })

    return pd.DataFrame(results)
