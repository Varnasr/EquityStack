"""
Propensity Score Matching for observational impact evaluation.
Nearest-neighbor matching with balance diagnostics.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm


def estimate_propensity_scores(df, treatment, covariates):
    """
    Estimate propensity scores using logistic regression.

    Returns
    -------
    tuple of (DataFrame with pscore column, fitted model)
    """
    X = sm.add_constant(df[covariates])
    model = sm.Logit(df[treatment], X).fit(disp=0)
    df = df.copy()
    df["pscore"] = model.predict(X)
    return df, model


def nearest_neighbor_match(df, treatment, caliper=0.1, replace=False):
    """
    Match each treated unit to nearest control by propensity score.
    Returns DataFrame of matched pairs with distances.
    """
    treated = df[df[treatment] == 1]
    control = df[df[treatment] == 0].copy()
    used = set()
    matches = []

    for idx, row in treated.iterrows():
        dists = abs(control["pscore"] - row["pscore"])
        if not replace:
            dists[control.index.isin(used)] = np.inf
        best = dists.idxmin()
        if dists[best] <= caliper:
            if not replace:
                used.add(best)
            matches.append({"treated_idx": idx, "control_idx": best, "distance": dists[best]})

    return pd.DataFrame(matches)


def balance_table(df, treatment, covariates, matches):
    """
    Compute standardised mean differences before and after matching.
    Values < 0.1 indicate good balance.
    """
    t_idx = matches["treated_idx"].values
    c_idx = matches["control_idx"].values
    results = []

    for var in covariates:
        # Before matching
        t_all = df[df[treatment] == 1][var]
        c_all = df[df[treatment] == 0][var]
        pooled_sd = np.sqrt((t_all.var() + c_all.var()) / 2)
        smd_before = (t_all.mean() - c_all.mean()) / pooled_sd if pooled_sd > 0 else 0

        # After matching
        t_matched = df.loc[t_idx, var]
        c_matched = df.loc[c_idx, var]
        pooled_sd_m = np.sqrt((t_matched.var() + c_matched.var()) / 2)
        smd_after = (t_matched.mean() - c_matched.mean()) / pooled_sd_m if pooled_sd_m > 0 else 0

        results.append({
            "variable": var,
            "smd_before": round(abs(smd_before), 3),
            "smd_after": round(abs(smd_after), 3),
            "balanced": abs(smd_after) < 0.1,
        })

    return pd.DataFrame(results)


def estimate_att(df, outcome, matches):
    """Estimate ATT on matched sample."""
    t_outcomes = df.loc[matches["treated_idx"], outcome].values
    c_outcomes = df.loc[matches["control_idx"], outcome].values
    diff = t_outcomes - c_outcomes
    att = diff.mean()
    se = diff.std() / np.sqrt(len(diff))
    return {"att": round(att, 3), "se": round(se, 3), "n_pairs": len(diff)}
